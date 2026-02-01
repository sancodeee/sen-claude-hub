#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Dependency-Aware Parallel Testing System
用于 agent-browser-integration-test skill 的智能并行测试模块

特性：
- 自动分析元素间依赖关系
- 拓扑排序确定执行顺序
- 安全并行（无依赖冲突的元素）
- 运行时冲突检测与自动回退
"""

import logging
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Set, List, Optional, Dict, Tuple, Any, TYPE_CHECKING
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import time
import os
import sys

# Import shared data models
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from models import InteractiveElement, TestResult, TestConfig

# Type hints for type checkers (avoiding circular import at runtime)
if TYPE_CHECKING:
    from browser_manager import BrowserManager
    from run_test import NetworkMonitor, ElementTester

logger = logging.getLogger(__name__)


# =============================================================================
# Data Classes
# =============================================================================

class DependencyType(Enum):
    """依赖类型枚举"""
    FORM_GROUP = "form_group"           # 同一表单内的元素
    DOM_PARENT = "dom_parent"           # DOM 父子关系
    STATE_DEPENDENT = "state_dependent" # 状态依赖（先勾选再提交）
    SEQUENTIAL = "sequential"           # 顺序操作（计数器+/-）
    TEMPORAL = "temporal"               # 时间依赖（先加载再操作）
    SAFE_PARALLEL = "safe_parallel"     # 可以安全并行


@dataclass
class ElementDependency:
    """元素依赖关系"""
    source: str           # 源元素 selector（后执行）
    target: str           # 目标元素 selector（先执行）
    dep_type: DependencyType
    reason: str
    weight: int = 1       # 依赖权重，用于打破循环


@dataclass
class ExecutionGroup:
    """可并行执行的元素组"""
    elements: List['InteractiveElement']
    group_id: int
    dependencies: Set[str] = field(default_factory=set)  # 依赖的前置元素
    can_parallel: bool = True


# =============================================================================
# Dependency Analyzer
# =============================================================================

class DependencyAnalyzer:
    """
    元素依赖分析器
    
    通过 JavaScript 和启发式规则分析元素间的依赖关系，
    构建依赖图用于后续拓扑排序。
    """
    
    def __init__(self, browser: 'BrowserManager'):
        self.browser = browser
        self.dependency_rules = self._init_rules()
    
    def _init_rules(self) -> Dict:
        """初始化依赖检测规则"""
        return {
            'form_submit_keywords': [
                'submit', 'save', 'create', 'register', 'login',
                '提交', '保存', '创建', '注册', '登录', '发送'
            ],
            'state_trigger_keywords': [
                'agree', 'accept', 'confirm', 'checkbox',
                '同意', '接受', '确认'
            ],
            'sequential_pairs': [
                (['+', 'add', '增加', 'increment'], ['-', 'remove', '减少', 'decrement']),
                (['up', '上', 'previous'], ['down', '下', 'next']),
                (['open', '打开', 'expand'], ['close', '关闭', 'collapse'])
            ],
            'dangerous_keywords': [
                'delete', 'destroy', 'remove', 'pay', 'checkout',
                '删除', '移除', '支付', '结算'
            ]
        }
    
    def analyze_dependencies(self, elements: List['InteractiveElement']) -> 'DependencyGraph':
        """
        分析元素依赖关系，构建依赖图

        Args:
            elements: 页面上的交互元素列表

        Returns:
            DependencyGraph: 依赖图对象
        """
        graph = DependencyGraph()
        
        # 添加所有节点
        for elem in elements:
            graph.add_node(elem.selector, element=elem)
        
        # 建立索引加速查询
        form_elements = defaultdict(list)
        for elem in elements:
            if elem.form_id:
                form_elements[elem.form_id].append(elem)
        
        # 分析每对元素的依赖关系
        for i, elem1 in enumerate(elements):
            for elem2 in elements[i+1:]:
                deps = self._detect_dependencies(elem1, elem2, form_elements)
                for dep in deps:
                    graph.add_edge(dep.target, dep.source, 
                                 type=dep.dep_type.value,
                                 reason=dep.reason,
                                 weight=dep.weight)
        
        logger.info(f"依赖分析完成: {len(elements)} 个元素, "
                   f"{graph.edge_count()} 条依赖边")
        
        return graph
    
    def _detect_dependencies(self, elem1: 'InteractiveElement',
                            elem2: 'InteractiveElement',
                            form_elements: Dict) -> List[ElementDependency]:
        """
        检测两个元素之间的所有依赖关系
        
        Returns:
            List[ElementDependency]: 发现的依赖关系列表
        """
        deps = []
        
        # 规则1: 同一表单内的提交依赖
        form_dep = self._check_form_dependency(elem1, elem2, form_elements)
        if form_dep:
            deps.append(form_dep)
        
        # 规则2: DOM 父子关系
        dom_dep = self._check_dom_dependency(elem1, elem2)
        if dom_dep:
            deps.append(dom_dep)
        
        # 规则3: 状态依赖（如：勾选协议后才能注册）
        state_dep = self._check_state_dependency(elem1, elem2)
        if state_dep:
            deps.append(state_dep)
        
        # 规则4: 顺序操作（如：数量加减）
        seq_dep = self._check_sequential_dependency(elem1, elem2)
        if seq_dep:
            deps.append(seq_dep)
        
        # 规则5: 危险操作依赖（危险操作必须在其他操作完成后执行）
        danger_dep = self._check_dangerous_dependency(elem1, elem2)
        if danger_dep:
            deps.append(danger_dep)
        
        return deps
    
    def _check_form_dependency(self, elem1: 'InteractiveElement',
                               elem2: 'InteractiveElement',
                               form_elements: Dict) -> Optional[ElementDependency]:
        """检查表单依赖：表单字段必须在提交按钮之前填充"""
        
        # 识别提交按钮
        def is_submit_button(elem):
            if elem.type != 'button':
                return False
            text_lower = elem.text.lower() if elem.text else ""
            return any(kw in text_lower for kw in self.dependency_rules['form_submit_keywords'])
        
        # 识别表单输入字段
        def is_form_input(elem):
            return elem.type in ['input', 'select', 'checkbox', 'radio', 'textarea']
        
        # 检查是否在同一表单
        if (elem1.form_id and elem2.form_id and 
            elem1.form_id == elem2.form_id):
            
            # 情况1: elem1是字段, elem2是提交按钮
            if is_form_input(elem1) and is_submit_button(elem2):
                return ElementDependency(
                    source=elem2.selector,
                    target=elem1.selector,
                    dep_type=DependencyType.FORM_GROUP,
                    reason=f"表单'{elem1.form_id}': 字段'{elem1.text}'必须在提交按钮'{elem2.text}'之前填充",
                    weight=10
                )
            
            # 情况2: elem2是字段, elem1是提交按钮
            if is_form_input(elem2) and is_submit_button(elem1):
                return ElementDependency(
                    source=elem1.selector,
                    target=elem2.selector,
                    dep_type=DependencyType.FORM_GROUP,
                    reason=f"表单'{elem2.form_id}': 字段'{elem2.text}'必须在提交按钮'{elem1.text}'之前填充",
                    weight=10
                )
        
        return None
    
    def _check_dom_dependency(self, elem1: 'InteractiveElement',
                             elem2: 'InteractiveElement') -> Optional[ElementDependency]:
        """检查 DOM 父子关系依赖"""
        
        # 使用 JavaScript 检测 DOM 关系
        js_code = f'''
        (() => {{
            const e1 = document.querySelector("{elem1.selector}");
            const e2 = document.querySelector("{elem2.selector}");
            if (!e1 || !e2) return "none";
            
            // 检查是否包含关系
            if (e1.contains(e2)) return "e1_contains_e2";
            if (e2.contains(e1)) return "e2_contains_e1";
            
            // 检查是否有共同父级（如 tabs）
            const getParents = (el) => {{
                const parents = [];
                while (el.parentElement) {{
                    parents.push(el.parentElement);
                    el = el.parentElement;
                }}
                return parents;
            }};
            
            const parents1 = getParents(e1);
            const parents2 = getParents(e2);
            const common = parents1.find(p => parents2.includes(p));
            
            if (common) {{
                // 检查是否是 tab/accordion 等组件
                const role = common.getAttribute('role');
                if (role === 'tablist' || role === 'tabpanel') return "common_tab";
                if (common.classList.contains('tabs') || 
                    common.classList.contains('accordion')) return "common_component";
            }}
            
            return "none";
        }})()
        '''
        
        try:
            result = self.browser.eval_js(js_code)
            
            if result == "e1_contains_e2":
                # e1 是父级，应该先操作 e1 打开/展开
                return ElementDependency(
                    source=elem2.selector,
                    target=elem1.selector,
                    dep_type=DependencyType.DOM_PARENT,
                    reason=f"DOM关系: '{elem1.text}'是父容器，必须先操作",
                    weight=5
                )
            elif result == "e2_contains_e1":
                return ElementDependency(
                    source=elem1.selector,
                    target=elem2.selector,
                    dep_type=DependencyType.DOM_PARENT,
                    reason=f"DOM关系: '{elem2.text}'是父容器，必须先操作",
                    weight=5
                )
            elif result in ["common_tab", "common_component"]:
                # 同组件内的元素应该串行
                return ElementDependency(
                    source=elem2.selector,
                    target=elem1.selector,
                    dep_type=DependencyType.DOM_PARENT,
                    reason="同组件(Tab/Accordion)内元素需要串行操作",
                    weight=3
                )
        except Exception as e:
            logger.warning(f"DOM依赖检测失败: {e}")
        
        return None
    
    def _check_state_dependency(self, elem1: 'InteractiveElement',
                               elem2: 'InteractiveElement') -> Optional[ElementDependency]:
        """检查状态依赖（如：勾选协议后才能点击注册）"""
        
        # 识别触发器（checkbox）
        def is_trigger(elem):
            if elem.type != 'checkbox':
                return False
            text_lower = elem.text.lower() if elem.text else ""
            return any(kw in text_lower for kw in self.dependency_rules['state_trigger_keywords'])
        
        # 识别依赖操作（如注册按钮）
        def is_dependent_action(elem):
            if elem.type != 'button':
                return False
            text_lower = elem.text.lower() if elem.text else ""
            return any(kw in text_lower for kw in ['register', 'signup', 'submit', '注册'])
        
        # 检查距离（需要在相近区域内）
        if is_trigger(elem1) and is_dependent_action(elem2):
            if self._are_elements_close(elem1, elem2):
                return ElementDependency(
                    source=elem2.selector,
                    target=elem1.selector,
                    dep_type=DependencyType.STATE_DEPENDENT,
                    reason=f"状态依赖: 必须先勾选'{elem1.text}'才能点击'{elem2.text}'",
                    weight=8
                )
        
        if is_trigger(elem2) and is_dependent_action(elem1):
            if self._are_elements_close(elem1, elem2):
                return ElementDependency(
                    source=elem1.selector,
                    target=elem2.selector,
                    dep_type=DependencyType.STATE_DEPENDENT,
                    reason=f"状态依赖: 必须先勾选'{elem2.text}'才能点击'{elem1.text}'",
                    weight=8
                )
        
        return None
    
    def _check_sequential_dependency(self, elem1: 'InteractiveElement',
                                    elem2: 'InteractiveElement') -> Optional[ElementDependency]:
        """检查顺序操作依赖（如数量+/-按钮）"""
        
        text1 = (elem1.text or "").lower()
        text2 = (elem2.text or "").lower()
        
        for inc_keywords, dec_keywords in self.dependency_rules['sequential_pairs']:
            # 检查是否是一对顺序操作
            elem1_is_inc = any(kw in text1 for kw in inc_keywords)
            elem1_is_dec = any(kw in text1 for kw in dec_keywords)
            elem2_is_inc = any(kw in text2 for kw in inc_keywords)
            elem2_is_dec = any(kw in text2 for kw in dec_keywords)
            
            # 如果它们共享同一个父容器（如购物车商品数量控制）
            if (elem1_is_inc or elem1_is_dec) and (elem2_is_inc or elem2_is_dec):
                if self._share_same_container(elem1, elem2):
                    # 这些操作共享状态，必须串行
                    return ElementDependency(
                        source=elem2.selector,
                        target=elem1.selector,
                        dep_type=DependencyType.SEQUENTIAL,
                        reason=f"顺序操作: '{elem1.text}'和'{elem2.text}'共享计数器状态，必须串行",
                        weight=10
                    )
        
        return None
    
    def _check_dangerous_dependency(self, elem1: 'InteractiveElement',
                                   elem2: 'InteractiveElement') -> Optional[ElementDependency]:
        """
        危险操作依赖：危险操作应该在其他测试完成后执行
        这样即使出问题，也不会影响其他测试
        """
        text1 = (elem1.text or "").lower()
        text2 = (elem2.text or "").lower()
        
        elem1_is_dangerous = any(kw in text1 for kw in self.dependency_rules['dangerous_keywords'])
        elem2_is_dangerous = any(kw in text2 for kw in self.dependency_rules['dangerous_keywords'])
        
        # 危险操作应该在普通操作之后执行
        if elem1_is_dangerous and not elem2_is_dangerous:
            return ElementDependency(
                source=elem1.selector,
                target=elem2.selector,
                dep_type=DependencyType.TEMPORAL,
                reason=f"危险操作'{elem1.text}'应该在普通操作之后执行",
                weight=6
            )
        
        if elem2_is_dangerous and not elem1_is_dangerous:
            return ElementDependency(
                source=elem2.selector,
                target=elem1.selector,
                dep_type=DependencyType.TEMPORAL,
                reason=f"危险操作'{elem2.text}'应该在普通操作之后执行",
                weight=6
            )
        
        return None
    
    def _are_elements_close(self, elem1: 'InteractiveElement',
                           elem2: 'InteractiveElement',
                           threshold: int = 200) -> bool:
        """检查两个元素是否在空间上接近"""
        js_code = f'''
        (() => {{
            const e1 = document.querySelector("{elem1.selector}");
            const e2 = document.querySelector("{elem2.selector}");
            if (!e1 || !e2) return false;
            
            const rect1 = e1.getBoundingClientRect();
            const rect2 = e2.getBoundingClientRect();
            
            // 计算中心点距离
            const center1 = {{
                x: rect1.left + rect1.width / 2,
                y: rect1.top + rect1.height / 2
            }};
            const center2 = {{
                x: rect2.left + rect2.width / 2,
                y: rect2.top + rect2.height / 2
            }};
            
            const distance = Math.sqrt(
                Math.pow(center1.x - center2.x, 2) + 
                Math.pow(center1.y - center2.y, 2)
            );
            
            return distance < {threshold};
        }})()
        '''
        
        try:
            result = self.browser.eval_js(js_code)
            return result == "true"
        except:
            return False
    
    def _share_same_container(self, elem1: 'InteractiveElement',
                             elem2: 'InteractiveElement') -> bool:
        """检查两个元素是否共享同一个父容器"""
        js_code = f'''
        (() => {{
            const e1 = document.querySelector("{elem1.selector}");
            const e2 = document.querySelector("{elem2.selector}");
            if (!e1 || !e2) return false;
            
            // 检查是否有共同的 list-item 或 cart-item 父级
            let p1 = e1.parentElement;
            let p2 = e2.parentElement;
            
            while (p1 && p1.tagName !== 'BODY') {{
                if (p1.classList.contains('item') || 
                    p1.classList.contains('row') ||
                    p1.tagName === 'LI') {{
                    // 检查 e2 是否也在同一容器下
                    return p1.contains(e2);
                }}
                p1 = p1.parentElement;
            }}
            
            return false;
        }})()
        '''
        
        try:
            result = self.browser.eval_js(js_code)
            return result == "true"
        except:
            return False


# =============================================================================
# Dependency Graph
# =============================================================================

class DependencyGraph:
    """依赖图实现（使用邻接表）"""
    
    def __init__(self):
        self.nodes: Dict[str, Dict] = {}  # selector -> {element, edges}
        self.edges: List[Tuple[str, str, Dict]] = []  # (from, to, attrs)
    
    def add_node(self, selector: str, element: Any):
        """添加节点"""
        if selector not in self.nodes:
            self.nodes[selector] = {
                'element': element,
                'outgoing': [],
                'incoming': []
            }
    
    def add_edge(self, from_selector: str, to_selector: str, **attrs):
        """添加边（from 必须在 to 之前执行）"""
        if from_selector in self.nodes and to_selector in self.nodes:
            edge_data = {'to': to_selector, **attrs}
            self.nodes[from_selector]['outgoing'].append(edge_data)
            
            edge_data_back = {'from': from_selector, **attrs}
            self.nodes[to_selector]['incoming'].append(edge_data_back)
            
            self.edges.append((from_selector, to_selector, attrs))
    
    def edge_count(self) -> int:
        """返回边的数量"""
        return len(self.edges)
    
    def has_cycle(self) -> bool:
        """检测图中是否有环"""
        visited = set()
        rec_stack = set()
        
        def dfs(node):
            visited.add(node)
            rec_stack.add(node)
            
            for edge in self.nodes.get(node, {}).get('outgoing', []):
                neighbor = edge['to']
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(node)
            return False
        
        for node in self.nodes:
            if node not in visited:
                if dfs(node):
                    return True
        
        return False
    
    def topological_sort(self) -> List[str]:
        """
        拓扑排序（Kahn算法）
        
        Returns:
            按依赖顺序排列的元素 selector 列表
        """
        # 计算入度
        in_degree = {node: 0 for node in self.nodes}
        for node in self.nodes:
            for edge in self.nodes[node].get('outgoing', []):
                in_degree[edge['to']] += 1
        
        # 初始化队列（入度为0的节点）
        queue = [node for node in self.nodes if in_degree[node] == 0]
        result = []
        
        while queue:
            # 按权重排序，优先执行权重低的（基础操作）
            queue.sort(key=lambda n: self._get_node_weight(n))
            
            node = queue.pop(0)
            result.append(node)
            
            for edge in self.nodes[node].get('outgoing', []):
                neighbor = edge['to']
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        if len(result) != len(self.nodes):
            # 有环，需要打破
            logger.warning("检测到循环依赖，尝试打破...")
            self._break_cycles()
            return self.topological_sort()
        
        return result
    
    def _get_node_weight(self, selector: str) -> int:
        """获取节点的总权重（用于排序）"""
        incoming = self.nodes.get(selector, {}).get('incoming', [])
        return sum(edge.get('weight', 1) for edge in incoming)
    
    def _break_cycles(self):
        """打破循环依赖（移除权重最低的边）"""
        # 找出入度最小的非零节点
        in_degree = {node: 0 for node in self.nodes}
        for node in self.nodes:
            for edge in self.nodes[node].get('outgoing', []):
                in_degree[edge['to']] += 1

        candidates = [(n, d) for n, d in in_degree.items() if d > 0]
        if candidates:
            # 移除入度最小的节点的权重最低的边
            node_to_fix = min(candidates, key=lambda x: x[1])[0]
            incoming = self.nodes[node_to_fix].get('incoming', [])
            if incoming:
                # 移除权重最低的边
                min_edge = min(incoming, key=lambda e: e.get('weight', 1))
                from_node = min_edge['from']
                edge_reason = min_edge.get('reason', 'unknown')
                edge_weight = min_edge.get('weight', 1)

                # 从图中移除这条边
                self.nodes[from_node]['outgoing'] = [
                    e for e in self.nodes[from_node]['outgoing']
                    if e['to'] != node_to_fix
                ]
                self.nodes[node_to_fix]['incoming'] = [
                    e for e in self.nodes[node_to_fix]['incoming']
                    if e['from'] != from_node
                ]

                logger.warning(f"打破循环依赖: 移除边 {from_node} -> {node_to_fix} "
                             f"(权重: {edge_weight}, 原因: {edge_reason})")
    
    def group_by_parallelization(self, sorted_nodes: List[str]) -> List[ExecutionGroup]:
        """
        将排序后的节点分组，同组内的元素可以安全并行
        
        算法：
        1. 遍历排序后的节点
        2. 如果当前节点与组内任何节点有依赖关系，则开启新组
        3. 否则加入当前组
        
        Returns:
            List[ExecutionGroup]: 执行组列表
        """
        groups = []
        current_group = []
        current_group_deps = set()
        
        for i, selector in enumerate(sorted_nodes):
            if selector not in self.nodes:
                continue
            
            # 获取这个节点的所有依赖（祖先节点）
            ancestors = self._get_ancestors(selector)
            
            # 检查是否与当前组有依赖冲突
            if current_group and (ancestors & current_group_deps):
                # 有冲突，保存当前组，开启新组
                groups.append(ExecutionGroup(
                    elements=[self.nodes[s]['element'] for s in current_group],
                    group_id=len(groups),
                    dependencies=current_group_deps.copy()
                ))
                current_group = []
                current_group_deps = set()
            
            # 加入当前组
            current_group.append(selector)
            current_group_deps.add(selector)
            current_group_deps.update(ancestors)
        
        # 保存最后一组
        if current_group:
            groups.append(ExecutionGroup(
                elements=[self.nodes[s]['element'] for s in current_group],
                group_id=len(groups),
                dependencies=current_group_deps.copy()
            ))
        
        # 标记可以并行的组（组内元素数>1且都是安全操作）
        for group in groups:
            if len(group.elements) > 1:
                # 检查组内是否有危险操作
                has_dangerous = any(
                    self._is_dangerous_element(e) for e in group.elements
                )
                group.can_parallel = not has_dangerous
        
        return groups
    
    def _get_ancestors(self, selector: str, visited: Set[str] = None) -> Set[str]:
        """获取节点的所有祖先（依赖）"""
        if visited is None:
            visited = set()
        
        if selector in visited:
            return set()
        
        visited.add(selector)
        ancestors = set()
        
        for edge in self.nodes.get(selector, {}).get('incoming', []):
            parent = edge['from']
            ancestors.add(parent)
            ancestors.update(self._get_ancestors(parent, visited))
        
        return ancestors
    
    def _is_dangerous_element(self, element: 'InteractiveElement') -> bool:
        """检查元素是否危险操作"""
        text = (element.text or "").lower()
        dangerous = ['delete', 'destroy', 'remove', 'pay', 'checkout',
                    '删除', '移除', '支付', '结算']
        return any(kw in text for kw in dangerous)
    
    def to_dict(self) -> Dict:
        """将依赖图转为字典（用于调试）"""
        return {
            'nodes': list(self.nodes.keys()),
            'edges': [
                {
                    'from': from_node,
                    'to': to_node,
                    **attrs
                }
                for from_node, to_node, attrs in self.edges
            ]
        }


# =============================================================================
# Runtime Conflict Detector
# =============================================================================

class RuntimeConflictDetector:
    """
    运行时冲突检测器 - 改进版本，支持锁清理

    在并行执行时实时监控DOM冲突，自动回退到串行模式。
    支持定期清理长时间未使用的锁，防止资源泄漏。
    """

    def __init__(self, cleanup_interval: int = 300):
        """
        Args:
            cleanup_interval: 锁清理间隔（秒），0 表示禁用自动清理
        """
        self.active_locks: Dict[str, threading.Lock] = {}
        self.lock_timestamps: Dict[str, float] = {}  # 记录锁的最后使用时间
        self.global_lock = threading.Lock()
        self.conflict_count = 0
        self.fallback_to_sequential = False
        self.cleanup_interval = cleanup_interval
        self._last_cleanup = time.time()
    
    def acquire_lock(self, selector: str, timeout: float = 5.0) -> bool:
        """
        尝试获取元素执行锁 - 带真正超时支持的版本

        Args:
            selector: 元素选择器
            timeout: 超时时间（秒），实际支持超时等待

        Returns:
            bool: 是否成功获取锁

        Note:
            修复了原实现中 timeout 参数未真正使用的问题。
            现在使用轮询方式在 global_lock 外实现真正的超时等待。
        """
        import time

        start_time = time.time()
        poll_interval = 0.1  # 100ms 轮询间隔

        while True:
            # 检查超时
            elapsed = time.time() - start_time
            if elapsed >= timeout:
                self.conflict_count += 1
                logger.warning(f"获取锁超时: {selector} (等待了 {elapsed:.1f}s)")

                # 如果冲突太多，切换到串行模式
                if self.conflict_count > 5:
                    logger.warning("冲突过多，切换到串行模式")
                    self.fallback_to_sequential = True

                return False

            # 在 global_lock 保护下检查并尝试获取锁
            with self.global_lock:
                if selector not in self.active_locks:
                    self.active_locks[selector] = threading.Lock()

                lock = self.active_locks[selector]

                # 尝试非阻塞获取锁
                acquired = lock.acquire(blocking=False)
                if acquired:
                    # 记录锁的获取时间
                    self.lock_timestamps[selector] = time.time()
                    return True

            # 未获取到锁，等待一小段时间后重试
            time.sleep(poll_interval)
    
    def release_lock(self, selector: str):
        """释放元素执行锁 - 改进版本，记录释放时间"""
        with self.global_lock:
            if selector in self.active_locks:
                try:
                    self.active_locks[selector].release()
                    # 记录锁的释放时间
                    self.lock_timestamps[selector] = time.time()
                except RuntimeError:
                    # 锁未被持有
                    pass

    def cleanup_old_locks(self, max_age_seconds: int = None):
        """
        清理长时间未使用的锁

        Args:
            max_age_seconds: 锁的最大闲置时间（秒），None 表示使用配置的清理间隔
        """
        if self.cleanup_interval == 0:
            return  # 禁用自动清理

        age_limit = max_age_seconds or self.cleanup_interval
        current_time = time.time()

        # 检查是否需要执行清理（避免频繁清理）
        if current_time - self._last_cleanup < self.cleanup_interval:
            return

        with self.global_lock:
            expired = []
            for selector, last_used in self.lock_timestamps.items():
                if current_time - last_used > age_limit:
                    expired.append(selector)

            for selector in expired:
                # 只删除未锁定的锁
                lock = self.active_locks.get(selector)
                if lock and not lock.locked():
                    del self.active_locks[selector]
                    del self.lock_timestamps[selector]
                    logger.debug(f"清理闲置锁: {selector}")

            self._last_cleanup = current_time

            if expired:
                logger.info(f"清理了 {len(expired)} 个闲置锁")
    
    def check_dom_conflict(self, selector1: str, selector2: str,
                          browser: 'BrowserManager') -> bool:
        """检查两个选择器是否操作同一DOM区域"""
        js_code = f'''
        (() => {{
            const e1 = document.querySelector("{selector1}");
            const e2 = document.querySelector("{selector2}");
            if (!e1 || !e2) return false;
            
            // 检查是否相同或包含
            if (e1 === e2) return true;
            if (e1.contains(e2) || e2.contains(e1)) return true;
            
            // 检查是否有共同父级且在相近区域内
            const rect1 = e1.getBoundingClientRect();
            const rect2 = e2.getBoundingClientRect();
            
            // 检查矩形是否相交
            const intersect = !(rect1.right < rect2.left || 
                               rect2.right < rect1.left ||
                               rect1.bottom < rect2.top || 
                               rect2.bottom < rect1.top);
            
            return intersect;
        }})()
        '''
        
        try:
            result = browser.eval_js(js_code)
            return result == "true"
        except:
            return False
    
    def should_fallback_to_sequential(self) -> bool:
        """是否应该回退到串行模式"""
        return self.fallback_to_sequential
    
    def get_stats(self) -> Dict:
        """获取冲突统计"""
        return {
            'conflict_count': self.conflict_count,
            'active_locks': len([l for l in self.active_locks.values() 
                                if l.locked()]),
            'fallback_triggered': self.fallback_to_sequential
        }


# =============================================================================
# Smart Parallel Executor
# =============================================================================

class SmartParallelExecutor:
    """
    智能并行执行器
    
    核心特性：
    1. 基于依赖图拓扑排序
    2. 分组并行执行（无依赖冲突的组内元素）
    3. 运行时冲突检测与自动回退
    4. 详细的执行统计
    """
    
    def __init__(self, browser: 'BrowserManager',
                 monitor: 'NetworkMonitor',
                 tester: 'ElementTester',
                 config: 'TestConfig' = None):
        self.browser = browser
        self.monitor = monitor
        self.tester = tester
        # TestConfig is now imported at top level, but we keep the fallback logic
        self.config = config or TestConfig()
            
        self.analyzer = DependencyAnalyzer(browser)
        self.conflict_detector = RuntimeConflictDetector()
        self.results: List['TestResult'] = []
        self.stats = {
            'groups_executed': 0,
            'elements_parallel': 0,
            'elements_sequential': 0,
            'conflicts_detected': 0,
            'fallback_triggered': False
        }
    
    def execute(self, elements: List['InteractiveElement']) -> List['TestResult']:
        """
        执行智能并行测试
        
        Args:
            elements: 要测试的交互元素列表
            
        Returns:
            List[TestResult]: 测试结果列表
        """
        logger.info(f"开始智能并行测试: {len(elements)} 个元素")
        
        # 阶段1: 分析依赖
        logger.info("步骤1: 分析元素依赖关系...")
        dep_graph = self.analyzer.analyze_dependencies(elements)
        
        # 输出依赖图信息
        graph_info = dep_graph.to_dict()
        logger.info(f"依赖图: {len(graph_info['nodes'])} 节点, "
                   f"{len(graph_info['edges'])} 条边")
        
        # 阶段2: 拓扑排序
        logger.info("步骤2: 拓扑排序...")
        sorted_selectors = dep_graph.topological_sort()
        logger.info(f"执行顺序: {len(sorted_selectors)} 个元素")
        
        # 阶段3: 分组并行化
        logger.info("步骤3: 分组并行化...")
        execution_groups = dep_graph.group_by_parallelization(sorted_selectors)
        logger.info(f"分为 {len(execution_groups)} 个执行组")
        
        for i, group in enumerate(execution_groups):
            mode = "并行" if group.can_parallel and len(group.elements) > 1 else "串行"
            logger.info(f"  组 {i+1}: {len(group.elements)} 个元素 ({mode})")
        
        # 阶段4: 执行
        logger.info("步骤4: 执行测试...")
        for group in execution_groups:
            self._execute_group(group)
            
            # 检查是否需要回退
            if self.conflict_detector.should_fallback_to_sequential():
                logger.warning("触发回退机制，剩余组将串行执行")
                self.stats['fallback_triggered'] = True
        
        # 输出统计
        self._log_statistics()
        
        return self.results
    
    def _execute_group(self, group: ExecutionGroup):
        """执行一个组"""
        self.stats['groups_executed'] += 1
        
        if group.can_parallel and len(group.elements) > 1:
            # 并行执行
            self._execute_parallel(group)
        else:
            # 串行执行
            self._execute_sequential(group)
    
    def _execute_sequential(self, group: ExecutionGroup):
        """串行执行组内元素"""
        self.stats['elements_sequential'] += len(group.elements)
        
        for element in group.elements:
            logger.info(f"串行测试: {element.type} '{element.text[:30]}'")
            
            result = self._test_element_safe(element)
            self.results.append(result)
    
    def _execute_parallel(self, group: ExecutionGroup):
        """并行执行组内元素 - 改进版本，带线程取消机制"""
        self.stats['elements_parallel'] += len(group.elements)

        logger.info(f"并行测试 {len(group.elements)} 个元素...")

        # 使用线程池
        with ThreadPoolExecutor(max_workers=min(len(group.elements), 5)) as executor:
            # 提交所有任务
            future_to_element = {}
            for element in group.elements:
                future = executor.submit(self._test_element_with_lock, element)
                future_to_element[future] = element

            # 收集结果，带超时和取消机制
            # 使用配置的超时时间，如果未配置则使用默认值
            wait_timeout = self.config.default_timeout * 2 if self.config else 60
            cmd_timeout = self.config.default_timeout if self.config else 30
            
            for future in as_completed(future_to_element, timeout=wait_timeout):
                element = future_to_element[future]
                try:
                    result = future.result(timeout=cmd_timeout)
                    self.results.append(result)
                except Exception as e:
                    logger.error(f"并行测试失败 {element.text}: {e}")

                    # 尝试取消任务（如果还在运行）
                    if not future.done():
                        future.cancel()
                        logger.warning(f"已取消超时任务: {element.text}")

                    self.results.append(TestResult(
                        element=element,
                        success=False,
                        apis_called=[],
                        error=f"并行执行异常: {str(e)}"
                    ))

            # 等待剩余任务完成或超时
            for future in future_to_element:
                if not future.done():
                    logger.warning("等待剩余任务完成...")
                    try:
                        future.result(timeout=5)
                    except Exception:
                        future.cancel()
                        logger.warning("强制取消未完成的任务")
    
    def _test_element_safe(self, element: 'InteractiveElement') -> 'TestResult':
        """安全地测试单个元素（串行模式）"""
        try:
            self.monitor.start_recording()
            result = self.tester.test_element(element, self.monitor)
            result.apis_called = self.monitor.capture_new_requests(element.text)
            return result
        except Exception as e:
            logger.error(f"测试失败 {element.selector}: {e}")
            return TestResult(
                element=element,
                success=False,
                apis_called=[],
                error=str(e)
            )
    
    def _test_element_with_lock(self, element: 'InteractiveElement') -> 'TestResult':
        """带锁地测试单个元素（并行模式）"""
        selector = element.selector
        
        # 尝试获取锁
        if not self.conflict_detector.acquire_lock(selector, timeout=5.0):
            # 获取锁失败，说明有冲突，回退到串行
            logger.warning(f"获取锁失败，串行执行: {selector}")
            return self._test_element_safe(element)
        
        try:
            # 执行测试
            result = self._test_element_safe(element)
            return result
        finally:
            # 释放锁
            self.conflict_detector.release_lock(selector)
    
    def _log_statistics(self):
        """输出执行统计"""
        conflict_stats = self.conflict_detector.get_stats()
        
        logger.info("=" * 50)
        logger.info("智能并行测试统计")
        logger.info("=" * 50)
        logger.info(f"执行组数: {self.stats['groups_executed']}")
        logger.info(f"并行测试元素: {self.stats['elements_parallel']}")
        logger.info(f"串行测试元素: {self.stats['elements_sequential']}")
        logger.info(f"冲突检测: {conflict_stats['conflict_count']}")
        logger.info(f"回退触发: {self.stats['fallback_triggered']}")
        logger.info(f"总结果数: {len(self.results)}")
        logger.info("=" * 50)
    
    def get_execution_report(self) -> Dict:
        """获取执行报告（用于最终测试报告）"""
        return {
            'execution_mode': 'smart_parallel',
            'statistics': self.stats,
            'conflict_stats': self.conflict_detector.get_stats(),
            'total_results': len(self.results),
            'success_count': sum(1 for r in self.results if r.success),
            'failure_count': sum(1 for r in self.results if not r.success)
        }


if __name__ == "__main__":
    # 简单测试
    logging.basicConfig(level=logging.INFO)
    logger.info("Dependency-Aware Parallel Testing System")
    logger.info("导入成功，可以作为模块使用")

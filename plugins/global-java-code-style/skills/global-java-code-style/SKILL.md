---
name: global-java-code-style
description: 提供 Java 编码风格、项目结构、注释规范、异常处理、测试规范等标准指引
argument-hint: "[规范类型] [具体问题] 例如：命名约定、异常处理、测试规范等"
user-invocable: true
---

# 全局Java代码规范指南

## 概述

本指南提供统一的代码编写规范，涵盖命名约定、代码格式、项目结构、注释文档、异常处理、测试规范、依赖管理、安全健壮性以及 AI
代码生成指引。遵循这些规范有助于提升代码质量、可读性和可维护性。

---

## 命名约定

### 类和接口

- 【强制】使用**大驼峰命名法**（`UpperCamelCase`）
- 【强制】类名应为名词，接口名可为名词或形容词
- 【强制】抽象类使用 `Abstract` 或 `Base` 开头
- 【强制】异常类使用 `Exception` 结尾
- 【强制】测试类以它要测试的类名开始加 `Test` 结尾
- 【强制】禁止以下划线或美元符号开始/结束命名

**示例：**

```java
// 正例
public class UserService {
}

public interface Serializable {
}

public abstract class AbstractUserService {
}

public class CustomException extends Exception {
}

public class UserServiceTest {
}

// 反例
public class _UserService {
}

public class UserService$ {
}

public class userService {
}
```

### 方法和变量

- 【强制】使用**小驼峰命名法**（`lowerCamelCase`）
- 【强制】方法名应为动词短语
- 【强制】禁止以下划线或美元符号开始/结束
- 【强制】POJO 中布尔变量不加 `is` 前缀（否则部分框架解析会出错）

**示例：**

```java
// 正例
public void calculateTotal() {
}

private String userName;
private boolean success; // 不使用 isSuccess

// 反例
public void Calculate_Total() {
}

private String _userName;
private boolean isSuccess; // POJO 中禁止
```

### 数组定义

- 【强制】数组定义：`String[] args` 而非 `String args[]`

**示例：**

```java
// 正例
String[] args;
int[] numbers;

// 反例
String args[];
int numbers[];
```

### 常量

- 【强制】使用**全大写加下划线**（`UPPER_SNAKE_CASE`）
- 【强制】long 赋值使用大写 `L`（非小写 `l`）
- 【强制】浮点数后缀统一大写 `D` 或 `F`

**示例：**

```java
// 正例
public static final long MAX_RETRY_COUNT = 100L;
public static final double DEFAULT_RATE = 3.14D;
public static final float PI = 3.14F;

// 反例
public static final long MAX_RETRY_COUNT = 100l; // 小写 l 容易与 1 混淆
public static final float PI = 3.14f; // 应使用大写 F
```

### 包名

- 【强制】包名使用小写，单数形式
- 【强制】点分隔符间只有一个自然语义单词
- 【强制】禁止下划线、美元符号等特殊字符
- 【强制】杜绝不规范的缩写

**示例：**

```java
// 正例
com.example.project.service
com.alibaba.cloud.nacos

// 反例
com.example.project.serviceImpl  // Impl 应为独立单词
com.example.project.user_service // 禁止下划线
com.example.project.userService  // service 应为小写
```

### 命名通用规范

- 【强制】禁止拼音与英文混合
- 【强制】禁止中文命名
- 【强制】杜绝不规范的英文缩写
- 【推荐】使用完整单词，保持清晰易懂

---

## 常量定义规范

### 魔法值

- 【强制】不允许魔法值（即未经定义的常量）直接出现在代码中

**示例：**

```java
// 反例
if(status ==1){
        // ...
        }

// 正例
public static final int STATUS_ACTIVE = 1;
if(status ==STATUS_ACTIVE){
        // ...
        }
```

### 常量组织

- 【推荐】按功能归类维护常量，而非一个庞大的常量类
- 【推荐】五层复用层次：
    1. 跨应用共享常量：放置在二方库中（如 `commons-module`）
    2. 应用内共享常量：放置在内部模块（如 `core-module`）
    3. 子工程内共享：放置在 `constants` 包
    4. 包内共享：放在当前包的 `constants` 子包
    5. 类内共享：放在类的 `private static final`

**示例：**

```java
// 跨应用共享（二方库）
// commons-module/src/main/java/com/example/commons/constants/SystemConstants.java
public static final String DEFAULT_CHARSET = "UTF-8";

// 应用内共享
// core-module/src/main/java/com/example/core/constants/BusinessConstants.java
public static final int ORDER_STATUS_PENDING = 0;

// 类内使用
private static final int MAX_RETRY_TIMES = 3;
```

### 枚举使用

- 【推荐】固定范围变化用 `enum`，不要用常量

**示例：**

```java
// 正例 - 使用枚举
public enum OrderStatus {
    PENDING(0, "待支付"),
    PAID(1, "已支付"),
    SHIPPED(2, "已发货"),
    COMPLETED(3, "已完成");

    private final int code;
    private final String desc;

    OrderStatus(int code, String desc) {
        this.code = code;
        this.desc = desc;
    }
}

// 反例 - 使用常量
public static final int ORDER_STATUS_PENDING = 0;
public static final int ORDER_STATUS_PAID = 1;
```

### 变量与常量

- 【强制】只读变量（`final` 修饰）命名全部大写
- 【强制】非只读变量使用小驼峰

---

## 代码格式

### 缩进

- 【强制】采用 **4 个空格**缩进，禁用 Tab
- 【强制】IDE 编码设置为 UTF-8，换行符设置为 Unix 格式（LF）

### 大括号（K&R 风格）

- 【强制】左大括号前加空格
- 【强制】空大括号写成 `{}`，无需换行空格
- 【强制】非空大括号：左括号不换行，右括号换行

**示例：**

```java
// 正例
if(condition){
        // 语句
        }else{
        // 语句
        }

public void method() {
}

// 反例
if(condition)
        {
        // 语句
        }
```

### 空格规则

- 【强制】左小括号右边无空格，右小括号左边无空格
- 【强制】`if`/`for`/`while` 等保留字与括号间加空格
- 【强制】所有二目、三目运算符左右加空格
- 【强制】方法参数逗号后加空格
- 【强制】注释双斜线与内容间仅一个空格
- 【强制】类型强制转换：右括号与值间无空格

**示例：**

```java
// 正例
if(a ==b){}
int sum = a + b;
String result = (condition) ? "yes" : "no";

method(a, b, c);

// 注释内容
int value = (int) (amount * 100);

// 反例
if(a ==b){}                  // if 后缺少空格
int sum = a + b;                   // 运算符缺少空格

method(a, b, c);                 // 逗号后缺少空格

//  注释内容                   // 双斜线后多个空格
int value = (int) (amount * 100);  // 括号多余空格
```

### 行长度与换行

- 【强制】单行字符不超过 **120 个**
- 【推荐】单个方法不超过 **80 行**
- 【推荐】不同逻辑、语义、业务间插入空行分隔

### 组织结构

- 【强制】成员之间用空行分隔
- 【强制】相关成员可额外加空格分组
- 【强制】重载方法放在一起

---

## OOP 规约

### 方法调用

- 【强制】避免通过对象访问静态变量或方法
- 【强制】覆写方法必须加 `@Override` 注解
- 【强制】外部调用的接口不允许修改方法签名
- 【强制】不能使用过时的类或方法（`@Deprecated`）

**示例：**

```java
// 反例 - 通过对象访问静态方法
User user = new User();
user.

staticMethod();

// 正例
User.

staticMethod();

// 正例 - 覆写方法加注解
@Override
public String toString() {
    return "User{name=" + name + "}";
}
```

### 可变参数

- 【强制】相同参数类型和业务含义才能使用可变参数
- 【强制】可变参数必须放在参数列表最后

**示例：**

```java
// 正例
public void method(String... args) {
}

// 反例 - 可变参数不在最后
public void method(String... args, int count) {
}
```

### equals 与 hashCode

- 【强制】`equals` 方法用常量或确定有值的对象调用
- 【强制】整型包装类比较使用 `equals`，而非 `==`
- 【强制】只要覆写 `equals`，就必须覆写 `hashCode`
- 【强制】POJO 类必须写 `toString` 方法

**示例：**

```java
// 反例 - equals 可能抛出 NPE
if(user.equals(currentUser)){}

// 正例
        if(currentUser.

equals(user)){}
// 或
        if(Objects.

equals(user, currentUser)){}

// 反例 - 整型包装类用 == 比较
Integer a = 100;
Integer b = 100;
if(a ==b){}  // -128~127 之间才相等

// 正例
        if(a.

equals(b)){}

// 正例 - 同时覆写 hashCode
@Override
public boolean equals(Object o) {
    if (this == o) return true;
    if (o == null || getClass() != o.getClass()) return false;
    User user = (User) o;
    return Objects.equals(id, user.id);
}

@Override
public int hashCode() {
    return Objects.hash(id);
}
```

### 数值计算

- 【强制】货币金额使用最小货币单位整型存储
- 【强制】浮点数等值判断使用 `BigDecimal`
- 【强制】`BigDecimal` 等值比较用 `compareTo()` 而非 `equals()`

**示例：**

```java
// 正例 - 金额用最小单位（分）存储
private Long amount;  // 单位：分

// 反例 - 浮点数直接比较
if(0.1+0.2==0.3){}  // false

// 正例
BigDecimal a = new BigDecimal("0.1");
BigDecimal b = new BigDecimal("0.2");
BigDecimal sum = a.add(b);
if(sum.

compareTo(new BigDecimal("0.3"))==0){}

// 反例 - BigDecimal equals 比较（会考虑精度）
        if(new

BigDecimal("0.1").

equals(new BigDecimal("0.10"))){}  // false

// 正例
        if(new

BigDecimal("0.1").

compareTo(new BigDecimal("0.10"))==0){}  // true
```

---

## 日期时间处理规范

### 年份格式化

- 【强制】年份格式化使用 `yyyy` 表示当天所在的年，**禁止使用 `YYYY`**
- 【强制】`YYYY` 表示"week in which year"，可能导致跨年错误

**示例：**

```java
// 反例 - YYYY 表示"week in which year"，可能导致跨年错误
DateTimeFormatter formatter = DateTimeFormatter.ofPattern("YYYY-MM-dd");
// 2024年12月31日（周二）可能会被格式化为 2025-12-31

// 正例 - yyyy 表示当天所在的年
DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd");
```

### 日期计算

- 【强制】禁止写死一年为365天，应使用 `plusYears(1)`
- 【推荐】使用 Java 8+ 日期 API（`LocalDateTime`、`ZonedDateTime`）
- 【强制】避免使用 `Date`、`SimpleDateFormat`（线程不安全）

**示例：**

```java
// 反例 - 写死365天，未考虑闰年
int days = 365;
LocalDate nextYear = today.plusDays(days);

// 正例 - 使用 plusYears 自动处理闰年
LocalDate nextYear = today.plusYears(1);

// 反例 - SimpleDateFormat 线程不安全
private static final SimpleDateFormat FORMAT = new SimpleDateFormat("yyyy-MM-dd");

// 正例 - DateTimeFormatter 线程安全
private static final DateTimeFormatter FORMATTER = DateTimeFormatter.ofPattern("yyyy-MM-dd");
```

### 时区处理

- 【推荐】明确指定时区，避免使用系统默认时区
- 【推荐】统一时区：UTC 或 GMT+8

**示例：**

```java
// 正例 - 明确指定时区
ZonedDateTime utcTime = ZonedDateTime.now(ZoneId.of("UTC"));
ZonedDateTime beijingTime = ZonedDateTime.now(ZoneId.of("Asia/Shanghai"));

// 反例 - 使用系统默认时区，可能在不同环境表现不一致
LocalDateTime.

now();
```

### 前后端时间格式统一

- 【推荐】统一格式：`yyyy-MM-dd HH:mm:ss`
- 【推荐】不推荐使用时间戳（可读性差）
- 【推荐】前端传入时间需包含时区信息

**示例：**

```java
// 正例 - 统一的时间格式
public class OrderDTO {
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss", timezone = "GMT+8")
    private LocalDateTime createTime;
}

// 反例 - 使用时间戳，可读性差
public class OrderDTO {
    private Long createTime;  // 毫秒时间戳
}
```

---

## 集合处理规范

### 集合判空

- 【强制】判断集合是否为空使用 `isEmpty()` 而非 `size() == 0`
- 【强制】判断集合是否非空时，先判断是否为 `null`

**示例：**

```java
// 正例
if(CollectionUtils.isEmpty(list)){}
        if(list !=null&&!list.

isEmpty()){}

// 反例
        if(list.

size() ==0){}  // 若 list 为 null 会抛出 NPE
```

### 类型转换

- 【强制】`ArrayList` 的 `subList` 结果不可强转成 `ArrayList`
- 【强制】`subList` 是原集合的视图，对原集合增删会导致 `ConcurrentModificationException`
- 【强制】`Collections.sort` 返回泛型 `List` 不可转成 `ArrayList`

**示例：**

```java
// 反例
List<String> list = new ArrayList<>();
List<String> subList = list.subList(0, 5);
ArrayList<String> arrayList = (ArrayList<String>) subList;  // ClassCastException

// 正例 - 创建新集合
List<String> subList = list.subList(0, 5);
List<String> newList = new ArrayList<>(subList);

// 反例 - subList 后修改原集合
List<String> list = new ArrayList<>(Arrays.asList("a", "b", "c"));
List<String> subList = list.subList(0, 2);
list.

add("d");  // 修改原集合
subList.

get(0); // ConcurrentModificationException
```

### foreach 循环操作

- 【强制】禁止在 `foreach` 循环中对集合进行 `add`/`remove` 操作
- 【强制】使用 `Iterator` 的 `remove()` 方法或 Java 8+ 的 `removeIf()`

**示例：**

```java
// 反例 - foreach 中 remove 会抛出 ConcurrentModificationException
List<String> list = new ArrayList<>(Arrays.asList("a", "b", "c"));
for(
String item :list){
        if("a".

equals(item)){
        list.

remove(item);  // ConcurrentModificationException
    }
            }

// 正例 - 使用 Iterator
Iterator<String> iterator = list.iterator();
while(iterator.

hasNext()){
String item = iterator.next();
    if("a".

equals(item)){
        iterator.

remove();
    }
            }

// 正例 - 使用 removeIf（Java 8+）
            list.

removeIf("a"::equals);
```

### Arrays.asList 限制

- 【强制】`Arrays.asList()` 返回的是固定大小的列表，不支持 `add`/`remove`
- 【强制】对基本类型数组使用 `Arrays.asList()` 时注意返回值

**示例：**

```java
// 反例 - Arrays.asList 返回的列表不可增删
List<String> list = Arrays.asList("a", "b", "c");
list.

add("d");  // UnsupportedOperationException

// 正例 - 包装成可变列表
List<String> list = new ArrayList<>(Arrays.asList("a", "b", "c"));
list.

add("d");

// 反例 - 基本类型数组
int[] arr = {1, 2, 3};
List<int[]> list = Arrays.asList(arr);  // 只有一个元素，类型是 int[]

// 正例 - 使用包装类型数组
Integer[] arr = {1, 2, 3};
List<Integer> list = Arrays.asList(arr);  // 三个元素
```

### Map 遍历

- 【强制】使用 `entrySet` 遍历 `Map` 类而不是 `keySet`
- 【推荐】JDK 8+ 使用 `forEach` 方法遍历

**示例：**

```java
// 反例 - 使用 keySet 需要两次查找
for(String key :map.

keySet()){
String value = map.get(key);  // 额外的 get 操作
}

// 正例 - 使用 entrySet 只需一次遍历
        for(
Map.Entry<String, String> entry :map.

entrySet()){
String key = entry.getKey();
String value = entry.getValue();
}

// 正例 - JDK 8+ forEach
        map.

forEach((key, value) ->{
        // 处理逻辑
        });
```

### 集合初始化

- 【强制】集合初始化时指定容量，避免扩容开销
- 【推荐】HashMap 初始容量计算：`expectedSize / 0.75 + 1`

**示例：**

```java
// 正例 - 预估容量
int expectedSize = 100;
Map<String, String> map = new HashMap<>((int) (expectedSize / 0.75 + 1));
List<String> list = new ArrayList<>(expectedSize);

// 反例
List<String> list = new ArrayList<>();  // 默认容量 10，可能多次扩容
Map<String, String> map = new HashMap<>();  // 默认容量 16
```

### 泛型通配符

- 【推荐】`<? extends T>` 用于消费集合元素（只读），`<? super T>` 用于生产集合元素（只写）
- 【推荐】遵循 PECS 原则：Producer Extends, Consumer Super

**示例：**

```java
// 正例 - 只读取，使用 extends
public void printAll(List<? extends Number> list) {
    for (Number n : list) {
        System.out.println(n);
    }
}

// 正例 - 只写入，使用 super
public void addNumbers(List<? super Integer> list) {
    list.add(1);
    list.add(2);
}

// 正例 - 复制方法
public static <T> void copy(List<? super T> dest, List<? extends T> src) {
    for (T item : src) {
        dest.add(item);
    }
}
```

### 集合转数组

- 【强制】使用 `toArray(T[] array)` 方法，传入类型完全一致、长度为 0 的空数组

**示例：**

```java
// 正例
List<String> list = new ArrayList<>();
String[] array = list.toArray(new String[0]);

// 反例 - 无参 toArray 返回 Object[]
Object[] array = list.toArray();  // 类型不安全
```

---

## 并发处理规范

### 单例模式

- 【强制】获取单例需保证线程安全

**示例：**

```java
// 正例 - 双重检查锁
public class Singleton {
    private static volatile Singleton instance;

    private Singleton() {
    }

    public static Singleton getInstance() {
        if (instance == null) {
            synchronized (Singleton.class) {
                if (instance == null) {
                    instance = new Singleton();
                }
            }
        }
        return instance;
    }
}

// 正例 - 静态内部类（推荐）
public class Singleton {
    private Singleton() {
    }

    public static Singleton getInstance() {
        return Holder.INSTANCE;
    }

    private static class Holder {
        private static final Singleton INSTANCE = new Singleton();
    }
}

// 正例 - 枚举单例（最佳实践）
public enum Singleton {
    INSTANCE;

    public void doSomething() {
        // 业务逻辑
    }
}
```

### 线程池创建

- 【强制】线程池不允许使用 `Executors` 创建
- 【强制】使用 `ThreadPoolExecutor` 自定义创建
- 【强制】自定义线程工厂，设置有意义的线程名

**示例：**

```java
// 反例 - 允许请求队列长度为 Integer.MAX_VALUE，可能导致 OOM
ExecutorService executor = Executors.newFixedThreadPool(10);
ExecutorService executor = Executors.newCachedThreadPool();  // 最大线程数为 Integer.MAX_VALUE

// 正例 - 自定义线程池
ThreadPoolExecutor executor = new ThreadPoolExecutor(
        5,                          // 核心线程数
        10,                         // 最大线程数
        60L,                        // 空闲存活时间
        TimeUnit.SECONDS,
        new LinkedBlockingQueue<>(1000),  // 有界队列
        new ThreadFactoryBuilder()
                .setNameFormat("order-pool-%d")  // 有意义的线程名
                .setUncaughtExceptionHandler((t, e) ->
                        logger.error("Thread {} error", t.getName(), e))
                .build(),
        new ThreadPoolExecutor.CallerRunsPolicy()  // 拒绝策略
);
```

### ThreadLocal 使用

- 【强制】使用 `ThreadLocal` 后必须手动 `remove()`，防止内存泄漏
- 【强制】在线程池场景下尤其重要，线程复用会导致数据残留

**示例：**

```java
// 正例 - 使用完毕后手动清理
private static final ThreadLocal<UserContext> USER_CONTEXT = new ThreadLocal<>();

public void process() {
    try {
        USER_CONTEXT.set(new UserContext());
        // 业务逻辑
        doSomething();
    } finally {
        USER_CONTEXT.remove();  // 必须清理，防止内存泄漏
    }
}

// 正例 - 使用 InheritableThreadLocal 传递上下文（父子线程）
private static final InheritableThreadLocal<String> TRACE_ID = new InheritableThreadLocal<>();

// 反例 - 使用后不清理
public void process() {
    USER_CONTEXT.set(new UserContext());
    doSomething();
    // 没有 remove，线程池复用时数据残留
}
```

### 锁使用规范

- 【强制】加锁必须保证 `unlock()` 在 `finally` 块中执行
- 【推荐】优先使用 `tryLock(timeout)` 而非无限等待的 `lock()`
- 【强制】多个资源加锁时，注意加锁顺序，防止死锁

**示例：**

```java
// 正例 - finally 中释放锁
private final ReentrantLock lock = new ReentrantLock();

public void update() {
    lock.lock();
    try {
        // 临界区代码
    } finally {
        lock.unlock();  // 必须在 finally 中释放
    }
}

// 正例 - 使用 tryLock 带超时
public boolean updateWithTimeout() {
    try {
        if (lock.tryLock(5, TimeUnit.SECONDS)) {
            try {
                // 临界区代码
                return true;
            } finally {
                lock.unlock();
            }
        } else {
            logger.warn("获取锁超时");
            return false;
        }
    } catch (InterruptedException e) {
        Thread.currentThread().interrupt();
        return false;
    }
}

// 反例 - 可能导致死锁
// 线程1: lockA -> lockB
// 线程2: lockB -> lockA
```

### volatile 使用

- 【强制】`volatile` 只保证可见性和有序性，不保证原子性
- 【强制】复合操作（如 `i++`）仍需使用 `synchronized` 或 `AtomicInteger`

**示例：**

```java
// 正例 - volatile 用于状态标识
private volatile boolean running = true;

public void stop() {
    running = false;  // 其他线程立即可见
}

public void run() {
    while (running) {
        // 业务逻辑
    }
}

// 反例 - volatile 不保证原子性
private volatile int count = 0;

public void increment() {
    count++;  // 非原子操作，不安全
}

// 正例 - 使用 AtomicInteger
private final AtomicInteger count = new AtomicInteger(0);

public void increment() {
    count.incrementAndGet();
}
```

### 日期格式化

- 【强制】`SimpleDateFormat` 是线程不安全的
- 【强制】使用 `DateTimeFormatter`（Java 8+）或 `Joda-Time`

**示例：**

```java
// 反例 - SimpleDateFormat 线程不安全
private static final SimpleDateFormat FORMAT = new SimpleDateFormat("yyyy-MM-dd");

// 正例 - DateTimeFormatter 线程安全
private static final DateTimeFormatter FORMATTER = DateTimeFormatter.ofPattern("yyyy-MM-dd");
```

### 随机数生成

- 【强制】避免 `Random` 实例被多线程使用
- 【强制】使用 `ThreadLocalRandom`

**示例：**

```java
// 反例
private static final Random RANDOM = new Random();

// 正例
int randomValue = ThreadLocalRandom.current().nextInt(min, max);
```

### 并发集合

- 【强制】高并发时 `HashMap` 可能死循环，使用 `ConcurrentHashMap`
- 【强制】`ConcurrentHashMap` 的 `get`/`put` 是原子的，但组合操作不是

**示例：**

```java
// 反例 - 高并发下可能死循环
Map<String, String> map = new HashMap<>();

// 正例
ConcurrentHashMap<String, String> map = new ConcurrentHashMap<>();

// 反例 - 组合操作非原子
if(!map.

containsKey(key)){  // 检查
        map.

put(key, value);       // 放入，两步非原子
}

// 正例 - 使用原子方法
        map.

putIfAbsent(key, value);
map.

computeIfAbsent(key, k ->

createValue());
```

### CountDownLatch 和 Semaphore

- 【推荐】`CountDownLatch` 用于等待多个线程完成
- 【推荐】`Semaphore` 用于控制并发数量

**示例：**

```java
// CountDownLatch 示例
CountDownLatch latch = new CountDownLatch(3);

for(
int i = 0;
i< 3;i++){
        executor.

submit(() ->{
        try{
        // 执行任务
        }finally{
        latch.

countDown();
        }
                });
                }

                latch.

await(10,TimeUnit.SECONDS);  // 等待所有任务完成

// Semaphore 限流示例
Semaphore semaphore = new Semaphore(10);  // 最多10个并发

public void process() {
    try {
        semaphore.acquire();
        // 执行任务
    } catch (InterruptedException e) {
        Thread.currentThread().interrupt();
    } finally {
        semaphore.release();
    }
}
```

---

## 控制语句规范

### switch 语句

- 【强制】每个 `case` 需要使用 `break`/`continue`/`return` 或注释说明
- 【强制】必须包含 `default` 分支，即使什么也不做
- 【强制】`default` 分支放在最后

**示例：**

```java
// 正例
switch(status){
        case PENDING:

handlePending();
        break;
                case PROCESSING:

handleProcessing();
        break;
                case COMPLETED:
        // fall through - 故意穿透
        case CLOSED:

handleClose();
        break;
default:
        throw new

IllegalArgumentException("Unknown status: "+status);
}

// 反例 - 缺少 break，导致意外 fallthrough
        switch(status){
        case PENDING:

handlePending();
    case PROCESSING:  // 会意外执行到这里

handleProcessing();
        break;
                }

// 反例 - 缺少 default
                switch(status){
        case PENDING:

handlePending();
        break;
                }
```

### 大括号使用

- 【强制】`if`/`else`/`for`/`while`/`do` 必须使用大括号，即使只有一行

**示例：**

```java
// 正例
if(condition){

doSomething();
}

// 反例 - 不使用大括号
        if(condition)

doSomething();
```

### 条件表达式

- 【推荐】不要在条件表达式复杂时使用 `?:` 简化
- 【强制】三目运算符注意类型转换，避免自动拆箱导致 NPE

**示例：**

```java
// 正例 - 简单条件
int max = (a > b) ? a : b;

// 反例 - 复杂条件，应使用 if-else
String result = (a > b && c < d || e == f) ? complexCalculation() : anotherCalculation();

// 正例 - 复杂条件使用 if-else
String result;
if(a >b &&c<d ||e ==f){
result =

complexCalculation();
}else{
result =

anotherCalculation();
}

// 反例 - 自动拆箱导致 NPE
Integer a = 1;
Integer b = null;
Integer c = condition ? a : b;  // b 为 null 时可能 NPE

// 正例 - 避免空指针
Integer c = condition ? a : (b != null ? b : 0);
```

### 避免取反逻辑

- 【推荐】尽量使用正向逻辑，避免使用取反操作 `!`

**示例：**

```java
// 反例 - 取反逻辑
if(!isNotValid()){}

// 正例 - 正向逻辑
        if(

isValid()){}

// 反例 - 双重取反
        if(!!flag){}
```

### 条件判断顺序

- 【推荐】将较大概率成立的条件放在前面
- 【推荐】将简单的条件放在前面（短路评估）

**示例：**

```java
// 正例 - 简单条件在前，利用短路
if(flag &&

expensiveCheck()){}

// 反例 - 复杂条件在前
        if(

expensiveCheck() &&flag){}
```

### null 判断优化

- 【推荐】使用 `Objects.isNull()` 或 `Objects.nonNull()` 代替 `== null`
- 【推荐】使用 `Optional` 避免多层 null 检查

**示例：**

```java
// 正例 - 使用 Objects 工具类
if(Objects.isNull(user)){}
        if(Objects.

nonNull(user)){}

// 正例 - 使用 Optional 链式调用
String cityName = Optional.ofNullable(user)
        .map(User::getAddress)
        .map(Address::getCity)
        .map(City::getName)
        .orElse("Unknown");

// 反例 - 多层 null 检查
String cityName = "Unknown";
if(user !=null){
Address address = user.getAddress();
    if(address !=null){
City city = address.getCity();
        if(city !=null){
cityName =city.

getName();
        }
                }
                }
```

---

## 前后端规范

### 接口返回数据结构

- 【强制】统一响应结构，包含 `code`、`message`、`data`、`timestamp`

**示例：**

```java
// 正例 - 统一的响应结构
public class ApiResponse<T> {
    /**
     * 响应码。
     */
    private Integer code;

    /**
     * 响应消息。
     */
    private String message;

    /**
     * 响应数据。
     */
    private T data;

    /**
     * 响应时间戳。
     */
    private Long timestamp;

    public static <T> ApiResponse<T> success(T data) {
        ApiResponse<T> response = new ApiResponse<>();
        response.setCode(200);
        response.setMessage("success");
        response.setData(data);
        response.setTimestamp(System.currentTimeMillis());
        return response;
    }

    public static <T> ApiResponse<T> error(Integer code, String message) {
        ApiResponse<T> response = new ApiResponse<>();
        response.setCode(code);
        response.setMessage(message);
        response.setTimestamp(System.currentTimeMillis());
        return response;
    }
}
```

### RESTful API 设计

- 【推荐】使用 HTTP 动词：GET、POST、PUT、DELETE
- 【推荐】资源命名使用名词复数：`/users`、`/orders`
- 【推荐】版本控制：`/api/v1/users`

**示例：**

```java
// 正例 - RESTful 风格
GET    /api/v1/users          #获取用户列表
GET    /api/v1/users/{id}     #获取指定用户
POST   /api/v1/users          #创建用户
PUT    /api/v1/users/{id}     #更新用户
DELETE /api/v1/users/{id}     #删除用户

// 反例 - 非RESTful风格
GET    /api/v1/getUserList
POST   /api/v1/createUser
POST   /api/v1/deleteUserById
```

### 接口参数验证

- 【强制】使用 JSR-303/JSR-380 注解进行参数验证
- 【推荐】自定义验证注解处理复杂业务规则

**示例：**

```java
// 正例 - 使用验证注解
public class CreateUserRequest {
    @NotBlank(message = "用户名不能为空")
    @Size(min = 2, max = 20, message = "用户名长度2-20字符")
    private String username;

    @NotBlank(message = "邮箱不能为空")
    @Email(message = "邮箱格式不正确")
    private String email;

    @NotNull(message = "年龄不能为空")
    @Min(value = 18, message = "年龄必须大于18岁")
    private Integer age;
}

@PostMapping("/users")
public ApiResponse<User> createUser(@Valid @RequestBody CreateUserRequest request) {
    // ...
}
```

### 分页参数规范

- 【推荐】统一使用 `page`（页码，从1开始）和 `size`（每页数量）
- 【推荐】设置默认值和最大值限制

**示例：**

```java
// 正例 - 统一分页参数
@GetMapping("/users")
public ApiResponse<PageResult<User>> getUsers(
        @RequestParam(defaultValue = "1") Integer page,
        @RequestParam(defaultValue = "10") Integer size
) {
    // 限制最大每页数量
    if (size > 100) {
        size = 100;
    }
    // ...
}
```

### 错误码规范

- 【推荐】使用统一的错误码枚举
- 【推荐】错误码格式：`模块号(2位) + 业务号(3位) + 错误类型(1位)`

**示例：**

```java
// 正例 - 统一错误码
public enum ErrorCode {
    // 用户模块 01
    USER_NOT_FOUND(01001, "用户不存在"),
    USER_ALREADY_EXISTS(01002, "用户已存在"),
    USER_PASSWORD_ERROR(01003, "密码错误"),

    // 订单模块 02
    ORDER_NOT_FOUND(02001, "订单不存在"),
    ORDER_STATUS_ERROR(02002, "订单状态错误");

    private final Integer code;
    private final String message;

    ErrorCode(Integer code, String message) {
        this.code = code;
        this.message = message;
    }
}
```

### 接口文档

- 【推荐】使用 Swagger/OpenAPI 生成接口文档
- 【强制】必须包含参数说明、返回值说明、错误码说明

**示例：**

```java
// 正例 - Swagger 注解
@RestController
@RequestMapping("/api/v1/users")
@Tag(name = "用户管理", description = "用户相关接口")
public class UserController {

    @Operation(summary = "获取用户列表", description = "分页获取用户列表")
    @Parameters({
            @Parameter(name = "page", description = "页码，从1开始"),
            @Parameter(name = "size", description = "每页数量")
    })
    @GetMapping
    public ApiResponse<PageResult<User>> getUsers(
            @RequestParam(defaultValue = "1") Integer page,
            @RequestParam(defaultValue = "10") Integer size
    ) {
        // ...
    }
}
```

### 前后端时间格式

- 【推荐】后端返回统一格式：`yyyy-MM-dd HH:mm:ss`
- 【推荐】前端传入同上格式
- 【推荐】时区统一为 UTC 或 GMT+8

---

## 项目结构标准

### 标准目录布局

```
project-root/
├── src/
│   ├── main/
│   │   ├── java/           # 应用源码
│   │   └── resources/      # 资源文件
│   └── test/
│       ├── java/           # 单元测试
│       └── resources/      # 测试资源
├── pom.xml / build.gradle  # 构建文件
├── README.md
└── LICENSE.txt
```

### 应用分层

- 【推荐】推荐的分层结构：Controller → Service → Manager → DAO
- 【强制】上层依赖下层，下层不得反向依赖

```
┌─────────────────────────────────────────────────────────┐
│                    Controller 层                        │
│    负责请求转发、参数校验、响应封装                        │
└──────────────────────────┬──────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────┐
│                    Service 层                           │
│    核心业务逻辑、事务控制                                 │
└──────────────────────────┬──────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────┐
│                    Manager 层 (可选)                     │
│    通用业务处理：                                        │
│    - 对第三方平台封装（支付、短信、OSS 等）                │
│    - 对 Service 层通用能力的下沉                         │
│    - 与 DAO 层交互，对多个 DAO 的组合复用                 │
└──────────────────────────┬──────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────┐
│                    DAO 层                               │
│    数据访问层：与数据库交互                               │
└─────────────────────────────────────────────────────────┘
```

### 领域模型命名

- 【强制】各层使用不同的领域模型，禁止跨层传递

| 模型    | 全称                   | 用途       | 所在层            |
|-------|----------------------|----------|----------------|
| DO    | Data Object          | 数据库表映射对象 | DAO 层          |
| DTO   | Data Transfer Object | 数据传输对象   | Service 层输入/输出 |
| VO    | View Object          | 视图对象，展示层 | Controller 层输出 |
| BO    | Business Object      | 业务对象     | Service 层内部    |
| Query | Query Object         | 查询条件封装   | 各层输入           |

**示例：**

```java
// DO - 数据库映射
@TableName("t_user")
public class UserDO {
    private Long id;
    private String userName;
    private String password;  // 敏感字段
    private LocalDateTime createTime;
}

// DTO - 服务层传输
public class UserDTO {
    private Long id;
    private String userName;
    private String email;
    // 不包含敏感字段
}

// VO - 视图展示
public class UserVO {
    private Long id;
    private String userName;
    private String displayName;
    private String avatarUrl;
}

// Query - 查询条件
public class UserQuery {
    private String keyword;
    private Integer status;
    private LocalDate startDate;
    private LocalDate endDate;
    private Integer page;
    private Integer size;
}
```

### 包与模块

- 【强制】包结构反映模块/功能划分
- 【强制】避免包之间循环依赖
- 【推荐】常见分包方式：`controller`、`service`、`manager`、`dao`/`mapper`、`model`、`config`
- 【推荐】多模块项目在根构建文件中定义子模块

**标准包结构：**

```
com.example.project/
├── controller/          # 控制器层
│   └── UserController.java
├── service/             # 服务层
│   ├── UserService.java
│   └── impl/
│       └── UserServiceImpl.java
├── manager/             # 通用业务层（可选）
│   └── ThirdPartyPayManager.java
├── dao/                 # 数据访问层
│   └── UserMapper.java
├── model/               # 领域模型
│   ├── entity/          # DO
│   │   └── UserDO.java
│   ├── dto/             # DTO
│   │   └── UserDTO.java
│   ├── vo/              # VO
│   │   └── UserVO.java
│   └── query/           # 查询对象
│       └── UserQuery.java
├── config/              # 配置类
│   └── WebConfig.java
├── common/              # 公共组件
│   ├── exception/       # 异常定义
│   ├── constants/       # 常量定义
│   └── utils/           # 工具类
└── Application.java     # 启动类
```

### 类文件管理

- 【强制】一个 `.java` 文件只包含一个 `public` 类
- 【强制】公共类名与文件名一致
- 【推荐】内部类可写在同一文件中

---

## 注释与文档要求

### Javadoc 规范

- 【强制】类、类属性、类方法必须使用 Javadoc 格式 `/** */`，不得使用 `// xxx`
- 【强制】所有公有类、构造方法、方法和字段必须使用 Javadoc
- 【强制】抽象方法必须添加注释
- 【强制】所有类添加创建者和创建日期
- 【强制】每个非 `void` 方法必须有 `@return` 标签
- 【强制】每个参数使用 `@param` 标签
- 【强制】可能抛出的异常使用 `@throws` 说明

**示例：**

```java
/**
 * 用户服务实现类。
 *
 * @author 张三
 * @since 2024-01-01
 */
public class UserServiceImpl implements UserService {

    /**
     * 用户仓储。
     */
    private final UserRepository userRepository;

    /**
     * 计算两个数字的和。
     *
     * @param a 第一个加数
     * @param b 第二个加数
     * @return 两个数字的和
     * @throws IllegalArgumentException 如果参数为 null
     */
    public int add(Integer a, Integer b) {
        // ...
    }

    /**
     * 处理订单（抽象方法必须注释）。
     *
     * @param orderId 订单ID
     */
    public abstract void processOrder(String orderId);
}
```

### 注释风格

- 【推荐】使用 `/* */` 注释说明"为什么"，`//` 注释说明"做什么"
- 【推荐】多行注释使用 `/* */`，单行注释使用 `//`
- 【强制】注释双斜线与内容间仅一个空格

**示例：**

```java
/*
 * 这里使用 HashMap 而非 TreeMap，是因为：
 * 1. 不需要排序功能
 * 2. HashMap 的查询性能 O(1) 更优
 */
Map<String, String> cache = new HashMap<>();

// 检查用户是否存在
boolean exists = userMapper.selectById(userId) != null;
```

### 注释内容

- 【强制】解释"为什么"而非"做什么"
- 【强制】复杂算法、业务规则需详细说明
- 【强制】保持注释与代码同步
- 【强制】禁止保留无用的注释代码块
- 【推荐】使用英语或团队约定的统一语言

### 特殊标记注释

- 【强制】待办事项使用 `TODO` 标记，格式：`// TODO: [描述] - [负责人] [日期]`
- 【强制】已知缺陷使用 `FIXME` 标记，格式：`// FIXME: [描述] - [负责人] [日期]`
- 【推荐】定期清理 TODO 和 FIXME 标记

**示例：**

```java
// TODO: 增加缓存支持 - 张三 2024-01-15
public User getUserById(Long id) {
    return userMapper.selectById(id);
}

// FIXME: 并发场景下可能有问题，需要加锁 - 李四 2024-01-20
public void updateCounter() {
    counter++;
}

// XXX: 这里的实现有性能问题，后续需要优化
public List<User> getAllUsers() {
    return userMapper.selectAll();
}
```

### 本地注释规范

- 【推荐】参考项目中现有代码的注释风格
- 【推荐】保持与项目本地注释规范一致

---

## 错误与异常处理

### 异常抛出

- 【强制】检测到错误时抛出异常，**不返回错误码**
- 【强制】抛出具体的异常类型（`IllegalArgumentException`、`IOException` 等）
- 【推荐】必要时自定义异常类

**示例：**

```java
// 正例
public void divide(int a, int b) {
    if (b == 0) {
        throw new IllegalArgumentException("除数不能为零");
    }
}

// 反例
public int divide(int a, int b) {
    if (b == 0) {
        return -1;  // 不应返回错误码
    }
}
```

### 预检查 vs 异常捕获

- 【强制】`RuntimeException` 不应通过 `catch` 方式处理，应提前检查
- 【推荐】对于可预见的异常条件，使用前置检查

**示例：**

```java
// 反例 - 捕获 NullPointerException
try{
        user.getName();
}catch(
NullPointerException e){
        // ...
        }

// 正例 - 前置检查
        if(user !=null){
        user.

getName();
}
```

### 异常捕获规则

- 【强制】不要捕获 `Exception` 或 `Throwable`
- 【强制】`catch` 分清稳定代码（不会/极少出错）和非稳定代码
- 【强制】区分异常类型，分别处理
- 【强制】不要空捕获异常

**示例：**

```java
// 反例 - 捕获所有异常
try{
        // ...
        }catch(Exception e){
        // 吞掉异常
        }

// 正例 - 区分异常类型
        try{
        // 可能抛出 IOException 的代码
        }catch(
FileNotFoundException e){
        logger.

error("文件不存在: {}",e.getMessage(),e);
        throw new

BusinessException("文件配置错误",e);
}catch(
IOException e){
        logger.

error("IO 异常: {}",e.getMessage(),e);
        throw new

BusinessException("文件读取失败",e);
}
```

### 分层异常处理

- 【参考】DAO 层捕获异常并抛出业务异常

**示例：**

```java
// DAO 层
public User findById(Long id) {
    try {
        return userMapper.selectById(id);
    } catch (Exception e) {
        logger.error("查询用户失败, id={}", id, e);
        throw new DAOException("查询用户失败", e);
    }
}

// Service 层
public User getUser(Long id) {
    try {
        return userDao.findById(id);
    } catch (DAOException e) {
        logger.error("获取用户失败, id={}", id, e);
        throw new ServiceException("获取用户失败", e);
    }
}
```

### 资源管理

- 【强制】使用 try-with-resources 关闭资源
- 【推荐】确保所有 `Closeable` 资源正确关闭

**示例：**

```java
// 正例 - try-with-resources
try(InputStream is = new FileInputStream(file);
BufferedReader reader = new BufferedReader(new InputStreamReader(is))){
        // ...
        }

// 反例 - 手动关闭可能泄漏
InputStream is = null;
try{
is =new

FileInputStream(file);
// ...
}finally{
        if(is !=null){
        is.

close();  // 可能抛出异常导致资源未关闭
    }
            }
```

---

## 日志规约

### 日志框架

- 【强制】不可直接使用 Log4j/Logback API，应使用 SLF4J
- 【强制】Logger 声明：`private static final Logger logger = LoggerFactory.getLogger(Test.class);`

**示例：**

```java
// 正例

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class UserService {
    private static final Logger logger = LoggerFactory.getLogger(UserService.class);
}

// 反例 - 直接使用 Log4j
import org.apache.log4j.Logger;
private static final Logger logger = Logger.getLogger(UserService.class);
```

### 日志输出

- 【强制】使用 `{}` 占位符而非字符串拼接
- 【强制】debug 日志调用前判断：`if (logger.isDebugEnabled())`
- 【推荐】日志中避免使用 `toString()` 序列化整个对象

**示例：**

```java
// 正例 - 使用占位符
logger.info("用户登录成功, userId={}, userName={}",user.getId(),user.

getName());

// 反例 - 字符串拼接
        logger.

info("用户登录成功, userId="+user.getId() +", userName="+user.

getName());

// 正例 - debug 判断
        if(logger.

isDebugEnabled()){
        logger.

debug("详细信息: {}",expensiveOperation());
        }

// 反例 - 直接输出对象（可能产生大量日志）
        logger.

info("用户信息: {}",user);  // 可能输出大量字段
```

### 日志级别使用

- 【参考】`ERROR`：系统错误、异常，需要紧急处理
- 【参考】`WARN`：预期外但可恢复的情况，需要关注
- 【参考】`INFO`：关键业务流程、重要状态变化
- 【参考】`DEBUG`：调试信息，问题排查

**示例：**

```java
// ERROR - 系统异常，需要紧急处理
logger.error("支付处理失败, orderId={}, error={}",orderId, e.getMessage(),e);

// WARN - 预期外但可恢复
        logger.

warn("库存不足, skuId={}, 当前库存={}, 需求数量={}",skuId, stock, quantity);

// INFO - 关键业务流程
logger.

info("订单创建成功, orderId={}, userId={}, amount={}",orderId, userId, amount);

// DEBUG - 调试信息
logger.

debug("进入方法 processOrder, orderId={}",orderId);
```

### 异常日志

- 【强制】记录异常时包含堆栈信息

**示例：**

```java
// 正例
try{
        // ...
        }catch(Exception e){
        logger.

error("操作失败, userId={}",userId, e);  // e 会输出堆栈
}

// 反例 - 只输出消息，没有堆栈
        try{
        // ...
        }catch(
Exception e){
        logger.

error("操作失败, userId={}, error={}",userId, e.getMessage());
        }
```

### 禁止事项

- 【强制】禁止使用 `System.out` 或 `System.err` 输出日志
- 【强制】禁止在生产环境打印大量 debug 日志
- 【强制】禁止在日志中输出敏感信息（密码、密钥等）

---

## MySQL 数据库规范

### 建表规约

- 【强制】表名使用小写字母+下划线，长度不超过32字符
- 【强制】禁止使用 MySQL 保留字作为表名
- 【强制】字段名使用小写字母+下划线
- 【强制】布尔类型字段使用 `is_xxx` 命名
- 【强制】主键字段统一使用 `id`
- 【强制】字符集：`utf8mb4`，排序规则：`utf8mb4_general_ci` 或 `utf8mb4_unicode_ci`

**示例：**

```sql
-- 正例 - 标准建表语句
CREATE TABLE `t_user`
(
    `id`          BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键',
    `user_name`   VARCHAR(50)  NOT NULL COMMENT '用户名',
    `email`       VARCHAR(100) NOT NULL COMMENT '邮箱',
    `is_active`   TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否激活',
    `create_time` DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time` DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- 反例 - 表名使用大写、缺少注释、字符集错误
CREATE TABLE User
(
    ID       BIGINT      NOT NULL AUTO_INCREMENT,
    UserName VARCHAR(50) NOT NULL,
    PRIMARY KEY (ID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
```

### 字段规约

- 【强制】必选字段：`id`、`create_time`、`update_time`
- 【推荐】`create_time` 使用 `DEFAULT CURRENT_TIMESTAMP`
- 【推荐】`update_time` 使用 `ON UPDATE CURRENT_TIMESTAMP`
- 【强制】小数类型使用 `DECIMAL`
- 【强制】存储字符串使用 `VARCHAR`、`CHAR`，避免使用 `TEXT`

**示例：**

```sql
-- 正例 - 金额使用 DECIMAL
`amount`
DECIMAL(10, 2) NOT NULL COMMENT '金额'

-- 反例 - 金额使用 DOUBLE（精度丢失）
`amount` DOUBLE NOT NULL COMMENT '金额'

-- 正例 - 枚举使用 TINYINT
`status` TINYINT NOT NULL DEFAULT 0 COMMENT '状态：0-待支付，1-已支付'

-- 反例 - 枚举使用 VARCHAR
`status` VARCHAR(20) NOT NULL COMMENT '状态'
```

### 索引规约

- 【强制】主键使用 `BIGINT` 自增，**禁止使用 UUID** 作为主键
- 【强制】业务唯一字段必须建立唯一索引，命名格式：`uk_字段名`
- 【强制】区分度高的字段建立普通索引，命名格式：`idx_字段名`
- 【推荐】联合索引字段数不超过5个
- 【推荐】遵循最左前缀原则
- 【推荐】避免冗余索引

**示例：**

```sql
-- 正例 - 索引命名规范
PRIMARY KEY (`id`),
UNIQUE KEY `uk_email` (`email`),
KEY `idx_user_name` (`user_name`),
KEY `idx_create_time_status` (`create_time`, `status`);

-- 反例 - 使用 UUID 作为主键
`id`
VARCHAR(36) NOT NULL COMMENT '主键'

-- 反例 - 冗余索引
KEY `idx_a_b` (`a`, `b`),
KEY `idx_a` (`a`);  -- 冗余，已被 idx_a_b 覆盖
```

### SQL 语句规约

- 【强制】禁止使用 `SELECT *`，必须明确指定字段
- 【强制】超过三个表禁止 JOIN，需拆分为多次查询
- 【强制】`IN` 操作元素数量控制在 1000 以内
- 【推荐】分页查询优化，大偏移量使用游标或延迟关联
- 【强制】禁止在 WHERE 条件中对字段进行函数操作（导致索引失效）
- 【推荐】避免 `OR` 连接条件，使用 `UNION ALL` 代替
- 【强制】使用 `count(*)` 或 `count(1)` 统计行数，避免 `count(列名)`

**示例：**

```sql
-- 反例 - SELECT *
SELECT *
FROM t_user
WHERE id = 1;

-- 正例 - 明确指定字段
SELECT id, user_name, email
FROM t_user
WHERE id = 1;

-- 反例 - 超过 3 表 JOIN
SELECT *
FROM t_order o
         JOIN t_user u ON o.user_id = u.id
         JOIN t_product p ON o.product_id = p.id
         JOIN t_category c ON p.category_id = c.id
         JOIN t_brand b ON p.brand_id = b.id;

-- 正例 - 拆分查询
SELECT id, user_id, product_id
FROM t_order
WHERE id = 1;
-- 再单独查询用户和商品信息

-- 反例 - 大偏移量性能差
SELECT *
FROM t_user LIMIT 1000000, 10;

-- 正例 - 使用游标分页
SELECT *
FROM t_user
WHERE id > 1000000 LIMIT 10;

-- 反例 - WHERE 中对字段使用函数（索引失效）
WHERE DATE(create_time) = '2024-01-01'

-- 正例 - 范围查询（可使用索引）
WHERE create_time >= '2024-01-01 00:00:00'
  AND create_time < '2024-01-02 00:00:00'

-- 反例 - count(列名) 会忽略 NULL 值
SELECT count(email)
FROM t_user;

-- 正例 - count(*) 统计所有行
SELECT count(*)
FROM t_user;
```

### ORM 映射规约（MyBatis）

- 【强制】使用 `#{}` 预编译，禁止使用 `${}` 传递用户输入
- 【推荐】复杂查询必须使用 ResultMap
- 【推荐】避免使用自动映射

**示例：**

```xml
<!-- 正例 - 使用 #{} 预编译 -->
<select id="getUserById" resultType="User">
    SELECT id, user_name, email
    FROM t_user
    WHERE id = #{id}
</select>

        <!-- 反例 - 使用 ${} 字符串拼接，SQL 注入风险 -->
<select id="getUserById" resultType="User">
SELECT id, user_name, email
FROM t_user
WHERE id = ${id}
</select>

        <!-- 正例 - 使用 ResultMap -->
<resultMap id="UserResultMap" type="User">
<id property="id" column="id"/>
<result property="userName" column="user_name"/>
<result property="email" column="email"/>
</resultMap>

<select id="getUserWithOrders" resultMap="UserResultMap">
SELECT u.id, u.user_name, u.email, o.id as order_id
FROM t_user u
LEFT JOIN t_order o ON u.id = o.user_id
WHERE u.id = #{userId}
</select>
```

### 事务规约

- 【强制】事务粒度要小，避免大事务
- 【推荐】事务方法命名以 `tx` 开头（如 `txCreateOrder`）
- 【强制】查询操作不使用事务

**示例：**

```java
// 正例 - 事务方法命名清晰
@Transactional(rollbackFor = Exception.class)
public void txCreateOrder(Order order) {
    // 创建订单
    // 扣减库存
    // 创建支付记录
}

// 反例 - 查询使用事务
@Transactional(readOnly = true)
public Order getOrderById(Long id) {
    return orderMapper.selectById(id);
}
```

---

## 测试规范

### 基本原则

- 【强制】单元测试必须遵循 **AIR 原则**：
    - **A**utomatic（自动化）：测试必须全自动执行，无需人工干预
    - **I**ndependent（独立性）：测试之间相互独立，不依赖执行顺序
    - **R**epeatable（可重复）：任何环境下运行结果一致

- 【强制】单元测试必须遵循 **BCDE 原则**：
    - **B**order（边界）：测试边界值和极端情况
    - **C**orrect（正确）：测试正确输入的预期输出
    - **D**esign（设计）：按照设计文档编写测试
    - **E**rror（错误）：测试异常输入和错误路径

### 禁止事项

- 【强制】禁止使用 `System.out` 输出人工验证，必须使用断言
- 【强制】禁止在测试中使用 `Thread.sleep()` 模拟等待
- 【强制】禁止测试代码依赖外部资源（网络、数据库等）

**示例：**

```java
// 反例 - 使用 System.out 人工验证
@Test
void test() {
    String result = service.process();
    System.out.println(result);  // 需要人工查看
}

// 正例 - 使用断言自动验证
@Test
void test() {
    String result = service.process();
    assertEquals("expected", result);
}
```

### 测试目录

- 单元测试放在 `src/test/java`
- 目录结构与主代码保持一致
- 每个被测类对应一个测试类

### 测试框架

- 推荐 **JUnit 5**
- 测试类名以被测类名加 `Test` 结尾
- 测试方法使用 `@Test` 注解

### 测试命名

- 【推荐】使用具有可读性的方法名
- 【推荐】命名风格：`givenX_whenY_thenZ` 或 `should_Y_when_X`
- 【推荐】使用 `@DisplayName` 提供中文描述

**示例：**

```java

@Test
@DisplayName("给定有效用户ID，当查询用户时，返回正确的用户对象")
void givenValidUserId_whenFindById_thenReturnUser() {
    // Given
    Long userId = 1L;
    User expectedUser = new User(userId, "张三");
    when(mockRepository.findById(userId)).thenReturn(Optional.of(expectedUser));

    // When
    User actualUser = userService.getUserById(userId);

    // Then
    assertNotNull(actualUser);
    assertEquals("张三", actualUser.getName());
    verify(mockRepository).findById(userId);
}

@Test
@DisplayName("给定无效用户ID，当查询用户时，抛出异常")
void givenInvalidUserId_whenFindById_thenThrowException() {
    // Given
    Long userId = -1L;

    // When & Then
    assertThrows(IllegalArgumentException.class, () -> {
        userService.getUserById(userId);
    });
}
```

### 覆盖率与范围

- 【推荐】目标覆盖率：**70%～80%** 以上
- 【强制】核心业务逻辑覆盖率不低于 **80%**
- 【推荐】重点测试复杂逻辑、输入验证、异常分支
- 【推荐】关注极端值和无效输入

### 隔离与独立性

- 【强制】单元测试应相互独立，可并行执行
- 【强制】使用 Mock 框架（如 Mockito）模拟外部依赖
- 【强制】避免测试间相互影响
- 【推荐】每个测试方法测试一个场景

**示例：**

```java

@ExtendWith(MockitoExtension.class)
class UserServiceTest {

    @Mock
    private UserRepository userRepository;

    @InjectMocks
    private UserService userService;

    @BeforeEach
    void setUp() {
        // 每个测试前重置状态
    }

    @AfterEach
    void tearDown() {
        // 每个测试后清理资源
    }
}
```

### 测试数据管理

- 【推荐】使用 `@BeforeEach` 准备测试数据
- 【推荐】使用 `@AfterEach` 清理测试数据
- 【强制】数据库测试使用事务回滚

**示例：**

```java

@SpringBootTest
@Transactional  // 测试完成后自动回滚
class UserRepositoryTest {

    @Autowired
    private UserRepository userRepository;

    @Test
    void saveUser_shouldPersist() {
        User user = new User("test@example.com");
        userRepository.save(user);
        assertNotNull(user.getId());
    }
    // 事务回滚，不会影响数据库
}
```

### 参数化测试

- 【推荐】使用 JUnit 5 的 `@ParameterizedTest` 减少重复代码

**示例：**

```java

@ParameterizedTest
@ValueSource(strings = {"", " ", "  "})
@DisplayName("空白字符串应该验证失败")
void validate_shouldFail_whenBlankString(String input) {
    assertFalse(validator.isValid(input));
}

@ParameterizedTest
@CsvSource({
        "1, 2, 3",
        "0, 0, 0",
        "-1, 1, 0"
})
@DisplayName("加法运算测试")
void add_shouldReturnCorrectSum(int a, int b, int expected) {
    assertEquals(expected, calculator.add(a, b));
}
```

---

## 依赖管理

### 构建工具

- 使用 Maven 或 Gradle
- 所有依赖显式声明版本号

### Maven 依赖管理

- 使用 `<dependencyManagement>` 或 **BOM** 集中管理版本
- 各模块引入依赖时可省略版本号
- 统一升级版本，避免冲突

### 版本策略

- 遵循 **语义化版本**（SemVer）：`MAJOR.MINOR.PATCH`
- MAJOR：向后不兼容的更改
- MINOR：向后兼容的新功能
- PATCH：缺陷修复
- 使用 Git 标签（如 `v1.2.3`）标注发布版本

### 依赖更新

- 定期检查并更新第三方依赖
- 使用 Maven Versions Plugin、Dependabot 等工具
- 避免使用已知有安全漏洞的版本

---

## 安全与健壮性建议

### 权限校验

- 【强制】用户敏感数据操作必须进行**水平越权**校验
- 【强制】验证当前用户只能操作自己的数据

**示例：**

```java
// 正例 - 水平越权校验
public Order getOrder(Long orderId) {
    Order order = orderMapper.selectById(orderId);
    if (order == null) {
        throw new NotFoundException("订单不存在");
    }

    // 校验当前用户是否有权限访问该订单
    Long currentUserId = SecurityContext.getCurrentUserId();
    if (!order.getUserId().equals(currentUserId)) {
        throw new ForbiddenException("无权访问该订单");
    }

    return order;
}

// 反例 - 没有越权校验
public Order getOrder(Long orderId) {
    return orderMapper.selectById(orderId);  // 任何人都可以查看任意订单
}
```

### 敏感数据脱敏

- 【强制】手机号、身份证、银行卡等敏感信息禁止明文展示
- 【强制】日志中禁止输出敏感数据

**示例：**

```java
// 正例 - 敏感数据脱敏
public class DesensitizeUtils {

    /**
     * 手机号脱敏：138****8888
     */
    public static String maskPhone(String phone) {
        if (phone == null || phone.length() < 11) {
            return phone;
        }
        return phone.substring(0, 3) + "****" + phone.substring(7);
    }

    /**
     * 身份证脱敏：110***********1234
     */
    public static String maskIdCard(String idCard) {
        if (idCard == null || idCard.length() < 18) {
            return idCard;
        }
        return idCard.substring(0, 3) + "***********" + idCard.substring(14);
    }

    /**
     * 邮箱脱敏：t***@example.com
     */
    public static String maskEmail(String email) {
        if (email == null || !email.contains("@")) {
            return email;
        }
        int atIndex = email.indexOf("@");
        if (atIndex <= 1) {
            return email;
        }
        return email.charAt(0) + "***" + email.substring(atIndex);
    }
}

// 反例 - 日志输出敏感信息
logger.

info("用户注册成功, phone={}, idCard={}",phone, idCard);

// 正例 - 日志脱敏
logger.

info("用户注册成功, phone={}, idCard={}",
     DesensitizeUtils.maskPhone(phone), 
    DesensitizeUtils.

maskIdCard(idCard));
```

### 输入验证

- 【强制】对所有外部输入进行严格验证和清洗
- 【强制】防止 SQL 注入、XSS 等攻击
- 【强制】敏感数据安全存储，不在日志中明文输出

**示例：**

```java
// 正例 - 参数校验
public void createUser(@Valid CreateUserRequest request) {
    // 使用 JSR-303 注解自动校验
}

// 正例 - 手动校验
public void updateUser(Long userId, String name) {
    Objects.requireNonNull(userId, "userId 不能为空");
    if (userId <= 0) {
        throw new IllegalArgumentException("userId 必须大于 0");
    }
    if (StringUtils.isBlank(name)) {
        throw new IllegalArgumentException("name 不能为空");
    }
    // 防止 XSS：对输入进行转义
    name = HtmlUtils.htmlEscape(name);
}
```

### 密码存储

- 【强制】密码必须使用强哈希算法存储（如 BCrypt、Argon2）
- 【强制】禁止明文存储密码
- 【强制】禁止使用 MD5、SHA1 等弱哈希

**示例：**

```java
// 正例 - 使用 BCrypt
@Service
public class PasswordService {
    private final BCryptPasswordEncoder encoder = new BCryptPasswordEncoder();

    public String encryptPassword(String rawPassword) {
        return encoder.encode(rawPassword);
    }

    public boolean matches(String rawPassword, String encodedPassword) {
        return encoder.matches(rawPassword, encodedPassword);
    }
}

// 反例 - 使用 MD5
String password = DigestUtils.md5Hex(rawPassword);  // 不安全
```

### Web 安全防护

- 【强制】表单和 AJAX 提交必须执行 **CSRF** 安全验证
- 【强制】URL 外部重定向传入的目标地址必须执行**白名单过滤**
- 【强制】关键业务（支付、下单、短信）必须实现**防重放**机制（如 nonce、token、验证码）

**示例：**

```java
// 正例 - 重定向白名单校验
public void redirect(String url, HttpServletResponse response) throws IOException {
    if (!isValidUrl(url)) {
        throw new IllegalArgumentException("非法重定向地址");
    }
    response.sendRedirect(url);
}

private boolean isValidUrl(String url) {
    // 校验域名是否在白名单内
    return DomainWhitelist.contains(extractDomain(url));
}
```

### 空值处理

```java
public void setName(String name) {
    this.name = Objects.requireNonNull(name, "name 不能为空");
}
```

- 【推荐】尽量避免返回 `null`
- 【推荐】使用 `Optional<T>` 明确表达可能为空的返回值
- 【强制】使用 `Objects.requireNonNull` 检查参数

### 线程安全

- 【推荐】优先设计无状态或不可变的类
- 【强制】共享可变状态使用合适的并发控制：
    - `synchronized`
    - 显式锁
    - `volatile`
    - `java.util.concurrent` 原子类/线程安全集合
- 【强制】避免竞态条件

### 异常安全

- 【强制】使用 try-with-resources 管理可关闭资源
- 【强制】确保文件、网络连接等及时释放
- 【强制】捕获异常时保证资源不泄露

### 健壮原则

- 【强制】对边界值和异常输入有明确处理逻辑
- 【强制】永远不要假设数据正确无误
- 【强制】做合理的错误检查

---

## 设计规约

### 设计评审要求

- 【强制】存储方案和底层数据结构设计需要获得评审一致通过
- 【强制】设计评审必须沉淀为设计文档
- 【推荐】评审内容包括：存储介质选型、表结构设计、存取性能评估、扩展性考虑

### UML 建模规约

- 【强制】业务对象状态超过 **3 个**，必须使用**状态图**表达，明确触发条件
- 【强制】功能调用链路涉及对象超过 **3 个**，必须使用**时序图**表达
- 【强制】模型类超过 **5 个**且存在复杂依赖关系，必须使用**类图**表达
- 【强制】涉及 User 超过一类且 UseCase 超过 5 个，必须使用**用例图**

**示例：**

```mermaid
// 状态图示例 (Mermaid)
stateDiagram-v2
    [*] --> PENDING
    PENDING --> PAID : 支付成功
    PENDING --> CLOSED : 超时未付
    PAID --> SHIPPED : 发货
    SHIPPED --> COMPLETED : 确认收货
    CLOSED --> [*]
    COMPLETED --> [*]
```

### 设计原则（SOLID）

- 【推荐】单一职责原则（SRP）：一个类只负责一个职责
- 【推荐】开闭原则（OCP）：对扩展开放，对修改关闭
- 【推荐】里氏替换原则（LSP）：子类可以替换父类
- 【推荐】接口隔离原则（ISP）：使用多个小接口而非一个大接口
- 【推荐】依赖倒置原则（DIP）：依赖抽象而非具体实现

**示例：**

```java
// 正例 - 单一职责
public class UserService {
    public void createUser(User user) {
    }

    public User getUserById(Long id) {
    }
}

public class OrderService {
    public void createOrder(Order order) {
    }

    public Order getOrderById(Long id) {
    }
}

// 反例 - 一个类负责多个职责
public class UserService {
    public void createUser(User user) {
    }

    public void createOrder(Order order) {
    }

    public void sendEmail(Email email) {
    }
}

// 正例 - 依赖倒置（依赖接口）
public class OrderService {
    private final PaymentService paymentService;  // 接口

    public OrderService(PaymentService paymentService) {
        this.paymentService = paymentService;
    }
}

// 反例 - 依赖具体实现
public class OrderService {
    private final AlipayServiceImpl paymentService;  // 具体实现
}
```

### 设计模式使用

- 【推荐】单例模式：确保线程安全（双重检查锁、静态内部类、枚举）
- 【推荐】工厂模式：创建复杂对象
- 【推荐】策略模式：消除大量 if-else
- 【推荐】模板方法模式：定义算法骨架
- 【推荐】代理模式：AOP、RPC

**示例：**

```java
// 正例 - 策略模式消除 if-else
public interface PaymentStrategy {
    void pay(PaymentRequest request);
}

public class AlipayStrategy implements PaymentStrategy {
    @Override
    public void pay(PaymentRequest request) {
        // 支付宝支付逻辑
    }
}

public class WechatPayStrategy implements PaymentStrategy {
    @Override
    public void pay(PaymentRequest request) {
        // 微信支付逻辑
    }
}

// 使用策略
public class PaymentService {
    private final Map<String, PaymentStrategy> strategyMap;

    public void pay(String paymentType, PaymentRequest request) {
        PaymentStrategy strategy = strategyMap.get(paymentType);
        strategy.pay(request);
    }
}

// 反例 - 大量 if-else
public void pay(String paymentType, PaymentRequest request) {
    if ("alipay".equals(paymentType)) {
        // 支付宝支付逻辑
    } else if ("wechat".equals(paymentType)) {
        // 微信支付逻辑
    } else if ("unionpay".equals(paymentType)) {
        // 银联支付逻辑
    }
    // ...
}
```

### 缓存设计规约

- 【推荐】缓存数据需设置过期时间
- 【推荐】缓存 Key 使用统一前缀，便于管理
- 【推荐】缓存更新策略：先更新数据库，再删除缓存
- 【推荐】缓存穿透：对不存在的 Key 也缓存空值
- 【推荐】缓存雪崩：过期时间加随机值

**示例：**

```java
// 正例 - 缓存 Key 统一前缀
public class CacheKeyConstants {
    public static final String USER_PREFIX = "user:";
    public static final String ORDER_PREFIX = "order:";

    public static String userKey(Long userId) {
        return USER_PREFIX + userId;
    }
}

// 正例 - 先更新数据库，再删除缓存
public void updateUser(User user) {
    userMapper.updateById(user);
    redisTemplate.delete(CacheKeyConstants.userKey(user.getId()));
}

// 正例 - 缓存空值防止穿透
public User getUserById(Long userId) {
    String key = CacheKeyConstants.userKey(userId);
    User user = redisTemplate.opsForValue().get(key);
    if (user != null) {
        return user;
    }

    user = userMapper.selectById(userId);
    if (user != null) {
        redisTemplate.opsForValue().set(key, user, 30, TimeUnit.MINUTES);
    } else {
        // 缓存空值，防止穿透
        redisTemplate.opsForValue().set(key, NULL_USER, 5, TimeUnit.MINUTES);
    }
    return user;
}
```

### 接口设计规约

- 【推荐】接口返回值不要包含业务逻辑判断的标识，使用 HTTP 状态码
- 【推荐】接口幂等性：GET、PUT、DELETE 操作应保证幂等
- 【推荐】避免接口过度设计，不要为了扩展而扩展

**示例：**

```java
// 正例 - 使用 HTTP 状态码
@DeleteMapping("/users/{id}")
public ResponseEntity<Void> deleteUser(@PathVariable Long id) {
    userService.deleteUser(id);
    return ResponseEntity.noContent().build();  // 204 No Content
}

// 反例 - 返回值包含业务标识
@DeleteMapping("/users/{id}")
public ApiResponse<Boolean> deleteUser(@PathVariable Long id) {
    boolean success = userService.deleteUser(id);
    return ApiResponse.success(success);
}
```

### 存储方案选型

- 【推荐】MySQL：结构化数据、事务支持、复杂查询
- 【推荐】Redis：缓存、分布式锁、计数器
- 【推荐】MongoDB：非结构化数据、文档存储
- 【推荐】Elasticsearch：全文搜索、日志分析

---

## AI 代码生成指引

### 可读性与清晰性

- 优先考虑代码清晰和可读性
- 避免过度"巧妙"而晦涩难懂的写法
- 代码要**自解释**，命名有描述性

### 单一职责

- 函数、方法和类职责单一（**SRP**）
- 复杂功能拆分为多个小模块
- 相关逻辑组织在一起

### 避免重复与简单优先

- 遵循 **DRY**（不要重复自己）
- 保持代码简单直接（**KISS** 原则）
- 不必追求过度抽象或极致优化

### 可维护性和扩展性

- 使用接口和抽象解耦模块
- 便于未来扩展和单元测试
- 避免紧耦合设计
- 遵循 **SOLID** 设计原则

### 错误处理与日志

- 遵循异常处理规范
- 生成有意义的错误信息
- 避免吞掉异常
- 必要时添加日志输出

### 注释与文档

- 加入适当注释和文档模板
- 解释"为什么"选择该实现
- 使用 TODO 注释标记待完成工作

---

## 使用示例

调用本 skill 时可以指定具体规范类型：

```
请按照 Java 命名约定编写这个类
检查这段代码的异常处理是否符合规范
帮我写符合规范的 Javadoc 注释
这个方法的命名符合 Java 规范吗
```

或直接描述需求，会自动应用相应规范。

---

## 代码规范示例参考

- [Java 代码规范示例](references/examples.md)

---

## 规范级别说明

本规范中使用以下级别标识：

- **【强制】**：必须遵守，否则可能导致严重问题
- **【推荐】**：建议遵守，提升代码质量和可维护性
- **【参考】**：供参考的最佳实践，可根据实际情况调整

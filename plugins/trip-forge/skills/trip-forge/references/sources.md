# 权威信息源清单

本文件为 TripForge **调研阶段**提供按信息类型分类的权威站点与**经实测的取数方法**，目的是：让 LLM 联网核实时直接用对的平台和方法，**不必反复试错、费时费 token**。
内容写什么见 `template.md`，HTML 设计见 `assets/report-template.html`，本文件只管「去哪查、怎么查」。

> **核验说明：** 本清单所有方法均于 **2026-06-15 实测**（WebSearch / WebFetch 实跑，测试用例：烟台 / 北京、东京 / 巴黎 / 纽约）。下表的 URL 模式与查询写法都验证过能取到数据；网址与反爬策略会变，调研时以实际可达为准。

## 一、可信分级（结论可信度）

| 标签 | 含义 | 使用规则 |
| --- | --- | --- |
| 🏛️ **官方权威** | 运营方 / 政府 / 景区 / 航司 / 气象台官方 | 结论可直接采信，仍注明来源与核验日期 |
| 🛒 **主流平台** | 预订 / 聚合 / 点评平台 | 价格、营业时间、班次须与 🏛️ 官方或第二来源**交叉验证**后才采用 |
| 💬 **UGC 社区** | 用户生成内容（攻略 / 笔记 / 问答 / 短视频） | **默认含大量营销软广、刷量好评**，不代表真实情况。**仅用于发现线索**，须逐条交叉验证；**不得直接作为结论写入正文** |

## 二、访问方式（怎么才取得到，决定省不省 token）

| 标签 | 含义 | 操作 |
| --- | --- | --- |
| 🌐 **可直抓** | WebFetch 某 URL（含 JSON 接口）直接返回数据，实测有效 | 直接 WebFetch 目标 URL 模式 |
| 🔍 **走搜索** | 站点反爬 / 动态 / 需交互，直接抓首页拿不到 | **不要抓首页**；WebSearch（必要时带 `allowed_domains`）拿快照与深层 URL，再视情 WebFetch 深层页 |
| 📱 **App / 登录墙** | 网页基本取不到 | 只能靠搜索引擎快照；UGC 按营销甄别处理，勿直引 |

## 三、核心方法 = 两段式「搜索 → 深抓」+ 实测可用的取数路径

> **省 token 铁律：** 标 🔍 / 📱 的站点**绝不直接 WebFetch 首页/搜索页**（多返回验证页、空白、JS 占位或仅话题标题）。先 WebSearch 拿线索/深层 URL，需要细节再 WebFetch 深层内容页。`<...>` 占位符用搜到的真实值替换。

**下表每条都经 2026-06-15 实测可取到数据：**

| 信息类型 | 方式 | 实测可用的 URL 模式 / 查询写法 | 能拿到 |
| --- | --- | --- | --- |
| 天气·国内 | 🌐 | `www.nmc.cn/publish/forecast/<省码>/<城市拼音>.html`、`qweather.com/weather/<拼音>-<id>.html`、`www.weather.com.cn/weather/<城市编码>.shtml` | 7 天逐日+逐3小时预报 |
| 天气·海外 | 🌐 | 美国 `forecast.weather.gov/MapClick.php?lat=<纬>&lon=<经>`；日本 `www.jma.go.jp/bosai/forecast/data/forecast/<区域码>.json`（JSON）；全球 windy.com / accuweather | 多日预报、风浪 |
| 高铁·国内 | 🌐 | `trains.ctrip.com/TrainSchedule/<甲>-<乙>/gaotie/`（**双向**，甲乙用城市拼音） | 车次/时刻/二等座票价 |
| 高铁·海外 | 🔍 | WebSearch `<A> to <B> train timetable fare`（命中 NaviTime/trip.com/trainline）；**bahn.de 首页抓不到** | 时刻/票价/时长 |
| 机票 | 🌐+🔍 | 时刻：`flights.ctrip.com/international/schedule/<出发码>-<到达码>.html`；价格区间：WebSearch `<甲> 到 <乙> 机票 价格` | 航班号/时刻/航司 + 价格区间 |
| 路线耗时·国内 | 🔍 | WebSearch `<出发> 到 <目的> 打车 多长时间 多少钱 公交`（命中本地宝/政府/攻略） | 概略耗时+费用+公交线路 |
| 路线耗时·海外 | 🔍 | WebSearch `<A> to <B> transit time fare`（命中 **Rome2Rio** rome2rio.com） | 多方式耗时+票价 |
| 门票/开放/预约 | 🔍 | WebSearch `<景点> 开放时间 门票 预约 官网`（国内命中景区官网+本地宝；海外命中景点官网，如 louvre.fr） | 票价/开放时间/闭馆日/预约规则 |
| 潮汐/赶海 | 🔍 | WebSearch `<地点> <年月> 潮汐表 赶海 退潮时间`（命中潮汐表精灵 `eisk.cn/Tides/<id>.html?date=`） | 涨退潮时刻/赶海窗口 |
| 日出日落 | 🌐 | `api.sunrise-sunset.org/json?lat=<纬>&lng=<经>&date=<YYYY-MM-DD>`（JSON，**返回 UTC，需转当地时**） | 日出/日落/各级暮光 |
| 餐饮·国内 | 🔍 | `allowed_domains:["dianping.com"]` 搜 → WebFetch `m.dianping.com/discovery/<id>`；榜单 `www.amap.com/ranking/<城市>` | 店名/营业时间/招牌菜/人气榜 |
| 餐饮·海外 | 🔍 | `allowed_domains:["tripadvisor.com"]` 搜 `<城市> <品类> restaurant price`；Google Maps 商户 | 店名/评分/价格区间 |
| 酒店 | 🔍 | WebSearch `<片区> 酒店 推荐 价格`（国内深链 `hotels.ctrip.com/hotels/<id>.html`；海外命中 tripadvisor/trip.com/kayak） | 酒店名/片区/价格区间 |
| 攻略/避坑（UGC） | 🔍 | `allowed_domains:["xiaohongshu.com"]` / `["mafengwo.cn"]` 搜 `<城市> 攻略 / 避雷` | 候选点位/避雷线索（须甄别） |

> **抓不到的（别浪费 token）：** 抖音正文（仅话题标题）、美团域名搜（仅团购广告）、点评 `dishes/list`、高德/百度/Booking/bahn.de 首页（JS/反爬）、**reddit.com（被搜索爬虫屏蔽，allowed_domains 直接报错）**。
>
> **通用原则：** 同一条易变信息，🏛️ 官方 > 🛒 平台 > 💬 UGC；至少交叉核验两处；搜到的快照可能非实时，价格/营业时间标 ⚠️ 回官方二次确认；无法核实标 `❓`，不得编造。

------

## 四、分类信息源明细

### 1 · 天气与气象（☀️ 强依赖点位排程的依据）

- 🌐🏛️ 国内：中国天气网 weather.com.cn、中央气象台 nmc.cn、和风天气 qweather.com —— 均**实测可直抓** 7 天预报
- 🌐🏛️ 海外：美国 weather.gov（lat/lon 直抓）、日本 jma.go.jp（JSON 接口）、AccuWeather；🔍 windy.com（风浪，走搜索）

### 2 · 火车 / 高铁

- 🌐🛒 国内：携程 `trains.ctrip.com/TrainSchedule/<甲>-<乙>/gaotie/` —— **实测双向可直抓**车次/时刻/票价，最省事
- 🔍🏛️ 国内购票：12306 `www.12306.cn` —— 官方购票与余票，站本身需交互，**仅作下单口**
- 🔍🛒 海外：WebSearch 命中 NaviTime（日本）、trip.com、trainline（欧洲）；**bahn.de 首页 JS 抓不到**

### 3 · 机票 / 航班

- 🌐🛒 时刻表：`flights.ctrip.com/international/schedule/<出发码>-<到达码>.html` —— **实测可直抓**航班号/起降/航司/机型
- 🔍🛒 价格区间：WebSearch 路线（命中携程/去哪儿/Skyscanner），出经济舱区间+航司
- 🔍🏛️ 航班实时动态（延误）：飞常准 variflight、航司 App —— 计划用搜索时刻即可，**实时状态属用户出行当天事项**

### 4 · 地图 / 路线耗时

- 🔍🏛️ 国内：WebSearch `<A> 到 <B> 打车 时间 费用 公交`（命中本地宝/政府/攻略），出概略耗时+费用+公交线路号
- 🔍🏛️ 海外：WebSearch 命中 **Rome2Rio**，出多方式耗时+票价
- ⚠️ **实时路况/精确导航**无零配置抓取法 → 报告给概略耗时并标 ⚠️，提示用户出行时用高德/百度/Google Maps App 实时查

### 5 · 景点门票 / 开放预约 / 文旅官方

- 🔍🏛️ 国内：WebSearch `<景点> 开放时间 门票 预约 官网`（命中景区官网如 dpm.org.cn + 本地宝）；文旅政策查 mct.gov.cn / 各省文旅厅
- 🔍🏛️ 海外：WebSearch 命中景点官网（louvre.fr 等）、GetYourGuide、Klook
- ⚠️ 实名预约名额/当日余票属实时，标 ⚠️ 让用户提前在官方小程序/官网抢

### 6 · 酒店住宿

- 🔍🛒 国内：WebSearch `<片区> 酒店/民宿 推荐 价格`（出具体酒店名+片区+价格区间，深链 `hotels.ctrip.com/hotels/<id>.html`）
- 🔍🛒 海外：WebSearch 命中 tripadvisor / trip.com / kayak / booking 快照，出价格区间+代表酒店
- ⚠️ **精确房价与余房属实时**，报告给片区建议+价格区间并标 ⚠️，下单让用户在携程/Booking App 查实时

### 7 · 餐饮（营业时间 / 人均 / 口碑）

- 🔍🛒 国内：大众点评 **`allowed_domains:["dianping.com"]` 搜 → WebFetch `m.dianping.com/discovery/<id>`**（店名/营业时间/招牌菜/人气榜）；高德美食榜 `www.amap.com/ranking/<城市>`。**点评仅作参照之一**，评分受刷单影响，结合本地口碑与避雷搜索交叉
- 🔍🛒 海外：`allowed_domains:["tripadvisor.com"]`（**实测出店名/评分/价格**，如一兰 4.5★ $6-7）、Google Maps 商户
- ⛔ 美团域名搜（仅团购广告）、抖音（仅话题标题）——不作取数源；美团店铺细节走点评 discovery

### 8 · 潮汐 / 日出日落 / 赶海（呼应「看景诉求」）

- 🔍🛒 潮汐：WebSearch 命中潮汐表精灵 `eisk.cn/Tides/<id>.html?date=` / tidescn.com，出涨退潮时刻与赶海窗口
- 🌐🛒 日出日落：`api.sunrise-sunset.org/json?lat=&lng=&date=` JSON 接口，**返回 UTC 需转当地时**
- 🏛️ 国家海洋预报台 nmefc.cn —— 海浪/风暴潮官方背景

### 9 · 综合攻略 / 避坑（💬 仅发现线索，须交叉验证）

- 🔍💬 国内：小红书 `allowed_domains:["xiaohongshu.com"]`、马蜂窝 `allowed_domains:["mafengwo.cn"]` —— **实测出候选点位/路线/避雷线索**
- 🔍💬 海外：TripAdvisor 论坛、Lonely Planet、马蜂窝海外版
- ⛔ **Reddit `reddit.com` 被搜索爬虫屏蔽（allowed_domains 直接 400 报错），不可用**；海外 UGC 改走 TripAdvisor / 小红书海外笔记

### 营销帖甄别（国内外社交平台同理，写入前先过筛）

社交平台（小红书 / 抖音 / 马蜂窝 / TikTok / Instagram 等）充斥**探店软广、恰饭推广、刷量好评、摆拍滤镜**，与真实体验经常脱节。命中以下信号**视为营销线索而非事实**，必须降权并交叉验证：

- **通篇无缺点、全程彩虹屁**，只夸不提任何短板 / 排队 / 性价比问题；
- **统一话术 / 同款文案 / 同款机位**短期集中出现；
- **强引导消费**：带门店定位、团购链接、优惠码、"私我领券"、"报我名字有折扣"；
- **图文与实物不符**：重滤镜摆拍、"小众秘境"实为人挤人；
- **博主属性可疑**：探店带货号而非普通游客，主页清一色商单。

**甄别动作：** 主动搜「X 避雷 / 踩雷 / 不推荐 / 难吃」与好评对冲；优先本地人视角；要求多个互不关联来源印证；可核实项回 🏛️ 官方 / 🛒 平台确认；存疑按 `❓` 处理，**宁缺毋滥**。

------

## 五、信息缺口（无零配置可搜索源，须显式告知用户）

以下信息**无法靠 WebSearch/WebFetch 稳定取到**，报告中给出可搜到的「计划值」并标 ⚠️，明确提示用户在对应 App 内实时确认：

| 缺口 | 现状 | 退路 |
| --- | --- | --- |
| 实时路况 / 精确导航耗时 | 概略耗时可搜，实时车流不可得 | 给概略值 ⚠️，让用户出行用地图 App 实时查 |
| 酒店精确房价 / 当日余房 | 价格区间与代表酒店可搜 | 给区间 ⚠️，下单用携程/Booking App |
| 机票精确票价 / 余位 | 价格区间+时刻可搜 | 给区间 ⚠️，下单用航司/携程 App |
| 航班实时延误状态 | 计划时刻可搜 | 出行当天用飞常准/航司 App |
| 景点当日预约余量 | 票价/规则可搜 | 提前用官方小程序/官网抢，标 ⚠️ |
| Reddit 海外 UGC | 被搜索爬虫屏蔽，不可用 | 改用 TripAdvisor 论坛 / 小红书 / 马蜂窝 |

> 这些缺口属**实时/交易类**数据，本就不应写死进攻略；制定方案时用「计划值 + ⚠️ 出行前确认」处理即可，不影响行程框架。

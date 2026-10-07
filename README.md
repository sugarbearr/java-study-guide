# Java 入门到面试指南

> 🌐 **在线阅读**：<https://sugarbearr.github.io/java-study-guide/>（Astro + AstroPaper 主题；学习进度按浏览器域名保存，练习场左下角可「导出/导入进度」迁移）

一套基于五个优质站点整合的 **Java 后端自学路线 + 知识手册 + 面试冲刺** 三合一指南：

| 站点 | 在这套指南中的角色 |
|------|--------------------|
| [廖雪峰 Java 教程](https://liaoxuefeng.com/books/java/introduction/index.html) | 系统入门教材：边读边敲，覆盖语法到 Spring 全家桶 |
| [慕课网《Java入门第一季》](https://www.imooc.com/learn/85) | 零基础免费视频（5 小时），适合完全没编程经验时先看 |
| [JavaGuide](https://javaguide.cn/home.html) | 面试导向的知识点与八股题库，面试篇的主要来源 |
| [pdai.tech Java 全栈知识体系](https://pdai.tech/) | 原理与体系图（并发/JVM/数据库/中间件/架构），进阶篇的主要来源 |
| [码工具 Java 8 中文 API](https://www.matools.com/api/java8) | 随手查类和方法签名的 API 速查手册 |

---

## 怎么用这套指南

**1. 零基础 → 从头学**：打开 [ROADMAP.md](ROADMAP.md) 看总路线，然后从 [01-入门篇](01-入门篇/01-环境搭建与基础语法.md) 逐文件推进，配合 [STUDY-TRACKER.md](STUDY-TRACKER.md) 打卡。每个文件都按「学习目标 → 知识点 → 动手实践 → 面试题 → 资料」组织：先读资料清单里的廖雪峰对应章节，再回来看知识点提纲，做完动手实践，最后用面试题自测。

**2. 有基础 → 查漏补缺**：直接翻 [STUDY-TRACKER.md](STUDY-TRACKER.md)，把每个条目当自测题，不会的再进对应文件补。

**3. 面试冲刺 → 三件事**：过 [两份八股速查清单](07-面试篇/01-Java高频八股速查.md) + 刷 [选择填空题库](07-面试篇/05-选择填空题库.md)（应用内在线作答、错题重练）+ 复盘 [中间件](04-中间件篇/01-Redis.md) 与 [高并发场景题](06-分布式与高并发篇/02-高并发系统设计.md)。

---

## 目录导航

### 基础能力（先修）

| 文件 | 内容 |
|------|------|
| [01-入门篇/01-环境搭建与基础语法](01-入门篇/01-环境搭建与基础语法.md) | JDK/IDEA、基本类型、流程控制、方法、数组 |
| [01-入门篇/02-面向对象与核心类](01-入门篇/02-面向对象与核心类.md) | 封装继承多态、equals/hashCode、String、包装类、枚举、BigDecimal |
| [01-入门篇/03-集合与泛型](01-入门篇/03-集合与泛型.md) | Collection/Map 体系、ArrayList/HashMap 原理、泛型与 PECS |
| [01-入门篇/04-异常-IO-反射-注解](01-入门篇/04-异常-IO-反射-注解.md) | 异常体系、流与序列化、反射、动态代理、自定义注解 |
| [01-入门篇/05-Lambda-Stream与Java8新特性](01-入门篇/05-Lambda-Stream与Java8新特性.md) | 函数式接口、Stream、Optional、Java 8~21 版本脉络 |

### 深入 Java

| 文件 | 内容 |
|------|------|
| [02-进阶篇/01-多线程与并发编程](02-进阶篇/01-多线程与并发编程.md) | JMM、synchronized/volatile、线程池、JUC、ThreadLocal |
| [02-进阶篇/02-JVM核心](02-进阶篇/02-JVM核心.md) | 内存区域、GC 与收集器、类加载、调优与排查 |
| [02-进阶篇/03-IO模型与网络编程](02-进阶篇/03-IO模型与网络编程.md) | TCP/HTTP、BIO/NIO/AIO、零拷贝、Netty |

### 数据库与框架

| 文件 | 内容 |
|------|------|
| [03-数据库篇/01-MySQL基础与SQL实战](03-数据库篇/01-MySQL基础与SQL实战.md) | SQL 全量语法、连接查询、JDBC 到 ORM |
| [03-数据库篇/02-索引-事务-锁与调优](03-数据库篇/02-索引-事务-锁与调优.md) | B+ 树、MVCC、三大日志、慢 SQL、分库分表 |
| [05-框架篇/01-Spring核心](05-框架篇/01-Spring核心.md) | IoC/AOP、Bean 生命周期、事务、循环依赖、SpringMVC |
| [05-框架篇/02-SpringBoot实战](05-框架篇/02-SpringBoot实战.md) | 自动配置原理、统一返回/异常/校验、第一个完整项目 |
| [05-框架篇/03-MyBatis](05-框架篇/03-MyBatis.md) | 动态 SQL、缓存、MyBatis-Plus、Mapper 原理 |
| [05-框架篇/04-SpringCloud微服务](05-框架篇/04-SpringCloud微服务.md) | Nacos、OpenFeign、Gateway、Sentinel |

### 中间件（重点篇）

| 文件 | 内容 |
|------|------|
| [04-中间件篇/01-Redis](04-中间件篇/01-Redis.md) | 五大类型、持久化、缓存三兄弟、分布式锁、哨兵/集群 |
| [04-中间件篇/02-RabbitMQ](04-中间件篇/02-RabbitMQ.md) | AMQP 模型、消息可靠性、死信队列、延迟队列 |
| [04-中间件篇/03-Kafka](04-中间件篇/03-Kafka.md) | 分区与消费组、ACK/ISR、为什么快 |
| [04-中间件篇/04-RocketMQ](04-中间件篇/04-RocketMQ.md) | 事务消息、顺序/延迟消息、三大 MQ 选型对比 |
| [04-中间件篇/05-Elasticsearch](04-中间件篇/05-Elasticsearch.md) | 倒排索引、DSL 查询、数据同步 |
| [04-中间件篇/06-ZooKeeper与Nacos](04-中间件篇/06-ZooKeeper与Nacos.md) | 注册/配置中心、Watcher、AP/CP |
| [04-中间件篇/07-Nginx](04-中间件篇/07-Nginx.md) | 反向代理、负载均衡、动静分离、限流 |
| [04-中间件篇/08-MongoDB](04-中间件篇/08-MongoDB.md) | 文档模型、CRUD 与聚合、选型场景 |

### 架构与求职

| 文件 | 内容 |
|------|------|
| [06-分布式与高并发篇/01-分布式理论基础](06-分布式与高并发篇/01-分布式理论基础.md) | CAP/BASE、一致性哈希、分布式 ID/锁/事务 |
| [06-分布式与高并发篇/02-高并发系统设计](06-分布式与高并发篇/02-高并发系统设计.md) | 限流熔断降级、分库分表、秒杀系统设计 |
| [07-面试篇/01-Java高频八股速查](07-面试篇/01-Java高频八股速查.md) | Java 基础/集合/并发/JVM/Spring 自测清单（约 93 题） |
| [07-面试篇/02-数据库与中间件面试速查](07-面试篇/02-数据库与中间件面试速查.md) | MySQL/Redis/MQ/ES/网络/OS 自测清单（约 82 题） |
| [07-面试篇/03-算法刷题路线](07-面试篇/03-算法刷题路线.md) | 专题刷题顺序、200 题清单、手撕模板 |
| [07-面试篇/04-简历与求职指南](07-面试篇/04-简历与求职指南.md) | 简历写法、项目 STAR、各轮面试侧重 |
| [07-面试篇/05-选择填空题库](07-面试篇/05-选择填空题库.md) | 90 题（选择 64 + 填空 26）覆盖全部章节；应用内支持「📖 章节小考」「🎲 乱序」「🔁 只做错题」 |
| [07-面试篇/06-考点详略表](07-面试篇/06-考点详略表.md) | 每章标注 🔴 必考精通 / 🟡 高频掌握 / 🟢 了解即可 + 时间紧时的取舍清单 |

### 总览

| 文件 | 内容 |
|------|------|
| [ROADMAP.md](ROADMAP.md) | 总路线图、三档时间规划、过关标准 |
| [STUDY-TRACKER.md](STUDY-TRACKER.md) | 全知识点打卡清单 + 周复盘模板 |

---

## 三条贯穿始终的主线

1. **项目线**：入门完成后做一个 `todo-list` REST API（见 SpringBoot 实战篇），学完 MyBatis 后把它接入数据库，学完中间件后演进成一个「带缓存 + 消息队列 + 搜索」的商城 demo，最后用秒杀设计串起高并发知识。面试讲项目时，这套演进过程本身就是亮点。
2. **算法线**：从进阶篇开始每天 2~3 题，按 [算法刷题路线](07-面试篇/03-算法刷题路线.md) 的专题推进，总量目标 200 题。
3. **面试线**：每学完一个文件，先做文件末尾的高频面试题自测；面试篇的八股清单在冲刺期每天过一遍。

## 约定

- 每个文件的「🔗 推荐资料」只指向上面五个站点（均已验证可访问），外部资料以这五个站为骨架，需要官方文档时自行延伸。
- 学习进度一律记在 [STUDY-TRACKER.md](STUDY-TRACKER.md)，勾选即可。
- 建议时长按「每天 2~3 小时」估算，全程约 6~7 个月；赶时间可看 ROADMAP 里的加速方案。

## 仓库结构与技术栈

- **站点**：Astro 7 + [AstroPaper](https://github.com/satnaing/astro-paper) 主题（Tailwind CSS 4 + Pagefind 搜索）。文章内容在 `src/content/posts/`，由 `app/migrate-astro.py` 从根目录分篇 md 生成（注入 frontmatter、改写内链）。
- **练习场**：`src/pages/practice.astro`（八股闪卡 / 选择填空 / 综合大考 / 进度打卡），数据由 `app/migrate-astro.py` 生成到 `src/data/guide-app.json`。
- **离线版**：根目录 `index.html` 为单文件离线应用，由 `app/build.py` 生成，双击即用。

## 本地开发与更新

```bash
# 修改根目录的 md 内容后：
python3 app/migrate-astro.py   # 同步到 Astro 内容集合 + 练习场数据
npm run build                  # 构建到 dist/（本地预览：npm run dev 或 npm run preview）

# 离线单文件版（可选）：
python3 app/build.py           # 重新生成根目录 index.html

# 发布：
git add -A && git commit -m "更新内容" && git push   # Actions 自动部署到 GitHub Pages
```

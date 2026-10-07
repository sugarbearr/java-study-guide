---
title: "学习进度打卡表"
description: "用法：每条即一个自测点。能独立完成/讲清才算打勾；一个文件的条目全部打勾 = 该篇过关。阶段过关标准见 ROADMAP.md"
pubDatetime: 2026-08-20T09:00:00
tags:
  - "总览"

featured: true
draft: false
---

> 用法：每条即一个自测点。能独立完成/讲清才算打勾；一个文件的条目全部打勾 = 该篇过关。阶段过关标准见 [ROADMAP.md](/java-study-guide/posts/ROADMAP/)。

## ① 入门篇

### [01-环境搭建与基础语法](/java-study-guide/posts/01-环境搭建与基础语法/)
- [ ] 能解释 JDK/JRE/JVM 关系，并完成 JDK + IDEA 安装
- [ ] 8 种基本类型、类型转换、运算符用过一遍
- [ ] 流程控制 + 方法 + 重载练熟（九九乘法表、猜数字）
- [ ] 数组遍历、排序、Arrays 工具
- [ ] 能讲清「Java 只有值传递」

### [02-面向对象与核心类](/java-study-guide/posts/02-面向对象与核心类/)
- [ ] 封装/继承/多态各写出一个例子
- [ ] 能对比接口与抽象类、重写与重载
- [ ] equals 与 hashCode 的关系讲得清
- [ ] String 不可变、StringBuilder、Integer 缓存
- [ ] 枚举、BigDecimal、java.time 用法

### [03-集合与泛型](/java-study-guide/posts/03-集合与泛型/)
- [ ] 画出 Collection/Map 两棵树
- [ ] ArrayList 扩容、与 LinkedList 的选型
- [ ] HashMap put 流程、扩容、1.7 vs 1.8
- [ ] 遍历中安全删除元素
- [ ] 泛型通配符与 PECS

### [04-异常-IO-反射-注解](/java-study-guide/posts/04-异常-IO-反射-注解/)
- [ ] 异常体系与 try-with-resources
- [ ] 字节/字符流、缓冲流拷贝对比
- [ ] 序列化与 serialVersionUID
- [ ] 反射获取 Class 并操作字段方法
- [ ] 自定义注解 + 反射解析跑通

### [05-Lambda-Stream与Java8新特性](/java-study-guide/posts/05-Lambda-Stream与Java8新特性/)
- [ ] 四大函数式接口
- [ ] Stream 分组/过滤/汇总一套连招
- [ ] map vs flatMap 讲得清
- [ ] Optional 正确用法
- [ ] Java 8→21 版本脉络一句话各自说得出

## ② 进阶篇

### [01-多线程与并发编程](/java-study-guide/posts/01-多线程与并发编程/)
- [ ] 线程 6 种状态与流转
- [ ] volatile 能解决什么、不能解决什么
- [ ] synchronized vs Lock
- [ ] 线程池 7 参数 + 执行流程 + 拒绝策略
- [ ] ThreadLocal 内存泄漏原因
- [ ] CAS 与 ABA
- [ ] ConcurrentHashMap 1.7 vs 1.8

### [02-JVM核心](/java-study-guide/posts/02-JVM核心/)
- [ ] 五块运行时数据区及各自 OOM
- [ ] 对象何时进老年代
- [ ] GC Roots 与四种引用
- [ ] G1 的特点、CMS 为何被淘汰
- [ ] 类加载五阶段与双亲委派
- [ ] CPU 100% 排查流程（jps→top→jstack）
- [ ] 用 jmap/jstack 实际分析过一次

### [03-IO模型与网络编程](/java-study-guide/posts/03-IO模型与网络编程/)
- [ ] 三次握手/四次挥手及原因
- [ ] TCP vs UDP 选型
- [ ] BIO/NIO/AIO 区别与 NIO 三大件
- [ ] 零拷贝是什么
- [ ] Netty 为什么快

## ③ 数据库篇

### [01-MySQL基础与SQL实战](/java-study-guide/posts/01-MySQL基础与SQL实战/)
- [ ] Docker 起过 MySQL
- [ ] 字段类型选择（char/varchar、datetime/decimal）
- [ ] 连接查询与子查询练熟
- [ ] 说出 SQL 逻辑执行顺序
- [ ] 学生选课库 10 道 SQL 全部独立完成

### [02-索引-事务-锁与调优](/java-study-guide/posts/02-索引-事务-锁与调优/)
- [ ] 为什么用 B+ 树（对比三种结构）
- [ ] 聚簇索引、回表、覆盖索引、最左前缀
- [ ] 索引失效场景列举 5 个以上
- [ ] ACID、四个隔离级别、MVCC
- [ ] redo/undo/binlog 各自作用
- [ ] 用 explain 优化过慢 SQL
- [ ] 读写分离与分库分表思路

## ④ 框架篇

### [01-Spring核心](/java-study-guide/posts/01-Spring核心/)
- [ ] IoC/DI 是什么、解决什么
- [ ] Bean 生命周期与作用域
- [ ] AOP 原理（JDK 代理 vs CGLIB）
- [ ] @Transactional 失效场景
- [ ] 循环依赖与三级缓存
- [ ] SpringMVC 请求流程

### [02-SpringBoot实战](/java-study-guide/posts/02-SpringBoot实战/)
- [ ] 自动配置原理
- [ ] yml 多环境与配置优先级
- [ ] 统一返回 + 全局异常 + 参数校验
- [ ] todo-list 项目完成并通过验收清单

### [03-MyBatis](/java-study-guide/posts/03-MyBatis/)
- [ ] #{} vs ${} 与 SQL 注入
- [ ] 动态 SQL 标签熟练
- [ ] 一级/二级缓存与二级缓存的风险
- [ ] Mapper 接口无需实现类的原理
- [ ] MyBatis-Plus 条件构造器/分页/乐观锁

### [04-SpringCloud微服务](/java-study-guide/posts/04-SpringCloud微服务/)
- [ ] 微服务拆分的收益与代价
- [ ] Nacos 注册 + 配置热更新
- [ ] OpenFeign 声明式调用与超时
- [ ] Gateway 路由与全局过滤器
- [ ] Sentinel 限流熔断配置过

## ⑤ 中间件篇

### [01-Redis](/java-study-guide/posts/01-Redis/)
- [ ] 五大类型各自的使用场景
- [ ] RDB vs AOF vs 混合持久化
- [ ] 过期删除与内存淘汰策略
- [ ] 穿透/击穿/雪崩现象+方案
- [ ] 缓存与数据库一致性方案
- [ ] Redisson 分布式锁 + 看门狗
- [ ] 主从/哨兵/Cluster 区别
- [ ] Spring Boot 整合 demo 跑通

### [02-RabbitMQ](/java-study-guide/posts/02-RabbitMQ/)
- [ ] 四种交换机与路由
- [ ] 消息不丢全链路（confirm/持久化/ACK/死信）
- [ ] 幂等消费方案
- [ ] 延迟队列两种实现
- [ ] Spring Boot 收发 demo 跑通

### [03-Kafka](/java-study-guide/posts/03-Kafka/)
- [ ] Topic/Partition/Replica/消费组概念
- [ ] ACK 级别与 ISR
- [ ] 分区内有序怎么保证
- [ ] 为什么快（顺序写/零拷贝/批量）
- [ ] 命令行 + Spring Boot demo 跑通

### [04-RocketMQ](/java-study-guide/posts/04-RocketMQ/)
- [ ] 架构组件与部署模型
- [ ] 事务消息流程（半消息+回查）
- [ ] 顺序消息实现
- [ ] 延迟消息等级
- [ ] 三大 MQ 选型对比说得出口

### [05-Elasticsearch](/java-study-guide/posts/05-Elasticsearch/)
- [ ] 倒排索引原理
- [ ] Index/Mapping/Shard 概念与 MySQL 对照
- [ ] match/term/bool DSL 练过
- [ ] text vs keyword
- [ ] MySQL→ES 数据同步方案对比

### [06-ZooKeeper与Nacos](/java-study-guide/posts/06-ZooKeeper与Nacos/)
- [ ] ZK znode/临时节点/Watcher
- [ ] ZK 分布式锁原理
- [ ] ZK 的 CP 特性对注册中心意味着什么
- [ ] Nacos 注册 + 配置热更新
- [ ] AP/CP 选型说得清

### [07-Nginx](/java-study-guide/posts/07-Nginx/)
- [ ] 正向 vs 反向代理
- [ ] server/location 配置写过
- [ ] 四种负载均衡策略
- [ ] 动静分离与限流 limit_req
- [ ] Nginx 与网关的分工

### [08-MongoDB](/java-study-guide/posts/08-MongoDB/)
- [ ] 文档模型与 MySQL 概念对照
- [ ] CRUD 与聚合管道入门
- [ ] 适用与不适用场景
- [ ] ObjectId 与副本集概念

## ⑥ 分布式与高并发篇

### [01-分布式理论基础](/java-study-guide/posts/01-分布式理论基础/)
- [ ] CAP 与 BASE，注册中心的 CP/AP 例证
- [ ] 一致性哈希与虚拟节点
- [ ] 雪花算法结构与时钟回拨
- [ ] 三种分布式锁对比与选型
- [ ] 分布式事务五种方案与选型表
- [ ] 亲手实现雪花算法

### [02-高并发系统设计](/java-study-guide/posts/02-高并发系统设计/)
- [ ] 演进路径一条线讲下来
- [ ] 四种限流算法与实现选型
- [ ] 熔断/降级/限流三者区别
- [ ] 分库分表的问题清单
- [ ] 秒杀系统全链路（含防超卖）
- [ ] Redis+Lua 限流器写过

## ⑦ 面试篇

### [01-Java高频八股速查](/java-study-guide/posts/01-Java高频八股速查/)
- [ ] Java 基础 20 题全部自测通过
- [ ] 集合 15 题全部自测通过
- [ ] 并发 20 题全部自测通过
- [ ] JVM 15 题全部自测通过
- [ ] Spring/SpringBoot 15 题全部自测通过
- [ ] MyBatis 8 题全部自测通过

### [02-数据库与中间件面试速查](/java-study-guide/posts/02-数据库与中间件面试速查/)
- [ ] MySQL 20 题全部自测通过
- [ ] Redis 15 题全部自测通过
- [ ] 消息队列 12 题全部自测通过
- [ ] ES/ZK/Nacos 12 题全部自测通过
- [ ] 网络 15 题全部自测通过
- [ ] 操作系统 8 题全部自测通过

### [03-算法刷题路线](/java-study-guide/posts/03-算法刷题路线/)
- [ ] 前六个专题完成（数组/链表/栈队列/哈希/二叉树/搜索）
- [ ] 回溯 + 贪心 + 二分完成
- [ ] 动态规划经典类完成
- [ ] 7 个手撕模板能默写
- [ ] 总量达到 200 题、热题 100 完成

### [04-简历与求职指南](/java-study-guide/posts/04-简历与求职指南/)
- [ ] 简历一页定稿
- [ ] 每个项目都有 STAR + 量化结果
- [ ] 技能清单每条都经得起追问
- [ ] 完成 3 次模拟面试（自录/朋友/AI）

### [05-选择填空题库](/java-study-guide/posts/05-选择填空题库/)
- [ ] 48 道选择题全部做过（应用「📝 选择填空练习」）
- [ ] 20 道填空题全部做过
- [ ] 最近一轮全部答对（🔁 只做错题时池为空）
- [ ] 累计正确率 ≥ 90%

---

## 每周复盘模板（复制使用）

```markdown
## 第 N 周复盘（MM.DD ~ MM.DD）
- 本周完成：xxx（对应打卡条目）
- 动手产出：xxx（代码/项目进展）
- 面试题自测正确率：xx/xx
- 没搞懂的问题（下周解决）：
  1.
- 算法：完成 x 题，错题：
- 下周计划：
```

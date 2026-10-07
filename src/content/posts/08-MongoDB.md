---
title: "08-MongoDB"
description: "阶段：中间件篇 ｜ 建议时长：2 天 ｜ 前置：MySQL 基础（03-数据库篇）"
pubDatetime: 2026-08-24T11:00:00
tags:
  - "④ 中间件篇"

draft: false
---

> **阶段**：中间件篇 ｜ **建议时长**：2 天 ｜ **前置**：MySQL 基础（03-数据库篇）

## 它是什么，解决什么问题

MongoDB 是**文档型 NoSQL 数据库**，数据以 **BSON**（二进制 JSON）存储，一行可以是一个嵌套任意层级的 JSON 文档。它不要求每条记录字段一致（**schema 灵活**），查询语法面向文档而非 SQL，索引机制却与 MySQL 类似（B+ 树），是"既要灵活结构、又要像数据库一样查询"场景的最优解。

**与 MySQL 概念对照（必须记住）**：

| MongoDB | MySQL | 说明 |
| --- | --- | --- |
| database | database | 库 |
| collection | table | 集合（表），无需建表结构 |
| document | row（一行） | BSON 文档，字段可各不相同 |
| field | column | 字段 |
| `_id` | 主键 | 默认自动生成 ObjectId |
| index | index | B+ 树索引，语法不同思想相同 |

核心差异：MySQL 先定义表结构才能写；MongoDB **随时往集合里塞不同结构的文档**——商品 A 有"颜色"规格、商品 B 有"内存/硬盘"规格，放同一集合毫无压力，这正是关系库做"商品多规格"时的痛点（一堆 NULL 列或 EAV 反范式）。

## 典型使用场景

| 业务场景 | 为什么用它 | 不用的后果 |
| --- | --- | --- |
| 内容管理（文章/评论/CMS） | 文档结构可嵌套，字段增减无需 DDL | MySQL 频繁改表结构，字段大量为 NULL |
| 商品详情聚合 | 标题、规格、图文、扩展属性一个大文档一次查出 | 多表 JOIN 拼装，SQL 复杂且慢 |
| 日志/埋点存储 | 写入吞吐高，字段随业务变化，按 TTL 自动过期 | MySQL 单表暴涨，加字段要 DDL 锁表 |
| 用户画像/标签 | 每个用户标签数不同，文档天然表达 | 关系库做标签需 EAV 多表关联，查询慢 |

**不适用**（同样重要，面试会问）：需要**强事务、多表复杂关联、金额类强一致**的场景（如订单资金、账务系统）→ 用 MySQL。MongoDB 4.0+ 虽支持多文档事务，但性能与生态仍不如关系库，别把它当 MySQL 的替代品。

## 快速上手

### 1. Docker 启动 + mongosh CRUD

```bash
docker run -d --name mongo -p 27017:27017 mongo:7.0
docker exec -it mongo mongosh          # 进入交互式 shell
```

```javascript
use shop                                // 创建/切换库（写数据时才真正创建）

// 增：insertOne / insertMany，无需建表
db.product.insertOne({ name: "华为 Mate60 Pro", brand: "华为", price: 6999,
                       specs: { memory: "12G", storage: "512G" }, tags: ["旗舰", "5G"] })

// 查：find + 条件 + 投影
db.product.find({ brand: "华为" })                                  // 等值
db.product.find({ price: { $gte: 5000, $lte: 8000 } })              // 范围：$gte/$lte/$gt/$lt
db.product.find({ tags: "旗舰" })                                   // 数组包含
db.product.find({}, { name: 1, price: 1, _id: 0 })                  // 只返回指定字段

// 排序分页：sort / skip / limit（跳过前 10 条取 5 条，按价格倒序）
db.product.find().sort({ price: -1 }).skip(10).limit(5)

// 统计
db.product.countDocuments({ brand: "华为" })

// 改：updateOne + $set（只改指定字段，不会覆盖整个文档）
db.product.updateOne({ name: "华为 Mate60 Pro" }, { $set: { price: 6499 } })
db.product.updateOne({ name: "华为 Mate60 Pro" }, { $addToSet: { tags: "卫星通信" } }) // 数组去重追加

// 删
db.product.deleteOne({ name: "华为 Mate60 Pro" })

// 索引：与 MySQL 一样，等值/排序字段要建索引
db.product.createIndex({ brand: 1 })                 // 普通索引
db.product.createIndex({ name: "text" })             // 全文索引
db.log_events.createIndex({ createdAt: 1 }, { expireAfterSeconds: 3600 })  // TTL 自动过期
```

### 2. 聚合管道（MongoDB 版的 GROUP BY + JOIN）

```javascript
// 按品牌统计商品数与均价：$match(过滤) → $group(分组聚合) → $sort(排序)
db.product.aggregate([
  { $match: { price: { $gte: 1000 } } },
  { $group: { _id: "$brand", count: { $sum: 1 }, avgPrice: { $avg: "$price" } } },
  { $sort: { count: -1 } }
])
```

### 3. Spring Boot 整合（MongoTemplate 常用操作）

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-data-mongodb</artifactId>
</dependency>
```

```yaml
spring:
  data:
    mongodb:
      uri: mongodb://localhost:27017/shop
```

```java
@Document(collection = "product")
@Data
public class Product {
    @Id
    private String id;          // 不赋值则自动生成 ObjectId
    private String name;
    private String brand;
    private Double price;
    private Map<String, Object> specs;   // 灵活 schema：任意规格字段
    private List<String> tags;
}

@Service
@RequiredArgsConstructor
public class ProductService {
    private final MongoTemplate mongoTemplate;

    public void demo() {
        // 插入
        Product p = new Product();
        p.setName("小米 14"); p.setBrand("小米"); p.setPrice(4999.0);
        mongoTemplate.save(p);

        // 条件查询：brand=华为 且 price 在 [5000,8000]，按价格倒序
        Query query = new Query(
                new Criteria().andOperator(
                        Criteria.where("brand").is("华为"),
                        Criteria.where("price").gte(5000).lte(8000)))
                .with(Sort.by(Sort.Direction.DESC, "price"))
                .skip(0).limit(10);
        List<Product> list = mongoTemplate.find(query, Product.class);

        // 更新：$set
        mongoTemplate.updateFirst(
                Query.query(Criteria.where("name").is("小米 14")),
                Update.update("price", 4599.0), Product.class);

        // 聚合：按品牌统计
        mongoTemplate.aggregate(
                Aggregation.newAggregation(
                        Aggregation.group("brand").count().as("count"),
                        Aggregation.sort(Sort.Direction.DESC, "count")),
                "product", Document.class);

        // 计数与删除
        long count = mongoTemplate.count(
                Query.query(Criteria.where("brand").is("华为")), Product.class);
        mongoTemplate.remove(Query.query(Criteria.where("price").lt(100)), Product.class);
    }
}
```

## 常用命令 / API 速查

| 操作 | mongosh | MongoTemplate |
| --- | --- | --- |
| 插入 | `insertOne/insertMany` | `save()` / `insert()` |
| 查询 | `find({条件}, {投影})` | `find(Query, Class)` |
| 范围 | `$gte $lte $gt $lt $in $ne` | `Criteria.where(...).gte(...)` |
| 更新 | `updateOne + $set/$inc/$push` | `updateFirst(Query, Update, Class)` |
| 删除 | `deleteOne/deleteMany` | `remove(Query, Class)` |
| 分页 | `sort().skip().limit()` | `Sort / skip / limit` |
| 聚合 | `aggregate([$match, $group])` | `Aggregation.newAggregation(...)` |
| 索引 | `createIndex({field: 1})` | `@Indexed` / `@CompoundIndex` 注解 |

## 核心进阶

### 1. ObjectId 结构（面试常考）

`_id` 默认生成的 ObjectId 共 **12 字节**：

| 部分 | 长度 | 含义 |
| --- | --- | --- |
| 时间戳 | 4 字节 | 创建时间（秒级），所以 ObjectId 本身就带创建时间且**大致按时间递增** |
| 随机值 | 5 字节 | 机器 + 进程标识（同一实例唯一） |
| 递增计数 | 3 字节 | 同一秒内的自增序号 |

价值：主键生成**不依赖数据库协调**（应用端即可生成），天然趋势递增，适合做索引键。

### 2. 副本集与分片（一句话级别即可）

- **副本集（Replica Set）**：一主多从自动选主——主节点写、从节点读，主挂了从节点自动选举接管，等同 MySQL 主从 + MHA 的开箱即用版；生产最小 3 节点（PSS 或 PSA）；
- **分片（Sharding）**：按分片键（如 user_id 哈希）把 collection 水平拆到多台机器，解决单机容量与写入瓶颈，mongos 路由组件对应用透明；
- 一句话：**副本集保高可用，分片保扩展性**。

### 3. 事务与一致性

- 4.0 起支持**多文档事务**（副本集内），用法与 Spring `@Transactional` 类似；
- 但单文档操作本身就是原子的（一条 BSON 的更新不会写一半），所以"把强一致需求的关联数据放进同一个文档"是 MongoDB 的惯用设计，比开事务更高效；
- 默认读自己写的没问题，但跨文档、跨集合的一致性需求仍是 MySQL 的主场。

## 高频面试题

**Q：MongoDB 和 MySQL 怎么选型？**
- MySQL：强事务（资金/订单）、多表关联、结构固定的业务主数据；
- MongoDB：schema 灵活多变（内容管理、商品多规格、日志埋点）、文档自包含一次读取、写入吞吐优先；
- 常见组合：MySQL 存核心交易数据，MongoDB 存内容/详情/日志类数据。

**Q：什么场景适合 MongoDB？不适合什么场景？**
- 适合：字段不固定或嵌套复杂、单文档整体读写、大容量写多读多（CMS、商品详情、日志、画像）；
- 不适合：强事务与金额一致性、复杂多表 JOIN（`$lookup` 能力有限且慢）；
- 4.0+ 有事务但不是它的主场，选型要明确"文档优先"的设计思路。

**Q：ObjectId 是什么结构？**
- 12 字节：4 字节秒级时间戳 + 5 字节机器/进程随机值 + 3 字节自增计数；
- 应用端生成，无需数据库协调；带时间信息、趋势递增，利于索引；
- 这也是 MongoDB 写入性能好的原因之一（主键不冲突、不回页）。

**Q：副本集和分片分别解决什么问题？**
- 副本集：一主多从 + 自动选主，解决**高可用**与读写分离；
- 分片：按分片键水平拆分数据到多节点，解决**容量与写入扩展**；
- 生产通常"分片集群的每个分片本身是一个副本集"。

## 推荐资料

| 资料 | 说明 | 链接 |
| --- | --- | --- |
| JavaGuide MongoDB 面试题 | 面试导向的知识点梳理 | https://javaguide.cn/database/mongodb/mongodb-questions-01.html |
| pdai MongoDB 总览 | MongoDB 知识体系与原理 | https://pdai.tech/md/db/nosql-mongo/mongo.html |
| 廖雪峰 Spring Boot 集成 MongoDB | Spring Boot 整合实操 | https://liaoxuefeng.com/books/java/springboot/index.html |
| pdai 架构知识体系 | NoSQL 在整体架构中的位置 | https://pdai.tech/md/arch/arch-z-overview.html |

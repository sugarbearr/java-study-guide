---
title: "05-Elasticsearch"
description: "阶段：中间件篇 ｜ 建议时长：4 天 ｜ 前置：MySQL 基础（03-数据库篇）、Docker 基础"
pubDatetime: 2026-08-25T08:00:00
tags:
  - "④ 中间件篇"

draft: false
---

> **阶段**：中间件篇 ｜ **建议时长**：4 天 ｜ **前置**：MySQL 基础（03-数据库篇）、Docker 基础

## 它是什么，解决什么问题

Elasticsearch（ES）是基于 Lucene 的**分布式搜索与分析引擎**，核心是**倒排索引**：把文档分词后建立"**词 → 文档 ID 列表**"的映射，查"华为手机"时直接拿到包含这两个词的文档集合，再按**相关度评分**排序——这正是 MySQL 做不好的事。

**ES 与 MySQL 的分工**：

| 对比点 | MySQL | Elasticsearch |
| --- | --- | --- |
| `LIKE '%手机%'` | 前模糊不走索引，**全表扫描** | 分词后命中倒排表，毫秒级 |
| 相关度排序 | 只能按字段值排 | 按 BM25 评分：词频、权重、字段长度综合打分 |
| 复杂聚合分析 | 慢，易拖垮主库 | 倒排+列存 doc_values，聚合飞快 |
| 事务/强一致 | 强项 | 不支持事务，近实时（约 1s 延迟） |

一句话：**MySQL 是"存数据的"，ES 是"查数据的"**。典型架构：MySQL 为主存，数据同步到 ES 专供搜索。

## 典型使用场景

| 业务场景 | 为什么用它 | 不用的后果 |
| --- | --- | --- |
| 商品搜索（电商） | 多关键词分词检索 + 筛选 + 排序 + 高亮 | `LIKE '%xx%'` 全表扫，商品百万级时秒开不可能 |
| 日志分析（ELK） | Filebeat→Kafka→Logstash→ES，集中检索海量日志 | 故障排查只能登机器 grep，效率极低 |
| 站内搜索（文章/简历） | 全文检索 + 相关度排序 + 分词纠错 | 搜索结果不相关，用户体验差 |
| 数据聚合看板 | terms/range 聚合秒级出报表 | MySQL `GROUP BY` 大表慢查询堆积 |

## 快速上手

### 1. Docker 启动（单节点，可选 Kibana）

```bash
docker run -d --name es \
  -p 9200:9200 \
  -e discovery.type=single-node \
  -e ES_JAVA_OPTS="-Xms512m -Xmx512m" \
  -e xpack.security.enabled=false \
  elasticsearch:8.14.0
# 验证：curl http://localhost:9200
# 9200 = REST API 端口；Kibana（可视化，可选）映射 5601 连接 http://host.docker.internal:9200
# 中文分词需安装 IK 插件（镜像内执行 elasticsearch-plugin install analysis-ik 或自制镜像）
```

### 2. REST 风格 CRUD + DSL 查询

```bash
# 建索引 + Mapping：商品名用 text 分词，品牌用 keyword 精确
PUT /product
{
  "mappings": {
    "properties": {
      "name":  { "type": "text",    "analyzer": "ik_max_word", "search_analyzer": "ik_smart" },
      "brand": { "type": "keyword" },
      "price": { "type": "double" },
      "desc":  { "type": "text",    "analyzer": "ik_max_word" }
    }
  }
}

# 写入文档（可指定 id；不指定用自动生成）
POST /product/_doc/1
{ "name": "华为 Mate60 Pro", "brand": "华为", "price": 6999, "desc": "麒麟芯片 支持卫星通信" }
POST /product/_doc/2
{ "name": "小米 14 Ultra",  "brand": "小米", "price": 6499, "desc": "徕卡光学 骁龙芯片" }

# 查询：bool 组合 —— must 打分、filter 不打分可缓存
GET /product/_search
{
  "query": {
    "bool": {
      "must":     [ { "match": { "name": "华为手机" } } ],
      "should":   [ { "match": { "desc": "卫星通信" } } ],
      "filter":   [ { "range": { "price": { "gte": 5000, "lte": 8000 } } } ]
    }
  },
  "highlight": { "fields": { "name": {} } },     // 命中词高亮
  "sort":  [ { "price": "desc" } ],              // 排序
  "from": 0, "size": 10                          // 分页
}
```

| DSL 关键词 | 作用 | 注意 |
| --- | --- | --- |
| `match` | 对 text 分词后检索，参与相关度打分 | 搜索字段用这个 |
| `match_phrase` | 短语匹配，分词后要求**按序相邻** | 更精确，召回更少 |
| `term` | 精确匹配，**不涉及分词** | 只对 keyword/数值/日期字段用 |
| `bool` | 组合：`must`(AND) / `should`(OR) / `must_not` / `filter` | filter 不算分且可缓存，条件过滤放这里 |
| `from/size` | 浅分页 | `from + size <= 10000`，深分页用 `search_after` |

### 3. Spring Boot 整合（Spring Data Elasticsearch）

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-data-elasticsearch</artifactId>
</dependency>
```

```yaml
spring:
  elasticsearch:
    uris: http://localhost:9200
```

```java
@Document(indexName = "product")
@Data
public class Product {
    @Id
    private Long id;
    @Field(type = FieldType.Text, analyzer = "ik_max_word", searchAnalyzer = "ik_smart")
    private String name;
    @Field(type = FieldType.Keyword)     // 品牌精确匹配/聚合，必须是 Keyword
    private String brand;
    @Field(type = FieldType.Double)
    private Double price;
}

public interface ProductRepository extends ElasticsearchRepository<Product, Long> {
    List<Product> findByName(String name);   // 方法名派生查询
}

// 常用操作
@Service
@RequiredArgsConstructor
public class ProductSearchService {
    private final ProductRepository repository;
    private final ElasticsearchOperations operations; // 复杂查询用Criteria/原生DSL

    public void save(Product p) { repository.save(p); }
    public List<Product> search(String keyword) { return repository.findByName(keyword); }
    public long countByBrand(String brand) { return repository.count(); }
}
```

## 常用命令 / API 速查

| 操作 | 命令 |
| --- | --- |
| 查看集群健康 | `GET /_cluster/health`（green/yellow/red） |
| 查看索引 Mapping | `GET /product/_mapping` |
| 删除索引 | `DELETE /product` |
| 按 id 查/删 | `GET/DELETE /product/_doc/1` |
| 批量导入 | `POST /_bulk`（一行动作描述 + 一行文档） |
| 分词测试 | `GET /product/_analyze {"analyzer":"ik_smart","text":"华为手机"}` |
| 聚合统计 | `"aggs": {"brand_count": {"terms": {"field": "brand"}}}` |

**与 MySQL 概念对照**：

| Elasticsearch | MySQL | 说明 |
| --- | --- | --- |
| Index | Table | 一类文档的集合 |
| Document | Row | JSON 文档 |
| Field | Column | 字段 |
| Mapping | Schema | 字段类型定义 |
| Shard（主分片） | 分库分表 | 建索引时定，之后不可改 |
| Replica（副本） | 从库 | 容灾 + 读扩展 |

## 核心进阶

### 1. 倒排索引（面试必问）

- 正排：文档 ID → 内容（MySQL 主键查询）；倒排：**分词后的词条 → 包含该词的文档 ID 列表（posting list）**；
- 写入时对 text 字段分词，为每个词建倒排；查询"华为手机"→ 分词为"华为/手机" → 查两张倒排表 → 取交集/并集 → 按相关度（BM25）排序；
- 词条表有序 + 压缩，查找近似 O(logN)，因此海量文档也能毫秒级检索。

### 2. text vs keyword（高频坑）

- `text`：写入时**分词**建倒排，用于全文检索（match）；不能直接精确匹配/聚合；
- `keyword`：**不分词**，整体作为一个词，用于精确匹配（term）、排序、聚合；
- 经典错误：对 text 字段用 term 查"华为手机"查不到（因为分词后没有"华为手机"这个整体词）；品牌、状态、类别字段必须用 keyword；
- 一个字段可同时要两个能力：`"fields": {"raw": {"type": "keyword"}}`。

### 3. 写入为什么是"近实时"（NRT）

```
写入 → Index Buffer(内存) + translog(事务日志,防丢)
  ↓ refresh（默认每 1s）→ 生成 segment，写入 OS 页缓存 → 此时才可被搜索
  ↓ flush（默认 30min 或 translog 满）→ segment 持久化到磁盘，清空 translog
```

- 所以写入到可搜索**最多有约 1 秒延迟**（`refresh_interval` 可调）；追求实时可设 `refresh_interval=1s` 以下但费性能；
- segment 一旦生成不可修改：删除只是打标记，更新=删旧+插新，这是 ES 更新代价高的根源。

### 4. 深分页问题

- `from + size`：每个分片都要取 `from + size` 条到协调节点排序，`from` 越大代价越高，默认上限 10000；
- 深翻页方案：**`search_after` + PIT（Point in Time）**——用上一页最后一条的排序值做游标，性能稳定，适合"下一页"式翻页；`scroll` 适合一次性导出全量（已不推荐做分页）；
- 产品层面规避：搜索结果只允许翻前 100 页（如 Google）。

### 5. 数据同步方案（MySQL → ES）

| 方案 | 原理 | 优点 | 缺点 |
| --- | --- | --- | --- |
| 同步双写 | 代码里写完 MySQL 写 ES | 简单、实时 | 代码耦合；双写不一致风险 |
| 异步 MQ | 写库后发消息，消费者更新 ES | 解耦、可重试、可靠 | 毫秒~秒级延迟；要处理堆积 |
| canal | 伪装 MySQL 从库订阅 binlog | 对业务零侵入 | 多一套 canal 运维；有延迟 |
| Logstash | 定时按 `update_time` 拉增量 | 纯配置，上手快 | 秒~分钟级延迟；给 DB 带来查询压力 |

生产主流：**MQ 异步同步**或 **canal 订阅 binlog**；要求最终一致再加对账任务。

### 6. 集群

- 主分片数建索引时固定（默认 1），副本可动态调；分片是数据分布与并行的单位；
- 节点角色：master（管理）、data（存数据）、coordinating（协调，所有节点默认兼任）；
- 容量评估经验：单分片建议 20~50GB 以内。

## 高频面试题

**Q：倒排索引是什么？**
- 与正排（ID→文档）相反，倒排是"分词后的词条→文档 ID 列表"；
- 写入时分词建表，查询时对关键词分词后查倒排表，取交集并集再按相关度排序；
- 词典有序查找近似 O(logN)，因此全量数据也能毫秒级检索。

**Q：ES 和 MySQL 怎么选型？**
- 主数据、强事务、多表关联 → MySQL；全文检索、模糊搜索、聚合分析、日志 → ES；
- 典型架构：MySQL 存主数据，异步同步（MQ/canal）到 ES 专供搜索；
- ES 不支持事务、近实时、更新代价高，别当主库用。

**Q：ES 深分页怎么办？**
- `from+size` 每个分片都取前 N 条再归并，代价随 from 线性涨，默认限 10000；
- 翻页用 `search_after` + PIT 游标；全量导出用 scroll（或 search_after）；
- 产品上限制可翻页深度是通用做法。

**Q：text 和 keyword 的区别？**
- text 会分词建倒排，用于 match 全文搜索；keyword 不分词，用于 term 精确匹配、排序、聚合；
- 坑：对 text 字段 term 查整句通常查不到；状态/品牌/分类字段务必用 keyword。

**Q：ES 写入为什么是近实时的？**
- 写入先进内存 buffer + translog；**refresh（默认 1s）** 生成 segment 进入页缓存后才可搜索；
- **flush** 才真正落盘并清 translog；调小 refresh_interval 可降延迟但增加开销；
- segment 不可变，删除/更新是标记与重建，这也解释了 ES 更新昂贵。

## 推荐资料

| 资料 | 说明 | 链接 |
| --- | --- | --- |
| JavaGuide Elasticsearch 面试题 | 面试题合集（部分内容付费，注意甄别） | https://javaguide.cn/database/elasticsearch/elasticsearch-questions-01.html |
| pdai Elasticsearch 总览 | ES 知识体系与原理详解 | https://pdai.tech/md/db/nosql-es/elasticsearch.html |
| 廖雪峰 Spring Boot 集成 ES | Spring Boot 整合实操 | https://liaoxuefeng.com/books/java/springboot/index.html |
| pdai 架构知识体系 | 搜索中间件在架构中的位置 | https://pdai.tech/md/arch/arch-z-overview.html |

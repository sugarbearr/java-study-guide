---
title: "03-Kafka"
description: "阶段：中间件篇 ｜ 建议时长：3 天 ｜ 前置：02-RabbitMQ（理解消息队列基本概念）"
pubDatetime: 2026-08-25T22:00:00
tags:
  - "④ 中间件篇"

draft: false
---

> **阶段**：中间件篇 ｜ **建议时长**：3 天 ｜ **前置**：02-RabbitMQ（理解消息队列基本概念）

## 它是什么，解决什么问题

Kafka 是 LinkedIn 开源的**分布式日志/流处理平台**，Scala+Java 编写，特点是**超高吞吐（单机百万级）、消息按 offset 持久化可回溯**，是日志采集、用户行为埋点、大数据管道（对接 Flink/Spark）领域的事实标准。

**与 RabbitMQ 的定位差异**：RabbitMQ 面向"业务消息"，确认即删；Kafka 面向"数据流"，消息像日志文件一样顺序追加到磁盘，按保留策略（时间/容量）删除，**消费只移动 offset，不删除消息**——所以它能被多个系统反复消费、也能回溯重放。

**核心概念（必须全部搞懂）**：

| 概念 | 含义 |
| --- | --- |
| Broker | 一个 Kafka 服务节点 |
| Topic | 消息的逻辑分类（如 order-topic） |
| Partition | Topic 的物理分片，**并行度和顺序性的基本单位** |
| Replica | 分区副本：1 Leader + N Follower，Leader 负责读写 |
| Consumer Group | 消费组：组内分区分摊、组间广播 |
| offset | 消息在分区内的唯一序号，消费进度就是"提交到了哪个 offset" |

## 典型使用场景

| 业务场景 | 为什么用它 | 不用的后果 |
| --- | --- | --- |
| 日志采集（ELK 前置） | Filebeat→Kafka→Logstash→ES，缓冲+解耦，ES 挂了日志不丢 | 日志直写 ES，高峰打挂 ES 且无法回补 |
| 用户行为埋点 | App/网页 PV/UV 事件流高吞吐写入，下游多系统消费 | 直接写库扛不住峰值，埋点丢失无法追溯 |
| 大数据管道 | Flink/Spark 从 Kafka 消费做实时计算（实时大屏、风控） | 各计算任务直连业务库，互相影响 |
| 大流量削峰 | 秒杀/活动消息排队，消费端按能力处理 | 瞬时流量冲垮下游 |
| 消息回溯/重放 | 数据错了重置 offset 重新消费即可 | 传统 MQ 消费即删，错了只能人工补数 |

## 快速上手

### 1. Docker Compose 单机 KRaft 模式（无需 ZooKeeper）

```yaml
# docker-compose.yml
services:
  kafka:
    image: bitnami/kafka:3.7
    container_name: kafka
    ports:
      - "9092:9092"
    environment:
      - KAFKA_CFG_NODE_ID=0
      - KAFKA_CFG_PROCESS_ROLES=controller,broker      # KRaft：本机既是控制器又是 Broker
      - KAFKA_CFG_LISTENERS=PLAINTEXT://:9092,CONTROLLER://:9093
      - KAFKA_CFG_ADVERTISED_LISTENERS=PLAINTEXT://localhost:9092
      - KAFKA_CFG_LISTENER_SECURITY_PROTOCOL_MAP=CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT
      - KAFKA_CFG_CONTROLLER_QUORUM_VOTERS=0@kafka:9093
      - KAFKA_CFG_CONTROLLER_LISTENER_NAMES=CONTROLLER
```

```bash
docker compose up -d
```

### 2. 命令行创建 Topic、生产、消费

```bash
# 创建 topic：3 个分区
docker exec -it kafka kafka-topics.sh --bootstrap-server localhost:9092 \
  --create --topic order-topic --partitions 3 --replication-factor 1

# 控制台生产（输入一行发一条）
docker exec -it kafka kafka-console-producer.sh \
  --bootstrap-server localhost:9092 --topic order-topic

# 控制台消费（从头消费）
docker exec -it kafka kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 --topic order-topic --from-beginning

# 查看消费组积压
docker exec -it kafka kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 --describe --group order-group
```

### 3. Spring Boot 整合（KafkaTemplate + @KafkaListener）

```xml
<dependency>
    <groupId>org.springframework.kafka</groupId>
    <artifactId>spring-kafka</artifactId>
</dependency>
```

```yaml
spring:
  kafka:
    bootstrap-servers: localhost:9092
    producer:
      key-serializer: org.apache.kafka.common.serialization.StringSerializer
      value-serializer: org.apache.kafka.common.serialization.StringSerializer
      acks: all                        # 等所有 ISR 副本确认，最高可靠
      properties:
        enable.idempotence: true       # 幂等生产者
    consumer:
      group-id: order-group
      auto-offset-reset: earliest      # 无初始位移时从头消费
      key-deserializer: org.apache.kafka.common.serialization.StringDeserializer
      value-deserializer: org.apache.kafka.common.serialization.StringDeserializer
      enable-auto-commit: false        # 关闭自动提交，业务处理完手动提交
    listener:
      ack-mode: manual_immediate
```

```java
@Service
@RequiredArgsConstructor
public class OrderProducer {
    private final KafkaTemplate<String, String> kafkaTemplate;
    private final ObjectMapper objectMapper; // spring-boot-starter-web 自带

    public void send(OrderMsg msg) throws Exception {
        // key = 订单号：相同 key 哈希进同一分区，保证该订单的消息分区内有序
        kafkaTemplate.send("order-topic", msg.getOrderId(), objectMapper.writeValueAsString(msg));
    }
}

@Component
@Slf4j
public class OrderConsumer {
    @KafkaListener(topics = "order-topic", groupId = "order-group")
    public void onMessage(ConsumerRecord<String, String> record, Acknowledgment ack) {
        log.info("partition={}, offset={}, key={}, value={}",
                record.partition(), record.offset(), record.key(), record.value());
        // 业务处理（需幂等：可能重复消费）...
        ack.acknowledge();   // 手动提交位移，防止处理中宕机丢消息
    }
}
```

## 常用命令 / API 速查

| 操作 | 命令 / API |
| --- | --- |
| 创建 topic | `kafka-topics.sh --create --topic t --partitions 3 --replication-factor 2` |
| 查看 topic 详情 | `kafka-topics.sh --describe --topic t`（看分区/Leader/ISR） |
| 扩分区（只能加不能减） | `kafka-topics.sh --alter --topic t --partitions 6` |
| 查看消费积压 | `kafka-consumer-groups.sh --describe --group g`（LAG 列） |
| 重置 offset（回放） | `kafka-consumer-groups.sh --reset-offsets --group g --topic t --to-earliest --execute` |
| 发送消息 | `kafkaTemplate.send(topic, key, value)` |
| 消费消息 | `@KafkaListener(topics = "t", groupId = "g")` |

## 核心进阶

### 1. 分区机制与消息顺序

- **为什么分区**：一个 Topic 的消息水平切到多个 Partition，分布在多个 Broker 上——这是 Kafka 横向扩容和并行消费的根基；
- **分区策略**：指定了 partition 用指定值；有 key 按 `hash(key) % 分区数`；都没有则轮询/粘性分区（sticky，攒批更高效）；
- **顺序保证**：Kafka 只保证**分区内有序**。需要"同一业务实体有序"就按业务 key（如订单号）路由到同一分区；需要全局有序只能 1 个分区（牺牲并行度）；
- 注意：扩分区会改变 key→分区映射，破坏"同 key 同分区"，所以分区数尽量一次规划好。

### 2. 消费组与 Rebalance

- 消费组内**一个分区同一时刻只分配给一个消费者**（组间广播、组内负载均衡）；
- 触发 rebalance 的三种情况：组内**成员增减**（消费者上/下线、宕机）、**分区数变化**、订阅的 topic 变化；
- rebalance 期间整个消费组停止消费（类似 STW），生产环境要避免频繁 rebalance：合理设置 `session.timeout.ms`、`max.poll.interval.ms`，避免消费太慢被踢出；
- 分区分配策略：Range、RoundRobin、Sticky、CooperativeSticky（增量 rebalance，停顿最短）。

### 3. 可靠性三件套

- **acks 三个级别**：`0`（发出即成功，可能丢）、`1`（Leader 写入即成功，Leader 挂了副本没同步则丢）、`all/-1`（等所有 ISR 副本写入，最可靠）；`all` 必须配合 `min.insync.replicas>=2`（至少 2 个副本同步成功），否则退化成"单副本也行"；
- **ISR（In-Sync Replicas）**：与 Leader 保持同步的副本集合，落后的会被踢出 ISR；`all` 只需 ISR 内确认；
- **幂等生产者**（`enable.idempotence=true`）：Broker 用 `<PID, 分区, 序列号>` 去重，解决生产者重试导致的单分区重复写入（不能跨分区跨会话）；跨分区原子写用**事务**（`transactional.id` + `initTransactions`）；
- **位移提交与重复消费**：`enable.auto.commit=true` 按间隔自动提交，处理到一半宕机会**丢消息**（先提交后处理）；手动在**处理完成后提交**则宕机后重读 → **重复消费**。所以工程上"先处理后提交 + 消费端幂等"是标准答案。

### 4. 为什么 Kafka 这么快（高频）

1. **顺序写磁盘**：消息追加到日志文件末尾（append-only），磁盘顺序写速度接近内存；
2. **页缓存（PageCache）**：读写都走 OS 页缓存，命中率高，JVM 不存消息数据（避免 GC 压力）；
3. **零拷贝（sendfile）**：消费者拉取时数据从页缓存直接到网卡，不经过用户态，省 2 次拷贝 2 次上下文切换；
4. **批量 + 压缩**：生产者攒批（`batch.size`/`linger.ms`）后整体压缩（lz4/snappy）发送，网络与磁盘 IO 都按批摊销；
5. **拉模式消费**：Consumer 主动拉取，按自身能力控制速率，天然避免推模式压垮慢消费者。

### 5. 消息积压的应急与根治（实战高频）

- 现象：消费速度追不上生产速度，`kafka-consumer-groups.sh --describe` 的 **LAG（落后位移）持续增大**；
- 应急：扩容消费者实例——**消费者数最多等于分区数**，多出来只会空转；分区数不够时新建多分区 topic，写程序把旧 topic 消息搬过去并行消费；
- 根治：批量拉取（`max.poll.records`）+ 批量落库、消费逻辑异步化、非核心处理降级延后；
- 预防：上线前压测确定"分区数 : 消费者数"配比，对 LAG 配置告警；
- 提交方式坑：`enable.auto.commit=true` 是定时提交位移，与消费进度脱钩，业务系统一律改为手动提交。
- 常见坑：频繁 rebalance（消费耗时超过 `max.poll.interval.ms` 被踢出）会雪上加霜，先调大该参数止血；
- 另一个坑：`kafkaTemplate.send()` 是**异步**的，不 `get()` 阻塞等待或注册回调，发送失败是无感知的——可靠性要求高的场景必须检查发送结果。

## 高频面试题

**Q：Kafka 为什么吞吐量这么高？**
- 顺序写磁盘（append-only log）+ 页缓存，读写都不过 JVM 堆；
- 零拷贝 sendfile，消费路径数据不进用户态；
- 分区并行 + 生产端批量发送与压缩；
- 消费端拉（pull）模式，按消费能力拉取，天然流控。

**Q：Kafka 怎么保证消息不丢不重？**
- 不丢：生产者 `acks=all` + `min.insync.replicas>=2` + 重试；Broker 副本机制；消费者先处理后手动提交 offset；
- 不重（难完全做到）：生产端幂等生产者/事务解决 broker 侧重试重复；消费端必然可能重复（重试、rebalance），**靠业务幂等**（唯一键、去重表）兜底；
- 口诀：生产 acks=all、Broker 副本、消费先处理再提交 + 幂等。

**Q：消费者组是什么机制？什么时候 rebalance？**
- 组内消费者分摊分区（一分区只归一个消费者），组间各自独立消费（广播）；
- 触发：成员上/下线、分区数变化、订阅变化；
- rebalance 期间整组停摆，生产要避免频繁触发；用 Sticky/CooperativeSticky 减少影响。

**Q：Kafka 如何保证消息顺序？**
- 全局只能保证分区内有序；
- 业务上按关键 key（订单号/用户 ID）作为消息 key，哈希进同一分区，同一实体的消息先进先出；
- 消费端同分区由同一线程处理（`max.poll` 单线程消费即可保证）。

**Q：acks=1 会丢消息吗？**
- 会。Leader 写入成功即返回，若 Leader 随即宕机且消息尚未同步给 Follower，新 Leader 上没有这条消息；
- 关键业务用 `acks=all` + `min.insync.replicas=2` + `retries` 调大。

## 推荐资料

| 资料 | 说明 | 链接 |
| --- | --- | --- |
| JavaGuide 消息队列基础 | 消息队列通用知识与选型 | https://javaguide.cn/high-performance/message-queue/message-queue.html |
| pdai 零拷贝 | sendfile/mmap 原理，理解 Kafka 快的关键 | https://pdai.tech/md/java/io/java-io-nio-zerocopy.html |
| 廖雪峰 Spring Boot 集成 Kafka | Spring Boot 整合实操 | https://liaoxuefeng.com/books/java/springboot/index.html |
| pdai 架构知识体系 | 消息队列在整体架构中的位置 | https://pdai.tech/md/arch/arch-z-overview.html |

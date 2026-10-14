# 04-RocketMQ

> **阶段**：中间件篇 ｜ **建议时长**：3 天 ｜ **前置**：02-RabbitMQ、03-Kafka（理解消息队列与分区概念）

## 🧩 它是什么，解决什么问题

RocketMQ 是阿里开源、Java 编写的消息中间件，为**电商级业务场景**而生：吞吐十万级、毫秒级延迟，且把业务最需要的能力做成了原生特性——**事务消息、顺序消息、延迟消息、消息轨迹**。国内大厂（阿里系生态）用得极多，Spring Cloud Alibaba 体系默认 MQ。

核心架构：

```
NameServer（无状态注册中心：Broker 上报路由，客户端来问地址）
   ↑ 注册            │ 发现路由
Broker（Master/Slave，消息存储与转发，存储单元是 CommitLog + ConsumeQueue）
   ↑ ↓
Producer ──发送──> Topic（逻辑分类，物理上由多个 MessageQueue 组成）──投递──> Consumer
```

| 概念 | 含义 | 与 Kafka 对比 |
| --- | --- | --- |
| NameServer | 轻量无状态路由中心 | 类似 ZK 但更简单，无选主 |
| Broker | 存储转发节点 | 主从架构 |
| Topic | 消息主题 | 同 Kafka |
| MessageQueue | Topic 的分区 | 同 Kafka Partition |
| Tag | 消息二级标签，用于过滤 | 类似子主题，Consumer 按 Tag 订阅 |

## 📌 典型使用场景

| 业务场景 | 为什么用它 | 不用的后果 |
| --- | --- | --- |
| 订单创建最终一致（事务消息） | 下单→扣库存/冻积分，用半消息+本地事务保证"库和消息"原子性 | 本地事务成功但消息没发出去，下游永远不知道 |
| 延时发货/超时取消 | 原生延迟消息（18 个等级，5.x 支持任意延迟） | RabbitMQ 要 TTL+死信绕一圈，还有队头阻塞 |
| 积分/优惠券异步发放 | 下单主流程发消息即返回，下游各自消费 | 串行调用下游，下单接口耗时叠加 |
| 电商大促削峰 | 十万级吞吐扛住瞬时下单洪峰 | 数据库被瞬时流量打垮 |

## 🚀 快速上手

### 1. Docker 启动（NameServer + Broker + Dashboard）

```bash
# 1) NameServer
docker run -d --name rmqnamesrv -p 9876:9876 apache/rocketmq:5.3.1 sh mqnamesrv

# 2) Broker（Mac 上用 host.docker.internal 连 NameServer；Linux 用宿主机 IP）
docker run -d --name rmqbroker -p 10911:10911 -p 10909:10909 \
  -e "NAMESRV_ADDR=host.docker.internal:9876" \
  -e "JAVA_OPT_EXT=-Xmx512m -Xms512m" \
  apache/rocketmq:5.3.1 sh mqbroker -n host.docker.internal:9876

# 3) 可视化控制台
docker run -d --name rmqdashboard -p 8081:8080 \
  -e "JAVA_OPTS=-Drocketmq.namesrv.addr=host.docker.internal:9876" \
  apacherocketmq/rocketmq-dashboard:latest
# 控制台：http://localhost:8081
```

### 2. Spring Boot 整合（三种发送方式 + 消费）

```xml
<dependency>
    <groupId>org.apache.rocketmq</groupId>
    <artifactId>rocketmq-spring-boot-starter</artifactId>
    <version>2.3.1</version>
</dependency>
```

```yaml
# application.yml
rocketmq:
  name-server: localhost:9876
  producer:
    group: order-producer-group        # 生产者组（事务消息回查时有用）
    send-message-timeout: 3000
```

```java
@Service
@RequiredArgsConstructor
@Slf4j
public class OrderProducer {
    private final RocketMQTemplate template;

    /** 同步发送：等 Broker 确认，可靠性要求高（订单、支付） */
    public void syncSend(OrderMsg msg) {
        SendResult result = template.syncSend("order-topic", msg);
        log.info("发送状态: {}", result.getSendStatus());
    }

    /** 异步发送：回调通知成功/失败，兼顾吞吐与可靠 */
    public void asyncSend(OrderMsg msg) {
        template.asyncSend("order-topic", msg, new SendCallback() {
            public void onSuccess(SendResult r) { log.info("OK"); }
            public void onException(Throwable e) { log.error("失败，落库补偿", e); }
        });
    }

    /** 单向发送：只管发不等结果，用于日志类消息（可能丢） */
    public void sendOneWay(OrderMsg msg) { template.sendOneWay("order-topic", msg); }

    /** 延迟消息：默认 18 个等级（1s 5s 10s 30s 1m 2m 3m 4m 5m 6m 7m 8m 9m 10m 20m 30m 1h 2h） */
    public void sendDelay(OrderMsg msg) {
        template.syncSend("order-topic",
                MessageBuilder.withPayload(msg).build(), 3000, 3); // level 3 = 10s
    }

    /** 顺序消息：同一 orderId 哈希到同一 MessageQueue，分区内先进先出 */
    public void sendOrderly(OrderMsg msg) {
        template.syncSendOrderly("order-topic", msg, msg.getOrderId());
    }
}

@Component
@RocketMQMessageListener(
        topic = "order-topic",
        consumerGroup = "order-consumer-group",
        consumeMode = ConsumeMode.ORDERLY,     // 顺序消费；默认 CONCURRENTLY 并发消费
        selectorExpression = "TagA || TagB")   // 按 Tag 过滤，"*" 表示全部
@Slf4j
public class OrderConsumer implements RocketMQListener<OrderMsg> {
    @Override
    public void onMessage(OrderMsg msg) {
        log.info("消费: {}", msg.getOrderId()); // 抛异常 = 消费失败，触发重试
    }
}
```

## 🔧 常用命令 / API 速查

| 操作 | 命令 / API |
| --- | --- |
| 控制台 | Dashboard 查看 Topic、消费组、消息轨迹、堆积 |
| 创建 Topic | 控制台创建，或 `sh mqadmin updateTopic -n localhost:9876 -t order-topic -c DefaultCluster` |
| 发送消息 | `template.syncSend(topic, msg)` / `asyncSend` / `sendOneWay` |
| 消费消息 | 类实现 `RocketMQListener<T>`，加 `@RocketMQMessageListener` |
| 消费模式 | `MessageModel.CLUSTERING`（默认，负载均衡）/ `BROADCASTING`（广播） |
| 死信 Topic | `%DLQ%+消费者组名`，重试耗尽后自动进入 |

## 🧠 核心进阶

### 1. 事务消息（面试重点，必须会画流程）

```
Producer                          Broker                         Consumer
   │ ①发送半消息(Half Msg) ────────> │ (对消费者不可见)
   │ <────②ACK 半消息落盘成功────────│
   │ ③执行本地事务(扣库存/下单)
   │ ④Commit/Rollback ────────────> │ Commit: 消息对消费者可见
   │                                │ Rollback: 删除半消息
   │      （若④网络丢失）            │ ⑤定时回查 checkLocalTransaction()
   │ <────⑥回查请求────────────────│    根据本地事务状态返回 COMMIT/ROLLBACK
   │                                │ ⑦消息可见 → 推送给 Consumer 消费
```

- 解决的问题：**"本地事务成功"与"消息发出"的原子性**（先发消息可能事务回滚了消息已出去；先提交事务再发消息可能发送失败）；
- 注意：它只保证**生产端与本地事务的一致**，消费端仍需自己做幂等；
- 回查依据：`@RocketMQTransactionListener` 的 `checkLocalTransaction()` 里反查业务表状态（如订单是否创建成功）。

### 2. 顺序消息

- 全局有序代价大，业务上只需**同一业务 key 有序**（同一订单：创建→支付→发货）；
- 实现：发送时 `syncSendOrderly(topic, msg, orderId)`，相同 key 经哈希进入**同一个 MessageQueue**；消费端 `ConsumeMode.ORDERLY` 用队列级锁单线程消费该队列；
- 注意：消费失败会阻塞当前队列重试，需设置合理的最大重试次数；Broker 宕机切换会短暂破坏顺序。

### 3. 延迟消息

- 4.x 固定 18 个等级（level 1~18，见上方注释），存入内部的 `SCHEDULE_TOPIC_XXXX`，定时任务按等级扫描到期后转回真实 Topic；
- 5.x 基于**时间轮**支持任意时刻延迟（`deliverTimeMs`）；
- 与 RabbitMQ 对比：原生支持、无队头阻塞，这是选 RocketMQ 的常见理由。

### 4. 消费重试与死信、消费模式

- 消费抛异常 → 默认重试 **16 次**，间隔递增（10s 起逐步拉长到 2h），期间消息堆积在 `RETRY_TOPIC`；全部失败进入死信 Topic **`%DLQ%消费者组名`**，人工处理；
- **集群模式**（默认）：组内消费者分摊 MessageQueue，一条消息只被组内一个实例消费；**广播模式**：组内每个实例都消费一遍（如本地缓存刷新），广播模式失败不重试。

### 5. 三大 MQ 对比与选型（必背）

| 维度 | RabbitMQ | Kafka | RocketMQ |
| --- | --- | --- | --- |
| 吞吐量 | 万~十万级 | 百万级 | 十万级 |
| 延迟 | 微秒~毫秒（最低） | 毫秒级 | 毫秒级 |
| 路由能力 | 最强（四种交换机） | 弱（仅 topic/分区） | 中（Topic+Tag） |
| 特色功能 | 延迟(插件)、死信、优先级 | 消息回溯、流处理生态 | 事务消息、顺序消息、延迟消息、消息轨迹 |
| 消息保留 | 确认即删 | 按 offset/时间保留，可回放 | 确认后按时间保留 |
| 语言/社区 | Erlang，社区活跃 | Scala/Java，大数据生态标准 | Java，阿里/国内生态 |
| 典型场景 | 业务系统异步解耦、低延迟场景 | 日志、埋点、大数据管道 | 电商交易、订单等强业务场景 |

选型建议：中小业务系统、需要灵活路由和低延迟 → RabbitMQ；日志流、大数据实时计算、超高吞吐 → Kafka；电商交易类业务、需要事务/顺序/延迟消息 → RocketMQ。没被公司技术栈绑架时，Java 团队业务系统选 RocketMQ 最省心。

## 💼 高频面试题

**Q：RocketMQ 事务消息的流程？**
- 先发**半消息**（消费者不可见）→ Broker ACK → 执行**本地事务** → 根据结果 Commit/Rollback；
- 若 Broker 未收到二次确认，定时**回查**生产者本地事务状态（查业务表）决定提交或回滚；
- 本质：用"半消息+回查"把"本地事务成功"和"消息可达"绑成最终一致；消费端仍要幂等。

**Q：顺序消息怎么保证？**
- 发送端：同一业务 key（订单号）哈希路由到同一个 MessageQueue，队列内天然 FIFO；
- 消费端：`ConsumeMode.ORDERLY`，对队列加锁单线程消费；
- 代价：吞吐下降、消费失败会阻塞队列、Broker 扩缩容会短暂乱序。

**Q：延迟消息是怎么实现的？**
- 4.x：18 个固定等级，消息先写到系统 Topic `SCHEDULE_TOPIC_XXXX`，定时任务按等级扫描，到期后投回真实 Topic；
- 5.x：时间轮支持任意延迟时间；
- 面试可对比：RabbitMQ 用 TTL+死信有队头阻塞，Kafka 原生不支持延迟。

**Q：三大 MQ 怎么选型？**
- 吞吐：Kafka(百万) > RocketMQ(十万) > RabbitMQ(万~十万)；
- 功能：业务功能 RocketMQ 最全（事务/顺序/延迟/轨迹），路由能力 RabbitMQ 最强；
- 场景：日志/大数据管道选 Kafka；低延迟业务解耦选 RabbitMQ；电商交易、需要事务消息选 RocketMQ。

**Q：消费重试机制？**
- 并发消费失败默认重试 16 次，间隔指数递增；期间进入重试 Topic `%RETRY%组名`；
- 耗尽后进入死信 Topic `%DLQ%组名`，需人工/补偿任务处理；
- 广播模式不重试；顺序消费会本地重试并阻塞队列。

## 🔗 推荐资料

| 资料 | 说明 | 链接 |
| --- | --- | --- |
| JavaGuide 消息队列基础 | 消息队列通用知识与可靠性设计 | https://javaguide.cn/high-performance/message-queue/message-queue.html |
| 廖雪峰 Spring Boot 集成消息队列 | Spring Boot 整合 MQ 实操 | https://liaoxuefeng.com/books/java/springboot/index.html |
| JavaGuide 高可用系统设计指南 | 削峰、异步、解耦的系统性设计 | https://javaguide.cn/high-availability/high-availability-system-design.html |
| pdai 架构知识体系 | MQ 在整体架构中的位置 | https://pdai.tech/md/arch/arch-z-overview.html |

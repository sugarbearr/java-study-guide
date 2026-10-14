# 02-RabbitMQ

> **阶段**：中间件篇 ｜ **建议时长**：3 天 ｜ **前置**：01-Redis（中间件基础）、Spring Boot 基础

## 🧩 它是什么，解决什么问题

RabbitMQ 是基于 **AMQP 协议**的消息中间件，Erlang 语言编写，特点是**低延迟、路由灵活、功能完善**，吞吐量万级到十万级，是中小规模业务系统（电商、支付、CRM）最常用的 MQ。

**消息队列解决的三个核心问题**：

1. **异步**：下单后要发短信、加积分、通知仓储——串行要 800ms，发条消息让下游异步消费，主流程 100ms 返回；
2. **解耦**：订单系统不直接调用下游 N 个系统，只发一条"订单已创建"事件，新增订阅方无需改订单代码；
3. **削峰**：秒杀瞬时 10 万请求先排队，消费端按自己的节奏（如每秒 2000 单）处理，保护数据库。

**核心模型（AMQP）**：

```
Producer ──(RoutingKey)──> Exchange ──(Binding 绑定规则)──> Queue ──> Consumer
 生产者                      交换机（不存消息，只路由）        队列（存消息）    消费者
```

关键理解：**生产者永远不直接把消息发到队列，而是发给交换机**，交换机按绑定规则（Binding + RoutingKey）决定投递到哪个队列——这就是 RabbitMQ 路由灵活的原因。

## 📌 典型使用场景

| 业务场景 | 为什么用它 | 不用的后果 |
| --- | --- | --- |
| 订单超时自动取消（延迟消息） | 下单 15 分钟未支付自动关闭，TTL+死信或延迟插件实现 | 定时任务轮询订单表，延迟高、扫表压力大 |
| 下单后异步通知（短信/积分/推送） | 主流程只发消息，多个下游各自订阅 | 串行调用，一个下游超时拖垮下单接口 |
| 秒杀削峰 | 请求先进队列，消费端匀速落库 | 瞬时流量直接打爆 MySQL |
| 系统间事件广播（fanout） | 一次发布，多个系统各自消费 | 新系统接入需改动上游代码，强耦合 |

## 🚀 快速上手

### 1. Docker 启动（带管理台）

```bash
docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3.13-management
# 管理台：http://localhost:15672  账号密码默认 guest/guest
# 5672 = AMQP 通信端口，15672 = Web 管理台端口
```

### 2. Spring Boot 整合（声明队列 + JSON 序列化 + 手动 ACK）

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-amqp</artifactId>
</dependency>
```

```yaml
# application.yml
spring:
  rabbitmq:
    host: localhost
    port: 5672
    username: guest
    password: guest
    publisher-confirm-type: correlated   # 生产者确认（异步 Confirm）
    publisher-returns: true              # 路由不到队列时回调 ReturnCallback
    listener:
      simple:
        acknowledge-mode: manual         # 消费者手动 ACK
        prefetch: 10                     # 每个消费者未确认消息数上限（限流）
```

```java
@Configuration
public class RabbitConfig {
    public static final String ORDER_EXCHANGE = "order.exchange";
    public static final String ORDER_QUEUE    = "order.create.queue";
    public static final String DLX_EXCHANGE   = "order.dlx.exchange";
    public static final String DLQ            = "order.create.dlq";

    @Bean
    public DirectExchange orderExchange() { return new DirectExchange(ORDER_EXCHANGE); }

    /** 业务队列：绑定死信交换机，消费失败的消息转投 DLQ，人工兜底 */
    @Bean
    public Queue orderQueue() {
        return QueueBuilder.durable(ORDER_QUEUE)          // 持久化队列
                .deadLetterExchange(DLX_EXCHANGE)
                .deadLetterRoutingKey("order.dead")
                .build();
    }

    @Bean
    public DirectExchange dlxExchange() { return new DirectExchange(DLX_EXCHANGE); }

    @Bean
    public Queue dlq() { return QueueBuilder.durable(DLQ).build(); }

    @Bean
    public Binding orderBinding() {
        return BindingBuilder.bind(orderQueue()).to(orderExchange()).with("order.create");
    }

    @Bean
    public Binding dlqBinding() {
        return BindingBuilder.bind(dlq()).to(dlxExchange()).with("order.dead");
    }

    /** 默认 SimpleMessageConverter 只支持基本类型；换成 JSON，收发对象都走 JSON */
    @Bean
    public MessageConverter jacksonConverter() { return new Jackson2JsonMessageConverter(); }
}
```

```java
@Service
@RequiredArgsConstructor
@Slf4j
public class OrderProducer {
    private final RabbitTemplate rabbitTemplate;

    public void sendOrderCreated(OrderMsg msg) {
        rabbitTemplate.convertAndSend(RabbitConfig.ORDER_EXCHANGE, "order.create", msg);
        log.info("已发送订单消息: {}", msg.getOrderId());
    }
}

@Component
@RequiredArgsConstructor
@Slf4j
public class OrderConsumer {
    private final ObjectMapper objectMapper; // spring-boot-starter-web 自带

    @RabbitListener(queues = RabbitConfig.ORDER_QUEUE)
    public void onMessage(Message message, Channel channel) throws IOException {
        long tag = message.getMessageProperties().getDeliveryTag();
        try {
            // Jackson2JsonMessageConverter 已配置时，参数直接声明为 OrderMsg 类型即可自动反序列化
            OrderMsg msg = objectMapper.readValue(message.getBody(), OrderMsg.class);
            handle(msg);
            channel.basicAck(tag, false);            // 处理成功才确认
        } catch (Exception e) {
            log.error("消费失败", e);
            // requeue=false：不再回队列，直接转入死信队列，避免无限重投
            channel.basicNack(tag, false, false);
        }
    }
    private void handle(OrderMsg msg) { /* 业务逻辑 */ }
}
```

## 🔧 常用命令 / API 速查

| 操作 | 命令 / API |
| --- | --- |
| 管理台 | http://localhost:15672（guest/guest），查看队列、堆积、消费者 |
| 列出队列 | `docker exec rabbitmq rabbitmqctl list_queues name messages consumers` |
| 创建用户 | `rabbitmqctl add_user app 123456 && rabbitmqctl set_permissions -p / app ".*" ".*" ".*"` |
| 发消息 | `rabbitTemplate.convertAndSend(exchange, routingKey, object)` |
| 收消息 | `@RabbitListener(queues = "xxx")` 标注在方法上 |
| 手动确认 | `channel.basicAck(tag, false)` / 拒绝 `channel.basicNack(tag, false, requeue)` |

**四种交换机**：

| 类型 | 路由规则 | 示例 |
| --- | --- | --- |
| direct | RoutingKey **精确匹配** | `order.create` 只进绑定了该 key 的队列 |
| topic | RoutingKey **模式匹配**：`#` 多级、`*` 一级 | `order.*` 匹配 `order.create`；`order.#` 匹配 `order.create.success` |
| fanout | 广播，忽略 RoutingKey，投给所有绑定队列 | 配置变更通知所有服务实例 |
| headers | 按消息 header 匹配（性能差，少用） | — |

## 🧠 核心进阶

### 1. 消息不丢的全链路（必须会讲）

```
生产者 ──①Confirm确认──> Broker(交换机/队列/消息持久化②) ──> 消费者 ──③手动ACK后才删除
   │                        │ 路由不到队列 → ④备用交换机兜底
   └─ 发送失败重试/记录表补偿 ─┘ 消费失败 → ⑤重试N次后进死信队列，人工处理
```

- **①生产者 Confirm**：消息到达 Broker 后异步回调 `ConfirmCallback`（`publisher-confirm-type: correlated`），失败则重发或落库补偿；`publisher-returns: true` + `ReturnCallback` 捕获"到了交换机但路由不到队列"的消息；
- **②Broker 端持久化**：交换机 `durable`、队列 `durable`、消息 `deliveryMode=2`（用 Spring AMQP 发对象默认持久化），三者缺一不可；配合镜像/仲裁队列防止单机磁盘损坏；
- **③消费者手动 ACK**：`acknowledge-mode: manual`，处理成功才 `basicAck`；未 ACK 时消费者挂掉，消息会重新投递给其他消费者；
- **⑤死信队列（DLX）**：消息被 `nack(requeue=false)`、被拒绝、或 TTL 到期、或队列超长时，转发到死信交换机，最终落在死信队列里由人工/补偿任务处理——**这是排查"消息去哪了"的关键**。

### 2. 幂等消费（重复消费不可避免，必须兜底）

消息**至少一次投递**（At Least Once），网络抖动、ACK 丢失都会导致重复。方案：**唯一消息 ID + 去重表**——

```java
// 发送端：msg.setMessageId(UUID.randomUUID().toString());
// 消费端：先查去重表（业务库一张表，消息ID唯一索引）
if (messageLogMapper.existsByMsgId(msgId)) { channel.basicAck(tag, false); return; } // 已处理过，直接确认
handle(msg);
messageLogMapper.insert(msgId); // 与业务操作放同一事务
```

### 3. 延迟队列的两种实现

- **TTL + 死信**：给队列设 TTL，到期后转入死信交换机实现延迟。缺陷：**队列头阻塞**——前面 10 分钟的消息没消费，后面 1 分钟的到期了也出不来（FIFO 限制）；
- **延迟插件**（推荐）：安装 `rabbitmq_delayed_message_exchange`，交换机类型声明为 `x-delayed-message`，发送时设置 `x-delay`，消息到点才投递，无队头阻塞。

### 4. 其他能力

- **优先级队列**：声明队列时设 `x-max-priority`，高优先级消息优先投递（如 VIP 订单）；
- **集群与高可用**：经典集群只共享元数据不共享消息；镜像队列（classic）每节点全量复制，性能开销大已不推荐；**仲裁队列 Quorum Queue**（3.8+）基于 Raft 多数派写入，官方当前推荐。

## 💼 高频面试题

**Q：四种交换机的区别？**
- direct：RoutingKey 精确匹配；topic：`#`/`*` 模式匹配，最灵活；
- fanout：广播给所有绑定队列，忽略 RoutingKey；headers：按 header 匹配，少用；
- 业务里最常用 direct（点对点）和 topic（多订阅、分级路由）。

**Q：怎么保证消息不丢？（全链路）**
- 生产端：Confirm 确认 + ReturnCallback，失败重发或落库补偿；
- Broker 端：交换机、队列、消息三个层面都持久化，配合仲裁队列防单点；
- 消费端：手动 ACK，处理成功才确认；失败进重试，多次失败进死信队列人工兜底。

**Q：重复消费怎么办？**
- 重复不可避免（At Least Once），要在消费端做幂等；
- 常用：唯一消息 ID + 去重表（消息 ID 加唯一索引，与业务同事务）；或用业务天然幂等键（订单号、`UPDATE ... WHERE status=待处理`）；
- Redis `SETNX msgId` 做轻量去重也可以，但要考虑 Redis 不可用时的兜底。

**Q：死信队列有什么用？**
- 三种进死信的情况：被 nack/reject 且不回队列、TTL 到期、队列超长；
- 用途一：消费失败的兜底容器，避免阻塞正常队列，人工补偿；
- 用途二：配合 TTL 实现延迟队列（订单超时取消）。

**Q：RabbitMQ 和 Kafka 怎么选？**
- 一句话：**业务级消息（低延迟、灵活路由、需要延迟/死信/优先级）选 RabbitMQ；日志流、大数据管道、超高吞吐、消息回溯选 Kafka**；
- RabbitMQ 吞吐万级~十万级、微秒毫秒级延迟、消息确认后即删；Kafka 吞吐百万级、消息按 offset 保留可重复消费，但路由能力弱。

## 🔗 推荐资料

| 资料 | 说明 | 链接 |
| --- | --- | --- |
| JavaGuide 消息队列基础 | 消息队列通用知识：使用场景、可靠性、幂等 | https://javaguide.cn/high-performance/message-queue/message-queue.html |
| JavaGuide 高可用系统设计指南 | 削峰、限流、降级等系统设计视角 | https://javaguide.cn/high-availability/high-availability-system-design.html |
| 廖雪峰 Spring Boot 集成 RabbitMQ | Spring Boot 整合实操 | https://liaoxuefeng.com/books/java/springboot/index.html |
| pdai 架构知识体系 | 异步/解耦/削峰在整体架构中的位置 | https://pdai.tech/md/arch/arch-z-overview.html |

# 01-Redis

> **阶段**：中间件篇 ｜ **建议时长**：4 天 ｜ **前置**：MySQL 基础（03-数据库篇）、Spring Boot 基础

## 🧩 它是什么，解决什么问题

Redis（Remote Dictionary Server）是基于**内存**的 key-value NoSQL 数据库，单机 QPS 可达 10 万+。它是后端面试与实际工作中出现频率最高的中间件，没有之一。

**磁盘数据库 vs 内存数据库**：

| 维度 | MySQL（磁盘） | Redis（内存） |
| --- | --- | --- |
| 数据存放 | 磁盘（B+ 树数据页） | 内存（哈希表/跳表等） |
| 随机读写 | 毫秒级，受磁盘 IO 限制 | 微秒级，10 万级 QPS |
| 定位 | 持久化主存、复杂查询、事务 | 高速读写、缓存、简单结构 |
| 容量 | TB 级 | 受内存限制（单实例不宜过大） |

一句话：**MySQL 负责"存得下"，Redis 负责"跑得快"**。典型架构是 MySQL 为主存，Redis 做缓存层挡住大部分热点读。

**为什么这么快？（高频面试题）**

1. **纯内存操作**：数据在内存中读写，比磁盘快几个数量级；
2. **命令执行单线程**：无锁竞争、无线程上下文切换（6.0 后网络 IO 用多线程，但**命令执行仍是单线程**，不存在并发安全问题）；
3. **IO 多路复用**：基于 epoll 的 Reactor 模型，单线程同时监听大量连接，谁的请求就绪就处理谁；
4. **高效数据结构**：SDS 动态字符串、跳表（ZSet）、压缩列表等，针对场景专门优化。

## 📌 典型使用场景

| 业务场景 | 为什么用它 | 不用的后果 |
| --- | --- | --- |
| 热点缓存（商品详情） | 读多写少，内存读微秒级 | 高峰期请求全打到 MySQL，数据库被打垮 |
| 分布式锁（秒杀扣库存） | `SET NX EX`/Redisson 跨进程互斥 | 多实例并发超卖库存 |
| 计数器（点赞/浏览量） | `INCR` 原子自增，天然无并发问题 | `count = count + 1` 在并发下丢失更新 |
| 排行榜（游戏积分/热搜） | ZSet 按分数自动排序，`REVRANGE` 直接取 Top N | MySQL `ORDER BY` 大表排序慢，实时更新代价高 |
| 会话共享（集群登录态） | 多台应用实例读写同一份 Session | Session 存本机，Nginx 轮询后用户频繁掉登录 |
| 接口限流 | `INCR + EXPIRE` 按时间窗口计数 | 无限流则恶意请求/突发流量打垮服务 |
| 签到打卡 | BitMap 1 bit/天，一年 365 天仅 46 字节 | MySQL 存签到记录，亿级用户存储与统计成本高 |

## 🚀 快速上手

### 1. Docker 启动

```bash
docker run -d --name redis -p 6379:6379 redis:7.2 --requirepass "123456"
# 进入命令行
docker exec -it redis redis-cli -a 123456
```

```bash
# redis-cli 基本操作
set name zhangsan          # 写
get name                   # 读
set lock:order:1 1 NX EX 10  # 不存在才设置 + 10 秒过期（分布式锁雏形）
incr count                 # 原子自增
expire name 60             # 设置过期时间
ttl name                   # 查看剩余过期时间
keys *                     # 列出所有 key（生产禁用，会阻塞；用 scan 代替）
del name                   # 删除
```

### 2. Spring Boot 整合（StringRedisTemplate 五大类型操作）

```xml
<!-- pom.xml -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-data-redis</artifactId>
</dependency>
<!-- Redisson：生产级分布式锁 -->
<dependency>
    <groupId>org.redisson</groupId>
    <artifactId>redisson-spring-boot-starter</artifactId>
    <version>3.30.0</version>
</dependency>
```

```yaml
# application.yml（Spring Boot 3.x 用 spring.data.redis；2.x 用 spring.redis）
spring:
  data:
    redis:
      host: localhost
      port: 6379
      password: 123456
```

```java
@Service
@RequiredArgsConstructor
public class RedisTypeDemo {
    private final StringRedisTemplate redis;

    /** String：缓存 JSON + 过期时间 + 计数器 */
    public void string() {
        redis.opsForValue().set("user:1", "{\"name\":\"张三\"}", 30, TimeUnit.MINUTES);
        redis.opsForValue().get("user:1");
        redis.opsForValue().increment("article:1001:like");   // 原子 +1
    }

    /** Hash：对象按字段读写，局部更新不整存整取 */
    public void hash() {
        redis.opsForHash().put("user:1:profile", "name", "张三");
        redis.opsForHash().get("user:1:profile", "name");
        redis.opsForHash().delete("user:1:profile", "name");
    }

    /** List：最新消息/简易队列（左进右出） */
    public void list() {
        redis.opsForList().leftPush("msg:list", "hello");
        redis.opsForList().rightPop("msg:list");
        redis.opsForList().range("msg:list", 0, 9);           // 取最新 10 条
    }

    /** Set：去重、抽奖、共同关注 */
    public void set() {
        redis.opsForSet().add("article:1001:readers", "u1", "u2");  // 自动去重
        redis.opsForSet().intersect("u1:follow", "u2:follow");      // 共同关注
        redis.opsForSet().pop("lottery:1");                          // 随机弹出（抽奖）
    }

    /** ZSet：排行榜，按 score 自动排序 */
    public void zset() {
        redis.opsForZSet().incrementScore("rank:score", "player1", 10); // 加 10 分
        redis.opsForZSet().reverseRange("rank:score", 0, 9);            // Top 10
        redis.opsForZSet().reverseRank("rank:score", "player1");        // 我的排名
    }
}
```

### 3. Redisson 分布式锁（看门狗自动续期）

```java
@Service
@RequiredArgsConstructor
public class StockService {
    private final RedissonClient redisson;

    public void deductStock(String productId) {
        RLock lock = redisson.getLock("lock:stock:" + productId);
        lock.lock(); // 不传 leaseTime → 启用看门狗：默认锁 30s，每 10s 检查并自动续期
        try {
            // 查库存 → 判断 → 扣减，临界区必须包含"查+改"全程
        } finally {
            if (lock.isHeldByCurrentThread()) { // 防止误释放别人的锁
                lock.unlock();
            }
        }
    }

    public boolean tryDeduct(String productId) throws InterruptedException {
        RLock lock = redisson.getLock("lock:stock:" + productId);
        // tryLock：最多等 5 秒，拿到锁后 10 秒自动释放（不启用看门狗）
        if (!lock.tryLock(5, 10, TimeUnit.SECONDS)) {
            return false; // 没抢到锁，快速失败
        }
        try { /* 业务 */ return true; }
        finally { lock.unlock(); }
    }
}
```

## 🔧 常用命令 / API 速查

| 类型 | 常用命令 | 典型场景 |
| --- | --- | --- |
| String | `SET/GET`、`INCR/DECR`、`SET key val NX EX 10`、`MSET/MGET` | 缓存、计数器、分布式锁、限流 |
| List | `LPUSH/RPOP`、`LRANGE`、`LLEN`、`BLPOP` | 最新列表、消息队列、时间线 |
| Hash | `HSET/HGET/HGETALL`、`HDEL`、`HINCRBY` | 对象属性存储、购物车 |
| Set | `SADD/SMEMBERS`、`SINTER/SUNION/SDIFF`、`SPOP` | 去重、共同好友、抽奖 |
| ZSet | `ZADD`、`ZINCRBY`、`ZREVRANGE`、`ZRANK`、`ZRANGEBYSCORE` | 排行榜、延迟队列、范围检索 |
| Stream | `XADD`、`XREADGROUP`、`XACK` | 消息队列/消费者组雏形（5.0+，面试加分项，了解即可） |
| BitMap | `SETBIT/GETBIT`、`BITCOUNT` | 签到、活跃用户统计 |
| 通用 | `EXPIRE/TTL`、`SCAN`、`DEL/UNLINK`、`TYPE` | 过期管理、渐进遍历、删除 |

## 🧠 核心进阶

### 1. 过期删除与内存淘汰

- **过期删除**（处理已设 TTL 的 key）：不是"到点即删"。采用 **惰性删除**（访问时检查过期才删）+ **定期删除**（每 100ms 随机抽一批 key 检查删除）的折中策略，兼顾 CPU 与内存。
- **内存淘汰**（内存达到 `maxmemory` 后触发）：`noeviction`（默认，写报错）、`allkeys-lru`（全键 LRU，缓存场景最常用）、`allkeys-lfu`（访问频率优先）、`volatile-lru/lfu/ttl/random`（只淘汰设了 TTL 的）、`allkeys-random`。缓存场景推荐 `allkeys-lru` 或 `allkeys-lfu`。

### 2. 持久化：RDB vs AOF vs 混合

| 方案 | 原理 | 优点 | 缺点 |
| --- | --- | --- | --- |
| RDB | 定时 `bgsave` fork 子进程做全量快照（二进制） | 文件小、恢复快 | 两次快照间的数据会丢 |
| AOF | 追加记录每条写命令，`appendfsync everysec` | 最多丢 1 秒数据 | 文件大、恢复慢（有重写机制压缩） |
| 混合（4.0+） | AOF 重写时前半段存 RDB 全量 + 后半段增量命令 | 恢复快 + 丢得少 | 仅 Redis 4.0+ 支持 |

生产推荐：开启混合持久化（`aof-use-rdb-preamble yes`）。

**bgsave 的 fork 与写时复制（线上高频追问）**：`bgsave` 靠 fork 子进程做快照，靠的就是 OS 的写时复制——fork 瞬间**不复制数据**，父子共享同一批物理页，所以 60GB 实例 fork 也很快。但代价在后面：

- 快照期间主进程仍接受写入，**任何一个被改动的页都会触发复制**，额外占用内存；写入越猛、被改的页越多，峰值内存越接近**翻倍**。
- 所以线上要留出内存余量（经验值：留给 COW 的空间 ≈ 写入速率 × 快照耗时），并控制 `maxmemory` 不超过物理内存的一半左右；反之则可能触发 swap 甚至 OOM。
- 同理，`fork` 本身虽然快，但**fork 那一刻主进程会短暂阻塞**（要复制页表，堆越大页表越大，阻塞越久），这是"大实例 fork 卡顿"的来源。

**AOF 重写期间的新命令去哪了？**：子进程重写期间，主进程把新收到的写命令**追加到 `aof_rewrite_buf`（重写缓冲区）**，同时照常写入原 AOF 文件。子进程写完新 AOF 后，主进程把 `aof_rewrite_buf` 的内容**追加到新文件末尾**，再用新文件原子替换旧文件——这样重写期间的写入一条不丢，也不会污染重写出的快照。

### 3. 缓存穿透 / 击穿 / 雪崩（必须会画会讲）

| 问题 | 现象 | 解决方案 |
| --- | --- | --- |
| 穿透 | 查询**根本不存在**的数据，缓存永远 miss，请求全打到 DB | ① 缓存空值（短 TTL）；② **布隆过滤器**前置拦截（说"不存在"则一定不存在，说"存在"可能误判，空间极省）；③ 参数校验 |
| 击穿 | 某个**热点 key 过期瞬间**，海量并发同时回源 DB | ① **互斥锁**：只放一个线程重建缓存，其他等待；② 逻辑过期：热点 key 不设 TTL，值里存过期时间异步更新 |
| 雪崩 | **大量 key 同时过期**或 Redis 宕机，DB 瞬间被冲垮 | ① TTL 加随机值打散；② 多级缓存（本地 Caffeine + Redis）；③ 集群高可用 + 限流、降级兜底 |

### 4. 缓存与数据库一致性

- 主流方案 **Cache Aside**：读——先读缓存，miss 则查库回填；写——**先更新数据库，再删除缓存**（不是更新缓存：并发写会覆盖出旧值，删除保留"下次读时再加载"的懒加载语义）。
- 该方案仍有极小概率不一致（读线程在写线程删缓存后、更新数据库前把旧值回填），可用**延迟双删**：删缓存 → 更新库 → 延迟 500ms~1s 再删一次。
- 更可靠的方案：订阅 MySQL binlog（canal）异步删除/更新缓存，业务代码零侵入。

### 5. 三种高可用架构对比

| 架构 | 解决什么 | 原理 | 局限 |
| --- | --- | --- | --- |
| 主从复制 | 读写分离、备份 | 从节点全量 RDB + 增量命令同步，写主读从 | 主挂需手动切换 |
| 哨兵 Sentinel | 主挂**自动故障转移** | 哨兵集群监控主节点，多数派投票选新主并通知客户端 | 不扩容，容量仍受单机限制 |
| Cluster | 数据分片 + 高可用 | 16384 个 slot 按 `CRC16(key) % 16384` 分给多个主节点，每主带从 | 多 key 跨槽操作受限（需 hash tag）、运维复杂 |

**主从复制的两个阶段**（面试常追问）：

- **全量复制**：首次连接或增量不可用时，主节点 `bgsave` 生成 RDB 发给从节点，期间的写命令缓存后一并发过去，从节点加载完成。
- **增量复制（断线重连的关键）**：主节点维护一个 **`repl_backlog` 环形缓冲区**（默认 1MB），记录最近一段写命令与 `master_repl_offset`；从节点重连时上报自己的 offset，**只要 offset 仍落在 backlog 范围内，就只补发差额部分**；反之（offset 已被覆盖/不连续）只能**退化成全量复制**——大内存实例全量复制要重新 fork + 传输整个 RDB，代价极高。所以生产上 `repl-backlog-size` 要按"断线时长 × 写入速率"给足。
- **复制是异步的 → 读写分离会读到旧值**：主节点执行完写命令就返回客户端，命令再**异步**传播给从节点。主从之间因此存在一个同步窗口，**窗口内去读从节点必然拿到旧值**。对一致性敏感的操作（支付后立刻查订单状态）要**强制读主库**，或先 `WAIT` 等若干副本确认。哨兵只负责监控与故障转移，**不代理读写请求**——读旧值不是哨兵的问题。

**哨兵的主观下线与客观下线**：单个哨兵 `PING` 主节点超时后，先标记为**主观下线（SDOWN）**——这只是它一家的判断，可能是自己的网络抖动。它会向其他哨兵询问，**达到 quorum 数量的哨兵都认为失联**时，才判定**客观下线（ODOWN）**并触发选举与故障转移。两层判定就是为了避免单点误判引发无谓的主从切换。

**槽与 key 的路由**：客户端算 `CRC16(key) % 16384` 得到槽号，再查本地缓存的「槽 → 节点」映射，直接连对应节点。

- **请求发错节点时的两种重定向**（高频追问）：
  - **MOVED**：该槽**永久**归属另一个节点 → 节点返回 `MOVED <slot> <ip:port>`，客户端**更新本地槽映射**后重新请求（槽的归属是预先划分好的，节点不做代理转发，只做重定向）。
  - **ASK**：该槽**正在迁移中**，key 已被搬到目标节点但迁移未完成 → 返回 `ASK`，客户端仅对**这一次**请求临时改投目标节点，**不更新**槽映射（否则迁移未完成时映射会来回抖动）。
  - 一句话：**MOVED 是永久改派（要刷新映射），ASK 是一次性绕行（不刷新）**。
- **CROSSSLOT 错误**：多 key 命令（`MGET`、`SINTER`、`MSET`、Lua 多 key）要求所有 key 在**同一个槽**，否则报 `CROSSSLOT Keys in request don't hash to the same slot`。`user:1:follow` 与 `user:2:follow` 的 CRC16 结果通常不同 → 分属不同节点 → 直接报错。
  - 解法：**hash tag**——用 `{}` 包住参与哈希的部分，只有花括号内的内容参与计算：`{u1}:follow` 与 `{u1}:fans` 的哈希部分都是 `u1`，必然同槽，可以放心一起操作。

### 6. 热 key 与大 key

- **热 key**：单个 key 被超高频率访问，打爆某个节点 → 本地缓存兜一层、key 加随机后缀打散到多节点。
- **大 key**：value 过大（如百万元素的 List）→ 删除/迁移阻塞主线程 → 拆分成多 key、压缩、用 `UNLINK` 异步删除，`redis-cli --bigkeys` 排查。

### 7. 发布/订阅与键过期通知

- `SUBSCRIBE/PSUBSCRIBE` 频道订阅、`PUBLISH` 发布；配合 `notify-keyspace-events Ex` 可订阅**键过期/删除事件**，常见用法是集群各节点收到"某缓存 key 失效"广播后清掉本地缓存。
- 缺陷：**不可靠**——订阅者离线期间的消息直接丢失，没有持久化、没有 ACK、没有重投。结论：做**缓存失效广播**这类"丢一两次无大碍"的事可以，做**业务消息**（订单、支付）不行 → 这正是需要专业 MQ（RabbitMQ/Kafka/RocketMQ）的理由。

### 8. 对象编码与内存优化

同一种类型，Redis 会按数据规模**自动切换底层编码**以省内存（`OBJECT ENCODING key` 可查看）：

| 类型 | 小对象编码 | 大对象编码 | 切换阈值（默认） |
| --- | --- | --- | --- |
| String | int / embstr | raw | 整数用 int；≤44 字节用 embstr |
| Hash | **listpack**（旧版 ziplist） | hashtable | 字段数 ≤128 且值 ≤64 字节 |
| List | listpack | quicklist | 元素数/大小超阈值 |
| ZSet | **listpack**（旧版 ziplist） | skiplist + dict | 元素数 ≤128 且成员 ≤64 字节 |
| Set | intset / listpack | hashtable | 全整数用 intset；元素数 ≤128 且值 ≤64 字节 |

- 大 ZSet 的**双结构**：**skiplist** 支持按 score 范围与排名 O(logN) 查找，**dict** 支持按成员 O(1) 取分数——两者互补，代价是内存翻倍。
- 优化口径：小对象紧凑编码省内存但增删代价高（要移动连续内存），超过阈值自动转成指针结构；调 `hash-max-listpack-entries` 等参数可控制阈值，通常不用动。

## 💼 高频面试题

**Q：Redis 为什么快？**
- 纯内存操作，避免磁盘 IO；
- 命令执行单线程，无锁、无线程切换开销（6.0 的多线程只用于网络 IO）；
- epoll IO 多路复用，单线程支撑大量并发连接；
- 专门优化的高效数据结构（跳表、SDS、压缩列表等）。

**Q：五大基本类型及使用场景？**
- String：缓存 JSON、计数器（INCR）、分布式锁（SET NX EX）、限流；
- List：最新消息列表、简单消息队列（LPUSH/RPOP）；
- Hash：对象按字段存取（购物车、用户属性）；
- Set：去重、共同关注（SINTER）、抽奖（SPOP）；
- ZSet：排行榜（分数排序）、延迟队列（score 存执行时间）。
- 加分项：还有 **Stream**（5.0+，带 ID 的消息流 + 消费者组 + ACK，消息队列雏形），以及 BitMap/HyperLogLog/GEO 等扩展类型。

**扩展类型速记**（统计类场景的高频考点）：

| 类型 | 用途 | 关键数字 |
| --- | --- | --- |
| BitMap | 签到、活跃统计 | 1 bit/天，一年 365 天仅 46 字节 |
| **HyperLogLog** | 统计**去重后的基数**（UV、PV 去重） | **固定约 12KB**，标准误差 **0.81%**；16384 个 6bit 寄存器做概率估算 |
| GEO | 附近的人、距离计算 | 底层是 ZSET，按经纬度编码成分值 |
| Stream | 消息队列雏形 | 带 ID、消费者组、ACK |

- HyperLogLog 的取舍：内存恒定、不要成员列表，只给近似计数。**只关心"有多少个不同的"，不关心"分别是谁"**时用它（UV）；要精确、要成员列表就用 SET，但内存随基数线性增长。判断精度是否够，先问业务对误差的容忍度。

**Q：持久化怎么选？**
- RDB 快照：文件小恢复快，但会丢两次快照间的数据；
- AOF：everysec 最多丢 1 秒，文件大恢复慢；
- 生产用 4.0+ 混合持久化：RDB 做底 + AOF 增量，兼顾恢复速度与数据安全。

**Q：缓存穿透、击穿、雪崩的区别与方案？**
- 穿透=数据压根不存在→布隆过滤器/缓存空值/参数校验；
- 击穿=单个热点 key 失效瞬间→互斥锁重建/逻辑过期；
- 雪崩=大量 key 同时失效或 Redis 挂掉→TTL 随机打散/多级缓存/集群+限流降级。

**Q：如何保证缓存与数据库一致性？**
- 先更新数据库，再删除缓存（Cache Aside），失败靠重试；
- 并发窗口要求高用延迟双删；
- 终极方案：canal 订阅 binlog 异步删缓存，解耦且不易漏。

**Q：Redisson 分布式锁的原理？**
- 加锁/解锁用 Lua 脚本保证原子性；底层是 Hash 结构记录"持有线程+重入次数"，支持可重入；
- 看门狗：不指定 leaseTime 时默认锁 30 秒，后台线程每 10 秒检查续期，业务没执行完锁不会过期；
- 相比自写 `SET NX EX`：解决了"业务超时锁先过期""误删他人锁""不可重入"三大坑。

**Q：哨兵和 Cluster 怎么选？**
- 哨兵：数据量小、写并发不高，只要高可用 + 读写分离，方案简单；
- Cluster：数据量大（单机放不下）或写 QPS 高，需要分片横向扩容；
- Cluster 解决分片+高可用，哨兵只解决高可用。

## 🔗 推荐资料

| 资料 | 说明 | 链接 |
| --- | --- | --- |
| JavaGuide Redis 面试题（上） | 面试导向，覆盖本篇全部考点 | https://javaguide.cn/database/redis/redis-questions-01.html |
| pdai Redis 总览 | 知识体系全景图 | https://pdai.tech/md/db/nosql-redis/db-redis-overview.html |
| pdai Redis 数据类型 | 五大类型与底层结构详解 | https://pdai.tech/md/db/nosql-redis/db-redis-data-types.html |
| pdai RDB 与 AOF | 持久化机制与混合持久化 | https://pdai.tech/md/db/nosql-redis/db-redis-x-rdb-aof.html |
| pdai 缓存问题 | 穿透/击穿/雪崩/一致性 | https://pdai.tech/md/db/nosql-redis/db-redis-x-cache.html |
| pdai Redis 哨兵 | 主从架构与故障转移 | https://pdai.tech/md/db/nosql-redis/db-redis-x-sentinel.html |
| pdai Redis Cluster | 分片原理与槽位机制 | https://pdai.tech/md/db/nosql-redis/db-redis-x-cluster.html |
| 廖雪峰 Spring Boot 集成 Redis | Spring Boot 整合实操 | https://liaoxuefeng.com/books/java/springboot/index.html |

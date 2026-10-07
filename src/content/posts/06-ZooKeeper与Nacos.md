---
title: "06-ZooKeeper与Nacos"
description: "阶段：中间件篇 ｜ 建议时长：3 天 ｜ 前置：Spring Boot 基础、01-Redis（理解分布式锁）"
pubDatetime: 2026-08-25T01:00:00
tags:
  - "④ 中间件篇"

draft: false
---

> **阶段**：中间件篇 ｜ **建议时长**：3 天 ｜ **前置**：Spring Boot 基础、01-Redis（理解分布式锁）

## 它是什么，解决什么问题

进入微服务后出现两个新问题，注册中心/配置中心就是为它们而生的：

1. **服务动态感知（注册中心）**：服务提供者有多台实例，随时扩容、缩容、宕机，调用方不能把 IP 写死在配置里——实例启动时把地址注册上去，调用方实时拉取并监听列表变化；
2. **配置集中管理 + 热更新（配置中心）**：几十个实例的开关、阈值、连接串散落在各自配置文件里，改一次要逐个重启——配置集中存放，改完自动推送到所有实例，**不用重启**。

**ZooKeeper（ZK）**：Apache 的分布式协调服务，本质是"高可靠的树形 K-V 存储 + Watcher 通知"，并非专为服务发现设计，但 Hadoop/Kafka/Dubbo 早期都拿它当注册中心，它的**临时节点、Watcher、顺序节点**是面试核心。

**Nacos**：阿里开源的**注册中心 + 配置中心二合一**，Spring Cloud Alibaba 生态的标配，开箱即用、带控制台，是目前国内 Java 微服务的最主流选择。

## 典型使用场景

| 业务场景 | 用什么 | 为什么 | 不用的后果 |
| --- | --- | --- | --- |
| 微服务互相调用 | Nacos 注册中心 | 调用方按服务名动态发现实例，自动剔除宕机实例 | IP 写死，扩缩容要改所有调用方配置 |
| 业务开关/阈值热更新 | Nacos 配置中心 | 控制台改配置秒级推送，无需重启 | 改个开关要发版重启全部实例 |
| 分布式锁/选主 | ZK | 临时顺序节点 + Watcher 实现公平锁与 Leader 选举 | 多进程并发操作共享资源无序 |
| 大数据组件依赖 | ZK | Kafka(旧)、HBase、SolrCloud 的协调底座 | 组件无法选主与元数据管理 |

## 快速上手

### 1. Docker 启动 Nacos（单机模式）

```bash
docker run -d --name nacos \
  -p 8848:8848 -p 9848:9848 \
  -e MODE=standalone \
  -e NACOS_AUTH_ENABLE=false \
  nacos/nacos-server:v2.3.2
# 控制台：http://localhost:8848/nacos（默认 nacos/nacos）
# 8848=控制台/HTTP API，9848=客户端 gRPC（2.x 必须开放）
```

### 2. （可选）Docker 启动 ZooKeeper，体验临时节点

```bash
docker run -d --name zk -p 2181:2181 zookeeper:3.9
docker exec -it zk zkCli.sh

create -e /order-svc "192.168.1.10:8080"   # -e：创建临时节点，模拟服务注册
ls /order-svc                              # 能看到节点
quit                                       # 退出 = 会话断开
# 重新进入 zkCli 后 ls /order-svc：节点已自动消失（临时节点随会话销毁）
```

### 3. Spring Boot 接入（注册中心 + 配置中心）

```xml
<dependency>
    <groupId>com.alibaba.cloud</groupId>
    <artifactId>spring-cloud-starter-alibaba-nacos-discovery</artifactId>
</dependency>
<dependency>
    <groupId>com.alibaba.cloud</groupId>
    <artifactId>spring-cloud-starter-alibaba-nacos-config</artifactId>
</dependency>
<!-- 版本随 Spring Cloud Alibaba BOM 管理，Boot 3.x 对应 2023.x 系列 -->
```

```yaml
# application.yml（Boot 3.x 用 spring.config.import 引入远端配置）
spring:
  application:
    name: order-service              # 服务名 = 注册中心里的标识
  cloud:
    nacos:
      server-addr: localhost:8848
      discovery:
        namespace: dev               # 命名空间隔离环境（dev/test/prod）
      config:
        file-extension: yaml
  config:
    import: nacos:order-service.yaml # 拉取 Nacos 上的配置
```

在 Nacos 控制台新建配置 `order-service.yaml`（Group 默认 DEFAULT_GROUP），写入：

```yaml
order:
  discount: 100       # 折扣阈值，演示热更新
```

```java
// 服务提供方：启动即自动注册到 Nacos（discovery 依赖引入即生效）

// 配置热更新：控制台改 discount 后，本 Bean 无需重启即拿到新值
@RestController
@RefreshScope                     // 让 @Value 绑定的配置支持热刷新
public class ConfigController {
    @Value("${order.discount:100}")
    private int discount;

    @GetMapping("/discount")
    public int discount() { return discount; }
}

// 服务消费方：从注册中心拿可用实例列表（配合 LoadBalancer 实现负载均衡）
@Service
@RequiredArgsConstructor
public class DiscoveryDemo {
    private final DiscoveryClient discoveryClient;

    public List<String> instances() {
        return discoveryClient.getInstances("order-service").stream()
                .map(i -> i.getHost() + ":" + i.getPort()).toList();
    }
}
```

## 常用命令 / API 速查

| 操作 | 命令 / API |
| --- | --- |
| Nacos 控制台 | `http://localhost:8848/nacos`：服务列表、配置管理、命名空间 |
| 注册服务 | 引入 discovery 依赖 + `spring.cloud.nacos.server-addr` 即自动注册 |
| 手动上下线 | 控制台对实例"上线/下线"，用于发布前摘流量 |
| 读取配置 | `@Value` + `@RefreshScope`，或 `@ConfigurationProperties`（天然支持刷新） |
| 查看实例列表 | `discoveryClient.getInstances("service-name")` |
| ZK 客户端 | `docker exec -it zk zkCli.sh` 进入命令行 |

**ZooKeeper 常用操作（zkCli.sh）**：

| 命令 | 说明 |
| --- | --- |
| `create /app/lock/seq- "data"` | 创建 znode（`-e` 临时、`-s` 顺序） |
| `get /app/config` | 读节点数据并注册 Watcher |
| `ls /app` | 列子节点并注册 Watcher |
| `set /app/config "new"` | 更新数据，触发 Watcher 通知 |
| `delete /app/config` | 删除节点 |

## 核心进阶

### 1. ZooKeeper 三大机制（面试核心）

- **znode**：树形命名空间中的节点，类似文件/目录二合一，可存少量数据（建议 < 1MB）；
- **临时节点（ephemeral）**：**与客户端会话绑定，会话断开自动删除**——这就是服务注册与锁自动释放的基石（实例宕机 → 会话失效 → 节点消失 → 下游立刻感知）；另有**临时顺序节点**：自动追加单调递增序号（`lock-0001`、`lock-0002`）；
- **Watcher 机制**：客户端对节点注册监听，节点**变化时触发一次通知**（数据变更、子节点增减、节点删除）；注意是**一次性**的，收到通知后要重新注册——服务发现每次拉完列表都要再挂一次 Watcher。

**ZAB 协议一句话**：ZK 用 ZAB（原子广播）保证一致性——写请求都转发给 Leader，**过半节点写入成功才算提交**；Leader 挂掉触发选举，恢复期间集群不可写。由此 ZK 的**写性能受限于过半同步**，且部署节点建议为奇数（3/5 台）以省资源。

**临时顺序节点实现分布式锁**：

```
1. 各客户端在 /lock/ 下创建临时顺序节点 seq-
2. 判断自己是不是序号最小的 → 是则获锁
3. 否则 watch「比自己序号小的最近一个节点」
4. 持锁者释放锁/会话断开 → 节点删除 → 下一个收到通知 → 回到 2
```

比"所有人抢同一个节点"好在**避免惊群**：锁释放只唤醒一个等待者；会话断开自动删节点则天然解决"持锁进程挂死锁不释放"。

**CP 的代价**：ZK 是 CP 系统，Leader 选举期间（可能长达数十秒）整个集群**拒绝服务**——服务发现场景下"宁可返回旧列表也不能不可用"，这就是"ZK 不适合做注册中心"论断的核心；再加上 Watcher 一次性、无控制台、运维重，新项目基本不再选它做注册。

### 2. Nacos 架构与 AP/CP

- **AP/CP 可切换⭐**：**临时实例（默认）用 AP（Distro 协议）**——客户端每 5s 发心跳，15s 未收到标记不健康，30s 未收到剔除；实例下线最终一致，可用性优先。**持久实例用 CP（Raft 协议）**——强一致，适合数据库类"必须全员知道"的服务；
- 注册中心要的恰恰是"宕机也能返回旧列表"，所以**临时实例 + AP 是服务发现的正确姿势**；面试追问"为什么不用 CP"就答 ZK 选举期不可用的反例；
- **配置中心**：长轮询（客户端 30s 内监听配置变更，改动秒级推送）+ MD5 比对；`@RefreshScope` 触发 Bean 重建实现热更新；`@ConfigurationProperties` 绑定的配置自动刷新；与 ZK Watcher 对比：Nacos 长轮询可重复等待无需反复注册，使用成本低得多；
- **保护阈值（雪崩保护）**：健康实例比例低于阈值时，Nacos 把不健康实例也返回给调用方——宁可部分调用失败，也不返回空列表导致服务全瘫，这正是"可用性优先"的体现；
- **集群部署**：生产至少 3 节点组集群（内嵌 Raft/Distro 协议选主与同步），配置持久化到 MySQL（单机默认 Derby），客户端通过 gRPC 长连接保持实时感知；
- **命名空间（namespace）**：按环境隔离（dev/test/prod 各一个 namespace），配合 Group、Cluster 做多级隔离；
- **优雅上下线**：发布前在控制台对实例"下线"摘流量，等流量排空再停机，避免发布瞬间报错——注册中心的控制台能力比"能注册"更值钱。

### 3. 三者对比与选型

| 维度 | ZooKeeper | Nacos | Eureka |
| --- | --- | --- | --- |
| 一致性 | CP | AP/CP 可切换 | AP |
| 健康检查 | 会话 keepalive | 心跳 + 主动探测 | 客户端心跳 |
| 功能 | 树形 K-V + Watcher | 注册 + 配置 + 控制台 | 仅注册 |
| 易用性 | 无 UI、运维重 | 控制台开箱即用 | 有控制台但已停更 |
| 典型用途 | 选主/锁/大数据组件 | Spring Cloud Alibaba 微服务 | 旧 Spring Cloud Netflix |

选型：**Spring Cloud Alibaba 体系直接用 Nacos**（注册+配置一站式）；需要强一致的协调原语（选主、严格的锁）用 ZK 或 etcd；新项目不要再选已停更的 Eureka。国内新项目 90% 的组合是：Nacos（注册+配置）+ OpenFeign（调用）+ Sentinel（限流熔断），即 Spring Cloud Alibaba 标准全家桶。

## 高频面试题

**Q：ZooKeeper 能干什么？**
- 树形 znode 存储 + 临时节点 + Watcher，提供高可靠的分布式协调原语；
- 典型用途：注册中心（早期 Dubbo/Kafka）、分布式锁（临时顺序节点）、Leader 选举、配置共享；
- 本质是 CP 的协调服务，不是专门的服务发现组件。

**Q：Watcher 机制是什么？**
- 客户端对节点读操作可注册监听，节点数据变更/子节点变化/删除时服务端推送一次通知；
- **一次性触发**：收到通知后必须重新注册，否则后续变更收不到；
- 服务发现依赖它：列表变化 → 通知 → 重新拉取 + 重新注册。

**Q：临时节点有什么用途？**
- 生命周期绑定客户端**会话**，会话断开自动删除；
- 服务注册：实例宕机 → 节点消失 → 调用方即时感知；
- 分布式锁：持锁进程崩溃 → 锁节点自动删除 → 不会死锁；加顺序性后可实现公平锁并避免惊群。

**Q：为什么说 ZK 不适合做注册中心？**
- CP：Leader 选举期间集群不可用，而服务发现更需要可用性（AP）——宁可返回略旧的实例列表；
- Watcher 一次性，客户端要反复注册，实现繁琐；
- 无健康检查语义外的管理能力（无控制台、无权重/灰度），运维成本高。

**Q：Nacos 的 AP 和 CP 怎么选？**
- 临时实例（默认）→ AP/Distro：客户端心跳保活，宕机靠心跳超时剔除，最终一致，适合绝大多数微服务；
- 持久实例 → CP/Raft：不会自动剔除，需主动注销，适合配置类、数据库类强一致服务；
- 同一 Nacos 集群可同时承载两种模式，按实例类型自动路由。

**Q：Nacos 配置中心如何实现热更新？**
- 客户端与 Nacos 保持**长轮询**，配置变更后秒级返回新版本；
- `@Value` 字段所在 Bean 加 `@RefreshScope`：刷新时销毁重建 Bean 重新注入；`@ConfigurationProperties` 绑定类天然支持；
- 灰度发布与回滚可直接在控制台操作。

## 推荐资料

| 资料 | 说明 | 链接 |
| --- | --- | --- |
| JavaGuide ZooKeeper 入门 | znode/Watcher/ZAB 等核心概念 | https://javaguide.cn/distributed-system/distributed-process-coordination/zookeeper/zookeeper-intro.html |
| pdai 架构知识体系 | 注册中心/配置中心在微服务架构中的位置 | https://pdai.tech/md/arch/arch-z-overview.html |
| 廖雪峰 Spring Boot 教程 | Spring Boot 整合实操基础 | https://liaoxuefeng.com/books/java/springboot/index.html |
| JavaGuide 高可用系统设计指南 | 服务注册发现的可用性设计视角 | https://javaguide.cn/high-availability/high-availability-system-design.html |

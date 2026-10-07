---
title: "SpringCloud微服务"
description: "阶段：框架篇 ｜ 建议时长：6 天 ｜ 前置：02-SpringBoot实战.md"
pubDatetime: 2026-08-23T07:00:00
tags:
  - "⑤ 框架篇"

draft: false
---

> **阶段**：框架篇 ｜ **建议时长**：6 天 ｜ **前置**：02-SpringBoot实战.md

## 学习目标

- 能说出微服务拆分的时机与代价，并画出微服务技术栈全景图。
- 能讲清 Nacos 注册中心的注册/心跳/发现机制，并实现配置中心热更新。
- 能用 OpenFeign 完成服务间声明式调用，并配置超时、重试与日志。
- 能用 Gateway 统一入口并写一个全局鉴权过滤器，能用 Sentinel 配置限流与熔断降级。
- 能独立完成 order/product 双服务实战，通过全部验收标准。

## 核心知识点

### 1. 单体 → 微服务 ⭐

> 面试官想听：不是背"微服务好"，而是能说出"什么时候该拆、拆了要付出什么"。

- 拆分收益：模块独立部署发布（互不拖累）、故障隔离（一个服务挂不拖垮全站）、按服务伸缩（订单服务单独扩容）、团队并行开发、技术栈可选。
- 拆分代价：分布式复杂性全部入场——网络调用不可靠、数据一致性变难、链路排查复杂、运维成本翻倍。
- 拆分时机：团队规模大了需要并行；模块间发布节奏冲突严重；不同模块负载差异大需要独立伸缩。**早期单体能扛就先单体**，拆分是演进不是起点。
- 组件全景（每个角色解决一个分布式问题）：

```text
注册发现：服务上下线感知（Nacos）
配置中心：配置集中管理与热更新（Nacos）
远程调用：跨服务 HTTP 调用（OpenFeign）+ 负载均衡（LoadBalancer）
API 网关：统一入口、鉴权、路由、限流（Gateway）
熔断限流：保护服务不被打垮（Sentinel）
链路追踪：一次请求跨多个服务，怎么串起来（SkyWalking）
分布式事务：跨库写一致性（Seata，衔接分布式篇）
```

### 2. 技术栈现状 ⭐

> 面试官想听：知道行业从 Netflix 迁移到 Spring Cloud Alibaba 的现状，版本对应能说一句即可。

- **Netflix 全家桶**（Eureka 注册、Ribbon 负载均衡、Hystrix 熔断、Zuul 网关）2018 年起陆续停止更新、进入维护模式，新项目不用。
- **国内主流组合**：Spring Cloud Alibaba（Nacos + Sentinel + Seata）+ Spring Cloud 官方（Gateway + OpenFeign + LoadBalancer）。
- 版本对应一句话：**Spring Cloud Alibaba 2022.x ↔ Spring Cloud 2022.x ↔ Spring Boot 3.0.x，Nacos 用 2.x**——三者版本必须配套，官方对照表查一下再用。

### 3. Nacos：注册中心 + 配置中心 ⭐

> 面试官想听：服务怎么注册、怎么知道对方还活着、配置怎么热更新，三问连环。

**注册中心原理**：

```text
服务注册：服务启动时把 实例名/IP/端口 上报到 Nacos
心跳检测：临时实例默认每 5s 发一次心跳（Nacos 2.x 临时实例走 gRPC 长连接，机制等价）
          15s 未心跳标记为不健康，30s 未心跳剔除实例
服务发现：消费者从 Nacos 拉取实例列表并订阅，实例变更时推送更新
```

注册中心解决的是"服务地址动态变化"：扩缩容、重启后 IP 变了，调用方无需改配置。

**配置中心 + 热更新**：配置集中存到 Nacos，改完不用重启即生效——`@Value` 所在类加 `@RefreshScope`，或用 `@ConfigurationProperties` 绑定（原生支持刷新）：

```java
@RestController
@RefreshScope
public class ConfigController {
    @Value("${app.welcome:hello}")
    private String welcome;      // Nacos 控制台改值发布后，这里立即读到新值
}
```

**namespace 与 group**：namespace 隔离环境（dev/test/prod 各一个），group 隔离项目/模块；配置按 `dataId + group + namespace` 三元组定位。

### 4. OpenFeign：声明式远程调用 ⭐

> 面试官想听：Feign 的原理一句话（接口 + 动态代理 → HTTP 请求），以及超时重试的幂等意识。

```java
@FeignClient(name = "product-service")      // 服务名，走注册中心寻址
public interface ProductClient {
    @GetMapping("/api/products/{id}")
    ProductVO getById(@PathVariable("id") Long id);
}

// 注入即用，像调用本地方法一样发 HTTP 请求
@Service
@RequiredArgsConstructor
public class OrderService {
    private final ProductClient productClient;

    public OrderVO create(Long productId) {
        ProductVO product = productClient.getById(productId);  // 远程调用
        return orderAssembler.assemble(product);
    }
}
```

要点：

- 原理：接口方法 → 动态代理 → 组装 HTTP 请求 → 经 LoadBalancer 从实例列表选一台发出 → 解码响应。`lb://` 前缀即"负载均衡寻址"。
- **超时**：默认偏保守，必须显式配置 `connectTimeout` / `readTimeout`，防止下游慢调用拖垮自己。
- **重试**：`Retryer` 可配次数与间隔；只对幂等操作（查询）开重试，下单、扣款这类非幂等操作重试会造成重复下单。
- **日志**：`Logger.Level.BASIC/FULL` + `logging.level.<client包>=debug`，排查联调问题的第一手段。

### 5. Gateway：统一入口 ⭐

> 面试官想听：网关三大概念 + 全局过滤器做鉴权的思路。

网关作用：统一入口、路由转发、统一鉴权、限流、跨域处理——让鉴权这类横切逻辑只做一次，不用每个服务重复实现。

三大概念：**Route**（一条路由 = 目标 URI + 断言 + 过滤器）、**Predicate**（断言：Path/Method/Query/Header 等匹配条件）、**Filter**（请求/响应的加工处理）。

```yaml
spring:
  cloud:
    gateway:
      routes:
        - id: order-route
          uri: lb://order-service          # lb = 从注册中心负载均衡
          predicates:
            - Path=/api/orders/**
        - id: product-route
          uri: lb://product-service
          predicates:
            - Path=/api/products/**
```

**全局过滤器鉴权**：

```java
@Component
public class AuthGlobalFilter implements GlobalFilter, Ordered {
    private static final Set<String> WHITE_LIST = Set.of("/api/auth/login", "/api/auth/register");

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        String path = exchange.getRequest().getPath().value();
        if (WHITE_LIST.stream().anyMatch(path::startsWith)) return chain.filter(exchange);
        String token = exchange.getRequest().getHeaders().getFirst("Authorization");
        if (!StringUtils.hasText(token)) {                        // 未登录直接拦截
            exchange.getResponse().setStatusCode(HttpStatus.UNAUTHORIZED);
            return exchange.getResponse().setComplete();
        }
        // 校验 token，把用户信息透传给下游服务（放 header）
        return chain.filter(exchange);
    }
    @Override
    public int getOrder() { return -1; }                          // 数值越小越先执行
}
```

### 6. Sentinel：限流与熔断降级 ⭐

> 面试官想听：限流/熔断/降级三者区别，这是微服务稳定性面试的核心题。

- **限流**：请求量超阈值直接拒绝，保护自己（如 QPS 限 100）。规则维度：QPS / 并发线程数；流控效果：快速失败、Warm Up（预热爬升）、排队等待。
- **熔断**：下游大量超时/异常时"跳闸"，一段时间内不再调用下游，直接走兜底，防止线程池被拖垮引发**服务雪崩**（一个服务慢 → 上游线程全堵住 → 连锁崩溃）。熔断器状态：关闭 → 打开 → 半开（放几个探测请求，成功则恢复）。
- **降级**：被限流/熔断/异常时的兜底方案：返回缓存旧值、默认值、空列表等"有损但可用"的结果。
- 雪崩应对三板斧：超时、限流、熔断降级。

```java
@GetMapping("/{id}")
@SentinelResource(value = "getProduct",
                  blockHandler = "getProductBlock",    // 处理限流/熔断触发
                  fallback = "getProductFallback")     // 处理业务异常
public ProductVO getProduct(@PathVariable Long id) {
    return productService.getById(id);
}

public ProductVO getProductBlock(Long id, BlockException ex) {
    return ProductVO.defaultFallback();    // 限流/熔断时的兜底
}
```

规则可在 Sentinel Dashboard（控制台）配置，默认内存态、重启丢失，生产要接 Nacos 做规则持久化——这是加分项。

### 7. 可观测与一致性（概念铺垫）

- **链路追踪**：一次请求经过网关→订单→商品多个服务，SkyWalking 用 TraceId 把整条调用链串起来，可视化展示每段耗时、定位慢点和报错点；特点是基于字节码增强、业务代码零侵入。一句话了解即可，中间件篇/分布式篇展开。
- **Seata**：分布式事务框架，AT 模式最常用——一阶段自动记录数据快照生成 undo_log，二阶段成功则删日志、失败则用快照反向补偿回滚。此处只需知道"跨服务跨库的写操作需要它"，详细机制在分布式篇。

## 动手实践

### 任务 ⭐：order/product 双服务微服务链路（4 天）

**第 1 步：起环境**——Docker 启动 Nacos（standalone）：

```bash
docker run -d --name nacos -e MODE=standalone \
  -p 8848:8848 -p 9848:9848 nacos/nacos-server:v2.2.3
```

**第 2 步：两个 Spring Boot 服务**——`product-service`（商品查询/列表）与 `order-service`（下单，需要查商品）。依赖版本配套：Spring Boot 3.0.x + spring-cloud 2022.0.x + spring-cloud-alibaba 2022.0.0.x，依赖 `spring-cloud-starter-alibaba-nacos-discovery`、`spring-cloud-starter-openfeign`、`spring-cloud-starter-loadbalancer`。yml 关键配置：

```yaml
spring:
  application:
    name: product-service          # 服务名即注册名，消费方按它寻址
  cloud:
    nacos:
      server-addr: localhost:8848
```

**第 3 步：Feign 互调**——order-service 定义 `ProductClient` 调 product-service 的查询接口（见第 4 节），配好超时与 BASIC 日志。

**第 4 步：Gateway 统一入口**——新建 gateway 服务，按第 5 节配置两条路由，并实现 `AuthGlobalFilter`：白名单放行登录接口，其余无 token 返回 401。

**第 5 步：Sentinel 限流**——order/order-list 资源加 `@SentinelResource`，控制台对该资源配置 QPS=2 的流控规则，触发后返回兜底数据；再给 product 接口模拟慢调用，配置慢调用比例熔断规则，观察"熔断打开→请求直接走 fallback→半开恢复"的过程。

**验收标准清单（全部满足才算完成）**：

- [ ] Nacos 控制台的服务列表能看到 product-service 和 order-service 两个实例，IP 端口正确。
- [ ] 杀掉 product-service，约 30s 后实例被剔除；重启后自动恢复注册。
- [ ] 通过 order-service 的接口下单，能拿到商品信息（Feign 调用成功），SQL/调用日志可见。
- [ ] Nacos 上新建配置并发布，@RefreshScope 的属性值不重启即生效。
- [ ] 直接访问 `localhost:8080/api/products/1`（Gateway 端口）能路由到 product-service。
- [ ] 不带 Authorization 头访问非白名单接口返回 401；登录接口白名单放行。
- [ ] Sentinel 上给资源配 QPS=2 流控后，快速刷新页面触发限流，返回兜底结果而非报错堆栈。
- [ ] 模拟 product 慢调用触发熔断：连续超时后一段时间内请求直接走 fallback，之后恢复。
- [ ] 停掉 order-service，gateway 路由返回 503 而不是网关崩溃。

## 高频面试题

**Q：微服务有什么优缺点？什么时候该拆？**
- 优点：独立部署发布、故障隔离、独立伸缩、团队并行。
- 缺点：网络调用不可靠、分布式事务与数据一致性难、运维与排查成本高。
- 拆分时机：团队规模与发布冲突、模块负载差异需要独立伸缩；单体扛得住就先单体，演进式拆分。

**Q：注册中心的原理？Nacos 怎么感知服务上下线？**
- 服务启动时上报实例信息（注册），消费者拉取并订阅实例列表，变更时推送。
- 临时实例靠心跳保活：5s 一次心跳，15s 不健康，30s 剔除（2.x 临时实例走长连接，机制等价）。
- 调用方本地缓存实例列表，注册中心短暂不可用时仍可按缓存调用，保证可用性。

**Q：Feign 的原理？**
- 声明式 HTTP 客户端：接口 + @FeignClient，启动时用动态代理生成实现。
- 调用方法 → 按注解组装 HTTP 请求 → 经负载均衡从注册中心实例列表选一台 → 发请求 → 解码响应。
- 必须配超时；重试只用于幂等操作，非幂等接口重试会重复下单。

**Q：网关的作用？**
- 统一入口，客户端不感知内部服务地址；按路由规则转发到各服务（lb 负载均衡）。
- 横切能力收敛一处：鉴权、限流、跨域、日志。
- 组成：Route（路由）、Predicate（断言匹配）、Filter（前置/后置加工），全局过滤器适合做统一鉴权。

**Q：限流、熔断、降级的区别？**
- 限流：限制进入的请求量（QPS/线程数），超出直接拒绝，保护自己。
- 熔断：下游异常率/慢调用超阈值后暂时"跳闸"不再调用，防止故障蔓延引发雪崩，状态机为关闭→打开→半开。
- 降级：被限流/熔断/异常时的兜底响应，返回默认值或缓存旧值，保证有损可用。
- 三者配合：限流挡量、熔断止损、降级兜底。

**Q：Feign 调用和 Dubbo/RPC 有什么区别？**
- Feign 基于 HTTP + JSON，跨语言友好、调试简单，性能一般。
- RPC（如 Dubbo）基于 TCP + 二进制序列化，性能高，但耦合序列化协议。
- 选型：对外或异构系统用 HTTP；内部大规模高性能调用可上 RPC（见 RPC 入门资料）。

**Q：微服务/分布式环境下会遇到哪些典型问题？**
- 服务治理：注册发现、负载均衡、故障转移。
- 数据一致性：跨服务跨库事务（Seata/消息最终一致）、分布式 ID、幂等设计。
- 稳定性：雪崩防护（超时/限流/熔断降级）、服务依赖治理。
- 可观测：链路追踪、日志聚合、监控告警；以及配置集中管理与热更新。

## 推荐资料

| 资料 | 说明 | 链接 |
| --- | --- | --- |
| 廖雪峰 Spring Cloud 教程 | 注册发现、网关等组件的入门实操 | https://liaoxuefeng.com/books/java/springcloud/index.html |
| JavaGuide RPC & Dubbo 入门 | 理解 Feign 与 RPC 的异同 | https://javaguide.cn/distributed-system/rpc/rpc-intro.html |
| JavaGuide API 网关 | 网关的职责与选型总结 | https://javaguide.cn/distributed-system/api-gateway.html |
| JavaGuide 高可用系统设计指南 | 限流、熔断、降级、超时的系统论述 | https://javaguide.cn/high-availability/high-availability-system-design.html |
| pdai 架构知识体系 | 微服务演进与架构设计全景图 | https://pdai.tech/md/arch/arch-z-overview.html |

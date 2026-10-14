# SpringBoot实战

> **阶段**：框架篇 ｜ **建议时长**：5 天 ｜ **前置**：01-Spring核心.md

## 🎯 学习目标

- 能完整讲出 Spring Boot 自动配置原理（三个注解 + 条件注解 + AutoConfiguration.imports）。
- 能用 yml 多环境 Profile 管理配置，并说清 @ConfigurationProperties 与 @Value 的取舍。
- 能搭建一套规范 Web 工程：统一返回体、全局异常、参数校验、slf4j 日志。
- 能独立完成 todo-list REST API：MyBatis-Plus + MySQL + Redis 缓存 + 打包部署。
- 能说清 Spring Boot 启动流程概览与自定义 starter 的思路。

## 📖 核心知识点

### 1. 约定优于配置与起步依赖 ⭐

> 面试官想听：Spring Boot 解决了 Spring 什么痛点——XML 地狱和依赖版本冲突。

- **约定优于配置**：默认扫描主类所在包及子包、默认嵌入式 Tomcat 端口 8080、默认配置文件 application.yml，不配置也能跑。
- **起步依赖（starter）**：`spring-boot-starter-web` = 一组按功能聚合的依赖 + 对应的自动配置。引入 starter 即引入整套能力，版本由 `spring-boot-starter-parent` 统一仲裁，杜绝版本冲突。
- Web 项目最小依赖：`spring-boot-starter-web`、数据库驱动、持久层 starter（下一篇用 `mybatis-plus`）、`spring-boot-starter-validation`。
- 版本差异：Spring Boot 2.7 基于 javax、Java 8+；Spring Boot 3.x 基于 Jakarta EE（`javax.*` → `jakarta.*`）、要求 Java 17+。新学建议直接上 3.x，老项目要会看 2.7。

### 2. 自动配置原理 ⭐

> 面试官想听：出现率最高的 Spring Boot 面试题，按"三个注解 → 选择器 → imports 文件 → 条件注解"四步讲。

`@SpringBootApplication` 是三合一：

```text
@SpringBootConfiguration   —— 本质是 @Configuration，标记配置类
@EnableAutoConfiguration   —— 自动配置的总开关
@ComponentScan             —— 扫描主类所在包及子包的组件
```

自动配置的加载链路：

```text
@EnableAutoConfiguration
  → @Import(AutoConfigurationImportSelector)
  → 读取所有 jar 包的 META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports
    （Spring Boot 2.7 之前是 META-INF/spring.factories）
  → 拿到全部候选自动配置类（如 DataSourceAutoConfiguration、RedisAutoConfiguration）
  → 用条件注解逐个过滤，符合条件的才注册为 Bean
```

条件注解是筛选的关键：`@ConditionalOnClass`（类路径有某类才生效）、`@ConditionalOnMissingBean`（用户没自定义才生效——这就是"默认配置永远让位给你的配置"）、`@ConditionalOnProperty`（配置项满足才生效）。

**自定义 starter 思路**：建两个模块 `xxx-autoconfigure`（写自动配置类 + 条件注解）和 `xxx-starter`（只做依赖聚合），并在 autoconfigure 模块的 `AutoConfiguration.imports` 文件里登记配置类。面试能说出这两个模块的分工即可。

### 3. 配置体系 ⭐

> 面试官想听：@ConfigurationProperties 与 @Value 怎么选，以及配置优先级。

```yaml
# application.yml：冒号后必须有空格，缩进两个空格
server:
  port: 8080
spring:
  profiles:
    active: dev          # 激活 dev 环境
app:
  todo:
    cache-ttl: 10m
    key-prefix: "todo:"
```

多环境：`application-dev.yml`、`application-prod.yml`、`application-test.yml`，由 `spring.profiles.active` 决定加载哪套；启动时可覆盖：`java -jar app.jar --spring.profiles.active=prod`。

两种读取方式：

```java
// 批量绑定：前缀下的配置映射成对象，类型安全、可加校验（推荐）
@Component
@ConfigurationProperties(prefix = "app.todo")
@Data
public class TodoProperties {
    private Duration cacheTtl;
    private String keyPrefix;
}

// 单个读取：适合零散配置，支持 SpEL（@Value("#{...}")）
@Value("${server.port}")
private int port;
```

配置优先级（高 → 低）：命令行参数 > Java 系统属性 > 操作系统环境变量 > `application-{profile}.yml` > `application.yml`。一句话：越"外部、越具体"的越优先，便于部署时用环境变量覆盖。

### 4. Web 实战规范 ⭐

> 面试官想听：统一返回体 + 全局异常 + 参数校验是一套组合拳，体现工程规范意识。

**RESTful 风格**：URL 表示资源（名词复数），HTTP 方法表示动作，状态码表达结果——`GET /api/todos` 列表、`POST /api/todos` 创建、`PUT /api/todos/1` 更新、`DELETE /api/todos/1` 删除。

**统一返回体**：

```java
@Data
public class Result<T> {
    private int code;        // 业务码：200 成功，4xx 客户端问题，5xx 服务端问题
    private String message;
    private T data;

    public static <T> Result<T> ok(T data) { return build(200, "success", data); }
    public static <T> Result<T> fail(int code, String message) { return build(code, message, null); }
}
```

**全局异常处理**：

```java
@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(MethodArgumentNotValidException.class)   // 参数校验失败
    public Result<Void> handleValid(MethodArgumentNotValidException e) {
        String msg = e.getBindingResult().getFieldErrors().stream()
                .map(f -> f.getField() + ": " + f.getDefaultMessage())
                .collect(Collectors.joining("; "));
        return Result.fail(400, msg);
    }

    @ExceptionHandler(BusinessException.class)                 // 业务异常：返回明确提示
    public Result<Void> handleBiz(BusinessException e) {
        return Result.fail(e.getCode(), e.getMessage());
    }

    @ExceptionHandler(Exception.class)                         // 兜底：不暴露堆栈给前端
    public Result<Void> handleOther(Exception e) {
        log.error("unexpected error", e);
        return Result.fail(500, "系统繁忙，请稍后重试");
    }
}
```

**参数校验**：引入 `spring-boot-starter-validation`，实体上打约束注解，Controller 参数前加 `@Valid`，失败异常由上面的全局处理器接住：

```java
public record TodoCreateRequest(
        @NotBlank(message = "标题不能为空")
        @Size(max = 50, message = "标题最长 50 字") String title,
        @Size(max = 500) String content) {}

@PostMapping("/api/todos")
public Result<TodoVO> create(@Valid @RequestBody TodoCreateRequest req) {
    return Result.ok(todoService.create(req));
}
```

**日志**：门面 slf4j + 实现 Logback（Boot 默认），用 Lombok 的 `@Slf4j` 注入 logger；级别 `TRACE < DEBUG < INFO < WARN < ERROR`，生产默认 INFO；配置输出格式与滚动策略，禁止 `System.out.println`（不走级别控制、无上下文、影响性能）。

### 5. 整合与部署

- **MyBatis-Plus**：引入 starter + 驱动，yml 配数据源，`@MapperScan` 扫 Mapper 包，继承 `BaseMapper` 即得 CRUD（下一篇专讲）。
- **Redis**：引入 `spring-boot-starter-data-redis`；默认 `RedisTemplate` 用 JDK 序列化（乱码且跨语言差），推荐 `StringRedisTemplate` + 手动 JSON 序列化，或自定义 key/value 序列化器。
- **Actuator**：`/actuator/health` 健康检查、`/actuator/info`、`/actuator/metrics`，是接监控体系（Prometheus）的基础，生产注意暴露范围。
- **打包部署**：`mvn clean package` 打出可执行 fat jar（内嵌 Tomcat），`java -jar xxx.jar --spring.profiles.active=prod` 直接运行；Docker 部署本质就是把 jar 拷进镜像用 `java -jar` 启动。

## 🛠 动手实践（本指南第一个完整项目）

### 任务 ⭐：todo-list REST API（3 天，贯穿本篇所有知识点）

**第 1 步：建库建表**

```sql
CREATE DATABASE todo_db DEFAULT CHARSET utf8mb4;
USE todo_db;
CREATE TABLE todo (
  id         BIGINT PRIMARY KEY AUTO_INCREMENT,
  title      VARCHAR(50)  NOT NULL,
  content    VARCHAR(500),
  done       TINYINT      NOT NULL DEFAULT 0 COMMENT '0未完成 1完成',
  created_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

**第 2 步：工程骨架**——`spring-boot-starter-web` + `spring-boot-starter-validation` + 数据库/持久层 + Redis 依赖；`application-dev.yml`（本地数据库）与 `application-prod.yml`（改端口 8081、日志级别 WARN）双环境。

**第 3 步：实现接口**——实体 Todo、Mapper、Service、Controller 四层；接口清单：

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | /api/todos?done=false&page=1&size=10 | 分页条件查询 |
| GET | /api/todos/{id} | 详情（走 Redis 缓存） |
| POST | /api/todos | 新增，@Valid 校验 |
| PUT | /api/todos/{id} | 更新 |
| DELETE | /api/todos/{id} | 删除 |

**第 4 步：横切能力**——`Result<T>` 统一返回、`GlobalExceptionHandler` 三段式异常处理、`BusinessException`（如 id 不存在抛 404）、`@Slf4j` 记录入参出参。

**第 5 步：Redis 缓存查询结果**：

```java
public TodoVO getById(Long id) {
    String key = todoProperties.getKeyPrefix() + id;
    String cached = stringRedisTemplate.opsForValue().get(key);
    if (cached != null) return objectMapper.readValue(cached, TodoVO.class);
    TodoVO vo = todoMapper.selectById(id);
    if (vo == null) throw new BusinessException(404, "待办不存在");
    stringRedisTemplate.opsForValue().set(key, objectMapper.writeValueAsString(vo),
                                          todoProperties.getCacheTtl());
    return vo;
}
```

注意：新增/更新/删除后删除对应缓存 key（先更新库，再删缓存）。

**验收标准清单（全部满足才算完成）**：

- [ ] 10 个验收点逐一自测：POST 缺标题返回 400 + 统一错误体，正常创建返回 `code=200` 与 data。
- [ ] GET 单个：首次查库、二次命中 Redis（日志可见），更新后缓存被删、再次查询回源。
- [ ] 查询不存在的 id 返回业务码 404 而不是 500。
- [ ] 分页接口 page/size/done 条件生效。
- [ ] DELETE 后 GET 返回 404。
- [ ] 手动抛 RuntimeException 能被全局异常兜底为统一 500 体，控制台有堆栈。
- [ ] `--spring.profiles.active=prod` 启动后端口变为 8081。
- [ ] `mvn clean package` 打出 fat jar，`java -jar` 运行功能不缩水。
- [ ] `/actuator/health` 返回 `{"status":"UP"}`。
- [ ] 代码分层清晰：Controller 只做参数处理，业务在 Service。

## 💼 高频面试题

**Q：Spring Boot 自动配置的原理？**
- @EnableAutoConfiguration 通过 AutoConfigurationImportSelector 读取各 jar 的 `META-INF/spring/...AutoConfiguration.imports` 文件（2.7 前是 spring.factories），拿到全部候选配置类。
- 再用条件注解过滤：@ConditionalOnClass 类存在、@ConditionalOnMissingBean 用户没自定义、@ConditionalOnProperty 配置满足。
- 结论：框架给默认值，用户一旦配置/自定义 Bean 就让位——这就是约定优于配置的实现方式。

**Q：@SpringBootApplication 由哪些注解组成？**
- @SpringBootConfiguration：本质是 @Configuration，标记主类为配置类。
- @EnableAutoConfiguration：开启自动配置。
- @ComponentScan：扫描主类所在包及子包，所以主类要放最外层。

**Q：什么是 starter？如何自定义？**
- starter = 按功能聚合的依赖集合 + 对应自动配置，引入即用，版本由 parent 统一管理。
- 自定义：xxx-autoconfigure 模块写自动配置类（加条件注解）并在 AutoConfiguration.imports 登记；xxx-starter 模块聚合依赖。
- 使用方引入 xxx-starter，配置对应属性即可生效。

**Q：@ConfigurationProperties 和 @Value 怎么选？**
- @ConfigurationProperties 按前缀批量绑定成对象，类型安全、支持 JSR303 校验、支持松散绑定（cache-ttl → cacheTtl），适合一组相关配置。
- @Value 单个注入，支持 SpEL，适合零散的简单值。
- 都能获取配置，但 @Value 不支持复杂对象绑定与校验。

**Q：Spring Boot 的启动流程大概是什么样的？**
- new SpringApplication()：推断应用类型（Servlet/Reactive）、加载 Initializer 与 Listener。
- run()：准备 Environment（加载配置）→ 创建 ApplicationContext → prepareContext 加载主类 → **refresh()（核心：解析自动配置、注册 Bean）** → 回调 CommandLineRunner/ApplicationRunner。
- 一句话：启动 = 准备环境 → 创建并刷新容器（自动配置在这里生效）→ 执行 Runner。

**Q：全局异常处理怎么实现？**
- @RestControllerAdvice + @ExceptionHandler 捕获 Controller 层抛出的异常。
- 细分处理：参数校验异常返回 400、业务异常 BusinessException 返回业务码、Exception 兜底返回 500 并记录日志。
- 配合统一返回体，前端拿到的永远是 `{code, message, data}` 结构。

**Q：为什么推荐 slf4j + Logback？**
- slf4j 是门面（API 抽象），Logback 是实现，门面与实现分离，换实现不改业务代码。
- 有级别控制、异步输出、滚动归档等生产必备能力；System.out 都不具备且不可控。

## 🔗 推荐资料

| 资料 | 说明 | 链接 |
| --- | --- | --- |
| 廖雪峰 Spring Boot 教程 | 从 Hello World 到完整的开发流程 | https://liaoxuefeng.com/books/java/springboot/index.html |
| JavaGuide Spring 常见问题总结 | 含 Spring Boot 面试高频题 | https://javaguide.cn/system-design/framework/spring/spring-knowledge-and-questions-summary.html |
| pdai Spring 知识体系 | 含 Spring Boot 核心机制章节 | https://pdai.tech/md/spring/spring.html |
| 廖雪峰 Maven 教程 | 打包、依赖管理，部署实践的基础 | https://liaoxuefeng.com/books/java/maven/index.html |

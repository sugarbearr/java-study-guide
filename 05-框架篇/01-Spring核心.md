# Spring核心

> **阶段**：框架篇 ｜ **建议时长**：6 天 ｜ **前置**：已完成入门篇/进阶篇

## 🎯 学习目标

- 能说清 IoC/DI 概念与好处，并用注解和 JavaConfig 两种方式完成依赖注入。
- 能按顺序复述 Bean 生命周期，并说出 AOP 代理生成的时机。
- 能解释 JDK 动态代理与 CGLIB 的区别，并手写一个记录接口耗时的切面。
- 能列出 @Transactional 至少 5 种失效场景，并现场演示、修复其中一种。
- 能讲出循环依赖三级缓存的流转过程与"为什么是三级"。
- 能画出 DispatcherServlet 处理请求的完整流程。

## 📖 核心知识点

### 1. IoC 与 DI ⭐

> 面试官想听：能否一句话讲清"控制反转是什么、反转了什么"，以及它解决了什么痛点。

- **IoC（控制反转）**：对象的创建和依赖关系的管理，从程序员手写 `new` 反转为交给 Spring 容器统一负责。**DI（依赖注入）**是 IoC 的实现手段：容器在创建对象时，把依赖的对象"注入"进来。
- 好处：调用方与实现类解耦（换实现只改配置）；便于单测（注入 Mock）；对象生命周期与配置集中管理。
- 注解装配：`@Component` 通用组件，衍生 `@Service / @Repository / @Controller`（语义分层）；注入用 `@Autowired`（Spring 提供，按类型匹配，多个候选配合 `@Qualifier` 或 `@Primary`）、`@Resource`（JDK 规范，默认按名称）。
- JavaConfig：`@Configuration` + `@Bean`，适合装配第三方类（没源码、没法打注解的类）。

```java
@Configuration
public class AppConfig {
    @Bean   // 方法名即 beanName，返回值交给容器管理
    public OrderService orderService(UserRepository repo) {  // 参数自动注入
        return new OrderService(repo);
    }
}
```

**Bean 作用域**：`singleton`（默认，容器内单例）、`prototype`（每次获取新建）、`request`/`session`（Web 环境）。注意：单例 Bean 中持有可变成员变量是并发隐患，尽量无状态。

### 2. Bean 生命周期 ⭐

> 面试官想听：能按顺序说出五个阶段，并知道 AOP 代理在初始化之后、由 BeanPostProcessor 生成。

```text
1. 实例化 Instantiation     —— 反射调用构造器，只是个"毛坯"对象
2. 属性填充 Populate        —— @Autowired / @Value 注入依赖
3. 初始化 Initialization    —— Aware 回调（BeanNameAware/ApplicationContextAware）
                              → BeanPostProcessor#postProcessBeforeInitialization
                              → @PostConstruct → InitializingBean#afterPropertiesSet → init-method
                              → BeanPostProcessor#postProcessAfterInitialization（AOP 代理通常在这里生成）
4. 使用
5. 销毁 Destruction         —— 容器关闭时：@PreDestroy → DisposableBean#destroy → destroy-method
```

记忆抓手：`InstantiationAwareBeanPostProcessor` 前后夹着实例化和初始化；`BeanPostProcessor` 是 AOP、@Autowired 注入等框架能力的扩展点——这也是"Spring 大部分黑魔法都靠 BeanPostProcessor"这个加分项的来源。

### 3. AOP：面向切面编程 ⭐

> 面试官想听：术语不出错 + 两种代理的区别 + 你真实用它做过什么。

- 术语：**连接点 JoinPoint**（可被拦截的方法）、**切点 Pointcut**（筛选连接点的表达式）、**通知 Advice**（拦截后做什么：@Before/@After/@AfterReturning/@AfterThrowing/@Around）、**切面 Aspect**（切点 + 通知）、**织入**（把切面应用到目标对象生成代理）。
- **JDK 动态代理**：基于接口，运行时生成实现相同接口的代理类（`Proxy + InvocationHandler`）。
- **CGLIB**：基于继承，生成目标类的子类字节码，不能代理 final 类/方法。
- Spring Boot 2.x 起默认强制使用 CGLIB（`proxyTargetClass=true`）；有接口也用 CGLIB，保证注入统一。

```java
@Aspect @Component
public class CostAspect {
    @Around("execution(* com.example.demo.controller..*(..))")
    public Object around(ProceedingJoinPoint pjp) throws Throwable {
        long start = System.currentTimeMillis();
        try {
            return pjp.proceed();
        } finally {
            log.info("{} cost {}ms", pjp.getSignature(), System.currentTimeMillis() - start);
        }
    }
}
```

典型应用：接口耗时监控、操作日志、权限校验、接口幂等/限流；`@Transactional` 的底层就是 AOP——这一点直接衔接下一节的事务失效。

### 4. 事务与失效场景大全 ⭐

> 面试官想听：失效场景是 Spring 面试出现率最高的问题之一，要能说出 5 个以上并讲出"失效本质 = 没走到代理"。

`@Transactional` 关键属性：`propagation`（传播行为）、`isolation`（隔离级别）、`rollbackFor`（触发回滚的异常）、`readOnly`、`timeout`。

**传播行为三剑客**：

- `REQUIRED`（默认）：有事务就加入，没有就新建。
- `REQUIRES_NEW`：挂起当前事务，新建独立事务——内部操作是否回滚与外层无关（如"记录操作日志"即使业务回滚也要落库）。
- `NESTED`：在当前事务内打保存点，可回滚到保存点而不影响外层；外层回滚则它一定回滚。

**失效场景大全**：

```java
@Service
public class OrderService {
    public void create() {
        this.doSave();                       // ① 自调用：this 是原始对象不是代理 → 失效
    }
    @Transactional
    public void doSave() { ... }

    @Transactional
    public void bad() {
        try {
            orderMapper.update(...);
        } catch (Exception e) { log.error(...); }   // ② 异常被吞 → 失效
    }

    @Transactional                            // ③ 默认只回滚 RuntimeException/Error
    public void check() throws Exception {
        throw new Exception("受检异常默认不回滚");   // 需 rollbackFor = Exception.class
    }
    // ④ 方法不是 public（代理只拦截 public）
    // ⑤ 类没被 Spring 管理（没加 @Service 等）
    // ⑥ 数据库引擎不支持事务（MyISAM）
    // ⑦ 传播行为配错，如 NOT_SUPPORTED 会以非事务运行
}
```

修复 ①：注入自身代理（`@Autowired private OrderService self;`）、`AopContext.currentProxy()` 或把方法拆到另一个类。记忆主线：**事务由代理实现，一切让调用绕过代理的写法都会失效**。

### 5. 循环依赖与三级缓存 ⭐

> 面试官想听：三级缓存各自存什么、流转过程，以及"为什么二级不够"。

A 依赖 B、B 依赖 A（都是单例、setter/字段注入）时的解法：

```text
一级缓存 singletonObjects      成品 Bean
二级缓存 earlySingletonObjects 提前曝光的半成品（已实例化、未完成属性填充）
三级缓存 singletonFactories    ObjectFactory（能生产早期引用，必要时在这里提前生成 AOP 代理）

流程：A 实例化 → 把 A 的工厂放入三级缓存 → A 填充属性发现要 B
     → B 实例化 → B 填充属性要 A → 从三级缓存拿到 A 的早期引用（放进二级缓存）
     → B 完成初始化进入一级缓存 → A 继续完成初始化进入一级缓存
```

为什么需要三级而不是二级：三级缓存存的是工厂，**只有真正发生循环依赖时才会提前创建 AOP 代理**；没有循环依赖时代理仍走正常初始化后生成，不破坏 Bean 生命周期。二级缓存也能工作，但会迫使所有 Bean 提前生成代理。

边界：构造器注入的循环依赖无解（实例化前就需要对方）；prototype 不处理；Spring Boot 2.6+ 默认禁止循环依赖，启动报错，需 `spring.main.allow-circular-references=true` 放开——官方态度是"循环依赖是设计坏味道，该重构"。

### 6. SpringMVC：请求处理流程 ⭐

> 面试官想听：从请求进来到响应出去，中间经过哪些组件，能说出 HttpMessageConverter 更佳。

```text
请求 → DispatcherServlet（前端控制器，唯一入口）
     → HandlerMapping（根据 URL 找到 Handler 及拦截器链 HandlerExecutionChain）
     → HandlerAdapter → 参数解析（@RequestParam/@PathVariable/@RequestBody）
                        → 反射调用 Controller 方法 → 返回值处理
     → @ResponseBody：HttpMessageConverter 序列化为 JSON 直接写响应（前后端分离主流）
     → 传统视图：ViewResolver 解析视图 → 渲染模板
     → 过程中抛异常 → @ControllerAdvice + @ExceptionHandler 统一捕获
```

**拦截器 vs 过滤器**：过滤器是 Servlet 规范组件，由容器管理，在 DispatcherServlet 之前执行，能拿到的是原始 request/response，适合编码、跨域；拦截器是 Spring 的组件，在 Controller 前后执行，可以注入 Spring Bean、拿到 Handler 信息，适合登录校验、日志、权限。

**参数注解辨析**：`@RequestParam` 接 query/form 单值参数；`@PathVariable` 接 URL 路径占位符；`@RequestBody` 把请求体 JSON 反序列化为对象（Content-Type: application/json，走 HttpMessageConverter）。

全局异常：`@RestControllerAdvice` 捕获所有 Controller 的异常，配合自定义 `BusinessException` 返回统一错误体——下一篇 SpringBoot 实战直接落地。

## 🛠 动手实践

### 任务 1：JavaConfig 演示 IoC/DI（1 小时）

不用任何注解扫包，纯 JavaConfig 装配：

```java
public interface SmsSender { void send(String msg); }
public class AliyunSmsSender implements SmsSender {
    @Override public void send(String msg) { System.out.println("阿里云短信: " + msg); }
}

@Configuration
public class AppConfig {
    @Bean public SmsSender smsSender() { return new AliyunSmsSender(); }
    @Bean public NotifyService notifyService(SmsSender sender) {   // 构造器注入
        return new NotifyService(sender);
    }
}

public class Main {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(AppConfig.class);
        ctx.getBean(NotifyService.class).notifyAll("欢迎注册");
    }
}
```

验收：新增一个 `TencentSmsSender` 实现类，只改 `AppConfig` 一处就能切换实现，体会"面向接口 + 容器装配"的解耦。

### 任务 2：AOP 记录接口耗时（1.5 小时）

用 Spring Boot 建一个最小 Web 项目，写两个 Controller 接口，按上文 `CostAspect` 实现 `@Around` 切面。
验收：调用接口后控制台打印"方法签名 + 耗时"；把切点改成只拦 `service` 包后接口耗时日志消失，验证切点生效范围。

### 任务 3：演示并修复一次事务失效（1.5 小时）

建表 `account(id, balance)`，写转账 Service：

```java
@Service
public class TransferService {
    @Transactional
    public void transfer(Long from, Long to, int amount) {
        accountMapper.decrease(from, amount);
        if (amount > 1000) throw new RuntimeException("超限");  // 制造异常
        accountMapper.increase(to, amount);
    }
}
```

先构造失效版本：另写一个方法 `public void proxy() { this.transfer(...); }` 从外部调 `proxy()`，观察异常抛出后余额仍被扣减（没回滚）。
验收：修复方式三选一（注入自身代理 / 拆方法到另一个 Service / AopContext），修复后异常时两步操作都回滚；能用一句话解释失效原因（自调用绕过了代理）。

## 💼 高频面试题

**Q：什么是 IoC 和 DI？带来了什么好处？**
- IoC：对象的创建与依赖管理由容器负责，控制权从程序员手里反转给框架；DI 是它的实现方式，依赖由容器注入。
- 好处：调用方只依赖接口，替换实现不改代码（解耦）；单测可注入 Mock；生命周期、配置集中管理。
- 装配方式：注解扫包（@Component 系列）与 JavaConfig（@Configuration + @Bean）。

**Q：说说 Bean 的生命周期。**
- 实例化（构造器）→ 属性填充（依赖注入）→ 初始化（Aware 回调 → BeanPostProcessor 前置 → @PostConstruct → afterPropertiesSet → BeanPostProcessor 后置）→ 使用 → 销毁（@PreDestroy → destroy）。
- 加分：AOP 代理在初始化后由 BeanPostProcessor 生成；框架扩展大多通过 BeanPostProcessor 实现。

**Q：Bean 的作用域有哪些？**
- singleton 默认，容器内单例；prototype 每次获取新建。
- Web 环境还有 request、session。
- 注意单例 Bean 里放可变状态有线程安全问题，Service 应保持无状态。

**Q：AOP 是什么原理？JDK 动态代理和 CGLIB 的区别？**
- AOP 把日志、事务等横切逻辑从业务代码中抽离，运行期由代理对象织入。
- JDK 动态代理基于接口（Proxy + InvocationHandler）；CGLIB 基于继承生成子类，不能代理 final 类和方法。
- Spring Boot 2.x 起默认 CGLIB；典型应用：事务、日志、耗时监控、权限。

**Q：@Transactional 的传播行为？**
- REQUIRED（默认）：有事务加入，无则新建。
- REQUIRES_NEW：挂起当前事务另起新事务，内外回滚互不影响，适合"日志必须落库"。
- NESTED：保存点机制，可局部回滚，外层回滚则整体回滚。

**Q：@Transactional 在哪些情况下会失效？**
- 自调用（this 调用绕过代理）、方法非 public、类未被 Spring 管理。
- 异常被 try-catch 吞掉；抛受检异常但没配 rollbackFor。
- 数据库引擎不支持事务（MyISAM）、传播行为配置错误。
- 本质一句话：事务靠 AOP 代理实现，绕过代理就不生效。

**Q：Spring 怎么解决循环依赖？为什么需要三级缓存？**
- 用三级缓存：一级成品、二级半成品、三级 ObjectFactory。
- A 实例化后先暴露工厂引用，B 注入 A 时拿到早期引用，B 先完成，A 再完成。
- 三级缓存的意义：只在发生循环依赖时才提前生成 AOP 代理，不破坏正常生命周期；构造器注入的循环依赖无解，Spring Boot 2.6+ 默认禁止。

**Q：BeanFactory 和 FactoryBean 的区别？**
- BeanFactory 是 IoC 容器的顶层接口，负责生产和管理所有 Bean。
- FactoryBean 是一种特殊 Bean：getObject() 里封装复杂对象的创建逻辑，容器里放的是 getObject() 的产物。
- 想拿 FactoryBean 本身要在 beanName 前加 `&`；MyBatis 的 Mapper 就是通过 MapperFactoryBean 注册的。

**Q：SpringMVC 处理一个请求的流程？**
- DispatcherServlet 统一接收 → HandlerMapping 找到 Handler 和拦截器链 → HandlerAdapter 执行（参数解析、消息转换）→ Controller 返回。
- @ResponseBody 时由 HttpMessageConverter 序列化 JSON 直接写出；传统方式再走 ViewResolver 渲染。
- 异常统一交给 @ControllerAdvice 处理。

**Q：拦截器和过滤器的区别？**
- 过滤器属于 Servlet 规范，在 DispatcherServlet 之前执行，处理原始请求响应，适合编码、跨域、全局 XSS 过滤。
- 拦截器属于 Spring MVC，围绕 Handler 执行，能注入 Spring Bean、拿到处理方法信息，适合鉴权、日志。
- 执行顺序：过滤器 → DispatcherServlet → 拦截器 preHandle → Controller → 拦截器 postHandle/afterCompletion → 过滤器。

## 🔗 推荐资料

| 资料 | 说明 | 链接 |
| --- | --- | --- |
| JavaGuide Spring 常见问题总结 | IoC/AOP/事务/生命周期面试题合集 | https://javaguide.cn/system-design/framework/spring/spring-knowledge-and-questions-summary.html |
| pdai Spring 知识体系 | 从核心机制到源码的体系化目录 | https://pdai.tech/md/spring/spring.html |
| 廖雪峰 Spring 教程 | IoC、AOP、事务的入门实操 | https://liaoxuefeng.com/books/java/spring/index.html |
| 廖雪峰 Maven 教程 | 框架篇所有工程的依赖管理基础 | https://liaoxuefeng.com/books/java/maven/index.html |

---
title: "05-Lambda-Stream与Java8新特性"
description: "阶段：入门篇 ｜ 建议时长：3 天 ｜ 前置：03-集合与泛型.md"
pubDatetime: 2026-08-28T06:00:00
tags:
  - "① 入门篇"

draft: false
---

> **阶段**：入门篇 ｜ **建议时长**：3 天 ｜ **前置**：03-集合与泛型.md

## 学习目标

- 会写 Lambda 与方法引用，能说出「函数式接口 = 一个抽象方法的接口」这一本质。
- 掌握 Function/Consumer/Supplier/Predicate 四大内置接口的输入输出方向。
- 能用 Stream 完成过滤、映射、排序、分组统计、TopN、去重全流程。
- 会正确使用 Optional 链式取值，避免 `get()` 反模式。
- 能按版本脉络说出 Java 9/11/17/21 的代表性新特性。

## 核心知识点

### Lambda 表达式

- 本质：**函数式接口（只有一个抽象方法的接口）的实例**；`@FunctionalInterface` 注解用于声明与校验。
- 语法：`(参数) -> 表达式` 或 `(参数) -> { 语句块; return x; }`；单参数可省括号，无参必须 `()`。

```java
Runnable r = () -> System.out.println("run");
Comparator<Integer> cmp = (a, b) -> a - b;              // 建议用 Integer.compare
list.forEach(x -> System.out.println(x));
```

- Lambda 只能访问 **effectively final**（实际不变）的局部变量——因为局部变量在线程栈上，Lambda 可能被异步执行，捕获引用会引发并发问题；成员变量/静态变量可以修改。
- 匿名内部类能表达多方法接口，Lambda 只服务函数式接口；this 语义也不同（Lambda 中 this 指外围对象）。

### 四大内置函数式接口

面试官想听：能用「输入输出」一句话区分四个接口，并举出各自在 Stream 里的对应方法。

| 接口 | 抽象方法 | 语义 | Stream 中的对应 |
|---|---|---|---|
| `Function<T,R>` | `R apply(T t)` | 输入 T 输出 R（转换） | `map` |
| `Consumer<T>` | `void accept(T t)` | 输入 T 无返回（消费） | `forEach`、`peek` |
| `Supplier<T>` | `T get()` | 无输入输出 T（生产） | `collect(Supplier, ...)`、`Stream.generate` |
| `Predicate<T>` | `boolean test(T t)` | 输入 T 返回布尔（判断） | `filter` |

- 变体：`BiFunction<T,U,R>`、`UnaryOperator<T>`、`IntPredicate` 等针对基本类型的特化版（避免装箱）。

### 方法引用

- Lambda 的简写，四种形式：

```java
list.forEach(System.out::println);          // 对象::实例方法
list.sort(Integer::compare);                // 类::静态方法
map.replaceAll(String::concat);             // 类::实例方法（第一个参数作为调用者）
Supplier<List<String>> s = ArrayList::new;  // 类::new 构造引用
```

- 优先用方法引用让代码更短，但以可读为先。

### Stream：创建与惰性求值

- 创建：`list.stream()`、`Arrays.stream(arr)`、`Stream.of(...)`、`Stream.generate/infinite`、`Files.lines(path)`（读文件行）。
- 操作分两类：**中间操作惰性**（filter/map/sorted/limit/distinct/peek，返回新 Stream，不执行）与**终端操作触发**（forEach/collect/count/reduce/anyMatch，一次消费后流关闭）。
- 不调用终端操作，中间操作永远不执行——验证方式：只写 `stream().map(x -> x * 2)` 不收集，无任何输出。

### map / filter / sorted / collect / groupingBy

面试官想听：groupingBy + count/partitioningBy 是业务统计的高频写法，能直接上代码。

```java
List<Order> orders = ...;
// 过滤 + 映射 + 收集
List<String> names = orders.stream()
        .filter(o -> o.getAmount() > 100)
        .sorted(Comparator.comparing(Order::getAmount).reversed())
        .limit(3)                                   // TopN
        .map(Order::getUser)                        // 一对一转换
        .map(User::getName)
        .collect(Collectors.toList());              // Java 16+ 可直接 .toList()

// 分组统计
Map<String, Long> cnt = orders.stream()
        .collect(Collectors.groupingBy(Order::getStatus, Collectors.counting()));
Map<String, Double> sum = orders.stream()
        .collect(Collectors.groupingBy(Order::getStatus,
                 Collectors.summingDouble(Order::getAmount)));   // 分组求和

// 分区（按条件二分）
Map<Boolean, List<Order>> parts = orders.stream()
        .collect(Collectors.partitioningBy(o -> o.getAmount() > 100));

// 去重与扁平化
List<Integer> distinct = list.stream().distinct().collect(Collectors.toList());
List<String> chars = words.stream().map(w -> w.split(""))
        .flatMap(Arrays::stream).distinct().collect(Collectors.toList());
```

- `reduce` 聚合：`Optional<Integer> sum = nums.stream().reduce(Integer::sum);` 带初值版本返回具体值。
- 数值流避免装箱：`mapToInt(Order::getAmount).sum()/average()/summaryStatistics()`。
- `collect` 到 Map：`Collectors.toMap(Order::getId, o -> o)`；**value 为 null 或 key 重复会抛异常**，需传合并函数：`toMap(k, v, (a, b) -> a)`。

### map vs flatMap

面试官想听：一对一是 map，一对多打散合并是 flatMap——各给一个例子。

- `map`：一对一转换，`Stream<Stream<R>>` 仍是嵌套结构；例：`map(String::length)` 得到长度流。
- `flatMap`：把每个元素转换成流后**压平**合并；例：把句子流拆成单词流、把多层数组拍平。
- 记忆：flatMap = map + flatten（扁平化）。

### 并行流注意点

面试官想听：知道它底层是 ForkJoinPool 公共池，能说出何时不用。

- `list.parallelStream()` 把任务切分后多线程处理再合并；底层使用 **ForkJoinPool.commonPool()**，与全局共享，一个慢任务会拖累整个 JVM 的并行流。
- 适用：**数据量大（万级以上）+ 无状态 + 可无序 + CPU 密集**；ArrayList 数组切分高效，LinkedList/Iterator 源切分代价大。
- 陷阱：操作里修改共享变量会出并发问题；I/O 阻塞任务别用；默认排序 `forEach` 顺序不保证；小数据量并行反而更慢（拆分与合并开销）。

### Optional 正确用法

面试官想听：Optional 是「返回类型语义化」工具（可能为空），不是万能判空器。

```java
Optional<User> opt = repository.findByName(name);          // 方法返回 Optional 表示可能为空
String city = opt.map(User::getAddress)                    // 值存在则转换
                 .map(Address::getCity)                    // 链式穿透多层判空
                 .orElse("unknown");                       // 为空给默认值
String v = opt.orElseGet(() -> loadDefault());             // 默认值昂贵时用 orElseGet（惰性）
opt.orElseThrow(() -> new BizException(404, "未找到"));     // 为空抛业务异常
```

- 正确姿势：作为方法返回值；用 `map/flatMap/filter` 链式处理；`ifPresent(u -> ...)` 替代 isPresent+get。
- 反模式：`opt.get()` 不判空直接取、把 Optional 做字段/入参、`Optional.of(null)`（会 NPE，可空用 `ofNullable`）。

### 接口默认方法

- Java 8 允许接口有 `default` 方法与 `static` 方法：不破坏已有实现类即可给接口加新能力（如 `Collection.stream()`、`Comparator.reversed()`）。
- 类优先原则：同时继承父类方法和实现接口 default 方法时，父类方法优先；冲突的接口 default 必须显式 `A.super.m()`。

### java.time 与版本脉络

面试官想听：知道 SimpleDateFormat 的线程安全问题，以及近年版本的一句话定位。

```java
LocalDateTime now = LocalDateTime.now();
String s = now.format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"));  // 线程安全
LocalDateTime d = LocalDateTime.parse("2026-01-15T10:30", DateTimeFormatter.ISO_LOCAL_DATE_TIME);
long between = ChronoUnit.DAYS.between(now, d);            // 间隔天数
```

| 版本 | 关键特性（一句话） |
|---|---|
| Java 8 | Lambda/Stream/Optional/接口默认方法/java.time |
| Java 9 | 模块化 JPMS、集合工厂方法 List.of、jshell |
| Java 11（LTS） | HttpClient 标准 HTTP 客户端、var 局部变量（Java 10 引入）、String 新方法 |
| Java 14+ | switch 表达式、文本块 `"""`（13+）、instanceof 模式匹配（16+）、record 不可变数据类（16+） |
| Java 17（LTS） | sealed 密封类（限定继承体系）、RandomGenerator、更强 G1 |
| Java 21（LTS） | **虚拟线程**正式发布（轻量级并发，见文件 6）、模式匹配 switch、结构化并发预览 |

- `var` 只用于局部变量且必须有初始值，可读性优先；`record` 一行定义不可变 DTO：`record Point(int x, int y) {}` 自动生成构造/访问器/equals/hashCode。

## 动手实践

### 任务 1：订单列表统计三连

- 要求：构造 20 条订单（用户、金额、状态、日期），分别用 Stream 完成：① 按状态分组统计条数与金额总和；② 金额 Top3 的订单号列表；③ 所有状态为 PAID 的用户去重（`distinct` 或 `toSet`）。
- 验收标准：三问均一条 Stream 表达式完成（不超过 3 行）；TopN 用 `sorted().limit()`；分组用 `groupingBy` 组合 `counting`/`summingDouble`；对比 traditional for 循环版本的行数差异。

### 任务 2：Optional 链式取值

- 要求：`Order -> User -> Address -> City` 的多层嵌套对象，用 Optional 一行取出 city，任一层为 null 返回 `"unknown"`；再写一个「为空则抛 BizException」的版本。
- 验收标准：全程无显式 if (x != null)；故意置空中间对象验证不抛 NPE；能解释为什么不用 `Optional` 做字段。

### 任务 3：LocalDateTime 格式化练习

- 要求：把 `LocalDateTime.now()` 格式化为 `yyyy/MM/dd HH:mm`；解析字符串 `"2026-01-15 10:30:00"`；计算距今的天数；把日期列表格式化后输出。
- 验收标准：`DateTimeFormatter` 定义为 static final 复用；无 SimpleDateFormat 出现；能说出 SimpleDateFormat 非线程安全的后果（数据错乱/异常）。

## 高频面试题

**Q：Java 8 有哪些新特性？⭐**
- Lambda 表达式与函数式接口（Function/Consumer/Supplier/Predicate）。
- Stream API 声明式集合处理，接口 default/static 方法。
- Optional、新的日期时间 API java.time（不可变、线程安全）。
- 方法引用、`HashMap` 红黑树优化、`MetaSpace` 取代永久代。
- 能结合自己最常用的（如 Stream 分组统计）展开一句。

**Q：map 和 flatMap 的区别？⭐**
- map：一对一，把每个元素转换成另一个元素，结果可能嵌套。
- flatMap：一对多转换后扁平化合并成一个流，常用于「拆分/展开」场景。
- 例：`map(this::splitToWords)` 得到 `Stream<List<String>>`；`flatMap` 直接得到 `Stream<String>`。

**Q：Optional 解决什么问题？怎么正确使用？⭐**
- 用类型系统表达「可能为空」，把 NPE 从运行时提前到编译期提示，减少层层判空。
- 正确用法：作为返回值；`map/flatMap/filter` 链式取值；`orElse/orElseGet/orElseThrow` 处理缺省。
- 反模式：直接 get()、用作字段或方法参数、of(null)。

**Q：常见的函数式接口有哪些？**
- Function<T,R> 转换、Consumer<T> 消费、Supplier<T> 生产、Predicate<T> 断言。
- 二元版本 BiFunction/BinaryOperator、基本类型特化 IntStream 相关。
- 在 Stream 中的对应：map/filter/forEach/collect(Supplier)。

**Q：Stream 和 for 循环谁性能好？**
- 小数据量下 for 循环更快（Stream 有 lambda 调用与装箱开销，数值流可缓解）。
- Stream 的价值在可读性、可组合、易并行（parallelStream），万级以上数据且 CPU 密集时并行流可能有优势。
- 面试结论：性能敏感的紧密循环用 for；业务数据处理优先 Stream，瓶颈时再测再换。

**Q：并行流有哪些注意事项？**
- 底层共用 ForkJoinPool.commonPool，任务被全局共享，不适合阻塞/I/O 任务。
- 操作必须无状态、无副作用，不要在 lambda 里改共享集合。
- 数据量小、LinkedList 源、依赖顺序的场景都不适合。

**Q：var 和 record 是干什么的？**
- var：局部变量类型推断，类型由右侧推断，仅限局部变量，提高可读性不改运行时行为。
- record：不可变数据载体，一行声明自动生成构造器、getter、equals/hashCode/toString，适合 DTO 与值对象。

## 推荐资料

| 资料 | 说明 | 链接 |
|---|---|---|
| 廖雪峰 Java 函数式编程 | Lambda/Stream/Optional 系统教程 | https://liaoxuefeng.com/books/java/functional/index.html |
| pdai Java 8 特性 | 新特性全景与代码示例汇总 | https://pdai.tech/md/java/java8/java8.html |
| JavaGuide Java 8 新特性 | 新特性面试向整理与示例 | https://javaguide.cn/java/new-features/java8-tutorial-translate.html |
| 廖雪峰 日期与时间 | java.time 详细用法 | https://liaoxuefeng.com/books/java/datetime/index.html |

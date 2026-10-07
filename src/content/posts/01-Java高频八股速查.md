---
title: "01-Java高频八股速查"
description: "阶段：面试篇 ｜ 用法：遮住答案自测，能独立说出 3 条以上要点再打勾；冲刺期每天过一遍"
pubDatetime: 2026-08-22T10:00:00
tags:
  - "⑦ 面试篇"

draft: false
---

> **阶段**：面试篇 ｜ **用法**：遮住答案自测，能独立说出 3 条以上要点再打勾；冲刺期每天过一遍

## 使用说明

- 每条格式：`- [ ] **Q：xxx？** —— 一句话核心答案 ｜ 详见《对应指南文件名》`，一句话只是提醒方向，真正的标准是**能展开说 3 条以上要点**；
- 顺序按考察频率排列，越靠前越常被问；每道题的完整版答案与追问链在"详见"对应的指南文件里；
- 冲刺期节奏：每天 1~2 个板块，全部过完一轮后重刷未打勾的题；面试前一晚只看打勾但"心里没底"的；
- 八股追问是链式的（如 HashMap → 扩容 → 并发问题 → ConcurrentHashMap），建议按板块连着练，不要跳着背；
- 每个板块开头有一行"面试形式"提示，说明该板块怎么考，按提示的连环问法对练；
- 有精力时点开板块末尾的资料链接读完整版，把每条"一句话答案"扩成自己的 3 条要点；
- 算法与项目经验不在本文件，见[《03-算法刷题路线》](/java-study-guide/posts/03-算法刷题路线/)与[《04-简历与求职指南》](/java-study-guide/posts/04-简历与求职指南/)。

## 自测清单

### Java 基础（20 题）

> 面试形式：单点直问 + 小连环（== → equals → hashCode 连问）；基础题答错一条，面试官会直接调低对整体的评价。

- [ ] **Q：== 与 equals 的区别？** —— == 比较栈里的值（基本类型比值、引用类型比地址），equals 默认同 ==，String 等重写后比较内容 ｜ 详见[《02-面向对象与核心类》](/java-study-guide/posts/02-面向对象与核心类/)
- [ ] **Q：为什么重写 equals 必须重写 hashCode？** —— 约定相等对象必须有相同哈希值，否则重写后两个"相等"对象在 HashMap 中会落到不同桶 ｜ 详见[《02-面向对象与核心类》](/java-study-guide/posts/02-面向对象与核心类/)
- [ ] **Q：String 为什么设计成不可变？** —— private final 存储不暴露修改方法：安全性、hashCode 可缓存、字符串常量池复用 ｜ 详见[《02-面向对象与核心类》](/java-study-guide/posts/02-面向对象与核心类/)
- [ ] **Q：String、StringBuilder、StringBuffer 怎么选？** —— 常量用 String，单线程频繁拼接用 StringBuilder，多线程共享拼接用 StringBuffer ｜ 详见[《02-面向对象与核心类》](/java-study-guide/posts/02-面向对象与核心类/)
- [ ] **Q：Integer 缓存机制？** —— IntegerCache 缓存 -128~127，范围内 == 为 true，范围外必须用 equals，面试常挖箱拆箱 NPE ｜ 详见[《02-面向对象与核心类》](/java-study-guide/posts/02-面向对象与核心类/)
- [ ] **Q：Java 是值传递还是引用传递？** —— 永远是值传递；传对象时复制的是引用值，方法内改属性生效、重新赋值不影响原对象 ｜ 详见[《02-面向对象与核心类》](/java-study-guide/posts/02-面向对象与核心类/)
- [ ] **Q：重载与重写的区别？** —— 重载是同类同名不同参（编译期确定），重写是子类覆盖父类同签名方法（运行期多态）｜ 详见[《02-面向对象与核心类》](/java-study-guide/posts/02-面向对象与核心类/)
- [ ] **Q：接口与抽象类的区别？** —— 抽象类表示"是什么"（单继承、可有状态），接口表示"能做什么"（多实现，Java 8 后可有 default/static 方法）｜ 详见[《02-面向对象与核心类》](/java-study-guide/posts/02-面向对象与核心类/)
- [ ] **Q：final 关键字有哪些用法？** —— 类不可继承、方法不可重写、变量不可重新赋值（引用不变但对象内容可变）｜ 详见[《02-面向对象与核心类》](/java-study-guide/posts/02-面向对象与核心类/)
- [ ] **Q：面向对象三大特性？** —— 封装隐藏细节、继承复用扩展、多态同一方法不同实现（编译看左边、运行看右边）｜ 详见[《02-面向对象与核心类》](/java-study-guide/posts/02-面向对象与核心类/)
- [ ] **Q：Java 异常体系？** —— Throwable 下分 Error（OOM/StackOverflowError 不该捕获）与 Exception，后者分受检异常与运行时异常 ｜ 详见[《04-异常-IO-反射-注解》](/java-study-guide/posts/04-异常-IO-反射-注解/)
- [ ] **Q：反射是什么？有什么用？** —— 运行期动态获取类信息并创建对象、调用方法，是 Spring IoC、MyBatis Mapper 等框架的底层基石 ｜ 详见[《04-异常-IO-反射-注解》](/java-study-guide/posts/04-异常-IO-反射-注解/)
- [ ] **Q：注解的原理？** —— @interface 本质是继承 Annotation 的接口，运行期靠反射读取元数据，Retention 决定保留到源码/字节码/运行期 ｜ 详见[《04-异常-IO-反射-注解》](/java-study-guide/posts/04-异常-IO-反射-注解/)
- [ ] **Q：什么是泛型擦除？** —— 泛型只存在于编译期做类型检查，运行期 List\<String\> 与 List\<Integer\> 都是 List，桥接方法保证多态 ｜ 详见[《03-集合与泛型》](/java-study-guide/posts/03-集合与泛型/)
- [ ] **Q：static 关键字的用法？** —— 静态变量/方法/代码块/内部类都属于类而非实例，静态方法不能访问实例成员，加载时初始化 ｜ 详见[《01-环境搭建与基础语法》](/java-study-guide/posts/01-环境搭建与基础语法/)
- [ ] **Q：内部类有哪些？** —— 成员、静态、局部、匿名内部类；匿名内部类访问局部变量要求 effectively final ｜ 详见[《04-异常-IO-反射-注解》](/java-study-guide/posts/04-异常-IO-反射-注解/)
- [ ] **Q：BigDecimal 为什么能避免精度丢失？** —— 用"无标度整数+标度"精确表示十进制；金额计算必用，除法必须指定舍入模式与精度 ｜ 详见[《02-面向对象与核心类》](/java-study-guide/posts/02-面向对象与核心类/)
- [ ] **Q：Java 8 有哪些新特性？** —— Lambda、函数式接口、Stream、Optional、接口 default 方法、新时间日期 API ｜ 详见[《05-Lambda-Stream与Java8新特性》](/java-study-guide/posts/05-Lambda-Stream与Java8新特性/)
- [ ] **Q：Stream 常用操作？** —— 中间操作 filter/map/sorted/flatMap 惰性执行，终端操作 collect/reduce/count/forEach 触发计算，只能消费一次 ｜ 详见[《05-Lambda-Stream与Java8新特性》](/java-study-guide/posts/05-Lambda-Stream与Java8新特性/)
- [ ] **Q：Optional 解决什么问题？** —— 显式表达"可能为空"，用 map/orElse/ifPresent 链式处理减少 NPE，不建议用作字段 ｜ 详见[《05-Lambda-Stream与Java8新特性》](/java-study-guide/posts/05-Lambda-Stream与Java8新特性/)

### 集合（15 题）

> 面试形式：以 HashMap 为绝对中心向下挖（put → 扩容 → 1.7/1.8 → 线程安全），ConcurrentHashMap 是通往并发板块的衔接点。

- [ ] **Q：ArrayList 和 LinkedList 的区别？** —— 数组随机访问 O(1) vs 双向链表头尾插删 O(1)；实际绝大多数场景用 ArrayList（CPU 缓存友好、无指针开销）｜ 详见[《03-集合与泛型》](/java-study-guide/posts/03-集合与泛型/)
- [ ] **Q：ArrayList 扩容机制？** —— 首次 add 创建容量 10，超出后扩为 1.5 倍并 Arrays.copyOf 拷贝；能预估数据量就指定初始容量 ｜ 详见[《03-集合与泛型》](/java-study-guide/posts/03-集合与泛型/)
- [ ] **Q：HashMap 底层数据结构？** —— 1.8 起数组+链表+红黑树：链表长度 ≥8 且数组长度 ≥64 转红黑树，节点减到 6 退化回链表 ｜ 详见[《03-集合与泛型》](/java-study-guide/posts/03-集合与泛型/)
- [ ] **Q：HashMap 的 put 流程？** —— 计算 hash 定位桶 → 空桶直接放 → 链表尾插或树插入 → key 已存在则覆盖 → 超过阈值扩容 ｜ 详见[《03-集合与泛型》](/java-study-guide/posts/03-集合与泛型/)
- [ ] **Q：HashMap 扩容机制？** —— 容量翻倍、负载因子 0.75；1.8 优化：元素要么留在原索引，要么移到"原索引+旧容量"位置 ｜ 详见[《03-集合与泛型》](/java-study-guide/posts/03-集合与泛型/)
- [ ] **Q：HashMap 1.7 和 1.8 的区别？** —— 1.7 头插法+纯链表（并发扩容可能成环死循环），1.8 尾插法+红黑树+扩容高位拆分优化 ｜ 详见[《03-集合与泛型》](/java-study-guide/posts/03-集合与泛型/)
- [ ] **Q：HashMap 容量为什么是 2 的幂？** —— 使 (n-1) & hash 等价于取模且位运算更快，同时保证散列均匀 ｜ 详见[《03-集合与泛型》](/java-study-guide/posts/03-集合与泛型/)
- [ ] **Q：HashSet 如何去重？** —— 底层就是 HashMap，元素作 key，add 时先比 hashCode 再比 equals ｜ 详见[《03-集合与泛型》](/java-study-guide/posts/03-集合与泛型/)
- [ ] **Q：ConcurrentHashMap 1.8 的实现原理？** —— CAS 初始化 + synchronized 锁单个桶头节点，扩容支持多线程协助迁移，size 用 CounterCell 分散计数 ｜ 详见[《03-集合与泛型》](/java-study-guide/posts/03-集合与泛型/)
- [ ] **Q：fail-fast 与 fail-safe？** —— 遍历中结构被改抛 ConcurrentModificationException（modCount 校验）；CopyOnWrite 系列是 fail-safe 的快照遍历 ｜ 详见[《03-集合与泛型》](/java-study-guide/posts/03-集合与泛型/)
- [ ] **Q：遍历集合时如何安全删除元素？** —— 用 Iterator.remove() 或 removeIf()，不能在 for-each 中直接 list.remove() ｜ 详见[《03-集合与泛型》](/java-study-guide/posts/03-集合与泛型/)
- [ ] **Q：TreeMap 的底层与使用场景？** —— 红黑树实现，key 有序，支持范围查询与首个/最后一个元素，需自然排序或 Comparator ｜ 详见[《03-集合与泛型》](/java-study-guide/posts/03-集合与泛型/)
- [ ] **Q：List/Set/Queue/Map 怎么选型？** —— 有序可重复选 List、去重选 Set、先进先出/优先级选 Queue、键值映射选 Map，再看是否需要排序与并发 ｜ 详见[《03-集合与泛型》](/java-study-guide/posts/03-集合与泛型/)
- [ ] **Q：ArrayList 线程安全吗？怎么解决？** —— 不安全；Vector 已过时，读多写少用 CopyOnWriteArrayList，或 Collections.synchronizedList ｜ 详见[《01-多线程与并发编程》](/java-study-guide/posts/01-多线程与并发编程/)
- [ ] **Q：Comparable 与 Comparator 的区别？** —— Comparable 在类内部定义自然排序（compareTo），Comparator 外部定制排序规则（compare），后者可多套并存 ｜ 详见[《03-集合与泛型》](/java-study-guide/posts/03-集合与泛型/)

### 并发（20 题）

> 面试形式：追问最深的板块，线程池 7 参数与 synchronized/volatile 几乎必考，常要求现场写出线程池使用代码。

- [ ] **Q：创建线程有几种方式？** —— 本质都是 new Thread 传 Runnable（Callable 配 FutureTask 可拿返回值）；生产环境一律用线程池 ｜ 详见[《01-多线程与并发编程》](/java-study-guide/posts/01-多线程与并发编程/)
- [ ] **Q：线程有哪些状态？** —— NEW/RUNNABLE/BLOCKED/WAITING/TIMED_WAITING/TERMINATED 六种，常追问 wait 与 sleep 的区别 ｜ 详见[《01-多线程与并发编程》](/java-study-guide/posts/01-多线程与并发编程/)
- [ ] **Q：synchronized 的底层原理？** —— 基于对象头 Mark Word 与 monitor（monitorenter/monitorexit 字节码指令），锁状态记录在对象头 ｜ 详见[《01-多线程与并发编程》](/java-study-guide/posts/01-多线程与并发编程/)
- [ ] **Q：锁升级过程？** —— 无锁 → 偏向锁 → 轻量级锁（CAS 自旋）→ 重量级锁（monitor 阻塞），偏向锁在 JDK 15 后已废弃 ｜ 详见[《01-多线程与并发编程》](/java-study-guide/posts/01-多线程与并发编程/)
- [ ] **Q：volatile 的作用？** —— 保证可见性（写立即刷主存、读失效本地缓存）与有序性（内存屏障禁重排），**不保证原子性** ｜ 详见[《01-多线程与并发编程》](/java-study-guide/posts/01-多线程与并发编程/)
- [ ] **Q：JMM（Java 内存模型）是什么？** —— 主内存+工作内存的抽象，定义 happens-before 规则，解决多线程的可见性与有序性问题 ｜ 详见[《01-多线程与并发编程》](/java-study-guide/posts/01-多线程与并发编程/)
- [ ] **Q：CAS 的原理与问题？** —— CPU 原子比较交换指令；存在 ABA（用 AtomicStampedReference 加版本号）与自旋空转问题 ｜ 详见[《01-多线程与并发编程》](/java-study-guide/posts/01-多线程与并发编程/)
- [ ] **Q：一句话说清 AQS？** —— 抽象队列同步器：volatile 的 state + CLH 变体等待队列 + 模板方法，ReentrantLock/Semaphore/CountDownLatch 的共同基石 ｜ 详见[《01-多线程与并发编程》](/java-study-guide/posts/01-多线程与并发编程/)
- [ ] **Q：ReentrantLock 与 synchronized 的区别？** —— 支持可中断、tryLock 超时、公平锁、多个 Condition；JDK 6 后性能相当，简单场景仍用 synchronized ｜ 详见[《01-多线程与并发编程》](/java-study-guide/posts/01-多线程与并发编程/)
- [ ] **Q：公平锁与非公平锁？** —— 公平锁按队列顺序获取防饥饿；非公平锁允许新请求直接插队，吞吐更高，ReentrantLock 默认非公平 ｜ 详见[《01-多线程与并发编程》](/java-study-guide/posts/01-多线程与并发编程/)
- [ ] **Q：线程池的 7 个参数？** —— corePoolSize、maximumPoolSize、keepAliveTime、unit、workQueue、threadFactory、handler ｜ 详见[《01-多线程与并发编程》](/java-study-guide/posts/01-多线程与并发编程/)
- [ ] **Q：线程池的任务执行流程？** —— 先填核心线程 → 满了入队列 → 队列满了开非核心线程 → 到 maximum 后触发拒绝策略（注意"先排队再扩容"）｜ 详见[《01-多线程与并发编程》](/java-study-guide/posts/01-多线程与并发编程/)
- [ ] **Q：四种拒绝策略？** —— AbortPolicy 抛异常（默认）、CallerRunsPolicy 调用者线程执行、DiscardPolicy 静默丢弃、DiscardOldestPolicy 丢最旧任务 ｜ 详见[《01-多线程与并发编程》](/java-study-guide/posts/01-多线程与并发编程/)
- [ ] **Q：线程池大小怎么定？** —— 经验公式 CPU 密集 N+1、IO 密集 N×(1+等待时间/计算时间)，最终靠压测校准，不建议 unbounded 队列 ｜ 详见[《01-多线程与并发编程》](/java-study-guide/posts/01-多线程与并发编程/)
- [ ] **Q：ThreadLocal 原理与内存泄漏？** —— 每个 Thread 内有 ThreadLocalMap，key 是弱引用、value 是强引用，用完必须 remove() 防止 value 泄漏 ｜ 详见[《01-多线程与并发编程》](/java-study-guide/posts/01-多线程与并发编程/)
- [ ] **Q：CountDownLatch/CyclicBarrier/Semaphore 的区别？** —— 一次性倒数开门 / 可复用的集体等齐 / 控制并发数（permits），三者都基于 AQS ｜ 详见[《01-多线程与并发编程》](/java-study-guide/posts/01-多线程与并发编程/)
- [ ] **Q：死锁的产生条件与排查？** —— 互斥、请求与保持、不可剥夺、循环等待四个必要条件；jstack 可直接检测出死锁 ｜ 详见[《01-多线程与并发编程》](/java-study-guide/posts/01-多线程与并发编程/)
- [ ] **Q：CompletableFuture 怎么用？** —— supplyAsync/thenApply/thenCompose/allOf 做异步编排与结果组合，注意默认线程池与异常传播 ｜ 详见[《01-多线程与并发编程》](/java-study-guide/posts/01-多线程与并发编程/)
- [ ] **Q：ConcurrentHashMap 并发 put 为什么安全？** —— 1.8 用 CAS 初始化 + 对桶头节点 synchronized，锁粒度到单个桶；get 无锁靠 volatile ｜ 详见[《01-多线程与并发编程》](/java-study-guide/posts/01-多线程与并发编程/)
- [ ] **Q：虚拟线程是什么？** —— JDK 21 正式特性：由 JVM 调度的轻量线程，阻塞时不占用 OS 线程，可创建百万级，适合 IO 密集场景 ｜ 详见[《01-多线程与并发编程》](/java-study-guide/posts/01-多线程与并发编程/)

### JVM（15 题）

> 面试形式：概念之外一定接实操——CPU 飙高与 OOM 排查两类题要按步骤背熟，最好配上自己跑过的例子。

- [ ] **Q：JVM 内存区域划分？** —— 线程私有：虚拟机栈、本地方法栈、程序计数器；线程共享：堆、方法区（JDK 8 后由元空间实现）｜ 详见[《02-JVM核心》](/java-study-guide/posts/02-JVM核心/)
- [ ] **Q：对象的创建过程？** —— 类加载检查 → 分配内存（TLAB/指针碰撞）→ 零值初始化 → 设置对象头 → 执行构造函数 ｜ 详见[《02-JVM核心》](/java-study-guide/posts/02-JVM核心/)
- [ ] **Q：GC Roots 有哪些？** —— 栈帧局部变量、静态变量、常量引用、JNI 引用、活跃线程等，是可达性分析的起点 ｜ 详见[《02-JVM核心》](/java-study-guide/posts/02-JVM核心/)
- [ ] **Q：四种引用的区别？** —— 强引用不回收；软引用内存不足才回收（缓存）；弱引用下次 GC 必回收（ThreadLocal key）；虚引用仅用于跟踪回收 ｜ 详见[《02-JVM核心》](/java-study-guide/posts/02-JVM核心/)
- [ ] **Q：三种基础 GC 算法？** —— 标记-清除（有碎片）、标记-复制（新生代，浪费空间）、标记-整理（老年代，移动对象慢）｜ 详见[《02-JVM核心》](/java-study-guide/posts/02-JVM核心/)
- [ ] **Q：分代收集的设计？** —— 新生代 Eden:Survivor:Survivor = 8:1:1 用复制算法，对象熬过 15 次 GC（默认）晋升老年代用标记整理 ｜ 详见[《02-JVM核心》](/java-study-guide/posts/02-JVM核心/)
- [ ] **Q：Minor GC 和 Full GC 的区别？** —— Minor 只清新生代、STW 短且频繁；Full GC 清整堆+元空间、STW 长，是性能优化的头号目标 ｜ 详见[《02-JVM核心》](/java-study-guide/posts/02-JVM核心/)
- [ ] **Q：对象什么时候进入老年代？** —— 年龄达阈值（默认 15）、大对象直接进入、动态年龄判断、Survivor 放不下 ｜ 详见[《02-JVM核心》](/java-study-guide/posts/02-JVM核心/)
- [ ] **Q：CMS 的原理与问题？** —— 并发标记-清除收集器，四阶段中标记可并发；产生内存碎片、并发失败退化为 Serial Old，已在新版移除 ｜ 详见[《02-JVM核心》](/java-study-guide/posts/02-JVM核心/)
- [ ] **Q：G1 的原理？** —— 堆划分为多个 Region，按"停顿时间目标"优先回收垃圾最多的 Region（Mixed GC），JDK 9 起默认 ｜ 详见[《02-JVM核心》](/java-study-guide/posts/02-JVM核心/)
- [ ] **Q：ZGC 的特点？** —— 着色指针+读屏障实现并发整理，停顿 <1ms 且与堆大小无关，适合超大堆低延迟场景 ｜ 详见[《02-JVM核心》](/java-study-guide/posts/02-JVM核心/)
- [ ] **Q：类加载过程？** —— 加载 → 验证 → 准备（静态变量赋零值）→ 解析 → 初始化（执行 \<clinit\>），五步常按"什么时候触发初始化"追问 ｜ 详见[《02-JVM核心》](/java-study-guide/posts/02-JVM核心/)
- [ ] **Q：双亲委派模型？** —— 类加载请求逐级向上委托（自定义 → 应用 → 扩展 → 启动），保证核心类安全与唯一；打破场景：SPI、热部署、Tomcat 隔离 ｜ 详见[《02-JVM核心》](/java-study-guide/posts/02-JVM核心/)
- [ ] **Q：CPU 飙到 100% 怎么排查？** —— top 找进程 → top -Hp 找线程 → printf '%x' 转十六进制 → jstack 中按 nid 定位到代码行 ｜ 详见[《02-JVM核心》](/java-study-guide/posts/02-JVM核心/)
- [ ] **Q：OOM 怎么排查？** —— 启动加 -XX:+HeapDumpOnOutOfMemoryError 拿堆转储 → MAT/jvisualvm 分析支配树与大对象 → 沿引用链定位泄漏代码 ｜ 详见[《02-JVM核心》](/java-study-guide/posts/02-JVM核心/)

### Spring/SpringBoot（15 题）

> 面试形式：围绕 Bean 生命周期、事务失效、自动配置三条主线追问，常结合项目问"你项目里怎么用的"。

- [ ] **Q：什么是 IoC 和 DI？** —— IoC 把对象创建与依赖管理交给容器（控制反转），DI 是实现手段：构造器/setter/字段注入 ｜ 详见[《Spring核心》](/java-study-guide/posts/01-Spring核心/)
- [ ] **Q：Bean 的生命周期？** —— 实例化 → 属性填充 → Aware 回调 → BeanPostProcessor 前置 → 初始化（@PostConstruct/afterPropertiesSet）→ 后置处理 → 销毁 ｜ 详见[《Spring核心》](/java-study-guide/posts/01-Spring核心/)
- [ ] **Q：三级缓存如何解决循环依赖？** —— 成品池/早期引用池/工厂池三步走，只能解决单例 + setter 注入的循环依赖，构造器依赖无解 ｜ 详见[《Spring核心》](/java-study-guide/posts/01-Spring核心/)
- [ ] **Q：Bean 的作用域？** —— singleton（默认，容器单例）、prototype（每次新建）、request/session 等 Web 作用域 ｜ 详见[《Spring核心》](/java-study-guide/posts/01-Spring核心/)
- [ ] **Q：AOP 的原理？** —— 运行期动态代理织入横切逻辑：目标类有接口走 JDK 动态代理，无接口走 CGLIB 子类代理 ｜ 详见[《Spring核心》](/java-study-guide/posts/01-Spring核心/)
- [ ] **Q：JDK 动态代理与 CGLIB 的区别？** —— JDK 基于接口反射实现代理，CGLIB 生成子类字节码；final 类/方法无法被 CGLIB 代理 ｜ 详见[《Spring核心》](/java-study-guide/posts/01-Spring核心/)
- [ ] **Q：Spring 事务的传播行为？** —— REQUIRED（默认，有事务则加入）、REQUIRES_NEW（挂起当前另开新事务）、NESTED（嵌套保存点）等 7 种 ｜ 详见[《Spring核心》](/java-study-guide/posts/01-Spring核心/)
- [ ] **Q：Spring 事务失效的场景？** —— 自调用（this 绕过代理）、方法非 public、异常被 catch 吞掉、默认只回滚 RuntimeException、引擎不支持事务 ｜ 详见[《Spring核心》](/java-study-guide/posts/01-Spring核心/)
- [ ] **Q：SpringMVC 的执行流程？** —— 请求到 DispatcherServlet → HandlerMapping 找处理器 → HandlerAdapter 调用 Controller → 返回视图渲染 ｜ 详见[《Spring核心》](/java-study-guide/posts/01-Spring核心/)
- [ ] **Q：SpringBoot 自动配置原理？** —— @EnableAutoConfiguration 读取 AutoConfiguration.imports 文件，配合 @ConditionalOnClass 等条件注解按需装配 ｜ 详见[《SpringBoot实战》](/java-study-guide/posts/02-SpringBoot实战/)
- [ ] **Q：starter 是什么？** —— 依赖聚合 + 自动配置的封装，引入即用；自定义 starter = 自动配置模块 + starter 空壳依赖 ｜ 详见[《SpringBoot实战》](/java-study-guide/posts/02-SpringBoot实战/)
- [ ] **Q：@Autowired 和 @Resource 的区别？** —— @Autowired 是 Spring 的，先按类型后按名称；@Resource 是 JSR-250 的，先按名称后按类型 ｜ 详见[《SpringBoot实战》](/java-study-guide/posts/02-SpringBoot实战/)
- [ ] **Q：@ConfigurationProperties 与 @Value 怎么选？** —— 前者批量绑定前缀配置、类型安全、支持校验；后者适合单个值，支持 SpEL ｜ 详见[《SpringBoot实战》](/java-study-guide/posts/02-SpringBoot实战/)
- [ ] **Q：@Configuration 与 @Component 的区别？** —— @Configuration 类被 CGLIB 代理，@Bean 方法互调仍走容器保证单例；@Component 下互调会 new 新对象 ｜ 详见[《Spring核心》](/java-study-guide/posts/01-Spring核心/)
- [ ] **Q：BeanFactory 和 FactoryBean 的区别？** —— BeanFactory 是容器顶层接口；FactoryBean 是"生产 Bean 的 Bean"，用于封装复杂对象的构建（如 SqlSessionFactoryBean）｜ 详见[《Spring核心》](/java-study-guide/posts/01-Spring核心/)

### MyBatis（8 题）

> 面试形式：题量少但 #{} vs ${} 与 Mapper 动态代理几乎必问，答好后会转向 MyBatis-Plus 与分页等使用细节。

- [ ] **Q：#{} 和 ${} 的区别？** —— #{} 是预编译占位符防 SQL 注入；${} 是字符串拼接，只用于动态表名/列名等受控场景 ｜ 详见[《MyBatis》](/java-study-guide/posts/03-MyBatis/)
- [ ] **Q：一级缓存与二级缓存？** —— 一级是 SqlSession 级默认开启；二级是 namespace 级需手动开启，跨会话共享，分布式下易脏读生产慎用 ｜ 详见[《MyBatis》](/java-study-guide/posts/03-MyBatis/)
- [ ] **Q：Mapper 接口没有实现类为什么能执行 SQL？** —— JDK 动态代理 MapperProxy 拦截方法调用，接口全限定名+方法名映射到 XML 的 statement id ｜ 详见[《MyBatis》](/java-study-guide/posts/03-MyBatis/)
- [ ] **Q：常用动态 SQL 标签？** —— if/where/choose/when/otherwise/set/foreach/trim，用于条件拼接与批量插入 ｜ 详见[《MyBatis》](/java-study-guide/posts/03-MyBatis/)
- [ ] **Q：resultMap 什么时候用？** —— 列名与属性名不一致、一对一/一对多关联映射、自定义类型转换时使用 ｜ 详见[《MyBatis》](/java-study-guide/posts/03-MyBatis/)
- [ ] **Q：MyBatis 的分页方案？** —— RowBounds 是内存逻辑分页（全查再截取，有 OOM 风险）；生产用 PageHelper 物理分页（改写 SQL 加 LIMIT）｜ 详见[《MyBatis》](/java-study-guide/posts/03-MyBatis/)
- [ ] **Q：MyBatis-Plus 有哪些特性？** —— BaseMapper 通用 CRUD、Wrapper 条件构造器、分页/乐观锁插件、自动填充、代码生成器 ｜ 详见[《MyBatis》](/java-study-guide/posts/03-MyBatis/)
- [ ] **Q：MyBatis 和 JPA 怎么选？** —— SQL 需要精细控制、复杂查询多选 MyBatis（国内主流）；标准 CRUD 快速开发选 JPA/Hibernate ｜ 详见[《MyBatis》](/java-study-guide/posts/03-MyBatis/)

## 深入学习资料

| 资料 | 说明 | 链接 |
| --- | --- | --- |
| JavaGuide Java 基础面试题（系列共 3 篇） | 基础题的完整版答案与追问 | https://javaguide.cn/java/basis/java-basic-questions-01.html |
| JavaGuide 集合面试题（系列共 3 篇） | HashMap/ConcurrentHashMap 深挖 | https://javaguide.cn/java/collection/java-collection-questions-01.html |
| JavaGuide 并发面试题（系列共 3 篇） | 线程池/AQS/volatile 逐层追问 | https://javaguide.cn/java/concurrent/java-concurrent-questions-01.html |
| JavaGuide JVM 面试题 | 内存区域、GC、类加载完整版 | https://javaguide.cn/java/jvm/jvm-interview-questions.html |
| JavaGuide Spring 常见问题 | 事务、循环依赖、AOP 深挖 | https://javaguide.cn/system-design/framework/spring/spring-knowledge-and-questions-summary.html |
| JavaGuide MyBatis 面试题 | 缓存、Mapper 原理完整版 | https://javaguide.cn/system-design/framework/mybatis/mybatis-interview.html |
| JavaGuide 面试突击版 | 冲刺期快速过题的浓缩版 | https://interview.javaguide.cn/home.html |
| pdai 面试知识体系 | 按专题组织的 Java 面试题库 | https://pdai.tech/md/interview/x-interview.html |

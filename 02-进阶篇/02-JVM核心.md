# 02-JVM核心

> **阶段**：进阶篇 ｜ **建议时长**：5 天 ｜ **前置**：建议先学 01-多线程与并发编程.md

## 🎯 学习目标

- 能默画运行时数据区五块区域，并说明哪些线程共享、哪些线程私有。
- 能演示三种 OOM（堆、栈、元空间）并说出对应参数。
- 能讲清类加载五阶段、双亲委派模型及其打破场景。
- 掌握 GC 判活算法、四种引用、三大回收算法与 G1 的核心特点。
- 会用 jps/jstat/jmap/jstack/arthas 完成 CPU 飙高与 Full GC 频繁的排查。

## 📖 核心知识点

### ⭐运行时数据区

面试官想听：先分「线程私有 vs 共享」再逐区说职责与 OOM 表现，这是 JVM 面试的第一题。

```
线程私有：程序计数器 ｜ 虚拟机栈（栈帧：局部变量表/操作数栈/动态链接/返回地址）｜ 本地方法栈
线程共享：堆（对象实例；分新生代 Eden+2*Survivor / 老年代）｜ 元空间 Metaspace（类元数据）
```

- **程序计数器**：当前线程字节码执行行号，唯一不会 OOM/StackOverflow 的区域。
- **虚拟机栈**：每个方法调用压入一个栈帧；递归过深抛 `StackOverflowError`；线程过多也可能 OOM（无法创建本地线程）。
- **堆**：GC 主战场；`-Xms` 初始大小、`-Xmx` 最大大小；分配不下的对象抛 `java.lang.OutOfMemoryError: Java heap space`。
- **元空间**（Java 8 取代永久代）：存类元信息、常量池（运行时常量）、静态变量移至堆（Java 8 起在堆中）；用本地内存，`-XX:MaxMetaspaceSize` 限制，动态生成类过多会 OOM: Metaspace。
- 直接内存（NIO DirectByteBuffer）：不属于运行时数据区但受 `-XX:MaxDirectMemorySize` 限制。

### 对象创建与内存布局

- 创建流程：检查类是否已加载 → 分配内存（指针碰撞/空闲列表；TLAB 线程私有缓冲避免并发竞争）→ 零值初始化 → 设置对象头（哈希码、GC 分代年龄、锁标志）→ 执行构造方法。
- 内存布局三部分：**对象头**（Mark Word + 类型指针 + 数组长度）、**实例数据**、**对齐填充**（8 字节整数倍）。
- 对象分配优先在 Eden（TLAB），大对象直接进老年代（`-XX:PretenureSizeThreshold`），长期存活（年龄 ≥ 15）晋升老年代。

### 各区域 OOM 演示

```java
List<byte[]> heapLeak = new ArrayList<>();          // OOM: Java heap space
while (true) heapLeak.add(new byte[1024 * 1024]);

public void stackOverflow(int i) { stackOverflow(i + 1); }   // StackOverflowError

// OOM: Metaspace —— CGLIB/反射在循环里动态生成类不回收
// 启动参数：-Xmx32m -Xss128k -XX:MaxMetaspaceSize=16m
```

- 排查的第一步永远是让 OOM 时自动 dump：`-XX:+HeapDumpOnOutOfMemoryError -XX:HeapDumpPath=/tmp`。

### ⭐类加载五阶段

面试官想听：加载→验证→准备→解析→初始化的顺序，以及「准备阶段赋默认值、初始化阶段才执行 <clinit>」的细节。

- **加载**：读取字节码生成 Class 对象；**验证**：格式/元数据/字节码/符号引用合法性；**准备**：为静态变量分配内存并赋**零值**（`static int a = 1` 此时 a=0；被 `static final` 修饰的常量则直接赋值）；**解析**：符号引用转直接引用；**初始化**：执行静态变量赋值与静态代码块（`<clinit>`，JVM 保证加锁、只执行一次）。
- 触发初始化的时机（主动引用）：`new`、读写静态字段（非 final）、调用静态方法、反射、子类初始化触发父类、main 所在类。
- 不触发初始化：通过子类引用父类静态字段、数组定义、访问 final 常量（编译期已入常量池）。
- 验证练习：`static int a = 1; static int b;` 中准备阶段后 a=0、b=0，`<clinit>` 执行后 a 才等于 1；`static final int C = 1` 在准备阶段即赋值（ConstantValue 属性）。
- 类加载器是隔离的基础：同一个 `.class` 被两个不同加载器加载会得到两个互不兼容的 Class 对象（`instanceof` 为 false），Tomcat 多应用隔离正基于此。

### ⭐类加载器与双亲委派

面试官想听：三层加载器 + 「先委托父加载器，父无法加载才自己加载」的流程，能说出安全与唯一性两个意义。

```
Bootstrap（核心类库 rt.jar，C++ 实现）← 扩展类加载器 PlatformClassLoader ← 应用类加载器 AppClassLoader ← 自定义类加载器
```

- 流程：收到加载请求先向上委托，父加载器能加载就返回；都到顶仍失败才逐层向下由子加载器尝试。
- 意义：① 安全——用户自定义 `java.lang.String` 不会被加载替换核心类；② 唯一——同一个类只被加载一次，保证 `Class` 对象全局唯一。
- **打破双亲委派的场景**：SPI/JDBC（`Thread.contextClassLoader` 线程上下文类加载器反向委托）、OSGi/容器热部署（每个模块独立加载器）、Tomcat 的 WebappClassLoader（先自己加载 web 应用类实现隔离）。

### ⭐GC Roots 可达性分析

面试官想听：能列举至少四类 GC Roots，并说清与引用计数的对比（为什么 Java 不用引用计数）。

- 可作为 GC Roots 的对象：**虚拟机栈（栈帧局部变量表）引用的对象、方法区类静态变量引用的对象、方法区常量引用的对象、JNI（本地方法栈）引用的对象、活跃线程、锁持有的对象**。
- 从 Roots 出发不可达 ⇒ 可回收。相比引用计数，可达性分析能正确处理循环引用（Java 不用引用计数的核心原因）。
- 四种引用（强 → 软 → 弱 → 虚）：强引用不回收；**软引用**内存不足才回收（缓存）；**弱引用**下次 GC 必回收（WeakHashMap、ThreadLocalMap 的 key）；虚引用仅用于回收通知（堆外内存管理）。

### 回收算法与分代

- **标记-清除**：标记可达后清除；缺点：效率不稳、内存碎片。
- **标记-复制**：内存分两块，存活对象复制到另一半；无碎片、效率高，代价是可用内存减半——**适合存活率低的新生代**（Eden:S0:S1 = 8:1:1）。
- **标记-整理**：存活对象向一端移动；无碎片但移动成本高——**适合存活率高的老年代**。
- Minor GC：回收新生代，Eden 满触发，复制算法，STW 短；对象年龄 +1。
- **Full GC（Major GC）触发条件**：老年代空间不足、元空间不足、`System.gc()` 建议、空间分配担保失败、大对象直接分配失败。STW 时间长，**线上要重点监控**。

### ⭐垃圾收集器演进：CMS → G1 → ZGC

面试官想听：按「追求更短停顿」这条主线串起演进，能说出 G1 三点核心设计。

| 收集器 | 特点 | 局限 |
|---|---|---|
| Parallel GC（1.8 默认） | 吞吐量优先，多线程并行回收 | 停顿长 |
| CMS（9 已移除） | 并发标记清除，停顿短 | 碎片、并发失败退化、CPU 敏感 |
| **G1（9+ 默认）** | 分 Region 管理、可预测停顿（`-XX:MaxGCPauseMillis=200`）、整体标记整理+局部复制 | 大堆下的记忆集开销 |
| ZGC/Shenandoah | 着色指针/读屏障，停顿 <1ms，支持 TB 级堆 | 吞吐略有损耗，版本要求高 |

- **G1 三个关键词**：Region 化布局（不再物理分代，逻辑上分 Eden/Survivor/Old/Humongous）、按停顿目标优先回收「垃圾最多」的 Region（Garbage First 得名）、并行并发混合回收。

### 常用 JVM 参数表

| 参数 | 作用 | 常用值 |
|---|---|---|
| -Xms / -Xmx | 堆初始/最大（两者设为相同避免抖动） | 2g / 2g |
| -Xss | 单线程栈大小 | 512k~1m |
| -Xmn | 新生代大小 | 堆的 1/3 |
| -XX:MetaspaceSize / MaxMetaspaceSize | 元空间初始/上限 | 256m |
| -XX:MaxGCPauseMillis | G1 停顿目标 | 200 |
| -XX:+HeapDumpOnOutOfMemoryError | OOM 自动 dump | 开启 |
| -XX:+PrintGCDetails（或 -Xlog:gc*） | GC 日志 | 开启 |
| -XX:SurvivorRatio / PretenureSizeThreshold | Eden 比 / 大对象阈值 | 8 / 视情况 |

### ⭐排查工具箱与两个经典案例

面试官想听：工具会一个一个报出名字，并按固定套路描述排查过程，这是校招/社招的「过程分」。

- 工具：`jps`（进程号）、`jstat -gcutil pid 1000`（GC 统计）、`jmap -heap`/`jmap -dump:live,format=b,file=heap.hprof pid`（堆转储）、`jstack pid`（线程栈）、`jinfo`、图形化 jconsole/VisualVM/MAT/JProfiler、在线诊断 **Arthas**（`dashboard`、`thread -n 3`、`heapdump`、`trace`）。
- Arthas 三步上手：`curl -O arthas-boot.jar` 启动选择进程 → `dashboard` 总览线程/内存/GC → `thread -b` 直接找死锁、`watch 类名 方法名 '{params,returnObj}'` 观察入参出参，无需重启应用。

**CPU 100% 排查流程：**
1. `top` 找到高 CPU 的 Java 进程 PID。
2. `top -Hp pid` 找到该进程内高 CPU 的线程 TID。
3. `printf '%x' TID` 把线程号转十六进制。
4. `jstack pid | grep -A 30 '0x十六进制'` 定位线程栈，看它卡在哪个业务方法。
5. 常见原因：死循环、正则回溯、频繁 Full GC（GC 线程本身占满）。

**内存泄漏排查思路：**
1. 现象确认：jstat 观察 Old 区持续上涨、Full GC 后回收很少。
2. `jmap -dump` 导出堆快照（或 OOM 自动 dump）。
3. MAT/VisualVM 分析支配树，找 Retained Size 最大的对象链，定位到持有引用的业务代码。
4. 常见泄漏源：静态集合只增不减、ThreadLocal 未 remove、监听器/回调未注销、连接未关闭。

## 🛠 动手实践

### 任务 1：堆 OOM 复现并用 jmap 定位

- 要求：用 `-Xmx32m -XX:+HeapDumpOnOutOfMemoryError -XX:HeapDumpPath=/tmp` 启动一段「List 持续添加 1MB 数组」的代码，触发 OOM；用 MAT 或 `jmap -histo pid` 找到占用最大的类型。
- 验收标准：能截出 OOM 日志与 dump 分析图；能说出「哪一行代码持有引用、为什么 GC 无法回收」；写出让堆存活参数生效的完整启动命令。

### 任务 2：jstack 分析死锁

- 要求：写两个线程互锁（A 锁 o1 等 o2，B 锁 o2 等 o1），启动后执行 `jstack pid`。
- 验收标准：找到输出中的 `Found one Java-level deadlock` 段落并贴出两个线程的栈帧；能按栈信息对上代码中两把锁的获取顺序；改造成按序加锁后死锁消失。

### 任务 3：jstat 观察 Full GC

- 要求：程序周期性创建大对象但不持有引用，再改造成持续持有引用两个版本；`jstat -gcutil pid 500` 观察 Eden/Survivor/Old/FGC 变化。
- 验收标准：能解释 YGC 与 FGC 列数值的变化含义；第二版本出现 Old 持续增长、FGC 次数上升；总结一行结论（Old 涨且 FGC 不降 ≈ 泄漏嫌疑）。

## 💼 高频面试题

**Q：说说 JVM 运行时内存区域。⭐**
- 线程私有：程序计数器（行号）、虚拟机栈（栈帧，StackOverflowError 发生地）、本地方法栈。
- 线程共享：堆（对象实例，分新生代/老年代）、元空间（类元数据，Java 8 取代永久代，用本地内存）。
- 再补一句各区域对应的 OOM 类型，体现理解深度。

**Q：对象什么时候进入老年代？⭐**
- 年龄达到阈值（默认 15，CMS 6）长期存活的对象。
- 大对象直接进入老年代（避免 Eden 与 Survivor 间反复复制）。
- Minor GC 后 Survivor 放不下的对象通过空间分配担保提前进入老年代；动态年龄判断：同龄对象总大小超 Survivor 一半，该年龄及以上直接晋升。

**Q：如何判断对象可以被回收？⭐**
- 可达性分析：从 GC Roots（栈局部变量、静态变量、常量、JNI 引用、活跃线程等）出发，不可达即可回收。
- 引用计数无法处理循环引用，JVM 不采用。
- 补充四种引用强度：强不回收、软引用内存不足回收、弱引用下次 GC 回收、虚引用仅通知。

**Q：G1 和 CMS 的区别？为什么 G1 成为主流？⭐**
- CMS 标记-清除产生碎片，并发失败退化 Serial Old；G1 整体标记整理无碎片。
- G1 按停顿目标优先回收垃圾最多的 Region，停顿可预测可控；CMS 只针对老年代，G1 全堆统一管理。
- CMS 已在 Java 9 移除，G1 自 Java 9 起为默认收集器。

**Q：类加载过程与双亲委派模型。⭐**
- 五阶段：加载、验证、准备（静态变量赋零值）、解析、初始化（执行 <clinit>）。
- 双亲委派：收到请求先委托父加载器，直到 Bootstrap，父加载不了才自己加载。
- 意义：防止核心类被篡改、保证类全局唯一。打破场景：SPI 的线程上下文类加载器、Tomcat 隔离部署、热部署。

**Q：线上 CPU 飙高怎么排查？⭐**
- top 找高 CPU 进程 → top -Hp 找高 CPU 线程 → printf '%x' 转十六进制 → jstack 按线程号 grep 定位栈帧。
- 常见根因：死循环、正则回溯灾难、频繁 GC（看 jstat）。
- 有条件用 Arthas：thread -n 3 一步定位，dashboard 总览。

**Q：Full GC 频繁怎么排查？⭐**
- 先看 GC 日志/jstat 确认频率与每次回收量：Old 回收后仍高 ⇒ 疑似泄漏，dump 分析大对象链。
- 回收后 Old 很低但仍频繁触发 ⇒ 检查堆太小、MetaSpace 不足、System.gc() 调用、内存分配速率过高。
- 手段组合：GC 日志 + jmap dump + MAT 支配树；优化方向：调大堆/元空间、修泄漏、对象池化、降低分配速率。

**Q：有哪些 JVM 调优参数是你常用的？**
- -Xms=-Xmx 固定堆、-Xss 栈、-XX:MaxMetaspaceSize、-XX:MaxGCPauseMillis（G1 停顿目标）。
- 排障三件套：HeapDumpOnOutOfMemoryError、GC 日志、（容器环境）-XX:+UseContainerSupport。
- 强调：调优基于监控数据，不是背参数。

## 🔗 推荐资料

| 资料 | 说明 | 链接 |
|---|---|---|
| pdai JVM 内存结构 | 运行时数据区图文详解 | https://pdai.tech/md/java/jvm/java-jvm-struct.html |
| pdai JVM 垃圾回收 | GC 算法与收集器演进梳理 | https://pdai.tech/md/java/jvm/java-jvm-gc.html |
| pdai 类加载机制 | 双亲委派与打破场景 | https://pdai.tech/md/java/jvm/java-jvm-classload.html |
| JavaGuide JVM 面试题 | 本章面试题的完整版答案 | https://javaguide.cn/java/jvm/jvm-interview-questions.html |

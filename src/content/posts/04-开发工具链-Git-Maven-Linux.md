---
title: "04-开发工具链-Git-Maven-Linux"
description: "阶段：进阶篇 ｜ 建议时长：5 天（可拆开贯穿全程） ｜ 前置：01-入门篇/01-环境搭建与基础语法.md"
pubDatetime: 2026-08-28T13:00:00
tags:
  - "② 进阶篇"

draft: false
---

> **阶段**：进阶篇 ｜ **建议时长**：5 天（可拆开贯穿全程） ｜ **前置**：01-入门篇/01-环境搭建与基础语法.md

## 学习目标

- 能画出 Git 工作区/暂存区/仓库三区模型，说清 `reset --soft/--mixed/--hard` 各回退到哪。
- 会用 `rebase` 整理提交、`cherry-pick` 摘补丁、`stash` 临时存改动，并知道**公共历史禁止 rebase**。
- 能解释 Maven 依赖冲突的两个原则，用 `dependency:tree` 定位并 `<exclusion>` 排除。
- 能在 Linux 上独立完成：起服务、看日志、找进程、探端口、统计 Top10 IP。
- 会走 Java 线上排查命令链：`ps` → `top -Hp` → `printf %x` → `jstack`。

## 核心知识点

### 一、Git

一句话：**Git 本质是对快照和指针的管理**——每次 commit 是一个指向内容快照的对象，分支只是一个可移动的 41 字节指针，`HEAD` 是指向"当前分支"的指针。理解这句，所有命令都只是在动指针。

#### 三区模型

```
工作区(Working Dir) --add--> 暂存区(Index/Stage) --commit--> 本地仓库(.git)
                                                             --push--> 远程仓库(origin)
       <-- checkout/restore --'        <-- reset --'        <-- fetch/pull --'
```

- `git status` 看的其实是"工作区 vs 暂存区 vs HEAD"三者的差异。
- 撤销的核心区别：`restore` 只撤工作区（未 add），`restore --staged` 撤到暂存区（已 add 未 commit），`reset` 撤到已提交（改指针）。

#### 高频命令表

| 目的 | 命令 | 备注 |
|---|---|---|
| 提交但改上一次 | `git commit --amend -m "新信息"` | ⭐**只能改未 push 的提交**，push 后 amend 会造成历史分叉 |
| 建并切分支 | `git switch -c feature/x` | 老写法 `checkout -b` 同义；switch/restore 是新式的分工明确版 |
| 切分支 | `git switch main` | 切分支前工作区必须干净，否则先 stash |
| 合并 | `git merge feature/x` | 保留分支拓扑，可能产生 merge commit |
| 变基 | `git rebase main` | 把当前分支的提交"逐个重放"到 main 之后，历史变线性 |
| 摘单个提交 | `git cherry-pick <sha>` | 紧急修 bug 往 release 分支摘补丁常用 |
| 回退指针 | `git reset --soft/--mixed/--hard HEAD~1` | 见下表 |
| 反做提交 | `git revert <sha>` | 生成一个"新提交"抵消旧改动，**不改历史，公共分支安全** |
| 临时藏改动 | `git stash` / `git stash pop` | 切分支救急；`git stash list` 查 |
| 打标签 | `git tag -a v1.0.0 -m "发布" && git push --tags` | 版本发布用 |
| 只看某人某天的提交 | `git log --since=1.day --until=2.day --author=xxx` | 周报生成器 |
| 逐行找谁写的 | `git blame file.java` | 追责利器 |
| 找某段代码首次出现的提交 | `git log -S "关键词" --oneline` | 排查"这行为什么在这" |

#### reset 三种模式

| 模式 | 指针 | 暂存区 | 工作区 | 用途 |
|---|---|---|---|---|
| `--soft` | 移动 | 保留 | 保留 | 把几个提交"退回未提交"，重新组织成一次提交 |
| `--mixed`（默认） | 移动 | **清空** | 保留 | 退回已 add 状态，边看边重新 add |
| `--hard` | 移动 | 清空 | **丢弃** | 彻底放弃改动，⚠️**不可恢复**（只能靠 `git reflog`） |

- 救命命令：`git reflog` 记录 HEAD 的所有移动，误 `reset --hard` 后 `git reset --hard <reflog里的sha>` 能捞回来。

#### merge vs rebase 与团队协作禁忌

| 维度 | merge | rebase |
|---|---|---|
| 历史 | 保留真实分支轨迹，有 merge commit | 线性、干净、好看 |
| 提交 sha | 不变 | **全部重写**（同一改动新 sha） |
| 冲突处理 | 一次性解决 | 逐个提交解决，可能反复 |
| 适用 | 合到主干、要留痕 | 提交前整理自己的本地小提交、同步上游 |

- **禁忌（必考）：已经 push 到公共分支（多人协作的 main/develop）的提交绝对不要 rebase。** 因为你重写了 sha，别人本地还指着旧历史，各自 rebase 后互相 force push 会把别人的提交冲掉，团队立刻炸锅。
- 安全用法：**只 rebase 自己本地还没推的提交**，或者"我 pull --rebase 把远程改动拉到我提交之前"（这只重写我自己的提交）。
- 冲突解决三步：① `git status` 看哪些文件 `both modified`；② 打开文件找 `<<<<<<< HEAD` / `=======` / `>>>>>>>` 标记，留下正确内容（或 `git checkout --ours/--theirs`）；③ `git add` 标记已解决 → `git commit`（merge 场景）或 `git rebase --continue`。
- `.gitignore` 只忽略**未被跟踪**的文件；已经被提交过的 `.idea/` 加了 ignore 也不会生效，需要 `git rm -r --cached .idea` 再提交。

#### 回滚：revert vs reset

- 未 push：`reset`（改历史，干净）。
- 已 push/生产分支：`revert`（加新提交抵消，历史完整可追溯）。团队规范上主干基本只允许 PR 合并 + revert。

#### GitHub/GitLab 协作流程（PR/MR）

```
fork 仓库 → git clone 自己的 fork → git switch -c fix/xxx → 改代码 → commit → push origin fix/xxx
→ 在网页提 Pull Request（base=上游 main, compare=fix/xxx）→ Code Review → 修改后继续 push（PR 自动更新）
→ 合并 → 删除分支 → git fetch upstream && git switch main && git merge upstream/main
```
- 一句话：**PR 的价值不是搬代码，是把 Review 变成强制流程**——CI 跑测试 + 至少一人 approve 才允许合并。

### 二、Maven

一句话：**约定大于配置的依赖管理 + 标准化构建生命周期**。

#### 坐标与常用 scope

```xml
<dependency>
  <groupId>com.alibaba</groupId>     <!-- 组织 -->
  <artifactId>druid-spring-boot-starter</artifactId>  <!-- 项目名 -->
  <version>1.2.23</version>          <!-- 版本 -->
  <scope>provided</scope>            <!-- 依赖范围 -->
</dependency>
```

| scope | 编译 | 测试 | 打包 | 典型场景 |
|---|---|---|---|---|
| `compile`（默认） | ✅ | ✅ | ✅ | 业务依赖 |
| `provided` | ✅ | ✅ | ❌ | Servlet API（容器已提供）、Lombok（只编译期用） |
| `runtime` | ❌ | ✅ | ✅ | JDBC 驱动（编译只依赖 `java.sql` 接口） |
| `test` | ❌ | ✅ | ❌ | JUnit、Mockito |
| `system` | — | — | — | 已废弃，指向本地 jar 路径 |

- ⭐`scope=provided` 打 war 的场景：Web 项目打 war 部署到外部 Tomcat，`spring-boot-starter-tomcat` 必须 provided，否则和容器自带 Tomcat 冲突启动失败。打可执行 jar 则不需要。

#### 生命周期（一根顺序链）

```
clean → validate → compile → test → package → verify → install → deploy
```
- 命令都是"**执行到该阶段**"，会连带跑前面所有阶段：`mvn package` 会自动 compile + test。
- `install` = 装进本地仓库 `~/.m2/repository`（别人/别的项目才能依赖你）；`deploy` = 推到私服 Nexus。
- 跳过测试：`mvn package -DskipTests`（编译测试代码但不跑）；`-Dmaven.test.skip=true`（连测试代码都不编译，不推荐）。

#### 依赖传递与冲突两个原则

Maven 会自动把你依赖的依赖也拉进来（传递依赖），同一个 jar 出现两个版本就冲突。裁决规则：

1. **就近优先（路径最短者胜）**：A→B→C→X:1.0 与 A→D→X:2.0 冲突时，X:2.0 胜（深度 1 < 深度 3）。
2. **声明优先（同深度时，先声明者胜）**：路径深度相同，pom 里写在上面的那个胜。

排查与处理：

```bash
mvn dependency:tree                          # 看整棵树
mvn dependency:tree -Dverbose -Dincludes=com.fasterxml.jackson.core
mvn dependency:analyze                       # 找出"用了没声明/声明了没用"
```

```xml
<dependency>
  <groupId>org.springframework.boot</groupId>
  <artifactId>spring-boot-starter-web</artifactId>
  <exclusions><exclusion>
      <groupId>org.apache.logging.log4j</groupId>     <!-- 排除冲突的日志实现，只留一个 -->
      <artifactId>log4j-to-slf4j</artifactId>
  </exclusion></exclusions>
</dependency>
```

- 冲突症状：`NoSuchMethodError`（运行时加载到旧版本，方法不存在）、`ClassNotFoundException`、`IncompatibleClassChangeError`。⭐注意 `NoSuchMethodError` 而不是编译报错，就是因为编译期和运行期的 jar 版本不一致。

#### BOM 与 dependencyManagement

- `<dependencyManagement>` **只统一版本号，不真正引入依赖**——子模块 `<dependency>` 写 groupId+artifactId 就够，version 由父 pom 决定。
- Spring Boot 的 `spring-boot-starter-parent` 就是靠继承 + `spring-boot-dependencies` 这个 **BOM**（bill of materials）管理上万个 artifact 的版本，所以业务 pom 里几乎不写 version。
- 不能继承 parent 时改用 `<scope>import</scope>` 导入 BOM。这是"为什么我的依赖不用写版本号"的答案。

#### 聚合 vs 继承

| | 聚合（modules） | 继承（parent） |
|---|---|---|
| pom 元素 | `<modules><module>` | `<parent>` |
| 目的 | 一条命令构建多个模块（reactor 排序） | 复用依赖版本、插件配置、属性 |
| 关系 | 平级，一次性打包 | 父子，属性向下传递 |
- 多模块项目常两者同时用。

#### Gradle 一句对比

- Gradle 用 Groovy/Kotlin DSL（编程式，灵活但可读性看人），**增量构建与依赖缓存快于 Maven**，Android 官方构建工具。Java 后端主流仍是 Maven——面试被问到就说"两者定位一样，Gradle 赢在构建性能与脚本灵活度，Maven 赢在约定简单和生态稳定"。

### 三、Linux

定位：**Java 工程师的 Linux = 上服务器看进程、看日志、看端口**，不需要会写内核。

#### 文件与文本

| 目的 | 命令 |
|---|---|
| 看详情/大小 | `ls -lh`（`-a` 隐藏文件，`-t` 按时间） |
| 目录树 | `tree -L 2` |
| 找文件 | `find /app -name "*.jar"`；`find . -mtime +7 -name "*.log"`（配合 `-delete` 清日志） |
| 搜内容 | `grep -rn "关键词" ./src`（`-r` 递归 `-n` 行号 `-i` 忽略大小 `-C 3` 上下 3 行） |
| 行数 / 头尾 | `wc -l f`、`head -20 f`、`tail -50 f`、⭐`tail -f app.log`（实时跟，`Ctrl+C` 退） |
| 翻页大文件 | `less big.log`（`/关键词` 搜、`n` 下一个、`G` 到底、`q` 退） |

**文本三剑客一句话**：
- `grep` 找：`grep -c "ERROR" app.log`（统计条数）。
- `sed` 改：`sed -i 's/旧值/新值/g' application.yml`（原地全局替换，macOS 要 `sed -i ''`）；`sed -n '10,20p' f` 只打印 10~20 行。
- `awk` 按列算：`awk '{print $1}' access.log | sort | uniq -c | sort -rn | head -10`（第一列计数降序取 Top10）；`awk '$9==500' access.log`（筛状态码 500）。

#### 权限与进程

- `chmod 755 start.sh`：**r=4 w=2 x=1**，`755` = 属主 `rwx`(7)、属组 `r-x`(5)、其他 `r-x`(5)。目录的 x 是"能进入"。
- `chown app:app /app/service` 改属主属组；`chmod -R` 递归（别对着 `/` 手滑）。
- 进程：
  - `ps -ef | grep java` 找 Java 进程（`-ef` 全格式含父 pid；`ps aux` 含 CPU/内存占用）。
  - `kill -15 <pid>` 优雅退出（发 TERM，JVM 会跑 shutdown hook，**先用这个**）；`kill -9 <pid>` 强杀（SIGKILL，不给清理机会，临时文件/锁/消息 ACK 可能残留）。
  - `top` 全局看；交互界面里 `Shift+P` 按 CPU 排序、`Shift+M` 按内存排序、`1` 展开各核、`c` 显示完整命令行。
  - `nohup java -jar app.jar > app.log 2>&1 &` 后台常驻（`nohup` 防挂断，`2>&1` 合并错误流，`&` 后台）；`jobs`/`fg`/`disown` 管理。

#### 网络

| 目的 | 命令 |
|---|---|
| 调接口 | `curl -X POST -H "Content-Type: application/json" -d '{"id":1}' http://localhost:8080/users` |
| 探连通 | `ping host`（只能测 IP 层，很多服务器禁 ICMP） |
| 探端口 | `telnet 127.0.0.1 6379` 或 `nc -zv 127.0.0.1 6379`（比 telnet 更适合脚本） |
| 看谁在监听 | ⭐`ss -lntp`（新，快）vs `netstat -tunlp`（老，功能一样；精简镜像常没装） |
| 看 IP | `ip addr`（新）vs `ifconfig`（老，net-tools 包里） |
| 域名解析 | `dig +short javaguide.cn`、`nslookup` |

#### vi/vim 三种模式

- **普通模式**（打开即在）：`h j k l` 移动、`w b` 跳词、`dd` 删行、`u` 撤销、`yy` 复制、`p` 粘贴、`G` 到末行、`gg` 到首行、`/xxx` 搜索。
- **插入模式**：`i`（光标前）/ `a`（光标后）/ `o`（新开一行）进入，`Esc` 退出。
- **命令模式**：`:` 进入，`:wq` 保存退出、`:q!` 强制不存退出、`:%s/old/new/g` 全文替换。
- 新人最常卡住的是"不知道自己在哪个模式"——`Esc` 是万能退路。

#### Java 工程师的线上排查命令链

**CPU 打满 / 线程卡死四步（面试手写流程）**：

```bash
ps -ef | grep java                 # 1. 找到应用 pid，比如 20481
top -c -p 20481                    # 2. 看进程；按 Shift+H 进线程视图，Shift+P 按 CPU 排
top -Hp 20481                      #    找出 CPU 最高的线程 tid，比如 20500
printf "%x\n" 20500                # 3. 线程号转 16 进制 → 5014
jstack 20481 | grep -A 30 'nid=0x5014'   # 4. 定位到具体代码行（nid 是 16 进制带 0x）
```

- 补充链：`jmap -histo:live <pid> | head -20` 看对象直方图（大对象嫌疑）；`jmap -dump:live,format=b,file=heap.hprof <pid>` 导堆给 MAT（⚠️会 STW，生产慎用，先摘流量）；`jstat -gcutil <pid> 1000 10` 每秒打印 GC 情况，判断是不是频繁 Full GC。详见[《02-JVM核心》](/java-study-guide/posts/02-JVM核心/)。
- 日志：`tail -f app.log | grep --line-buffered "orderId=123"` 追一笔订单；`grep -E "ERROR|Exception" -C 5 app.log > err.txt` 抓上下文。
- 磁盘满（`No space left on device`）：`df -h` 看哪个分区满 → `du -sh /app/logs/*` 找大头 → `> app.log` 清空（不要 `rm` 正被进程写的文件，句柄不释放空间照样不回来）。
- 内存/负载：`free -h`（看 available 而不是 free）、`uptime`（1/5/15 分钟负载，对比核数）、`vmstat 1 5`。

## 动手实践

### 任务 1：Git 造冲突 + rebase 整理提交

- 要求：① 建 `feature/a` 和 `feature/b` 两个分支改**同一行**，合并制造冲突并解决；② 在 `feature/a` 上用 `git rebase -i HEAD~3` 把 3 个提交（含一个 "fix typo"）压成 1 个语义清晰的提交。
- 验收标准：`git log --oneline` 上只剩 1 条描述规范的提交；能说出 `pick/squash/fixup/drop/reword` 各干什么；能说明为什么这次 rebase 是安全的（**该分支还没 push 给别人**）；冲突文件里没有残留 `<<<<<<<` 标记。

### 任务 2：Maven 依赖冲突定位并排除

- 要求：给项目引入两个各自依赖不同版本 Jackson 的 starter，用 `mvn dependency:tree` 找出实际生效版本，再用 `<exclusion>` + 显式声明统一到指定版本。
- 验收标准：能贴出 `dependency:tree -Dverbose` 里被标记 `omitted for conflict` 的那一行并解释为什么被裁掉；处理后 `mvn dependency:tree` 只出现一个 jackson-databind 版本；能说出 `dependencyManagement` 和 `exclusion` 两种解法的差别（前者统一版本、后者按路径剪枝）。

### 任务 3：Linux 统计 access.log Top10 IP

- 要求：本地造一份 nginx 格式 `access.log`（≥1000 行），一条命令输出访问次数 Top10 的 IP 及次数；再用 `awk` 统计 5xx 响应占比。
- 验收标准：命令为 `awk '{print $1}' access.log | sort | uniq -c | sort -rn | head -10`，能解释每个环节干什么（取列→计数→排序→截断）；5xx 用 `awk '$9>=500{e++} END{print e/NR}' access.log`；说出为什么不能用 `sort -rn` 直接排原文件。

## 高频面试题

- [ ] **Q：merge 和 rebase 的区别？什么时候不能 rebase？⭐** —— merge 保留拓扑生成 merge commit、rebase 重放提交使历史线性但改写 sha；已 push 的公共分支禁止 rebase，会让协作者历史分叉 ｜ 详见[《01-环境搭建与基础语法》](/java-study-guide/posts/01-环境搭建与基础语法/)
- [ ] **Q：git reset 和 git revert 的区别？⭐** —— reset 移动 HEAD 指针改写历史（--soft 留暂存区、--mixed 留工作区、--hard 全丢），只适合未 push；revert 生成反向新提交不改历史，公共分支安全 ｜ 详见[《01-环境搭建与基础语法》](/java-study-guide/posts/01-环境搭建与基础语法/)
- [ ] **Q：Maven 依赖冲突怎么解决？两个原则是什么？⭐** —— 就近优先（路径浅者胜）+ 同深度声明优先；用 mvn dependency:tree -Dverbose 定位，再 exclusion 排除或 dependencyManagement 统一版本 ｜ 详见[《SpringBoot实战》](/java-study-guide/posts/02-SpringBoot实战/)
- [ ] **Q：pom 里为什么不写依赖版本号？⭐** —— 继承 spring-boot-starter-parent 并导入 spring-boot-dependencies 这个 BOM，dependencyManagement 只统版本不引入，子模块省略 version ｜ 详见[《SpringBoot实战》](/java-study-guide/posts/02-SpringBoot实战/)
- [ ] **Q：scope=provided 是什么意思？什么场景用？⭐** —— 编译和测试可用、不打进包，由运行容器提供；典型是打 war 部署外部 Tomcat 时 starter-tomcat 设 provided，以及 Lombok 只编译期生效 ｜ 详见[《SpringBoot实战》](/java-study-guide/posts/02-SpringBoot实战/)
- [ ] **Q：线上 CPU 打满怎么排查？⭐** —— ps -ef|grep java 拿 pid → top -Hp 找最耗 CPU 线程 tid → printf "%x" 转 16 进制 → jstack 按 nid=0x 定位代码；再配合 jstat 看 GC ｜ 详见[《02-JVM核心》](/java-study-guide/posts/02-JVM核心/)
- [ ] **Q：kill -9 和 kill -15 有什么区别？⭐** —— -15 是 SIGTERM，可被捕获，进程能做清理（JVM 会跑 shutdown hook、Spring 能优雅下线）；-9 是 SIGKILL，内核直接杀、不可捕获，连接/锁/临时文件都不清理，生产先试 -15 ｜ 详见[《02-JVM核心》](/java-study-guide/posts/02-JVM核心/)
- [ ] **Q：NoSuchMethodError 是什么问题？怎么查？⭐** —— 编译期与运行期 jar 版本不一致导致方法缺失，属依赖冲突；用 dependency:tree 看实际加载版本、jar 包检查、-verbose:class 看类从哪加载 ｜ 详见[《02-JVM核心》](/java-study-guide/posts/02-JVM核心/)
- [ ] **Q：.gitignore 加了但文件还在被跟踪怎么办？⭐** —— ignore 只对未跟踪文件生效；git rm -r --cached <路径> 取消索引再提交，本地文件不被删 ｜ 详见[《01-环境搭建与基础语法》](/java-study-guide/posts/01-环境搭建与基础语法/)
- [ ] **Q：install 和 deploy 的区别？⭐** —— install 装进本地 ~/.m2 仓库供本机其他项目依赖；deploy 发布到远程私服 Nexus 供团队共享 ｜ 详见[《SpringBoot实战》](/java-study-guide/posts/02-SpringBoot实战/)

## 推荐资料

| 资料 | 用来干什么 | 链接 |
|---|---|---|
| 廖雪峰 Git 教程 | 三区模型、分支管理、冲突与回滚的入门主线 | https://liaoxuefeng.com/books/git/introduction/index.html |
| 廖雪峰 Maven 教程 | 坐标、生命周期、依赖范围的基础讲解 | https://liaoxuefeng.com/books/java/maven/index.html |
| JavaGuide Maven 总结 | 依赖冲突、BOM、多模块的工程化总结 | https://javaguide.cn/tools/maven/maven-best-practice.html |
| pdai Maven 详解 | 生命周期与插件机制的完整知识图谱 | https://pdai.tech/md/techtools/tools-maven-detail.html |
| 慕课 Linux 命令实战 | 服务器排查与 Shell 命令跟练 | https://www.imooc.com/course/list?c=linux |
| 码工具 Linux 命令速查 | 在线查命令参数与用法示例 | https://www.matools.com/linux |

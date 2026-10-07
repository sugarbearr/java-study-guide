# MySQL基础与SQL实战

> **阶段**：数据库篇 ｜ **建议时长**：6 天 ｜ **前置**：无

## 🎯 学习目标

- 能用 Docker 启动 MySQL 8 实例，通过客户端完成建库、建表、造数等基本操作。
- 能说出核心数据类型（int/bigint/varchar/char/datetime/decimal）的选型依据与常见坑。
- 能熟练书写连接查询、分组聚合、子查询、分页 SQL，独立完成本篇 10 道练习题。
- 能背出 SQL 逻辑执行顺序，并用它解释 where/having、别名引用等规则。
- 能说清 JDBC 六步、连接池的作用，以及"从 JDBC 到 MyBatis"的演进原因。

## 📖 核心知识点

### 1. 环境搭建：库、表、行

Docker 一条命令启动 MySQL 8（数据落在具名卷 `mysql-data`，删容器不丢数据）：

```bash
docker run -d --name mysql8 \
  -p 3306:3306 \
  -e MYSQL_ROOT_PASSWORD=root123 \
  -e TZ=Asia/Shanghai \
  -v mysql-data:/var/lib/mysql \
  mysql:8.0.36 \
  --character-set-server=utf8mb4 \
  --collation-server=utf8mb4_general_ci
```

```bash
# 进入命令行客户端
docker exec -it mysql8 mysql -uroot -proot123
```

```sql
SHOW DATABASES;                                    -- 查看所有库
CREATE DATABASE school DEFAULT CHARSET utf8mb4;    -- 建库，字符集统一 utf8mb4
USE school;
SHOW TABLES;                                       -- 查看库中的表
DESC student;                                      -- 查看表结构
```

三个层级：**database（库）→ table（表）→ row（行）/ column（列）**。一个库对应一个业务域（如订单库、用户库），一张表对应一类实体，一行就是一条记录。

客户端工具：命令行 `mysql`、IDEA 自带 Database 面板、Navicat / DataGrip / DBeaver（免费），学习期任选其一即可。

### 2. 数据类型选择与约束 ⭐

> 面试官想听：能否按业务选对类型，并说出"金额为什么用 DECIMAL、字段为什么尽量 NOT NULL"。

| 类型 | 适用场景 | 注意点 |
| --- | --- | --- |
| INT | 状态、数量（约 ±21 亿） | `INT(11)` 的 11 只是显示宽度，不影响存储范围 |
| BIGINT | 主键、雪花 ID | 主键首选，永不溢出 |
| DECIMAL(M,D) | 金额 | FLOAT/DOUBLE 有精度丢失，金额禁用 |
| CHAR(N) | 定长：身份证、MD5 串 | 不足补空格存取略快，过长浪费空间 |
| VARCHAR(N) | 变长：姓名、标题 | 额外 1~2 字节存长度；N 是字符数不是字节数 |
| DATETIME | 绝大多数时间字段 | 无时区转换，8 字节，范围 1000~9999 年 |
| TIMESTAMP | 需要时区转换的场景 | 4 字节，最大只到 2038 年，受时区影响 |

选型三原则：能用数字不用字符串；字段尽量 `NOT NULL` 并给默认值（NULL 会干扰索引、统计和 `COUNT`）；长文本用 TEXT 并考虑拆到扩展表。

常用约束：`PRIMARY KEY`（唯一+非空）、`UNIQUE`、`NOT NULL`、`DEFAULT`、`FOREIGN KEY`。互联网公司普遍**不建物理外键**，只建普通索引并在应用层校验：外键带来级联锁与维护开销，且不利于后续分库分表。

### 3. SQL 三大类

- DDL（定义）：`CREATE / ALTER / DROP / TRUNCATE`，操作表结构。
- DML（操作）：`INSERT / UPDATE / DELETE`，操作数据。
- DQL（查询）：`SELECT`，面试与日常工作的主战场。
- 另有 DCL（`GRANT/REVOKE` 权限）、TCL（`COMMIT/ROLLBACK` 事务），了解即可。

### 4. 查询核心：连接、分组、子查询 ⭐

> 面试官想听：SQL 逻辑执行顺序脱口而出，并能解释"为什么 where 里不能用 select 的别名"。

**SQL 逻辑执行顺序**（书写从 SELECT 开始，执行却不是）：

```text
FROM → ON → JOIN → WHERE → GROUP BY → HAVING → SELECT(含别名) → DISTINCT → ORDER BY → LIMIT
```

两条推论：`WHERE` 阶段早于 `SELECT`，所以引用不了 SELECT 定义的别名，`ORDER BY` 可以；`WHERE` 过滤行，`HAVING` 过滤分组后的结果。

基础骨架：

```sql
SELECT s.name, c.name AS course_name, sc.value
FROM score sc
JOIN student s ON sc.student_id = s.id
JOIN course  c ON sc.course_id  = c.id
WHERE sc.value >= 60
GROUP BY sc.course_id, c.name
HAVING AVG(sc.value) > 80
ORDER BY sc.value DESC
LIMIT 10;
```

**三种连接**：

- `INNER JOIN`：只返回两表都匹配上的行。
- `LEFT JOIN`：左表全部保留，右表匹配不上补 NULL——"查没有 XX 的记录"类题目的标准解法。
- `RIGHT JOIN`：LEFT 的镜像，项目里几乎不用（交换表顺序改写成 LEFT）。

**子查询与 EXISTS**：子查询可出现在 WHERE（标量/列/表）、FROM（派生表）中。`IN` 与 `EXISTS` 的选择：子查询结果集小用 `IN`，外表小用 `EXISTS`，核心思想都是"小表驱动大表"。

**UNION vs UNION ALL**：`UNION` 合并后去重（多一步去重计算，慢），`UNION ALL` 直接拼接（快）；确定无重复数据时一律用 UNION ALL。

### 5. 常用函数与实用写法 ⭐

> 面试官想听：CASE WHEN 行转列、IFNULL 兜底这类"写得出"的硬功夫。

```sql
-- 字符串：拼接、截取、长度、替换
SELECT CONCAT(name, '-', gender) FROM student;
SELECT SUBSTRING(name, 1, 1), LENGTH(name), REPLACE(name, '张', '章') FROM student;

-- 日期：当前时间、加减、差值、格式化
SELECT NOW(), CURDATE();
SELECT DATE_ADD(NOW(), INTERVAL 7 DAY), DATEDIFF(NOW(), '2026-01-01');
SELECT DATE_FORMAT(NOW(), '%Y-%m-%d %H:%i:%s');

-- IFNULL 空值兜底；IF 三元
SELECT IFNULL(value, 0) FROM score;

-- CASE WHEN：分段统计与行转列的核心
SELECT value,
  CASE WHEN value >= 90 THEN 'A'
       WHEN value >= 60 THEN 'B'
       ELSE 'C' END AS grade
FROM score;
```

分页：`LIMIT offset, size`，第 1 页 `LIMIT 0,10`、第 2 页 `LIMIT 10,10`；offset 越大越慢（深分页问题，下一篇详讲）。去重：`SELECT DISTINCT course_id FROM score;`。

COUNT 三兄弟：`COUNT(*)`（InnoDB 有专门优化，推荐）、`COUNT(1)`（与 * 等价）、`COUNT(col)`（不统计该列为 NULL 的行，语义不同）。

### 6. 从 JDBC 到 ORM（衔接框架篇）

**JDBC 六步**：加载驱动 → 获取连接 `DriverManager.getConnection()` → 创建 Statement → 执行 SQL → 处理 ResultSet → 关闭资源（倒序释放）。原生写法痛点：样板代码冗长、SQL 与 Java 代码耦合、结果集要手动映射成对象。

**连接池**解决"连接无法复用"：TCP 建连 + 认证开销大，池子提前建好连接、借还复用。Spring Boot 2.x 起默认 **HikariCP**（轻量高效），国内也常用 **Druid**（阿里出品，自带 SQL 监控页面）。

ORM 演进：JDBC → JdbcTemplate（只省样板代码）→ **MyBatis**（SQL 独立到 XML、结果自动映射、灵活可控）→ JPA/Hibernate（全自动但复杂 SQL 难写）。国内互联网主流是 MyBatis-Plus，框架篇展开。

## 🛠 动手实践

### 任务 1：Docker 起库并熟悉客户端（30 分钟）

按上文命令启动 MySQL 8，命令行和 IDEA Database 面板各连一次。
验收：`SELECT VERSION();` 显示 8.x；能熟练完成建库、`SHOW TABLES`、`DESC`。

### 任务 2：学生-课程-成绩三表并造数（1 小时）

```sql
CREATE DATABASE school DEFAULT CHARSET utf8mb4;
USE school;

CREATE TABLE student (
  id         BIGINT PRIMARY KEY AUTO_INCREMENT,
  name       VARCHAR(20) NOT NULL,
  gender     TINYINT     NOT NULL DEFAULT 1 COMMENT '1男 0女',
  birthday   DATE,
  created_at DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE course (
  id   BIGINT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(30) NOT NULL UNIQUE
);

CREATE TABLE score (
  id         BIGINT PRIMARY KEY AUTO_INCREMENT,
  student_id BIGINT NOT NULL,
  course_id  BIGINT NOT NULL,
  value      DECIMAL(5,1) NOT NULL,
  UNIQUE KEY uk_student_course (student_id, course_id)  -- 一人一课只允许一条成绩
);

INSERT INTO student (name, gender, birthday) VALUES
('张三', 1, '2003-05-12'), ('李四', 1, '2002-11-03'),
('王五', 0, '2003-08-21'), ('赵六', 0, '2004-01-15');

INSERT INTO course (name) VALUES ('语文'), ('数学'), ('英语'), ('体育');

INSERT INTO score (student_id, course_id, value) VALUES
(1,1,85.5),(1,2,92.0),(1,3,78.0),
(2,1,74.0),(2,2,88.5),
(3,1,90.0),(3,3,95.5),
(4,2,59.5);
```

验收：三表能独立查询，也能 JOIN 出"学生名-课程名-分数"宽表。

### 任务 3：10 道经典 SQL 练习（3 天）

前 3 题给思路，先自己写再看答案；后 7 题独立完成。

**第 1 题：每门课程的平均分，只保留平均分大于 80 的课程。**
思路：按课程分组 → 组内求平均 → 对"分组结果"过滤。过滤组必须用 HAVING（WHERE 过滤行且执行在聚合之前）。

```sql
SELECT c.name, AVG(sc.value) AS avg_value
FROM score sc JOIN course c ON sc.course_id = c.id
GROUP BY sc.course_id, c.name
HAVING avg_value > 80;
```

**第 2 题：每门课程最高分对应的学生姓名（考虑并列第一）。**
思路：不能直接 `MAX(value)` 后顺手取姓名（非聚合列会取到错误行）。先分组聚合出"课程-最高分"，再把这个结果当一张表 join 回去查姓名。

```sql
SELECT c.name AS course_name, s.name, t.max_value
FROM (SELECT course_id, MAX(value) AS max_value FROM score GROUP BY course_id) t
JOIN score  sc ON sc.course_id = t.course_id AND sc.value = t.max_value
JOIN course c  ON c.id = sc.course_id
JOIN student s ON s.id = sc.student_id;
```

**第 3 题：查询没有选「数学」课的学生姓名。**
思路：`NOT IN` 的子查询结果含 NULL 时整个查询返回空，推荐 `NOT EXISTS` 或 LEFT JOIN + IS NULL。

```sql
SELECT s.name FROM student s
WHERE NOT EXISTS (
  SELECT 1 FROM score sc
  JOIN course c ON c.id = sc.course_id
  WHERE sc.student_id = s.id AND c.name = '数学'
);
```

**第 4~10 题（独立完成，附提示）：**

| # | 题目 | 提示 |
| --- | --- | --- |
| 4 | 每个学生的平均分并降序排名 | GROUP BY + ORDER BY |
| 5 | 选课数量大于等于 2 门的学生姓名 | COUNT + HAVING |
| 6 | 既选了语文又选了数学的学生 | GROUP BY 后 HAVING COUNT(DISTINCT course_id) = 2 |
| 7 | 每科成绩前两名（考虑并列） | MySQL 8 窗口函数 ROW_NUMBER / RANK |
| 8 | 没有任何选课记录的学生 | LEFT JOIN ... IS NULL 或 NOT EXISTS |
| 9 | 行转列：输出 学生/语文/数学/英语 每人一行 | CASE WHEN + GROUP BY + MAX |
| 10 | 统计 90+、60~89、60 以下各分数段人数 | CASE WHEN 作为分组维度 |

验收：10 题全部在本地库跑出正确结果；第 2、3 题不看答案能复述思路。

## 💼 高频面试题

**Q：CHAR 和 VARCHAR 的区别？**
- CHAR(N) 定长，不足自动补空格，存取效率略高，适合长度固定的值（身份证、MD5）。
- VARCHAR(N) 变长，额外 1~2 字节记录实际长度，省空间，适合长度波动大的值。
- N 都是字符数不是字节数；utf8mb4 下一个中文最多 3 字节，emoji 占 4 字节。

**Q：DATETIME 和 TIMESTAMP 怎么选？**
- DATETIME 8 字节，范围 1000~9999 年，与时区无关；TIMESTAMP 4 字节，最大到 2038 年，存取时做时区转换。
- 一般业务字段用 DATETIME + 应用层统一时区；"跟随客户端时区变化"的全球化场景才考虑 TIMESTAMP。
- 建表常用 `DEFAULT CURRENT_TIMESTAMP` 和 `ON UPDATE CURRENT_TIMESTAMP` 自动维护创建/更新时间。

**Q：DROP、DELETE、TRUNCATE 的区别？**
- DELETE 是 DML：逐行删、可加 WHERE、事务内可回滚、不重置自增。
- TRUNCATE 是 DDL：清空整表、不可回滚、重置自增、速度远快于无 WHERE 的 DELETE。
- DROP 是 DDL：连表带结构一起删，不可回滚。
- 一句话：删部分数据用 DELETE，清空重置用 TRUNCATE，表不要了用 DROP。

**Q：内连接和左连接的区别？**
- INNER JOIN 只返回两表都匹配的行；LEFT JOIN 保留左表全部行，右表匹配不上补 NULL。
- 典型场景："查询所有用户，包括没下过单的"必须 LEFT JOIN；内连接会把没下单的用户丢掉。
- 反向需求"只查没匹配上的行"用 LEFT JOIN + WHERE 右表主键 IS NULL。

**Q：WHERE 和 HAVING 的区别？**
- 执行顺序上 WHERE 在 GROUP BY 之前过滤行，HAVING 在之后过滤分组。
- WHERE 不能用聚合函数，HAVING 可以（此时聚合结果已产生）。
- 能放 WHERE 的条件不放 HAVING：先过滤行，减少参与分组的数据量。

**Q：IN 和 EXISTS 的区别？**
- IN 先执行子查询得到结果集，外表逐行去匹配；EXISTS 以外表为驱动，逐行到子查询探测是否存在。
- 经验法则：子查询结果集小用 IN，外表小用 EXISTS，本质都是小表驱动大表。
- 注意 NOT IN 遇到 NULL 会整体返回空，用 NOT EXISTS 更安全。

**Q：COUNT(*)、COUNT(1)、COUNT(列) 有什么区别？**
- InnoDB 下 COUNT(*) 与 COUNT(1) 等价，官方对 COUNT(*) 有专门优化，推荐使用。
- COUNT(col) 不统计 col 为 NULL 的行，语义不同，不要混用。
- COUNT(主键) 并不更快，没必要替代 COUNT(*)。

## 🔗 推荐资料

| 资料 | 说明 | 链接 |
| --- | --- | --- |
| JavaGuide 数据库基础知识 | 基础概念、范式、数据类型全覆盖 | https://javaguide.cn/database/basis.html |
| JavaGuide SQL 语句面试题 | 经典 SQL 练习题与解析，配合本篇练习 | https://javaguide.cn/database/sql/sql-questions-01.html |
| JavaGuide MySQL 面试题 | 基础+进阶面试题速查 | https://javaguide.cn/database/mysql/mysql-questions-01.html |
| pdai MySQL 知识体系总览 | 从安装到调优的知识目录地图 | https://pdai.tech/md/db/sql-mysql/sql-mysql-overview.html |
| 廖雪峰 JDBC 教程 | 本篇第 6 节 JDBC 六步的代码级讲解 | https://liaoxuefeng.com/books/java/jdbc/index.html |

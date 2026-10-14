# MyBatis

> **阶段**：框架篇 ｜ **建议时长**：4 天 ｜ **前置**：02-SpringBoot实战.md（及数据库篇）

## 🎯 学习目标

- 能说清 #{} 与 ${} 的本质区别，以及什么场景才允许用 ${}。
- 能熟练使用 if/where/choose/set/foreach 编写动态 SQL，并用 resultMap 完成一对多映射。
- 能讲出一二级缓存的作用域与"二级缓存为什么生产慎用"。
- 能给现有项目接入 MyBatis-Plus：BaseMapper、Wrapper、分页、自动填充、逻辑删除、乐观锁。
- 能解释"Mapper 接口没有实现类为什么能执行"（动态代理原理）。

## 📖 核心知识点

### 1. 定位与核心组件

> MyBatis 是半自动 ORM：SQL 自己写（可控、可优化），参数与结果映射自动做（省样板代码）。

核心组件四件套：`SqlSessionFactoryBuilder`（读配置建工厂）→ `SqlSessionFactory`（重量级，全局一份）→ `SqlSession`（轻量，一次会话）→ **Mapper 接口 + XML**（真正的业务入口）。Spring Boot 整合后前三者被容器托管，你只面对 Mapper。

Spring Boot 接入（Boot 3.x 用 `mybatis-plus-spring-boot3-starter`，2.7 用 `mybatis-plus-boot-starter`；裸 MyBatis 用 `mybatis-spring-boot-starter`）：

```yaml
# application.yml
spring:
  datasource:
    url: jdbc:mysql://localhost:3306/todo_db?useSSL=false&serverTimezone=Asia/Shanghai
    username: root
    password: root123
mybatis-plus:
  configuration:
    map-underscore-to-camel-case: true   # created_at → createdAt 自动驼峰映射
  global-config:
    db-config:
      id-type: auto                      # 主键用数据库自增
logging:
  level:
    com.example.demo.mapper: debug       # 打印 SQL，调试必备
```

```java
@SpringBootApplication
@MapperScan("com.example.demo.mapper")   // 扫描 Mapper 接口
public class DemoApplication { ... }
```

### 2. CRUD 与 #{}/${} ⭐

> 面试官想听：#{} 预编译防注入、${} 拼接有风险，必须说出"什么情况下才用 ${}"。

```xml
<select id="getById" resultType="Todo">        <!-- #{} → 占位符 ? -->
  SELECT * FROM todo WHERE id = #{id}
</select>
<insert id="insert" useGeneratedKeys="true" keyProperty="id">  <!-- 主键回填到实体 -->
  INSERT INTO todo (title, content) VALUES (#{title}, #{content})
</insert>
```

- **#{})**：预编译占位符，`#{id}` 变成 `?`，值由 PreparedStatement 安全设置，**防 SQL 注入**，绝大多数场景用它。
- **${}**：字符串直接替换进 SQL，有注入风险。只用于表名、列名、`ORDER BY` 字段这类"不能加引号"的动态部位，且必须用白名单校验：

```java
private static final Set<String> SORTABLE = Set.of("created_at", "title");  // 白名单
// if (!SORTABLE.contains(sortField)) throw new IllegalArgumentException();
```

### 3. 动态 SQL ⭐

> 面试官想听：写过多条件查询就一定用过这些标签，each 标签说得出解决什么问题。

```xml
<select id="search" resultType="Todo">
  SELECT * FROM todo
  <where>                                          <!-- where 标签：自动去掉开头多余的 AND/OR -->
    <if test="done != null">AND done = #{done}</if>
    <if test="keyword != null and keyword != ''">
      AND title LIKE CONCAT('%', #{keyword}, '%')
    </if>
    <choose>                                       <!-- choose/when/otherwise = if/else if/else -->
      <when test="orderBy == 'time'">ORDER BY created_at DESC</when>
      <otherwise>ORDER BY id DESC</otherwise>
    </choose>
  </where>
</select>

<update id="updateTodo">                           <!-- set 标签：自动去掉末尾多余的逗号 -->
  UPDATE todo
  <set>
    <if test="title != null">title = #{title},</if>
    <if test="content != null">content = #{content},</if>
    <if test="done != null">done = #{done},</if>
  </set>
  WHERE id = #{id}
</update>

<insert id="batchInsert">                          <!-- foreach：in 查询 / 批量插入 -->
  INSERT INTO todo (title, content) VALUES
  <foreach collection="list" item="t" separator=",">
    (#{t.title}, #{t.content})
  </foreach>
</insert>
```

记忆口诀：`if` 条件拼接、`where` 去头、`set` 去尾、`choose` 分支、`foreach` 循环。

### 4. resultMap 与关联映射

自动映射搞不定"一对多/一对一"和列名对不上时用 `resultMap`：

```xml
<resultMap id="studentWithScores" type="Student">
  <id property="id" column="id"/>
  <result property="name" column="name"/>
  <collection property="scores" ofType="Score">     <!-- 一对多；一对一用 association -->
    <id property="id" column="score_id"/>
    <result property="courseName" column="course_name"/>
    <result property="value" column="value"/>
  </collection>
</resultMap>

<select id="getStudentWithScores" resultMap="studentWithScores">
  SELECT s.id, s.name, sc.id AS score_id, c.name AS course_name, sc.value
  FROM student s
  LEFT JOIN score sc ON sc.student_id = s.id
  LEFT JOIN course c ON c.id = sc.course_id
  WHERE s.id = #{id}
</select>
```

联表一次查出（结果集映射）适合少量数据；分步查询（先查学生再按 id 查成绩）适合懒加载，但要警惕 **N+1 问题**：查 1 次列表又对每行发 1 次子查询。原则：列表页用联表，详情页可分步。

### 5. 缓存与批量操作 ⭐

> 面试官想听：一级二级缓存的作用域差别，以及"为什么二级缓存生产慎用"。

- **一级缓存**：SqlSession 级别，默认开启。同一 SqlSession 内相同查询直接命中；任何增删改都会清空。Spring 整合后每次请求通常是新 SqlSession，所以平时感觉不到它的存在（同一事务内有效）。
- **二级缓存**：namespace（Mapper）级别，需手动开启（`<cache/>`），跨 SqlSession 共享。慎用原因：多表关联时任一表更新，其他 Mapper 的缓存感知不到，容易读到脏数据；分布式部署下多节点缓存不同步。生产一般不开启，统一用 Redis 做缓存。
- **PageHelper 分页**：`PageHelper.startPage(page, size)` 用 ThreadLocal 携带分页参数，拦截下一条 SQL 自动拼 `LIMIT`，物理分页：

```java
PageHelper.startPage(1, 10);
List<Todo> list = todoMapper.search(keyword, done);
PageInfo<Todo> page = new PageInfo<>(list);   // total、pages 等分页信息
```

注意 startPage 和查询必须紧挨着，且不要 try 包裹后中途 return。

- **批量操作**：小批量用 `foreach` 拼多值 INSERT；大批量（万级）用 `ExecutorType.BATCH` 的 SqlSession 分批 flush，避免 SQL 过长与超参数上限。

### 6. MyBatis-Plus ⭐

> 面试官想听：MP 解决"单表 CRUD 重复劳动"，但复杂 SQL 仍要手写——知道边界比背 API 重要。

```java
@TableName("todo")
public class Todo {
    @TableId(type = IdType.AUTO)
    private Long id;
    private String title;
    private String content;
    private Boolean done;
    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createdAt;
    @TableLogic                                    // 逻辑删除：delete 变 UPDATE deleted=1
    private Integer deleted;
    @Version                                       // 乐观锁版本号
    private Integer version;
}

public interface TodoMapper extends BaseMapper<Todo> {}   // 继承即得 CRUD

// 条件构造器：动态条件不用再写 XML
LambdaQueryWrapper<Todo> qw = new LambdaQueryWrapper<>();
qw.eq(Todo::getDone, false)
  .like(StringUtils.hasText(keyword), Todo::getTitle, keyword)   // 条件为 true 才拼接
  .orderByDesc(Todo::getCreatedAt);
List<Todo> list = todoMapper.selectList(qw);

// 分页插件：物理分页
Page<Todo> page = todoMapper.selectPage(new Page<>(1, 10), qw);
```

三个内置插件一次配齐：

```java
@Bean
public MybatisPlusInterceptor mybatisPlusInterceptor() {
    MybatisPlusInterceptor interceptor = new MybatisPlusInterceptor();
    interceptor.addInnerInterceptor(new PaginationInnerInterceptor(DbType.MYSQL)); // 分页
    interceptor.addInnerInterceptor(new OptimisticLockerInnerInterceptor());       // 乐观锁
    return interceptor;
}

@Component
public class FillHandler implements MetaObjectHandler {     // 自动填充 created_at 等
    @Override
    public void insertFill(MetaObject metaObject) {
        strictInsertFill(metaObject, "createdAt", LocalDateTime.class, LocalDateTime.now());
    }
    @Override
    public void updateFill(MetaObject metaObject) {
        strictUpdateFill(metaObject, "updatedAt", LocalDateTime.class, LocalDateTime.now());
    }
}
```

Service 层用 `IService<Todo>` / `ServiceImpl<TodoMapper, Todo>`，自带 `saveBatch`、`getById`、`page` 等封装。

### 7. 原理与选型 ⭐

> 面试官想听：Mapper 接口原理是 MyBatis 最高频的原理题，答对关键在"JDK 动态代理 + 全限定名定位 SQL"。

```text
@MapperScan 扫描接口 → 每个接口注册为 MapperFactoryBean
调用接口方法 → JDK 动态代理 MapperProxy 拦截
→ 用 接口全限定名.方法名 定位 MappedStatement（XML 里 <select id="..."> 对应一条）
→ SqlSession 执行 JDBC → 结果按映射规则转成对象
```

所以接口无需实现类：**代理对象的 invoke 逻辑就是"方法签名 → SQL 语句 → 执行 → 映射"**，id 的对应关系由"namespace 必须等于接口全限定名"保证。

**MyBatis vs JPA/Hibernate**：MyBatis SQL 可控、好优化、上手快，但每个查询要自己写；JPA 全自动 CRUD、移植性好，但复杂查询/优化受限。国内互联网主流 MyBatis(-Plus)（业务 SQL 复杂、重性能），海外及简单业务系统 JPA 居多——回答时给出"按场景选型"的结论。

## 🛠 动手实践

### 任务 1：给 todo-list 项目接入 MyBatis-Plus（1.5 小时）

替换 SpringBoot 实战篇项目中的持久层实现（保留 Controller/Service 接口不变，体现分层价值）。
验收：`TodoMapper extends BaseMapper<Todo>` 完成 5 个接口的 CRUD；`LambdaQueryWrapper` 实现按 done + 关键字筛选；打开 SQL 日志能看到执行的语句。

### 任务 2：动态 SQL 多条件分页查询（2 小时）

XML 写法：`search` 语句支持 keyword（模糊）、done（等值）、时间范围（`&gt;=` 用 `<![CDATA[ ]]>` 或转义），配合 PageHelper 分页。
验收：四种参数组合（全空/只有 keyword/只有 done/全有）生成的 SQL 各不相同且正确；PageInfo 的 total 与实际数据条数一致。

### 任务 3：MP 三件套生效验证（1.5 小时）

开启分页、自动填充、逻辑删除、乐观锁插件（见第 6 节代码），逐个验证。
验收：分页 SQL 出现 `LIMIT`；insert 自动写入 createdAt；delete 后表里数据还在（`deleted=1`），查询默认过滤已删数据；两个会话并发更新同一条数据，version 冲突时后提交的影响行数为 0，业务代码能感知并重试。

## 💼 高频面试题

**Q：#{} 和 ${} 的区别？**
- #{} 预编译占位符，编译成 `?` 由 PreparedStatement 设值，防 SQL 注入，默认用它。
- ${} 字符串拼接，直接替换进 SQL，有注入风险。
- ${} 只用于动态表名/列名/排序字段等不能加引号的位置，且必须白名单校验。

**Q：MyBatis 的一级、二级缓存？为什么二级慎用？**
- 一级缓存 SqlSession 级默认开启，会话内相同查询命中，增删改清空；Spring 下每次请求新会话，基本感知不到。
- 二级缓存 namespace 级，跨会话共享，需手动开启。
- 慎用原因：多表关联更新时其他 Mapper 感知不到，易脏读；分布式部署多节点不同步。生产一般用 Redis 替代。

**Q：Mapper 接口没有实现类，为什么能执行 SQL？**
- MyBatis 用 JDK 动态代理为接口生成 MapperProxy 代理对象。
- 调用方法时用"接口全限定名.方法名"匹配 XML 里的 MappedStatement（namespace = 接口全限定名，id = 方法名）。
- 代理的 invoke 里走 SqlSession 执行 JDBC 并做结果映射，所以不需要手写实现类。

**Q：动态 SQL 有哪些标签？**
- if 条件拼接；where 自动去掉开头 AND/OR；set 自动去掉末尾逗号。
- choose/when/otherwise 实现多分支；foreach 处理集合（in、批量插入）。
- trim 可自定义前后缀的增删，是 where/set 的底层实现。

**Q：MyBatis 和 JPA/Hibernate 怎么选？**
- MyBatis 半自动：SQL 自己写，可控、易优化，适合复杂查询、报表、互联网业务。
- JPA 全自动：CRUD 零 SQL、开发效率高，但复杂查询难调优。
- 国内主流 MyBatis-Plus：单表交给 MP，复杂 SQL 回到 XML 手写。

**Q：什么是 N+1 问题？怎么避免？**
- 查 1 次主列表后，对每行记录再发 1 次子查询，1 次变 N+1 次，性能崩塌。
- 避免列表页用联表一次查出（resultMap collection/association）。
- 分步查询仅在详情页或确有懒加载需求时使用，并控制列表行数。

**Q：PageHelper 分页的原理？**
- PageHelper.startPage 把分页参数放进 ThreadLocal。
- 拦截器拦截紧跟其后的第一条查询，改写 SQL 追加 LIMIT，并额外发 COUNT 语句求总数。
- 注意 startPage 与查询必须紧邻，防止 ThreadLocal 残留误伤其他 SQL。

## 🔗 推荐资料

| 资料 | 说明 | 链接 |
| --- | --- | --- |
| JavaGuide MyBatis 面试题 | 本篇高频题的标准答案库 | https://javaguide.cn/system-design/framework/mybatis/mybatis-interview.html |
| JavaGuide SQL 语句面试题 | 动态 SQL 要解决的查询场景练手 | https://javaguide.cn/database/sql/sql-questions-01.html |
| JavaGuide MySQL 面试题 | SQL 层面试题与 MyBatis 面试题互补 | https://javaguide.cn/database/mysql/mysql-questions-01.html |
| 廖雪峰 Spring Boot 教程 | 整合数据访问与工程组织的上下文 | https://liaoxuefeng.com/books/java/springboot/index.html |

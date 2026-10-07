#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把根目录的指南 md 迁移为 AstroPaper 内容集合：
1. 为 33 篇文件注入 frontmatter（title/description/pubDatetime/tags/featured），去掉正文 H1
2. 去掉标题里的装饰性 emoji（保留 ⭐ 与详略表的功能色 🔴🟡🟢）
3. 内部 .md 链接 / 《x.md》引用改写为 /java-study-guide/posts/<slug>/
4. 生成 src/content/pages/about.md 与练习场数据 src/data/guide-app.json
"""
import json, os, re, datetime, hashlib, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
POST_BASE = "/java-study-guide/posts"

STAGES = [
    ("总览", ["README.md"]),
    ("① 入门篇", [
        "01-入门篇/01-环境搭建与基础语法.md",
        "01-入门篇/02-面向对象与核心类.md",
        "01-入门篇/03-集合与泛型.md",
        "01-入门篇/04-异常-IO-反射-注解.md",
        "01-入门篇/05-Lambda-Stream与Java8新特性.md",
    ]),
    ("② 进阶篇", [
        "02-进阶篇/01-多线程与并发编程.md",
        "02-进阶篇/02-JVM核心.md",
        "02-进阶篇/03-IO模型与网络编程.md",
    ]),
    ("③ 数据库篇", [
        "03-数据库篇/01-MySQL基础与SQL实战.md",
        "03-数据库篇/02-索引-事务-锁与调优.md",
    ]),
    ("④ 中间件篇", [
        "04-中间件篇/01-Redis.md",
        "04-中间件篇/02-RabbitMQ.md",
        "04-中间件篇/03-Kafka.md",
        "04-中间件篇/04-RocketMQ.md",
        "04-中间件篇/05-Elasticsearch.md",
        "04-中间件篇/06-ZooKeeper与Nacos.md",
        "04-中间件篇/07-Nginx.md",
        "04-中间件篇/08-MongoDB.md",
    ]),
    ("⑤ 框架篇", [
        "05-框架篇/01-Spring核心.md",
        "05-框架篇/02-SpringBoot实战.md",
        "05-框架篇/03-MyBatis.md",
        "05-框架篇/04-SpringCloud微服务.md",
    ]),
    ("⑥ 分布式与高并发篇", [
        "06-分布式与高并发篇/01-分布式理论基础.md",
        "06-分布式与高并发篇/02-高并发系统设计.md",
    ]),
    ("⑦ 面试篇", [
        "07-面试篇/01-Java高频八股速查.md",
        "07-面试篇/02-数据库与中间件面试速查.md",
        "07-面试篇/03-算法刷题路线.md",
        "07-面试篇/04-简历与求职指南.md",
        "07-面试篇/05-选择填空题库.md",
        "07-面试篇/06-考点详略表.md",
    ]),
]
FEATURED = {"ROADMAP.md", "STUDY-TRACKER.md", "05-选择填空题库.md", "06-考点详略表.md"}
EMOJI_CLASS = (
    "\U0001F000-\U0001FAFF\u2190-\u21FF\u2300-\u23FF"
    "\u2600-\u27BF\u2B00-\u2BFF\uFE0F\u200D"
)
DECOR_EMOJI = re.compile(r"^(\s*#{1,6}\s*)(?:[" + EMOJI_CLASS + r"]+\s*)+")

def slug_of(path):
    return path.replace(".md", "").split("/")[-1]

def yaml_str(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'

def strip_decor_emoji(text):
    return "\n".join(DECOR_EMOJI.sub(r"\1", ln) for ln in text.split("\n"))

def first_sentence(md):
    for ln in md.split("\n"):
        t = ln.strip()
        if not t or t.startswith("#"):
            continue
        t = re.sub(r"^>\s*", "", t)
        t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", t)
        t = re.sub(r"[\*`\[\]()]", "", t)
        t = t.strip()
        if len(t) < 12:
            continue
        return t[:100].rstrip("。，；,;")
    return "Java 学习指南章节。"

def stage_index(path):
    for idx, (name, paths) in enumerate(STAGES):
        if path in paths:
            return idx
        if path in ("ROADMAP.md", "STUDY-TRACKER.md") and idx == 0:
            return 0
    raise ValueError(path)

def stage_name(path):
    return STAGES[stage_index(path)][0]

def main():
    all_paths = [p for _, paths in STAGES for p in paths] + ["ROADMAP.md", "STUDY-TRACKER.md"]
    slug2title, contents = {}, {}
    for p in all_paths:
        md = (ROOT / p).read_text(encoding="utf-8")
        m = re.search(r"^#\s+(.+?)\s*$", md, re.M)
        slug2title[slug_of(p)] = m.group(1).strip() if m else slug_of(p)
        contents[p] = md

    out_dir = ROOT / "src" / "content" / "posts"
    out_dir.mkdir(parents=True, exist_ok=True)

    base_dt = datetime.datetime(2026, 8, 20, 9, 0, 0)
    order_index = {p: i for i, p in enumerate(reversed(all_paths))}

    ref_link_re = re.compile(r"(?:｜\s*)?详见\s*\[《[^》]+》\]\((/java-study-guide/posts/[^)]+?)/\)\s*$")
    ref_plain_re = re.compile(r"(?:｜\s*)?详见《([^》]+)》\s*$")
    head_re = re.compile(r"^###\s+(.+?)\s*$", re.M)
    sec_re = re.compile(r"^##\s+(选择题|填空题)\s*$", re.M)
    card_line = re.compile(r"^\s*- \[( |x)\] \*\*Q：(.+?)\*\*\s*——\s*(.+?)\s*$", re.M)

    meta, cards, quiz = [], [], []
    for p in all_paths:
        md = contents[p]
        title = slug2title[slug_of(p)]
        md = re.sub(r"^#\s+.+?\n", "", md, count=1)
        md = strip_decor_emoji(md)

        def repl_link(m):
            return "](%s/%s/)" % (POST_BASE, slug_of(m.group(1).strip()))

        def repl_book(m):
            slug = slug_of(m.group(1).strip())
            return "[《%s》](%s/%s/)" % (slug2title.get(slug, slug), POST_BASE, slug)

        md = re.sub(r"\]\(([^)#]*?\.md)\)", repl_link, md)
        md = re.sub(r"《([^《》]*?\.md)》", repl_book, md)

        desc = first_sentence(md)
        dt = base_dt + datetime.timedelta(hours=7 * order_index[p])
        featured = "\nfeatured: true" if p in FEATURED else ""
        fm = (
            "---\n"
            "title: %s\n"
            "description: %s\n"
            "pubDatetime: %s\n"
            "tags:\n  - %s\n"
            "%s\n"
            "draft: false\n"
            "---\n"
        ) % (yaml_str(title), yaml_str(desc), dt.isoformat(), yaml_str(stage_name(p)), featured)
        (out_dir / os.path.basename(p)).write_text(fm + "\n" + md.lstrip("\n"), encoding="utf-8")

        ck = len(re.findall(r"^\s*- \[( |x)\]", md, re.M))
        meta.append({"path": p, "slug": slug_of(p), "title": title, "ck": ck})

    # ---- about 页 ----
    about = """---
title: 关于本指南
---
一套基于五个优质站点整合的 **Java 后端自学路线 + 知识手册 + 面试冲刺** 三合一指南。

| 站点 | 角色 |
|------|------|
| [廖雪峰 Java 教程](https://liaoxuefeng.com/books/java/introduction/index.html) | 系统入门教材：边读边敲，覆盖语法到 Spring 全家桶 |
| [慕课网《Java入门第一季》](https://www.imooc.com/learn/85) | 零基础免费视频（5 小时），适合完全没编程经验时先看 |
| [JavaGuide](https://javaguide.cn/home.html) | 面试导向的知识点与八股题库，面试篇的主要来源 |
| [pdai.tech Java 全栈知识体系](https://pdai.tech/) | 原理与体系图（并发/JVM/数据库/中间件/架构），进阶篇的主要来源 |
| [码工具 Java 8 中文 API](https://www.matools.com/api/java8) | 随手查类和方法签名的 API 速查手册 |

## 怎么用

- **零基础**：先读[学习路线图](/java-study-guide/posts/ROADMAP/)，然后从[环境搭建与基础语法](/java-study-guide/posts/01-环境搭建与基础语法/)逐篇推进，配合[进度打卡表](/java-study-guide/posts/STUDY-TRACKER/)勾选。
- **有基础**：把[打卡表](/java-study-guide/posts/STUDY-TRACKER/)当自测清单，不会的再进对应文章补。
- **面试冲刺**：过两份[八股速查](/java-study-guide/posts/01-Java高频八股速查/)，刷[选择填空题库](/java-study-guide/posts/05-选择填空题库/)，按[考点详略表](/java-study-guide/posts/06-考点详略表/)取舍精力；「练习场」里有章节小考、综合大考和八股闪卡。
- **离线版**：仓库根目录的 `index.html` 双击即可离线使用全部练习功能。

学习进度按浏览器域名分别保存，可用练习场左下角「导出进度 / 导入进度」迁移。
"""
    (ROOT / "src" / "content" / "pages" / "about.md").write_text(about, encoding="utf-8")

    # ---- 练习场数据（闪卡 + 选择/填空题 + 打卡计数） ----
    files_meta = []
    for i, m in enumerate(meta):
        files_meta.append({
            "id": "f%d" % i, "stage": stage_index(m["path"]),
            "title": m["title"], "url": "%s/%s/" % (POST_BASE, m["slug"]), "ck": m["ck"],
        })

    for i, m in enumerate(meta):
        md = contents[m["path"]]
        is_bank_list = "速查" in m["title"]
        is_bank = "选择填空题库" in m["title"]
        if not (is_bank or is_bank_list):
            continue
        cmarks = [(x.start(), re.sub(r"（\d+\s*题）", "", x.group(1)).strip()) for x in head_re.finditer(md)]
        sec_marks = [(x.start(), {"选择题": "select", "填空题": "blank"}[x.group(1)]) for x in sec_re.finditer(md)]
        sec_marks.append((len(md), None))

        # 闪卡（两份速查清单的 checkbox Q 行）
        for x in card_line.finditer(md):
            cat = ""
            for pos, name in cmarks:
                if pos < x.start():
                    cat = name
                else:
                    break
            ans = x.group(3)
            refurl, reftitle = "", ""
            m1, m2 = ref_link_re.search(ans), ref_plain_re.search(ans)
            if m1:
                refurl = m1.group(1) + "/"
            elif m2:
                slug = slug_of(m2.group(1).strip())
                refurl, reftitle = "%s/%s/" % (POST_BASE, slug), slug2title.get(slug, "")
            ans = ref_link_re.sub("", ref_plain_re.sub("", ans)).strip()
            cards.append({"id": "c" + hashlib.md5(x.group(2).encode()).hexdigest()[:8],
                          "cat": cat, "q": x.group(2).strip(), "a": ans,
                          "ref": refurl, "refTitle": reftitle})

        # 选择/填空题（05-选择填空题库）
        if not is_bank:
            continue
        for (start, kind), (end, _) in zip(sec_marks, sec_marks[1:]):
            body = md[start:end].split("\n", 1)[1]
            for block in re.split(r"^###\s+", body, flags=re.M)[1:]:
                lines = block.splitlines()
                head = re.match(r"(?:\d+[\.、]\s*)?（([^·（）]+)·([^（）]+)）\s*(.+)$", lines[0].strip())
                rest = "\n".join(lines[1:])
                am = re.search(r"^答案[：:]\s*(.+?)\s*$", rest, re.M)
                em = re.search(r"^解析[：:]\s*(.+?)\s*$", rest, re.M)
                if not (head and am and em):
                    print("warn 题库:", block[:40].replace("\n", " "))
                    continue
                cat, diff, stem = head.group(1).strip(), head.group(2).strip(), head.group(3).strip()
                exp = em.group(1).strip()
                refurl, reftitle = "", ""
                m1, m2 = ref_link_re.search(exp), ref_plain_re.search(exp)
                if m1:
                    refurl = m1.group(1) + "/"
                elif m2:
                    slug = slug_of(m2.group(1).strip())
                    refurl, reftitle = "%s/%s/" % (POST_BASE, slug), slug2title.get(slug, "")
                exp = ref_link_re.sub("", ref_plain_re.sub("", exp)).strip()
                qid = "q" + hashlib.md5(stem.encode("utf-8")).hexdigest()[:8]
                if kind == "select":
                    opts = re.findall(r"^-\s*(?:\[)?([A-D])(?:\])?[\.、]\s*(.+)$", rest, re.M)
                    letter = am.group(1).strip().upper()[:1]
                    if len(opts) < 2 or letter not in "ABCD"[:len(opts)]:
                        print("warn 选择题:", stem[:30]); continue
                    quiz.append({"id": qid, "kind": "select", "cat": cat, "diff": diff, "q": stem,
                                 "opts": [o[1].strip() for o in opts], "a": letter, "exp": exp,
                                 "ref": refurl, "refTitle": reftitle})
                else:
                    nblank = len(re.findall(r"＿{2,}", stem))
                    alts = [[x.strip() for x in s.split("／") if x.strip()] for s in re.split(r"[；;]", am.group(1)) if s.strip()]
                    if nblank and len(alts) != nblank:
                        print("warn 填空空数(%d≠%d): %s" % (nblank, len(alts), stem[:30]))
                    quiz.append({"id": qid, "kind": "blank", "cat": cat, "diff": diff, "q": stem,
                                 "alts": alts, "exp": exp, "ref": refurl, "refTitle": reftitle})

    data = {"stages": [name for name, _ in STAGES], "files": files_meta, "cards": cards, "quiz": quiz}
    data_dir = ROOT / "src" / "data"
    data_dir.mkdir(exist_ok=True)
    (data_dir / "guide-app.json").write_text(
        json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    print("迁移完成：%d 篇 posts，%d 张闪卡，%d 道练习题" % (len(meta), len(cards), len(quiz)))

if __name__ == "__main__":
    main()

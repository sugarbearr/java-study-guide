#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把本目录的 Java 学习指南打包成单文件离线 Web 应用（../index.html）。
用法：python3 app/build.py   （改动 md 后重新运行即可）"""
import json, re, os, datetime, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent

STAGES = [
    ("总览", "🧭", [
        "README.md", "ROADMAP.md", "STUDY-TRACKER.md",
    ]),
    ("① 入门篇", "🌱", [
        "01-入门篇/01-环境搭建与基础语法.md",
        "01-入门篇/02-面向对象与核心类.md",
        "01-入门篇/03-集合与泛型.md",
        "01-入门篇/04-异常-IO-反射-注解.md",
        "01-入门篇/05-Lambda-Stream与Java8新特性.md",
    ]),
    ("② 进阶篇", "⚙️", [
        "02-进阶篇/01-多线程与并发编程.md",
        "02-进阶篇/02-JVM核心.md",
        "02-进阶篇/03-IO模型与网络编程.md",
    ]),
    ("③ 数据库篇", "🗄️", [
        "03-数据库篇/01-MySQL基础与SQL实战.md",
        "03-数据库篇/02-索引-事务-锁与调优.md",
    ]),
    ("④ 中间件篇", "🧩", [
        "04-中间件篇/01-Redis.md",
        "04-中间件篇/02-RabbitMQ.md",
        "04-中间件篇/03-Kafka.md",
        "04-中间件篇/04-RocketMQ.md",
        "04-中间件篇/05-Elasticsearch.md",
        "04-中间件篇/06-ZooKeeper与Nacos.md",
        "04-中间件篇/07-Nginx.md",
        "04-中间件篇/08-MongoDB.md",
    ]),
    ("⑤ 框架篇", "🏗️", [
        "05-框架篇/01-Spring核心.md",
        "05-框架篇/02-SpringBoot实战.md",
        "05-框架篇/03-MyBatis.md",
        "05-框架篇/04-SpringCloud微服务.md",
    ]),
    ("⑥ 分布式与高并发篇", "🌐", [
        "06-分布式与高并发篇/01-分布式理论基础.md",
        "06-分布式与高并发篇/02-高并发系统设计.md",
    ]),
    ("⑦ 面试篇", "🎯", [
        "07-面试篇/01-Java高频八股速查.md",
        "07-面试篇/02-数据库与中间件面试速查.md",
        "07-面试篇/03-算法刷题路线.md",
        "07-面试篇/04-简历与求职指南.md",
        "07-面试篇/05-选择填空题库.md",
        "07-面试篇/06-考点详略表.md",
    ]),
]

def title_of(md_text, fallback):
    m = re.search(r'^#\s+(.+?)\s*$', md_text, re.M)
    return m.group(1).strip() if m else fallback

def main():
    # ---------- 读取文件、分配 id ----------
    files, path2id = [], {}
    for si, (sname, icon, paths) in enumerate(STAGES):
        for p in paths:
            text = (ROOT / p).read_text(encoding="utf-8")
            text = re.sub(r"\A---\n.*?\n---\n", "", text, flags=re.S)  # 剥离迁移注入的 frontmatter
            fid = "f%d" % len(files)
            path2id[os.path.normpath(p)] = fid
            files.append({
                "id": fid, "stage": si, "path": p,
                "title": title_of(text, pathlib.Path(p).stem),
                "md": text,
            })

    # ---------- 链接改写：内部 .md 相对链接 → #f/<id>；《path.md》→ 内链 ----------
    for f in files:
        base = os.path.dirname(f["path"])
        text = f["md"]

        def repl_md_link(m, base=base):
            raw = m.group(1).strip()
            norm = os.path.normpath(os.path.join(base, raw))
            fid = path2id.get(norm)
            return "](" + ("#/f/" + fid if fid else raw) + ")"

        text = re.sub(r"\]\(([^)#]*?\.md)\)", repl_md_link, text)

        def repl_book(m, base=base):
            raw = m.group(1).strip()
            norm = os.path.normpath(os.path.join(base, raw))
            if norm not in path2id:
                norm = os.path.normpath(raw)  # 兜底：仓库根相对路径
            fid = path2id.get(norm)
            if not fid:
                return m.group(0)
            title = next(x["title"] for x in files if x["id"] == fid)
            return "[《%s》](#/f/%s)" % (title, fid)

        text = re.sub(r"《([^《》]*?\.md)》", repl_book, text)
        f["md"] = text

    # ---------- 打卡项计数 ----------
    for f in files:
        f["ck"] = len(re.findall(r"^\s*- \[( |x)\]", f["md"], re.M))

    # ---------- 八股闪卡提取 ----------
    cards = []
    card_line = re.compile(r"^\s*- \[( |x)\] \*\*Q：(.+?)\*\*\s*——\s*(.+?)\s*$", re.M)
    ref_re = re.compile(r"｜\s*详见《([^》]+)》\s*$")
    ref_link_re = re.compile(r"｜\s*详见\s*\[《[^》]+》\]\(#/f/(f\d+)\)\s*$")
    head_re = re.compile(r"^###\s+(.+?)\s*$", re.M)
    for f in files:
        if "速查" not in f["title"]:
            continue
        # 用标题位置切分板块
        marks = [(m.start(), re.sub(r"（\d+\s*题）", "", m.group(1)).strip())
                 for m in head_re.finditer(f["md"])]
        for m in card_line.finditer(f["md"]):
            cat = ""
            for pos, name in marks:
                if pos < m.start():
                    cat = name
                else:
                    break
            ans = m.group(3)
            refid, reftitle = "", ""
            rm = ref_link_re.search(ans) or ref_re.search(ans)
            if rm:
                if rm.re is ref_link_re:
                    refid = rm.group(1)
                    reftitle = next(x["title"] for x in files if x["id"] == refid)
                else:
                    raw = rm.group(1).strip()
                    norm = os.path.normpath(os.path.join(os.path.dirname(f["path"]), raw))
                    fid = path2id.get(norm)
                    if fid:
                        refid = fid
                        reftitle = next(x["title"] for x in files if x["id"] == fid)
                ans = (ref_link_re.sub("", ref_re.sub("", ans))).strip()
            cards.append({
                "id": "c%d" % len(cards), "cat": cat, "q": m.group(2).strip(),
                "a": ans.strip(), "ref": refid, "refTitle": reftitle,
            })

    # ---------- 选择/填空题库提取 ----------
    import hashlib
    quiz = []
    quiz_file = next((f for f in files if f["path"].endswith("选择填空题库.md")), None)
    if quiz_file:
        qsec_re = re.compile(r"^##\s+(选择题|填空题)\s*$", re.M)
        marks = [(m.start(), {"选择题": "select", "填空题": "blank"}[m.group(1)])
                 for m in qsec_re.finditer(quiz_file["md"])]
        marks.append((len(quiz_file["md"]), None))
        for (start, kind), (end, _) in zip(marks, marks[1:]):
            body = quiz_file["md"][start:end].split("\n", 1)[1]
            for block in re.split(r"^###\s+", body, flags=re.M)[1:]:
                lines = block.splitlines()
                head = re.match(r"(?:\d+[\.、]\s*)?（([^·（）]+)·([^（）]+)）\s*(.+)$", lines[0].strip())
                rest = "\n".join(lines[1:])
                am = re.search(r"^答案[：:]\s*(.+?)\s*$", rest, re.M)
                em = re.search(r"^解析[：:]\s*(.+?)\s*$", rest, re.M)
                if not (head and am and em):
                    print("warn: 题库小节解析失败:", block[:40].replace("\n", " "))
                    continue
                cat, diff, stem = head.group(1).strip(), head.group(2).strip(), head.group(3).strip()
                exp = em.group(1).strip()
                refid = ""
                rm = re.search(r"\]\(#/f/(f\d+)\)", exp)
                if rm:
                    refid = rm.group(1)
                qid = "q" + hashlib.md5(stem.encode("utf-8")).hexdigest()[:8]
                if kind == "select":
                    opts = re.findall(r"^-\s*(?:\[)?([A-D])(?:\])?[\.、]\s*(.+)$", rest, re.M)
                    letter = am.group(1).strip().upper()[:1]
                    if len(opts) < 2 or letter not in "ABCD"[:len(opts)]:
                        print("warn: 选择题选项/答案异常:", stem[:30])
                        continue
                    quiz.append({"id": qid, "kind": "select", "cat": cat, "diff": diff,
                                 "q": stem, "opts": [o[1].strip() for o in opts],
                                 "a": letter, "exp": exp, "ref": refid})
                else:
                    nblank = len(re.findall(r"＿{2,}", stem))
                    alts = [[x.strip() for x in p.split("／") if x.strip()]
                            for p in re.split(r"[；;]", am.group(1)) if p.strip()]
                    if nblank and len(alts) != nblank:
                        print("warn: 填空空数与答案数不符(%d≠%d): %s" % (nblank, len(alts), stem[:30]))
                    quiz.append({"id": qid, "kind": "blank", "cat": cat, "diff": diff,
                                 "q": stem, "alts": alts, "exp": exp, "ref": refid})

    data = {
        "generated": datetime.date.today().isoformat(),
        "stages": [{"name": n, "icon": i} for n, i, _ in STAGES],
        "files": files,
        "cards": cards,
        "quiz": quiz,
    }
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

    html = TEMPLATE.replace("__DATA__", payload)
    out = ROOT / "index.html"
    out.write_text(html, encoding="utf-8")
    print("生成 %s（%.1f KB，%d 篇文档，%d 张闪卡，%d 道练习题，%d 个打卡项）"
          % (out, out.stat().st_size / 1024, len(files), len(cards), len(quiz),
             sum(f["ck"] for f in files)))

TEMPLATE = r'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Java 入门到面试指南</title>
<style>
:root{
  --bg:#f6f7f9; --card:#ffffff; --text:#1f2328; --muted:#6b7280;
  --accent:#2563eb; --accent-soft:#eff6ff; --good:#16a34a; --warn:#d97706;
  --border:#e5e7eb; --code-bg:#0f172a; --code-fg:#e2e8f0;
  --side-bg:#0f172a; --side-fg:#cbd5e1; --side-active:#38bdf8;
  --mark:#fde68a;
}
[data-theme="dark"]{
  --bg:#0b1220; --card:#111a2c; --text:#e5eaf3; --muted:#94a3b8;
  --accent:#60a5fa; --accent-soft:#16233d; --good:#4ade80;
  --border:#24314d; --mark:#a16207;
}
*{box-sizing:border-box}
html,body{height:100%}
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;background:var(--bg);color:var(--text);display:flex}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}
/* ---------- 侧边栏 ---------- */
#sidebar{width:292px;flex:0 0 292px;background:var(--side-bg);color:var(--side-fg);height:100vh;overflow-y:auto;padding:18px 14px;position:sticky;top:0}
#sidebar h1{font-size:17px;color:#fff;margin:4px 6px 2px}
#sidebar .sub{font-size:11px;color:#64748b;margin:0 6px 14px}
.overall{background:#1e293b;border-radius:10px;padding:10px 12px;margin:0 2px 16px}
.overall .row{display:flex;justify-content:space-between;font-size:12px;color:#94a3b8;margin-bottom:6px}
.bar{height:6px;background:#334155;border-radius:99px;overflow:hidden}
.bar>i{display:block;height:100%;background:linear-gradient(90deg,#38bdf8,#34d399);border-radius:99px;transition:width .3s}
.scard .bar{background:#e5e7eb}
[data-theme="dark"] .scard .bar{background:#24314d}
.stage{margin-bottom:6px}
.stage-h{display:flex;align-items:center;gap:8px;padding:8px 8px;border-radius:8px;cursor:pointer;font-size:13.5px;font-weight:600;color:#e2e8f0;user-select:none}
.stage-h:hover{background:#1e293b}
.stage-h .n{margin-left:auto;font-size:11px;color:#64748b;font-weight:400}
.stage-h .arrow{transition:transform .2s;font-size:10px;color:#64748b}
.stage.open .arrow{transform:rotate(90deg)}
.stage-files{display:none;padding:2px 0 6px}
.stage.open .stage-files{display:block}
.fitem{display:flex;align-items:center;gap:8px;padding:6px 8px 6px 22px;border-radius:7px;font-size:12.5px;color:var(--side-fg);cursor:pointer}
.fitem:hover{background:#1e293b;color:#fff}
.fitem.active{background:#1d4ed84d;color:#fff}
.fitem .dot{width:7px;height:7px;border-radius:99px;background:#475569;flex:0 0 7px}
.fitem.done .dot{background:#34d399}
#sidefoot{margin-top:18px;padding-top:12px;border-top:1px solid #1e293b;display:flex;gap:6px;flex-wrap:wrap}
.sbtn{font-size:11px;background:#1e293b;color:#94a3b8;border:none;border-radius:6px;padding:5px 8px;cursor:pointer}
.sbtn:hover{color:#fff;background:#334155}
/* ---------- 主区 ---------- */
#mainwrap{flex:1;height:100vh;overflow-y:auto;scroll-behavior:smooth}
#topbar{position:sticky;top:0;z-index:30;display:flex;align-items:center;gap:10px;padding:10px 22px;background:color-mix(in srgb,var(--bg) 86%,transparent);backdrop-filter:blur(8px);border-bottom:1px solid var(--border)}
#burger{display:none;background:none;border:1px solid var(--border);border-radius:8px;font-size:15px;padding:4px 9px;cursor:pointer;color:var(--text)}
#search{flex:1;max-width:460px;margin-left:auto;display:flex}
#search input{width:100%;padding:8px 12px;border-radius:9px;border:1px solid var(--border);background:var(--card);color:var(--text);font-size:13px;outline:none}
#search input:focus{border-color:var(--accent)}
#themeBtn{background:var(--card);border:1px solid var(--border);border-radius:9px;padding:7px 10px;cursor:pointer;font-size:13px}
#content{max-width:900px;margin:0 auto;padding:26px 34px 90px}
/* ---------- Markdown ---------- */
.md h1{font-size:26px;margin:.2em 0 .6em;padding-bottom:.35em;border-bottom:2px solid var(--border);letter-spacing:.2px}
.md h2{font-size:20px;margin:1.6em 0 .6em;padding-bottom:.3em;border-bottom:1px solid var(--border)}
.md h3{font-size:16.5px;margin:1.35em 0 .5em;color:var(--text)}
.md h4{font-size:14.5px;margin:1.2em 0 .4em}
.md p{line-height:1.85;margin:.65em 0;font-size:14.5px}
.md li{line-height:1.8;margin:.28em 0;font-size:14.5px}
.md ul,.md ol{padding-left:1.5em;margin:.5em 0}
.md blockquote{margin:1em 0;padding:.7em 1em;border-left:3px solid var(--accent);background:var(--accent-soft);border-radius:0 10px 10px 0;color:var(--muted)}
.md blockquote p{margin:.25em 0}
.md code{background:color-mix(in srgb,var(--accent) 10%,transparent);color:var(--accent);border-radius:5px;padding:2px 6px;font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:.88em}
pre.code{background:var(--code-bg);color:var(--code-fg);border-radius:12px;padding:16px 18px;overflow-x:auto;position:relative;margin:1em 0}
pre.code code{background:none;color:inherit;padding:0;font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:12.8px;line-height:1.7;white-space:pre}
pre.code[data-lang]::before{content:attr(data-lang);position:absolute;top:8px;right:14px;font-size:10.5px;color:#64748b;text-transform:uppercase;letter-spacing:1px}
.mermaidbox{border:1px dashed var(--border);border-radius:12px;padding:10px 14px;margin:1em 0;background:var(--card)}
.mermaidbox-h{font-size:12px;color:var(--muted);margin-bottom:6px}
.twrap{overflow-x:auto;margin:1em 0;border:1px solid var(--border);border-radius:12px}
.md table{border-collapse:collapse;width:100%;font-size:13.5px}
.md th{background:color-mix(in srgb,var(--accent) 8%,var(--card));text-align:left;font-weight:600}
.md th,.md td{padding:9px 13px;border-bottom:1px solid var(--border);line-height:1.65;vertical-align:top}
.md tr:last-child td{border-bottom:none}
.md hr{border:none;border-top:1px solid var(--border);margin:2em 0}
label.ck{display:flex;gap:9px;align-items:flex-start;cursor:pointer;padding:2px 0}
label.ck input{accent-color:var(--good);width:15px;height:15px;margin-top:4px;flex:0 0 15px;cursor:pointer}
label.ck span{flex:1}
mark{background:var(--mark);color:inherit;border-radius:3px;padding:0 2px}
/* ---------- 阅读页头 ---------- */
.doc-head{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:8px}
.crumb{font-size:12.5px;color:var(--muted)}
.crumb b{color:var(--text)}
.spacer{flex:1}
.btn{border:1px solid var(--border);background:var(--card);color:var(--text);border-radius:9px;padding:7px 13px;font-size:12.5px;cursor:pointer}
.btn:hover{border-color:var(--accent);color:var(--accent)}
.btn.primary{background:var(--accent);border-color:var(--accent);color:#fff}
.btn.primary:hover{opacity:.9;color:#fff}
.btn.good{border-color:var(--good);color:var(--good)}
.pager{display:flex;justify-content:space-between;gap:10px;margin-top:34px;padding-top:16px;border-top:1px solid var(--border)}
/* ---------- 首页 ---------- */
.hero{background:linear-gradient(135deg,#1d4ed8,#0ea5e9 55%,#10b981);border-radius:18px;color:#fff;padding:30px 34px;margin-bottom:22px}
.hero h1{margin:0 0 6px;font-size:26px}
.hero p{margin:0 0 16px;opacity:.92;font-size:14px}
.hero .bar{background:#ffffff40;height:8px}
.hero .stat{font-size:12.5px;margin-top:8px;opacity:.95}
.hero .acts{display:flex;gap:10px;margin-top:16px;flex-wrap:wrap}
.hero .acts .btn{background:#ffffff22;border-color:#ffffff55;color:#fff;font-size:13px;padding:9px 16px}
.hero .acts .btn:hover{background:#ffffff35;color:#fff}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:14px}
.scard{background:var(--card);border:1px solid var(--border);border-radius:16px;padding:16px 18px;transition:box-shadow .2s,transform .2s}
.scard:hover{box-shadow:0 8px 24px #0f172a14;transform:translateY(-2px)}
.scard .t{font-weight:700;font-size:15px;display:flex;align-items:center;gap:8px;margin-bottom:4px}
.scard .d{font-size:12px;color:var(--muted);margin-bottom:10px}
.scard .flist{display:flex;flex-direction:column;gap:2px}
.scard .flist a{font-size:12.5px;padding:4px 6px;border-radius:6px;display:flex;gap:7px;align-items:center;color:var(--text)}
.scard .flist a:hover{background:var(--accent-soft);text-decoration:none}
.scard .flist .dot{width:6px;height:6px;border-radius:99px;background:#cbd5e1;flex:0 0 6px}
.scard .flist .dot.on{background:var(--good)}
.note{background:var(--card);border:1px solid var(--border);border-radius:16px;padding:14px 18px;font-size:13px;color:var(--muted);margin-top:18px;line-height:1.8}
/* ---------- 闪卡 ---------- */
.cards-wrap{max-width:760px;margin:0 auto}
.chips{display:flex;gap:8px;flex-wrap:wrap;margin:14px 0 20px}
.chip{border:1px solid var(--border);background:var(--card);border-radius:99px;padding:6px 13px;font-size:12.5px;cursor:pointer;color:var(--text)}
.chip.on{background:var(--accent);border-color:var(--accent);color:#fff}
.fcard{background:var(--card);border:1px solid var(--border);border-radius:20px;padding:34px 38px;min-height:300px;display:flex;flex-direction:column;box-shadow:0 10px 34px #0f172a0d}
.fcard .cat{font-size:12px;color:var(--accent);font-weight:600;margin-bottom:14px}
.fcard .q{font-size:19px;font-weight:700;line-height:1.65}
.fcard .a{margin-top:22px;padding-top:20px;border-top:1px dashed var(--border);font-size:14.5px;line-height:1.9;color:var(--text)}
.fcard .a.hidden .atext{filter:blur(7px);user-select:none;pointer-events:none}
.fcard .hint{font-size:11.5px;color:var(--muted);margin-top:14px}
.fcard .ref{margin-top:14px;font-size:12.5px}
.facts{display:flex;gap:10px;margin-top:20px}
.facts .btn{flex:1;padding:11px}
.cprog{display:flex;justify-content:space-between;font-size:12.5px;color:var(--muted);margin-bottom:10px}
.cstats{display:flex;gap:14px;margin-top:16px;font-size:12.5px;color:var(--muted);flex-wrap:wrap}
.cstats b{color:var(--text)}
/* ---------- 搜索结果 ---------- */
.sres{margin-top:8px}
.sres .grp{background:var(--card);border:1px solid var(--border);border-radius:14px;padding:12px 16px;margin-bottom:12px}
.sres .gt{font-weight:700;font-size:14.5px;cursor:pointer}
.sres .cnt{font-size:11.5px;color:var(--muted);margin-left:8px;font-weight:400}
.sres .ln{font-size:12.8px;color:var(--muted);padding:5px 8px;border-radius:6px;cursor:pointer;line-height:1.7}
.sres .ln:hover{background:var(--accent-soft);color:var(--text)}
.qstats{font-size:12.5px;color:var(--muted)}
.qopt{display:flex;gap:12px;align-items:flex-start;border:1px solid var(--border);border-radius:12px;padding:12px 14px;margin:9px 0;cursor:pointer;font-size:14.5px;line-height:1.75;background:var(--card)}
.qopt:hover{border-color:var(--accent)}
.qopt b{color:var(--accent);flex:0 0 auto;font-size:12.5px;margin-top:2px}
.qopt.right{border-color:var(--good);background:color-mix(in srgb,var(--good) 10%,var(--card))}
.qopt.wrong{border-color:#ef4444;background:color-mix(in srgb,#ef4444 8%,var(--card))}
.qstem{font-size:16.5px;font-weight:600;line-height:2.4;margin-top:8px}
.blankin{border:none;border-bottom:2px solid var(--accent);background:var(--accent-soft);padding:4px 12px;border-radius:8px 8px 0 0;font-size:14.5px;font-weight:600;color:var(--text);outline:none;margin:0 6px;min-width:130px;text-align:center}
.blankin:focus{background:color-mix(in srgb,var(--accent) 16%,var(--card))}
.blankin.ok{border-color:var(--good);background:color-mix(in srgb,var(--good) 10%,var(--card))}
.blankin.bad{border-color:#ef4444;background:color-mix(in srgb,#ef4444 8%,var(--card))}
.qfb{margin-top:18px;font-weight:700;font-size:15px}
.qfb.ok{color:var(--good)}
.qfb.bad{color:#ef4444}
.weakcard{background:color-mix(in srgb,var(--warn) 10%,var(--card));border:1px solid color-mix(in srgb,var(--warn) 45%,var(--border));border-radius:14px;padding:12px 18px;margin-bottom:14px;font-size:13.5px;display:flex;align-items:center;gap:12px;flex-wrap:wrap}
.weakcard b{color:var(--warn)}
.chap-sel{padding:7px 10px;border-radius:9px;border:1px solid var(--border);background:var(--card);color:var(--text);font-size:13px;outline:none}
.chap-sel:focus{border-color:var(--accent)}
.exbar{display:flex;align-items:center;gap:12px;margin-bottom:14px;flex-wrap:wrap}
.extimer{font-variant-numeric:tabular-nums;background:var(--accent);color:#fff;border-radius:99px;padding:6px 16px;font-weight:700;font-size:14.5px}
.extimer.low{background:#ef4444;animation:pulse 1s infinite}
@keyframes pulse{50%{opacity:.65}}
.exgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(38px,1fr));gap:6px;margin:0 0 14px}
.exdot{border:1px solid var(--border);border-radius:8px;text-align:center;padding:6px 0;font-size:12px;cursor:pointer;background:var(--card);color:var(--muted)}
.exdot.answered{background:var(--accent-soft);border-color:var(--accent);color:var(--accent);font-weight:700}
.exdot.cur{outline:2px solid var(--accent);outline-offset:1px}
.exscore{font-size:38px;font-weight:800;color:var(--accent)}
.exres-item{border:1px solid var(--border);border-radius:12px;padding:12px 16px;margin:8px 0;font-size:13.5px;line-height:1.85;background:var(--card)}
.exres-item.bad{border-color:color-mix(in srgb,#ef4444 45%,var(--border))}
/* ---------- 遮罩 ---------- */
#overlay{position:fixed;inset:0;background:#0f172a99;display:none;align-items:center;justify-content:center;z-index:99}
#overlay .box{background:var(--card);border-radius:16px;padding:22px;width:min(560px,92vw)}
#overlay textarea{width:100%;height:180px;border:1px solid var(--border);border-radius:10px;padding:10px;font-size:12px;background:var(--bg);color:var(--text)}
#overlay .row{display:flex;gap:10px;justify-content:flex-end;margin-top:12px}
@media (max-width:920px){
  #sidebar{position:fixed;z-index:50;left:0;top:0;transform:translateX(-100%);transition:transform .25s}
  #sidebar.open{transform:none;box-shadow:0 0 40px #0008}
  #burger{display:block}
  #content{padding:20px 18px 80px}
}
</style>
</head>
<body>
<nav id="sidebar">
  <h1>☕ Java 学习指南</h1>
  <p class="sub">入门 → 中间件 → 面试 · 本地离线版</p>
  <div class="overall">
    <div class="row"><span>总进度</span><span id="ovNum">0%</span></div>
    <div class="bar"><i id="ovBar" style="width:0%"></i></div>
  </div>
  <div id="stages"></div>
  <div id="sidefoot">
    <button class="sbtn" id="expBtn">导出进度</button>
    <button class="sbtn" id="impBtn">导入进度</button>
    <button class="sbtn" id="resetBtn">重置</button>
  </div>
</nav>
<div id="mainwrap">
  <div id="topbar">
    <button id="burger">☰</button>
    <div id="search"><input id="searchInput" placeholder="搜索知识点 / 面试题…（按 / 聚焦）"></div>
    <button id="themeBtn" title="切换主题">🌙</button>
  </div>
  <div id="content"></div>
</div>
<div id="overlay"><div class="box">
  <h3 id="ovTitle" style="margin:0 0 10px;font-size:15px">导入进度</h3>
  <textarea id="ovText" placeholder="粘贴之前导出的 JSON…"></textarea>
  <div class="row">
    <button class="btn" id="ovCancel">取消</button>
    <button class="btn primary" id="ovOk">确定</button>
  </div>
</div></div>
<noscript>需要启用 JavaScript。</noscript>
<script id="app-data" type="application/json">__DATA__</script>
<script>
window.addEventListener('error', function (e) {
  var el = document.getElementById('boot-err');
  if (!el) {
    el = document.createElement('div'); el.id = 'boot-err';
    el.style.cssText = 'position:fixed;top:0;left:0;right:0;z-index:9999;background:#dc2626;color:#fff;padding:10px 16px;font:13px/1.6 -apple-system,sans-serif';
    (document.body || document.documentElement).appendChild(el);
  }
  el.textContent = '⚠ 应用脚本出错：' + (e.message || '未知错误') + '（请把这段文字发给助手定位问题）';
});
const DATA = JSON.parse(document.getElementById('app-data').textContent);
const $ = s => document.querySelector(s);
const byId = Object.fromEntries(DATA.files.map(f => [f.id, f]));
const stageFiles = DATA.files.reduce((m, f) => { (m[f.stage] = m[f.stage] || []).push(f); return m; }, []);
const TOTAL_CK = DATA.files.reduce((s, f) => s + f.ck, 0);

/* ---------- 存储 ---------- */
let store;
try { store = JSON.parse(localStorage.getItem('jvg1') || '{}'); } catch (e) { store = {}; }
store.ck = store.ck || {}; store.done = store.done || {}; store.cards = store.cards || {}; store.quiz = store.quiz || {};
store.theme = store.theme || 'light'; store.last = store.last || null;
const save = () => { try { localStorage.setItem('jvg1', JSON.stringify(store)); } catch (e) { /* 浏览器禁用存储时静默降级，功能不受影响 */ } };

/* ---------- Markdown 渲染 ---------- */
function esc(s) { return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }
function inline(s) {
  const codes = [];
  s = s.replace(/`([^`]+)`/g, (m, c) => { codes.push(c); return '\u0000' + (codes.length - 1) + '\u0000'; });
  const links = [];
  s = s.replace(/\[([^\]]+)\]\(([^)\s]+)\)/g, (m, t, u) => { links.push([t, u]); return '\u0001' + (links.length - 1) + '\u0001'; });
  // 裸 URL 自动转为可点击链接（资料表里的纯文本网址）
  s = s.replace(/https?:\/\/[A-Za-z0-9._~:/?#[\]@!$&'()*+,;=%-]+/g,
    m => '<a href="' + m + '" target="_blank" rel="noopener">' + m + '</a>');
  s = s.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  s = s.replace(/(^|[^*])\*([^*\s][^*]*?)\*/g, '$1<em>$2</em>');
  s = s.replace(/~~([^~]+)~~/g, '<del>$1</del>');
  s = s.replace(/\u0001(\d+)\u0001/g, (m, i) => {
    const t = links[i][0], u = links[i][1];
    return u.startsWith('#')
      ? '<a class="ilink" href="' + u + '">' + t + '</a>'
      : '<a href="' + u + '" target="_blank" rel="noopener">' + t + '</a>';
  });
  s = s.replace(/\u0000(\d+)\u0000/g, (m, i) => '<code>' + codes[i] + '</code>');
  return s;
}
function itemHtml(txt, f) {
  const tm = txt.match(/^\[( |x)\]\s*([\s\S]*)$/);
  if (tm) {
    const key = f.id + ':' + (f._ck++);
    const on = tm[1] === 'x' || !!store.ck[key];
    return '<label class="ck"><input type="checkbox" data-ck="' + key + '"' + (on ? ' checked' : '') + '><span>' + inline(esc(tm[2])) + '</span></label>';
  }
  return inline(esc(txt));
}
function listHtml(items, f) {
  const root = { kids: [] }; const st = [{ ind: -1, node: root }];
  for (const it of items) {
    const n = { it, kids: [] };
    while (st[st.length - 1].ind >= it.ind) st.pop();
    st[st.length - 1].node.kids.push(n); st.push({ ind: it.ind, node: n });
  }
  function rec(n) {
    if (!n.kids.length) return '';
    const ord = n.kids[0].it.ord;
    let s = ord ? '<ol>' : '<ul>';
    for (const k of n.kids) s += '<li>' + itemHtml(k.it.txt, f) + rec(k) + '</li>';
    return s + (ord ? '</ol>' : '</ul>');
  }
  return rec(root);
}
function mdToHtml(md, f) {
  f._ck = 0;
  const lines = md.replace(/\r\n?/g, '\n').split('\n');
  const out = []; let i = 0;
  const blank = s => /^\s*$/.test(s);
  const blockStart = /^\s*(#{1,4}\s|```|>|\||\s*[-*]\s|\s*\d+\.\s)/;
  while (i < lines.length) {
    const ln = lines[i];
    if (/^\s*```/.test(ln)) {
      const lang = (ln.match(/^\s*```(\S*)/) || [])[1] || '';
      i++; const buf = [];
      while (i < lines.length && !/^\s*```/.test(lines[i])) { buf.push(lines[i]); i++; }
      i++;
      if (lang === 'mermaid') {
        out.push('<div class="mermaidbox"><div class="mermaidbox-h">📈 流程图（mermaid 源码，粘贴到 GitHub / typora 可直接渲染）</div><pre class="code"><code>' + esc(buf.join('\n')) + '</code></pre></div>');
      } else {
        out.push('<pre class="code"' + (lang ? ' data-lang="' + esc(lang) + '"' : '') + '><code>' + esc(buf.join('\n')) + '</code></pre>');
      }
      continue;
    }
    const hm = ln.match(/^(#{1,4})\s+(.*)$/);
    if (hm) { out.push('<h' + hm[1].length + '>' + inline(esc(hm[2])) + '</h' + hm[1].length + '>'); i++; continue; }
    if (/^\s*(---+|\*\*\*+)\s*$/.test(ln)) { out.push('<hr>'); i++; continue; }
    if (ln.includes('|') && i + 1 < lines.length && lines[i + 1].includes('-') && /^\s*\|?[\s:|-]+$/.test(lines[i + 1])) {
      const row = r => r.replace(/^\s*\|/, '').replace(/\|\s*$/, '').split('|').map(c => c.trim());
      const head = row(ln); i += 2; const rows = [];
      while (i < lines.length && lines[i].includes('|') && !blank(lines[i])) { rows.push(row(lines[i])); i++; }
      out.push('<div class="twrap"><table><thead><tr>' + head.map(c => '<th>' + inline(esc(c)) + '</th>').join('') + '</tr></thead><tbody>'
        + rows.map(r => '<tr>' + r.map(c => '<td>' + inline(esc(c)) + '</td>').join('') + '</tr>').join('') + '</tbody></table></div>');
      continue;
    }
    if (/^\s*>/.test(ln)) {
      const buf = [];
      while (i < lines.length && /^\s*>/.test(lines[i])) { buf.push(lines[i].replace(/^\s*>\s?/, '')); i++; }
      out.push('<blockquote>' + buf.map(s => blank(s) ? '' : '<p>' + inline(esc(s)) + '</p>').join('') + '</blockquote>');
      continue;
    }
    const lm = ln.match(/^(\s*)([-*]|\d+\.)\s+(.*)$/);
    if (lm) {
      const items = [{ ind: lm[1].length, ord: /\d/.test(lm[2]), txt: lm[3] }];
      i++;
      while (i < lines.length) {
        const m2 = lines[i].match(/^(\s*)([-*]|\d+\.)\s+(.*)$/);
        if (m2) { items.push({ ind: m2[1].length, ord: /\d/.test(m2[2]), txt: m2[3] }); i++; }
        else if (!blank(lines[i]) && /^\s{2,}\S/.test(lines[i]) && !blockStart.test(lines[i])) { items[items.length - 1].txt += '<br>' + lines[i].trim(); i++; }
        else if (blank(lines[i]) && i + 1 < lines.length && /^(\s*)([-*]|\d+\.)\s+/.test(lines[i + 1])) { i++; }
        else break;
      }
      out.push(listHtml(items, f));
      continue;
    }
    if (blank(ln)) { i++; continue; }
    const buf = [];
    while (i < lines.length && !blank(lines[i]) && !blockStart.test(lines[i])) { buf.push(lines[i].trim()); i++; }
    out.push('<p>' + buf.map(s => inline(esc(s))).join('<br>') + '</p>');
  }
  return out.join('\n');
}

/* ---------- 进度 ---------- */
function statsOf(files) {
  let total = 0, done = 0, doneFiles = 0;
  files.forEach(f => {
    if (f.ck > 0) {
      total += f.ck;
      for (let k = 0; k < f.ck; k++) if (store.ck[f.id + ':' + k]) done++;
    } else { total += 1; if (store.done[f.id]) done++; }
    if (store.done[f.id]) doneFiles++;
  });
  return { total, done, doneFiles, n: files.length };
}
function stageStats(si) { return statsOf(stageFiles[si] || []); }
function overall() { return statsOf(DATA.files); }
function updateBars() {
  const o = overall();
  const pct = o.total ? Math.round(o.done / o.total * 100) : 0;
  $('#ovBar').style.width = pct + '%'; $('#ovNum').textContent = pct + '%（' + o.done + '/' + o.total + '）';
  document.querySelectorAll('[data-stageprog]').forEach(el => {
    const s = stageStats(+el.dataset.stageprog);
    el.style.width = (s.total ? Math.round(s.done / s.total * 100) : 0) + '%';
  });
  document.querySelectorAll('[data-fdot]').forEach(el => el.classList.toggle('on', !!store.done[el.dataset.fdot]));
  document.querySelectorAll('.fitem').forEach(el => el.classList.toggle('done', !!store.done[el.dataset.id]));
}

/* ---------- 侧边栏 ---------- */
function buildSidebar() {
  let h = '';
  DATA.stages.forEach((st, si) => {
    const s = stageStats(si);
    h += '<div class="stage" data-stage="' + si + '"><div class="stage-h" onclick="toggleStage(this)">'
      + '<span class="arrow">▶</span><span>' + st.icon + ' ' + st.name + '</span><span class="n">' + s.doneFiles + '/' + s.n + '</span></div><div class="stage-files">';
    (stageFiles[si] || []).forEach(f => {
      h += '<div class="fitem" data-id="' + f.id + '" onclick="goto(\'' + f.id + '\')"><span class="dot" data-fdot="' + f.id + '"></span>' + esc(f.title.replace(/^\d+-/, '')) + '</div>';
    });
    h += '</div></div>';
  });
  $('#stages').innerHTML = h;
}
function toggleStage(el) { el.parentElement.classList.toggle('open'); }
function goto(id) { location.hash = '#/f/' + id; if (innerWidth <= 920) $('#sidebar').classList.remove('open'); }

/* ---------- 视图 ---------- */
let pendingHighlight = null;
function route() {
  const h = decodeURIComponent(location.hash || '#/home');
  let m;
  if (m = h.match(/^#\/f\/(.+)$/)) return renderFile(m[1]);
  if (h.startsWith('#/cards')) return renderCards();
  if (h.startsWith('#/quiz')) return renderQuiz();
  if (h.startsWith('#/exam')) return renderExam();
  if (h.startsWith('#/search/')) return renderSearch(h.slice(9));
  renderHome();
}
function crumbHtml(f) {
  return '<span class="crumb">' + esc(DATA.stages[f.stage].name) + ' <b>' + esc(f.title) + '</b></span>';
}
function renderFile(id) {
  const f = byId[id]; if (!f) return renderHome();
  store.last = id; save();
  const idx = DATA.files.indexOf(f);
  const prev = DATA.files[idx - 1], next = DATA.files[idx + 1];
  const html = mdToHtml(f.md, f);
  $('#content').innerHTML =
    '<div class="doc-head">' + crumbHtml(f) + '<span class="spacer"></span>'
    + '<button class="btn ' + (store.done[id] ? 'good' : '') + '" id="doneBtn">' + (store.done[id] ? '✅ 已学完' : '标记已学完') + '</button>'
    + '<button class="btn" onclick="scrollTo(0,0)">回顶部</button></div>'
    + '<div class="md">' + html + '</div>'
    + '<div class="pager">' + (prev ? '<button class="btn" onclick="goto(\'' + prev.id + '\')">← ' + esc(prev.title) + '</button>' : '<span></span>')
    + (next ? '<button class="btn" onclick="goto(\'' + next.id + '\')">' + esc(next.title) + ' →</button>' : '<span></span>') + '</div>';
  $('#doneBtn').onclick = () => { store.done[id] ? delete store.done[id] : store.done[id] = 1; save(); renderFile(id); updateBars(); };
  markActive(id);
  if (pendingHighlight) { highlightAll($('#content'), pendingHighlight); pendingHighlight = null; }
  $('#mainwrap').scrollTo(0, 0);
}
function markActive(id) {
  document.querySelectorAll('.fitem').forEach(el => el.classList.toggle('active', el.dataset.id === id));
  const cur = document.querySelector('.fitem.active');
  if (cur) { const st = cur.closest('.stage'); if (st) st.classList.add('open'); }
}
function renderHome() {
  const o = overall(); const pct = o.total ? Math.round(o.done / o.total * 100) : 0;
  const desc = ["定位与使用方法", "从零到能写程序", "并发 / JVM / 网络", "SQL 与调优", "用法与使用场景 ⭐", "Spring 全家桶", "架构与系统设计", "八股 / 算法 / 简历"];
  let cards = '';
  DATA.stages.forEach((st, si) => {
    const s = stageStats(si);
    cards += '<div class="scard"><div class="t">' + st.icon + ' ' + esc(st.name) + '</div><div class="d">' + esc(desc[si] || '') + ' · 进度 ' + s.done + '/' + s.total + ' · 已学完 ' + s.doneFiles + '/' + s.n + '</div>'
      + '<div class="bar" style="margin-bottom:10px"><i data-stageprog="' + si + '" style="width:0%"></i></div><div class="flist">'
      + (stageFiles[si] || []).map(f => '<a href="#/f/' + f.id + '"><span class="dot' + (store.done[f.id] ? ' on' : '') + '" data-fdot="' + f.id + '"></span>' + esc(f.title.replace(/^\d+-/, '')) + '</a>').join('')
      + '</div></div>';
  });
  const lastF = store.last && byId[store.last] ? store.last : null;
  const firstUndone = (DATA.files.find(f => f.stage > 0 && !store.done[f.id]) || DATA.files[1]).id;
  const known = Object.values(store.cards).filter(v => v === 'known').length;
  const catStats = {};
  (DATA.quiz || []).forEach(q => {
    const st = store.quiz[q.id]; if (!st) return;
    const c = catStats[q.cat] || (catStats[q.cat] = { r: 0, w: 0 });
    c.r += st.r || 0; c.w += st.w || 0;
  });
  const weak = Object.entries(catStats).filter(([, v]) => v.r + v.w >= 3)
    .sort((a, b) => (a[1].r / (a[1].r + a[1].w)) - (b[1].r / (b[1].r + b[1].w)))[0];
  let weakHtml = '';
  if (weak) {
    const v = weak[1], pct = Math.round(v.r / (v.r + v.w) * 100);
    weakHtml = '<div class="weakcard"><span>🎯 薄弱环节：<b>' + esc(weak[0]) + '</b>　练习正确率 ' + pct + '%（答对 ' + v.r + ' / 答错 ' + v.w + '）</span><span class="spacer"></span>'
      + '<button class="btn" onclick="goWeakCat(' + JSON.stringify(weak[0]).replace(/"/g, '&quot;') + ')">去针对性练习 →</button></div>';
  }
  $('#content').innerHTML =
    '<div class="hero"><h1>☕ Java 入门到面试指南</h1>'
    + '<p>基于廖雪峰教程 · 慕课网 · JavaGuide · pdai.tech · matools 五大站点整合 · 共 ' + DATA.files.length + ' 篇 / ' + DATA.cards.length + ' 张闪卡 / ' + (DATA.quiz || []).length + ' 道练习题</p>'
    + '<div class="bar"><i id="ovBar" style="width:' + pct + '%"></i></div>'
    + '<div class="stat">总进度 ' + pct + '%（' + o.done + ' / ' + o.total + '，含打卡与已学完）· 已学完 ' + Object.keys(store.done).length + ' 篇 · 闪卡已掌握 ' + known + ' 张</div>'
    + '<div class="acts">'
    + '<button class="btn primary" onclick="goto(\'' + (lastF || firstUndone) + '\')">' + (lastF ? '📖 继续学习：' + esc(byId[lastF].title) : '🚀 开始学习') + '</button>'
    + '<button class="btn" onclick="location.hash=\'#/cards\'">🃏 八股闪卡自测</button>'
    + '<button class="btn" onclick="location.hash=\'#/quiz\'">📝 选择填空练习</button>'
    + '<button class="btn" onclick="location.hash=\'#/exam\'">🏁 综合大考</button></div></div>'
    + weakHtml
    + '<div class="grid">' + cards + '</div>'
    + '<div class="note">💡 这是单文件离线应用：所有打卡进度存在浏览器本地（localStorage）。更换浏览器或电脑时，用左下角「导出进度 / 导入进度」迁移。源 Markdown 在仓库目录中，修改后运行 <code>python3 app/build.py</code> 重新生成本页。生成日期：' + DATA.generated + '。</div>';
  markActive(null); updateBars();
}

/* ---------- 搜索 ---------- */
let searchIndex = null;
function buildSearchIndex() {
  searchIndex = DATA.files.map(f => ({
    id: f.id, title: f.title, stage: f.stage,
    lines: f.md.split('\n')
      .map(l => l
        .replace(/\[([^\]]*)\]\([^)]*\)/g, '$1')
        .replace(/\*\*|~~|`/g, '')
        .replace(/^[#>\s\-*| ]+/, '')
        .replace(/^\[[ x]\]\s*/, '')
        .trim())
      .filter(l => l.length > 4)
  }));
}
function renderSearch(q) {
  if (!searchIndex) buildSearchIndex();
  q = q.trim();
  if (!q) return renderHome();
  const ql = q.toLowerCase(); const res = [];
  for (const f of searchIndex) {
    const hits = f.lines.filter(l => l.toLowerCase().includes(ql));
    if (hits.length) res.push({ f, hits: hits.slice(0, 4), total: hits.length });
  }
  res.sort((a, b) => b.total - a.total);
  $('#content').innerHTML = '<div class="md"><h1>🔍 搜索：' + esc(q) + '</h1></div>'
    + (res.length ? '<div class="sres">' + res.slice(0, 40).map(r =>
      '<div class="grp"><div class="gt" onclick="pendingHighlight=' + JSON.stringify(JSON.stringify(q)) + ';goto(\'' + r.f.id + '\')">' + esc(r.f.title) + '<span class="cnt">' + r.total + ' 处匹配</span></div>'
      + r.hits.map(hl => '<div class="ln" onclick="pendingHighlight=' + JSON.stringify(JSON.stringify(q)) + ';goto(\'' + r.f.id + '\')">' + esc(hl.slice(0, 160)) + '</div>').join('')
      + '</div>').join('') + '</div>'
      : '<div class="note">没有找到「' + esc(q) + '」。试试更短的关键词，如：HashMap、线程池、缓存穿透、秒杀。</div>');
  markActive(null);
  $('#mainwrap').scrollTo(0, 0);
}
function highlightAll(root, q) {
  if (!q) return;
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT); const nodes = [];
  while (walker.nextNode()) nodes.push(walker.currentNode);
  const escRe = q.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const re = new RegExp(escRe, 'gi');
  let first = null;
  for (const n of nodes) {
    if (n.parentElement.closest('pre, code, script, mark, input')) continue;
    if (!re.test(n.nodeValue)) continue;
    re.lastIndex = 0;
    const frag = document.createDocumentFragment(); let last = 0, m;
    const text = n.nodeValue;
    while ((m = re.exec(text))) {
      frag.appendChild(document.createTextNode(text.slice(last, m.index)));
      const mk = document.createElement('mark'); mk.textContent = m[0]; frag.appendChild(mk);
      if (!first) first = mk;
      last = m.index + m[0].length;
      if (m[0].length === 0) re.lastIndex++;
    }
    frag.appendChild(document.createTextNode(text.slice(last)));
    n.parentNode.replaceChild(frag, n);
  }
  if (first) setTimeout(() => first.scrollIntoView({ block: 'center', behavior: 'smooth' }), 60);
}

/* ---------- 闪卡 ---------- */
let cardSession = null;
function renderCards() {
  const cats = [...new Set(DATA.cards.map(c => c.cat))];
  if (!cardSession) cardSession = { cat: 'all', onlyReview: false, shuffled: false, i: 0, revealed: false, order: [], sig: null };
  const s = cardSession;
  const pool = DATA.cards.filter(c => (s.cat === 'all' || c.cat === s.cat) && (!s.onlyReview || store.cards[c.id] !== 'known'));
  const sig = [s.cat, s.onlyReview, s.shuffled].join('|');
  if (s.sig !== sig) { s.sig = sig; s.order = s.shuffled ? shuffledArr(pool) : pool; s.i = Math.min(s.i, Math.max(0, s.order.length - 1)); }
  const card = s.order[s.i];
  const known = Object.values(store.cards).filter(v => v === 'known').length;
  let chips = '<div class="chips"><span class="chip ' + (s.cat === 'all' ? 'on' : '') + '" onclick="cardSession.cat=\'all\';cardSession.i=0;cardSession.revealed=false;renderCards()">全部</span>'
    + cats.map(c => '<span class="chip ' + (s.cat === c ? 'on' : '') + '" onclick="cardSession.cat=' + JSON.stringify(c).replace(/"/g, '&quot;') + ';cardSession.i=0;cardSession.revealed=false;renderCards()">' + esc(c) + '</span>').join('')
    + '<span class="chip ' + (s.shuffled ? 'on' : '') + '" onclick="cardSession.shuffled=!cardSession.shuffled;cardSession.i=0;cardSession.revealed=false;cardSession.sig=null;renderCards()">🎲 乱序</span>'
    + '<span class="chip ' + (s.onlyReview ? 'on' : '') + '" style="margin-left:auto" onclick="cardSession.onlyReview=!cardSession.onlyReview;cardSession.i=0;cardSession.revealed=false;cardSession.sig=null;renderCards()">🔁 只看未掌握</span></div>';
  let body;
  if (!card) {
    body = '<div class="fcard" style="align-items:center;justify-content:center"><div style="font-size:40px">🎉</div><div class="q" style="margin-top:10px">这个筛选下没有卡片了</div><div class="hint">切换板块或关闭「只看未掌握」</div></div>';
  } else {
    body = '<div class="fcard" onclick="cardSession.revealed=!cardSession.revealed;renderCards()">'
      + '<div class="cat">' + esc(card.cat) + ' · 第 ' + (s.i + 1) + ' / ' + s.order.length + ' 题</div>'
      + '<div class="q">Q：' + esc(card.q) + '</div>'
      + '<div class="a ' + (s.revealed ? '' : 'hidden') + '"><div class="atext">' + inline(esc(card.a)) + '</div>'
      + (s.revealed ? (card.ref ? '<div class="ref">📖 详见 <a href="#/f/' + card.ref + '">' + esc(card.refTitle) + '</a></div>' : '') : '')
      + '</div>'
      + '<div class="hint">' + (s.revealed ? '👇 自评：真的掌握了再点「会了」' : '点击卡片显示答案') + '</div></div>'
      + '<div class="facts">'
      + '<button class="btn good" onclick="grade(\'known\')">✅ 会了</button>'
      + '<button class="btn" onclick="grade(\'review\')">🔁 再看看</button>'
      + '<button class="btn" onclick="cardSession.i=Math.min(cardSession.i+1,cardSession.order.length-1);cardSession.revealed=false;renderCards()">跳过 →</button></div>';
  }
  $('#content').innerHTML = '<div class="cards-wrap"><div class="md"><h1>🃏 八股闪卡自测</h1>'
    + '<p style="color:var(--muted);font-size:13.5px">来自两份八股速查清单，共 ' + DATA.cards.length + ' 题。先自己说答案，再翻卡对照；答不上就点「再看看」，冲刺期只刷未掌握的。</p></div>'
    + chips + body
    + '<div class="cstats">已掌握 <b>' + known + '</b> / ' + DATA.cards.length + ' · 未掌握 <b>' + (DATA.cards.length - known) + '</b></div></div>';
  markActive(null);
  $('#mainwrap').scrollTo(0, 0);
}
function grade(v) {
  const card = cardSession.order[cardSession.i];
  if (card) { store.cards[card.id] = v; save(); }
  cardSession.i = Math.min(cardSession.i + 1, cardSession.order.length - 1);
  cardSession.revealed = false;
  renderCards();
}

/* ---------- 选择/填空练习 ---------- */
let quizSession = null;
const QNORM = s => String(s).trim().toLowerCase().replace(/\s+/g, '');
function shuffledArr(arr) {
  const a = arr.slice();
  for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; }
  return a;
}
function renderQuiz() {
  const qs = DATA.quiz || [];
  if (!quizSession) quizSession = { cat: 'all', kind: 'all', file: 'all', onlyWrong: false, shuffled: false, i: 0, pool: [], revealed: false, sel: -1, vals: [], round: { done: 0, right: 0 } };
  const s = quizSession;
  if (window.__pendingCat) { s.cat = window.__pendingCat; window.__pendingCat = null; s.sig = null; }
  const pool = qs.filter(q => (s.cat === 'all' || q.cat === s.cat)
    && (s.kind === 'all' || q.kind === s.kind)
    && (s.file === 'all' || q.ref === s.file)
    && (!s.onlyWrong || (store.quiz[q.id] || {}).last === 'wrong'));
  const sig = [s.cat, s.kind, s.file, s.onlyWrong, s.shuffled].join('|');
  if (s.sig !== sig || !s.pool) {
    s.sig = sig; s.pool = s.shuffled ? shuffledArr(pool) : pool;
    s.i = 0; s.revealed = false; s.sel = -1; s.vals = []; s.round = { done: 0, right: 0 };
  }
  const cats = [...new Set(qs.map(q => q.cat))];
  const totalRight = qs.reduce((n, q) => n + ((store.quiz[q.id] || {}).r || 0), 0);
  const totalWrong = qs.reduce((n, q) => n + ((store.quiz[q.id] || {}).w || 0), 0);
  const chapMap = {};
  qs.forEach(q => { if (q.ref && byId[q.ref]) chapMap[q.ref] = (chapMap[q.ref] || 0) + 1; });
  const chapSel = '<div class="chips"><span style="font-size:12.5px;color:var(--muted);align-self:center;padding-left:4px">📖 章节小考：</span>'
    + '<select class="chap-sel" onchange="quizFilter({file:this.value})">'
    + '<option value="all"' + (s.file === 'all' ? ' selected' : '') + '>全部章节（' + qs.length + ' 题）</option>'
    + Object.keys(chapMap).map(id => '<option value="' + id + '"' + (s.file === id ? ' selected' : '') + '>' + esc(byId[id].title) + '（' + chapMap[id] + ' 题）</option>').join('')
    + '</select><span style="font-size:12px;color:var(--muted);align-self:center">选一章 = 本章小考，建议配 🎲 乱序</span></div>';
  let chips = '<div class="chips"><span class="chip ' + (s.kind === 'all' ? 'on' : '') + '" onclick="quizFilter({kind:\'all\'})">全部题型</span>'
    + '<span class="chip ' + (s.kind === 'select' ? 'on' : '') + '" onclick="quizFilter({kind:\'select\'})">仅选择题</span>'
    + '<span class="chip ' + (s.kind === 'blank' ? 'on' : '') + '" onclick="quizFilter({kind:\'blank\'})">仅填空题</span>'
    + '<span class="chip ' + (s.shuffled ? 'on' : '') + '" onclick="quizFilter({shuffled:!quizSession.shuffled})">🎲 乱序</span>'
    + '<span class="chip ' + (s.onlyWrong ? 'on' : '') + '" style="margin-left:auto" onclick="quizFilter({onlyWrong:!quizSession.onlyWrong})">🔁 只做错题</span></div>'
    + '<div class="chips"><span class="chip ' + (s.cat === 'all' ? 'on' : '') + '" onclick="quizFilter({cat:\'all\'})">全部板块</span>'
    + cats.map(c => '<span class="chip ' + (s.cat === c ? 'on' : '') + '" onclick="quizFilter({cat:' + JSON.stringify(c).replace(/"/g, '&quot;') + '})">' + esc(c) + '</span>').join('') + '</div>';

  let body;
  if (!qs.length) {
    body = '<div class="fcard" style="align-items:center"><div class="q">题库为空</div></div>';
  } else if (s.i >= s.pool.length) {
    body = '<div class="fcard" style="align-items:center;justify-content:center"><div style="font-size:40px">🎉</div>'
      + '<div class="q" style="margin-top:10px">本轮完成！' + s.round.done + ' 题答对 ' + s.round.right + ' 题</div>'
      + '<div class="hint">错题已记录，可用「🔁 只做错题」针对性重练</div></div>'
      + '<div class="facts"><button class="btn primary" onclick="quizRestart()">再来一轮</button></div>';
  } else {
    const q = s.pool[s.i];
    const head = '<div class="cat">' + esc(q.cat) + ' · ' + esc(q.diff) + ' · 第 ' + (s.i + 1) + ' / ' + s.pool.length + ' 题（本轮答对 ' + s.round.right + '/' + s.round.done + '）</div>';
    if (q.kind === 'select') {
      const aIdx = 'ABCD'.indexOf(q.a);
      const opts = q.opts.map((o, k) => {
        let cls = 'qopt';
        if (s.revealed) { if (k === aIdx) cls += ' right'; else if (k === s.sel) cls += ' wrong'; }
        return '<div class="' + cls + '" onclick="pickOpt(' + k + ')"><b>' + 'ABCD'[k] + '</b><span>' + inline(esc(o)) + '</span></div>';
      }).join('');
      body = '<div class="fcard" onclick="event.stopPropagation()">' + head
        + '<div class="q">' + inline(esc(q.q)) + '</div><div style="margin-top:16px">' + opts + '</div>'
        + (s.revealed ? quizFeedback(q, s.sel === aIdx, '正确答案：' + q.a) : '<div class="hint">点击选项作答，答完立即判分</div>') + '</div>';
    } else {
      const segs = q.q.split(/＿{2,}/);
      const stem = segs.map((seg, k) => inline(esc(seg))
        + (k < segs.length - 1 ? '<input class="blankin' + (s.revealed ? (s.blankOk[k] ? ' ok' : ' bad') : '') + '" data-k="' + k + '" value="' + esc(s.vals[k] || '') + '"' + (s.revealed ? ' disabled' : '') + ' placeholder="填空' + (k + 1) + '">' : '')).join('');
      const ansTxt = '正确答案：' + q.alts.map(a => a.join('／')).join('；');
      body = '<div class="fcard" onclick="event.stopPropagation()">' + head
        + '<div class="qstem">' + stem + '</div>'
        + (s.revealed ? quizFeedback(q, s.blankOk.every(Boolean), ansTxt)
          : '<div class="facts" style="margin-top:18px"><button class="btn primary" onclick="submitBlanks()">提交答案</button></div><div class="hint">回车键也可提交</div>') + '</div>';
    }
  }
  $('#content').innerHTML = '<div class="cards-wrap"><div class="md"><h1>📝 选择填空练习</h1>'
    + '<p style="color:var(--muted);font-size:13.5px">共 ' + qs.length + ' 题（选择题 ' + qs.filter(q => q.kind === 'select').length + ' / 填空题 ' + qs.filter(q => q.kind === 'blank').length + '）· 累计答对 <b>' + totalRight + '</b> 次 · 答错 <b>' + totalWrong + '</b> 次　<button class="btn" style="font-size:12px;padding:3px 10px;vertical-align:middle" onclick="exportWrong()">📤 导出错题</button>　<a href="#/exam" style="font-size:12.5px">🏁 去综合大考 →</a></p></div>'
    + chapSel + chips + body + '</div>';
  markActive(null);
  $('#mainwrap').scrollTo(0, 0);
  if (!s.revealed && s.pool[s.i] && s.pool[s.i].kind === 'blank') {
    const inp = document.querySelector('.blankin');
    if (inp) inp.focus();
  }
}
function quizFeedback(q, ok, ansTxt) {
  let h = '<div class="qfb ' + (ok ? 'ok' : 'bad') + '">' + (ok ? '✅ 回答正确' : '❌ 回答错误　' + esc(ansTxt)) + '</div>'
    + '<blockquote><p>' + inline(esc(q.exp)) + '</p></blockquote>';
  if (q.ref) h += '<div class="ref" style="margin:-6px 0 14px;font-size:12.5px">📖 详见 <a href="#/f/' + q.ref + '">' + esc(byId[q.ref] ? byId[q.ref].title : '') + '</a></div>';
  h += '<div class="facts"><button class="btn primary" onclick="quizNext()">' + (quizSession.i + 1 >= quizSession.pool.length ? '查看本轮成绩 →' : '下一题 →') + '</button></div>';
  return h;
}
function goWeakCat(c) { window.__pendingCat = c; location.hash = '#/quiz'; }
function quizFilter(patch) {
  Object.assign(quizSession, patch, { i: 0, revealed: false, sel: -1, vals: [], round: { done: 0, right: 0 } });
  renderQuiz();
}
function quizRestart() { Object.assign(quizSession, { i: 0, revealed: false, sel: -1, vals: [], round: { done: 0, right: 0 } }); renderQuiz(); }
function quizNext() { quizSession.i++; quizSession.revealed = false; quizSession.sel = -1; quizSession.vals = []; renderQuiz(); }
function recordQuiz(q, ok) {
  const st = store.quiz[q.id] || (store.quiz[q.id] = { r: 0, w: 0 });
  ok ? st.r++ : st.w++;
  st.last = ok ? 'right' : 'wrong';
  if (quizSession) { quizSession.round.done++; if (ok) quizSession.round.right++; }
  save();
}
function pickOpt(k) {
  const s = quizSession, q = s.pool[s.i];
  if (!q || s.revealed || q.kind !== 'select') return;
  s.sel = k; s.revealed = true;
  recordQuiz(q, k === 'ABCD'.indexOf(q.a));
  renderQuiz();
}
function submitBlanks() {
  const s = quizSession, q = s.pool[s.i];
  if (!q || s.revealed || q.kind !== 'blank') return;
  const n = q.q.split(/＿{2,}/).length - 1;
  const inputs = document.querySelectorAll('.blankin');
  s.vals = []; s.blankOk = [];
  for (let k = 0; k < n; k++) {
    const v = (inputs[k] ? inputs[k].value : '');
    s.vals.push(v);
    const alts = (q.alts[k] || []);
    s.blankOk.push(alts.some(a => QNORM(a) === QNORM(v)));
  }
  s.revealed = true;
  recordQuiz(q, s.blankOk.every(Boolean));
  renderQuiz();
  if (!s.blankOk.every(Boolean)) {
    const inp = document.querySelector('.blankin');
    if (inp) inp.focus();
  }
}
function exportWrong() {
  const wrong = (DATA.quiz || []).filter(q => (store.quiz[q.id] || {}).last === 'wrong');
  if (!wrong.length) { openOverlay('📤 错题导出', '当前错题池是空的，太棒了！保持下去。', () => true); return; }
  let md = '# 错题本（' + new Date().toLocaleDateString() + '，共 ' + wrong.length + ' 题）\n\n';
  wrong.forEach(q => {
    md += '## [' + q.cat + '·' + q.diff + '] ' + q.q + '\n';
    if (q.kind === 'select') { q.opts.forEach((o, k) => md += '- ' + 'ABCD'[k] + '. ' + o + '\n'); md += '\n正确答案：' + q.a + '\n'; }
    else md += '\n正确答案：' + q.alts.map(a => a.join('／')).join('；') + '\n';
    md += '解析：' + q.exp.replace(/\[《([^》]+)》\]\(#[^)]+\)/g, '《$1》') + '\n\n';
  });
  const done = ok => openOverlay('📤 错题导出（' + wrong.length + ' 题，' + (ok ? '已复制到剪贴板' : '请手动复制') + '）', md, () => true);
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(md).then(() => done(true)).catch(() => done(false));
  } else done(false);
}

/* ---------- 综合大考 ---------- */
let examSession = null, examTimer = null;
function fmtMs(ms) {
  const t = Math.max(0, Math.floor(ms / 1000));
  return Math.floor(t / 60) + ':' + String(t % 60).padStart(2, '0');
}
function renderExam() {
  const s = examSession;
  if (!s) {
    $('#content').innerHTML = '<div class="cards-wrap"><div class="md"><h1>🏁 综合大考</h1>'
      + '<p style="color:var(--muted);font-size:13.5px">从全部 ' + (DATA.quiz || []).length + ' 题中随机抽题、统一计时，交卷后出分并逐题解析；成绩计入错题本与首页「薄弱环节」。建议大部分内容学完后再来，每次大考间隔至少一周。</p></div>'
      + '<div class="fcard" style="align-items:center;gap:16px;text-align:center">'
      + '<div style="font-size:13.5px;color:var(--muted)">选择题量（每题 1 分钟，中途可切换题目）</div>'
      + '<div class="chips" style="justify-content:center;margin:0">'
      + [10, 20, 40].map(n => '<span class="chip" onclick="startExam(' + n + ')">' + n + ' 题 · ' + n + ' 分钟</span>').join('')
      + '</div><div class="hint">快捷键：数字键 1~4 选答案 · ←/→ 切换题目 · E 交卷</div></div></div>';
    markActive(null); return;
  }
  if (s.phase === 'run') {
    const q = s.order[s.i];
    const answeredN = s.order.filter(x => {
      const a = s.answers[x.id];
      return a !== undefined && a !== null && !(Array.isArray(a) && a.every(v => !v));
    }).length;
    const dots = s.order.map((x, k) => {
      const a = s.answers[x.id];
      const has = a !== undefined && a !== null && !(Array.isArray(a) && a.every(v => !v));
      return '<div class="exdot' + (has ? ' answered' : '') + (k === s.i ? ' cur' : '') + '" onclick="examGo(' + k + ')">' + (k + 1) + '</div>';
    }).join('');
    let body;
    if (q.kind === 'select') {
      const sel = s.answers[q.id];
      body = '<div class="q">' + inline(esc(q.q)) + '</div><div style="margin-top:16px">'
        + q.opts.map((o, k) => '<div class="qopt' + (sel === 'ABCD'[k] ? ' right' : '') + '" onclick="examPick(' + k + ')"><b>' + 'ABCD'[k] + '</b><span>' + inline(esc(o)) + '</span></div>').join('') + '</div>';
    } else {
      const segs = q.q.split(/＿{2,}/);
      const cur = s.answers[q.id] || [];
      const stem = segs.map((seg, k) => inline(esc(seg))
        + (k < segs.length - 1 ? '<input class="blankin" data-k="' + k + '" value="' + esc(cur[k] || '') + '" oninput="examSetBlank(this)" placeholder="填空' + (k + 1) + '">' : '')).join('');
      body = '<div class="qstem">' + stem + '</div><div class="hint" style="margin-top:14px">作答会自动保存，切题不丢失</div>';
    }
    $('#content').innerHTML = '<div class="cards-wrap">'
      + '<div class="exbar"><span class="extimer" id="examTimer">' + fmtMs(s.deadline - Date.now()) + '</span>'
      + '<span style="font-size:13px;color:var(--muted)">第 ' + (s.i + 1) + ' / ' + s.order.length + ' 题 · 已答 ' + answeredN + '</span><span class="spacer"></span>'
      + '<button class="btn primary" onclick="submitExam()">交卷</button>'
      + '<button class="btn" onclick="examQuit()">放弃</button></div>'
      + '<div class="exgrid">' + dots + '</div>'
      + '<div class="fcard" onclick="event.stopPropagation()"><div class="cat">' + esc(q.cat) + ' · ' + esc(q.diff) + '</div>' + body + '</div>'
      + '<div class="facts"><button class="btn" onclick="examGo(' + (s.i - 1) + ')"' + (s.i === 0 ? ' disabled' : '') + '>← 上一题</button>'
      + '<button class="btn primary" onclick="examGo(' + (s.i + 1) + ')"' + (s.i === s.order.length - 1 ? ' disabled' : '') + '>下一题 →</button></div></div>';
    markActive(null); return;
  }
  const right = s.order.filter(q => s.result[q.id]).length;
  const list = s.order.map((q, k) => {
    const ok = s.result[q.id];
    return '<div class="exres-item' + (ok ? '' : ' bad') + '"><b>' + (ok ? '✅' : '❌') + ' 第 ' + (k + 1) + ' 题（' + esc(q.cat) + '·' + esc(q.diff) + '）</b>'
      + '<div style="margin:4px 0">' + inline(esc(q.q)) + '</div>'
      + (q.kind === 'select'
        ? '<div style="font-size:12.5px;color:var(--muted)">你的答案：' + esc(String(s.answers[q.id] || '未作答')) + '　·　正确答案：' + esc(q.a) + '</div>'
        : '<div style="font-size:12.5px;color:var(--muted)">正确答案：' + esc(q.alts.map(a => a.join('／')).join('；')) + '</div>')
      + '<blockquote style="margin:8px 0 0"><p>' + inline(esc(q.exp)) + '</p></blockquote>'
      + (q.ref && byId[q.ref] ? '<div class="ref" style="font-size:12.5px;margin-top:6px">📖 详见 <a href="#/f/' + q.ref + '">' + esc(byId[q.ref].title) + '</a></div>' : '')
      + '</div>';
  }).join('');
  $('#content').innerHTML = '<div class="cards-wrap"><div class="md"><h1>🏁 大考成绩</h1></div>'
    + '<div class="fcard" style="align-items:center;text-align:center"><div class="exscore">' + right + ' / ' + s.order.length + '</div>'
    + '<div style="font-size:14px;color:var(--muted);margin-top:6px">正确率 ' + Math.round(right / s.order.length * 100) + '% · 用时 ' + fmtMs(s.usedMs) + ' · ' + (right / s.order.length >= 0.85 ? '达到 85% 分手线，继续保持！' : '未到 85% 分手线：用「只做错题」+ 首页「薄弱环节」补漏后再来') + '</div>'
    + '<div class="acts" style="margin-top:14px;justify-content:center"><button class="btn primary" onclick="examSession=null;renderExam()">再来一套</button>'
    + '<button class="btn" onclick="location.hash=\'#/quiz\'">去练习模式复盘</button></div></div>'
    + '<div style="margin-top:14px">' + list + '</div></div>';
  markActive(null);
}
function startExam(n) {
  if (examTimer) clearInterval(examTimer);
  const pool = (DATA.quiz || []).slice();
  const order = shuffledArr(pool).slice(0, Math.min(n, pool.length));
  examSession = { phase: 'run', order, i: 0, answers: {}, result: {}, deadline: Date.now() + order.length * 60000, startTs: Date.now(), usedMs: 0 };
  examTimer = setInterval(examTick, 500);
  renderExam();
}
function examTick() {
  const s = examSession;
  if (!s || s.phase !== 'run') return;
  const el = document.getElementById('examTimer');
  if (el) {
    const left = s.deadline - Date.now();
    el.textContent = fmtMs(left);
    el.classList.toggle('low', left < 60000);
  }
  if (Date.now() >= s.deadline) submitExam(true);
}
function examGo(k) { const s = examSession; if (!s || k < 0 || k >= s.order.length) return; s.i = k; renderExam(); }
function examPick(k) { const s = examSession, q = s.order[s.i]; if (q.kind !== 'select') return; s.answers[q.id] = 'ABCD'[k]; renderExam(); }
function examSetBlank(inp) {
  const s = examSession, q = s.order[s.i];
  const k = +inp.dataset.k;
  const cur = s.answers[q.id] || [];
  cur[k] = inp.value;
  s.answers[q.id] = cur;   // 不重渲染，避免输入焦点丢失
}
function examQuit() {
  if (confirm('放弃本次大考？作答将不计入记录。')) {
    if (examTimer) clearInterval(examTimer);
    examSession = null; renderExam();
  }
}
function submitExam(auto) {
  const s = examSession;
  if (!s || s.phase !== 'run') return;
  if (!auto && !confirm('确认交卷？未作答的题按错误计。')) return;
  if (examTimer) clearInterval(examTimer);
  s.usedMs = Date.now() - s.startTs; s.phase = 'done';
  s.order.forEach(q => {
    let ok;
    if (q.kind === 'select') ok = s.answers[q.id] === q.a;
    else {
      const n = q.q.split(/＿{2,}/).length - 1;
      const vals = s.answers[q.id] || [];
      ok = [];
      for (let k = 0; k < n; k++) ok.push((q.alts[k] || []).some(a => QNORM(a) === QNORM(vals[k] || '')));
      ok = ok.every(Boolean);
    }
    s.result[q.id] = ok;
    recordQuiz(q, ok);
  });
  if (location.hash.startsWith('#/exam') || auto) renderExam();
}

/* ---------- 导入导出 / 主题 / 事件 ---------- */
function openOverlay(title, text, onOk) {
  $('#ovTitle').textContent = title; $('#ovText').value = text || '';
  $('#overlay').style.display = 'flex';
  $('#ovOk').onclick = () => { if (onOk($('#ovText').value)) $('#overlay').style.display = 'none'; };
  $('#ovCancel').onclick = () => $('#overlay').style.display = 'none';
}
$('#expBtn').onclick = () => openOverlay('导出进度（复制保存）', JSON.stringify(store), () => true);
$('#impBtn').onclick = () => openOverlay('导入进度（粘贴 JSON）', '', t => {
  try { const s = JSON.parse(t); if (typeof s !== 'object') throw 0; store = s; store.ck = store.ck || {}; store.done = store.done || {}; store.cards = store.cards || {}; store.quiz = store.quiz || {}; save(); location.reload(); return true; }
  catch (e) { alert('JSON 解析失败，请检查内容'); return false; }
});
$('#resetBtn').onclick = () => { if (confirm('确定清空所有打卡与学习进度？')) { store = { ck: {}, done: {}, cards: {}, quiz: {}, theme: store.theme, last: null }; save(); location.reload(); } };
$('#themeBtn').onclick = () => {
  store.theme = store.theme === 'dark' ? 'light' : 'dark'; save();
  document.documentElement.dataset.theme = store.theme;
  $('#themeBtn').textContent = store.theme === 'dark' ? '☀️' : '🌙';
};
$('#burger').onclick = () => $('#sidebar').classList.toggle('open');
$('#searchInput').addEventListener('keydown', e => {
  if (e.key === 'Enter') { location.hash = '#/search/' + encodeURIComponent(e.target.value.trim()); }
});
document.addEventListener('keydown', e => {
  if (e.key === '/' && document.activeElement.tagName !== 'TEXTAREA' && document.activeElement.tagName !== 'INPUT') { e.preventDefault(); $('#searchInput').focus(); }
  if (e.key === 'Escape') { $('#overlay').style.display = 'none'; $('#sidebar').classList.remove('open'); }
  if (e.key === 'Enter' && e.target && e.target.classList && e.target.classList.contains('blankin')) { e.preventDefault(); submitBlanks(); }
  const tg = document.activeElement ? document.activeElement.tagName : '';
  if (tg === 'INPUT' || tg === 'TEXTAREA') return;
  const h = location.hash || '#/home';
  if (h.startsWith('#/f/')) {
    if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
      const id = decodeURIComponent(h.slice(4));
      const idx = DATA.files.findIndex(f => f.id === id);
      const nb = DATA.files[idx + (e.key === 'ArrowRight' ? 1 : -1)];
      if (nb) { e.preventDefault(); goto(nb.id); }
    }
  } else if (h.startsWith('#/cards')) {
    if (e.key === ' ') { e.preventDefault(); cardSession.revealed = !cardSession.revealed; renderCards(); }
    else if (e.key === '1' && cardSession.revealed) grade('known');
    else if (e.key === '2' && cardSession.revealed) grade('review');
  } else if (h.startsWith('#/quiz')) {
    const s = quizSession;
    if (!s || !s.pool || s.i >= s.pool.length) return;
    const q = s.pool[s.i];
    if (!s.revealed && q.kind === 'select' && /^[1-4]$/.test(e.key)) { e.preventDefault(); pickOpt(+e.key - 1); }
    else if (s.revealed && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); quizNext(); }
  } else if (h.startsWith('#/exam')) {
    const s = examSession;
    if (!s || s.phase !== 'run') return;
    const q = s.order[s.i];
    if (q.kind === 'select' && /^[1-4]$/.test(e.key)) { e.preventDefault(); examPick(+e.key - 1); }
    else if (e.key === 'ArrowRight') { e.preventDefault(); examGo(s.i + 1); }
    else if (e.key === 'ArrowLeft') { e.preventDefault(); examGo(s.i - 1); }
    else if (e.key === 'e' || e.key === 'E') { e.preventDefault(); submitExam(); }
  }
});
document.addEventListener('change', e => {
  if (e.target.dataset && e.target.dataset.ck) {
    if (e.target.checked) store.ck[e.target.dataset.ck] = 1; else delete store.ck[e.target.dataset.ck];
    save(); updateBars();
  }
});
window.addEventListener('hashchange', route);

/* ---------- 启动 ---------- */
document.documentElement.dataset.theme = store.theme;
$('#themeBtn').textContent = store.theme === 'dark' ? '☀️' : '🌙';
buildSidebar();
route();
updateBars();
if (innerWidth > 920) document.querySelector('.stage')?.classList.add('open');
</script>
</body>
</html>'''

if __name__ == "__main__":
    main()

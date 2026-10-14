#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把多个出题分片的题库合并进 07-面试篇/05-选择填空题库.md。

用法：
    python3 app/merge-bank.py /tmp/bank            # 预览（不写文件）
    python3 app/merge-bank.py /tmp/bank --write    # 实际合并并重编号

分片文件约定（与 Agent 出题格式一致）：
- 只有 ### 题目块，无 # / ## 标题
- 选择题：4 个选项 A-D + `答案：X` + `解析：…详见《路径》`
- 填空题：题干含全角 ＿＿＿ + `答案：a／b；c` + `解析：…`
- 判断题：2 个选项 A/B + `答案：X` + `解析：…`

合并逻辑：按块类型分入三节 → 去重（题干归一化精确匹配）→
校验（答案合法、空数=答案数、详见路径存在）→ 全库连续重编号 → 写回。
"""
import argparse
import collections
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
BANK = ROOT / "07-面试篇" / "05-选择填空题库.md"

SEC_RE = re.compile(r"^## (选择题|填空题|判断题)\s*$", re.M)
BLOCK_SPLIT = re.compile(r"^### ", re.M)
HEAD_RE = re.compile(r"^(?:\d+[\.、]\s*)?（([^·（）]+)·([^）]+)）\s*(.+)$")
OPT_RE = re.compile(r"^-\s*([A-D])[\.、]\s*(.+)$", re.M)
ANS_RE = re.compile(r"^答案[：:]\s*(.+?)\s*$", re.M)
EXP_RE = re.compile(r"^解析[：:]\s*(.+?)\s*$", re.M)
REF_RE = re.compile(r"详见《([^》]+)》")

PUNCT = "`＿_。，,．.？?！!：:；;、\"“”‘’（）()【】[]「」《》 \t"


def norm_stem(s: str) -> str:
    """归一化题干用于查重。"""
    s = re.sub(r"^（[^）]*）", "", s)
    return "".join(ch for ch in s if ch not in PUNCT).lower()


def parse_block(block: str, section: str, src: str):
    """解析一个 ### 块，返回 dict；失败返回 (None, 原因)。"""
    lines = block.split("\n")
    head = HEAD_RE.match(lines[0].strip())
    if not head:
        return None, "题干头格式不符: " + lines[0][:40]
    cat, diff, stem = head.group(1).strip(), head.group(2).strip(), head.group(3).strip()
    if diff not in ("易", "中", "难"):
        return None, "难度非法(%s): %s" % (diff, stem[:30])
    rest = "\n".join(lines[1:])
    am, em = ANS_RE.search(rest), EXP_RE.search(rest)
    if not am:
        return None, "缺少答案: " + stem[:30]
    if not em:
        return None, "缺少解析: " + stem[:30]
    exp = em.group(1).strip()
    refs = REF_RE.findall(exp)
    if not refs:
        return None, "解析缺详见: " + stem[:30]
    for r in refs:
        p = r.split("、")[0].strip()
        if not (ROOT / p).exists():
            return None, "详见路径不存在(%s): %s" % (p, stem[:30])
    opts = OPT_RE.findall(rest)
    rec = {"cat": cat, "diff": diff, "stem": stem, "exp": exp, "src": src}
    if section == "填空题":
        nblank = len(re.findall(r"＿{2,}", stem))
        alts = [x.strip() for x in re.split(r"[；;]", am.group(1)) if x.strip()]
        if not nblank:
            return None, "填空题干无＿＿＿: " + stem[:30]
        if len(alts) != nblank:
            return None, "填空空数/答案数不符(%d≠%d): %s" % (nblank, len(alts), stem[:30])
        rec.update(kind="blank", alts=alts)
    else:
        letters = [o[0] for o in opts]
        need = 4 if section == "选择题" else 2
        if letters != list("ABCD")[:need]:
            return None, "选项异常(%s): %s" % ("".join(letters), stem[:30])
        letter = am.group(1).strip().upper()
        if letter not in list("ABCD")[:need]:
            return None, "答案非法(%s): %s" % (letter, stem[:30])
        if len({o[1].strip() for o in opts}) != need:
            return None, "选项内容重复: " + stem[:30]
        rec.update(kind="select" if need == 4 else "judge",
                   opts=[o[1].strip() for o in opts], ans=letter)
    return rec, None


def render(rec: dict, n: int) -> str:
    head = "### %d.（%s·%s）%s" % (n, rec["cat"], rec["diff"], rec["stem"])
    if rec["kind"] == "blank":
        body = "答案：" + "；".join(rec["alts"])
    else:
        body = "\n".join("- %s. %s" % ("ABCD"[i], o) for i, o in enumerate(rec["opts"]))
        body += "\n\n答案：" + rec["ans"]
    return head + ("\n" + body if rec["kind"] == "blank" else "\n" + body) + "\n解析：" + rec["exp"] + "\n"


def load_existing():
    text = BANK.read_text(encoding="utf-8")
    marks = [(m.start(), m.group(1)) for m in SEC_RE.finditer(text)]
    marks.append((len(text), None))
    out = {"选择题": [], "填空题": [], "判断题": []}
    for (s, name), (e, _) in zip(marks, marks[1:]):
        body = text[s:e]
        for blk in BLOCK_SPLIT.split(body)[1:]:
            rec, err = parse_block(blk.rstrip(), name, "existing")
            if err:
                print("  [existing] 跳过: " + err)
            else:
                out[name].append(rec)
    return text, out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("staging_dir", help="分片目录（*.md，按文件名排序合并）")
    ap.add_argument("--write", action="store_true", help="写回题库文件（否则仅预览）")
    args = ap.parse_args()

    text, existing = load_existing()
    seen = {norm_stem(r["stem"]) for sec in existing.values() for r in sec}
    dup_near = []
    added = {"选择题": [], "填空题": [], "判断题": []}
    errors = []

    files = sorted(pathlib.Path(args.staging_dir).glob("*.md"))
    if not files:
        sys.exit("分片目录里没有 .md 文件: " + args.staging_dir)
    for f in files:
        raw = f.read_text(encoding="utf-8")
        for blk in BLOCK_SPLIT.split(raw)[1:]:
            blk = blk.rstrip()
            # 分片文件内部按块自判类型
            n_opt = len(OPT_RE.findall(blk))
            if n_opt == 4:
                section = "选择题"
            elif n_opt == 2 and "＿" not in blk.split("\n")[0]:
                section = "判断题"
            elif "＿" in blk.split("\n")[0]:
                section = "填空题"
            else:
                errors.append("%s: 无法判定题型: %s" % (f.name, blk.split("\n")[0][:40]))
                continue
            rec, err = parse_block(blk, section, f.name)
            if err:
                errors.append("%s: %s" % (f.name, err))
                continue
            key = norm_stem(rec["stem"])
            if key in seen:
                dup_near.append("重复丢弃: " + rec["stem"][:40])
                continue
            seen.add(key)
            added[section].append(rec)

    # ---- 统计 ----
    print("=" * 60)
    print("分片目录:", args.staging_dir, "(%d 个文件)" % len(files))
    for sec in ("选择题", "填空题", "判断题"):
        print("  %s: 原 %d + 新 %d = %d" % (sec, len(existing[sec]), len(added[sec]),
                                            len(existing[sec]) + len(added[sec])))
    total = sum(len(existing[s]) + len(added[s]) for s in added)
    print("  合计: %d 题" % total)
    if errors:
        print("\n!! 解析失败 %d 条:" % len(errors))
        for e in errors[:20]:
            print("   -", e)
    if dup_near:
        print("\n去重丢弃 %d 条（列前 10）:" % len(dup_near))
        for d in dup_near[:10]:
            print("   -", d)

    merged = {sec: existing[sec] + added[sec] for sec in existing}
    sel = [r for r in merged["选择题"] if r["kind"] == "select"]
    jud = [r for r in merged["判断题"]]
    print("\n答案分布: 选择", dict(collections.Counter(r["ans"] for r in sel)),
          "| 判断", dict(collections.Counter(r["ans"] for r in jud)))
    print("难度分布:", dict(collections.Counter(r["diff"] for s in merged.values() for r in s)))
    print("cat 分布:", dict(collections.Counter(r["cat"] for s in merged.values() for r in s).most_common()))

    if not args.write:
        print("\n预览模式，未写文件。加 --write 生效。")
        return

    # ---- 重编号写回 ----
    lines = text.split("\n")
    header_end = SEC_RE.search(text)
    assert header_end, "找不到 ## 选择题"
    header = text[: header_end.start()].rstrip() + "\n"
    usage = re.sub(r"共 \d+ 题（选择 \d+ \+ 填空 \d+ \+ 判断 \d+）",
                   "共 %d 题（选择 %d + 填空 %d + 判断 %d）" % (
                       total, len(merged["选择题"]), len(merged["填空题"]), len(merged["判断题"])),
                   header, count=1)
    parts = [usage]
    n = 0
    for sec in ("选择题", "填空题", "判断题"):
        parts.append("\n## %s\n" % sec)
        for rec in merged[sec]:
            n += 1
            parts.append("\n" + render(rec, n))
    BANK.write_text("".join(parts).rstrip() + "\n", encoding="utf-8")
    print("\n已写回 %s，共 %d 题" % (BANK, n))


if __name__ == "__main__":
    main()

"""将 Kubernetes 中文文档（CC BY 4.0）清洗为纯 Markdown，并按标题切分为 chunks。

输入: data/raw/*.md   (从 kubernetes/website 仓库 content/zh-cn/docs/concepts 下载)
输出: data/docs/*.md  (清洗后的文档，可直接上传到 Dify 知识库)
      data/chunks.jsonl (本地 RAG 使用的切片)
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW, DOCS = ROOT / "data" / "raw", ROOT / "data" / "docs"
SRC_BASE = "https://kubernetes.io/zh-cn/docs/concepts/"
GH_BASE = "https://github.com/kubernetes/website/blob/main/content/zh-cn/docs/concepts/"

MAX_CHARS = 600      # 单个 chunk 最大字符数（中文约 300~400 token）
OVERLAP = 100        # 超长段落二次切分时的重叠字符数
MAX_CODE_LINES = 25  # 超长代码块截断，避免 YAML 示例挤占检索空间


def clean(text: str) -> tuple[str, str]:
    title = ""
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if m:
        t = re.search(r"^title:\s*(.+)$", m.group(1), re.M)
        title = t.group(1).strip().strip('"') if t else ""
        text = text[m.end():]
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)                  # 英文原文注释
    text = re.sub(r'\{\{<\s*glossary_tooltip[^>]*?text="([^"]*)"[^>]*>\}\}', r"\1", text)
    text = re.sub(r'\{\{<\s*glossary_definition[^>]*?term_id="([^"]*)"[^>]*>\}\}', "", text)
    text = re.sub(r'\{\{<\s*(note|caution|warning)\s*>\}\}', "> **注意：**", text)
    text = re.sub(r"\{\{[<%].*?[>%]\}\}", "", text, flags=re.S)        # 其余 Hugo shortcode
    text = re.sub(r"\s*\{#[^}]*\}", "", text)                           # 标题锚点
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)                # 去掉链接只留文字

    def trim_code(m):
        lines = m.group(0).split("\n")
        if len(lines) > MAX_CODE_LINES + 2:
            lines = lines[: MAX_CODE_LINES + 1] + ["# ...（示例已截断）", lines[-1]]
        return "\n".join(lines)
    text = re.sub(r"```.*?```", trim_code, text, flags=re.S)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return title, text


def split_sections(text: str):
    """按 ##/### 标题切分，返回 [(标题路径, 正文)]。"""
    sections, path, buf = [], [], []
    for line in text.split("\n"):
        h = re.match(r"^(#{2,4})\s+(.*)", line)
        if h:
            if "".join(buf).strip():
                sections.append((" > ".join(path), "\n".join(buf).strip()))
            level = len(h.group(1)) - 2
            path = path[:level] + [h.group(2).strip()]
            buf = []
        else:
            buf.append(line)
    if "".join(buf).strip():
        sections.append((" > ".join(path), "\n".join(buf).strip()))
    return sections


def window(body: str):
    """段落优先的滑动窗口切分。"""
    paras = [p for p in body.split("\n\n") if p.strip()]
    out, cur = [], ""
    for p in paras:
        if len(cur) + len(p) + 2 <= MAX_CHARS:
            cur = f"{cur}\n\n{p}" if cur else p
            continue
        if cur:
            out.append(cur)
        while len(p) > MAX_CHARS:
            out.append(p[:MAX_CHARS])
            p = p[MAX_CHARS - OVERLAP:]
        cur = (out[-1][-OVERLAP:] + "\n\n" + p) if out and len(out[-1]) >= MAX_CHARS else p
    if cur:
        out.append(cur)
    return out


def main():
    DOCS.mkdir(parents=True, exist_ok=True)
    chunks = []
    for f in sorted(RAW.glob("*.md")):
        rel = f.stem.replace("__index", "").replace("_", "/")
        title, body = clean(f.read_text(encoding="utf-8"))
        url = SRC_BASE + rel + "/"
        header = (f"# {title}\n\n> 来源：Kubernetes 官方中文文档 {url}\n"
                  f"> 许可：CC BY 4.0，© The Kubernetes Authors，内容经清洗（去除英文注释与模板标记）\n\n")
        (DOCS / f"{f.stem.strip('_')}.md").write_text(header + body + "\n", encoding="utf-8")
        for sec, sbody in split_sections(body):
            for piece in window(sbody):
                if len(piece.strip()) < 30:
                    continue
                chunks.append({"id": len(chunks), "doc": title, "section": sec or "概述",
                               "url": url, "text": piece.strip()})
    with open(ROOT / "data" / "chunks.jsonl", "w", encoding="utf-8") as fp:
        for c in chunks:
            fp.write(json.dumps(c, ensure_ascii=False) + "\n")
    print(f"docs: {len(list(DOCS.glob('*.md')))}, chunks: {len(chunks)}", file=sys.stderr)


if __name__ == "__main__":
    main()

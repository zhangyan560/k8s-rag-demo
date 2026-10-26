"""跑一组示例问题，输出 Markdown 到 docs/example_qa.md。"""
from pathlib import Path
from rag.engine import RAG

QS = ["ConfigMap 和 Secret 有什么区别？", "Deployment 如何回滚到之前的版本？",
      "PersistentVolume 的回收策略有哪些？", "什么是污点和容忍度？", "今天上海天气怎么样？"]
rag = RAG()
out = ["# 示例问答（抽取式模式，未使用 LLM）\n"]
for q in QS:
    r = rag.answer(q)
    out.append(f"## 问：{q}\n\n模式：`{r['mode']}`\n\n{r['answer']}\n")
    for n, h in enumerate(r["hits"], 1):
        out.append(f"- [{n}] 《{h.chunk['doc']}》{h.chunk['section']}（重排分 {h.score:.2f}） {h.chunk['url']}")
    out.append("")
Path("docs").mkdir(exist_ok=True)
Path("docs/example_qa.md").write_text("\n".join(out), encoding="utf-8")
print("\n".join(out))

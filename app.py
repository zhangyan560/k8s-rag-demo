"""Streamlit 界面：Kubernetes 中文文档知识库问答（RAG Demo）。运行：streamlit run app.py"""
import time

import streamlit as st

from rag.engine import RAG, RERANK_MODEL, EMBED_MODEL

st.set_page_config(page_title="K8s 知识库问答 · RAG Demo", page_icon="📚", layout="wide")


@st.cache_resource(show_spinner="正在加载向量模型与索引…")
def load():
    return RAG()


rag = load()

with st.sidebar:
    st.header("⚙️ 检索设置")
    mode = st.radio("检索方式", ["hybrid", "dense", "bm25"], index=0,
                    format_func={"hybrid": "混合检索（向量 + BM25）", "dense": "仅向量检索", "bm25": "仅关键词 BM25"}.get)
    top_k = st.slider("Top K（引用片段数）", 2, 8, 4)
    st.divider()
    st.caption(f"生成模式：**{'LLM（OpenAI 兼容接口）' if rag.llm_enabled() else '抽取式（未配置 LLM 密钥）'}**")
    st.caption(f"向量模型：`{EMBED_MODEL}`")
    st.caption(f"重排序模型：`{RERANK_MODEL or '关闭'}`")
    st.caption(f"知识库：Kubernetes 官方中文文档 16 篇 · {len(rag.chunks)} 个切片")
    st.caption("文档许可：CC BY 4.0 © The Kubernetes Authors")

st.title("📚 Kubernetes 中文文档知识库问答")
st.caption("RAG 演示：文档切片 → 向量化 → 混合检索 + 重排序 → 带引用的回答")

examples = ["ConfigMap 和 Secret 有什么区别？", "Deployment 如何回滚到之前的版本？",
            "PersistentVolume 的回收策略有哪些？", "什么是污点和容忍度？"]
cols = st.columns(len(examples))
for c, q in zip(cols, examples):
    if c.button(q, use_container_width=True):
        st.session_state["q"] = q

query = st.text_input("请输入你的问题", key="q", placeholder="例如：Service 有哪几种类型？")

if query:
    t0 = time.time()
    with st.spinner("检索中…"):
        out = rag.answer(query, top_k=top_k, mode=mode)
    st.subheader("回答")
    st.markdown(out["answer"])
    st.caption(f"模式：{out['mode']} · 耗时 {time.time() - t0:.2f}s")
    if out["hits"]:
        st.subheader("引用来源")
        for n, h in enumerate(out["hits"], 1):
            c = h.chunk
            with st.expander(f"[{n}] 《{c['doc']}》 {c['section']}  ·  相关度 {h.score:.2f}", expanded=(n == 1)):
                st.markdown(c["text"])
                st.markdown(f"原文：[{c['url']}]({c['url']})")

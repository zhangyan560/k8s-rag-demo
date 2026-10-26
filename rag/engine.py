"""RAG 核心流程：加载 chunks -> 向量化 -> 混合检索（向量 + BM25）-> 生成带引用的回答。

生成模式：
- LLM 模式：设置 LLM_BASE_URL / LLM_API_KEY / LLM_MODEL（任意 OpenAI 兼容接口）后自动启用；
- 抽取式模式：未配置密钥时，从检索到的片段中挑选与问题最相关的句子拼成回答，并标注引用。
"""
from __future__ import annotations

import json
import math
import os
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
CHUNKS = ROOT / "data" / "chunks.jsonl"
INDEX = ROOT / "data" / "index.npy"
EMBED_MODEL = os.getenv("EMBED_MODEL", "BAAI/bge-small-zh-v1.5")
RERANK_MODEL = os.getenv("RERANK_MODEL", "BAAI/bge-reranker-base")  # 设为空字符串可关闭重排序
QUERY_PREFIX = "为这个句子生成表示以用于检索相关文章："  # bge-zh 官方推荐的查询指令

SYSTEM_PROMPT = """你是一个基于知识库回答问题的助手，知识库内容为 Kubernetes 官方中文文档。
请严格遵守：
1. 只根据<参考资料>中的内容回答，不要使用资料以外的知识，不要编造。
2. 每个关键结论后用 [编号] 标注引用来源，编号对应参考资料的序号。
3. 如果参考资料不足以回答，直接说"知识库中没有找到相关内容"，并建议用户换个问法。
4. 用简洁的中文回答，必要时使用列表；涉及配置时可给出简短 YAML 示例。"""


@dataclass
class Hit:
    chunk: dict
    score: float
    dense: float
    sparse: float


def tokenize(text: str) -> list[str]:
    """中英文混合分词：英文/数字按单词，中文按字 bigram（无需额外分词库）。"""
    text = text.lower()
    toks = re.findall(r"[a-z0-9][a-z0-9\-\.]*", text)
    for seg in re.findall(r"[\u4e00-\u9fff]+", text):
        toks += [seg[i:i + 2] for i in range(len(seg) - 1)] or [seg]
    return toks


class BM25:
    def __init__(self, docs: list[list[str]], k1=1.5, b=0.75):
        self.k1, self.b = k1, b
        self.tf = [Counter(d) for d in docs]
        self.len = np.array([len(d) for d in docs], dtype=float)
        self.avg = self.len.mean()
        df = Counter(t for d in docs for t in set(d))
        n = len(docs)
        self.idf = {t: math.log(1 + (n - v + 0.5) / (v + 0.5)) for t, v in df.items()}

    def scores(self, q: list[str]) -> np.ndarray:
        s = np.zeros(len(self.tf))
        for t in set(q):
            if t not in self.idf:
                continue
            f = np.array([tf.get(t, 0) for tf in self.tf], dtype=float)
            s += self.idf[t] * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * self.len / self.avg))
        return s


class RAG:
    def __init__(self):
        from fastembed import TextEmbedding
        self.chunks = [json.loads(l) for l in CHUNKS.read_text(encoding="utf-8").splitlines()]
        self.model = TextEmbedding(EMBED_MODEL, cache_dir=str(ROOT / "models"))
        self.texts = [f"{c['doc']} | {c['section']}\n{c['text']}" for c in self.chunks]
        if INDEX.exists() and np.load(INDEX).shape[0] == len(self.chunks):
            self.emb = np.load(INDEX)
        else:
            self.emb = self._embed(self.texts)
            np.save(INDEX, self.emb)
        self.bm25 = BM25([tokenize(t) for t in self.texts])
        self.reranker = None
        if RERANK_MODEL:
            from fastembed.rerank.cross_encoder import TextCrossEncoder
            self.reranker = TextCrossEncoder(RERANK_MODEL, cache_dir=str(ROOT / "models"))

    def _embed(self, texts):
        v = np.array(list(self.model.embed(texts, batch_size=32)), dtype=np.float32)
        return v / np.linalg.norm(v, axis=1, keepdims=True)

    # ---------- 检索 ----------
    def retrieve(self, query: str, top_k=4, mode="hybrid", rrf_k=60, min_dense=0.35,
                 recall_k=20, rerank=True) -> list[Hit]:
        """两阶段检索：混合召回 recall_k 个候选 -> 交叉编码器重排序 -> 取 top_k。"""
        q = self._embed([QUERY_PREFIX + query])[0]
        dense = self.emb @ q
        sparse = self.bm25.scores(tokenize(query))
        if mode == "dense":
            fused = dense.copy()
        elif mode == "bm25":
            fused = sparse.copy()
        else:  # Reciprocal Rank Fusion，避免两种分数量纲不同的问题
            rd = np.argsort(-dense).argsort()
            rs = np.argsort(-sparse).argsort()
            fused = 1 / (rrf_k + rd + 1) + 1 / (rrf_k + rs + 1)
        order = np.argsort(-fused)
        hits, seen = [], set()
        for i in order:
            if dense[i] < min_dense:          # 相关性阈值：过滤明显无关内容
                continue
            key = (self.chunks[i]["doc"], self.chunks[i]["section"])
            if key in seen:                   # 同一小节只保留一个，增加来源多样性
                continue
            seen.add(key)
            hits.append(Hit(self.chunks[i], float(fused[i]), float(dense[i]), float(sparse[i])))
            if len(hits) >= (recall_k if (rerank and self.reranker) else top_k):
                break
        if rerank and self.reranker and hits:
            rs = list(self.reranker.rerank(query, [h.chunk["text"] for h in hits]))
            for h, r in zip(hits, rs):
                h.score = float(r)
            hits = sorted(hits, key=lambda h: -h.score)[:top_k]
        return hits

    # ---------- 生成 ----------
    @staticmethod
    def llm_enabled() -> bool:
        return all(os.getenv(k) for k in ("LLM_BASE_URL", "LLM_API_KEY", "LLM_MODEL"))

    @staticmethod
    def build_context(hits: list[Hit]) -> str:
        return "\n\n".join(f"[{n}] 《{h.chunk['doc']}》- {h.chunk['section']}\n{h.chunk['text']}"
                           for n, h in enumerate(hits, 1))

    def answer(self, query: str, top_k=4, mode="hybrid") -> dict:
        hits = self.retrieve(query, top_k=top_k, mode=mode)
        if not hits:
            return {"answer": "知识库中没有找到相关内容，请换个问法试试。", "hits": [], "mode": "none"}
        if self.llm_enabled():
            try:
                return {"answer": self._llm(query, hits), "hits": hits, "mode": "llm"}
            except Exception as e:  # 网络或密钥问题时降级，保证 demo 可用
                ans = self._extractive(query, hits)
                return {"answer": f"（LLM 调用失败，已降级为抽取式：{e}）\n\n{ans}", "hits": hits, "mode": "extractive"}
        return {"answer": self._extractive(query, hits), "hits": hits, "mode": "extractive"}

    def _llm(self, query, hits) -> str:
        import requests
        r = requests.post(
            os.environ["LLM_BASE_URL"].rstrip("/") + "/chat/completions",
            headers={"Authorization": f"Bearer {os.environ['LLM_API_KEY']}"},
            json={"model": os.environ["LLM_MODEL"], "temperature": 0.2,
                  "messages": [{"role": "system", "content": SYSTEM_PROMPT},
                               {"role": "user", "content": f"<参考资料>\n{self.build_context(hits)}\n</参考资料>\n\n问题：{query}"}]},
            timeout=60)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]

    def _extractive(self, query, hits, max_sents=4) -> str:
        """抽取式回答：句子级向量相似度 + 关键词重合，选出最相关的句子并标注引用。"""
        cands = []
        for n, h in enumerate(hits, 1):
            text = re.sub(r"```.*?```", "", h.chunk["text"], flags=re.S)
            text = text.replace("\n\n", "。")
            text = re.sub(r"(?<=[\u4e00-\u9fff，。、：（）])\s*\n\s*|\s*\n\s*(?=[\u4e00-\u9fff，。、：（）])", "", text)
            text = re.sub(r"\s*\n\s*", " ", text)
            for s in re.split(r"(?<=[。！？；])", text):
                s = s.strip(" 。>*-：:")
                if 12 <= len(s) <= 220 and re.search(r"[\u4e00-\u9fff]", s):
                    cands.append((n, s))
        if not cands:
            return "知识库中没有找到可直接引用的句子，请查看下方参考片段。"
        if self.reranker:
            score = np.array(list(self.reranker.rerank(query, [s for _, s in cands])))
        else:
            sv = self._embed([s for _, s in cands])
            q = self._embed([QUERY_PREFIX + query])[0]
            qt = set(tokenize(query))
            score = sv @ q + 0.02 * np.array([len(qt & set(tokenize(s))) for _, s in cands])
        score = score - 0.05 * np.array([n for n, _ in cands])  # 轻微偏好排名靠前的片段
        picked = sorted(np.argsort(-score)[:max_sents], key=lambda i: (cands[i][0], i))
        lines = [f"- {cands[i][1]}。[{cands[i][0]}]" for i in picked]
        return "根据知识库中的相关内容：\n\n" + "\n".join(lines)


if __name__ == "__main__":
    import sys
    rag = RAG()
    for q in sys.argv[1:] or ["ConfigMap 和 Secret 有什么区别？"]:
        out = rag.answer(q)
        print(f"\n### 问：{q}  （模式：{out['mode']}）\n{out['answer']}")
        for n, h in enumerate(out["hits"], 1):
            print(f"  [{n}] {h.chunk['doc']} - {h.chunk['section']}  rerank={h.score:.2f} dense={h.dense:.3f}")

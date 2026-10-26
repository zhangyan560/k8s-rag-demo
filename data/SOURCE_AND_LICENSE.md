# 数据来源与许可

- 来源：Kubernetes 官方网站中文文档（kubernetes/website 仓库 `content/zh-cn/docs/concepts/`）
  - 仓库：https://github.com/kubernetes/website
  - 在线：https://kubernetes.io/zh-cn/docs/concepts/
- 许可：Creative Commons Attribution 4.0 International（CC BY 4.0），© The Kubernetes Authors
  - 许可全文：https://creativecommons.org/licenses/by/4.0/ 及仓库根目录 LICENSE
- 下载时间：2026-10-26（main 分支）
- 修改说明：`data/docs/` 为清洗后版本——去除了 YAML front matter、英文原文注释、Hugo 模板标记和超链接，超长代码示例做了截断；`data/chunks.jsonl` 为切片结果。原始文件保留在 `data/raw/`。
- 选取的 16 篇文档：概述、组件、Pod、Deployment、StatefulSet、DaemonSet、Job、Service、Ingress、ConfigMap、Secret、持久卷、卷、污点和容忍度、名字空间、标签和选择算符。

# 示例问答（抽取式模式，未使用 LLM）

## 问：ConfigMap 和 Secret 有什么区别？

模式：`extractive`

根据知识库中的相关内容：

- Secret 是一种包含少量敏感信息例如密码、令牌或密钥的对象。[1]
- Secret 类似于 ConfigMap但专门用于保存机密数据。[1]
- 尽管 ConfigMap 和 Secret 的工作方式类似，但 Kubernetes 对 Secret 有一些额外的保护。[2]
- ConfigMap 也可被系统的其他组件使用，而不一定直接暴露给 Pod。[4]

- [1] 《Secret》概述（重排分 4.64） https://kubernetes.io/zh-cn/docs/concepts/configuration/secret/
- [2] 《Secret》Secret 的信息安全问题（重排分 4.44） https://kubernetes.io/zh-cn/docs/concepts/configuration/secret/
- [3] 《Secret》不可更改的 Secret（重排分 2.01） https://kubernetes.io/zh-cn/docs/concepts/configuration/secret/
- [4] 《ConfigMap》使用 ConfigMap（重排分 1.95） https://kubernetes.io/zh-cn/docs/concepts/configuration/configmap/

## 问：Deployment 如何回滚到之前的版本？

模式：`extractive`

根据知识库中的相关内容：

- 按照下面给出的步骤将 Deployment 从当前版本回滚到以前的版本（即版本 2）。[1]
- 1. 假定现在你已决定撤消当前上线并回滚到以前的修订版本。[1]
- 现在，Deployment 正在回滚到以前的稳定版本。[1]
- 换言之，当你回滚到较早的修订版本时，只有 Deployment 的 Pod 模板部分会被回滚。[3]

- [1] 《Deployments》回滚 Deployment > 回滚到之前的修订版本（重排分 7.51） https://kubernetes.io/zh-cn/docs/concepts/workloads/controllers/deployment/
- [2] 《Deployments》清理策略（重排分 5.15） https://kubernetes.io/zh-cn/docs/concepts/workloads/controllers/deployment/
- [3] 《Deployments》回滚 Deployment（重排分 5.08） https://kubernetes.io/zh-cn/docs/concepts/workloads/controllers/deployment/
- [4] 《Deployments》编写 Deployment 规约 > 修订历史限制（重排分 4.76） https://kubernetes.io/zh-cn/docs/concepts/workloads/controllers/deployment/

## 问：PersistentVolume 的回收策略有哪些？

模式：`extractive`

根据知识库中的相关内容：

- 回收策略 `Retain` 使得用户可以手动回收资源。[1]
- 对于支持 `Delete` 回收策略的卷插件，删除动作会将 PersistentVolume 对象从Kubernetes 中移除，同时也会从外部基础设施中移除所关联的存储资产。[2]
- 动态制备的卷会继承其 StorageClass 中设置的回收策略，该策略默认为 `Delete`。[2]
- PersistentVolume 对象的回收策略告诉集群，当其被从申领中释放时如何处理该数据卷。[3]

- [1] 《持久卷》卷和申领的生命周期 > 回收（Reclaiming） > 保留（Retain）（重排分 7.55） https://kubernetes.io/zh-cn/docs/concepts/storage/persistent-volumes/
- [2] 《持久卷》卷和申领的生命周期 > 回收（Reclaiming） > 删除（Delete）（重排分 6.34） https://kubernetes.io/zh-cn/docs/concepts/storage/persistent-volumes/
- [3] 《持久卷》卷和申领的生命周期 > 回收（Reclaiming）（重排分 6.23） https://kubernetes.io/zh-cn/docs/concepts/storage/persistent-volumes/
- [4] 《持久卷》持久卷 > 回收策略（重排分 5.80） https://kubernetes.io/zh-cn/docs/concepts/storage/persistent-volumes/

## 问：什么是污点和容忍度？

模式：`extractive`

根据知识库中的相关内容：

- 与污点类似，容忍度会应用于共享同一分配设备的所有 Pod。[1]
- 通过污点和容忍度，可以灵活地让 Pod **避开**某些节点或者将 Pod 从某些节点驱逐。[2]
- 容忍度值和污点值都必须是有效的、带符号的 64 位整数（不允许带前导零的数字，例如 `"0550"`）。[3]
- Kubernetes 处理多个污点和容忍度的过程就像一个过滤器：从一个节点的所有污点开始遍历，过滤掉那些 Pod 中存在与之相匹配的容忍度的污点。[4]

- [1] 《污点和容忍度》设备污点与容忍度（重排分 3.53） https://kubernetes.io/zh-cn/docs/concepts/scheduling-eviction/taint-and-toleration/
- [2] 《污点和容忍度》使用例子（重排分 2.67） https://kubernetes.io/zh-cn/docs/concepts/scheduling-eviction/taint-and-toleration/
- [3] 《污点和容忍度》数值比较运算符（重排分 1.24） https://kubernetes.io/zh-cn/docs/concepts/scheduling-eviction/taint-and-toleration/
- [4] 《污点和容忍度》概念（重排分 0.38） https://kubernetes.io/zh-cn/docs/concepts/scheduling-eviction/taint-and-toleration/

## 问：今天上海天气怎么样？

模式：`none`

知识库中没有找到相关内容，请换个问法试试。


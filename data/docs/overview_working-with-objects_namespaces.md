# 名字空间

> 来源：Kubernetes 官方中文文档 https://kubernetes.io/zh-cn/docs/concepts/overview/working-with-objects/namespaces/
> 许可：CC BY 4.0，© The Kubernetes Authors，内容经清洗（去除英文注释与模板标记）

在 Kubernetes 中，**名字空间（Namespace）** 提供一种机制，将同一集群中的资源划分为相互隔离的组。
同一名字空间内的资源名称要唯一，但跨名字空间时没有这个要求。
名字空间作用域仅针对带有名字空间的对象，
（例如 Deployment、Service 等），这种作用域对集群范围的对象
（例如 StorageClass、Node、PersistentVolume 等）不适用。

## 何时使用多个名字空间

名字空间适用于存在很多跨多个团队或项目的用户的场景。
对于只有几到几十个用户的集群，根本不需要创建或考虑名字空间。
当需要名字空间提供的功能时，请开始使用它们。

名字空间为名称提供了一个范围。资源的名称需要在名字空间内是唯一的，但不能跨名字空间。
名字空间不能相互嵌套，每个 Kubernetes 资源只能在一个名字空间中。

名字空间是在多个用户之间划分集群资源的一种方法（通过资源配额）。

不必使用多个名字空间来分隔仅仅轻微不同的资源，例如同一软件的不同版本：
应该使用标签来区分同一名字空间中的不同资源。

> **注意：**

对于生产集群，请考虑**不要**使用 `default` 名字空间，
而是创建其他名字空间来使用。

## 初始名字空间

Kubernetes 启动时会创建四个初始名字空间：

`default`
: Kubernetes 包含这个名字空间，以便于你无需创建新的名字空间即可开始使用新集群。

`kube-node-lease`
: 该名字空间包含用于与各个节点关联的 Lease（租约）对象。
  节点租约允许 kubelet 发送心跳，
  由此控制面能够检测到节点故障。

`kube-public`
: **所有**的客户端（包括未经身份验证的客户端）都可以读取该名字空间。
  该名字空间主要预留为集群使用，以便某些资源需要在整个集群中可见可读。
  该名字空间的公共属性只是一种约定而非要求。

`kube-system`
: 该名字空间用于 Kubernetes 系统创建的对象。

## 使用名字空间

名字空间的创建和删除在名字空间的管理指南文档描述。

> **注意：**

避免使用前缀 `kube-` 创建名字空间，因为它是为 Kubernetes 系统名字空间保留的。

### 查看名字空间

你可以使用以下命令列出集群中现存的名字空间：

```shell
kubectl get namespace
```
```
NAME              STATUS   AGE
default           Active   1d
kube-node-lease   Active   1d
kube-public       Active   1d
kube-system       Active   1d
```

### 为请求设置名字空间

要为当前请求设置名字空间，请使用 `--namespace` 参数。

例如：

```shell
kubectl run nginx --image=nginx --namespace=<名字空间名称>
kubectl get pods --namespace=<名字空间名称>
```

### 设置名字空间偏好

你可以永久保存名字空间，以用于对应上下文中所有后续 kubectl 命令。

```shell
kubectl config set-context --current --namespace=<名字空间名称>
# 验证
kubectl config view --minify | grep namespace:
```

## 名字空间和 DNS

当你创建一个 Service 时，
Kubernetes 会创建一个相应的 DNS 条目。

该条目的形式是 `<Service 名称>.<名字空间名称>.svc.cluster.local`，这意味着如果容器只使用
`<Service 名称>`，它将被解析到本地名字空间的服务。这对于跨多个名字空间（如开发、测试和生产）
使用相同的配置非常有用。如果你希望跨名字空间访问，则需要使用完全限定域名（FQDN）。

因此，所有的名字空间名称都必须是合法的
RFC 1123 DNS 标签。

> **注意：**

通过创建与公共顶级域名同名的名字空间，
这些名字空间中的 Service 可以拥有与公共 DNS 记录重叠的、较短的 DNS 名称。
所有名字空间中的负载在执行 DNS 查找时，
如果查找的名称没有尾部句点，
就会被重定向到这些 Service 上，因此呈现出比公共 DNS 更高的优先序。

为了缓解这类问题，需要将创建名字空间的权限授予可信的用户。
如果需要，你可以额外部署第三方的安全控制机制，
例如以准入 Webhook
的形式，阻止用户创建与公共 TLD
同名的名字空间。

## 并非所有对象都在名字空间中

大多数 kubernetes 资源（例如 Pod、Service、副本控制器等）都位于某些名字空间中。
但是名字空间资源本身并不在名字空间中。而且底层资源，
例如节点和
持久化卷不属于任何名字空间。

查看哪些 Kubernetes 资源在名字空间中，哪些不在名字空间中：

```shell
# 位于名字空间中的资源
kubectl api-resources --namespaced=true

# 不在名字空间中的资源
kubectl api-resources --namespaced=false
```

## 自动打标签

Kubernetes 控制面会为所有名字空间设置一个不可变更的标签
`kubernetes.io/metadata.name`。
标签的值是名字空间的名称。

## 

* 进一步了解建立新的名字空间。
* 进一步了解删除名字空间。

# 污点和容忍度

> 来源：Kubernetes 官方中文文档 https://kubernetes.io/zh-cn/docs/concepts/scheduling-eviction/taint-and-toleration/
> 许可：CC BY 4.0，© The Kubernetes Authors，内容经清洗（去除英文注释与模板标记）

节点亲和性
是 Pod 的一种属性，它使 Pod
被吸引到一类特定的节点
（这可能出于一种偏好，也可能是硬性要求）。
**污点（Taint）** 则相反——它使节点能够排斥一类特定的 Pod。

**容忍度（Toleration）** 是应用于 Pod 上的。容忍度允许调度器调度带有对应污点的 Pod。
容忍度允许调度但并不保证调度：作为其功能的一部分，
调度器也会评估其他参数。

污点和容忍度（Toleration）相互配合，可以用来避免 Pod 被分配到不合适的节点上。
每个节点上都可以应用一个或多个污点，这表示对于那些不能容忍这些污点的 Pod，
是不会被该节点接受的。

## 概念

你可以使用命令 kubectl taint
给节点增加一个污点。比如：

```shell
kubectl taint nodes node1 key1=value1:NoSchedule
```

给节点 `node1` 增加一个污点，它的键名是 `key1`，键值是 `value1`，效果是 `NoSchedule`。
这表示只有拥有和这个污点相匹配的容忍度的 Pod 才能够被分配到 `node1` 这个节点。

若要移除上述命令所添加的污点，你可以执行：

```shell
kubectl taint nodes node1 key1=value1:NoSchedule-
```

你可以在 Pod 规约中为 Pod 设置容忍度。
下面两个容忍度均与上面例子中使用 `kubectl taint` 命令创建的污点相匹配，
因此如果一个 Pod 拥有其中的任何一个容忍度，都能够被调度到 `node1`：

```yaml
tolerations:
- key: "key1"
  operator: "Equal"
  value: "value1"
  effect: "NoSchedule"
```

```yaml
tolerations:
- key: "key1"
  operator: "Exists"
  effect: "NoSchedule"
```

默认的 Kubernetes 调度器在选择一个节点来运行特定的 Pod 时会考虑污点和容忍度。
然而，如果你手动为一个 Pod 指定了 `.spec.nodeName`，那么选节点操作会绕过调度器；
这个 Pod 将会绑定到你指定的节点上，即使你选择的节点上有 `NoSchedule` 的污点。
如果这种情况发生，且节点上还设置了 `NoExecute` 的污点，kubelet 会将 Pod 驱逐出去，除非有适当的容忍度设置。

下面是一个定义了一些容忍度的 Pod 的例子：

`operator` 的默认值是 `Equal`。

一个容忍度和一个污点相“匹配”是指它们有一样的键名和效果，并且：

* 如果 `operator` 是 `Exists`（此时容忍度不能指定 `value`），或者
* 如果 `operator` 是 `Equal`，则它们的值应该相等。

> **注意：**

存在两种特殊情况：

如果 `key` 为空，那么 `operator` 必须是 `Exists`，匹配所有 key 和 value。
注意，同时 `effect` 仍然需要匹配。

如果 `effect` 为空，则可以与所有键名 `key1` 的效果相匹配。

上述例子中 `effect` 使用的值为 `NoSchedule`，你也可以使用另外一个值 `PreferNoSchedule`。

`effect` 字段的允许值包括：

`NoExecute`
: 这会影响已在节点上运行的 Pod，具体影响如下：
  * 如果 Pod 不能容忍这类污点，会马上被驱逐。
  * 如果 Pod 能够容忍这类污点，但是在容忍度定义中没有指定 `tolerationSeconds`，
    则 Pod 还会一直在这个节点上运行。
  * 如果 Pod 能够容忍这类污点，而且指定了 `tolerationSeconds`，
    则 Pod 还能在这个节点上继续运行这个指定的时间长度。
    这段时间过去后，节点生命周期控制器从节点驱除这些 Pod。

`NoSchedule`
: 除非具有匹配的容忍度规约，否则新的 Pod 不会被调度到带有污点的节点上。
  当前正在节点上运行的 Pod **不会**被驱逐。

`PreferNoSchedule`
: `PreferNoSchedule` 是“偏好”或“软性”的 `NoSchedule`。
  控制平面将**尝试**避免将不能容忍污点的 Pod 调度到的节点上，但不能保证完全避免。

你可以给一个节点添加多个污点，也可以给一个 Pod 添加多个容忍度设置。
Kubernetes 处理多个污点和容忍度的过程就像一个过滤器：从一个节点的所有污点开始遍历，
过滤掉那些 Pod 中存在与之相匹配的容忍度的污点。余下未被过滤的污点的 effect 值决定了
Pod 是否会被分配到该节点。需要注意以下情况：

* 如果未被忽略的污点中存在至少一个 effect 值为 `NoSchedule` 的污点，
  则 Kubernetes 不会将 Pod 调度到该节点。
* 如果未被忽略的污点中不存在 effect 值为 `NoSchedule` 的污点，
  但是存在至少一个 effect 值为 `PreferNoSchedule` 的污点，
  则 Kubernetes 会**尝试**不将 Pod 调度到该节点。
* 如果未被忽略的污点中存在至少一个 effect 值为 `NoExecute` 的污点，
  则 Kubernetes 不会将 Pod 调度到该节点（如果 Pod 还未在节点上运行），
  并且会将 Pod 从该节点驱逐（如果 Pod 已经在节点上运行）。

例如，假设你给一个节点添加了如下污点：

```shell
kubectl taint nodes node1 key1=value1:NoSchedule
kubectl taint nodes node1 key1=value1:NoExecute
kubectl taint nodes node1 key2=value2:NoSchedule
```

假定某个 Pod 有两个容忍度：

```yaml
tolerations:
- key: "key1"
  operator: "Equal"
  value: "value1"
  effect: "NoSchedule"
- key: "key1"
  operator: "Equal"
  value: "value1"
  effect: "NoExecute"
```

在这种情况下，上述 Pod 不会被调度到上述节点，因为其没有容忍度和第三个污点相匹配。
但是如果在给节点添加上述污点之前，该 Pod 已经在上述节点运行，
那么它还可以继续运行在该节点上，因为第三个污点是三个污点中唯一不能被这个 Pod 容忍的。

通常情况下，如果给一个节点添加了一个 effect 值为 `NoExecute` 的污点，
则任何不能容忍这个污点的 Pod 都会马上被驱逐，任何可以容忍这个污点的 Pod 都不会被驱逐。
但是，如果 Pod 存在一个 effect 值为 `NoExecute` 的容忍度指定了可选属性
`tolerationSeconds` 的值，则表示在给节点添加了上述污点之后，
Pod 还能继续在节点上运行的时间。例如：

```yaml
tolerations:
- key: "key1"
  operator: "Equal"
  value: "value1"
  effect: "NoExecute"
  tolerationSeconds: 3600
```

这表示如果这个 Pod 正在运行，同时一个匹配的污点被添加到其所在的节点，
那么 Pod 还将继续在节点上运行 3600 秒，然后被驱逐。
如果在此之前上述污点被删除了，则 Pod 不会被驱逐。

## 数值比较运算符

除了 `Equal` 和 `Exists` 之外，你还可以使用数值比较运算符（`Gt` 和 `Lt`）
来匹配具有整数值的污点。这对于基于阈值的调度非常有用，
例如根据可靠性等级或 SLA 等级来匹配节点。

* `Gt`：当污点值大于容忍值时匹配。
* `Lt`：当污点值小于容忍值时匹配。

对于数值运算符，容忍值和污点值都必须是有效的整数。
如果二者中任一个值无法被解析为整数，则此容忍度不匹配。

> **注意：**

当你创建一个使用 `Gt` 或 `Lt` 容忍度运算符的 Pod 时，API
服务器会校验这些容忍度取值是否为有效整数。节点上的污点值在节点注册时不会被校验。
如果某个节点具有非数值的污点值（例如
`servicelevel.organization.example/agreed-service-level=high:NoSchedule`），
那么使用数值比较运算符的 Pod 将无法匹配该污点，因此也无法调度到该节点上。

例如，如果节点被打上表示服务级别协议（SLA）的污点：

```shell
kubectl taint nodes node1 servicelevel.organization.example/agreed-service-level=950:NoSchedule
```

Pod 可以容忍 SLA 大于 900 的节点：

此容忍度匹配 `node1` 上的污点，因为 `950 > 900`（对于 `Gt` 运算符来说，污点值大于容忍度值）。
同样地，你也可以使用 `Lt` 运算符来匹配污点值小于容忍度值的情况：

```yaml
tolerations:
- key: "servicelevel.organization.example/agreed-service-level"
  operator: "Lt"
  value: "1000"
  effect: "NoSchedule"
```

> **注意：**

当使用数值比较运算符时：

* 容忍度值和污点值都必须是有效的、带符号的 64 位整数
  （不允许带前导零的数字，例如 `"0550"`）。
* 如果某个值无法被解析为整数，则此容忍度不匹配。
* 数值运算符适用于所有污点效果：`NoSchedule`、`PreferNoSchedule` 和 `NoExecute`。
* 对于使用数值运算符的 `PreferNoSchedule`：如果 Pod 的容忍度不满足数值比较条件
  （例如在使用 `Gt` 时，污点值 < 容忍度值），调度器降低相应节点的优先级，
  但在没有更优选择的情况下，仍可能将 Pod 调度到该节点。

> **注意：**

在禁用 `TaintTolerationComparisonOperators` 特性门控之前：

* 你应定位所有使用 `Gt` 或 `Lt` 运算符的工作负载，以避免控制器出现热循环。
* 更新所有工作负载控制器模板，改为使用 `Equal` 或 `Exists` 运算符。
* 删除所有使用 `Gt` 或 `Lt` 运算符的 Pending Pod。
* 监控 `apiserver_request_total` 指标，关注校验错误是否突增。

## 使用例子

通过污点和容忍度，可以灵活地让 Pod **避开**某些节点或者将 Pod 从某些节点驱逐。
下面是几个使用例子：

* **专用节点**：如果想将某些节点专门分配给特定的一组用户使用，你可以给这些节点添加一个污点（即，
  `kubectl taint nodes nodename dedicated=groupName:NoSchedule`），
  然后给这组用户的 Pod 添加一个相对应的容忍度
  （通过编写一个自定义的准入控制器，
  很容易就能做到）。
  拥有上述容忍度的 Pod 就能够被调度到上述专用节点，同时也能够被调度到集群中的其它节点。
  如果你希望这些 Pod 只能被调度到上述专用节点，
  那么你还需要给这些专用节点另外添加一个和上述污点类似的 label（例如：`dedicated=groupName`），
  同时还要在上述准入控制器中给 Pod 增加节点亲和性要求，要求上述 Pod 只能被调度到添加了
  `dedicated=groupName` 标签的节点上。

* **配备了特殊硬件的节点**：在部分节点配备了特殊硬件（比如 GPU）的集群中，
  我们希望不需要这类硬件的 Pod 不要被调度到这些特殊节点，以便为后继需要这类硬件的 Pod 保留资源。
  要达到这个目的，可以先给配备了特殊硬件的节点添加污点
  （例如 `kubectl taint nodes nodename special=true:NoSchedule` 或
  `kubectl taint nodes nodename special=true:PreferNoSchedule`），
  然后给使用了这类特殊硬件的 Pod 添加一个相匹配的容忍度。
  和专用节点的例子类似，添加这个容忍度的最简单的方法是使用自定义
  准入控制器。
  比如，我们推荐使用扩展资源
  来表示特殊硬件，给配置了特殊硬件的节点添加污点时包含扩展资源名称，
  然后运行一个 ExtendedResourceToleration
  准入控制器。此时，因为节点已经被设置污点了，没有对应容忍度的 Pod 不会被调度到这些节点。
  但当你创建一个使用了扩展资源的 Pod 时，`ExtendedResourceToleration` 准入控制器会自动给
  Pod 加上正确的容忍度，这样 Pod 就会被自动调度到这些配置了特殊硬件的节点上。
  这种方式能够确保配置了特殊硬件的节点专门用于运行需要这些硬件的 Pod，
  并且你无需手动给这些 Pod 添加容忍度。

* **基于污点的驱逐**：这是在每个 Pod 中配置的在节点出现问题时的驱逐行为，
  接下来的章节会描述这个特性。

## 基于污点的驱逐

当某种条件为真时，节点控制器会自动给节点添加一个污点。当前内置的污点包括：

* `node.kubernetes.io/not-ready`：节点未准备好。这相当于节点状况 `Ready` 的值为 "`False`"。
* `node.kubernetes.io/unreachable`：节点控制器访问不到节点. 这相当于节点状况 `Ready`
  的值为 "`Unknown`"。
* `node.kubernetes.io/memory-pressure`：节点存在内存压力。
* `node.kubernetes.io/disk-pressure`：节点存在磁盘压力。
* `node.kubernetes.io/pid-pressure`：节点的 PID 压力。
* `node.kubernetes.io/network-unavailable`：节点网络不可用。
* `node.kubernetes.io/unschedulable`：节点不可调度。
* `node.cloudprovider.kubernetes.io/uninitialized`：如果 kubelet 启动时指定了一个“外部”云平台驱动，
  它将给当前节点添加一个污点将其标志为不可用。在 cloud-controller-manager
  的一个控制器初始化这个节点后，kubelet 将删除这个污点。

在节点被排空时，节点控制器或者 kubelet 会添加带有 `NoExecute` 效果的相关污点。
此效果被默认添加到 `node.kubernetes.io/not-ready` 和 `node.kubernetes.io/unreachable` 污点中。
如果异常状态恢复正常，kubelet 或节点控制器能够移除相关的污点。

在某些情况下，当节点不可达时，API 服务器无法与节点上的 kubelet 进行通信。
在与 API 服务器的通信被重新建立之前，删除 Pod 的决定无法传递到 kubelet。
同时，被调度进行删除的那些 Pod 可能会继续运行在分区后的节点上。

> **注意：**

控制面会限制向节点添加新污点的速率。这一速率限制可以管理多个节点同时不可达时
（例如出现网络中断的情况），可能触发的驱逐的数量。

你可以为 Pod 设置 `tolerationSeconds`，以指定当节点失效或者不响应时，
Pod 维系与该节点间绑定关系的时长。

比如，你可能希望在出现网络分裂事件时，对于一个与节点本地状态有着深度绑定的应用而言，
仍然停留在当前节点上运行一段较长的时间，以等待网络恢复以避免被驱逐。
你为这种 Pod 所设置的容忍度看起来可能是这样：

```yaml
tolerations:
- key: "node.kubernetes.io/unreachable"
  operator: "Exists"
  effect: "NoExecute"
  tolerationSeconds: 6000
```

> **注意：**

Kubernetes 会自动给 Pod 添加针对 `node.kubernetes.io/not-ready` 和
`node.kubernetes.io/unreachable` 的容忍度，且配置 `tolerationSeconds=300`，
除非用户自身或者某控制器显式设置此容忍度。

这些自动添加的容忍度意味着 Pod 可以在检测到对应的问题之一时，在 5
分钟内保持绑定在该节点上。

DaemonSet 中的 Pod 被创建时，
针对以下污点自动添加的 `NoExecute` 的容忍度将不会指定 `tolerationSeconds`：

* `node.kubernetes.io/unreachable`
* `node.kubernetes.io/not-ready`

这保证了出现上述问题时 DaemonSet 中的 Pod 永远不会被驱逐。

> **注意：**

在 1.29 之前，节点控制器负责为节点添加污点并驱逐 Pod。自 1.29 起，
基于污点的驱逐已从节点控制器中抽离，迁移为一个名为 taint-eviction-controller 的独立组件。
用户如需禁用基于污点的驱逐，可在 kube-controller-manager 中设置 `--controllers=-taint-eviction-controller`。

## 基于节点状态添加污点

控制平面使用节点控制器自动创建
与节点状况
对应的、效果为 `NoSchedule` 的污点。

调度器在进行调度时检查污点，而不是检查节点状况。这确保节点状况不会直接影响调度。
例如，如果 `DiskPressure` 节点状况处于活跃状态，则控制平面添加
`node.kubernetes.io/disk-pressure` 污点并且不会调度新的 Pod 到受影响的节点。
如果 `MemoryPressure` 节点状况处于活跃状态，则控制平面添加
`node.kubernetes.io/memory-pressure` 污点。

对于新创建的 Pod，可以通过添加相应的 Pod 容忍度来忽略节点状况。
控制平面还在具有除 `BestEffort` 之外的
QoS 类的 Pod 上添加
`node.kubernetes.io/memory-pressure` 容忍度。
这是因为 Kubernetes 将 `Guaranteed` 或 `Burstable` QoS 类中的 Pod（甚至没有设置内存请求的 Pod）
视为能够应对内存压力，而新创建的 `BestEffort` Pod 不会被调度到受影响的节点上。

DaemonSet 控制器自动为所有守护进程添加如下 `NoSchedule` 容忍度，以防 DaemonSet 崩溃：

* `node.kubernetes.io/memory-pressure`
* `node.kubernetes.io/disk-pressure`
* `node.kubernetes.io/pid-pressure`（1.14 或更高版本）
* `node.kubernetes.io/unschedulable`（1.10 或更高版本）
* `node.kubernetes.io/network-unavailable`（**只适合主机网络配置**）

添加上述容忍度确保了向后兼容，你也可以选择自由向 DaemonSet 添加容忍度。

## 设备污点与容忍度

在使用动态资源分配管理特殊硬件的集群中，
管理员可以选择为单个设备设置污点，
而不是为整个节点打污点。这样做的好处是，污点可以精确地作用于出现故障或需要维护的硬件。
同时也支持容忍度配置，并且可以在请求设备时指定。
与污点类似，容忍度会应用于共享同一分配设备的所有 Pod。

## 

* 阅读节点压力驱逐，
  以及如何配置其行为
* 阅读 Pod 优先级

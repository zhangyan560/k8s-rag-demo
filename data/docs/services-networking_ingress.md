# Ingress

> 来源：Kubernetes 官方中文文档 https://kubernetes.io/zh-cn/docs/concepts/services-networking/ingress/
> 许可：CC BY 4.0，© The Kubernetes Authors，内容经清洗（去除英文注释与模板标记）

> **注意：**

Kubernetes 项目推荐使用 Gateway 而不是
Ingress。
Ingress API 已经被冻结。

这意味着：
* Ingress API 是正式发布的，并且遵循正式发布 API
  的稳定性保证。
  Kubernetes 项目没有计划从 Kubernetes 中移除 Ingress。
* Ingress API 不再进行开发，也不会对其进行进一步的更改或更新。

## 术语

为了表达更加清晰，本指南定义以下术语：

* 节点（Node）: Kubernetes 集群中的一台工作机器，是集群的一部分。
* 集群（Cluster）: 一组运行容器化应用程序的 Node，这些应用由 Kubernetes 管理。
  在此示例和在大多数常见的 Kubernetes 部署环境中，集群中的节点都不在公共网络中。
* 边缘路由器（Edge Router）: 在集群中强制执行防火墙策略的路由器。
  可以是由云提供商管理的网关，也可以是物理硬件。
* 集群网络（Cluster Network）: 一组逻辑的或物理的连接，基于 Kubernetes
  网络模型实现集群内的通信。
* 服务（Service）：Kubernetes ，
  使用标签选择算符（Selectors）
  来选择一组 Pod。除非另作说明，否则假定 Service 具有只能在集群网络内路由的虚拟 IP。

## Ingress 是什么？

Ingress
提供从集群外部到集群内服务的
HTTP 和 HTTPS 路由。
流量路由由 Ingress 资源所定义的规则来控制。

下面是 Ingress 的一个简单示例，可将所有流量都发送到同一 Service：

通过配置，Ingress 可为 Service 提供外部可访问的 URL、对其流量作负载均衡、
终止 SSL/TLS，以及基于名称的虚拟托管等能力。
Ingress 控制器
负责完成 Ingress 的工作，具体实现上通常会使用某个负载均衡器，
不过也可以配置边缘路由器或其他前端来帮助处理流量。

Ingress 不会随意公开端口或协议。
将 HTTP 和 HTTPS 以外的服务开放到 Internet 时，通常使用
Service.Type=NodePort
或 Service.Type=LoadBalancer
类型的 Service。

## 环境准备

你必须拥有一个 Ingress 控制器 才能满足
Ingress 的要求。仅创建 Ingress 资源本身没有任何效果。

你可以从许多 Ingress 控制器中进行选择。

理想情况下，所有 Ingress 控制器都应遵从参考规范。
但实际上，各个 Ingress 控制器操作略有不同。

> **注意：**

确保你查看了 Ingress 控制器的文档，以了解选择它的注意事项。

## Ingress 资源

一个最小的 Ingress 资源示例：

Ingress 需要指定 `apiVersion`、`kind`、 `metadata`和 `spec` 字段。
Ingress 对象的命名必须是合法的 DNS 子域名名称。
关于如何使用配置文件的一般性信息，请参见部署应用、
配置容器、
管理资源。
Ingress 控制器经常使用注解来配置行为。
请查阅你选择的 Ingress 控制器的文档，以了解预期和/或支持的注解。

Ingress 规约
提供了配置负载均衡器或者代理服务器所需要的所有信息。
最重要的是，其中包含对所有入站请求进行匹配的规则列表。
Ingress 资源仅支持用于转发 HTTP(S) 流量的规则。

如果 `ingressClassName` 被省略，那么你应该定义一个默认的 Ingress 类。

有些 Ingress 控制器甚至可以在没有定义默认 IngressClass 的情况下工作。
即使你使用的 Ingress 控制器能够在没有任何 IngressClass 的情况下运行，
Kubernetes 项目仍然建议你定义一个默认的 IngressClass。

### Ingress 规则

每个 HTTP 规则都包含以下信息：

* 可选的 `host`。在此示例中，未指定 `host`，因此该规则基于所指定 IP 地址来匹配所有入站 HTTP 流量。
  如果提供了 `host`（例如 `foo.bar.com`），则 `rules` 适用于所指定的主机。
* 路径列表（例如 `/testpath`）。每个路径都有一个由 `service.name` 和 `service.port.name`
  或 `service.port.number` 确定的关联后端。
  主机和路径都必须与入站请求的内容相匹配，负载均衡器才会将流量引导到所引用的 Service，
* `backend`（后端）是 Service 文档中所述的 Service 和端口名称的组合，
  或者是通过 CRD
  方式来实现的自定义资源后端。
  对于发往 Ingress 的 HTTP（和 HTTPS）请求，如果与规则中的主机和路径匹配，
  则会被发送到所列出的后端。

通常会在 Ingress 控制器中配置 `defaultBackend`（默认后端），
以便为无法与规约中任何路径匹配的所有请求提供服务。

### 默认后端

没有设置规则的 Ingress 将所有流量发送到同一个默认后端，而在这种情况下
`.spec.defaultBackend` 则是负责处理请求的那个默认后端。
`defaultBackend` 通常是
Ingress 控制器的配置选项，
而非在 Ingress 资源中设置。
如果未设置 `.spec.rules`，则必须设置 `.spec.defaultBackend`。
如果未设置 `defaultBackend`，那么如何处理与所有规则都不匹配的流量将交由
Ingress 控制器决定（请参考你的 Ingress 控制器的文档以了解它是如何处理这种情况的）。

如果 Ingress 对象中主机和路径都没有与 HTTP 请求匹配，则流量将被路由到默认后端。

### 资源后端

`Resource` 后端是一个 ObjectRef 对象，指向同一名字空间中的另一个 Kubernetes 资源，
将其视为 Ingress 对象。
`Resource` 后端与 Service 后端是互斥的，在二者均被设置时会无法通过合法性检查。
`Resource` 后端的一种常见用法是将所有入站数据导向保存静态资产的对象存储后端。

创建了如上的 Ingress 之后，你可以使用下面的命令查看它：

```bash
kubectl describe ingress ingress-resource-backend
```

```
Name:             ingress-resource-backend
Namespace:        default
Address:
Default backend:  APIGroup: k8s.example.com, Kind: StorageBucket, Name: static-assets
Rules:
  Host        Path  Backends
  ----        ----  --------
  *
              /icons   APIGroup: k8s.example.com, Kind: StorageBucket, Name: icon-assets
Annotations:  <none>
Events:       <none>
```

### 路径类型

Ingress 中的每个路径都需要有对应的路径类型（Path Type）。未明确设置 `pathType`
的路径无法通过合法性检查。当前支持的路径类型有三种：

* `ImplementationSpecific`：对于这种路径类型，匹配方法取决于 IngressClass。
  具体实现可以将其作为单独的 `pathType` 处理或者作与 `Prefix` 或 `Exact`
  类型相同的处理。

* `Exact`：精确匹配 URL 路径，且区分大小写。

* `Prefix`：基于以 `/` 分隔的 URL 路径前缀匹配。匹配区分大小写，
  并且对路径中各个元素逐个执行匹配操作。
  路径元素指的是由 `/` 分隔符分隔的路径中的标签列表。
  如果每个 _p_ 都是请求路径 _p_ 的元素前缀，则请求与路径 _p_ 匹配。

  > **注意：**
  如果路径的最后一个元素是请求路径中最后一个元素的子字符串，则不会被视为匹配
  （例如：`/foo/bar` 匹配 `/foo/bar/baz`, 但不匹配 `/foo/barbaz`）。
  

### 示例

| 类型   | 路径                            | 请求路径        | 匹配与否？               |
|--------|---------------------------------|-----------------|--------------------------|
| Prefix | `/`                             | （所有路径）    | 是                       |
| Exact  | `/foo`                          | `/foo`          | 是                       |
| Exact  | `/foo`                          | `/bar`          | 否                       |
| Exact  | `/foo`                          | `/foo/`         | 否                       |
| Exact  | `/foo/`                         | `/foo`          | 否                       |
| Prefix | `/foo`                          | `/foo`, `/foo/` | 是                       |
| Prefix | `/foo/`                         | `/foo`, `/foo/` | 是                       |
| Prefix | `/aaa/bb`                       | `/aaa/bbb`      | 否                       |
| Prefix | `/aaa/bbb`                      | `/aaa/bbb`      | 是                       |
| Prefix | `/aaa/bbb/`                     | `/aaa/bbb`      | 是，忽略尾部斜线         |
| Prefix | `/aaa/bbb`                      | `/aaa/bbb/`     | 是，匹配尾部斜线         |
| Prefix | `/aaa/bbb`                      | `/aaa/bbb/ccc`  | 是，匹配子路径           |
| Prefix | `/aaa/bbb`                      | `/aaa/bbbxyz`   | 否，字符串前缀不匹配     |
| Prefix | `/`, `/aaa`                     | `/aaa/ccc`      | 是，匹配 `/aaa` 前缀     |
| Prefix | `/`, `/aaa`, `/aaa/bbb`         | `/aaa/bbb`      | 是，匹配 `/aaa/bbb` 前缀 |
| Prefix | `/`, `/aaa`, `/aaa/bbb`         | `/ccc`          | 是，匹配 `/` 前缀        |
| Prefix | `/aaa`                          | `/ccc`          | 否，使用默认后端         |
| 混合   | `/foo` (Prefix), `/foo` (Exact) | `/foo`          | 是，优选 Exact 类型      |

#### 多重匹配

在某些情况下，Ingress 中会有多条路径与同一个请求匹配。这时匹配路径最长者优先。
如果仍然有两条同等的匹配路径，则精确路径类型优先于前缀路径类型。

## 主机名通配符

主机名可以是精确匹配（例如 “`foo.bar.com`”）或者使用通配符来匹配
（例如 “`*.foo.com`”）。
精确匹配要求 HTTP `host` 头部字段与 `host` 字段值完全匹配。
通配符匹配则要求 HTTP `host` 头部字段与通配符规则中的后缀部分相同。

| 主机         | host 头部          | 匹配与否？                          |
| ------------ |--------------------| ------------------------------------|
| `*.foo.com`  | `bar.foo.com`      | 基于相同的后缀匹配                  |
| `*.foo.com`  | `baz.bar.foo.com`  | 不匹配，通配符仅覆盖了一个 DNS 标签 |
| `*.foo.com`  | `foo.com`          | 不匹配，通配符仅覆盖了一个 DNS 标签 |

## Ingress 类

Ingress 可以由不同的控制器实现，通常使用不同的配置。
每个 Ingress 应当指定一个类，也就是一个对 IngressClass 资源的引用。
IngressClass 资源包含额外的配置，其中包括应当实现该类的控制器名称。

IngressClass 中的 `.spec.parameters` 字段可用于引用其他资源以提供与该
IngressClass 相关的配置。

参数（`parameters`）的具体类型取决于你在 IngressClass 的 `.spec.controller`
字段中指定的 Ingress 控制器。

### IngressClass 的作用域

取决于你所使用的 Ingress 控制器，你可能可以使用集群作用域的参数或某个名字空间作用域的参数。

IngressClass 参数的默认作用域是集群范围。

如果你设置了 `.spec.parameters` 字段且未设置 `.spec.parameters.scope`
字段，或是将 `.spec.parameters.scope` 字段设为了 `Cluster`，
那么该 IngressClass 所引用的即是一个集群作用域的资源。
参数的 `kind`（和 `apiGroup` 一起）指向一个集群作用域的 API 类型
（可能是一个定制资源（Custom Resource）），而其 `name` 字段则进一步确定
该 API 类型的一个具体的、集群作用域的资源。

示例：

```yaml
---
apiVersion: networking.k8s.io/v1
kind: IngressClass
metadata:
  name: external-lb-1
spec:
  controller: example.com/ingress-controller
  parameters:
    # 此 IngressClass 的配置定义在一个名为 “external-config-1” 的
    # ClusterIngressParameter（API 组为 k8s.example.net）资源中。
    # 这项定义告诉 Kubernetes 去寻找一个集群作用域的参数资源。
    scope: Cluster
    apiGroup: k8s.example.net
    kind: ClusterIngressParameter
    name: external-config-1
```

如果你设置了 `.spec.parameters` 字段且将 `.spec.parameters.scope`
字段设为了 `Namespace`，那么该 IngressClass 将会引用一个名字空间作用域的资源。
`.spec.parameters.namespace` 必须和此资源所处的名字空间相同。

参数的 `kind`（和 `apiGroup` 一起）指向一个命名空间作用域的 API 类型
（例如：ConfigMap），而其 `name` 则进一步确定指定 API 类型的、
位于你指定的命名空间中的具体资源。

名字空间作用域的参数帮助集群操作者将对工作负载所需的配置数据（比如：负载均衡设置、
API 网关定义）的控制权力委派出去。如果你使用集群作用域的参数，那么你将面临以下情况之一：

- 每次应用一项新的配置变更时，集群操作团队需要批准其他团队所作的修改。
- 集群操作团队必须定义具体的准入控制规则，比如 RBAC
  角色与角色绑定，以使得应用程序团队可以修改集群作用域的配置参数资源。

IngressClass API 本身是集群作用域的。

这里是一个引用名字空间作用域配置参数的 IngressClass 的示例：

```yaml
---
apiVersion: networking.k8s.io/v1
kind: IngressClass
metadata:
  name: external-lb-2
spec:
  controller: example.com/ingress-controller
  parameters:
    # 此 IngressClass 的配置定义在一个名为 “external-config” 的
    # IngressParameter（API 组为 k8s.example.com）资源中，
    # 该资源位于 “external-configuration” 名字空间中。
    scope: Namespace
    apiGroup: k8s.example.com
    kind: IngressParameter
    namespace: external-configuration
    name: external-config
```

### 已废弃的注解

在 Kubernetes 1.18 版本引入 IngressClass 资源和 `ingressClassName` 字段之前，
Ingress 类是通过 Ingress 中的一个 `kubernetes.io/ingress.class` 注解来指定的。
这个注解从未被正式定义过，但是得到了 Ingress 控制器的广泛支持。

Ingress 中新的 `ingressClassName` 字段用来替代该注解，但并非完全等价。
注解通常用于引用实现该 Ingress 的控制器的名称，而这个新的字段则是对一个包含额外
Ingress 配置的 IngressClass 资源的引用，其中包括了 Ingress 控制器的名称。

### 默认 Ingress 类

你可以将一个特定的 IngressClass 标记为集群默认 Ingress 类。
将某个 IngressClass 资源的 `ingressclass.kubernetes.io/is-default-class` 注解设置为
`true` 将确保新的未指定 `ingressClassName` 字段的 Ingress 能够被赋予这一默认
IngressClass.

> **注意：**

如果集群中有多个 IngressClass 被标记为默认，准入控制器将阻止创建新的未指定
`ingressClassName` 的 Ingress 对象。
解决这个问题需要确保集群中最多只能有一个 IngressClass 被标记为默认。

首先定义一个默认的 IngressClass。建议指定默认的 IngressClass：

## Ingress 类型

### 由单个 Service 来支持的 Ingress

现有的 Kubernetes 概念允许你暴露单个 Service（参见替代方案）。
你也可以使用 Ingress 并设置无规则的**默认后端**来完成这类操作。

如果使用 `kubectl apply -f` 创建此 Ingress，则应该能够查看刚刚添加的 Ingress 的状态：

```shell
kubectl get ingress test-ingress
```

```
NAME           CLASS         HOSTS   ADDRESS         PORTS   AGE
test-ingress   external-lb   *       203.0.113.123   80      59s
```

其中 `203.0.113.123` 是由 Ingress 控制器分配的 IP，用以服务于此 Ingress。

> **注意：**

Ingress 控制器和负载平衡器的 IP 地址分配操作可能需要一两分钟。
在此之前，你通常会看到地址字段的取值为 `<pending>`。

### 简单扇出

一个扇出（Fanout）配置根据请求的 HTTP URI 将来自同一 IP 地址的流量路由到多个 Service。
Ingress 允许你将负载均衡器的数量降至最低。例如，这样的设置：

这将需要一个如下所示的 Ingress：

当你使用 `kubectl apply -f` 创建 Ingress 时：

```shell
kubectl describe ingress simple-fanout-example
```

```
Name:             simple-fanout-example
Namespace:        default
Address:          178.91.123.132
Default backend:  default-http-backend:80 (10.8.2.3:8080)
Rules:
  Host         Path  Backends
  ----         ----  --------
  foo.bar.com
               /foo   service1:4200 (10.8.0.90:4200)
               /bar   service2:8080 (10.8.0.91:8080)
Annotations:
  nginx.ingress.kubernetes.io/rewrite-target:  /
Events:
  Type     Reason  Age                From                     Message
  ----     ------  ----               ----                     -------
  Normal   ADD     22s                loadbalancer-controller  default/test
```

此 Ingress 控制器构造一个特定于实现的负载均衡器来供 Ingress 使用，
前提是 Service （`service1`、`service2`）存在。
当它完成负载均衡器的创建时，你会在 Address 字段看到负载均衡器的地址。

> **注意：**

取决于你所使用的 Ingress 控制器，
你可能需要创建默认 HTTP 后端服务。

### 基于名称的虚拟主机服务

基于名称的虚拟主机支持将针对多个主机名的 HTTP 流量路由到同一 IP 地址上。

以下 Ingress 让后台负载均衡器基于
Host 头部字段来路由请求。

如果你所创建的 Ingress 资源没有在 `rules` 中定义主机，则规则可以匹配指向
Ingress 控制器 IP 地址的所有网络流量，而无需基于名称的虚拟主机。

例如，下面的 Ingress 对象会将请求 `first.bar.com` 的流量路由到 `service1`，将请求
`second.bar.com` 的流量路由到 `service2`，而将所有其他流量路由到 `service3`。

### TLS

你可以通过设定包含 TLS 私钥和证书的Secret
来保护 Ingress。
Ingress 资源只支持一个 TLS 端口 443，并假定 TLS 连接终止于 Ingress 节点
（与 Service 及其 Pod 间的流量都以明文传输）。
如果 Ingress 中的 TLS 配置部分指定了不同主机，那么它们将通过
SNI TLS 扩展指定的主机名（如果 Ingress 控制器支持 SNI）在同一端口上进行复用。
TLS Secret 的数据中必须包含键名为 `tls.crt` 的证书和键名为 `tls.key` 的私钥，
才能用于 TLS 目的。例如：

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: testsecret-tls
  namespace: default
data:
  tls.crt: base64 编码的证书
  tls.key: base64 编码的私钥
type: kubernetes.io/tls
```

在 Ingress 中引用此 Secret 将会告诉 Ingress 控制器使用 TLS 加密从客户端到负载均衡器的通道。
你要确保所创建的 TLS Secret 创建自包含 `https-example.foo.com` 的公共名称
（Common Name，CN）的证书。这里的公共名称也被称为全限定域名（Fully Qualified Domain Name，FQDN）。

> **注意：**

注意，不能针对默认规则使用 TLS，因为这样做需要为所有可能的子域名签发证书。
因此，`tls` 字段中的 `hosts` 的取值需要与 `rules` 字段中的 `host` 完全匹配。

> **注意：**

各种 Ingress 控制器在所支持的 TLS 特性上参差不齐。
你应参考所选的 Ingress 控制器的文档，以了解 TLS
在你的环境中是如何工作的。

### 负载均衡

Ingress 控制器启动引导时使用一些适用于所有 Ingress 的负载均衡策略设置，
例如负载均衡算法、后端权重方案等。
更高级的负载均衡概念（例如持久会话、动态权重）尚未通过 Ingress 公开。
你可以通过用于 Service 的负载均衡器来获取这些功能。

值得注意的是，尽管健康检查不是通过 Ingress 直接暴露的，在 Kubernetes
中存在就绪态探针
这类等价的概念，供你实现相同的目的。
请查阅特定控制器的说明文档。

## 更新 Ingress

要更新现有的 Ingress 以添加新的 Host，可以通过编辑资源来更新它：

```shell
kubectl describe ingress test
```

```
Name:             test
Namespace:        default
Address:          178.91.123.132
Default backend:  default-http-backend:80 (10.8.2.3:8080)
Rules:
  Host         Path  Backends
  ----         ----  --------
  foo.bar.com
               /foo   service1:80 (10.8.0.90:80)
Events:
  Type     Reason  Age                From                     Message
  ----     ------  ----               ----                     -------
  Normal   ADD     35s                loadbalancer-controller  default/test
```

```shell
kubectl edit ingress test
```

这一命令将打开编辑器，允许你以 YAML 格式编辑现有配置。
修改它来增加新的主机：

```yaml
spec:
  rules:
  - host: foo.bar.com
    http:
      paths:
      - backend:
          service:
            name: service1
            port:
              number: 80
        path: /foo
        pathType: Prefix
  - host: bar.baz.com
    http:
      paths:
      - backend:
          service:
            name: service2
            port:
              number: 80
        path: /foo
        pathType: Prefix
..
```

保存更改后，kubectl 将更新 API 服务器上的资源，该资源将告诉 Ingress 控制器重新配置负载均衡器。

验证：

```shell
kubectl describe ingress test
```

```
Name:             test
Namespace:        default
Address:          178.91.123.132
Default backend:  default-http-backend:80 (10.8.2.3:8080)
Rules:
  Host         Path  Backends
  ----         ----  --------
  foo.bar.com
               /foo   service1:80 (10.8.0.90:80)
  bar.baz.com
               /foo   service2:80 (10.8.0.91:80)
Events:
  Type     Reason  Age                From                     Message
  ----     ------  ----               ----                     -------
  Normal   ADD     45s                loadbalancer-controller  default/test
```

你也可以针对修改后的 Ingress YAML 文件，通过 `kubectl replace -f` 命令获得同样结果。

## 跨可用区的失效

不同的云厂商使用不同的技术来实现跨故障域的流量分布。
请查看相关 Ingress 控制器的文档以了解详细信息。

## 替代方案

不直接使用 Ingress 资源，也有多种方法暴露 Service：

* 使用 Service.Type=LoadBalancer
* 使用 Service.Type=NodePort

## 

* 进一步了解 Ingress API
* 进一步了解 Ingress 控制器

# RPC协议的诞生背景与发展历程

## 概述
远程过程调用（**Remote Procedure Call**，RPC）协议是分布式系统发展的关键基石，其核心思想是让程序员能够像调用本地函数一样去调用位于另一台计算机上的函数，从而简化分布式应用的开发难度

## 发展历程

### ⏳ 时间线概览

| 时间点 | 关键事件 | 核心意义 |
| :--- | :--- | :--- |
| 1970年代 | **思想萌芽**：ARPAnet上出现关于远程调用的早期讨论，相关RFC文档（如RFC 674）提出过程调用协议的概念 | 奠定了RPC的基本设想，并早期意识到了远程调用与本地调用在故障、延迟等方面的差异 |
| 1984年 | **理论奠基**：Birrell和Nelson发表论文《Implementing Remote Procedure Calls》，系统性地阐述了RPC模型，引入了"存根（Stub）"概念 | 为RPC提供了经典的理论模型，明确了客户端存根和服务器存根的分工协作机制，影响至今 |
| 1980年代中后期 | **首次广泛应用**：Sun公司推出**SunRPC**（后称为ONC RPC），并将其成功应用于**网络文件系统（NFS）** | 证明了RPC在重大实际系统中的可行性，ONC RPC成为UNIX系统中的事实标准 |
| 1990年代初期 | **标准化与平台化**：开放软件基金会（OSF）发布**DCE/RPC**，作为其分布式计算环境（DCE）的一部分。同时，**CORBA**（公共对象请求代理体系结构）规范推出，支持跨语言通信 | 企业级RPC标准出现，旨在解决异构环境下的互操作问题 |
| 2000年代 | **Web服务与集成**：基于HTTP和XML的**XML-RPC**及其增强版**SOAP**协议盛行 | 将RPC理念与Web技术结合，虽然稍显笨重，但极大地促进了不同系统在互联网层面的集成 |
| 约2010年至今 | **现代化演进**：轻量级的RESTful架构流行，同时新一代高性能RPC框架涌现，如Google的**gRPC**（基于HTTP/2和Protocol Buffers） | 更注重性能、清晰的服务契约定义，以及对微服务架构的友好支持，标志着RPC技术进入成熟期 |

## REST架构风格/RESTful API
REST（英文Representational State Transfer）是一种基于客户端和服务器的架构风格，用于构建可伸缩、可维护的Web服务。REST的核心思想是，将Web应用程序的功能作为资源来表示，使用统一的标识符（URI）来对这些资源进行操作，并通过[HTTP协议](https://so.csdn.net/so/search?q=HTTP协议&spm=1001.2101.3001.7020)（GET、POST、PUT、DELETE等）来定义对这些资源的操作。

`Representational State Transfer`直接翻译是表现层状态转换，不是很好理解

https://developer.aliyun.com/article/1269846
https://www.ruanyifeng.com/blog/2011/09/restful.html

## RPC模型

https://zhuanlan.zhihu.com/p/376604163


## gPRC介绍
google开源的RPC框架，使用


### 使用了gRPC的明星产品
* 分布式计算框架Ray中使用gRPC完成不同组件间的通信
* 


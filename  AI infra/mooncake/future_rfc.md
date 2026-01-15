
# mooncake上如何发布kv event part 1 of 3
声明：这是一个讨论issue，欢迎大家交流各自的想法~
## 背景：
当前vllm[https://github.com/vllm-project/vllm/pull/16750]和sglang[https://github.com/sgl-project/sglang/pull/6098]均已支持发布kv-event用于外部组件实现kv-cache aware调度的能力。 mooncake作为 hicache的storage-backend接入sglang，也通过kv-connect接入了vllm。使用mooncake-store存储kv-cache是业界的一个共识，同时mooncake内segment allocat、migration、tired-cache、驱逐等特性会产生一个问题，即处理请求的node不一定在本地持有该请求的kv-cache. 那么使用mooncake-store后，如何做精确的cache aware policy便是一个有待解决的问题.

一种比较简单的想法是在mooncake上实现kv publisher，由mooncake主动发布kv event，已经有一个PR实现【贴 pr】。
## store event
直接通过
### take_event api (vllm)
如果将mooncake-store做为一个backend，可以在上层实现细致的api屏蔽掉store过程，但是例如kv 驱逐、移动等行为无法被router感知到
### 独立发布kv事件
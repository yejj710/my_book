# kv-event
vllm在 https://github.com/vllm-project/vllm/pull/16750 上提出一种通过zmq发布kvcache处理事件的能力。可以用于其他组件实时感知vllm系统中

# kv-event发展史

基于此，aibrix和dynamo等相继推出了基于kv-event的 cache aware调度能力，对应的PR分别是
https://github.com/vllm-project/aibrix/pull/1349 和 
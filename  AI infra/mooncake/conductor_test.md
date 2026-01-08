# 背景
测试conductor在不同场景下的性能收益 （PD混部、PD分离等）

# 部署设置

## PD分离
部署2p2d vllm实例，测试性能收益

122
prefiller    8100
decoder   8200
asibench
vllm_publisher   5557   5558

-------------
129
prefiller    8100
decoder   8200
toy-proxy  8877
conductor  13333
mooncake_master   50081
vllm_publisher   5557   5558
mooncake_publisher   19997

## mooncake、conductor设置
mooncake_config.json  用于mooncake_client初始化设置使用
```json
{
    "local_hostname": "",
    "metadata_server": "P2PHANDSHAKE",
    "protocol": "ascend",
    "device_name": "",
    "use_ascend_direct": true,
    "global_segment_size": 50000000000,
    "master_server_address": "129:50081"
}
```

conductor_config.json  用于conductor初始化使用
```json
{
    "kvevent_instance":
    {
        "vllm-1": 
        {
            "ip": "122",
            "port": 5557,
            "type": "vLLM",
            "modelname": "qwen2.5_7B",
            "lora_id": -1
        },
        "vllm-2":
        {
            "ip": "129",
            "port": 5557,
            "type": "vLLM",
            "modelname": "qwen2.5_7B",
            "lora_id": -1
        },
        "mooncake":
        {
            "ip": "129",
            "port": 19997,
            "type": "Mooncake",
            "modelname": "qwen2.5_7B",
            "lora_id": -1
        }
    },
    "http_server_port": 13333
}
```
# 服务拉起

## 拉起mooncake_master

```sh
mooncake_master -enable_kv_event_publish -kv_event_publisher_endpoint tcp://*:19997 -rpc_port 50081
```

## 拉起p、d实例
prefiller
```sh
export ASCEND_RT_VISIBLE_DEVICES=3
export VLLM_USE_V1=1
export MOONCAKE_CONFIG_PATH="xx/mooncake.json"
export ASCEND_BUFFER_POOL=4:8  # 配置中转传输Buffer
export PYTHONHASHSEED=1234


vllm serve model/qwen2.5_7B_instruct \
    --enforce-eager \
    --max-model-len 10000 \
    --port 8100 \
    --block-size 128 \
    --gpu-memory-utilization 0.8 \
    --served-model-name "qwen2.5_7B" \
    --trust-remote-code \
    --kv-events-config \
    '{
        "publisher": "zmq", 
        "enable_kv_cache_events": true, 
        "endpoint": "tcp://*:5557",
        "topic": "vllm",
        "replay_endpoint": "tcp://*:5558"
    }' \
    --kv-transfer-config \
	'{
		"kv_connector": "AscendStoreConnector",
        "kv_role": "kv_producer",
        "kv_connector_extra_config":{
            "use_layerwise": false,
            "backend": "mooncake",
            "lookup_rpc_port":"0"
        }
	}' > p.log

```

decoder

```sh
export ASCEND_RT_VISIBLE_DEVICES=5
export VLLM_USE_V1=1
export MOONCAKE_CONFIG_PATH="xx/mooncake.json"
export ASCEND_BUFFER_POOL=4:8 # 配置中转传输Buffer
export PYTHONHASHSEED=1234


vllm serve /model/qwen2.5_7B_instruct \
    --enforce-eager \
    --max-model-len 10000 \
    --port 8200 \
    --block-size 128 \
    --gpu-memory-utilization 0.8 \
    --served-model-name "qwen2.5_7B" \
    --trust-remote-code \
    --kv-transfer-config \
	'{
		"kv_connector": "AscendStoreConnector",
        "kv_role": "kv_consumer",
        "kv_connector_extra_config":{
            "use_layerwise": false,
            "backend": "mooncake",
            "lookup_rpc_port":"1",
            "consumer_is_to_load": true
        }
	}' > d.log

```

## conductor

```sh
export CONDUCTOR_CONFIG_PATH=""
mooncake_conductor
```

## toy-proxy

```sh
python cache_aware_disagg_proxy.py --prefiller-hosts 127.0.0.1 --prefiller-ports 8100 --decoder-host 127.0.0.1 --decoder-ports 8200 --conductor-address 127.0.0.1:13333 --port 8877 --host 127.0.0.1
```

## curl命令
```sh
curl -X POST http://127.0.0.1:8000/v1/completions \
    -H "Content-Type: application/json" \
    -d '{
    "prompt": "8AXZZzcK2c2sHfDMIMuzxbhTpeTpaMnZbom pJ2sNCuKscUAaT9M6fHJTntTGL5ezP2 4wAIcqZ1awBToir0yAmY72qeqxUB9dnP0ONceGj9lIoQTtjvm1wFTsFyDoQ8isdBA69dQbWWtNq3gOmdGoEswvfUz6jMkotPWiEWKX0rMcC31KCDQdJOX7ceyLEduFfjsl5YhWkk2hZtaHt5aFyeZr6yeozPmRAqWs1jQy1Qw1WOI3vSUkqviXUIhnqLs4loasU4N2RNeqb4jmBr1DC7zoXuDjQ2yT6X5vnZvHfHRmoAdHgPEBwJ5kexVxJDevhZopaH6YM1o2XdJmi4Es7RR0 4EH2acvWDNnvcdlfCytvBHaCw3YuJpu2Up64jdiOdenSi YGckVWy",
    "max_tokens": 100,
    "temperature": 0,
    "stream": True
    }'

```


## aisbench 性能测试
```sh
ais_bench --mode perf --models vllm_api_stream_chat_multiturn --datasets sharegpt_gen --num-prompts 1 --debug --num-warmups 0
```


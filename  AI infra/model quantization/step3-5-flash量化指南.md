# 1 环境准备

量化主要需要torch和transformers版本要对齐，step3-5依赖的transformer版本要求 :  {"transformers": ">=4.57.1,<5.0.0"}；

A5上torch_npu并未商发，可以先使用dev版本，torch安装2.9.0即可

# 2 msmodelslim环境准备

```sh
git clone https://gitcode.com/yejiajun/msmodelslim.git -b step35
cd msmodelslim/
bash install.sh
```

# 3 量化配置及命令

Step3-5-Flash模型有**42**层MOE，每层**288**个专家，每次只激活**8**个专家，官方提供了fp8的量化权重，在官方的量化处理中，只对路由专家的up_proj、gate_proj、down_proj做了动态量化，因此在做mxfp8的量化时，完全参照官方的实践进行即可，可以达到50%的权重压缩比。

理论上这种量化方式对精度的影响非常小，但是有几点问题需要进行分析：

- fp8的block划分和mxfp8不一致，理论上mxfp8具有更好的精度，减少离群值对于tensor的影响
- scale的精度不一致，mxfp8采用UE8M0存储scale，而fp8 per_block量化使用fp32存储scale

```sh
msmodelslim quant --trust_remote_code --model_path {放fp16权重的路径} --save_path {mxfp8权重生成路径} \ 
    --device npu:0 --model_type step3_5_flash \
    --config_path {xx/msmodelslim/lab_practice/step_3_5_flash/step3_5_moe_w8a8.yaml   modelslim中已经提供，根据自己代码clone的位置进行修改}
```

关键量化配置：

```yaml
# Copyright (c) Huawei Technologies Co., Ltd. 2025-2025. All rights reserved.
apiversion: modelslim_v1
metadata:
  config_id: Step-3.5-Flash_w8a8_mxfp8
  score: 90
  verified_model_types:
    - Step-3.5-Flash
  label:
    w_bit: 8
    a_bit: 8
    is_sparse: False
    kv_cache: False

default_w8a8_dynamic: &default_w8a8_dynamic
  act:
    scope: "per_block"
    dtype: "mxfp8"
    symmetric: True
    method: "minmax"
  weight:
    scope: "per_block"
    dtype: "mxfp8"
    symmetric: True
    method: "minmax"

spec:
  process:
    - type: "group"
      configs:
        - type: "linear_quant"
          qconfig: *default_w8a8_dynamic
          include: 
            - "*moe.experts*"
  save:
    - type: "ascendv1_saver"
      part_file_size: 4
  dataset: "data_list_1.jsonl"
```


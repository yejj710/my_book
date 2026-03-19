

# MicroScaling Data Formats



## 1. MicroScaling(MX)

![image-20260318165108648](./images/MicroScaling overview.png)

- MX 格式中的基本数据单元由 `k` 个数字组成的向量，并由一个共享的Scale `X` 组成

- 数据单元和Scale值的两种数据格式彼此独立，所有 `k` 个元素共享相同的元素数据格式

- MX 块的布局没有规定： 实现可以将 `X` 与元素连续存储，也可以分开存储，查看了step3-5和minimax存储方式，保存为safetensor的时候，采用的是分开存储方案（weight和scale维护不同的map key）。

  

方案A: Scale与元素交错存储
┌──────────┐──────────┐──────────┐
│  Scale                 │ Element0         │ Element1          │ ...
└──────────┴──────────┴──────────┘

方案B: Scale与元素分开存储
┌──────────┐──────────┐
│  All                     │ Elements          │
│  Scales               │                           │
└──────────┴──────────┘

## 2. 具体格式

![image-20260318171927002](./images/MX-comliant formats.png)

- 命名采用MX + element数据类型，例如 element元素的数据类型为int8，那么命名为MXINT8
- block_size 统一使用32，可能和硬件和DL中的设计和DL中



方案A: Scale与元素交错存储
┌──────────┐──────────┐──────────┐
│  Scale                 │ Element0         │ Element1          │ ...
└──────────┴──────────┴──────────┘

方案B: Scale与元素分开存储
┌──────────┐──────────┐
│  All                     │ Elements          │
│  Scales               │                           │
└──────────┴──────────┘

目前来看，对于FP8 per_block量化，方案B是当前业界更倾向的方式  

###  特殊值处理
MX格式通过两种方式编码`NaN`：
第一：如果`X`是`NaN`，则MX块中的所有element值都是`NaN`，无论编码方式如何
第二：如果X不是`NaN`，每个元素Pi可以单独编码`NaN`。根据元素格式，MX格式可以通过让`X`为一个数字（即不是`NaN`）且每个Pi单独编码Inf来编码Inf。共享的标度`X`不编码Inf



# 3. 华为体系

HiFP8



# reference

1. https://arxiv.org/pdf/2310.10537
2. https://www.opencompute.org/documents/ocp-microscaling-formats-mx-v1-0-spec-final-pdf
3. https://adg.csdn.net/69524bbd5b9f5f31781b6a33.html
4. https://github.com/microsoft/microxcaling?spm=a2ty_o01.29997173.0.0.69525171V0EEIn
5. 
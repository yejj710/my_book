# 背景

目前大多数模型主推的量化权重仍然以是fp8为主要数据格式，关于per_block量化方式，常用的block_size为128*128，scale使用fp32 存储。

| 指标   | BF16 | FP16 | FP32 |
| :----- | :--- | :--- | :--- |
| 总位数 | 16   | 16   | 32   |
| 指数位 | 8    | 5    | 8    |
| 尾数位 | 7    | 10   | 23   |
|        |      |      |      |

# 误差来源分析
当将FP32值转换为UE8M0格式时，主要误差来源是剔除23位尾数位和符号位，这会导致：

1. 量化误差 ：FP32值被强制舍入到最近的2的整数次幂
2. 相对误差 ：误差与数值大小成正比（约50%的相对误差）
3. 绝对误差 ：随数值增大而增大
4. 无法处理负的scale （**scale会有负数值吗，感觉并不需要？**）




# 误差评估方法

### 1.理论误差分析 

### 相对误差分析

对于原始FP32值，转换为最近的2的整数次幂，最大相对误差不会超过50%

### 绝对误差分析

绝对误差随着幂次的提升而提升，最大绝对误差为 2的127次方



# MXfp8 官方实践



### Algorithm 1: Convert vector of scalar floats $\{V_i\}_{i=1}^k$ to an MX block $\{X, \{P_i\}_{i=1}^k\}$

**Require:** $emax_{elem} = \text{exponent of the largest normal number in the element data format}$

1. $shared\_exp \leftarrow \lfloor \log_2(\max_i(|V_i|)) \rfloor - emax_{elem}$
2. $X \leftarrow 2^{shared\_exp}$
3. **for** $i = 1$ **to** $k$ **do**
4. &nbsp;&nbsp;&nbsp;&nbsp; $P_i = \text{quantize\_to\_element\_format}(V_i/X)$, clamping normal numbers
5. **end for**
6. **return** $X, \{P_i\}_{i=1}^k$



参考：https://arxiv.org/pdf/2310.10537

On Line 1, shared_exp contains an offset of emax_elem to map the max input exponent to the largest binade in the element data format. This enables full utilization of the element data format’s exponent range. 

On Line 4, when quantizing Vi/X, normal numbers that exceed the representable range of the element format are clamped to the maximum representable value, preserving the sign. Infs and NaNs are not clamped. This is in accordance with the OCP MX specification.

 On Line 4, Pi is set to zero if the corresponding input Vi is a subnormal Float32 number. This is not described in the OCP MX specification and was done to simplify the algorithm. 

When converting multi-dimensional tensors, a principle axis must be selected for the shared scale (typically the reduction dimension in matrix multiplication). For a 2D matrix, the scale can be shared by every k element in a row or column. Transposing a 2D matrix in an MX format changes the axis of the shared scale — i.e., conversion to MX format and transposing are not commutative operations.



# step3-5-Flash fp8量化权重迁移到A5 mxfp8分析

官方提供的fp8量化权重只对路由专家做了量化，由于该模型有**42**层MOE，每层**288**个专家，每次只激活**8**个专家，只对moe部分量化可以达到非常好的压缩比，并且对精度影响极小。

##  0. 两种格式block划分区别
### mxfp8
weight_block: 32
**gate_proj， up_proj**
Weight tensor Shape: [1280, 4096]
Weight tensor Dtype: F8_E4M3
Scale tensor Shape: [1280, 128]
Scale tensor Dtype: U8

**down_proj**
Weight tensor Shape: [4096, 1280]
Weight tensor Dtype: F8_E4M3
Scale tensor Shape: [4096, 40]
Scale tensor Dtype: U8


### fp8 per_block
weight_block: 128*128

**gate_proj， up_proj**
Weight tensor Shape: [288, 1280, 4096]
Weight tensor Dtype: F8_E4M3
Scale tensor Shape: [288, 10, 32]
Scale tensor Dtype: F32

**down_proj**
Weight tensor Shape: [288, 4096, 1280]
Weight tensor Dtype: F8_E4M3
Scale tensor Shape: [288, 32, 10]
Scale tensor Dtype: F32

### 如何进行block划分

### 



## 1. 查看fp8 per_block量化 每层scale的最小最大值，判断是否有负数值

(Pdb) max(min_scale_list)
0.00018637521
(Pdb) min(min_scale_list)
0.0001296997
(Pdb) max(max_scale_list)
0.0042201453
(Pdb) min(max_scale_list)
0.0003073556
(Pdb) len(min_scale_list)
126
(Pdb) len(max_scale_list)
126

step3-5-flash中并没有负值 scale

绘制gate_proj、up_proj、down_proj在不同层的走势曲线

![image-20260319190931655](C:\Users\yejiajun\AppData\Roaming\Typora\typora-user-images\image-20260319190931655.png)



## 2. 




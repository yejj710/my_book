from functools import reduce
import struct
import math
import os
from typing import Tuple, List
import json

from safetensors import safe_open
import numpy as np

from draw import plot_layer_values_with_statistics

def load_weight_map(index_path):
    with open(index_path, 'r') as f:
        index_data = json.load(f)
    return index_data['weight_map']

def get_group_size(weight_shape, scale_shape):
    weight_size = int(reduce(lambda x, y: x * y, weight_shape))
    scale_size = int(reduce(lambda x, y: x * y, scale_shape))
    
    if weight_size % scale_size != 0:
        raise ValueError(f"Weight size {weight_size} is not divisible by scale size {scale_size}")
    
    return weight_size // scale_size


def is_power_of_two(x: float, epsilon: float = 1e-7) -> bool:
    """
    检查一个浮点数是否是2的幂次方
    Args:
        x: 要检查的浮点数
        epsilon: 容差范围
    Returns:
        True如果是2的幂次方，否则False
    """
    if x == 0:
        return False
    
    log2_x = math.log2(abs(x))
    # 检查log2_x是否接近整数
    return abs(log2_x - round(log2_x)) < epsilon


def fp32_to_e8m0(x: float) -> Tuple[bool, int]:
    """
    Returns:
        (是否可无损转换, E8M0指数值)
    """
    if x == 0:
        return True, 0  # 0在E8M0中表示为指数0
    
    
    # 计算指数
    exponent = math.floor(math.log2(abs(x))) + 127  # 加上偏置
    
    if is_power_of_two(x):
        return True, exponent
    else:
        return False, exponent


def analyze_scale_tensor(tensor_data: np.ndarray) -> dict:
    """
    分析scale张量
    Args:
        tensor_data: scale张量的numpy数组
    Returns:
        分析结果字典
    """
    total_elements = tensor_data.size
    
    # 统计信息
    lossless_count = 0
    lossy_count = 0
    zero_count = 0
    
    # 存储详细信息
    lossless_values = []
    lossy_values = []
    
    # 指数分布统计
    exponent_distribution = {}
    
    # 遍历所有元素
    flat_data = tensor_data.flatten()
    
    for i, value in enumerate(flat_data):
        if value == 0:
            zero_count += 1
            lossless_count += 1  # 0可以无损表示
            exponent = 0
            exponent_distribution[exponent] = exponent_distribution.get(exponent, 0) + 1
            continue
        
        # 检查是否可以无损转换为E8M0
        is_lossless, exponent = fp32_to_e8m0(value)
        
        # 更新指数分布
        exponent_distribution[exponent] = exponent_distribution.get(exponent, 0) + 1
        
        if is_lossless:
            lossless_count += 1
            lossless_values.append((i, value, exponent))
        else:
            lossy_count += 1
            lossy_values.append((i, value, exponent))
    
    # 计算百分比
    lossless_percent = (lossless_count / total_elements) * 100
    lossy_percent = (lossy_count / total_elements) * 100
    zero_percent = (zero_count / total_elements) * 100
    
    # 值范围统计
    min_value = float(np.min(flat_data))
    max_value = float(np.max(flat_data))
    mean_value = float(np.mean(flat_data))
    std_value = float(np.std(flat_data))
    
    return {
        "total_elements": total_elements,
        "lossless_count": lossless_count,
        "lossy_count": lossy_count,
        "zero_count": zero_count,
        "lossless_percent": lossless_percent,
        "lossy_percent": lossy_percent,
        "zero_percent": zero_percent,
        "min_value": min_value,
        "max_value": max_value,
        "mean_value": mean_value,
        "std_value": std_value,
        "exponent_distribution": exponent_distribution,
        "lossless_values": lossless_values[:10],  # 只保留前10个作为示例
        "lossy_values": lossy_values[:10],        # 只保留前10个作为示例
        "shape": tensor_data.shape
    }


def print_analysis_results(results: dict):
    print("=" * 80)
    print("SCALE张量分析报告")
    print()
    
    print("E8M0无损转换统计:")
    print(f"  可无损转换: {results['lossless_count']:,} ({results['lossless_percent']:.2f}%)")
    print(f"  有损转换: {results['lossy_count']:,} ({results['lossy_percent']:.2f}%)")
    print(f"  零值数量: {results['zero_count']:,} ({results['zero_percent']:.2f}%)")
    print()
    
    print("值范围统计:")
    print(f"  最小值: {results['min_value']:.6e}")
    print(f"  最大值: {results['max_value']:.6e}")
    print(f"  平均值: {results['mean_value']:.6e}")
    print(f"  标准差: {results['std_value']:.6e}")
    print()
    
    # 打印指数分布（前10个最常见的指数）
    print("指数分布（前10个最常见的指数）:")
    sorted_exponents = sorted(results['exponent_distribution'].items(), 
                             key=lambda x: x[1], reverse=True)[:10]
    for exponent, count in sorted_exponents:
        percent = (count / results['total_elements']) * 100
        # 将存储的指数转换为实际值
        actual_exponent = exponent - 127 if exponent != 0 else 0
        actual_value = 2 ** actual_exponent if exponent != 0 else 0
        print(f"  指数{exponent:3d} (2^{actual_exponent:3d} = {actual_value:10.6e}): {count:6d} 个 ({percent:.2f}%)")
    print()
    
    # 打印示例值
    if results['lossless_values']:
        print("可无损转换的示例值（前10个）:")
        for idx, value, exponent in results['lossless_values']:
            actual_exponent = exponent - 127 if exponent != 0 else 0
            print(f"  索引{idx:6d}: {value:.6e} -> 2^{actual_exponent} (指数{exponent})")
        print()
    
    if results['lossy_values']:
        print("需要有损转换的示例值（前10个）:")
        for idx, value, exponent in results['lossy_values']:
            actual_exponent = exponent - 127 if exponent != 0 else 0
            approx_value = 2 ** actual_exponent if exponent != 0 else 0
            error = abs(value - approx_value) / abs(value) * 100
            print(f"  索引{idx:6d}: {value:.6e} -> 近似 {approx_value:.6e} (误差 {error:.2f}%)")
    
    print("=" * 80)


def compute_min_max_of_all_scale(model_path, index_path):
    weight_map = load_weight_map(index_path)
    gate_proj_min_map = {}
    up_proj_min_map = {}
    down_proj_min_map = {}

    gate_proj_max_map = {}
    up_proj_max_map = {}
    down_proj_max_map = {}

    for weight_key, value in weight_map.items():

        if "scale_inv" in weight_key:
            safe_tensor_file_name = os.path.join(model_path, value)
            quant_weight_key = weight_key.split("_scale_inv")[0]
            with safe_open(safe_tensor_file_name, framework="pt") as f:
                scale_value = f.get_slice(weight_key)
                tensor_data = scale_value[:].numpy()
                moe_idx = int(weight_key.split(".")[2])
                if "gate" in weight_key:
                    gate_proj_min_map[moe_idx] = tensor_data.min()
                    gate_proj_max_map[moe_idx] = tensor_data.max()
                elif "up" in weight_key:
                    up_proj_min_map[moe_idx] = tensor_data.min()
                    up_proj_max_map[moe_idx] = tensor_data.max()
                elif "down" in weight_key:
                    down_proj_min_map[moe_idx] = tensor_data.min()
                    down_proj_max_map[moe_idx] = tensor_data.max()
    

    plot_layer_values_with_statistics(gate_proj_min_map, up_proj_min_map, down_proj_min_map,
                                     dict1_label="gate_proj", dict2_label="up_proj", dict3_label="down_proj",
                                     save_path="./a.jpg")



# step 3-5 路径配置
step3p5_model_path = "/data/models/Step-3.5-Flash-FP8"
index_json = "/data/models/Step-3.5-Flash-FP8/model.safetensors.index.json"

# step 3-5 mxfp8量化

# filename = "/data/models/Step-3.5-Flash-FP8/model-00003.safetensors"
# scale_key = "model.layers.3.moe.up_proj.weight_scale_inv"
# weight_key = "model.layers.3.moe.up_proj.weight"

# minimax attention 量化
# scale_key = "model.layers.1.self_attn.q_proj.weight_scale_inv"
# weight_key = "model.layers.1.self_attn.q_proj.weight"
# filename = "/home/yejiajun/models/minimax2_5/model-00002-of-00126.safetensors"


# minimax moe 量化
# scale_key = "model.layers.1.block_sparse_moe.experts.1.w1.weight_scale_inv"
# weight_key = "model.layers.1.block_sparse_moe.experts.1.w1.weight"
# filename = "/home/yejiajun/models/minimax2_5/model-00002-of-00126.safetensors"

compute_min_max_of_all_scale(step3p5_model_path, index_json)
exit()

print(f"权重所在文件: {filename}")

try:

    with safe_open(filename, framework="pt") as f:
        tensor_weight = f.get_slice(weight_key)
        # print("-"*100)
        # print("-"*100)
        print(f"Weight tensor Shape: {tensor_weight.get_shape()}")
        print(f"Weight tensor Dtype: {tensor_weight.get_dtype()}")
        print()
        # breakpoint()
        scale_slice = f.get_slice(scale_key)
        print(f"Scale tensor Shape: {scale_slice.get_shape()}")
        print(f"Scale tensor Dtype: {scale_slice.get_dtype()}")
        print(f"fp8 quantion block_size: {get_group_size(tensor_weight.get_shape(), scale_slice.get_shape())}")


        # 将张量数据加载到numpy数组中
        tensor_data = scale_slice[:].numpy() if hasattr(scale_slice, '__getitem__') else scale_slice.numpy()
        print("正在分析scale张量...")
        analysis_results = analyze_scale_tensor(tensor_data)
        
        # print_analysis_results(analysis_results)
        
        del tensor_data
        del scale_slice
        del tensor_weight

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
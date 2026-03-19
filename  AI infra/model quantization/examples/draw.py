import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List


def plot_layer_values(dict1: Dict[int, float], dict2: Dict[int, float], dict3: Dict[int, float],
                     dict1_label: str = "Dict1", dict2_label: str = "Dict2", dict3_label: str = "Dict3",
                     title: str = "FP8 Per-block Quant scale Values Comparison", xlabel: str = "Decoder layer Index", ylabel: str = "Value",
                     save_path: str = None, show_plot: bool = False):
    """
    根据decoder_layer_idx递增地将gate up down 的moe scale的value绘制在一张走势图中

    Args:
        title: 图表标题
        xlabel: x轴标签
        ylabel: y轴标签
        save_path: 图片保存路径，如果为None则不保存
        show_plot: 是否显示图片（在Docker中通常为False）
    """
    all_keys = sorted(set(dict1.keys()) | set(dict2.keys()) | set(dict3.keys()))
    
    values1 = [dict1.get(key, None) for key in all_keys]
    values2 = [dict2.get(key, None) for key in all_keys]
    values3 = [dict3.get(key, None) for key in all_keys]
    
    plt.figure(figsize=(12, 6))
    
    line1, = plt.plot(all_keys, values1, 'b-o', label=dict1_label, linewidth=2, markersize=6)
    line2, = plt.plot(all_keys, values2, 'r-s', label=dict2_label, linewidth=2, markersize=6)
    line3, = plt.plot(all_keys, values3, 'g-^', label=dict3_label, linewidth=2, markersize=6)

    plt.title(title, fontsize=14, fontweight='bold')
    plt.xlabel(xlabel, fontsize=12)
    plt.ylabel(ylabel, fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.legend(fontsize=10)
    
    plt.xticks(all_keys)
    
    # 自动调整y轴范围
    all_values = [v for v in values1 + values2 + values3 if v is not None]
    if all_values:
        min_val = min(all_values)
        max_val = max(all_values)
        margin = (max_val - min_val) * 0.1
        plt.ylim(min_val - margin, max_val + margin)
    
    plt.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)

    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"图片已保存到: {save_path}")
    
    if show_plot:
        plt.show()
    else:
        plt.close()


def plot_layer_values_with_statistics(dict1: Dict[int, float], dict2: Dict[int, float], dict3: Dict[int, float],
                                     dict1_label: str = "Dict1", dict2_label: str = "Dict2", dict3_label: str = "Dict3",
                                     save_path: str = None, show_plot: bool = False):
    """
    绘制三个字典的value走势图，并显示统计信息
    
    Args:
        dict1: 第一个字典，格式为{layer_idx: value}
        dict2: 第二个字典，格式为{layer_idx: value}
        dict3: 第三个字典，格式为{layer_idx: value}
        dict1_label: 第一个字典在图例中的标签
        dict2_label: 第二个字典在图例中的标签
        dict3_label: 第三个字典在图例中的标签
        save_path: 图片保存路径，如果为None则不保存
        show_plot: 是否显示图片（在Docker中通常为False）
    """
    # 计算统计信息
    def get_stats(d: Dict[int, float], label: str):
        values = list(d.values())
        return {
            'label': label,
            'mean': np.mean(values),
            'std': np.std(values),
            'min': np.min(values),
            'max': np.max(values),
            'count': len(values)
        }
    
    stats1 = get_stats(dict1, dict1_label)
    stats2 = get_stats(dict2, dict2_label)
    stats3 = get_stats(dict3, dict3_label)
    
    print("=" * 60)
    print("统计信息:")
    print("=" * 60)
    for stats in [stats1, stats2, stats3]:
        print(f"{stats['label']}:")
        print(f"  数据点数量: {stats['count']}")
        print(f"  平均值: {stats['mean']:.6f}")
        print(f"  标准差: {stats['std']:.6f}")
        print(f"  最小值: {stats['min']:.6f}")
        print(f"  最大值: {stats['max']:.6f}")
        print()
    
    plot_layer_values(dict1, dict2, dict3, dict1_label, dict2_label, dict3_label,
                     title=f"FP8 Per-block Quant scale Values Comparison",
                     save_path=save_path, show_plot=show_plot)



def example_usage():
    """
    示例：如何使用这个绘图函数
    """
    # 创建示例数据
    dict1 = {i: np.random.randn() * 0.1 + i * 0.05 for i in range(1, 21)}
    dict2 = {i: np.random.randn() * 0.2 + i * 0.03 for i in range(1, 21)}
    dict3 = {i: np.random.randn() * 0.15 + i * 0.04 for i in range(1, 21)}
    
    # 绘制图表
    plot_layer_values_with_statistics(
        dict1, dict2, dict3,
        dict1_label="Model A",
        dict2_label="Model B", 
        dict3_label="Model C"
    )

if __name__ == "__main__":
    # 运行示例
    example_usage()
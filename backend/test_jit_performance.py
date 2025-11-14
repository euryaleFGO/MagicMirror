#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
JIT 编译性能对比测试脚本

测试使用 JIT 和不使用 JIT 的 TTS 推理性能差异

使用方法:
    python test_jit_performance.py
"""

import os
import sys
import time
import statistics

# 添加路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COSYVOICE_ROOT = os.path.join(BASE_DIR, "Cosy")
MATCHA_TTS_PATH = os.path.join(COSYVOICE_ROOT, "third_party", "Matcha-TTS")
for p in [COSYVOICE_ROOT, MATCHA_TTS_PATH]:
    if p not in sys.path:
        sys.path.append(p)

# 导入 TTS 模块
from TTS import CosyvoiceRealTimeTTS

# 测试文本（不同长度）
TEST_TEXTS = [
    "你好，这是一个短文本测试。",  # 短文本
    "这是一个中等长度的测试文本，用于测试 JIT 编译的性能提升效果。我们将对比使用 JIT 和不使用 JIT 的推理速度差异。",  # 中等文本
    "这是一个较长的测试文本，用于全面评估 JIT 编译对 TTS 推理性能的影响。我们将进行多次测试以确保结果的准确性。通过对比不同长度的文本，我们可以更好地了解 JIT 编译在不同场景下的性能表现。这个测试将帮助我们决定是否应该在生产环境中启用 JIT 编译优化。",  # 长文本
]

# 测试次数
NUM_RUNS = 5


def test_tts_performance(tts_engine, text, num_runs=5):
    """
    测试 TTS 推理性能
    
    Args:
        tts_engine: TTS 引擎实例
        text: 测试文本
        num_runs: 测试次数
    
    Returns:
        dict: 包含平均时间、最小时间、最大时间、标准差等统计信息
    """
    times = []
    
    print(f"  测试文本长度: {len(text)} 字符")
    print(f"  测试次数: {num_runs}")
    
    for i in range(num_runs):
        start_time = time.time()
        
        try:
            # 执行 TTS 推理
            audio_data = tts_engine.generate_audio(text)
            
            elapsed = time.time() - start_time
            times.append(elapsed)
            
            print(f"    第 {i+1} 次: {elapsed:.3f} 秒")
            
        except Exception as e:
            print(f"    ❌ 第 {i+1} 次测试失败: {e}")
            continue
    
    if not times:
        return None
    
    return {
        'times': times,
        'mean': statistics.mean(times),
        'median': statistics.median(times),
        'min': min(times),
        'max': max(times),
        'stdev': statistics.stdev(times) if len(times) > 1 else 0,
    }


def print_statistics(stats, label):
    """
    打印统计信息
    
    Args:
        stats: 统计信息字典
        label: 标签（如 "不使用 JIT" 或 "使用 JIT"）
    """
    if stats is None:
        print(f"  {label}: 测试失败")
        return
    
    print(f"\n  {label} 统计:")
    print(f"    平均时间: {stats['mean']:.3f} 秒")
    print(f"    中位数:   {stats['median']:.3f} 秒")
    print(f"    最短时间: {stats['min']:.3f} 秒")
    print(f"    最长时间: {stats['max']:.3f} 秒")
    if stats['stdev'] > 0:
        print(f"    标准差:   {stats['stdev']:.3f} 秒")


def compare_performance(without_jit_stats, with_jit_stats):
    """
    对比性能并计算提升百分比
    
    Args:
        without_jit_stats: 不使用 JIT 的统计信息
        with_jit_stats: 使用 JIT 的统计信息
    """
    if without_jit_stats is None or with_jit_stats is None:
        print("\n  ⚠️ 无法对比：部分测试失败")
        return
    
    speedup = without_jit_stats['mean'] / with_jit_stats['mean']
    improvement = (speedup - 1) * 100
    
    print(f"\n  📊 性能对比:")
    print(f"    速度提升: {improvement:.1f}%")
    print(f"    加速比:   {speedup:.2f}x")
    print(f"    时间节省: {without_jit_stats['mean'] - with_jit_stats['mean']:.3f} 秒")


def main():
    """主测试函数"""
    print("=" * 70)
    print("JIT 编译性能对比测试")
    print("=" * 70)
    
    # 模型路径
    model_path = os.path.join(BASE_DIR, "Model", "CosyVoice2-0.5B")
    ref_audio = os.path.join(BASE_DIR, "audio", "zjj.wav")
    
    if not os.path.exists(model_path):
        print(f"❌ 错误: 模型路径不存在: {model_path}")
        return
    
    if not os.path.exists(ref_audio):
        print(f"⚠️  警告: 参考音频不存在: {ref_audio}")
        print("   将使用默认参考音频（如果模型支持）")
        ref_audio = None
    
    results = {}
    
    # 测试 1: 不使用 JIT
    print("\n" + "=" * 70)
    print("测试 1: 不使用 JIT 编译")
    print("=" * 70)
    
    try:
        print("正在初始化 TTS 引擎（不使用 JIT）...")
        tts_without_jit = CosyvoiceRealTimeTTS(model_path, ref_audio, load_jit=False)
        print("✅ TTS 引擎初始化成功（不使用 JIT）")
        
        without_jit_results = {}
        for i, text in enumerate(TEST_TEXTS, 1):
            print(f"\n--- 测试文本 {i} ---")
            stats = test_tts_performance(tts_without_jit, text, NUM_RUNS)
            without_jit_results[f'text_{i}'] = stats
            print_statistics(stats, "不使用 JIT")
        
        results['without_jit'] = without_jit_results
        
    except Exception as e:
        print(f"❌ 初始化失败（不使用 JIT）: {e}")
        import traceback
        traceback.print_exc()
        results['without_jit'] = None
    
    # 测试 2: 使用 JIT
    print("\n" + "=" * 70)
    print("测试 2: 使用 JIT 编译")
    print("=" * 70)
    
    try:
        print("正在初始化 TTS 引擎（使用 JIT）...")
        tts_with_jit = CosyvoiceRealTimeTTS(model_path, ref_audio, load_jit=True)
        print("✅ TTS 引擎初始化成功（使用 JIT）")
        
        with_jit_results = {}
        for i, text in enumerate(TEST_TEXTS, 1):
            print(f"\n--- 测试文本 {i} ---")
            stats = test_tts_performance(tts_with_jit, text, NUM_RUNS)
            with_jit_results[f'text_{i}'] = stats
            print_statistics(stats, "使用 JIT")
        
        results['with_jit'] = with_jit_results
        
    except Exception as e:
        print(f"❌ 初始化失败（使用 JIT）: {e}")
        import traceback
        traceback.print_exc()
        results['with_jit'] = None
    
    # 性能对比
    print("\n" + "=" * 70)
    print("性能对比总结")
    print("=" * 70)
    
    if results['without_jit'] and results['with_jit']:
        for i, text in enumerate(TEST_TEXTS, 1):
            key = f'text_{i}'
            without_stats = results['without_jit'].get(key)
            with_stats = results['with_jit'].get(key)
            
            if without_stats and with_stats:
                print(f"\n--- 测试文本 {i} (长度: {len(text)} 字符) ---")
                compare_performance(without_stats, with_stats)
        
        # 总体统计
        print("\n" + "-" * 70)
        print("总体性能提升:")
        
        all_without_times = []
        all_with_times = []
        
        for i in range(1, len(TEST_TEXTS) + 1):
            key = f'text_{i}'
            if results['without_jit'].get(key) and results['with_jit'].get(key):
                all_without_times.extend(results['without_jit'][key]['times'])
                all_with_times.extend(results['with_jit'][key]['times'])
        
        if all_without_times and all_with_times:
            overall_without_mean = statistics.mean(all_without_times)
            overall_with_mean = statistics.mean(all_with_times)
            overall_speedup = overall_without_mean / overall_with_mean
            overall_improvement = (overall_speedup - 1) * 100
            
            print(f"  平均速度提升: {overall_improvement:.1f}%")
            print(f"  平均加速比:   {overall_speedup:.2f}x")
            print(f"  平均时间节省: {overall_without_mean - overall_with_mean:.3f} 秒")
    else:
        print("⚠️  无法进行完整对比，部分测试失败")
    
    print("\n" + "=" * 70)
    print("测试完成")
    print("=" * 70)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
    except Exception as e:
        print(f"\n\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


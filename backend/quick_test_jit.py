#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
快速 JIT 性能测试脚本（简化版）

快速对比使用 JIT 和不使用 JIT 的性能差异

使用方法:
    python quick_test_jit.py
"""

import os
import sys
import time

# 添加路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COSYVOICE_ROOT = os.path.join(BASE_DIR, "Cosy")
MATCHA_TTS_PATH = os.path.join(COSYVOICE_ROOT, "third_party", "Matcha-TTS")
for p in [COSYVOICE_ROOT, MATCHA_TTS_PATH]:
    if p not in sys.path:
        sys.path.append(p)

from TTS import CosyvoiceRealTimeTTS

def main():
    print("=" * 60)
    print("快速 JIT 性能测试")
    print("=" * 60)
    
    # 配置
    model_path = os.path.join(BASE_DIR, "Model", "CosyVoice2-0.5B")
    ref_audio = os.path.join(BASE_DIR, "audio", "zjj.wav")
    test_text = "这是一个性能测试文本，用于对比 JIT 编译的效果。我们将测试使用 JIT 和不使用 JIT 的推理速度差异。"
    
    if not os.path.exists(model_path):
        print(f"❌ 错误: 模型路径不存在: {model_path}")
        return
    
    print(f"\n测试文本长度: {len(test_text)} 字符")
    print(f"测试文本: {test_text[:50]}...")
    
    # 测试 1: 不使用 JIT
    print("\n" + "-" * 60)
    print("测试 1: 不使用 JIT")
    print("-" * 60)
    
    try:
        print("正在初始化 TTS 引擎（不使用 JIT）...")
        tts_without_jit = CosyvoiceRealTimeTTS(model_path, ref_audio, load_jit=False)
        
        print("执行推理测试...")
        times = []
        for i in range(3):
            start = time.time()
            audio = tts_without_jit.generate_audio(test_text)
            elapsed = time.time() - start
            times.append(elapsed)
            print(f"  第 {i+1} 次: {elapsed:.3f} 秒")
        
        avg_without_jit = sum(times) / len(times)
        print(f"\n平均时间: {avg_without_jit:.3f} 秒")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 测试 2: 使用 JIT
    print("\n" + "-" * 60)
    print("测试 2: 使用 JIT")
    print("-" * 60)
    
    try:
        print("正在初始化 TTS 引擎（使用 JIT）...")
        tts_with_jit = CosyvoiceRealTimeTTS(model_path, ref_audio, load_jit=True)
        
        print("执行推理测试...")
        times = []
        for i in range(3):
            start = time.time()
            audio = tts_with_jit.generate_audio(test_text)
            elapsed = time.time() - start
            times.append(elapsed)
            print(f"  第 {i+1} 次: {elapsed:.3f} 秒")
        
        avg_with_jit = sum(times) / len(times)
        print(f"\n平均时间: {avg_with_jit:.3f} 秒")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 性能对比
    print("\n" + "=" * 60)
    print("性能对比结果")
    print("=" * 60)
    
    speedup = avg_without_jit / avg_with_jit
    improvement = (speedup - 1) * 100
    time_saved = avg_without_jit - avg_with_jit
    
    print(f"不使用 JIT: {avg_without_jit:.3f} 秒")
    print(f"使用 JIT:   {avg_with_jit:.3f} 秒")
    print(f"\n速度提升: {improvement:.1f}%")
    print(f"加速比:   {speedup:.2f}x")
    print(f"时间节省: {time_saved:.3f} 秒")
    
    if improvement > 0:
        print(f"\n✅ JIT 编译有效果！性能提升了 {improvement:.1f}%")
    else:
        print(f"\n⚠️  JIT 编译没有明显提升，可能原因：")
        print("   - JIT 模型文件不存在或未正确加载")
        print("   - 文本太短，优化效果不明显")
        print("   - GPU 利用率已经很高")
    
    print("\n" + "=" * 60)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
    except Exception as e:
        print(f"\n\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


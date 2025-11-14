#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
导出 CosyVoice2 模型的 JIT 编译版本
用于加速推理性能

使用方法:
    python export_jit_model.py
"""

import os
import sys

# 添加 CosyVoice 路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COSYVOICE_ROOT = os.path.join(BASE_DIR, "Cosy")
MATCHA_TTS_PATH = os.path.join(COSYVOICE_ROOT, "third_party", "Matcha-TTS")
for p in [COSYVOICE_ROOT, MATCHA_TTS_PATH]:
    if p not in sys.path:
        sys.path.append(p)

# 导入 CosyVoice
from cosyvoice.cli.cosyvoice import CosyVoice2
from cosyvoice.utils.file_utils import logging
import torch

def export_jit_model(model_dir):
    """
    导出 CosyVoice2 模型的 JIT 编译版本
    
    Args:
        model_dir: 模型目录路径
    """
    print(f"开始导出 JIT 模型，模型目录: {model_dir}")
    
    # 检查模型目录是否存在
    if not os.path.exists(model_dir):
        print(f"错误: 模型目录不存在: {model_dir}")
        return False
    
    # 设置 JIT 优化选项
    torch._C._jit_set_fusion_strategy([('STATIC', 1)])
    torch._C._jit_set_profiling_mode(False)
    torch._C._jit_set_profiling_executor(False)
    
    try:
        # 加载模型
        print("正在加载模型...")
        model = CosyVoice2(model_dir, load_jit=False, load_trt=False, fp16=True)
        print("模型加载成功")
        
        # 导出 flow encoder (CosyVoice2 只支持这个模块)
        print("正在导出 flow.encoder...")
        flow_encoder = model.model.flow.encoder
        
        # FP32 版本
        print("  - 导出 FP32 版本...")
        script_fp32 = torch.jit.script(flow_encoder)
        script_fp32 = torch.jit.freeze(script_fp32)
        script_fp32 = torch.jit.optimize_for_inference(script_fp32)
        fp32_path = os.path.join(model_dir, 'flow.encoder.fp32.zip')
        script_fp32.save(fp32_path)
        print(f"  - FP32 版本已保存: {fp32_path}")
        
        # FP16 版本
        print("  - 导出 FP16 版本...")
        script_fp16 = torch.jit.script(flow_encoder.half())
        script_fp16 = torch.jit.freeze(script_fp16)
        script_fp16 = torch.jit.optimize_for_inference(script_fp16)
        fp16_path = os.path.join(model_dir, 'flow.encoder.fp16.zip')
        script_fp16.save(fp16_path)
        print(f"  - FP16 版本已保存: {fp16_path}")
        
        print("✅ JIT 模型导出成功！")
        print(f"\n生成的文件:")
        print(f"  - {fp32_path}")
        print(f"  - {fp16_path}")
        print(f"\n现在可以在 TTS.py 中使用 load_jit=True 来加载 JIT 模型")
        return True
        
    except Exception as e:
        print(f"❌ 导出失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    # 默认模型路径
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    MODEL_DIR = os.path.join(BASE_DIR, "Model", "CosyVoice2-0.5B")
    
    # 如果提供了命令行参数，使用参数
    if len(sys.argv) > 1:
        MODEL_DIR = sys.argv[1]
    
    print("=" * 60)
    print("CosyVoice2 JIT 模型导出工具")
    print("=" * 60)
    print(f"模型目录: {MODEL_DIR}")
    print("=" * 60)
    
    success = export_jit_model(MODEL_DIR)
    
    if success:
        print("\n✅ 导出完成！")
        sys.exit(0)
    else:
        print("\n❌ 导出失败！")
        sys.exit(1)


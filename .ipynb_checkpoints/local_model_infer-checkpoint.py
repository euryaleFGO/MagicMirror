from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
import torch
import time
from typing import List, Dict, Generator

# 4bit量化配置（适配大模型显存需求）
quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16
)

class LocalModelInfer:
    def __init__(self, model_path: str, system_message: str = "", 
                 device: str = None, load_in_4bit: bool = True):
        self.model_path = model_path
        self.system_message = system_message  # Qwen的system prompt
        self.conversation_history = []  # 对话历史缓存
        
        # 自动选择设备
        self.device = device if device else ("cuda" if torch.cuda.is_available() else "cpu")
        
        # 加载tokenizer和模型
        print(f"正在加载Qwen模型: {model_path} 到 {self.device}...")
        start_time = time.time()
        
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_path,
            trust_remote_code=True  # 必须开启，Qwen需要自定义tokenizer
        )
        self.tokenizer.pad_token = self.tokenizer.eos_token  # 设置pad token
        
        # 模型加载参数
        model_kwargs = {
            "device_map": "auto",
            "trust_remote_code": True,  # 必须开启，Qwen需要自定义模型代码
            "torch_dtype": torch.float16 if torch.cuda.is_available() else torch.float32
        }
        if load_in_4bit and torch.cuda.is_available():
            model_kwargs["quantization_config"] = quantization_config
        
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path,** model_kwargs
        )
        self.model.eval()  # 推理模式（关闭dropout等训练相关层）
        print(f"模型加载完成，耗时 {time.time() - start_time:.2f} 秒")

    def _build_prompt(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """构建Qwen格式的对话历史（包含system prompt）"""
        full_messages = []
        # 添加system prompt（如果有）
        if self.system_message:
            full_messages.append({"role": "system", "content": self.system_message})
        # 合并历史对话和新消息
        full_messages.extend(self.conversation_history + messages)
        return full_messages

    def infer(self, messages: List[Dict[str, str]], stream: bool = True, 
              temperature: float = 0.7, top_p: float = 0.95) -> Generator[str, None, None] or str:
        """Qwen模型推理（支持流式输出）"""
        # 添加用户消息到历史记录
        self.conversation_history.extend(messages)
        
        # 构建Qwen格式的对话
        prompt = self._build_prompt(messages)
        
        # 编码输入
        inputs = self.tokenizer.apply_chat_template(
            prompt,
            tokenize=True,
            return_tensors="pt",
            add_generation_prompt=True  # 自动添加生成提示（如"Assistant:"）
        ).to(self.device)
        
        # 生成配置
        generate_kwargs = {
            "temperature": temperature,
            "top_p": top_p,
            "do_sample": True,
            "max_new_tokens": 1024,
            "pad_token_id": self.tokenizer.pad_token_id,
            "eos_token_id": self.tokenizer.eos_token_id,
        }
        
        if stream:
            # 流式生成
            generated_text = ""
            for output in self.model.generate(inputs, **generate_kwargs):
                # 解码并过滤已有内容
                decoded = self.tokenizer.decode(output, skip_special_tokens=True)
                new_text = decoded[len(generated_text):].strip()
                if new_text:
                    generated_text = decoded
                    yield new_text
            return generated_text
        else:
            # 一次性生成
            outputs = self.model.generate(inputs,** generate_kwargs)
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            return response

    def add_assistant_response(self, content: str):
        """添加助手回复到历史"""
        self.conversation_history.append({"role": "assistant", "content": content})
    
    def clear_history(self):
        """清空对话历史"""
        self.conversation_history = []
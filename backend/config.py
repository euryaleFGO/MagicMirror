import os
from dotenv import load_dotenv

#加载环境变量（指定.env文件路径）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(BASE_DIR, '.env')

# 读取.env文件并去除BOM
if os.path.exists(env_path):
    with open(env_path, 'r', encoding='utf-8-sig') as f:  # utf-8-sig 自动去除BOM
        content = f.read()
    # 重新写入文件（去除BOM）
    with open(env_path, 'w', encoding='utf-8') as f:
        f.write(content)

load_dotenv(dotenv_path=env_path)

#获取密钥
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
#获取基础URL
BASE_URL = os.getenv('BASE_URL')
#获取模型名称
MODEL = os.getenv('MODEL')

# 验证必要的配置
if not DEEPSEEK_API_KEY:
    print("警告：DEEPSEEK_API_KEY 未设置，请检查 .env 文件")
if not BASE_URL:
    print("警告：BASE_URL 未设置，请检查 .env 文件")
if not MODEL:
    print("警告：MODEL 未设置，请检查 .env 文件")

# MySQL数据库配置
MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
MYSQL_PORT = int(os.getenv('MYSQL_PORT', 3306))
MYSQL_USER = os.getenv('MYSQL_USER', 'root')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'magicmirror')
MYSQL_CHARSET = os.getenv('MYSQL_CHARSET', 'utf8mb4')
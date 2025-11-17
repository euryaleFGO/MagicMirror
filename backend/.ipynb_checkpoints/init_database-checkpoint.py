#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MySQL数据库初始化脚本
用于创建和初始化数据库表结构
"""
import os
import sys
import pymysql

# 获取当前文件所在目录（backend目录）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 导入配置
sys.path.insert(0, BASE_DIR)
from config import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE, MYSQL_CHARSET

def get_db_connection(use_database=True):
    """获取MySQL数据库连接"""
    try:
        if use_database:
            conn = pymysql.connect(
                host=MYSQL_HOST,
                port=MYSQL_PORT,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD,
                database=MYSQL_DATABASE,
                charset=MYSQL_CHARSET,
                cursorclass=pymysql.cursors.DictCursor
            )
        else:
            # 连接到MySQL服务器（不指定数据库）
            conn = pymysql.connect(
                host=MYSQL_HOST,
                port=MYSQL_PORT,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD,
                charset=MYSQL_CHARSET
            )
        return conn
    except pymysql.Error as e:
        print(f"✗ 数据库连接失败: {e}")
        raise

def init_database():
    """初始化数据库，创建所有必要的表"""
    print(f"数据库服务器: {MYSQL_HOST}:{MYSQL_PORT}")
    print(f"数据库名称: {MYSQL_DATABASE}")
    print(f"字符集: {MYSQL_CHARSET}")
    print()
    
    try:
        # 先连接到MySQL服务器（不指定数据库）
        conn = get_db_connection(use_database=False)
        cursor = conn.cursor()
        
        # 创建数据库（如果不存在）
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_DATABASE} CHARACTER SET {MYSQL_CHARSET} COLLATE {MYSQL_CHARSET}_unicode_ci")
        conn.commit()
        print(f"✓ 数据库 {MYSQL_DATABASE} 创建成功或已存在")
        cursor.close()
        conn.close()
        
        # 连接到指定数据库并创建表
        conn = get_db_connection(use_database=True)
        cursor = conn.cursor()
        
        # 创建用户表
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci''')
        
        print("✓ 用户表创建成功或已存在")
        
        # 检查表是否存在
        cursor.execute("SHOW TABLES LIKE 'users'")
        if cursor.fetchone():
            print("✓ 数据库表验证成功")
            
            # 显示表结构
            cursor.execute("DESCRIBE users")
            columns = cursor.fetchall()
            print("\n表结构:")
            print("-" * 60)
            print(f"{'字段名':<20} {'类型':<20} {'允许NULL':<10} {'键':<10}")
            print("-" * 60)
            for col in columns:
                null_str = "YES" if col['Null'] == 'YES' else "NO"
                key_str = col['Key'] if col['Key'] else ""
                print(f"{col['Field']:<20} {col['Type']:<20} {null_str:<10} {key_str:<10}")
            print("-" * 60)
        
        conn.commit()
        print(f"\n✓ 数据库初始化完成")
        
        # 显示数据库信息
        cursor.execute("SELECT COUNT(*) as count FROM users")
        result = cursor.fetchone()
        user_count = result['count']
        print(f"✓ 当前用户数量: {user_count}")
        
        cursor.close()
        conn.close()
        
    except pymysql.Error as e:
        print(f"✗ 数据库初始化失败: {e}")
        return False
    
    return True

def verify_database():
    """验证数据库是否正常"""
    try:
        conn = get_db_connection(use_database=True)
        cursor = conn.cursor()
        
        # 检查表是否存在
        cursor.execute("SHOW TABLES LIKE 'users'")
        if not cursor.fetchone():
            print("✗ 用户表不存在")
            return False
        
        # 检查表结构
        cursor.execute("DESCRIBE users")
        columns = cursor.fetchall()
        column_names = [col['Field'] for col in columns]
        
        required_columns = ['id', 'username', 'password']
        for col in required_columns:
            if col not in column_names:
                print(f"✗ 缺少必需的列: {col}")
                return False
        
        print("✓ 数据库验证通过")
        return True
        
    except pymysql.Error as e:
        print(f"✗ 数据库验证失败: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    print("=" * 60)
    print("MySQL数据库初始化脚本")
    print("=" * 60)
    print()
    
    # 设置UTF-8编码
    if sys.stdout.encoding != 'utf-8':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except:
            pass
    
    # 初始化数据库
    if init_database():
        print()
        print("=" * 60)
        print("验证数据库...")
        print("=" * 60)
        verify_database()
        print()
        print("数据库部署完成！")
    else:
        print()
        print("数据库部署失败，请检查错误信息。")
        sys.exit(1)

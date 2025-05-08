# 测试 PyJWT 安装
try:
    import jwt
    print(f"JWT 导入成功，版本：{jwt.__version__}")
except ImportError as e:
    print(f"JWT 导入失败：{e}")
    print("尝试安装 PyJWT...")
    import subprocess
    subprocess.run(["pip", "install", "PyJWT"], check=True)
    try:
        import jwt
        print(f"安装并导入成功，版本：{jwt.__version__}")
    except ImportError as e:
        print(f"安装后仍然无法导入：{e}")

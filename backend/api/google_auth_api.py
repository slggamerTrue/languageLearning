from fastapi import APIRouter, HTTPException, Depends, Body
from typing import Dict, Any
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 直接导入
from services.google_auth import GoogleAuthService

router = APIRouter()

@router.post("/get-google-user-info")
async def get_google_user_info(request_data: dict = Body(...)):
    """
    验证Google令牌并返回用户信息
    """
    try:
        # 从请求中提取令牌
        token = request_data.get("access_token")
        redirect_uri = request_data.get("redirect_uri")
        if not token:
            raise ValueError("请求中缺少access_token参数")
        
        print(f"[INFO] 收到令牌，尝试验证")
        
        # 初始化Google验证服务
        google_auth = GoogleAuthService()
        
        # 如果是访问令牌，直接使用它获取用户信息
        if token.startswith("ya29."):
            user_info = await google_auth.get_user_info_from_access_token(token, redirect_uri)
        else:
            # 验证令牌并获取用户信息
            user_info = await google_auth.verify_token(token, redirect_uri)
        
        # 返回用户信息
        return user_info
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户信息过程中出错: {str(e)}")

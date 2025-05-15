import os
import json
import aiohttp
from typing import Dict, Any, Optional
from fastapi import HTTPException, status

class GoogleAuthService:
    """
    简单的Google OAuth服务，用于将授权码交换为访问令牌并获取用户信息
    """
    
    def __init__(self):
        # 获取Google Client ID和Client Secret环境变量
        self.client_id = os.getenv("GOOGLE_CLIENT_ID")
        self.client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        self.userinfo_endpoint = "https://www.googleapis.com/oauth2/v3/userinfo"
        
        if not self.client_id:
            print("[WARNING] GOOGLE_CLIENT_ID环境变量未设置")
        if not self.client_secret:
            print("[WARNING] GOOGLE_CLIENT_SECRET环境变量未设置")
    
    async def verify_token(self, token: str, redirect_uri: Optional[str] = None) -> Dict[str, Any]:
        """
        验证Google令牌并提取用户信息
        主要处理授权码，将其交换为访问令牌并获取用户信息
        """
        try:
            print(f"[DEBUG] 尝试验证令牌，令牌: {token[:10]}...")
            
            # 如果是访问令牌，直接使用它获取用户信息
            if token.startswith("ya29."):
                return await self.get_user_info_from_access_token(token)
            
            # 如果是授权码，交换为访问令牌
            if token.startswith("4/0A"):
                print(f"[DEBUG] 尝试将授权码交换为访问令牌")
                access_token = await self.exchange_code_for_token(token, redirect_uri)
                return await self.get_user_info_from_access_token(access_token)
            
            # 如果不是上述格式，尝试作为访问令牌使用
            return await self.get_user_info_from_access_token(token)
            
        except Exception as e:
            print(f"[ERROR] 验证过程中出错: {str(e)}")
            raise ValueError(f"验证过程中出错: {str(e)}")

    async def get_user_info_from_access_token(self, access_token: str) -> Dict[str, Any]:
        """
        使用访问令牌获取用户信息
        """
        try:
            print(f"[DEBUG] 尝试使用访问令牌获取用户信息，令牌: {access_token[:10]}...")
            
            # 使用访问令牌调用Google UserInfo API
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {access_token}"}
                async with session.get(self.userinfo_endpoint, headers=headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        print(f"[ERROR] 获取用户信息失败: {error_text}")
                        raise ValueError(f"获取用户信息失败: HTTP {response.status} - {error_text}")
                    
                    user_data = await response.json()
                    print(f"[DEBUG] 成功获取用户信息")
                    
                    # 提取用户信息
                    user_info = {
                        "email": user_data.get("email"),
                        "name": user_data.get("name"),
                        "picture": user_data.get("picture"),
                        "locale": user_data.get("locale"),
                        "family_name": user_data.get("family_name"),
                        "given_name": user_data.get("given_name")
                    }
                    
                    return user_info
        except Exception as e:
            print(f"[ERROR] 获取用户信息过程中出错: {str(e)}")
            raise ValueError(f"获取用户信息过程中出错: {str(e)}")
            
    async def exchange_code_for_token(self, code: str, redirect_uri: Optional[str] = None) -> str:
        """
        将授权码交换为访问令牌
        """
        try:
            print(f"[DEBUG] 尝试将授权码交换为访问令牌，授权码: {code[:10]}...")
            
            # 构建交换请求
            token_url = "https://oauth2.googleapis.com/token"
            
            # 注意：如果令牌已经是访问令牌格式，直接返回
            if code.startswith("ya29."):
                print(f"[DEBUG] 检测到访问令牌格式，直接返回")
                return code
                
            payload = {
                "code": code,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code"
            }
            
            # 发送交换请求
            async with aiohttp.ClientSession() as session:
                async with session.post(token_url, data=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        print(f"[ERROR] 交换令牌失败: {error_text}")
                        raise ValueError(f"交换令牌失败: HTTP {response.status} - {error_text}")
                    
                    token_data = await response.json()
                    access_token = token_data.get("access_token")
                    
                    if not access_token:
                        print(f"[ERROR] 交换响应中没有访问令牌: {token_data}")
                        raise ValueError("交换响应中没有访问令牌")
                    
                    print(f"[DEBUG] 成功交换授权码为访问令牌")
                    return access_token
        except Exception as e:
            print(f"[ERROR] 交换令牌过程中出错: {str(e)}")
            raise ValueError(f"交换令牌过程中出错: {str(e)}")

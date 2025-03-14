import aiohttp
import json
from typing import List, Dict
import os

class LLMService:
    def __init__(self):
        self.base_url = "https://llm.promptai.cn/pk/api/chat"
        self.model = "pkqwen2.5-32b:latest"
        self.headers = {
            "Content-Type": "application/json",
        }

    async def chat_completion(self, messages: List[Dict]) -> Dict:
        """
        调用 Ollama API 进行对话
        """
        try:
            ssl_context = aiohttp.TCPConnector(verify_ssl=False)
            async with aiohttp.ClientSession(connector=ssl_context) as session:
                payload = {
                    "model": self.model,
                    "messages": messages,
                    "stream": False
                }
                
                async with session.post(
                    self.base_url,
                    headers=self.headers,
                    json=payload
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"API call failed: {error_text}")
                    
                    result = await response.json()
                    return {"role": "assistant", "content": result["message"]["content"]}

        except Exception as e:
            raise Exception(f"Chat completion failed: {str(e)}")

    async def structured_chat(self, messages: List[Dict], output_format: str) -> Dict:
        """
        进行结构化输出的对话
        """
        # 添加格式要求到系统提示
        if output_format is not None:
            format_message = {
                "role": "system",
                "content": f'''
    输出格式为json，具体如下：
    {output_format}

    你必须遵守以下规则：
    1. 只输出纯 JSON 数据
    2. 不要包含任何注释或说明
    3. 不要使用单引号，只使用双引号
    4. 数组和对象的最后一个元素后不要加逗号
    5. 确保输出可以直接被 JSON.parse() 解析

    示例：
    {{
        "key": "value",
        "array": [
            "item1",
            "item2"
        ]
    }}
    或
    [
        {{
            "key": "value",
            "array": ["item1", "item2"]
        }}
    ]'''
            }
            
            messages = messages + [format_message]
        
        try:

            response = await self.chat_completion(messages)
            content = response["content"]
            
            print("\n=== API 响应内容 ===\n")
            print(content)
            print()
            
            # 删除可能的代码块标记和空行
            content = content.replace('```json', '').replace('```', '')
            
            # 处理 <ASSESSMENT_COMPLETE> 标记
            if "<ASSESSMENT_COMPLETE>" in content:
                # 如果标记在 JSON 之前，直接删除它
                content = content.replace("<ASSESSMENT_COMPLETE>", "")
            
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            content = '\n'.join(lines)
            
           # print("\n=== 清理后的内容 ===\n")
            #print(content)
            #print()
            
            # 先检查是否是数组
            array_start = content.find('[')
            object_start = content.find('{')
            
            # 尝试解析 JSON
            try:
                if array_start != -1 and (object_start == -1 or array_start < object_start):
                    start = array_start
                elif object_start != -1:
                    start = object_start
                else:
                    raise Exception("No valid JSON found in response")
                # 找到结束的花括号或方括号
                end = -1
                stack = []
                in_string = False
                escape = False
                
                for i, char in enumerate(content[start:]):
                    if char == '\\' and not escape:
                        escape = True
                        continue
                    
                    if char == '"' and not escape:
                        in_string = not in_string
                    
                    if not in_string:
                        if char in '{[':
                            stack.append(char)
                            #print(f"Push: {char}, Stack: {stack}")
                        elif char in '}]':
                            if not stack:
                                print(f"Error: Found closing {char} but stack is empty")
                                break
                            if (char == '}' and stack[-1] == '{') or (char == ']' and stack[-1] == '['):
                                stack.pop()
                                #print(f"Pop: {char}, Stack: {stack}")
                                if not stack:  # 找到匹配的结束括号
                                    end = i + 1
                                    #print(f"Found matching end at position {end}")
                                    break
                            else:
                                print(f"Error: Mismatched brackets. Found {char} but expected matching for {stack[-1]}")
                    
                    escape = False
                
                if end == -1:
                    raise Exception("Could not find matching closing bracket")
                
                json_str = content[start:start + end]
                #print("\n=== 提取的 JSON 字符串 ===\n")
                #print(json_str)
                #print()
                
                result = json.loads(json_str)
                # 如果结果是字符串，尝试解析为 JSON
                if isinstance(result, str):
                    result = json.loads(result)
                
                return result
            except Exception as e:
                print(f"\n=== JSON 解析错误 ===\n")
                print(f"Error: {str(e)}")
                print()
                return {"content": content}
            
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse JSON response: {str(e)}\nContent: {content}")
        except Exception as e:
            raise Exception(f"Structured chat failed: {str(e)}")

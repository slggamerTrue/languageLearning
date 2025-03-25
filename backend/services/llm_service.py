import aiohttp
import json
from typing import List, Dict, Optional
import os

class LLMService:
    def __init__(self):
        #self.base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
        #self.model = "qwen-plus"
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
        self.model = "gemini-2.0-flash"
        #self.base_url = "https://llm.promptai.cn/pk/api/chat"
        #self.model = "pkqwen2.5-32b:latest"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {os.getenv('PROMPTAI_API_KEY')}"
        }

    async def chat_completion(self, messages: List[Dict], model: Optional[str] = None) -> Dict:
        """
        调用 Ollama API 进行对话
        """
        try:
            ssl_context = aiohttp.TCPConnector(verify_ssl=False)
            async with aiohttp.ClientSession(connector=ssl_context) as session:
                payload = {
                    "model": model or self.model,
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
                    return {"role": "assistant", "content": result["choices"][0]["message"]["content"]}
                    #return {"role": "assistant", "content": result["message"]["content"]}

        except Exception as e:
            raise Exception(f"Chat completion failed: {str(e)}")

    async def structured_chat(self, messages: List[Dict], output_format: Optional[str] = None, model: Optional[str] = None) -> Dict:
        """
        进行结构化输出的对话
        """
        try:

            response = await self.chat_completion(messages, model)
            content = response["content"]
            
            print("\n=== API 响应内容 ===\n")
            print(content)
            print()
            
            # 删除可能的代码块标记和空行
            content = content.replace('```json', '').replace('```', '')
            
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
                
                # 解析失败后，尝试重新生成
                if output_format is not None:
                    print("尝试重新生成符合格式要求的响应...")
                    
                    # 创建一个更明确的格式要求
                    retry_message = {
                        "role": "system",
                        "content": f"之前的响应无法解析为有效的JSON。请严格按照以下格式要求重新生成响应，确保输出是有效的JSON格式，不要添加任何额外的文本、代码块标记或说明：\n\n{output_format}"
                    }
                    
                    # 添加重试消息
                    retry_messages = [messages[0]] + [{"role": "user", "content": "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in messages[1:]])}]
                    
                    try:
                        # 重新调用API
                        retry_response = await self.chat_completion(retry_messages, model)
                        retry_content = retry_response["content"]
                        
                        print("\n=== 重试生成的内容 ===\n")
                        print(retry_content)
                        print()
                        
                        # 清理内容
                        retry_content = retry_content.replace('```json', '').replace('```', '')
                        lines = [line.strip() for line in retry_content.split('\n') if line.strip()]
                        retry_content = '\n'.join(lines)
                        
                        # 尝试解析JSON
                        array_start = retry_content.find('[')
                        object_start = retry_content.find('{')
                        
                        if array_start != -1 and (object_start == -1 or array_start < object_start):
                            start = array_start
                        elif object_start != -1:
                            start = object_start
                        else:
                            raise Exception("No valid JSON found in retry response")
                            
                        # 找到结束的花括号或方括号
                        end = -1
                        stack = []
                        in_string = False
                        escape = False
                        
                        for i, char in enumerate(retry_content[start:]):
                            if char == '\\' and not escape:
                                escape = True
                                continue
                            
                            if char == '"' and not escape:
                                in_string = not in_string
                            
                            if not in_string:
                                if char in '{[':
                                    stack.append(char)
                                elif char in '}]':
                                    if not stack:
                                        print(f"Error: Found closing {char} but stack is empty")
                                        break
                                    if (char == '}' and stack[-1] == '{') or (char == ']' and stack[-1] == '['):
                                        stack.pop()
                                        if not stack:  # 找到匹配的结束括号
                                            end = i + 1
                                            break
                                    else:
                                        print(f"Error: Mismatched brackets. Found {char} but expected matching for {stack[-1]}")
                            
                            escape = False
                        
                        if end == -1:
                            raise Exception("Could not find matching closing bracket in retry response")
                        
                        json_str = retry_content[start:start + end]
                        retry_result = json.loads(json_str)
                        
                        # 如果结果是字符串，尝试解析为 JSON
                        if isinstance(retry_result, str):
                            retry_result = json.loads(retry_result)
                        
                        return retry_result
                    except Exception as retry_e:
                        print(f"\n=== 重试解析错误 ===\n")
                        print(f"Error: {str(retry_e)}")
                        print()
                
                # 如果重试也失败或没有输出格式要求，返回原始内容
                return {"content": content}
            
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse JSON response: {str(e)}\nContent: {content}")
        except Exception as e:
            raise Exception(f"Structured chat failed: {str(e)}")

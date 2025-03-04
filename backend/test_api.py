import asyncio
import httpx
import json
from typing import Dict, List

async def test_conversation_flow():
    """测试完整的对话流程"""
    async with httpx.AsyncClient(base_url="http://localhost:9000") as client:
        # 1. 创建课程
        create_lesson_data = {
            "mode": "practice",
            "topic": "Job Interview Practice",
            "assessment_day": {
                "day_number": 1,
                "knowledge_points": [
                    {
                        "name": "Interview greetings",
                        "level": 2,
                        "examples": ["Good morning, thank you for having me", "It's a pleasure to meet you"]
                    },
                    {
                        "name": "Self-introduction",
                        "level": 3,
                        "examples": ["I have X years of experience in...", "My background is in..."]
                    },
                    {
                        "name": "Discussing strengths",
                        "level": 2,
                        "examples": ["My greatest strength is...", "I excel at..."]
                    }
                ],
                "materials": [
                    {
                        "type": "video",
                        "title": "Successful Job Interviews",
                        "content": "A video showing examples of successful job interviews"
                    }
                ],
                "review_activities": [
                    {
                        "type": "roleplay",
                        "description": "Practice answering common interview questions"
                    }
                ],
                "estimated_time": 30
            }
        }
        
        response = await client.post("/api/lesson/create", json=create_lesson_data)
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text}")
        assert response.status_code == 200
        create_response = response.json()
        lesson = create_response["lesson"]
        conversation_history = create_response["conversation_history"]
        
        print("\n=== 课程创建成功 ===")
        print(json.dumps(create_response, indent=2, ensure_ascii=False))

        # 2. 测试多轮对话
        conversation_inputs = [
            "你好，我可以用中文吗？",  # 测试语言切换请求
            "Sorry, I'll try in English. My name is John and I have 5 years of product management experience.",  # 正常英文对话
            "I worked at a large tech company before, leading their SaaS products.",  # 提供工作经验
            "exit"  # 结束对话
        ]

        print("\n=== 开始多轮对话测试 ===")
        for user_input in conversation_inputs:
            if user_input.lower() == "exit":
                print("\n对话结束")
                break

            chat_data = {
                "lesson": lesson,
                "conversation_history": conversation_history,
                "user_input": user_input
            }
            
            response = await client.post("/api/lesson/chat", json=chat_data)
            assert response.status_code == 200
            chat_response = response.json()
            
            # 更新对话历史用于下一轮对话
            conversation_history = chat_response["conversation_history"]
            
            print(f"\n用户: {user_input}")
            print(f"助手: {chat_response['content']}")
            print("\n当前对话历史:")
            for msg in conversation_history:
                if msg["role"] != "system":
                    print(f"{msg['role']}: {msg['content'][:100]}...")

async def main():
    try:
        await test_conversation_flow()
    except Exception as e:
        import traceback
        print(f"测试过程中出现错误: {str(e)}")
        print("详细错误信息:")
        print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(main())

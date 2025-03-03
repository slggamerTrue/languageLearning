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
            "scene": {
                "description": "这是一个产品经理职位的面试。",
                "your_role": "你是一位面试官，是产品部门的高级经理。",
                "student_role": "学生是一位应聘产品经理职位的候选人。",
                "additional_info": "公司是一家成长期的科技公司，主要产品是企业SaaS软件。",
                "current_situation": "面试即将开始，候选人已经就座。"
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

from typing import List, Dict, Optional
from datetime import datetime
from models.user import UserProfile, LearningMaterial, KnowledgePoint
from .llm_service import LLMService

class LessonDeliveryService:
    def __init__(self):
        self.llm = LLMService()

    async def start_lesson(self, lesson_plan: Dict, user_profile: UserProfile) -> Dict:
        """
        开始一节课程，返回课程的开场白和第一个互动环节
        """
        try:
            # 准备课程上下文
            materials = lesson_plan.get('materials', [])
            knowledge_points = lesson_plan.get('knowledge_points', [])
            
            context_prompt = {
                "role": "system",
                "content": f'''你是一位友好、专业的英语老师，正在给学生上一节互动式课程。

课程信息：
- 主题：{lesson_plan['topic']}
- 教学材料：{materials[0]['title'] if materials else 'Not specified'}
- 目标知识点：{knowledge_points[0]['name'] if knowledge_points else 'Not specified'}

学生信息：
- 英语水平：{user_profile.english_level}
- 学习兴趣：{', '.join(user_profile.interests)}

你的任务是：
1. 以轻松友好的方式开始课程
2. 通过提问和互动来引导学生学习
3. 给予及时、有针对性的反馈
4. 鼓励学生积极参与

规则：
1. 每次回复限制在1-2个简短的问题或指示
2. 给学生足够的思考和回答时间
3. 根据学生的回答调整后续内容
4. 多使用开放性问题
5. 及时给予正面反馈和鼓励

开始上课时：
1. 简短问候
2. 介绍今天的学习内容
3. 用一个简单的问题开始互动'''
            }

            first_prompt = {
                "role": "user",
                "content": "请开始上课，记住要互动。"
            }

            response = await self.llm.chat_completion([context_prompt, first_prompt])
            return response

        except Exception as e:
            raise Exception(f"Failed to start lesson: {str(e)}")

    async def process_student_response(self, 
                                    lesson_plan: Dict, 
                                    user_profile: UserProfile,
                                    conversation_history: List[Dict],
                                    student_response: str) -> Dict:
        """
        处理学生的回答，提供反馈并继续课程
        """
        try:
            # 添加教学指导到系统提示
            teaching_prompt = {
                "role": "system",
                "content": f'''作为英语老师，请根据学生的回答继续课程。

当前课程进度：
- 主题：{lesson_plan['topic']}
- 已进行的对话数：{len(conversation_history)}

指导原则：
1. 先对学生的回答给出具体反馈
   - 如果正确，解释为什么好
   - 如果有误，温和地指出并解释
2. 然后继续课程
   - 循序渐进地引入新内容
   - 确保与前面的内容有联系
3. 提出下一个问题或活动
   - 根据学生表现调整难度
   - 保持互动性和趣味性

注意：
- 每次回复保持简短，最多包含一个反馈和一个新问题
- 多鼓励，少批评
- 让学生多说，老师少说'''
            }

            # 将学生回答添加到对话历史
            all_messages = [teaching_prompt] + conversation_history + [
                {"role": "user", "content": student_response}
            ]

            # 获取下一步教学响应
            response = await self.llm.chat_completion(all_messages)
            return response

        except Exception as e:
            raise Exception(f"Failed to process student response: {str(e)}")

    async def end_lesson(self, 
                        lesson_plan: Dict, 
                        user_profile: UserProfile,
                        conversation_history: List[Dict]) -> Dict:
        """
        结束课程，提供总结和反馈
        """
        try:
            summary_prompt = {
                "role": "system",
                "content": f'''请总结这节课的学习情况，包括：
1. 学生掌握得好的地方
2. 需要继续加强的地方
3. 课后练习建议
4. 鼓励性的结束语

注意：
- 具体指出学生在哪些方面表现出色
- 给出具体的练习建议
- 以积极向上的态度结束'''
            }

            all_messages = [summary_prompt] + conversation_history
            response = await self.llm.chat_completion(all_messages)
            return response

        except Exception as e:
            raise Exception(f"Failed to end lesson: {str(e)}")

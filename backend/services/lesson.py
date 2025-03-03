from typing import Dict, List, Literal
from enum import Enum
import json
from services.llm_service import LLMService

class LessonMode(Enum):
    STUDY = "study"
    PRACTICE = "practice"

class LessonService:
    def __init__(self):
        self.llm_service = LLMService()
        self.max_conversation_turns = 20  # 最大对话轮数，超过后需要总结
        self.conversation_history = []  # 存储对话历史

    async def generate_lesson_content(self, lesson_plan: Dict, user_profile: Dict) -> Dict:
        """
        根据课程计划生成具体的课程内容
        """
        try:
            prompt = f"""基于以下信息生成一节互动式英语课程：

            课程计划：
            主题：{lesson_plan['topic']}
            情境：{lesson_plan['scenario']}
            学习目标：{lesson_plan['objectives']}

            学生信息：
            英语水平：{user_profile['english_level']}
            兴趣：{', '.join(user_profile['interests'])}
            
            请生成：
            1. 开场白和热身活动
            2. 核心教学内容
            3. 互动练习
            4. 实践活动
            5. 课程总结

            注意：内容应该有趣且实用，避免过多的语法讲解。"""

            response = await self.llm_service.chat_completion(
                messages=[
                    {"role": "system", "content": "你是一个专业的英语教师，正在准备一节互动式课程。"},
                    {"role": "user", "content": prompt}
                ]
            )

            return eval(response)

        except Exception as e:
            raise Exception(f"Lesson content generation failed: {str(e)}")

    async def generate_lesson_summary(self, lesson_record: Dict) -> Dict:
        """
        生成课后总结和反馈
        """
        try:
            prompt = f"""基于以下课程记录生成学习总结：

            课程内容：{lesson_record['content']}
            学生表现：{lesson_record['performance']}
            学生反馈：{lesson_record['feedback']}

            请提供：
            1. 掌握得好的内容
            2. 需要改进的地方
            3. 常见错误分析
            4. 建议的复习重点
            5. 下一步学习建议"""

            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "你是一个专业的英语教师，正在为学生提供课后反馈。"},
                    {"role": "user", "content": prompt}
                ]
            )

            return eval(response.choices[0].message.content)

        except Exception as e:
            raise Exception(f"Lesson summary generation failed: {str(e)}")


    async def summarize_conversation(self, messages: List[Dict]) -> str:
        """
        总结之前的对话内容
        """
        try:
            summary_prompt = f"""
            请总结以下对话的要点，包括：
            1. 已经讨论的主要话题和知识点
            2. 学生表现出的困惑或特别关注的内容
            3. 教师提供的主要解释和例子
            4. 学生的理解程度
            
            对话历史：
            {messages}
            """
            
            response = await self.llm_service.chat_completion(
                messages=[
                    {"role": "system", "content": "你是一个专业的对话总结者，需要提取对话中的关键信息。"},
                    {"role": "user", "content": summary_prompt}
                ]
            )
            return response["content"]
        except Exception as e:
            raise Exception(f"Conversation summarization failed: {str(e)}")

    async def conduct_lesson(self, lesson_content: Dict, user_message: str = None, conversation_history: List[Dict] = None) -> Dict:
        """
        进行实时互动教学，处理用户输入并返回适当的响应
        返回格式：
        {
            "speech_text": str,  # 必须的语音内容
            "display_text": str  # 可选的展示内容，支持markdown格式
        }
        """
        try:
            # 使用传入的对话历史或创建新的
            if conversation_history is None:
                conversation_history = []
                
            # 构建系统提示
            system_prompt = None
            if lesson_content["mode"] == LessonMode.STUDY.value:
                system_prompt = f"""You are an experienced English tutor helping students learn English.
            Today's topic: {lesson_content["topic"]}
            Assessment day: {lesson_content["assessment_day"]}
            
            你需要结合下面对话的内容，来一步一步的引导学生完成本次课程的内容。
            返回需要两个字段,display_text和speech_text：
            speech_text字段就是按对话，老师讲课的内容或者对学生问题的回答，注意保持本次课程的连贯性，如果被打断了要注意回到课程内容上继续讲解。
            如有需要，比如展示一页slide，一份菜单，为方便讲解显示的一段文字等，在display_text字段以markdown格式显示，如无需要则置为空字符串即可。如果课程内容完成并确认了学生的学习效果，则输入<end_of_lesson>。
            """
            else:  # PRACTICE mode
                scene = lesson_content.get('scene', {})
                system_prompt = f"""
                这是一个英语对话练习场景。

                场景描述：{scene.get('description', '')}
                你的角色：{scene.get('your_role', '')}
                学生的角色：{scene.get('student_role', '')}
                
                要求：
                1. 完全按照角色设定进行对话
                2. 不要做教学解释，除非学生特意要求
                3. 如果学生的英语表达有错误，用自然方式展示正确用法
                4. 保持对话的自然流畅
                5. 如果学生使用中文，以符合角色的方式鼓励使用英语
                """

            # 检查是否需要总结对话历史
            if len(conversation_history) >= self.max_conversation_turns * 2:
                summary = await self.summarize_conversation(conversation_history)
                conversation_history = [
                    {"role": "assistant", "content": f"之前对话总结：\n{summary}"}
                ]

            # 处理用户消息
            if user_message is None and not conversation_history:
                conversation_history = [
                    {"role": "user", "content": "continue."}
                ]

            # 在调用 structured_chat 前，将 system_prompt 添加到 conversation_history 的开头
            messages_with_system = conversation_history.copy()
            if system_prompt:
                messages_with_system.insert(0, {"role": "system", "content": system_prompt})

            # 使用structured_chat生成带格式的响应
            output_format = '''
            {
                "display_text": "The text to be displayed to the user, can include markdown formatting",
                "speech_text": "The natural, conversational version of the text to be spoken"
            }
            '''
            
            response = await self.llm_service.structured_chat(
                messages=messages_with_system,
                output_format=output_format
            )
            
            # 解析JSON响应
            formatted_response = {
                "role": "assistant",
                "content": response.get("speech_text"),
                "speech_text": response.get("speech_text"),
                "display_text": response.get("display_text")
            }
            
            return formatted_response

        except Exception as e:
            raise Exception(f"Lesson interaction failed: {str(e)}")

    async def generate_weekly_summary(self, weekly_records: List[Dict]) -> Dict:
        """
        生成每周学习总结和下周计划
        """
        try:
            prompt = f"""基于以下一周的学习记录生成总结报告：

            课程记录：{weekly_records}

            请提供：
            1. 本周学习重点回顾
            2. 进步与成就
            3. 需要加强的领域
            4. 下周学习建议
            5. 调整后的学习计划"""

            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "你是一个专业的英语教育顾问，正在为学生提供周度学习报告。"},
                    {"role": "user", "content": prompt}
                ]
            )

            return eval(response.choices[0].message.content)

        except Exception as e:
            raise Exception(f"Weekly summary generation failed: {str(e)}")

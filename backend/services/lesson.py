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

            response = await self.llm_service.chat_completion(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "你是一个专业的英语教师，正在为学生提供课后反馈。"},
                    {"role": "user", "content": prompt}
                ]
            )

            return response["content"]

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
            "speechText": str,  # 必须的语音内容
            "displayText": str  # 可选的展示内容，支持markdown格式
        }
        """
        try:
            # 使用传入的对话历史或创建新的
            if conversation_history is None:
                conversation_history = []
                
            # 构建系统提示
            system_prompt = None
            if lesson_content["mode"] == LessonMode.STUDY.value:
                system_prompt = f"""你是一个知识丰富且专业的英语老师，你叫Polly，是一个美国人，出生在三番，从小了解中国文化. 课程内容如下：
            {lesson_content}
            
            你需要结合上面的内容和已有的对话，来一步一步的引导学生完成本次课程的内容。由于涉及到讲解知识，有些内容可能较长，
            生成的对话应该是一段完整的内容，而不是话没说完就结束，比如讲到有下面三种方式，但是没说哪三种方式，然后就结束了，这种情况是要尽量避免的。
            你可以考虑增加些需要学生反馈的问题，以避免一次生成太长的内容，如这里设定了场景让学生说一说他知道的方式，然后根据学生的回答继续讲解。

            Important guidelines:
            1. 返回以json格式需要三个字段, diagnose, displayText和speechText：
            diagnose字段: 对于学生的上一句回答，进行诊断，主要评测语法是否有错，单词短语使用是否准确，任务完成度，在当前语境下是否合适等。
            speechText字段: 格式为字符串数组，教师说话的内容，按内容分为一句一句的，方便语音合成播放。
            displayText字段: 如有需要，比如展示一页slide，一份菜单，为方便讲解显示的一段文字等，在displayText字段以markdown格式显示，如无需要则置为空字符串即可。
                             如果学习课程内容完成并确认了学生的学习效果，通过了practice的练习，则在displayText输出<end_of_lesson>。

            2. 始终记得自己是一个英语教师，既要及时解答学生的疑问，也要基于下面的教学大纲来完成本课的内容。被打断了要记得及时回到课程内容上继续讲解。
            上课的流程为：课程先讲解知识点，然后结合场景讲解一些具体的例子，最后再讲解总结。学生提问，老师解答，最后通过练习来确认学习效果。这是一个1v1的课程，所以讲解中和练习中也多问问学生实际遇到的场景来讲解，让学生更有参与感。

            3.user的会话前缀是[voice]表示用户是通过语音输入，所以如果有单词让你疑惑可能是用户发音不标准的问题，你可以猜测用户的意思进行回答即可。
            前缀[text]表示用户是通过文字输入，那可能存在一些拼写错误。

            4. 不要简单回答或者重复用户的回答，要基于当前的教学大纲和对话流程引导用户。你需要说更多的东西，让学生参与到对话中来。

            注意：返回格式只需要json格式，返回前你需要再次确认你的返回是json格式，不论对话有多长，一定不要忘记这个rule，json格式如下：
            {{
                "diagnose": [{{ # 根据user最近的一句对话，分析是否存在语法，单词，结构，上下文错误，如无错误则返回空数组。
                    "type": str,  # 错误类型Grammar, Vocabulary, Structure, Context
                    "description": str,  # 错误描述，引号引用原文，并用中文描述错误原因
                    "correct": str  # 正确的英文表达
                }}],
                "speechText": string[],  # 必须的语音内容,按内容分为一句一句的，方便语音合成播放。
                "displayText": str  # 可选的展示内容，支持markdown格式
            }}
            """
            else:  # PRACTICE mode
                system_prompt = f"""You are in a role-playing scenario. Stay in character and respond naturally based on your role.        
            课程内容如下：
            {lesson_content}
    

            Important guidelines:
            1. For each response, provide two fields:
            - diagnose字段: 对于学生的上一句回答，进行诊断，主要评测语法是否有错，单词短语使用是否准确，任务完成度，在当前语境下是否合适等。
            - displayText: 当需要展示场景中需要用到的菜单、列表、文档等时才使用markdown格式显示，显示尽量详细，按照现实中的来否则为空
            - speechText: bot角色说话的内容，按内容分为一句一句的，方便语音合成播放。
            
            要求：
            1. 完全按照角色设定进行对话
            2. 不要做教学解释，除非学生特意要求
            3. user的会话前缀是[voice]表示用户是通过语音输入，所以如果有单词让你疑惑可能是用户发音不标准的问题，你可以猜测用户的意思进行回答即可。
            前缀[text]表示用户是通过文字输入，那可能存在一些拼写错误。不用纠正，继续对话即可
            4. 如果user使用中文，用英语以符合角色的方式表达自己不太懂中文，让对方用英文简单描述。
            5. 注意对话中引导完成设定的场景目标，当完成场景目标或者结束对话时，displayText中输入<end_of_lesson>以结束课程
            6. 记住只有说话的内容是放在speechText中，如果要有场景描述或者旁白，都放在displayText中
            返回格式只需要json格式，如下：
            {{
                "diagnose": [{{ # 根据user最近的一句对话，分析是否存在语法，单词，结构，上下文错误，如无错误则返回空数组。
        "type": str,  # 错误类型Grammar, Vocabulary, Structure, Context
        "description": str,  # 错误描述，引号引用原文，并用中文描述错误原因
        "correct": str  # 正确的英文表达
                }}],
                "speechText": string[],  # 必须的语音内容,按内容分为一句一句的，方便语音合成播放。
                "displayText": str  # 可选的展示内容，支持markdown格式
            }}
                """

            output_format = """
            为方便程序处理返回格式必须为有效的json格式，如下：
            {
                "diagnose": [{ # 根据user最近的一句对话，分析是否存在语法，单词，结构，上下文错误，如无错误则返回空数组。
        "type": str,  # 错误类型Grammar, Vocabulary, Structure, Context
        "description": str,  # 错误描述，引号引用原文，并用中文描述错误原因
        "correct": str  # 正确的英文表达
                }],
                "speechText": string[],  # 必须的语音内容,按一段内容分为一句一句的，方便语音合成播放。
                "displayText": str  # 可选的展示内容，支持markdown格式
            }
            """
            # 处理用户消息
            if user_message is None and not conversation_history:
                conversation_history = [
                    {"role": "user", "content": "continue."}
                ]

            # 在调用 structured_chat 前，将 system_prompt 添加到 conversation_history 的开头
            messages_with_system = conversation_history.copy()
            # 循环messages_with_system将speechText删除
            messages_with_system = [{"role": "user", "content": "\n".join([
            f"{msg['role'].capitalize()}: {msg['content']}" + 
            (f"\nDisplayText: {msg['displayText']}" if msg.get("displayText") else "")
            for msg in messages_with_system
        ])}]
            if system_prompt:
                messages_with_system.insert(0, {"role": "system", "content": system_prompt})

            
            response = await self.llm_service.structured_chat(
                messages=messages_with_system, output_format=output_format
            )
            
            # 解析JSON响应
            formatted_response = {
                "role": "assistant",
                "content": response.get("speechText", response.get("content")),
                "speechText": response.get("speechText", response.get("content")),
                "displayText": response.get("displayText", ""),
                "diagnose": response.get("diagnose", "")
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

            response = await self.llm_service.chat_completion(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "你是一个专业的英语教育顾问，正在为学生提供周度学习报告。"},
                    {"role": "user", "content": prompt}
                ]
            )

            return response["content"]

        except Exception as e:
            raise Exception(f"Weekly summary generation failed: {str(e)}")

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
            
            你需要结合上面的内容和已有的对话，结合场景和主题，通过和学生探讨的方式，来一步一步的引导学生完成本次课程的内容。由于涉及到讲解知识，有些内容可能较长，
            生成的对话应该是一段完整的内容，而不是话没说完就结束，比如讲到一个场景中要表达什么有下面三种方式，但是没说哪三种方式，然后就结束了，这种情况是要尽量避免的。
            为了减少一次生成对话量，如果分多点的情况，先简单总体说一下，然后就一点一点的讲解，讲解一点的过程中应该让学生参与练习，这样增加学生参与感。
            再比如讲解了一个单词，一个句子，或者一个语法后，一句一停顿的让学生跟读，跟读或者纠正用户发音时，不要仅单词或者短语，而是放在一个具体的例句中，方便用户理解使用场景。
            然后设定几个场景让学生来回答。一方面让学生理解，另一方面也让学生有参与感。
            而不是老师一直在上面讲，记住这是一个1v1的课程，所以讲解中和练习中也多问问学生实际遇到的场景来讲解，让学生更有参与感。

            Important guidelines:
            1. 返回以json格式需要三个字段, diagnose, displayText和speechText：
            diagnose字段: 对于学生最后一句的回答，进行诊断，主要评测语法是否有错，单词短语使用是否准确，任务完成度，在当前语境下是否合适等。
            speechText字段: 格式为字符串数组，教师说话的内容，所以不要出现特殊字符如星号括号等不方便读的，按内容分为一句一句的，方便语音合成播放。
            displayText字段: 如有需要，比如展示一页slide，一份菜单，为方便讲解显示的一段文字等，在displayText字段以markdown格式显示，如无需要则置为空字符串即可。
                             如果学习课程内容完成并确认了学生的学习效果，通过了practice的练习，则在displayText输出<end_of_lesson>。

            2. 始终记得自己是一个英语教师，既要及时解答学生的疑问，也要基于下面的教学大纲来完成本课的内容。被打断了要记得及时回到课程内容上继续讲解。
            上课的流程为：课程先讲解知识点，可能让学生跟读一遍加深记忆，然后结合场景讲解一些具体的例子，同时让学生多练习一下，最后再讲解总结。所有知识点都学习完毕后通过几个综合的练习来确认学习效果。这是一个1v1的课程，设定场景时不要让学生自己练习，一定是和老师互动。

            3.user的会话前缀是[voice]表示用户是通过语音输入，所以如果有单词让你疑惑可能是用户发音不标准的问题，你可以猜测用户的意思进行回答即可。
            前缀[text]表示用户是通过文字输入，那可能存在一些拼写错误。

            4. 不要简单回答或者重复用户的回答，要基于当前的教学大纲和对话流程引导用户。你需要说更多的东西，让学生参与到对话中来。

            注意：返回格式只需要json格式，返回前你需要再次确认你的返回是json格式，不论对话有多长，一定不要忘记这个rule，json格式如下：
            {{
                "diagnose": [{{ # 根据user最近的一句对话，分析是否存在语法，单词，结构，上下文错误，如无错误则返回空数组。
                    "type": str,  # 错误类型必须为：Grammar, Vocabulary, Structure, Context
                    "description": str,  # 错误描述，引号引用原文，并用中文详细说明错误原因
                    "correct": str  # 正确的英文表达
                }}],
                "speechText": string[],  # 必须的方便TTS的文本内容，不要出现特殊字符如星号括号等不方便读的,按内容分为一句一句的，方便语音合成播放。
                "displayText": str  # 可选的展示内容，支持markdown格式
            }}
            """
            else:  # PRACTICE mode
                system_prompt = f"""You are in a role-playing scenario. Stay in character and respond naturally based on your role.        
            课程内容如下：
            {lesson_content}
    
            场景设定和需要完成的目标由下面的displayText字段提供。在实现目标的过程中，随机给用户2-3个突发情况。如目标是超市购买指定的牛油果，按店员
            指导到相应货架后发现没有牛油果了，你可以在完成第一轮对话后通过displayText字段说明这个突发情况，并提示用户于是你找到了店员，然后让用户继续进行会话。

            Important guidelines:
            1. For each response, provide two fields:
            - diagnose字段: 对于学生的上一句回答，进行诊断，主要评测语法是否有错，单词短语使用是否准确，任务完成度，在当前语境下是否合适等。
            - displayText: 默认为空，当需要转场描述或者展示场景中需要用到的菜单、列表、文档等时才使用markdown格式显示，因为在手机侧显示，生成markdown时注意不要显示太长以至于一屏都装不下
            - speechText: bot角色说话的内容，必须的方便TTS的文本内容，不要出现特殊字符如星号括号等不方便读的，按内容分为一句一句的，方便语音合成播放。
            
            要求：
            1. 完全按照角色设定进行对话，注意任务目标是用户需要完成的，你扮演的角色并不一定知道。
            2. 不要做教学解释，始终保持你的身份
            3. user的会话前缀是[voice]表示用户是通过语音输入，所以如果有单词让你疑惑可能是用户发音不标准的问题，你可以猜测用户的意思进行回答即可。
            前缀[text]表示用户是通过文字输入，那可能存在一些拼写错误。不用纠正，继续对话即可
            4. 如果user使用中文，用英语以符合角色的方式表达自己不太懂中文，让对方用英文简单描述。
            5. 当完成场景目标或者结束对话时，displayText中输出<end_of_lesson>以结束课程
            6. 记住只有说话的内容是放在speechText中，如果要有场景描述或者旁白，都放在displayText中
            返回格式只需要json格式，如下：
            {{
                "diagnose": [{{ # 根据user最近的一句对话，分析是否存在语法，单词，结构，上下文错误，如无错误则返回空数组。
                    "type": str,  # 错误类型必须为：Grammar, Vocabulary, Structure, Context
                    "description": str,  # 错误描述，引号引用原文，并用中文详细说明错误原因
                    "correct": str  # 正确的英文表达
                }}],
                "speechText": string[],  # 必须的方便TTS的文本内容，不要出现特殊字符，按内容分为一句一句的，方便语音合成播放。
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
                messages=[
                    {"role": "system", "content": "你是一个专业的英语教育顾问，正在为学生提供周度学习报告。"},
                    {"role": "user", "content": prompt}
                ]
            )

            return response["content"]

        except Exception as e:
            raise Exception(f"Weekly summary generation failed: {str(e)}")

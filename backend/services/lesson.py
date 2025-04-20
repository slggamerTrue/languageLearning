from typing import Dict, List
from enum import Enum
import json
from services.llm_service import LLMService
from models.lesson_models import Message, CreateLessonRequest, SummaryLessonRequest

class LessonMode(Enum):
    STUDY = "study"
    PRACTICE = "practice"

class LessonService:
    # 语言代码到语言名称的映射
    LANGUAGE_NAMES = {
        "cmn-CN": "中文",
        "en-US": "English",
        "fr-FR": "French",
        "es-ES": "Spanish",
        "de-DE": "German",
        "ja-JP": "Japanese",
        "ko-KR": "Korean"
    }
    
    def __init__(self):
        self.llm_service = LLMService()
        
    def get_language_name(self, lang_code: str) -> str:
        """
        将语言代码转换为完整的语言名称
        
        参数:
            lang_code: 语言代码，如 "cmn-CN", "en-US" 等
            
        返回:
            语言的完整名称，如 "中文", "English" 等
        """
        # 如果找不到对应的语言名称，则返回代码本身
        return self.LANGUAGE_NAMES.get(lang_code, lang_code)
    
    def should_use_english_prompt(self, native_lang: str) -> bool:
        """
        决定是否使用英语提示
        
        参数:
            native_lang: 用户母语代码
            
        返回:
            如果应该使用英语提示，则返回 True，否则返回 False
            
        说明:
            除了中文母语外，其他母语都使用英语提示
        """
        # 只有中文母语使用中文提示，其他语言都使用英语提示
        return True

    async def create_lesson(self, request: CreateLessonRequest, native_lang: str, learning_lang: str) -> Dict:
        # 获取语言名称
        # 生成系统提示和欢迎消息
        mode = LessonMode.STUDY if request.mode == "study" else LessonMode.PRACTICE
        native_language_name = self.get_language_name(native_lang)
        learning_language_name = self.get_language_name(learning_lang)
        if mode == LessonMode.PRACTICE:  # 角色扮演模式
            # 构建场景资源提示
            system_prompt = f"""You are a professional {learning_language_name} teacher, designing a role-playing scenario for a {native_language_name} mother tongue learner.
            Based on the information provided by the user to build a role-playing scenario. Need to set a completion goal to ensure this scenario is based on the user's level and challenging, 
            and add some random events to ensure the scenario is different each time.
            
            Important guidelines:
            1. For each response, provide two fields, displayText and speechText:
               - displayText: 基于课程信息生成一个场景，对场景进行简单描述，并且分配bot和user的角色，显示本场景设定达到的目标以及所需的一些信息，用markdown格式方便清晰的描述。为方便在手机上显示而优化。
               如是问路的场景，你可以用markdown提供一个地图，设定一个当前位置和目的地，看用户能否能用{learning_language_name}正确指路。如是餐厅的场景，
               你可以提供带价格的菜单，看用户能否按要求(如必须含有2份主食，吃素，有忌口或者价格限定在多少范围内)搭配点餐. Please use {native_language_name}.
               - speechText: 你作为bot, based on the role in displayText, generate an opening statement, if you should not speak first, return an empty array, the opening statement should be concise, for convenience of speech synthesis, divide into sentences.
            
            """
        else:  # 学习模式
            system_prompt = f"""You are an experienced English tutor helping user learn {learning_language_name} language.
            基于下面提供的课程信息和用户信息，你需要规划今天的课程大纲，并且生成一个开场语。生成大纲时请考虑用户目前的语言水平和用户年龄，如用户{learning_language_name}水平较低，请使用尽量基础的单词和句型。
            
            Important guidelines:
            1. Return two fields, displayText and speechText:
            displayText field: Plan today's course outline in markdown format, optimized for display on a mobile device.
            speechText field: Teacher's voice output content, divide into sentences for convenience of speech synthesis.
            
            2. This is a one-on-one teaching scenario, so you should plan the outline based on the student's level and the content to be learned.
            """
        
        # 使用structured_chat生成带格式的欢迎语
        output_format = '''
        Return format must be json format, as follows:
        {
            "speechText": string[],  # Required speech content, divided into sentences, do not use special characters like asterisks, brackets, pinyin, etc. which may cause speech synthesis errors
            "displayText": str  # Display content, support markdown format
        }
        '''
        
        response = await self.llm_service.structured_chat(
            messages=[{"role": "system", "content": system_prompt + output_format},
            {"role": "user", "content": str(request)}]
        )
        
        displayText = response["displayText"]
        speechText = response["speechText"]
        
        initial_conversation = [
            Message(
                role="assistant",
                content=" ".join(map(str, speechText)),  # Use speechText as the base content
                displayText=displayText,
                speechText=speechText
            )
        ]
        
        return {
            "conversation_history": initial_conversation
        }

    async def conduct_lesson(self, lesson_content: Dict, user: Dict = None, user_message: str = None, conversation_history: List[Dict] = None, native_lang: str = "cmn-CN", learning_lang: str = "en-US") -> Dict:
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
                
            # 获取语言名称
            native_language_name = self.get_language_name(native_lang)
            target_language_name = self.get_language_name(learning_lang)
            
            # 构建系统提示
            system_prompt = None
            if lesson_content["mode"] == LessonMode.STUDY.value:
                system_prompt = f"""You are a knowledgeable and professional {target_language_name} teacher, you are Polly, an American born in San Francisco, who has a deep understanding of {target_language_name} culture. 
                Course content: {lesson_content}
                User info: {user}
            
            你需要结合上面的课程内容, 用户信息以及下面提供的对话，结合场景和主题，通过和user探讨的方式，来一步一步的引导user完成本次{target_language_name}学习。这是一个一对一的教学，请保证充分的互动。

            2. 请使用{target_language_name}语言，不要出现其他语言内容。并且你需要根据用户的年龄和{target_language_name}语言水平来决定你使用语言的难易度。如用户年龄较小或{target_language_name}水平较低，请使用尽量基础的单词和句型，限定词汇量。
            另外，如果对话过程中用户表示太难了或者听不懂，你可以用更简单的方式重新解释，并且之后也一直保持简单，往下调低难度，限定词汇量等。

            Important guidelines:
            1. 返回以json格式需要三个字段, diagnose, displayText和speechText：
            diagnose字段: 对于下面user最后一句的回答，进行诊断，主要评测语法是否有错，单词短语使用是否准确，任务完成度，在当前语境下是否合适等。
            speechText字段: 格式为字符串数组，教师说话的内容，Please use {target_language_name} language，所以不要出现其他语言内容或者特殊字符如星号括号拼音等不方便语音合成的内容，内容分为一句一句的，方便语音合成播放。
            displayText字段: 尽量不显示，除非讲解中需要用到文字不好描述的内容，如展示一份菜单、地图等。在displayText字段以markdown格式显示，如无需要则置为空字符串即可。
                             如果学习课程内容完成并通过实际场景练习确认了学生的学习效果，则在displayText输出<end_of_lesson>。

            2. 始终记得自己是一个{target_language_name}教师，既要及时解答user的疑问，也要基于下面的教学大纲来完成本课的内容。被打断了要记得及时回到课程内容上来。
            教学中要充分保证互动，以确认user的学习效果。

            3.user的会话前缀是[voice]表示user是通过语音输入，所以如果有单词让你疑惑可能是user发音不标准造成语音识别的问题，你可以猜测user的意思进行回答即可。
            前缀[text]表示user是通过文字输入，那可能存在一些拼写错误。

            4. 你一次说话不要太长，需要鼓励user多说，让user参与到对话中来。

            注意：返回格式只需要json格式，返回前你需要再次确认你的返回是json格式，不论对话有多长，一定不要忘记这个rule，json格式如下：
            {{
                "diagnose": [{{ # 根据user最近的一句对话，分析是否存在语法，单词，结构，上下文错误，如无错误则返回空数组。
                    "type": str,  # 错误类型必须为：Grammar, Vocabulary, Structure, Context，Pronunciation
                    "description": str,  # 错误描述，引号引用原文，说明错误原因，please use {native_language_name} language
                    "correct": str  # 正确的{target_language_name}表达
                }}],
                "speechText": string[],  # Please use {target_language_name} language, do not use other languages or special characters like asterisks, brackets, pinyin, etc. which may cause speech synthesis errors, divide into sentences for convenience of speech synthesis.
                "displayText": str  # 默认为空，除非要展示一些语音不好描述的内容，如展示一份菜单、地图等，support markdown format, default use {target_language_name}, also can use {native_language_name}.
            }}
            """
            else:  # PRACTICE mode
                system_prompt = f"""You are in a role-playing scenario for {target_language_name}. Stay in character and respond naturally based on your role.        
            场景内容如下：
            {lesson_content}
    
            场景设定和需要完成的目标由下面的第一个message的displayText字段提供。在实现目标的过程中，随机给用户2-3个突发情况。如目标是超市购买指定的牛油果，按店员
            指导到相应货架后发现没有牛油果了，你可以在完成第一轮对话后通过displayText字段说明这个突发情况，并提示用户于是你找到了店员，然后让用户继续进行会话。

            Important guidelines:
            1. For each response, provide two fields:
            - diagnose字段: 对于下面user的最后一句回答，进行诊断，主要评测语法是否有错，单词短语使用是否准确，任务完成度，在当前语境下是否合适等。
            - displayText: 默认为空，当需要转场描述或者展示场景中需要用到的菜单、列表、文档等时才使用markdown格式显示，因为在手机侧显示，生成markdown时注意不要显示太长以至于一屏都装不下，Please use {target_language_name} language or {native_language_name} language.
            - speechText: bot角色说话的内容，必须的方便TTS的文本内容，不要出现特殊字符如星号括号等不方便读的，按内容分为一句一句的，方便语音合成播放。Please use {target_language_name} language.
            
            要求：
            1. 完全按照角色设定进行对话，注意任务目标是用户需要完成的任务，你扮演的角色并不一定知道。所以不要提示用户完成任务。
            2. 不要做教学解释，始终保持你的身份，说你的角色该说的话。
            3. user的会话前缀是[voice]表示用户是通过语音输入，所以如果有单词让你疑惑可能是用户发音不标准的问题，你可以猜测用户的意思进行回答即可。
            前缀[text]表示用户是通过文字输入，那可能存在一些拼写错误。不用纠正，继续对话即可
            4. 如果user使用非{target_language_name}，用{target_language_name}以符合角色的方式表达自己不太懂其他语言，让对方用{target_language_name}简单描述。
            5. 当完成场景目标或者结束对话时，displayText中输出<end_of_lesson>以结束课程
            6. 记住只有说话的内容是放在speechText中，如果要有场景描述或者旁白，都放在displayText中
            返回格式只需要json格式，如下：
            {{
                "diagnose": [{{ # 根据下面user最近的一次对话，分析是否存在语法，单词，结构，上下文错误，如无错误则返回空数组。
                    "type": str,  # 错误类型必须为：Grammar, Vocabulary, Structure, Context，Pronunciation
                    "description": str,  # 错误描述，引号引用原文，说明错误原因，please use {native_language_name} language
                    "correct": str  # 正确的{target_language_name}表达
                }}],
                "speechText": string[],  # 必须是方便TTS合成的文本内容，不要出现特殊字符如星号、括号、拼音等不方便读的，内容分为一句一句的，方便语音合成播放。
                "displayText": str  # 可选的展示内容，支持markdown格式，默认使用{target_language_name},如有需要也能使用{native_language_name}。
            }}
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
            #打印messages_with_system的最后一句
            print("user message:", messages_with_system[-1])
            messages_with_system.insert(0, {"role": "system", "content": system_prompt})

            
            response = await self.llm_service.structured_chat(
                messages=messages_with_system
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


    async def summary_lesson(self, request: SummaryLessonRequest, native_lang: str = "cmn-CN", learning_lang: str = "en-US") -> Dict:
        from datetime import datetime
        current_date = datetime.now().strftime("%Y-%m-%d")
        native_language_name = self.get_language_name(native_lang)
        target_language_name = self.get_language_name(learning_lang)
            
        system_prompt = f"""你是一个{target_language_name}教育专家，本次课程为{request.mode}模式. 今天的日期是：{current_date}

        本次课程的内容，用户信息和对话都在下面的用户输入中,其中user表示用户的对话，assistant表示bot的回复。user的会话前缀是[voice]表示用户是通过语音输入，
        所以如果有单词让你疑惑可能是用户发音不标准的问题，你可以猜测用户的意思进行回答即可。前缀[text]表示用户是通过文字输入，那可能存在一些拼写错误。

        TASK：The conversation is a {native_language_name} speaker study {target_language_name}.Please use {native_language_name} language generate a markdown report, 
        the report format example is as follows, you need to translate it to {native_language_name} language, only output correct and valid markdown format report, 
        do not add other descriptions:

        # 📊 对话评估报告

> **对话主题**：`[填写主题]`  
> **日期**：`{current_date}`  

---

## 🎯 表现概述
- **整体理解度**：`[对用户理解程度的总体评价]`
- **互动积极性**：`[描述用户在对话中的参与度]`
- **关键亮点**：
  - ✅ `[用户展现出的亮点 1]`
  - ✅ `[用户展现出的亮点 2]`
  - ✅ `[用户展现出的亮点 3]`
- **需要改进**：
  - 🔄 `[需要改进的方面 1]`
  - 🔄 `[需要改进的方面 2]`

---

## 📌 知识掌握情况
| 评估维度 | 评价 |
|---------|------|
| **核心概念理解** | `[浅显 / 部分掌握 / 较好 / 熟练]` |
| **实践应用能力** | `[弱 / 一般 / 良好 / 熟练]` |
| **逻辑表达能力** | `[需要提升 / 清晰流畅 / 优秀]` |
| **自主思考能力** | `[较弱 / 需要引导 / 主动思考]` |

---

## 📈 互动与反馈分析
- **学生提问情况**：
  - `[是否有深度问题，或仅停留在表面问题]`
  - `[提问是否能促进对话继续]`
- **回答质量**：
  - `[是否能完整表达自己的想法]`
  - `[是否能结合案例或个人理解]`
- **对关键知识点的反应**：
  - `[哪些内容学生反应积极]`
  - ⚠️ `[哪些内容学生较为困惑]`

---

## 🎯 未来学习建议
- **强化学习内容**：
  - 📖 `[建议复习的知识点]`
  - 🏗 `[推荐进一步练习的方法]`
- **提升互动表现**：
  - 🎤 `[如何更主动表达自己的观点]`
  - 🔍 `[如何提高沟通能力]`
- **个性化学习建议**：
  - 🎯 `[根据学生特点给出的具体建议]`

---

## 📎 总结
> `[用一句话总结这节课学生的整体学习效果]`

        """
        
        response = await self.llm_service.chat_completion(
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": str(request)}]  #, model="pkqwq:latest"
        )
        report = response["content"]
        if report.startswith("\"") and report.endswith("\""):
            report = report[1:-1]
        return report


    async def evaluate_lesson(self, request: SummaryLessonRequest, native_lang: str = "cmn-CN", learning_lang: str = "en-US") -> Dict:
        from datetime import datetime
        current_date = datetime.now().strftime("%Y-%m-%d")

        native_language_name = self.get_language_name(native_lang)
        target_language_name = self.get_language_name(learning_lang)
        
        system_prompt = f"""你是一个{target_language_name}教育专家，本次{target_language_name}课程为{request.mode}模式。
        今天的日期是：{current_date}

        本次课程的内容、用户信息以及对话见后。其中user表示用户的对话，assistant表示助手的回复。user的会话前缀是[voice]表示用户是通过语音输入，所以如果有单词让你疑惑可能是用户发音不标准的问题，你可以猜测用户的意思进行回答即可。
        前缀[text]表示用户是通过文字输入，那可能存在一些拼写错误。
        TASK: 你的任务是基于这些信息评估学生本课的完成情况以及本课中表现的英语水平。Please use {native_language_name} language to describe the reason.

        英语水平评测标准为
9分 专家水平：具有完全的英语运用能力，做到适当、精确、流利并能完全理解语言
8分 优秀水平：能将英语运用自如,只是有零星的错误或用词不当，在不熟悉语境下可能出现误解，可将复杂细节的争论掌握的相当好
7分 良好水平：能有效运用英语,虽然偶尔出现不准确、不适当和误解，大致可将复杂的英语掌握的不错，也能理解详细的推理
6分 合格水平：大致能有效运用英语，虽然有不准确、不适当和误解发生，能使用并理解比较复杂的英语，特别是在熟悉的语境下
5分 基础水平：可部分运用英语，虽然经常出现错误，但在大多数情况下可明白大致的意思，在经常涉及的领域内可应付基本的沟通
4分 有限水平：只限在熟悉的状况下有基本的理解力，在理解与表达上常发生问题，无法使用复杂英语
3分 极有限水平：在极熟悉的情况下也只能进行一般的沟通，频繁发生沟通障碍
2分 初学水平：难以听懂或者看懂英语
1分 不懂英语：掌握个别单词，几乎无法交流，最多能说出个别单词，根本无法用英语沟通
0分 英语0基础：完全不懂英语，英语有多少字母都不知道

        输出格式为有效的json，格式如下：
        {{
            "text": str,  # 一句话总结评分原因
            "eval": {{
                "score": int,  # 本课的完成情况，1-3分，3分最高，表示完成了课程要求的所有内容，2分表示完成了课程要求的大部分要求，1分最低，表示大部分要求没有完成。
                "reason": str  # 评级原因，如"要求进行的练习没有完成，或者回答的内容不够详细。" Please use {native_language_name} language.
                }}
            "level": {{
                "score": number,  # 综合得分, 按上面的雅思口语评分标准，得分0-9
                "reason": str  # 得分原因，如合格水平：大致能有效运用英语，虽然有不准确、不适当和误解发生，能使用并理解比较复杂的英语，特别是在熟悉的语境下 Please use {native_language_name} language.
            }}
        }}
        """
        
        response = await self.llm_service.structured_chat(
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": str(request)}]
        )
        return response


    async def generate_weekly_summary(self, request: Dict, native_lang: str = "cmn-CN", learning_lang: str = "en-US") -> Dict:
        """
        生成每周学习总结和下周计划
        """
        try:
            # 获取语言名称
            native_language_name = self.get_language_name(native_lang)
            target_language_name = self.get_language_name(learning_lang)
            
            system_prompt = f"""你是一个{target_language_name}教育专家，一位{native_language_name}母语的学习者本周学习报告如下，你需要生成一份总结报告。
        根据这一周的报告的平均水平以及用户当前水平评价是否需要调整用户的水平评价(level:0-9的雅思口语标准)和语速(speed：slowest, slow, normal),
        如需调整就加入到action中，否则action为空。注意一定要是变化明显的时候才调整，避免频繁调整。
        输出格式为json，格式如下：
        {{
            "summary": str,  # 本周学习重点回顾
            "achievements": str,  # 进步与成就
            "weaknesses": str,  # 需要加强的领域
            "suggestions": str,  # 下周学习建议
            "action": [{{
                "type": str, # 行为类型，目前只有level和speed
                "value": str, # 行为值
                "reason": str # 行为原因
            }}]
        }}
        """
        
            response = await self.llm_service.structured_chat(
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": str(request)}]
            )
            return response

        except Exception as e:
            raise Exception(f"Weekly summary generation failed: {str(e)}")

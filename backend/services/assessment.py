from typing import List, Dict, Optional
from datetime import datetime
from .llm_service import LLMService

class AssessmentService:
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
        self.llm = LLMService()
    
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


    async def conduct_initial_assessment(self, messages: List[Dict], native_lang: str = "", learning_lang: str = "en-US") -> Dict:
        """
        通过对话进行初始评估
        
        参数:
            messages: 对话历史
            native_lang: 用户母语，默认为"cmn-CN"（中文）
            learning_lang: 学习语言，默认为"en-US"（英语）
        """
        try:
            use_english_prompt = True
            if native_lang == "":
                native_lang = "cmn-CN"
                use_english_prompt = False
            # 获取语言名称
            native_language_name = self.get_language_name(native_lang)
            target_language_name = self.get_language_name(learning_lang)
            
            # 根据母语选择提示语言
            if use_english_prompt:
                system_content = f"""
--------Role-------------------
You are a professional {target_language_name} teacher. As the first step in helping a {native_language_name} speaker who want to learn {target_language_name} develop a {target_language_name} learning plan, 
you need to try to collect the following information through dialogue. If the user's conversation does not provide the above information, 
you can try to guide the user to provide it.
Your output must be in valid JSON format, with the guided dialogue content placed in the speechText field.

-------Target Information-------------------
1. The user's goal for learning {target_language_name}, what level they need to achieve
2. The user's self-assessed language proficiency level
3. Time available for daily study
4. User's personal information such as {target_language_name} name (if none, suggest one), gender, age, occupation, interests, etc.

---------Important----------------------
1. Ask only 1 question at a time, dynamically adjusting your expression based on the user's language proficiency.
2. If the user speaks in another language not {target_language_name}, you can understand but still maintain responses in {target_language_name}.
3. Maintain a professional and friendly attitude, keeping the dialogue process as brief as possible to complete the collection of information.
4. When you have collected all the target information or the user clearly indicates that they do not want to provide more information, include the <ASSESSMENT_COMPLETE> mark in the displayText field.
5. The output must be valid JSON in the following format:
{{
    "speechText": string[], # speechText string array, the teacher's speech content, divided into an array of sentences for convenient speech synthesis playback.
    "displayText": str # displayText string, normally empty, output <ASSESSMENT_COMPLETE> mark after collecting sufficient information.
}}
"""
            else:
                system_content = """
--------Role-------------------
你是一个专业的英语教师。作为帮学生制定英语学习计划的第一步，你需要通过对话尝试收集以下信息，如果学生的对话中没有提供以上信息，你可以尝试引导学生提供。
你的输出必须是一个有效的json格式，引导的对话内容放在speechText字段。

-------Target-------------------
1. user学习英语的目标，需要达到什么程度
2. 每日可用于学习的时间
3. user的个人信息如英语名(如没有则建议用户取一个)，性别，年龄，职业，兴趣爱好等

---------Important----------------------
1. 每次只问1个问题，根据用户的英语水平动态调整表达方式。
2. 如果学生用英语回答，就用英语交流；如果学生用其他语言说，你能理解但是仍然保持用英文回答。
3. 保持专业和友好的态度，尽量简短对话过程以完成信息的收集。
4. 当你收集到所有目标信息或者用户明确表示不想提供这些信息后，在displayText字段中包含 <ASSESSMENT_COMPLETE> 标记：
5. 输出必须是一个有效的json，json格式为：
{
    "speechText": string[], #speechText字符串数组，教师说话的内容，为方便语音合成播放，分为一句一句的数组.
    "displayText": str #displayText字符串，平时为空，收集到足够信息后，输出<ASSESSMENT_COMPLETE>标记.
}

# """
            
            system_message = {
                "role": "system",
                "content": system_content
            }
            
            messages_with_system = [system_message] + [{"role": "user", "content": "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in messages])}]
            #return await self.llm.chat_completion(all_messages)
            response = await self.llm.structured_chat(messages_with_system)
            content = "".join(response.get("speechText", response.get("content")))
            # 解析JSON响应
            formatted_response = {
                "role": "assistant",
                "content": content,
                "speechText": response.get("speechText", response.get("content")),
                "displayText": response.get("displayText", ""),
            }
            return formatted_response

        except Exception as e:
            raise Exception(f"Assessment failed: {str(e)}")

    async def analyze_assessment(self, conversation: List[Dict], native_lang: str = "", learning_lang: str = "en-US") -> Dict:
        """
        分析对话内容，生成用户档案
        
        参数:
            conversation: 对话历史
            native_lang: 用户母语，默认为"cmn-CN"（中文）
            learning_lang: 学习语言，默认为"en-US"（英语）
        """
        try:
            # 检查是否有完成标记
            assessment_complete = False
            for msg in conversation:
                if "<ASSESSMENT_COMPLETE>" in msg["content"]:
                    assessment_complete = True
                    break

            if not assessment_complete:
                print("\n警告：未找到 <ASSESSMENT_COMPLETE> 标记，可能评估尚未完成\n")

            # 将对话转换为更易读的格式
            formatted_conversation = ""
            for msg in conversation:
                role = msg["role"]
                content = msg["content"].replace("<ASSESSMENT_COMPLETE>", "").strip()
                formatted_conversation += f"{role}: {content}\n\n"

            use_english_prompt = True
            if native_lang == "":
                native_lang = "cmn-CN"
                use_english_prompt = False
            # 获取语言名称
            native_language_name = self.get_language_name(native_lang)
            target_language_name = self.get_language_name(learning_lang)

            if use_english_prompt:
                content_text = f"""Please analyze the following conversation and generate a learner profile:

{formatted_conversation}"""
                system_prompt = f"""
You are a professional {target_language_name} Teaching Consultant. Your primary task is to analyze conversations between a {native_language_name} speaker who want to learn {target_language_name} and a teacher to generate a comprehensive learner profile.

Based on the dialogue provided, you must extract the following information and structure it precisely according to the specified JSON format:

1.  **{target_language_name} Proficiency Level:**
    * Evaluate the user's spoken {target_language_name} proficiency using the IELTS Speaking Band Descriptors provided below.
    * Assign *both* a numerical score (0-9) and the corresponding textual description for that score.

    **IELTS Speaking Band Descriptors:**
    * **9 (Expert User):** Has fully operational command of the language: appropriate, accurate and fluent with complete understanding.
    * **8 (Very Good User):** Has fully operational command of the language with only occasional unsystematic inaccuracies and inappropriacies. Misunderstandings may occur in unfamiliar situations. Handles complex detailed argumentation well.
    * **7 (Good User):** Has operational command of the language, though with occasional inaccuracies, inappropriacies and misunderstandings in some situations. Generally handles complex language well and understands detailed reasoning.
    * **6 (Competent User):** Has generally effective command of the language despite some inaccuracies, inappropriacies and misunderstandings. Can use and understand fairly complex language, particularly in familiar situations.
    * **5 (Modest User):** Has partial command of the language, coping with overall meaning in most situations, though is likely to make many mistakes. Should be able to handle basic communication in own field.
    * **4 (Limited User):** Basic competence is limited to familiar situations. Has frequent problems in understanding and expression. Is not able to use complex language.
    * **3 (Extremely Limited User):** Conveys and understands only general meaning in very familiar situations. Frequent breakdowns in communication occur.
    * **2 (Intermittent User):** No real communication is possible except for the most basic information using isolated words or short formulae in familiar situations and to meet immediate needs. Has great difficulty understanding spoken and written {target_language_name}.
    * **1 (Non User):** Essentially has no ability to use the language beyond possibly a few isolated words.
    * **0 (Did not attempt / Absolute Beginner):** No assessable language produced / Completely new to {target_language_name}.

2.  **Interests and Hobbies:**
    * Extract and list all interests and hobbies mentioned by the user.
    * Descriptions should be as detailed as possible based on the conversation (e.g., if "movies" are mentioned, specify genres or specific film titles if discussed).
    * Include any specific names of movies, games, books, etc., mentioned.
    * Note any career-related interests mentioned.

3.  **Learning Goals:**
    * Extract and list all learning goals explicitly stated by the user.
    * Describe goals in detail (e.g., if "for work," specify the context like "difficulty expressing ideas during stand-up meetings" or "uncertainty in phrasing opinions in professional emails").
    * Include specific scenarios mentioned (e.g., "writing reports," "giving presentations").

4.  **Daily Study Time (minutes):**
    * Record the specific daily study time (in minutes) mentioned by the user.
    * If the user does not specify a time, recommend a suitable duration (as an integer representing minutes) based on their learning goals and interests.
    * The output value *must* be an integer.

5.  **Total Study Days:**
    * Record the number of study days based on any deadline or timeframe provided by the user.
    * If no deadline is provided, estimate the total number of days required to achieve the stated learning goals, considering their current proficiency level.
    * The output value *must* be an integer.

6.  **Pacing Recommendation:**
    * Based on the user's assessed {target_language_name} level and learning goals, recommend a suitable learning pace.
    * The value must be one of: `"slowest"`, `"slow"`, or `"normal"`.

**Output Format:**

The output *must* be a single, valid JSON object structured exactly as follows. use {native_language_name} language
Do not include any explanations, comments outside the defined structure, or fields not listed below.

```json
{{
    "user_profile": {{
        "name": string, // User's {target_language_name} name (use empty string "" if not provided)
        "age": number, // User's age (use 0 if not provided)
        "gender": string, // User's gender ("male" or "female", use empty string "" if not provided)
        "career": string, // User's occupation/career (use empty string "" if not provided)
        "other": string // Any other relevant personal information mentioned (use empty string "" if not provided)
    }},
    "language_level": {{
        "text": string,   // Text description of the assessed level, please use {native_language_name} language
        "score": number // The corresponding proficiency score (0-9)
    }},
    "speed": string, // Recommended learning pace: "slowest", "slow", or "normal"
    "interests": string[], // Array of strings detailing interests and hobbies
    "learning_goals": string[], // Array of strings detailing learning goals
    "study_time_per_day": number, // Recommended or stated daily study time in minutes (integer)
    "total_study_day": number // Estimated or stated total study days (integer)
}}
                """
                
            else:
                content_text = f"""请分析以下对话内容，生成一份学习者档案：

{formatted_conversation}"""
                system_prompt = """你是一个专业的英语教学顾问。你的工作是通过分析学生与教师的对话，生成一份学习者的档案。

你需要从对话内容中提取以下信息：

1. 英语水平：
基于下面的评估系统，你需要确定学生的英语水平。
雅思口语评分标准
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

2. 兴趣爱好：
   - 列出学生提到的所有兴趣爱好, 描述尽量详细，比如提到了喜欢看电影，要问清楚喜欢什么类型的电影，喜欢哪部电影列表等
   - 如果提到了具体的电影或游戏名称，也要包含在内
   - 如果提到了职业相关的兴趣，也要包含

3. 学习目标：
   - 列出学生明确表达的所有学习目标，学习目标也尽量详细，比如为了工作，就要问清楚工作中是遇到了哪方面的问题，是standup meeting的时候不知道如何表达自己的想法，还是写邮件的时候不知道如何表达自己的观点等
   - 如果提到了具体的场景（如写报告、做演示），要包含这些细节

4. 每日学习时间：
   - 使用学生提供的具体时间
   - 如果学生没有提供，根据学生的学习目标和兴趣爱好推荐合适的时长
   - 必须是一个整数，表示分钟数

5. 预计学习天数：
   - 如果学生提供得有deadline，则按此设定
   - 如果学生没有提供，则根据学生现有水平以及设定的目标，评估一个时间
   - 如果时间太长(>30天)，我们则建议将目标分阶段
   - 必须是一个整数，表示天数

6. 速度建议：
   - 根据学生的英语水平和学习目标，给出建议的速度
   - 可以是 "slowest", "slow", "normal" 中的一个

输出格式必须是一个有效的 JSON 对象，包含以下字段：
{
    "user_profile": {
        "english_name": string, // 用户的英文名
        "age": number, // 用户的年龄，未提供则为 0
        "gender": string, // 用户的性别，取值为 "male" 或 "female"
        "career": string, // 用户的职业
        "other": string // 其他信息
    },
    "english_level": {
        "text": string,   // 得分描述，如合格水平：大致能有效运用英语，虽然有不准确、不适当和误解发生，能使用并理解比较复杂的英语，特别是在熟悉的语境下
        "score": number // 综合得分, 按上面的雅思口语评分标准，得分0-9
    },
    "speed": string, // 建议语速，取值为 "slowest", "slow", "normal"     
    "interests": string[],       // 兴趣爱好列表，文字描述尽量详细
    "learning_goals": string[],  // 学习目标列表，文字描述尽量详细
    "study_time_per_day": number, // 每日学习时间（分钟）
    "total_study_day": number // 预计学习天数
}

请严格按照指定的格式输出，不要添加任何其他字段或注释。"""

            analysis_prompt = {
                "role": "system",
                "content": system_prompt
            }

            content_text_user = {
                "role": "user",
                "content": content_text
            }

            messages = [analysis_prompt, content_text_user]

            try:
                profile_data = await self.llm.structured_chat(messages)
                print("\n=== LLM 返回的数据 ===\n")
                print(profile_data)
                return profile_data
                
            except ValueError as e:
                print(f"\n=== 数据验证错误 ===\n")
                print(f"错误信息：{str(e)}")
                raise Exception(f"Profile analysis failed: {str(e)}")
            except Exception as e:
                print(f"\n=== LLM 服务错误 ===\n")
                print(f"错误信息：{str(e)}")
                raise Exception(f"Profile analysis failed: {str(e)}")

        except Exception as e:
            print(f"\n=== 分析失败 ===\n")
            print(f"错误信息：{str(e)}")
            raise Exception(f"Profile analysis failed: {str(e)}")


    async def generate_total_plan(self, user_profile: Dict, native_lang: str = "", learning_lang: str = "en-US") -> Dict:
        """
        根据用户档案估算学习时长（周数）
        
        参数:
            user_profile: 用户档案
            native_lang: 用户母语，默认为"cmn-CN"（中文）
            learning_lang: 学习语言，默认为"en-US"（英语）
        """
        try:
            use_english_prompt = True
            if native_lang == "":
                native_lang = "cmn-CN"
                use_english_prompt = False
            # 获取语言名称
            native_language_name = self.get_language_name(native_lang)
            target_language_name = self.get_language_name(learning_lang)
            
            # 根据母语选择提示语言
            if use_english_prompt:
                prompt_content = f'''
                Based on the following user information, please estimate the number of weeks needed to achieve the learning goals and create a total learning plan to study the {target_language_name} language for a {native_language_name} speaker. 
                When creating the learning plan, consider the user's learning purpose.
                If the user wants comprehensive improvement/travel/work, base the learning content on various real-life conversation scenarios.
                If the user wants to pass tests like TOEFL, IELTS, SAT, etc., follow the test outline to create learning content.
                If the user wants to learn about history, literature, art, or other knowledge, follow the knowledge outline of that field to create learning content.
                If the user just wants to learn a new language, follow the {target_language_name} country's most widely used textbooks to create learning content.
                
                {user_profile}
                
                Please consider the following factors:
                1. The user's starting point (current {target_language_name} level) and the user's age
                2. The difficulty and number of learning goals
                3. Daily study time invested
                4. General learning curve and progress
                5. Create a maximum 4-week learning plan, calculating 7 days of study per week. If there is too much content to learn, prioritize breadth over depth.
                
                Please return in JSON format, without additional information, including an estimated number of weeks (integer) and
                weekly learning content. The learning content should be an array of strings, with each string describing the goals and specific learning content for each week.
                The learning content should focus on common phrases and words used in real scenarios. When setting up real scenarios, try to make them practical and coherent. 
                Include the scenarios in each week's learning content to maintain consistency when generating detailed learning content later. Please use {native_language_name} language.
                JSON Format as follows:
                {{
                "estimated_weeks": 2,  # Example: estimated 2 weeks needed
                "weeks_plan":["",""] # Example: learning content for two weeks, describe by {native_language_name}
                }}
                '''
            else:
                prompt_content = f'''
                请基于以下用户信息，估算达到学习目标所需的周数并制定一个每周的学习内容，制定的学习计划时需要考虑用户的学习目的，
                如用户想要综合提升/旅游/工作，则基于各种实际会用到的会话场景来制定学习内容，
                如用户想要通过托福、雅思、SAT等考试，则需要按照该考试的考察内容大纲来制定学习内容，
                如用户想要顺便学习点历史、文学、艺术等其他知识，则需要按照该领域的知识大纲来制定学习内容：
                
                当前英语水平：{user_profile.get('english_level')}
                学习目标：{', '.join(user_profile.get('learning_goals', []))}
                每日学习时间：{user_profile.get('study_time_per_day')}分钟
                
                请考虑以下因素：
                1. 用户的起点（当前英语水平）
                2. 学习目标的难度和数量
                3. 每日投入的学习时间
                4. 一般学习曲线和进度
                5. 最长制定4周的学习计划，每周持7天都学习来计算，如果需要学习的内容实在太多，则广度优先，深度次之。
                
                请以json格式返回，无需其他信息，包含一个预计所需的周数（整数）和
                每周的学习内容，学习内容为一个字符串数组，字符串中描述每一周的目标和具体的学习内容，
                学习内容尽量按照实际场景中会用到的常用句式，单词为主, 设定实际场景时尽量贴近实际且具备连贯性。将设定写在每周的学习内容中方便后续每周生成细节的学习内容时设定保持一致
                格式如下
                {{
                "estimated_weeks": 2,  # 示例：预计需要2周,
                "weeks_plan":["",""] # 示例：写了两周的学习内容
                }}
                '''
            
            estimate_prompt = {
                "role": "user",
                "content": prompt_content
            }
            
            result = await self.llm.structured_chat([estimate_prompt])
            result['start_date'] = datetime.now()
            return result 
            
        except Exception as e:
            raise Exception(f"Study duration estimation failed: {str(e)}")

    async def generate_weekly_plan(self, user_profile: Dict, native_lang: str = "", learning_lang: str = "en-US") -> List[Dict]:
        """
        根据用户档案生成每周学习计划
        
        参数:
            user_profile: 用户档案
            native_lang: 用户母语，默认为"cmn-CN"（中文）
            learning_lang: 学习语言，默认为"en-US"（英语）
        """
        try:
            use_english_prompt = True
            if native_lang == "":
                native_lang = "cmn-CN"
                use_english_prompt = False
            # 获取语言名称
            native_language_name = self.get_language_name(native_lang)
            target_language_name = self.get_language_name(learning_lang)

            output_format = '''
            Generate a JSON array containing 7 daily lesson plans. please use {native_language_name} language
            Each day must be an object with these fields:

            1. day_number: integer (1-7)
            2. topic: string (lesson topic)
            3. scenarios: 本课主题可能应用于哪些场景, each containing:
               - title: 场景简单描述
               - content: 场景的详细描述，具体哪些情况下可能遇到
            4. knowledge_points: array of grammar/vocabulary points, each containing:
               - name: point name (e.g., "simple past tense")
               - level: difficulty (1-9)
               - examples: array of example sentences
            5. practice: 学习目标，判断达到本课要求的练习:
               - point: knowledge point to review
               - context: 检验学生掌握知识点的方式
               - difficulty: level (1-9)
            6. estimated_time: integer (days)

            Example:
            [
                {
                    "day_number": 1,
                    "topic": "Using Past Tense to Share Travel Experiences",
                    "scenarios": [
                        {
                            "title": "旅行后的聊天（Casual Conversations）",
                            "content": "朋友或同事之间聊天，分享最近的旅行经历"
                        },
                        {
                            "title": "写旅行日记（Travel Journals）",
                            "content": "记录自己的旅行经历，回忆美好瞬间，在 Instagram、Facebook、微博等社交平台上分享旅行回忆"
                        }
                    ],
                    "knowledge_points": [
                        {
                            "name": "simple past tense in travel narratives",
                            "level": 2,
                            "examples": [
                                "When I first arrived in Beijing, I felt overwhelmed by its size.",
                                "The local guide showed us hidden spots that most tourists never saw.",
                                "We spent three amazing days exploring the ancient temples."
                            ]
                        }
                    ],
                    "practice": [
                        {
                            "point": "past forms of be",
                            "context": "设计几句一般现在时，让学生转为一般过去时。",
                            "difficulty": 3
                        }
                    ],
                    "estimated_time": 45
                }
            ]
            '''

            # 根据母语选择提示语言
            if use_english_prompt:
                prompt_content = f'''
                As an experienced {target_language_name} teacher, please help a {native_language_name} speaker to create a detailed and engaging study plan for this week based on the user input.
                The learning plans may involve history, drawing, music, work, study, etc., but you should find ways to incorporate grammar, sentence patterns, 
                vocabulary, phrases, idioms, language sense, expressions, etc. to achieve the goal of learning through enjoyment. Ensure:
                1. Break down the weekly learning plan into daily learning plans, with practical scenarios for each learning plan
                2. Arrange appropriate review time for learning the content from the previous week
                3. Control the daily learning amount to match the user's time schedule; a lesson can have fewer knowledge points but more practical scenarios for students to practice
                4. If possible, relate the content to the user's interests to increase learning motivation
                5. For review content, design new situations and application scenarios to avoid simple repetition
                ''' + output_format
            else:
                prompt_content = f'''
                作为一名经验丰富的{target_language_name}教师，请根据下面提供的信息，为本周创建一份详细且具有吸引力的学习计划。
                
                学习计划可能是基于历史，绘画，音乐，工作，学习等，但你要想办法将语法，句式，单词，短语，
                习语，语感，表达方式等融入进去达到寓教于乐的目的，确保：
                1. 针对周学习计划细分为日学习计划，每个学习计划设计实用的场景
                2. 适当安排复习时间，学习上一周的内容
                3. 控制每天的学习量符合用户时间安排，一课的知识点可以少安排点，多一些实际的场景，让学生多练习。
                4. 内容如有可能与用户兴趣相关最好，增加学习积极性
                5. 如果是复习内容，设计新的情境和应用场景，避免简单重复
                ''' + output_format
                
            plan_prompt = {
                "role": "system",
                "content": prompt_content
            }

            user_content = {
                "role": "user",
                "content": str(user_profile)
            }

            # Pass the plan_prompt as a message, not inside a list
            return await self.llm.structured_chat([plan_prompt, user_content]) #, model="pkqwq:latest"

        except Exception as e:
            raise Exception(f"Weekly plan generation failed: {str(e)}")

    
   

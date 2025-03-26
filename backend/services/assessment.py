from typing import List, Dict, Optional
from datetime import datetime
from .llm_service import LLMService

class AssessmentService:
    def __init__(self):
        self.llm = LLMService()

    async def conduct_initial_assessment(self, messages: List[Dict]) -> Dict:
        """
        通过对话进行初始评估
        """
        try:
            system_message = {
                "role": "system",
                "content": """
--------Role-------------------
你是一个专业的英语教师。你的工作内容是通过对话尝试收集以下信息，如果学生的对话中没有提供以上信息，你可以尝试引导学生提供。
你的输出必须是一个有效的json格式，引导的对话内容放在speechText字段。

-------Target-------------------
1. user学习英语的目标，需要达到什么程度
2. 每日可用于学习的时间
3. user的个人信息如英语名(如没有则建议用户取一个)，性别，年龄，职业，兴趣爱好等

---------Important----------------------
1. 每次只问1个问题，根据用户的英语水平动态调整表达方式。
2. 如果学生用英语回答，就用英语交流；如果学生用中文，可以用中文引导学生使用英语，这样你才能更好的了解用户实际英语水平
3. 保持专业和友好的态度，尽量简短对话过程以完成信息的收集。
4. 当你收集到所有目标信息或者用户明确表示不想提供这些信息后，在displayText字段中包含 <ASSESSMENT_COMPLETE> 标记：
5. 输出必须是一个有效的json，json格式为：
{
    "speechText": string[], 
    "displayText": str
}
其中, speechText字符串数组，教师说话的内容，为方便语音合成播放，分为一句一句的数组.
displayText字符串，平时为空，收集到足够信息后，输出<ASSESSMENT_COMPLETE>标记.

"""
            }
            
            system_message = {
                "role": "system",
                "content": """
你是一个专业的英语教师，作为帮学生制定英语学习计划的第一步，你需要了解学生的基本情况，如英文名，性别，年龄，职业，兴趣爱好，
以及学习目标，每日可学习的时间。收集过程中尽量鼓励用户使用英文，以方便通过他的回答了解他的英语水平。不要总结收集到的信息，输出必须是一个有效的json，json格式为：
{
    "speechText": string[],  # 字符串数组，教师说话的内容，为方便语音合成播放，分为一句一句的数组
    "displayText": str  # 收集到足够信息后，输出<ASSESSMENT_COMPLETE>标记
}

"""
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

    async def analyze_assessment(self, conversation: List[Dict]) -> Dict:
        """
        分析对话内容，生成用户档案
        """
        try:
            print("\n=== 开始分析对话 ===\n")
            print("原始对话内容：")
            for msg in conversation:
                print(f"Role: {msg['role']}")
                print(f"Content: {msg['content']}")
                print()

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
            last_response = None
            user_inputs = []
            for msg in conversation:
                role = msg["role"]
                content = msg["content"].replace("<ASSESSMENT_COMPLETE>", "").strip()
                formatted_conversation += f"{role}: {content}\n\n"
                
                # 记录用户输入和最后一次助手回复
                if role == "user":
                    user_inputs.append(content)
                elif role == "assistant":
                    last_response = content
            
            print("\n=== 用户输入历史 ===\n")
            for i, input_text in enumerate(user_inputs, 1):
                print(f"输入 {i}: {input_text}")

            analysis_prompt = {
                "role": "system",
                "content": '''你是一个专业的英语教学顾问。你的工作是通过分析学生与教师的对话，生成一份学习者的档案。

你需要从对话内容中提取以下信息：

1. 英语水平：
基于下面的评估系统，你需要确定学生的英语水平。
# 评估系统 - 综合评分模型（基于 CEFR 级别）

| **级别** | **词汇复杂度（Lexical Diversity）** | **语法正确性（Grammar Accuracy）** | **句子连贯性（Coherence & Cohesion）** | **任务完成度（Task Achievement）** |
|------|--------------------------------|-------------------------------|--------------------------------|-------------------------------|
| **A1 (Beginner)** | 使用基础词汇，常见单词，重复较多 | 语法错误较多，简单句为主 | 句子独立，少连接词 | 回答简单，缺乏细节 |
| **A2 (Elementary)** | 使用基础词汇 + 一些短语 | 主要正确，偶尔错误 | 有少量连接词，如 "and", "but" | 回答较完整，但表达有限 |
| **B1 (Intermediate)** | 词汇较多样，能使用同义替换 | 语法基本正确，开始使用从句 | 句子自然流畅，过渡词增加 | 回答完整，表达具体 |
| **B2 (Upper-Intermediate)** | 使用高级词汇（同义替换、抽象词） | 语法准确，能使用复杂句 | 逻辑清晰，使用较多过渡词 | 回答全面，表达清楚，有细节支持 |
| **C1 (Advanced)** | 词汇丰富，偶尔使用专业术语 | 语法准确，掌握高级结构（倒装、虚拟语气） | 句子结构复杂，逻辑严密 | 回答深入，有观点支撑，表达自然 |
| **C2 (Proficient)** | 近母语水平，使用高级词汇、短语动词 | 语法几乎无错误，语法多样性高 | 文章级别连贯性，表达精确 | 观点清晰，表达精准，逻辑强 |

## **示例**
**问题**："Describe your last vacation."  
✅ **A1 级别**："It was good. I liked it." ❌（回答简单，不完整）  
✅ **B2 级别**："I traveled to Italy and visited Rome, Florence, and Venice. The architecture was breathtaking, and I enjoyed trying local pasta dishes." ✅（完整，表达清晰）
---

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
   - 如果时间太长(>90天)，我们则建议将目标分阶段
   - 必须是一个整数，表示天数

输出格式必须是一个有效的 JSON 对象，包含以下字段：
{
    "user_profile": {
        "english_name": string, // 学生的英文名
        "chinese_name": string, // 学生的中文名
        "age": number, // 学生的年龄，未提供则为 0
        "gender": string, // 学生的性别，取值为 "male" 或 "female"
        "career", string, //学生的职业
        "other", string, //其他信息
    }
    "english_level": {
        "lexical_diversity": {
            "text": string,   // 词汇多样性得分描述，如 "使用基础词汇，常见单词，重复较多"
            "score": number // 词汇多样性得分
        },
        "grammar_accuracy": {
            "text": string,   // 语法正确性得分描述，如 "语法错误较多，简单句为主"
            "score": number // 语法正确性得分
        },
        "coherence_cohesion": {
            "text": string,   // 句子连贯性得分描述，如 "句子结构简单，缺乏逻辑性"
            "score": number // 句子连贯性得分
        }, 
        "task_achievement": {
            "text": string,   // 任务完成度得分描述，如 "回答简单，缺乏细节"
            "score": number // 任务完成度得分
        },    
        "overall": {
            "text": string,   // 综合得分描述，如 "A2 级别，语法错误较多，缺乏逻辑性，回答简单，缺乏细节"
            "score": string // 综合得分, 必须为下面中的一个Beginner, Elementary, Intermediate, Upper Intermediate, Advanced, Proficient
        }
    },      
    "interests": string[],       // 兴趣爱好列表，文字描述尽量详细
    "learning_goals": string[],  // 学习目标列表，文字描述尽量详细
    "study_time_per_day": number // 每日学习时间（分钟）
    "total_study_day": number // 预计学习天数
}

请严格按照指定的格式输出，不要添加任何其他字段或注释。'''
            }

            analysis_prompt_user = {
                "role": "user",
                "content": f'''请分析以下对话内容，生成一份学习者档案：

{formatted_conversation}'''
            }


            print("\n=== 发送给 LLM 服务的消息 ===\n")
            messages = [analysis_prompt, analysis_prompt_user]
            for msg in messages:
                print(f"Role: {msg['role']}")
                print(f"Content: {msg['content'][:200]}...")
                print()

            try:
                profile_data = await self.llm.structured_chat(messages)
                
                print("\n=== LLM 返回的数据 ===\n")
                print(profile_data)
                
                # 验证必需字段
                required_fields = ["english_level", "interests", "learning_goals", "study_time_per_day"]
                missing_fields = [field for field in required_fields if field not in profile_data]
                if missing_fields:
                    raise ValueError(f"缺少必需的字段：{', '.join(missing_fields)}")
                
                # 验证字段类型
                if not isinstance(profile_data["english_level"], dict):
                    raise ValueError("english_level 必须是对象")
                if not isinstance(profile_data["interests"], list):
                    raise ValueError("interests 必须是数组")
                if not isinstance(profile_data["learning_goals"], list):
                    raise ValueError("learning_goals 必须是数组")
                if not isinstance(profile_data["study_time_per_day"], (int, float)):
                    raise ValueError("study_time_per_day 必须是数字")
                if not isinstance(profile_data["total_study_day"], (int, float)):
                    raise ValueError("total_study_day 必须是数字")
                
                print("\n=== 验证通过，创建用户档案 ===\n")
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

    async def generate_total_plan(self, user_profile: Dict) -> Dict:
        """
        根据用户档案估算学习时长（周数）
        """
        try:
            estimate_prompt = {
                "role": "user",
                "content": f'''
                请基于以下用户信息，估算达到学习目标所需的周数并按循序渐进的方式制定一个每周的学习内容：
                
                当前英语水平：{user_profile.get('english_level')}
                学习目标：{', '.join(user_profile.get('learning_goals', []))}
                每日学习时间：{user_profile.get('study_time_per_day')}分钟
                
                请考虑以下因素：
                1. 用户的起点（当前英语水平）
                2. 学习目标的难度和数量
                3. 每日投入的学习时间
                4. 一般学习曲线和进度
                
                请以json格式返回，无需其他信息，包含一个预计所需的周数（整数）和
                每周的学习内容，学习内容为一个字符串数组，字符串中描述每一周的目标和具体的学习内容，
                学习内容尽量按照实际场景中会用到的常用句式，单词为主, 设定实际场景时尽量贴近实际且具备连贯性。将设定写在每周的学习内容中方便后续每周生成细节的学习内容时设定保持一致
                格式如下
                {{
                "estimated_weeks": 2  # 示例：预计需要2周,
                "weeks_plan":["",""] # 示例：写了两周的学习内容
            }}
                '''
            }
            
            result = await self.llm.structured_chat([estimate_prompt])
            result['start_date'] = datetime.now()
            return result 
            
        except Exception as e:
            raise Exception(f"Study duration estimation failed: {str(e)}")

    async def generate_weekly_plan(self, user_profile: Dict) -> List[Dict]:
        """
        根据用户档案生成每周学习计划
        @param phase: 当前学习阶段（周数）
        """
        try:            
            # 获取上一周的评估结果（如果有）
            last_assessment = None
            if user_profile.get('completed_phases'):
                last_assessment = user_profile['completed_phases']
            
            # 根据评估结果调整计划重点
            focus_areas = []
            review_topics = []
            recommended_activities = []
            
            if last_assessment:
                # 添加需要加强的领域
                focus_areas.extend(last_assessment.get('areas_to_improve', []))
                
                # 从主要进展中提取已掌握的内容作为复习主题
                review_topics.extend(last_assessment.get('progress', []))
                
                # 获取评估建议中的活动建议
                if 'recommendations' in last_assessment:
                    recommended_activities.extend(
                        [rec for rec in last_assessment['recommendations'] 
                         if any(keyword in rec.lower() 
                             for keyword in ['练习', '尝试', '进行', '使用', '观看'])])
            
            # Get current learning progress and points to review
            current_points = user_profile.get('learning_progress', {}).get('current_points', []) if user_profile.get('learning_progress') else []
            review_points = []
            if user_profile.get('learning_progress') and user_profile.get('learning_progress', {}).get('mastered_points'):
                for point, mastery in user_profile.get('learning_progress', {}).get('mastered_points', {}).items():
                    if mastery < 80:  # Points with mastery below 80% need review
                        review_points.append(point)

            plan_prompt = {
                "role": "user",
                "content": f'''
                As an experienced English teacher, please create a detailed and engaging study plan for this week. Focus on using authentic, memorable content that naturally demonstrates language points.

                User Profile:
                - English Level: {user_profile.get('english_level')}
                - Interests: {', '.join(user_profile.get('interests', []))}
                - Learning Goals: {', '.join(user_profile.get('learning_goals', []))}
                - Daily Study Time: {user_profile.get('study_time_per_day')} minutes

                Current Learning Status:
                - Current Week plan: {user_profile.get('current_week_plan')}
                - Last Assessment: {user_profile.get('last_assessment')}
                
                请根据以上信息，生成针对性的每日学习计划。学习计划可能是语法，句式，单词，短语，习语，语感，表达方式等，确保：
                1. 针对周学习计划细分为日学习计划，每个学习计划设计实用的场景
                2. 适当安排复习时间，学习上一周的内容
                3. 控制每天的学习量符合用户时间安排，一课的知识点可以少安排点，多一些场景，让学生多练习。
                4. 内容如有可能与用户兴趣相关最好，增加学习积极性
                5. 如果是复习内容，设计新的情境和应用场景，避免简单重复
                '''
            }

            output_format = '''
            Generate a JSON array containing 7 daily lesson plans. Each day must be an object with these fields:

            1. day_number: integer (1-7)
            2. topic: string (lesson topic)
            3. scenarios: 本课主题可能应用于哪些场景, each containing:
               - title: 场景简单描述
               - content: 场景的详细描述，具体哪些情况下可能遇到
            4. knowledge_points: array of grammar/vocabulary points, each containing:
               - name: point name (e.g., "simple past tense")
               - level: difficulty (1-5)
               - examples: array of example sentences
            5. practice: 学习目标，判断达到本课要求的练习:
               - point: knowledge point to review
               - context: 检验学生掌握知识点的方式
               - difficulty: level (1-5)
            6. estimated_time: integer (minutes)

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

            return await self.llm.structured_chat([plan_prompt], output_format) #, model="pkqwq:latest"

        except Exception as e:
            raise Exception(f"Weekly plan generation failed: {str(e)}")

    def _format_completed_phases(self, completed_phases: Optional[List[Dict]]) -> str:
        """
        格式化已完成阶段的信息用于提示
        """
        if not completed_phases:
            return "尚未完成任何学习阶段。"
            
        result = "已完成的学习阶段：\n"
        for phase in completed_phases:
            result += f"- 第 {phase.get('phase_number')} 周：\n"
            result += f"  评估结果：{phase.get('assessment')}\n"
            result += f"  主要进展：{', '.join(phase.get('progress', []))}\n"
            result += f"  需要加强：{', '.join(phase.get('areas_to_improve', []))}\n"
        return result
    
    async def assess_weekly_progress(self, user_profile: Dict, weekly_report: Dict) -> Dict:
        """
        评估一周的学习进度
        @param weekly_report: 包含用户一周学习情况的报告
        """
        try:
            assessment_prompt = {
                "role": "user",
                "content": f'''
                请基于以下信息评估学习者本周的学习情况：
                
                学习者信息：
                - 英语水平：{user_profile.get('english_level')}
                - 学习目标：{', '.join(user_profile.get('learning_goals', []))}
                - 当前阶段：第 {user_profile.get('current_phase')} 周
                
                本周学习报告：
                - 完成的任务：{', '.join(weekly_report.get('completed_tasks', []))}
                - 学习时长：{weekly_report.get('total_study_time')}分钟
                - 遇到的困难：{', '.join(weekly_report.get('difficulties', []))}
                - 自评表现：{weekly_report.get('self_assessment')}
                
                请提供详细的评估报告，包括：
                1. 本周的主要进展
                2. 需要加强的领域
                3. 对下周学习的建议
                4. 是否需要调整学习计划
                '''
            }
            
            output_format = '''
            请返回一个包含以下字段的 JSON 对象：
            {
                "progress": ["进展1", "进展2"],  # 字符串数组，表示主要进展
                "areas_to_improve": ["领域1", "领域2"],  # 字符串数组，表示需要加强的领域
                "recommendations": ["建议1", "建议2"],  # 字符串数组，表示具体建议
                "plan_adjustment_needed": false,  # 布尔值，是否需要调整计划
                "assessment": "总体评估"  # 字符串，总体评估结果
            }
            '''
            
            assessment_result = await self.llm.structured_chat([assessment_prompt], output_format)
            
            # 更新用户档案
            if not user_profile.get('completed_phases'):
                user_profile['completed_phases'] = []
                
            user_profile['completed_phases'].append({
                "phase_number": user_profile.get('current_phase'),
                "assessment": assessment_result["assessment"],
                "progress": assessment_result["progress"],
                "areas_to_improve": assessment_result["areas_to_improve"],
                "date": datetime.now()
            })
            
            user_profile['last_assessment_date'] = datetime.now()
            user_profile['current_phase'] += 1
            
            return assessment_result
            
        except Exception as e:
            raise Exception(f"Weekly progress assessment failed: {str(e)}")

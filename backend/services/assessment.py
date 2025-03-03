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
                "content": """你是一个专业的英语教师，正在与学生进行初次交谈。

你需要收集以下信息：
1. 学生的英语水平（初级、中级或高级）
2. 学生的兴趣爱好（至少一个具体的例子）
3. 学习英语的目标（具体的应用场景）
4. 每日可用于学习的时间

你需要遵守以下规则：
1. 不要一次性问太多问题，每次只问 1-2 个问题
2. 先了解学生的英语水平，可以从具体场景入手，比如看电影时是否需要字幕
3. 如果学生用英语回答，就用英语交流；如果用中文，就先用中文，然后逐步引导使用英语
4. 当学生表达有困难时，可以用中文进行辅助解释
5. 保持专业和友好的态度

只有当你收集到以下所有信息后，才能在回复中包含 <ASSESSMENT_COMPLETE> 标记：
1. 能够确定学生的英语水平
2. 学生提供了至少一个具体的兴趣爱好
3. 学生说明了具体的学习目标
4. 学生提供了每日可用于学习的时间

例如，如果学生说“我想学英语，主要是为了看电影和玩游戏”，你可以这样回答：

“很高兴你对看英语电影和游戏感兴趣！这些都是很好的学习方式。你能告诉我，你看英语电影时需要中文字幕吗？”"""
            }
            
            all_messages = [system_message] + messages
            return await self.llm.chat_completion(all_messages)

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
   - 从学生的表达方式、语言选择和自我描述中判断
   - 如果学生自己描述了水平，优先使用学生的描述
   - 必须是以下三个值之一：beginner、intermediate、advanced

2. 兴趣爱好：
   - 列出学生提到的所有兴趣爱好
   - 如果提到了具体的电影或游戏名称，也要包含在内
   - 如果提到了职业相关的兴趣，也要包含

3. 学习目标：
   - 列出学生明确表达的所有学习目标
   - 如果提到了具体的场景（如写报告、做演示），要包含这些细节

4. 偏好的交流语言：
   - 根据学生的语言选择和实际使用情况判断
   - 如果学生主动选择了某种语言，优先使用学生的选择
   - 必须是以下两个值之一：zh、en

5. 每日学习时间：
   - 使用学生提供的具体时间
   - 如果学生没有提供，根据学生的学习目标和兴趣爱好推荐合适的时长
   - 必须是一个整数，表示分钟数

输出格式必须是一个有效的 JSON 对象，包含以下字段：
{
    "english_level": string,      // beginner, intermediate, 或 advanced
    "interests": string[],       // 兴趣爱好列表
    "learning_goals": string[],  // 学习目标列表
    "preferred_language": string, // zh 或 en
    "study_time_per_day": number // 每日学习时间（分钟）
}

请严格按照指定的格式输出，不要添加任何其他字段或注释。'''
            }

            analysis_prompt_user = {
                "role": "user",
                "content": f'''请分析以下对话内容，生成一份学习者档案：

{formatted_conversation}'''
            }

            output_format = '''请生成一个包含以下字段的 JSON 对象：

1. english_level: 学习者的英语水平，必须是以下三个值之一：
   - "beginner": 初学者
   - "intermediate": 中级水平
   - "advanced": 高级水平

2. interests: 学习者的兴趣爱好列表，必须是字符串数组

3. learning_goals: 学习者的学习目标列表，必须是字符串数组

4. preferred_language: 学习者偏好的交流语言，必须是以下两个值之一：
   - "zh": 中文
   - "en": 英文

5. study_time_per_day: 建议的每日学习时间，必须是一个整数，表示分钟数

示例输出：
{
    "english_level": "beginner",
    "interests": ["movies", "games"],
    "learning_goals": ["daily communication", "entertainment"],
    "preferred_language": "zh",
    "study_time_per_day": 30
}'''

            format_message = {
                "role": "system",
                "content": '''你是一个JSON格式化工具。你的工作是将用户输入转换为指定的JSON格式。

输出必须是一个有效的 JSON 对象，包含以下字段：
1. english_level: 只能是 "beginner"、"intermediate" 或 "advanced"
2. interests: 字符串数组
3. learning_goals: 字符串数组
4. preferred_language: 只能是 "zh" 或 "en"
5. study_time_per_day: 整数

请严格按照这个格式输出，不要添加任何其他字段或注释。'''
            }

            print("\n=== 发送给 LLM 服务的消息 ===\n")
            messages = [analysis_prompt, analysis_prompt_user, format_message]
            for msg in messages:
                print(f"Role: {msg['role']}")
                print(f"Content: {msg['content'][:200]}...")
                print()

            print("\n=== 输出格式 ===\n")
            print(output_format)

            try:
                profile_data = await self.llm.structured_chat(messages, output_format)
                
                print("\n=== LLM 返回的数据 ===\n")
                print(profile_data)
                
                # 验证必需字段
                required_fields = ["english_level", "interests", "learning_goals", "preferred_language", "study_time_per_day"]
                missing_fields = [field for field in required_fields if field not in profile_data]
                if missing_fields:
                    raise ValueError(f"缺少必需的字段：{', '.join(missing_fields)}")
                
                # 验证字段类型
                if not isinstance(profile_data["english_level"], str):
                    raise ValueError("english_level 必须是字符串")
                if not isinstance(profile_data["interests"], list):
                    raise ValueError("interests 必须是数组")
                if not isinstance(profile_data["learning_goals"], list):
                    raise ValueError("learning_goals 必须是数组")
                if not isinstance(profile_data["preferred_language"], str):
                    raise ValueError("preferred_language 必须是字符串")
                if not isinstance(profile_data["study_time_per_day"], (int, float)):
                    raise ValueError("study_time_per_day 必须是数字")
                
                # 验证字段值
                valid_levels = ["beginner", "intermediate", "advanced"]
                if profile_data["english_level"].lower() not in valid_levels:
                    raise ValueError(f"english_level 必须是以下值之一：{', '.join(valid_levels)}")
                
                valid_languages = ["zh", "en"]
                if profile_data["preferred_language"].lower() not in valid_languages:
                    raise ValueError(f"preferred_language 必须是以下值之一：{', '.join(valid_languages)}")
                
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

    async def estimate_study_duration(self, user_profile: Dict) -> int:
        """
        根据用户档案估算学习时长（周数）
        """
        try:
            estimate_prompt = {
                "role": "user",
                "content": f'''
                请基于以下用户信息，估算达到学习目标所需的周数：
                
                当前英语水平：{user_profile.get('english_level')}
                学习目标：{', '.join(user_profile.get('learning_goals', []))}
                每日学习时间：{user_profile.get('study_time_per_day')}分钟
                
                请考虑以下因素：
                1. 用户的起点（当前英语水平）
                2. 学习目标的难度和数量
                3. 每日投入的学习时间
                4. 一般学习曲线和进度
                
                请返回一个预计所需的周数（整数）。'''
            }
            
            result = await self.llm.structured_chat([estimate_prompt], '''{
                "estimated_weeks": 12  # 示例：预计需要12周
            }''')
            return result.get('estimated_weeks', 12)  # 如果无法获取估计值，默认返回12周
            
        except Exception as e:
            raise Exception(f"Study duration estimation failed: {str(e)}")

    async def generate_weekly_plan(self, user_profile: Dict, phase: int = 1) -> List[Dict]:
        """
        根据用户档案生成每周学习计划
        @param phase: 当前学习阶段（周数）
        """
        try:
            # 如果是第一次生成计划，估算总学习时长并更新用户档案
            if phase == 1 and not user_profile.get('estimated_completion_weeks'):
                user_profile['estimated_completion_weeks'] = await self.estimate_study_duration(user_profile)
                user_profile['start_date'] = datetime.now()
                user_profile['current_phase'] = 1
                user_profile['completed_phases'] = []
            
            # 获取上一周的评估结果（如果有）
            last_assessment = None
            if user_profile.get('completed_phases'):
                last_assessment = user_profile['completed_phases'][-1]
            
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
                As an experienced English teacher, please create a detailed and engaging study plan for week {phase}. Focus on using authentic, memorable content that naturally demonstrates language points.

                User Profile:
                - English Level: {user_profile.get('english_level')}
                - Interests: {', '.join(user_profile.get('interests', []))}
                - Learning Goals: {', '.join(user_profile.get('learning_goals', []))}
                - Daily Study Time: {user_profile.get('study_time_per_day')} minutes
                - Current Week: {phase} of {user_profile.get('estimated_completion_weeks')}

                Current Learning Status:
                - Active Knowledge Points: {', '.join(current_points)}
                - Points Needing Review: {', '.join(review_points)}

                Guidelines for Material Selection:
                1. Choose specific, memorable scenes from movies/TV shows that clearly demonstrate the target language points
                   Example: "The scene where Rachel explains to Monica about her first day at work, showing natural use of past tense"

                2. Select article excerpts that tell engaging stories
                   Example: "The author's vivid description of experiencing Japanese tea ceremony for the first time"

                3. Pick content that connects emotionally or practically with the learner
                   Example: For a business-focused learner, use scenes from workplace settings

                4. When reviewing grammar points, present them in new, interesting contexts and specify scenarios
                   Example: Practice past tense through travel stories (scenario: "When sharing vacation experiences in casual conversations"), 
                   or business achievements (scenario: "When discussing past projects in job interviews")

                5. Ensure materials build upon each other throughout the week
                   Example: Monday's vocabulary appears in Tuesday's reading, which prepares for Wednesday's discussion
                
                上周评估结果：
                {f"无" if not last_assessment else f"""需要加强的领域：
                {', '.join(focus_areas)}
                
                已有进展（需要复习巩固）：
                {', '.join(review_topics)}
                
                建议的学习活动：
                {', '.join(recommended_activities)}"""}
                
                请根据以上信息，特别是上周的评估结果，生成针对性的每日学习计划。确保：
                1. 优先关注需要加强的领域，设计专门的练习活动
                2. 适当安排复习时间，巩固已有进展
                3. 采用建议的学习活动，并根据实际情况调整和扩展
                4. 难度循序渐进，每天的学习量符合用户时间安排
                5. 内容要与用户兴趣相关，增加学习积极性
                6. 如果是复习内容，设计新的情境和应用场景，避免简单重复
                '''
            }

            output_format = '''
            Generate a JSON array containing 7 daily lesson plans. Each day must be an object with these fields:

            1. day_number: integer (1-7)
            2. topic: string (lesson topic)
            3. materials: array of learning materials, each containing:
               - type: material type (movie/book/article)
               - title: specific title (e.g., "Friends Season 1")
               - segment: specific segment (e.g., "Episode 3 15:20-18:30")
               - content: exact content (dialogue/text)
            4. knowledge_points: array of grammar/vocabulary points, each containing:
               - name: point name (e.g., "simple past tense")
               - level: difficulty (1-5)
               - examples: array of example sentences
               - exercises: array of practice exercises
               - scenario: string describing when and where to use this point (e.g., "When telling stories about past experiences in job interviews")
            5. review_activities: array of review tasks, each containing:
               - point: knowledge point to review
               - context: new practice context
               - difficulty: level (1-5)
            6. estimated_time: integer (minutes)

            Example:
            [
                {
                    "day_number": 1,
                    "topic": "Using Past Tense to Share Travel Experiences",
                    "materials": [
                        {
                            "type": "movie",
                            "title": "Friends Season 1",
                            "segment": "Ross tells his friends about his trip to China (Episode 3: The One with the Thumb)",
                            "content": "A heartwarming scene where Ross shares his travel experiences with his friends, using various past tense forms naturally in conversation. The scene perfectly demonstrates how past tense is used in storytelling and responding to questions."
                        },
                        {
                            "type": "article",
                            "title": "National Geographic: The Hidden Cities of Asia",
                            "segment": "The opening story about the author's first visit to Beijing's Forbidden City",
                            "content": "A vivid first-person narrative where the author describes their awe-inspiring first visit to the Forbidden City, rich with descriptive past tense usage and cultural insights."
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
                            ],
                            "exercises": [
                                "Share your own travel story using the scene as inspiration",
                                "Role-play: Interview a friend about their recent trip",
                                "Write a postcard about a memorable travel experience"
                            ]
                        }
                    ],
                    "review_activities": [
                        {
                            "point": "past forms of be",
                            "context": "Describing your old neighborhood and how it has changed",
                            "difficulty": 3,
                            "prompt": "Think about where you grew up: What was your street like? What were your neighbors like? How was the community different from now?"
                        }
                    ],
                    "estimated_time": 45
                }
            ]
            '''

            return await self.llm.structured_chat([plan_prompt], output_format)

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

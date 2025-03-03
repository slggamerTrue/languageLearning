import asyncio
import os
from dotenv import load_dotenv
from services.lesson import LessonService, LessonMode

# 加载环境变量
load_dotenv()

async def test_interactive_lesson():
    lesson_service = LessonService()
    
    # 测试数据：模拟一天的评估数据
    sample_assessment_day = {
        "day_number": 1,
        "topic": "Using Business Language in Presentations",
        "materials": [
            {
                "type": "movie",
                "title": "The Social Network",
                "segment": "Mark Zuckerberg pitches Facebook to investors",
                "content": "In this scene, Mark Zuckerberg gives a compelling presentation that includes key business concepts and vocabulary."
            }
        ],
        "knowledge_points": [
            {
                "name": "business terminology",
                "level": 2,
                "examples": [
                    "Market share: the percentage of a market that is controlled by one company.",
                    "Revenue: money earned from selling products or services.",
                    "Equity: ownership in a company"
                ],
                "exercises": [
                    "List five business terms you heard and explain their meanings",
                    "Role-play: pitch an imaginary product to a friend using the language you learned"
                ]
            }
        ],
        "review_activities": [
            {
                "point": "business email writing",
                "context": "Writing a follow-up email after the presentation",
                "difficulty": 2
            }
        ],
        "estimated_time": 45
    }

    async def simulate_lesson(mode: LessonMode, mode_name: str):
        print(f"\n=== Testing {mode_name} Mode ===\n")
        try:
            # 创建课程
            if mode == LessonMode.STUDY:
                lesson = await lesson_service.create_lesson(sample_assessment_day, mode)
            else:
                # 练习模式使用特定的场景设置
                practice_lesson = {
                    "mode": mode.value,
                    "topic": "Business Performance Review",
                    "scene": {
                        "description": "这是一个定期的业务评审会议，主要讨论公司的市场表现和营收情况。",
                        "your_role": "你是一位高级经理，负责评估和提出问题。",
                        "student_role": "学生是一位产品经理，正在汇报产品的市场表现。",
                        "additional_info": "会议时间是30分钟，需要包含市场份额、营收和利润等数据。",
                        "current_situation": "会议刚刚开始，产品经理准备开始汇报。"
                    }
                }
                lesson = practice_lesson
            
            print(f"\n{mode_name} 课程内容已生成：")
            print(f"模式: {lesson['mode']}")
            print(f"主题: {lesson.get('topic', 'Missing topic')}")
            if 'scene' in lesson:
                print("\n场景设置：")
                print(f"场景描述: {lesson['scene']['description']}")
                print(f"角色设定: {lesson['scene']['your_role']}")
            
            # 开始上课
            print("\n=== 开始上课 ===\n")
            
            # 课程开场
            response = await lesson_service.conduct_lesson(lesson)
            print("\n老师：")
            print(response["content"])
            
            # 模拟多轮对话来测试对话历史和总结功能
            if mode == LessonMode.STUDY:
                # 学习模式的问题
                questions = [
                    # 第一轮：应用场景
                    "能再详细解释一下market share这个概念吗？",
                    "market share和market size有什么区别？",
                    "能给个具体的例子吗？",
                    "我明白了，我们可以进入下一个知识点了",
                    
                    # 第二轮：营收和利润
                    "revenue和profit有什么区别？",
                    "能用一个实际的例子来解释吗？",
                    "如果我要在演讲中提到这两个概念，应该怎么说？",
                    "我明白了，这两个概念的区别",
                    
                    # 第三轮：股权
                    "能解释一下equity这个概念吗？",
                    "为什么创业公司经常会给员工equity？",
                    "能用一个简单的例子来解释吗？",
                    "我大概明白了，但还是有点困惑"
                ]
            else:
                # 练习模式 - 模拟业务评审会议
                questions = [
                    # 开场白
                    "Good morning everyone. I'm John from the Product team. Today I'll be presenting our Q4 market performance.",
                    
                    # 市场份额
                    "Our product has shown strong performance in Q4. We've increased our market share from 15% to 25%.",
                    "This growth was primarily driven by our expansion into the enterprise segment.",
                    
                    # 对问题的回应
                    "Yes, we've identified some challenges in the SMB market. We're working on a new pricing strategy.",
                    
                    # 营收数据
                    "Looking at revenue, we achieved $10M in Q4, up 30% year-over-year.",
                    "Our profit margin is now at 15%, thanks to improved operational efficiency.",
                    
                    # 总结
                    "That concludes my presentation. Happy to take any questions."
                ]
            
            # 进行互动对话
            print("\n=== 开始互动对话 ===\n")
            for i, question in enumerate(questions, 1):
                print(f"\n--- 第 {i} 轮对话 ---")
                print("\n学生：", question)
                response = await lesson_service.conduct_lesson(lesson, question)
                print("\n老师：")
                print(response["content"])
                
                # 每4轮对话显示一次对话历史长度
                if i % 4 == 0:
                    print(f"\n当前对话历史长度：{len(lesson_service.conversation_history)} 条消息")
                    
                # 如果超过最大对话轮数，显示总结信息
                if len(lesson_service.conversation_history) >= lesson_service.max_conversation_turns * 2:
                    print("\n=== 对话已达到上限，已自动总结 ===\n")
                    # 显示最新的总结（在conversation_history的第二条消息中）
                    if len(lesson_service.conversation_history) > 1:
                        print(lesson_service.conversation_history[1]["content"])
            
            print("\n课程互动测试成功！")
            return lesson
            
        except Exception as e:
            print(f"测试失败: {str(e)}")
            raise e

    # 测试学习模式
    study_lesson = await simulate_lesson(LessonMode.STUDY, "Study")
    
    # 测试练习模式
    practice_lesson = await simulate_lesson(LessonMode.PRACTICE, "Practice")
    
    return study_lesson, practice_lesson

async def interactive_lesson(mode: LessonMode):
    lesson_service = LessonService()
    
    if mode == LessonMode.PRACTICE:
        # 练习模式使用特定的场景设置
        lesson = {
            "mode": mode.value,
            "topic": "Job Interview Practice",
            "scene": {
                "description": "这是一个产品经理职位的面试。",
                "your_role": "你是一位面试官，是产品部门的高级经理。",
                "student_role": "学生是一位应聘产品经理职位的候选人。",
                "additional_info": "公司是一家成长期的科技公司，主要产品是企业SaaS软件。",
                "current_situation": "面试即将开始，候选人已经就座。"
            }
        }
    else:
        # 学习模式使用默认课程
        lesson = await lesson_service.create_lesson(sample_assessment_day, mode)
    
    print(f"\n=== 开始{mode.value}模式课程 ===\n")
    print(f"主题: {lesson['topic']}")
    if 'scene' in lesson:
        print("\n场景设置：")
        print(f"场景描述: {lesson['scene']['description']}")
        print(f"你的角色: {lesson['scene']['student_role']}")
        print(f"其他信息: {lesson['scene']['additional_info']}")
    
    # 开始上课
    print("\n=== 开始对话 ===\n")
    response = await lesson_service.conduct_lesson(lesson)
    print("\n老师/面试官：")
    print(response["content"])
    
    # 交互对话
    while True:
        try:
            user_input = input("\n你: ")
            if user_input.lower() in ['exit', 'quit', '退出']:
                print("\n课程结束！")
                break
                
            response = await lesson_service.conduct_lesson(lesson, user_input)
            print("\n老师/面试官：")
            print(response["content"])
            
            # 显示对话历史长度
            if len(lesson_service.conversation_history) % 6 == 0:
                print(f"\n当前对话历史长度：{len(lesson_service.conversation_history)} 条消息")
                
        except KeyboardInterrupt:
            print("\n课程被中断！")
            break
        except Exception as e:
            print(f"\n错误: {str(e)}")
            break

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        # 交互模式
        mode = LessonMode.PRACTICE  # 默认使用 Practice 模式
        if len(sys.argv) > 2:
            mode = LessonMode.STUDY if sys.argv[2].lower() == "study" else LessonMode.PRACTICE
        asyncio.run(interactive_lesson(mode))
    else:
        # 运行测试
        asyncio.run(test_interactive_lesson())

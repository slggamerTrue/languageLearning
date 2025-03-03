import asyncio
import os
from dotenv import load_dotenv
from services.assessment import AssessmentService
from models.user import UserProfile

# 加载环境变量
load_dotenv()

async def test_initial_assessment():
    assessment_service = AssessmentService()
    
    async def run_assessment_scenario(scenario_name: str, initial_message: str):
        print(f"\n=== {scenario_name} ===\n")
        try:
            # 初始化对话
            messages = [
                {"role": "user", "content": initial_message}
            ]

            # 进行对话直到收集到足够信息
            assessment_complete = False
            while not assessment_complete:
                response = await assessment_service.conduct_initial_assessment(messages)
                print("对话进展：")
                print(messages)

                if "<ASSESSMENT_COMPLETE>" in response["content"]:
                    assessment_complete = True
                    messages.append(response)
                    print("评估完成：")
                    print(messages)
                else:
                    messages.append(response)
                    # 根据对话进展模拟用户回答
                    if len(messages) == 2:  # 第一轮回答
                        if "zh" in initial_message:
                            messages.append({"role": "user", "content": "我是初学者，喜欢看电影和玩游戏。希望每天能学习半小时左右。"})
                        else:
                            messages.append({"role": "user", "content": "I'm at an intermediate level. I work in tech and need to improve my business communication. I can study for about 30 minutes daily."})
                    elif len(messages) == 4:  # 第二轮回答
                        if "zh" in initial_message:
                            messages.append({"role": "user", "content": "我的目标是能看懂英文电影和游戏，将来可以和外国朋友交流。"})
                        else:
                            messages.append({"role": "user", "content": "I want to improve my business writing and presentation skills, as I often need to communicate with international clients."})
                    else:
                        assessment_complete = True  # 防止无限循环

            # 分析用户档案
            user_profile = await assessment_service.analyze_assessment(messages)
            print("\n用户档案分析：")
            print(f"英语水平: {user_profile.english_level}")
            print(f"兴趣爱好: {', '.join(user_profile.interests)}")
            print(f"学习目标: {', '.join(user_profile.learning_goals)}")
            print(f"偏好语言: {user_profile.preferred_language}")
            print(f"每日学习时间: {user_profile.study_time_per_day}分钟")

            # 生成每周学习计划
            weekly_plan = await assessment_service.generate_weekly_plan(user_profile)
            print("\n每周学习计划：\n")
            for day in weekly_plan:
                print(f"第{day['day_number']}天:")
                print(f"主题: {day['topic']}")
                if 'materials' in day:
                    print("学习材料:")
                    for material in day['materials']:
                        print(f"  - {material['type']}: {material['title']}")
                        if 'segment' in material:
                            print(f"    片段: {material['segment']}")
                        if 'content' in material:
                            print(f"    内容: {material['content']}")
                if 'knowledge_points' in day:
                    print("知识要点:")
                    for point in day['knowledge_points']:
                        print(f"  - {point['name']} (难度等级: {point['level']})")
                        if 'examples' in point:
                            print(f"    例句: {', '.join(point['examples'])}")
                        if 'exercises' in point:
                            print(f"    练习: {', '.join(point['exercises'])}")
                if 'review_activities' in day:
                    print(f"复习活动: {', '.join(day['review_activities'])}")
                print(f"预计学习时间: {day['estimated_time']}分钟\n")

        except Exception as e:
            print(f"测试过程中出现错误: {str(e)}")

    # 运行两个测试场景
    await run_assessment_scenario("测试场景1：初学者评估", "我想学英语，主要是为了看电影和玩游戏。")
    await run_assessment_scenario("Test Scenario 2: Intermediate Learner Assessment", "I'd like to improve my business English, especially for writing reports and giving presentations.")

async def test_learning_plan_and_progress():
    print("\n=== 测试学习计划生成和进度评估 ===\n")
    assessment_service = AssessmentService()
    
    # 创建测试用户档案
    user_profile = UserProfile(
        english_level="intermediate",
        interests=["business", "technology", "movies"],
        learning_goals=["improve business communication", "give presentations", "write reports"],
        preferred_language="en",
        study_time_per_day=45
    )
    
    try:
        # 1. 估算学习时长
        print("1. 估算总学习时长...")
        weeks = await assessment_service.estimate_study_duration(user_profile)
        print(f"预计需要 {weeks} 周完成学习目标\n")
        
        # 2. 生成第一周学习计划
        print("2. 生成第一周学习计划...")
        week1_plan = await assessment_service.generate_weekly_plan(user_profile, phase=1)
        print("第一周学习计划：")
        for day in week1_plan:
            print(f"\n第{day['day_number']}天:")
            print(f"主题: {day['topic']}")
            if 'materials' in day:
                print("学习材料:")
                for material in day['materials']:
                    print(f"  - {material['type']}: {material['title']}")
                    if 'segment' in material:
                        print(f"    片段: {material['segment']}")
                    if 'content' in material:
                        print(f"    内容: {material['content']}")
            if 'knowledge_points' in day and day['knowledge_points']:
                print("知识要点:")
                for point in day['knowledge_points']:
                    print(f"  - {point['name']} (难度等级: {point['level']})")
                    if 'examples' in point and point['examples']:
                        print(f"    例句: {', '.join(point['examples'])}")
                    if 'exercises' in point and point['exercises']:
                        print(f"    练习: {', '.join(point['exercises'])}")
            if 'review_activities' in day:
                print("复习活动:")
                for activity in day['review_activities']:
                    if isinstance(activity, dict):
                        print(f"  - {activity['point']} (难度等级: {activity['difficulty']})")
                        print(f"    场景: {activity['context']}")
                        if 'prompt' in activity:
                            print(f"    任务: {activity['prompt']}")
                    else:
                        print(f"  - {activity}")
            print(f"预计学习时间: {day['estimated_time']}分钟")
        
        # 3. 模拟第一周学习报告
        print("\n3. 提交第一周学习报告...")
        week1_report = {
            "completed_tasks": [
                "完成商务邮件写作练习",
                "观看3个商务演讲视频",
                "进行2次模拟演讲",
                "学习50个商务词汇"
            ],
            "total_study_time": 300,  # 本周总学习时间（分钟）
            "difficulties": [
                "演讲时的语音语调不够自然",
                "商务词汇使用不够准确"
            ],
            "self_assessment": "整体完成度80%，对商务邮件写作有了更好的理解，但演讲技巧还需要加强"
        }
        
        # 4. 评估第一周进度
        print("4. 评估第一周学习进度...")
        assessment_result = await assessment_service.assess_weekly_progress(user_profile, week1_report)
        print("\n评估结果：")
        print(f"主要进展: {', '.join(assessment_result['progress'])}")
        print(f"需要加强: {', '.join(assessment_result['areas_to_improve'])}")
        print(f"建议: {', '.join(assessment_result['recommendations'])}")
        print(f"是否需要调整计划: {assessment_result['plan_adjustment_needed']}")
        print(f"总体评估: {assessment_result['assessment']}")
        
        # 5. 生成第二周计划（基于评估结果）
        print("\n5. 生成第二周学习计划...")
        week2_plan = await assessment_service.generate_weekly_plan(user_profile, phase=2)
        print("第二周学习计划：")
        for day in week2_plan:
            print(f"\n第{day['day_number']}天:")
            print(f"主题: {day['topic']}")
            if 'materials' in day:
                print("学习材料:")
                for material in day['materials']:
                    print(f"  - {material['type']}: {material['title']}")
                    if 'segment' in material:
                        print(f"    片段: {material['segment']}")
                    if 'content' in material:
                        print(f"    内容: {material['content']}")
            if 'knowledge_points' in day and day['knowledge_points']:
                print("知识要点:")
                for point in day['knowledge_points']:
                    print(f"  - {point['name']} (难度等级: {point['level']})")
                    if 'examples' in point and point['examples']:
                        print(f"    例句: {', '.join(point['examples'])}")
                    if 'exercises' in point and point['exercises']:
                        print(f"    练习: {', '.join(point['exercises'])}")
            if 'review_activities' in day:
                print("复习活动:")
                for activity in day['review_activities']:
                    if isinstance(activity, dict):
                        print(f"  - {activity['point']} (难度等级: {activity['difficulty']})")
                        print(f"    场景: {activity['context']}")
                        if 'prompt' in activity:
                            print(f"    任务: {activity['prompt']}")
                    else:
                        print(f"  - {activity}")
            print(f"预计学习时间: {day['estimated_time']}分钟")
        
        # 6. 检查用户档案更新
        print("\n6. 检查用户档案更新：")
        print(f"开始日期: {user_profile.start_date}")
        print(f"预计完成周数: {user_profile.estimated_completion_weeks}")
        print(f"当前阶段: {user_profile.current_phase}")
        print(f"最近评估日期: {user_profile.last_assessment_date}")
        print("已完成阶段：")
        for phase in user_profile.completed_phases:
            print(f"\n第 {phase['phase_number']} 周：")
            print(f"评估结果：{phase['assessment']}")
            print(f"主要进展：{', '.join(phase['progress'])}")
            print(f"需要加强：{', '.join(phase['areas_to_improve'])}")
            print(f"评估日期：{phase['date']}")
            
    except Exception as e:
        print(f"测试过程中出现错误: {str(e)}")

if __name__ == "__main__":
    # 运行所有测试
    asyncio.run(test_initial_assessment())
    asyncio.run(test_learning_plan_and_progress())

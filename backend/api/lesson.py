from fastapi import APIRouter, Depends, HTTPException
from ..services.lesson import LessonService
from ..services.lesson_delivery import LessonDeliveryService
from typing import Dict, List
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from datetime import datetime
from ..models.user import UserProfile

router = APIRouter()
lesson_service = LessonService()
lesson_delivery_service = LessonDeliveryService()

@router.get("/lessons/{user_id}/current")
async def get_current_lesson(
    user_id: str,
    db: AsyncIOMotorClient = Depends(lambda: None)
):
    """
    获取用户当前的课程
    """
    try:
        # 获取最新的学习计划
        study_plan = await db.study_plans.find_one(
            {"user_id": ObjectId(user_id)},
            sort=[("week_start", -1)]
        )
        
        if not study_plan:
            raise HTTPException(status_code=404, detail="No study plan found")
        
        # 获取用户完成的课程数
        completed_lessons = await db.lesson_records.count_documents({
            "user_id": ObjectId(user_id),
            "week_start": study_plan["week_start"]
        })
        
        # 获取当前课程
        current_lesson = study_plan["plan"][completed_lessons]
        return current_lesson
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/lessons/{user_id}/start")
async def start_interactive_lesson(
    user_id: str,
    lesson_id: str,
    db: AsyncIOMotorClient = Depends(lambda: None)
):
    """
    开始一节交互式课程
    """
    try:
        # 获取用户档案
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if not user or not user.get("profile"):
            raise HTTPException(status_code=404, detail="User profile not found")
        
        # 获取课程计划
        study_plan = await db.study_plans.find_one(
            {"user_id": ObjectId(user_id)},
            sort=[("week_start", -1)]
        )
        if not study_plan:
            raise HTTPException(status_code=404, detail="No study plan found")
        
        # 找到指定的课程
        lesson = None
        for daily_plan in study_plan["plan"]:
            if str(daily_plan.get("_id", "")) == lesson_id:
                lesson = daily_plan
                break
        
        if not lesson:
            raise HTTPException(status_code=404, detail="Lesson not found")
        
        # 创建新的课程会话
        session = {
            "user_id": ObjectId(user_id),
            "lesson_id": lesson_id,
            "start_time": datetime.now(),
            "conversation": []
        }
        await db.lesson_sessions.insert_one(session)
        
        # 开始课程
        response = await lesson_delivery_service.start_lesson(
            lesson,
            UserProfile(**user["profile"])
        )
        
        # 保存教师回复
        await db.lesson_sessions.update_one(
            {"_id": session["_id"]},
            {"$push": {"conversation": {
                "role": "assistant",
                "content": response["content"],
                "timestamp": datetime.now()
            }}}
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/lessons/{user_id}/interact")
async def interact_with_lesson(
    user_id: str,
    student_response: Dict,
    db: AsyncIOMotorClient = Depends(lambda: None)
):
    """
    在课程中进行互动
    """
    try:
        # 获取用户档案
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if not user or not user.get("profile"):
            raise HTTPException(status_code=404, detail="User profile not found")
        
        # 获取当前课程会话
        session = await db.lesson_sessions.find_one(
            {"user_id": ObjectId(user_id)},
            sort=[("start_time", -1)]
        )
        if not session:
            raise HTTPException(status_code=404, detail="No active lesson session")
        
        # 获取课程计划
        study_plan = await db.study_plans.find_one(
            {"user_id": ObjectId(user_id)},
            sort=[("week_start", -1)]
        )
        lesson = None
        for daily_plan in study_plan["plan"]:
            if str(daily_plan.get("_id", "")) == session["lesson_id"]:
                lesson = daily_plan
                break
        
        if not lesson:
            raise HTTPException(status_code=404, detail="Lesson not found")
        
        # 处理学生回答
        response = await lesson_delivery_service.process_student_response(
            lesson,
            UserProfile(**user["profile"]),
            session["conversation"],
            student_response["content"]
        )
        
        # 保存对话记录
        await db.lesson_sessions.update_one(
            {"_id": session["_id"]},
            {"$push": {
                "conversation": [
                    {
                        "role": "user",
                        "content": student_response["content"],
                        "timestamp": datetime.now()
                    },
                    {
                        "role": "assistant",
                        "content": response["content"],
                        "timestamp": datetime.now()
                    }
                ]
            }}
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/lessons/{user_id}/generate")
async def generate_lesson_content(
    user_id: str,
    lesson_plan: Dict,
    db: AsyncIOMotorClient = Depends(lambda: None)
):
    """
    生成课程内容
    """
    try:
        # 获取用户档案
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if not user or not user.get("profile"):
            raise HTTPException(status_code=404, detail="User profile not found")
        
        # 生成课程内容
        lesson_content = await lesson_service.generate_lesson_content(
            lesson_plan,
            user["profile"]
        )
        
        return lesson_content
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/lessons/{user_id}/complete")
async def complete_lesson(
    user_id: str,
    lesson_record: Dict,
    db: AsyncIOMotorClient = Depends(lambda: None)
):
    """
    完成课程并生成总结
    """
    try:
        # 生成课程总结
        summary = await lesson_service.generate_lesson_summary(lesson_record)
        
        # 保存课程记录和总结
        await db.lesson_records.insert_one({
            "user_id": ObjectId(user_id),
            "lesson_record": lesson_record,
            "summary": summary,
            "completed_at": datetime.now()
        })
        
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/lessons/{user_id}/weekly-summary")
async def generate_weekly_summary(
    user_id: str,
    db: AsyncIOMotorClient = Depends(lambda: None)
):
    """
    生成每周学习总结
    """
    try:
        # 获取本周的学习记录
        weekly_records = await db.lesson_records.find({
            "user_id": ObjectId(user_id),
            "completed_at": {
                "$gte": datetime.now() - timedelta(days=7)
            }
        }).to_list(length=7)
        
        if not weekly_records:
            raise HTTPException(status_code=404, detail="No lesson records found for this week")
        
        # 生成周总结
        summary = await lesson_service.generate_weekly_summary(weekly_records)
        
        # 保存周总结
        await db.weekly_summaries.insert_one({
            "user_id": ObjectId(user_id),
            "summary": summary,
            "week_end": datetime.now()
        })
        
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

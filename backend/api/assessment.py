from fastapi import APIRouter, HTTPException, Body
from services.assessment import AssessmentService
from typing import List, Dict

router = APIRouter(prefix="/api/assessment", tags=["assessment"])
assessment_service = AssessmentService()

@router.post("/initial-chat")
async def chat_with_ai(
    messages: List[Dict]
):
    """
    与AI进行初始对话评估
    """
    try:
        # 获取AI响应
        response = await assessment_service.conduct_initial_assessment(messages)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze-profile")
async def analyze_user_profile(
    messages: List[Dict] = Body(...)
):
    """
    分析对话内容生成用户档案
    """
    try:
        # 直接使用传入的对话历史进行分析
        profile = await assessment_service.analyze_assessment(messages)
        return profile
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/generate-total-plan")
async def generate_total_plan(
    profile: Dict = Body(...)
):
    """
    生成总体学习计划
    """
    try:
        # 直接使用传入的用户档案生成学习计划
        total_plan = await assessment_service.generate_total_plan(profile)
        return total_plan
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-weekly-plan")
async def generate_weekly_plan(
    topic_with_profile: Dict = Body(...)
):
    """
    生成每周学习计划
    """
    try:
        # 直接使用传入的用户档案生成学习计划
        weekly_plan = await assessment_service.generate_weekly_plan(topic_with_profile)
        return weekly_plan
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

import logging
from fastapi import APIRouter, HTTPException, Body, Query, Response
from typing import Dict, List
from services.lesson import LessonService, LessonMode
from models.lesson_models import Message, CreateLessonRequest, ChatRequest, SummaryLessonRequest

router = APIRouter(prefix="/api/lesson", tags=["lesson"])
lesson_service = LessonService()
logger = logging.getLogger(__name__)


@router.post("/create")
async def create_lesson(
    request: CreateLessonRequest,
    response: Response,
    native_lang: str = Query("cmn-CN", description="用户母语，默认为cmn-CN（中文）"),
    learning_lang: str = Query("en-US", description="学习语言，默认为en-US（英语）")
):
    """创建一个新的课程场景，返回初始化的课程信息和系统提示"""
    try: 
        if not request.lesson_info:
            raise HTTPException(status_code=400, detail="requires lesson_info data")
        
        result = await lesson_service.create_lesson(request, native_lang, learning_lang)
        usage = result.pop("usage", None)
        if usage and isinstance(usage, dict):
            # Add usage information to response headers
            if "prompt_tokens" in usage:
                response.headers["X-Prompt-Tokens"] = str(usage["prompt_tokens"])
            if "completion_tokens" in usage:
                response.headers["X-Completion-Tokens"] = str(usage["completion_tokens"])
            if "total_tokens" in usage:
                response.headers["X-Total-Tokens"] = str(usage["total_tokens"])
        return result
    except Exception as e:
        logger.error(f"Error creating lesson: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat")
async def chat(
    request: ChatRequest,
    response: Response,
    native_lang: str = Query("cmn-CN", description="用户母语，默认为cmn-CN（中文）"),
    learning_lang: str = Query("en-US", description="学习语言，默认为en-US（英语）")
):
    """进行对话交互，需要传入完整的课程信息和对话历史"""
    try:
        if not request.user_input:
            raise HTTPException(
                status_code=400,
                detail="Missing required fields: user_input"
            )
        
        # 直接使用传入的lesson和conversation_history
        lesson_dict = request.lesson.dict()
        
        # 将对话历史转换为LLM服务需要的格式
        messages = [msg.dict() for msg in request.conversation_history]
        
        # # 直接将用户消息添加到对话历史
        # messages.append({"role": "user", "content": request.user_input})
        
        # 进行对话，直接传入对话历史
        result = await lesson_service.conduct_lesson(
            lesson_dict, 
            user=request.user,
            user_message=request.user_input,
            conversation_history=messages,
            native_lang=native_lang,
            learning_lang=learning_lang
        )

        content = "".join(result.get("speechText", result.get("content")))
        usage = result.pop("usage", None)
        if usage and isinstance(usage, dict):
            # Add usage information to response headers
            if "prompt_tokens" in usage:
                response.headers["X-Prompt-Tokens"] = str(usage["prompt_tokens"])
            if "completion_tokens" in usage:
                response.headers["X-Completion-Tokens"] = str(usage["completion_tokens"])
            if "total_tokens" in usage:
                response.headers["X-Total-Tokens"] = str(usage["total_tokens"])
                
        assistant_message = {
            "role": "assistant",
            "content": content,
            "speechText": result.get("speechText"),
            "displayText": result.get("displayText", ""),
            "diagnose": result.get("diagnose", "")
        }
        
        return assistant_message
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    

@router.post("/summary")
async def summary_lesson(
    request: SummaryLessonRequest,
    response: Response,
    native_lang: str = Query("cmn-CN", description="用户母语，默认为cmn-CN（中文）"),
    learning_lang: str = Query("en-US", description="学习语言，默认为en-US（英语）")
):
    """总体分析本次课程的对话，按评分规则给出结论"""
    try:
        result = await lesson_service.summary_lesson(request, native_lang, learning_lang)
        
        # Check if the result contains usage information (from the lesson service)
        if isinstance(result, dict) and "usage" in result:
            usage = result.pop("usage", None)
            if usage and isinstance(usage, dict):
                # Add usage information to response headers
                if "prompt_tokens" in usage:
                    response.headers["X-Prompt-Tokens"] = str(usage["prompt_tokens"])
                if "completion_tokens" in usage:
                    response.headers["X-Completion-Tokens"] = str(usage["completion_tokens"])
                if "total_tokens" in usage:
                    response.headers["X-Total-Tokens"] = str(usage["total_tokens"])
            
            # If there's a content field in the result, return it directly to maintain the original format
            if "report" in result:
                return result["report"]
        
        return result
    except Exception as e:
        logger.error(f"Summary error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/evaluate")
async def evaluate_lesson(request: SummaryLessonRequest,
    response: Response,
    native_lang: str = Query("cmn-CN", description="用户母语，默认为cmn-CN（中文）"),
    learning_lang: str = Query("en-US", description="学习语言，默认为en-US（英语）")):
    """总体分析本次课程的对话，按评分规则给出结论"""
    try:
        result = await lesson_service.evaluate_lesson(request, native_lang, learning_lang)
        usage = result.pop("usage", None)
        if usage and isinstance(usage, dict):
            # Add usage information to response headers
            if "prompt_tokens" in usage:
                response.headers["X-Prompt-Tokens"] = str(usage["prompt_tokens"])
            if "completion_tokens" in usage:
                response.headers["X-Completion-Tokens"] = str(usage["completion_tokens"])
            if "total_tokens" in usage:
                response.headers["X-Total-Tokens"] = str(usage["total_tokens"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate_weekly_summary")
async def generate_weekly_summary(
    response: Response,
    request: Dict = Body(...),
    native_lang: str = Query("cmn-CN", description="用户母语，默认为cmn-CN（中文）"),
    learning_lang: str = Query("en-US", description="学习语言，默认为en-US（英语）")
):
    """详细分析本次课程的每一句对话，提出问题"""
    try:
        result = await lesson_service.generate_weekly_summary(request, native_lang, learning_lang)
        usage = result.pop("usage", None)
        if usage and isinstance(usage, dict):
            # Add usage information to response headers
            if "prompt_tokens" in usage:
                response.headers["X-Prompt-Tokens"] = str(usage["prompt_tokens"])
            if "completion_tokens" in usage:
                response.headers["X-Completion-Tokens"] = str(usage["completion_tokens"])
            if "total_tokens" in usage:
                response.headers["X-Total-Tokens"] = str(usage["total_tokens"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        



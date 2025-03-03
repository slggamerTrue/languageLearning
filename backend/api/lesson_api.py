from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Optional, List, Literal
from services.lesson import LessonService, LessonMode

router = APIRouter(prefix="/api/lesson", tags=["lesson"])
lesson_service = LessonService()

class Message(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str
    speech_text: Optional[str] = None  # 用于语音输出的纯文本版本
    display_text: Optional[str] = None  # 用于展示的文本，支持markdown格式

class SceneResource(BaseModel):
    resource_type: Literal["menu", "document", "image", "list"]
    title: str
    content: str
    display_format: Literal["markdown", "text", "table"] = "text"
    speech_text: Optional[str] = None  # 用于语音描述资源的文本

class SceneConfig(BaseModel):
    description: str
    your_role: str
    student_role: str
    additional_info: str
    current_situation: str
    resources: Optional[List[SceneResource]] = None  # 场景相关的资源（如菜单、文档等）

class Lesson(BaseModel):
    mode: str
    topic: str
    scene: Optional[SceneConfig] = None
    assessment_day: Optional[Dict] = None

class LessonContent(BaseModel):
    text: str  # 普通文本内容
    speech_text: Optional[str] = None  # 用于语音输出的版本
    content_type: Literal["introduction", "concept", "example", "exercise", "summary"] = "concept"
    display_type: Literal["text", "list", "example", "exercise"] = "text"

class LessonStep(BaseModel):
    title: str
    contents: List[LessonContent]
    requires_interaction: bool = False  # 是否需要学生互动

class CreateLessonRequest(BaseModel):
    mode: Literal["study", "practice"]
    topic: str
    scene: Optional[SceneConfig] = None
    assessment_day: Optional[Dict] = None

class ChatRequest(BaseModel):
    lesson: Lesson
    conversation_history: List[Message] = Field(default_factory=list)
    user_input: str

class ChatResponse(BaseModel):
    content: str
    conversation_history: List[Message]

@router.post("/create")
async def create_lesson(request: CreateLessonRequest):
    """创建一个新的课程场景，返回初始化的课程信息和系统提示"""
    try:
        mode = LessonMode.STUDY if request.mode == "study" else LessonMode.PRACTICE
        
        if mode == LessonMode.STUDY and not request.assessment_day:
            raise HTTPException(status_code=400, detail="Study mode requires assessment_day data")
            
        lesson = Lesson(
            mode=mode.value,
            topic=request.topic,
            scene=request.scene,
            assessment_day=request.assessment_day if mode == LessonMode.STUDY else None
        )
        
        # 生成系统提示和欢迎消息
        if lesson.scene:  # 角色扮演模式
            # 构建场景资源提示
            resources_prompt = ""
            if lesson.scene.resources:
                resources_prompt = "Available resources in this scene:\n"
                for resource in lesson.scene.resources:
                    resources_prompt += f"- {resource.title} ({resource.resource_type})\n"
            
            system_prompt = f"""You are in a role-playing scenario. Stay in character and respond naturally based on your role.
            If the student uses Chinese or asks to use Chinese, respond in a way that naturally encourages English use while staying in character.
            
            Scene description: {lesson.scene.description}
            Current situation: {lesson.scene.current_situation}
            Your role: {lesson.scene.your_role}
            Student role: {lesson.scene.student_role}
            Additional context: {lesson.scene.additional_info}
            
            {resources_prompt}
            
            Important guidelines:
            1. For each response, provide two fields:
               - display_text: The text shown to the user (can include formatting for menus, lists, etc)
               - speech_text: A natural, conversational version suitable for speaking
            
            2. When showing resources (like menus, lectures, etc):
               - Use appropriate formatting (markdown/tables) for display_text
               - Provide a slide-level description for speech_text if it can reduce the likelihood of confusion
               - Only show resources when specifically requested
            
            3. Stay in character while:
               - Describing or presenting resources
               - Answering questions about the resources
               - Guiding the conversation naturally
            
            Start with a natural, in-character greeting appropriate for the scene.
            """
        else:  # 学习模式
            system_prompt = f"""You are an experienced English tutor helping students learn English.
            Today's topic: {lesson.topic}
            Assessment day: {lesson.assessment_day}
            
            返回需要两个字段,display_text和speech_text：
            display_text字段中，以markdown格式规划今天课程的大纲出来
            需要包含下面几个部分：
               - Introduction: 讲解今天课程主要内容
               - Concept: Clear explanation of the learning point
               - Examples: Simple, practical examples
               - Practice: Interactive exercises
               - Summary: Brief recap of key points
            
            speech_text字段中， a natural, conversational introduction that sets up today's lesson.
            """
        
        # 使用structured_chat生成带格式的欢迎语
        output_format = '''
        {
            "display_text": "string",
            "speech_text": "string"  
        }
        '''
        
        response = await lesson_service.llm_service.structured_chat(
            messages=[{"role": "system", "content": system_prompt}],
            output_format=output_format
        )
        
        display_text = response["display_text"]
        speech_text = response["speech_text"]
        
        initial_conversation = [
            Message(
                role="assistant",
                content=speech_text,  # Use speech_text as the base content
                display_text=display_text,
                speech_text=speech_text
            )
        ]
        
        return {
            "lesson": lesson,
            "conversation_history": initial_conversation
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat")
async def chat(request: ChatRequest) -> ChatResponse:
    """进行对话交互，需要传入完整的课程信息和对话历史"""
    try:
        # 验证请求数据
        if not request.lesson or not request.user_input:
            raise HTTPException(
                status_code=400,
                detail="Missing required fields: lesson or user_input"
            )
        
        # 直接使用传入的lesson和conversation_history
        lesson_dict = request.lesson.dict()
        
        # 将对话历史转换为LLM服务需要的格式
        messages = [msg.dict() for msg in request.conversation_history]
        
        # # 直接将用户消息添加到对话历史
        # messages.append({"role": "user", "content": request.user_input})
        
        # 进行对话，直接传入对话历史
        response = await lesson_service.conduct_lesson(
            lesson_dict, 
            user_message=request.user_input,
            conversation_history=messages
        )
        
        # 创建用户消息和助手消息对象
        #user_message_obj = Message(role="user", content=request.user_input)
        assistant_message = Message(
            role="assistant",
            content=response["content"],
            speech_text=response.get("speech_text", response["content"]),
            display_text=response.get("display_text", "")
        )
        
        # 更新对话历史
        updated_history = request.conversation_history + [assistant_message]
        
        return ChatResponse(
            content=response["content"],
            conversation_history=updated_history
        )
    except Exception as e:
        print(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


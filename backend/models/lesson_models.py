from pydantic import BaseModel, Field
from typing import Dict, Optional, List, Literal

class Message(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str
    speechText: Optional[List[str]] = None  # 用于语音输出的纯文本版本
    displayText: Optional[str] = None  # 用于展示的文本，支持markdown格式

class SceneResource(BaseModel):
    resource_type: Literal["menu", "document", "image", "list"]
    title: str
    content: str
    display_format: Literal["markdown", "text", "table"] = "text"
    speechText: Optional[str] = None  # 用于语音描述资源的文本

class SceneConfig(BaseModel):
    description: str
    your_role: str
    student_role: str
    additional_info: str
    current_situation: str
    resources: Optional[List[SceneResource]] = None  # 场景相关的资源（如菜单、文档等）

class Lesson(BaseModel):
    mode: str
    lesson_info: Optional[Dict] = None

class LessonContent(BaseModel):
    text: str  # 普通文本内容
    speechText: Optional[str] = None  # 用于语音输出的版本
    content_type: Literal["introduction", "concept", "example", "exercise", "summary"] = "concept"
    display_type: Literal["text", "list", "example", "exercise"] = "text"

class LessonStep(BaseModel):
    title: str
    contents: List[LessonContent]
    requires_interaction: bool = False  # 是否需要学生互动

class CreateLessonRequest(BaseModel):
    mode: Literal["study", "practice"]
    lesson_info: Optional[Dict] = None
    user: Optional[Dict] = None

class SummaryLessonRequest(BaseModel):
    mode: Literal["study", "practice"]
    lesson: Optional[Dict] = None
    user: Optional[Dict] = None
    conversation_history: Optional[List[Message]] = None

class ChatRequest(BaseModel):
    lesson: Lesson
    user: Optional[Dict] = None
    conversation_history: List[Message] = Field(default_factory=list)
    user_input: str

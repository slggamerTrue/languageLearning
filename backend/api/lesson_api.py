import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Optional, List, Literal
from services.lesson import LessonService, LessonMode

router = APIRouter(prefix="/api/lesson", tags=["lesson"])
lesson_service = LessonService()
logger = logging.getLogger(__name__)
class Message(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str
    speech_text: Optional[List[str]] = None  # 用于语音输出的纯文本版本
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
    lesson_info: Optional[Dict] = None

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
    lesson_info: Optional[Dict] = None

class SummaryLessonRequest(BaseModel):
    mode: Literal["study", "practice"]
    lesson: Optional[Dict] = None
    user: Optional[Dict] = None
    conversation_history: Optional[List[Message]] = None

class ChatRequest(BaseModel):
    lesson: Lesson
    conversation_history: List[Message] = Field(default_factory=list)
    user_input: str


@router.post("/create")
async def create_lesson(request: CreateLessonRequest):
    """创建一个新的课程场景，返回初始化的课程信息和系统提示"""
    try:
        mode = LessonMode.STUDY if request.mode == "study" else LessonMode.PRACTICE
        
        if not request.lesson_info:
            raise HTTPException(status_code=400, detail="requires lesson_info data")
        
        # 生成系统提示和欢迎消息
        if mode == LessonMode.PRACTICE:  # 角色扮演模式
            # 构建场景资源提示
            system_prompt = f"""You are in a role-playing scenario. Stay in character and respond naturally based on your role.
            If the student uses Chinese or asks to use Chinese, respond in a way that naturally encourages English use while staying in character.
            
            Based on the following information to build a role-playing scenario. 需要设定一个完成的目标保证这次的场景基于用户的水平有挑战性，同时增加一些随机事件保证每次的场景不一样。
            {request.lesson_info}
            
            Important guidelines:
            1. For each response, provide two fields:
               - display_text: 基于课程信息生成一个场景，对场景进行简单描述，并且分配bot和user的角色，显示本场景设定达到的目标以及所需的一些信息，场景描述需足够清晰，用markdown格式方便清晰的描述。
               如是问路的场景，你甚至可以用markdown提供一个地图，设定一个当前位置和目的地，看用户能否正确指路。如是餐厅的场景，你可以提供带价格的菜单，看用户能否按要求(如必须含有2份主食，吃素，有忌口或者价格限定在多少范围内)搭配点餐
               - speech_text: 你作为bot，基于display_text中bot的角色，生成一个开场语，为方便语音合成，分割为一句一句的。
            
            2. Stay in character while:
               - Describing or presenting resources
               - Answering questions about the resources
               - Guiding the conversation naturally

            3. user的会话前缀是[voice]表示用户是通过语音输入，所以如果有单词让你疑惑可能是用户发音不标准的问题，你可以猜测用户的意思进行回答即可。
            前缀[text]表示用户是通过文字输入，那可能存在一些拼写错误。
               
            """
        else:  # 学习模式
            system_prompt = f"""You are an experienced English tutor helping students learn English.
            基于下面的课程信息，你需要规划今天的课程大纲，并且生成一个开场语。
            {request.lesson_info}
            
            Important guidelines:
            1. 返回需要两个字段,display_text和speech_text：
            display_text字段中，以markdown格式规划今天课程的大纲出来，大纲要求较为详细，方便后面的对话参照该大纲控制流程。
            speech_text字段中， 老师语音输出的内容，为便于语音合成，分割为一句一句的。
            
            2. 这是一个一对一的教学场景，所以你应该根据学生的水平，以及需要学习的内容制定大纲。
            """
        
        # 使用structured_chat生成带格式的欢迎语
        output_format = '''
        返回格式只需要json格式，如下：
        {
            "speech_text": string[],  # 必须的语音内容
            "display_text": str  # 可选的展示内容，支持markdown格式
        }
        '''
        
        response = await lesson_service.llm_service.structured_chat(
            messages=[{"role": "user", "content": system_prompt + output_format}]
        )
        
        display_text = response["display_text"]
        speech_text = response["speech_text"]
        
        initial_conversation = [
            Message(
                role="assistant",
                content="".join(map(str, speech_text)),  # Use speech_text as the base content
                display_text=display_text,
                speech_text=speech_text
            )
        ]
        
        return {
            "conversation_history": initial_conversation
        }
    except Exception as e:
        logger.error(f"Error creating lesson: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat")
async def chat(request: ChatRequest):
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
        response = await lesson_service.conduct_lesson(
            lesson_dict, 
            user_message=request.user_input,
            conversation_history=messages
        )

        content = "".join(response.get("speech_text", response.get("content")))

        assistant_message = {
            "role": "assistant",
            "content": content,
            "speech_text": response.get("speech_text"),
            "display_text": response.get("display_text", ""),
            "diagnose": response.get("diagnose", "")
        }
        
        return assistant_message
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    

@router.post("/summary")
async def summary_lesson(request: SummaryLessonRequest):
    """总体分析本次课程的对话，按评分规则给出结论"""
    try:
        
        system_prompt = f"""你是一个英语教育专家，课程内容为
        {request.lesson}

        学生的基本信息为
        {request.user}

        本次课程的对话为,其中user表示用户的对话，assistant表示助手的回复，system表示系统的提示。user的会话前缀是[voice]表示用户是通过语音输入，所以如果有单词让你疑惑可能是用户发音不标准的问题，你可以猜测用户的意思进行回答即可。
        前缀[text]表示用户是通过文字输入，那可能存在一些拼写错误。
        {request.conversation_history}

        你需要基于这些内容，按评估系统，你需要确定学生本课的英语水平。
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

        然后整理一份报告出来，学生哪些地方做的好，哪些地方做的不好，需要提出哪些建议，本次课程学习的效果如何。以markdown格式生成一份供用户查看的中文报告。
        注意，输出为markdown格式，不要内容。
        """
        
        response = await lesson_service.llm_service.chat_completion(
            messages=[{"role": "user", "content": system_prompt}]  #, model="pkqwq:latest"
        )
        return response["content"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@router.post("/detail_analysis")
async def detail_analysis(request: SummaryLessonRequest):
    """详细分析本次课程的每一句对话，提出问题"""
    try:
        
        system_prompt = f"""你是一个英语教育专家，课程内容为
        {request.lesson}

        学生的基本信息为
        {request.user}

        本次课程的对话为,其中user表示用户的对话，assistant表示助手的回复，system表示系统的提示。user的会话前缀是[voice]表示用户是通过语音输入，所以如果有单词让你疑惑可能是用户发音不标准的问题，你可以猜测用户的意思进行回答即可。
        前缀[text]表示用户是通过文字输入，那可能存在一些拼写错误。
        {request.conversation_history}

        你需要逐句分析user的每一句话，从四个维度去分析，分析出用户的错误类型，然后给出建议。错误类型有：语法错误、词汇错误、句子连贯性错误、任务完成度错误。
        按对话中user的句子顺序以下面的json格式返回
        [{{
 "sentence": string, //"user's raw message",
 "errors": [
       {{
      "error_type": str, // "grammar" or "vocabulary" or "coherence" or "achievement" or "others",
      "description": str, // description of the user's error and the correct form
     }}
    ],
 "advices": string[] // "表达没错，但是换一种表达更好的建议，或者基于当前场景更常用的表达，没有可以为空"
}}]

            
        """
        
        response = await lesson_service.llm_service.structured_chat(
            messages=[{"role": "system", "content": system_prompt}]
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/diagnose-chat")
async def diagnose_chat(messages: List[Dict]):
    """
    评估对话中的错误
    """
    try:
        system_message = {
            "role": "system",
            "content": """你是一个专业的英语教师，正在与学生进行交谈。你需要根据user最近的对话内容，分析是否存在一些错误，如无错误则返回空数组。

返回格式只需要json格式，如下：
{
    "diagnose": [{
        "type": str,  # 错误类型Grammar, Vocabulary, Structure, Context
        "description": str,  # 错误描述，引号引用原文，并用中文描述错误原因
        "correct": str  # 正确的英文表达
    }],
}
"""
        }
        
        all_messages = [system_message] + messages
        #return await lesson_service.llm_service.chat_completion(all_messages)
        response = await lesson_service.llm_service.structured_chat(all_messages)

        return response

    except Exception as e:
        raise Exception(f"Assessment failed: {str(e)}")



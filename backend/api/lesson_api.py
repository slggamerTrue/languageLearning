import logging
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field
from typing import Dict, Optional, List, Literal
from services.lesson import LessonService, LessonMode

router = APIRouter(prefix="/api/lesson", tags=["lesson"])
lesson_service = LessonService()
logger = logging.getLogger(__name__)
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
            system_prompt = f"""你是一个专业的英语教师，正在设计一个角色扮演的场景。
            Based on the following information to build a role-playing scenario. 需要设定一个完成的目标保证这次的场景基于用户的水平有挑战性，
            同时增加一些随机事件保证每次的场景不一样。
            {request.lesson_info}

            用户信息如下：
            {request.user}
            
            Important guidelines:
            1. For each response, provide two fields，displayText and speechText:
               - displayText: 基于课程信息生成一个场景，对场景进行简单描述，并且分配bot和user的角色，显示本场景设定达到的目标以及所需的一些信息，用markdown格式方便清晰的描述。为方便在手机上显示而优化。
               如是问路的场景，你可以用markdown提供一个地图，设定一个当前位置和目的地，看用户能否能用英文正确指路。如是餐厅的场景，你可以提供带价格的菜单，看用户能否按要求(如必须含有2份主食，吃素，有忌口或者价格限定在多少范围内)搭配点餐
               - speechText: 你作为bot，基于displayText中bot的角色，生成一个开场语，如按场景设定不该你先说，直接返回空数组即可，开场语尽量简洁，为方便语音合成，分割为一句一句的。
            
            """
        else:  # 学习模式
            system_prompt = f"""You are an experienced English tutor helping students learn English.
            基于下面的课程信息和用户信息，你需要规划今天的课程大纲，并且生成一个开场语。
            {request.lesson_info}
            
            用户信息如下：
            {request.user}
            
            Important guidelines:
            1. 返回需要两个字段,displayText和speechText：
            displayText字段中，以markdown格式规划今天课程的大纲出来，请为手机上显示优化。
            speechText字段中， 老师语音输出的内容，为便于语音合成，分割为一句一句的。
            
            2. 这是一个一对一的教学场景，所以你应该根据学生的水平，以及需要学习的内容制定大纲。
            """
        
        # 使用structured_chat生成带格式的欢迎语
        output_format = '''
        返回格式只需要json格式，如下：
        {
            "speechText": string[],  # 必须的语音内容
            "displayText": str  # 可选的展示内容，支持markdown格式
        }
        '''
        
        response = await lesson_service.llm_service.structured_chat(
            messages=[{"role": "user", "content": system_prompt + output_format}]
        )
        
        displayText = response["displayText"]
        speechText = response["speechText"]
        
        initial_conversation = [
            Message(
                role="assistant",
                content=" ".join(map(str, speechText)),  # Use speechText as the base content
                displayText=displayText,
                speechText=speechText
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

        content = "".join(response.get("speechText", response.get("content")))

        assistant_message = {
            "role": "assistant",
            "content": content,
            "speechText": response.get("speechText"),
            "displayText": response.get("displayText", ""),
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
        from datetime import datetime
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        system_prompt = f"""你是一个英语教育专家，本次课程为{request.mode}模式，课程内容为
        {request.lesson}

        学生的基本信息为
        {request.user}

        今天的日期是：{current_date}

        本次课程的对话为,其中user表示用户的对话，assistant表示助手的回复。user的会话前缀是[voice]表示用户是通过语音输入，所以如果有单词让你疑惑可能是用户发音不标准的问题，你可以猜测用户的意思进行回答即可。
        前缀[text]表示用户是通过文字输入，那可能存在一些拼写错误。
        {request.conversation_history}

        然后整理一份用markdown格式的报告出来，报告格式如下，只输出正确有效的markdown格式的报告，不要加引号，不要有其他说明：

        # 📊 对话评估报告

> **对话主题**：`[填写主题]`  
> **日期**：`{current_date}`  

---

## 🎯 表现概述
- **整体理解度**：`[对用户理解程度的总体评价]`
- **互动积极性**：`[描述用户在对话中的参与度]`
- **关键亮点**：
  - ✅ `[用户展现出的亮点 1]`
  - ✅ `[用户展现出的亮点 2]`
  - ✅ `[用户展现出的亮点 3]`
- **需要改进**：
  - 🔄 `[需要改进的方面 1]`
  - 🔄 `[需要改进的方面 2]`

---

## 📌 知识掌握情况
| 评估维度 | 评价 |
|---------|------|
| **核心概念理解** | `[浅显 / 部分掌握 / 较好 / 熟练]` |
| **实践应用能力** | `[弱 / 一般 / 良好 / 熟练]` |
| **逻辑表达能力** | `[需要提升 / 清晰流畅 / 优秀]` |
| **自主思考能力** | `[较弱 / 需要引导 / 主动思考]` |

---

## 📈 互动与反馈分析
- **学生提问情况**：
  - `[是否有深度问题，或仅停留在表面问题]`
  - `[提问是否能促进对话继续]`
- **回答质量**：
  - `[是否能完整表达自己的想法]`
  - `[是否能结合案例或个人理解]`
- **对关键知识点的反应**：
  - `[哪些内容学生反应积极]`
  - ⚠️ `[哪些内容学生较为困惑]`

---

## 🎯 未来学习建议
- **强化学习内容**：
  - 📖 `[建议复习的知识点]`
  - 🏗 `[推荐进一步练习的方法]`
- **提升互动表现**：
  - 🎤 `[如何更主动表达自己的观点]`
  - 🔍 `[如何提高沟通能力]`
- **个性化学习建议**：
  - 🎯 `[根据学生特点给出的具体建议]`

---

## 📎 总结
> `[用一句话总结这节课学生的整体学习效果]`

        """
        
        response = await lesson_service.llm_service.chat_completion(
            messages=[{"role": "user", "content": system_prompt}]  #, model="pkqwq:latest"
        )
        return response["content"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/evaluate")
async def evaluate_lesson(request: SummaryLessonRequest):
    """总体分析本次课程的对话，按评分规则给出结论"""
    try:
        from datetime import datetime
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        system_prompt = f"""你是一个英语教育专家，本次课程为{request.mode}模式，课程内容为
        {request.lesson}

        学生的基本信息为
        {request.user}

        今天的日期是：{current_date}

        本次课程的对话为,其中user表示用户的对话，assistant表示助手的回复。user的会话前缀是[voice]表示用户是通过语音输入，所以如果有单词让你疑惑可能是用户发音不标准的问题，你可以猜测用户的意思进行回答即可。
        前缀[text]表示用户是通过文字输入，那可能存在一些拼写错误。
        {request.conversation_history}

        你需要基于这些内容，按评估系统，你需要确定学生本课的英语水平。
按照雅思口语评分标准
9分 专家水平：具有完全的英语运用能力，做到适当、精确、流利并能完全理解语言
8分 优秀水平：能将英语运用自如,只是有零星的错误或用词不当，在不熟悉语境下可能出现误解，可将复杂细节的争论掌握的相当好
7分 良好水平：能有效运用英语,虽然偶尔出现不准确、不适当和误解，大致可将复杂的英语掌握的不错，也能理解详细的推理
6分 合格水平：大致能有效运用英语，虽然有不准确、不适当和误解发生，能使用并理解比较复杂的英语，特别是在熟悉的语境下
5分 基础水平：可部分运用英语，虽然经常出现错误，但在大多数情况下可明白大致的意思，在经常涉及的领域内可应付基本的沟通
4分 有限水平：只限在熟悉的状况下有基本的理解力，在理解与表达上常发生问题，无法使用复杂英语
3分 极有限水平：在极熟悉的情况下也只能进行一般的沟通，频繁发生沟通障碍
2分 初学水平：难以听懂或者看懂英语
1分 不懂英语：掌握个别单词，几乎无法交流，最多能说出个别单词，根本无法用英语沟通
0分 英语0基础：完全不懂英语，英语有多少字母都不知道

        输出格式为有效的json，格式如下：
        {{
            "text": str,  # 一句话总结评分原因
            "eval": {{
                "score": int,  # 本课的完成情况，1-3分，3分最高，表示完成了课程要求的所有内容，2分表示完成了课程要求的大部分要求，1分最低，表示大部分要求没有完成。
                "reason": str  # 评级原因，如"要求进行的练习没有完成，或者回答的内容不够详细。"
                }}
            "level": {{
                "score": number,  # 综合得分, 按上面的雅思口语评分标准，得分0-9
                "reason": str  # 得分原因，如合格水平：大致能有效运用英语，虽然有不准确、不适当和误解发生，能使用并理解比较复杂的英语，特别是在熟悉的语境下
            }}
        }}
        """
        
        response = await lesson_service.llm_service.structured_chat(
            messages=[{"role": "user", "content": system_prompt}]  #, model="pkqwq:latest"
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate_weekly_summary")
async def generate_weekly_summary(request: Dict = Body(...)):
    """详细分析本次课程的每一句对话，提出问题"""
    try:
        
        system_prompt = f"""你是一个英语教育专家，学生本周学习报告如下，你需要生成一份总结报告。
        {request}

        根据这一周的报告的平均水平以及用户当前水平评价是否需要调整用户的水平评价(level:0-9的雅思口语标准)和语速(speed：slowest, slow, normal),
        如需调整就加入到action中，否则action为空。注意一定要是变化明显的时候才调整，避免频繁调整。
        输出格式为json，格式如下：
        {{
            "summary": str,  # 本周学习重点回顾
            "achievements": str,  # 进步与成就
            "weaknesses": str,  # 需要加强的领域
            "suggestions": str,  # 下周学习建议
            "action": [{{
                "type": str, # 行为类型，目前只有level和speed
                "value": str, # 行为值
                "reason": str # 行为原因
            }}]
        }}
        """
        
        response = await lesson_service.llm_service.structured_chat(
            messages=[{"role": "user", "content": system_prompt}]
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



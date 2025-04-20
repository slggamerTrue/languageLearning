from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from services.tts_service import TTSService

router = APIRouter(prefix="/api/tts", tags=["Text-to-Speech"])

class TextToSpeechRequest(BaseModel):
    texts: List[str]
    temperature: Optional[float] = 0.3
    top_p: Optional[float] = 0.7
    top_k: Optional[int] = 20
    speed: Optional[int] = 5
    prompt: Optional[str] = '[oral_2][laugh_0][break_4]'
    use_random_speaker: Optional[bool] = False
    audio_seed: Optional[int] = None  # 添加种子参数，用于生成固定的说话人嵌入向量
    speaker_type: Optional[str] = None  # 可选值: 'male' 或 'female'或 None

class TextToSpeechResponse(BaseModel):
    results: List[dict]

# Dependency to get TTS service
def get_tts_service():
    return TTSService()

@router.post("/generate", response_model=TextToSpeechResponse)
async def generate_speech(
    request: TextToSpeechRequest,
    native_lang: str = Query("cmn-CN", description="用户母语，默认为cmn-CN（中文）"),
    learning_lang: str = Query("en-US", description="学习语言，默认为en-US（英语）"),
    tts_service: TTSService = Depends(get_tts_service)
):
    """
    Generate speech from text using Google's Text-to-Speech API
    """
    try:
        results = await tts_service.generate_speech(
            texts=request.texts,
            temperature=request.temperature,
            top_p=request.top_p,
            top_k=request.top_k,
            speed=request.speed,
            prompt=request.prompt,
            use_random_speaker=request.use_random_speaker,
            audio_seed=request.audio_seed,
            speaker_type=request.speaker_type,
            native_lang=native_lang,
            learning_lang=learning_lang
        )
        return TextToSpeechResponse(results=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

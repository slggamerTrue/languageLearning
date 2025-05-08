from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form, Query
from typing import List, Optional
from pydantic import BaseModel
import base64
from services.asr_service import ASRService

router = APIRouter(prefix="/api/asr", tags=["Speech-to-Text"])

class SpeechRecognitionRequest(BaseModel):
    audio_content: str  # Base64-encoded audio content
    language_code: str = "en-US"
    alternative_language_codes: Optional[List[str]] = None
    enable_automatic_punctuation: bool = True
    enable_word_time_offsets: bool = False
    max_alternatives: int = 1

class SpeechRecognitionResponse(BaseModel):
    transcript: str
    confidence: float
    results: List[dict]
    success: bool
    detected_languages: List[str] = []

# Dependency to get ASR service
def get_asr_service():
    return ASRService()

@router.post("/recognize", response_model=SpeechRecognitionResponse)
async def recognize_speech(
    request: SpeechRecognitionRequest,
    asr_service: ASRService = Depends(get_asr_service)
):
    """
    Recognize speech from base64-encoded audio using Google's Speech-to-Text API
    """
    try:
        result = await asr_service.recognize_speech(
            audio_content=request.audio_content,
            language_code=request.language_code,
            alternative_language_codes=request.alternative_language_codes,
            enable_automatic_punctuation=request.enable_automatic_punctuation,
            enable_word_time_offsets=request.enable_word_time_offsets,
            max_alternatives=request.max_alternatives
        )
        return SpeechRecognitionResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/recognize-upload", response_model=SpeechRecognitionResponse)
async def recognize_speech_upload(
    audio_file: UploadFile = File(...),
    language_code: str = Form("en-US"),
    alternative_language_codes: str = Form(""),
    enable_automatic_punctuation: bool = Form(True),
    enable_word_time_offsets: bool = Form(False),
    max_alternatives: int = Form(1),
    asr_service: ASRService = Depends(get_asr_service)
):
    """
    Recognize speech from uploaded audio file using Google's Speech-to-Text API
    """
    try:
        # Read the audio file content
        audio_content = await audio_file.read()
        
        # Convert to base64
        base64_audio = base64.b64encode(audio_content).decode('utf-8')
        
        # Parse alternative language codes
        alt_langs = []
        if alternative_language_codes:
            alt_langs = [lang.strip() for lang in alternative_language_codes.split(',')]
        
        result = await asr_service.recognize_speech(
            audio_content=base64_audio,
            language_code=language_code,
            alternative_language_codes=alt_langs,
            enable_automatic_punctuation=enable_automatic_punctuation,
            enable_word_time_offsets=enable_word_time_offsets,
            max_alternatives=max_alternatives
        )
        return SpeechRecognitionResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

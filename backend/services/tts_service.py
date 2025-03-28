import os
import json
import base64
import aiohttp
from typing import List, Optional, Dict, Any
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

class TTSService:
    """Service for interacting with Google's Text-to-Speech API"""
    
    def __init__(self):
        self.api_url = "https://texttospeech.googleapis.com/v1beta1/text:synthesize"
        self.api_key = os.getenv("PROMPTAI_API_KEY")
        if not self.api_key:
            logger.warning("GOOGLE_TTS_API_KEY environment variable not set")
    
    async def generate_speech(
        self, 
        texts: List[str],
        temperature: float = 0.3,
        top_p: float = 0.7,
        top_k: int = 20,
        speed: int = 5,
        prompt: str = '[oral_2][laugh_0][break_4]',
        use_random_speaker: bool = False,
        audio_seed: Optional[int] = None,
        speaker_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate speech from text using Google's Text-to-Speech API
        
        Args:
            texts: List of texts to convert to speech
            temperature: Controls the randomness of the generation
            top_p: Controls diversity via nucleus sampling
            top_k: Controls diversity via top-k sampling
            speed: Speaking rate (1-10)
            prompt: Special prompt for controlling speech style
            use_random_speaker: Whether to use a random speaker
            audio_seed: Seed for generating consistent speaker embedding
            speaker_type: Type of speaker (male, female, or None)
            
        Returns:
            List of dictionaries containing audio content in base64 format
        """
        if not self.api_key:
            raise HTTPException(status_code=500, detail="Google TTS API key not configured")
        
        results = []
        
        # Calculate speaking rate (Google TTS uses 1.0 as normal speed)
        speaking_rate = speed / 5.0  # Convert 1-10 scale to 0.2-2.0 scale
        
        # Determine language code and voice based on speaker_type
        language_code = "cmn-CN"
        voice_name = "cmn-CN-Chirp3-HD-Aoede"  # Default female voice
        
        if speaker_type == "male":
            voice_name = "cmn-CN-Chirp1-HD-Aoede"  # Male voice
        
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key
        }
        
        async with aiohttp.ClientSession() as session:
            for text in texts:
                # Prepare request payload
                payload = {
                    "input": {
                        "text": text
                    },
                    "voice": {
                        "languageCode": language_code,
                        "name": voice_name
                    },
                    "audioConfig": {
                        "audioEncoding": "MP3",
                        "effectsProfileId": [
                            "medium-bluetooth-speaker-class-device"
                        ],
                        "pitch": 0,
                        "speakingRate": speaking_rate
                    }
                }
                
                # Add audio seed if provided
                if audio_seed is not None:
                    payload["audioConfig"]["audioSeed"] = audio_seed
                
                try:
                    async with session.post(
                        f"{self.api_url}?key={self.api_key}", 
                        json=payload,
                        headers=headers
                    ) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            logger.error(f"Google TTS API error: {error_text}")
                            raise HTTPException(
                                status_code=response.status,
                                detail=f"Google TTS API error: {error_text}"
                            )
                        
                        response_data = await response.json()
                        results.append({
                            "audio_content": response_data.get("audioContent", ""),
                            "text": text
                        })
                        
                except Exception as e:
                    logger.error(f"Error calling Google TTS API: {str(e)}")
                    raise HTTPException(
                        status_code=500,
                        detail=f"Error calling Google TTS API: {str(e)}"
                    )
        
        return results

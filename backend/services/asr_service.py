import os
import json
import base64
import aiohttp
import asyncio
import time
import jwt
from typing import Dict, Any, Optional, List
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

class ASRService:
    """Service for interacting with Google's Speech-to-Text v2 API with Chirp model for multi-language speech recognition"""
    
    def __init__(self):
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "leotest-454308")
        self.region = "us-central1"  # Default region for Speech API v2
        self.api_endpoint = f"{self.region}-speech.googleapis.com"
        self.api_url = f"https://{self.api_endpoint}/v2/projects/{self.project_id}/locations/{self.region}/recognizers/_:recognize"
        
        # Path to service account credentials file
        self.credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if not self.credentials_path or not os.path.exists(self.credentials_path):
            logger.warning(f"GOOGLE_APPLICATION_CREDENTIALS not set or file not found: {self.credentials_path}")
    
    async def recognize_speech(
        self, 
        audio_content: str,
        language_code: str = "en-US",
        alternative_language_codes: Optional[List[str]] = None,
        enable_automatic_punctuation: bool = True,
        enable_word_time_offsets: bool = False,
        max_alternatives: int = 1
    ) -> Dict[str, Any]:
        """
        Recognize speech from audio using Google's Speech-to-Text v2 API with Chirp model
        
        Args:
            audio_content: Base64-encoded audio content
            language_code: Primary language code (e.g., "en-US", "cmn-CN") or "auto" for language detection
            alternative_language_codes: List of additional language codes for multi-language recognition
            enable_automatic_punctuation: Whether to add punctuation to results
            enable_word_time_offsets: Whether to include word timestamps
            max_alternatives: Maximum number of alternative transcriptions to return
            
        Returns:
            Dictionary containing recognition results
        """
        if not self.credentials_path or not os.path.exists(self.credentials_path):
            raise HTTPException(status_code=500, detail="Google Cloud credentials not configured properly")
        
        # Prepare language codes array
        language_codes = [language_code]
        if language_code != "auto" and alternative_language_codes:
            language_codes.extend(alternative_language_codes)
        
        try:
            # Read service account credentials
            with open(self.credentials_path, 'r') as f:
                credentials = json.load(f)
            
            # Get access token using service account credentials
            token = await self._get_access_token(credentials)
            if not token:
                raise HTTPException(status_code=500, detail="Failed to obtain access token")
            
            # Prepare request payload for Speech-to-Text v2 API with Chirp model
            payload = {
                "config": {
                    "autoDecodingConfig": {},
                    "languageCodes": language_codes,
                    "model": "chirp",
                    "features": {
                        "enableAutomaticPunctuation": enable_automatic_punctuation,
                        "enableWordTimeOffsets": enable_word_time_offsets,
                        "maxAlternatives": max_alternatives
                    }
                },
                "content": audio_content
            }
            
            # Set up headers with the access token
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            }
            
            # Make the API request
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, json=payload, headers=headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Google Speech API v2 error: {error_text}")
                        raise HTTPException(
                            status_code=response.status,
                            detail=f"Google Speech API v2 error: {error_text}"
                        )
                    
                    response_data = await response.json()
            
            # Process and format the response
            result = {
                "results": response_data.get("results", []),
                "success": True,
                "detected_languages": []
            }
            
            # Extract the transcript from the first result if available
            if result["results"] and "alternatives" in result["results"][0]:
                result["transcript"] = result["results"][0]["alternatives"][0].get("transcript", "")
                result["confidence"] = result["results"][0]["alternatives"][0].get("confidence", 0)
                
                # Extract detected language if available
                if "languageCode" in result["results"][0]:
                    result["detected_languages"].append(result["results"][0]["languageCode"])
            else:
                result["transcript"] = ""
                result["confidence"] = 0
            
            return result
                    
        except Exception as e:
            logger.error(f"Error calling Google Speech API v2: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error calling Google Speech API v2: {str(e)}"
            )
    
    async def _get_access_token(self, credentials):
        """Get access token from service account credentials"""
        try:
            # Prepare the token request
            token_url = "https://oauth2.googleapis.com/token"
            scope = "https://www.googleapis.com/auth/cloud-platform"
            
            # Create JWT claim
            current_time = int(time.time())
            
            # Create JWT header and payload
            header = {"alg": "RS256", "typ": "JWT"}
            payload = {
                "iss": credentials["client_email"],
                "scope": scope,
                "aud": token_url,
                "exp": current_time + 3600,  # Token expires in 1 hour
                "iat": current_time
            }
            private_key = credentials["private_key"]
            jwt_token = jwt.encode(payload, private_key, algorithm="RS256", headers=header)
            
            # Request access token
            token_data = {
                "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                "assertion": jwt_token
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(token_url, data=token_data) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Failed to get access token: {error_text}")
                        return None
                    
                    token_response = await response.json()
                    return token_response.get("access_token")
                    
        except Exception as e:
            logger.error(f"Error getting access token: {str(e)}")
            return None

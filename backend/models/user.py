from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Set, Any
from datetime import datetime
from enum import Enum

class MaterialType(str, Enum):
    MOVIE = "movie"
    BOOK = "book"
    ARTICLE = "article"
    VIDEO = "video"
    AUDIO = "audio"

class KnowledgeCategory(str, Enum):
    GRAMMAR = "grammar"
    VOCABULARY = "vocabulary"
    LISTENING = "listening"
    SPEAKING = "speaking"
    READING = "reading"
    WRITING = "writing"

class LearningMaterial(BaseModel):
    type: MaterialType
    title: str
    source: str  # Source: movie name, book title, article URL
    segment: str  # Specific segment: movie timestamp, book page, article paragraph
    content_reference: str  # Specific content: movie dialogue, article text, book chapter
    difficulty: int  # Difficulty level 1-5
    topics: List[str]  # Related topic tags
    vocabulary: List[str]  # Key vocabulary words
    grammar_points: List[str]  # Related grammar points
    learning_objectives: List[str]  # Specific learning objectives
    practice_activities: List[str]  # Suggested practice activities
    prerequisites: List[str]  # Required prerequisite knowledge points

class KnowledgePoint(BaseModel):
    category: KnowledgeCategory
    name: str  # Knowledge point name, e.g. "simple past tense"
    level: int  # Difficulty level 1-5
    prerequisites: List[str]  # Prerequisite knowledge points
    related_points: List[str]  # Related knowledge points
    practice_count: int = 0  # Number of practice sessions
    mastery_level: int = 0  # Mastery level 0-100
    last_practice: Optional[datetime] = None  # Last practice time
    next_review: Optional[datetime] = None  # Next review time
    practice_history: List[Dict[str, Any]] = []  # Practice history records
    example_sentences: List[str] = []  # Example sentences
    common_mistakes: List[str] = []  # Common mistakes
    practice_contexts: List[str] = []  # Practice contexts

class LearningProgress(BaseModel):
    completed_materials: List[str]  # 完成的学习材料ID
    mastered_points: Dict[str, int]  # 知识点ID及其掌握度
    current_points: List[str]  # 当前正在学习的知识点
    review_schedule: Dict[str, datetime]  # 知识点及其计划复习时间

class UserProfile(BaseModel):
    english_level: str  # beginner, intermediate, advanced
    interests: List[str]
    learning_goals: List[str]
    preferred_language: str  # "en" or "zh"
    study_time_per_day: int  # in minutes
    
    # 学习进度跟踪
    start_date: Optional[datetime] = None
    estimated_completion_weeks: Optional[int] = None  # 预计完成周数
    current_phase: Optional[int] = None  # 当前学习阶段
    completed_phases: Optional[List[Dict]] = None  # 已完成的阶段及其评估结果
    last_assessment_date: Optional[datetime] = None  # 最近一次评估日期
    
    # 学习内容跟踪
    learning_progress: Optional[LearningProgress] = None  # 学习进度
    preferred_materials: Optional[List[MaterialType]] = None  # 偏好的学习材料类型
    difficulty_preference: Optional[int] = None  # 1-5的难度偏好

class User(BaseModel):
    email: EmailStr
    username: str
    hashed_password: str
    profile: Optional[UserProfile] = None
    created_at: datetime = datetime.now()
    last_login: datetime = datetime.now()

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

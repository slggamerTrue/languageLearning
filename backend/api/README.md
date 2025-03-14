# English Tutor API Documentation

## API Workflow

1. Initial Assessment -> 2. Profile Analysis -> 3. Total Plan Generation -> 4. Weekly Plan Creation -> 5. Lesson Management

### 1. Initial Assessment

**Endpoint:** `POST /api/chat/init-assessment`

开始用户英语水平评估对话。系统会通过对话形式收集用户的英语水平、学习目标等信息。当评估完成时，系统会返回特殊标记 `<assessment_complete>`。

**Request:**
```json
{
    "user_info": {
        "name": "John Doe",
        "preferred_topics": ["business", "technology"],
        "study_time_per_day": 45
    }
}
```

**Response:**
```json
{
    "message": "Hi John! I'd like to understand your English proficiency better. Could you tell me about your experience with English learning?",
    "conversation_history": [
        {
            "role": "system",
            "content": "Initial assessment for new user John Doe"
        },
        {
            "role": "assistant",
            "content": "Hi John! I'd like to understand your English proficiency better. Could you tell me about your experience with English learning?"
        }
    ]
}
```

### 2. Profile Analysis

**Endpoint:** `POST /api/user/analysis-profile`

分析评估对话内容，生成用户档案。

**Request:**
```json
{
    "conversation_history": [
        {
            "role": "system",
            "content": "Initial assessment for new user John Doe"
        },
        {
            "role": "assistant",
            "content": "Hi John! I'd like to understand your English proficiency better. Could you tell me about your experience with English learning?"
        },
        {
            "role": "user",
            "content": "I've been learning English for about 5 years. I can handle daily conversations but struggle with business meetings."
        }
    ]
}
```

**Response:**
```json
{
    "user_profile": {
        "english_level": "intermediate",
        "strengths": ["daily conversation", "basic grammar"],
        "weaknesses": ["business vocabulary", "meeting communication"],
        "learning_style": "practice-oriented",
        "recommended_focus": ["business English", "meeting scenarios"],
        "estimated_study_duration": "3 months"
    }
}
```

### 3. Total Plan Generation

**Endpoint:** `POST /api/user/generate-total-plan`

基于用户档案生成整体学习计划。

**Request:**
```json
{
    "user_profile": {
        "english_level": "intermediate",
        "strengths": ["daily conversation", "basic grammar"],
        "weaknesses": ["business vocabulary", "meeting communication"],
        "learning_style": "practice-oriented",
        "recommended_focus": ["business English", "meeting scenarios"],
        "estimated_study_duration": "3 months"
    }
}
```

**Response:**
```json
{
    "total_plan": {
        "duration_weeks": 12,
        "weekly_plans": [
            {
                "week_number": 1,
                "theme": "Business Meeting Basics",
                "learning_goals": [
                    "Master common meeting vocabulary",
                    "Practice meeting opening phrases"
                ],
                "estimated_study_hours": 5
            }
        ]
    }
}
```

### 4. Weekly Plan Creation

**Endpoint:** `POST /api/user/generate-weekly-plan`

根据整体计划中的周计划和用户档案生成详细的每日学习计划。

**Request:**
```json
{
    "week_plan": {
        "week_number": 1,
        "theme": "Business Meeting Basics",
        "learning_goals": [
            "Master common meeting vocabulary",
            "Practice meeting opening phrases"
        ],
        "estimated_study_hours": 5
    },
    "user_profile": {
        "english_level": "intermediate",
        "study_time_per_day": 45
    }
}
```

**Response:**
```json
{
    "daily_lessons": [
        {
            "day_number": 1,
            "topic": "Meeting Vocabulary Essentials",
            "activities": [
                {
                    "type": "vocabulary_practice",
                    "duration_minutes": 20,
                    "content": "Key meeting terms and phrases"
                },
                {
                    "type": "role_play",
                    "duration_minutes": 25,
                    "scenario": "Meeting opening and agenda setting"
                }
            ]
        }
    ]
}
```

### 5. Lesson Management

#### 5.1 Create Lesson

**Endpoint:** `POST /api/lesson/create`

基于每日课程计划创建具体的课程场景。

**Request:**
```json
{
    "daily_lesson": {
        "day_number": 1,
        "topic": "Meeting Vocabulary Essentials",
        "activities": [
            {
                "type": "vocabulary_practice",
                "duration_minutes": 20,
                "content": "Key meeting terms and phrases"
            }
        ]
    },
    "mode": "study"
}
```

[Previous response content for lesson/create]

#### 5.2 Chat

**Endpoint:** `POST /api/lesson/chat`

进行课程对话。当课程完成时，系统会返回特殊标记 `<end_of_lesson>`。

[Previous response content for lesson/chat]

#### 5.3 Lesson Analysis

**Endpoint:** `POST /api/lesson/summary`

生成课程总结报告。

**Request:**
```json
{
    "lesson": {
        "topic": "Meeting Vocabulary Essentials",
        "mode": "study"
    },
    "user_profile": {
        "english_level": "intermediate"
    },
    "conversation_history": []
}
```

**Response:**
```json
{
    "summary": {
        "completed_objectives": [
            "Learned 15 new business meeting terms",
            "Practiced 3 meeting opening scenarios"
        ],
        "performance_metrics": {
            "vocabulary_retention": 85,
            "pronunciation_accuracy": 78,
            "fluency_score": 72
        },
        "recommendations": [
            "Review meeting closing phrases",
            "Practice agenda presentation"
        ]
    }
}
```

**Endpoint:** `POST /api/lesson/detailed-analysis`

生成详细的课程分析报告。

**Request:**
```json
{
    "lesson": {
        "topic": "Meeting Vocabulary Essentials",
        "mode": "study"
    },
    "user_profile": {
        "english_level": "intermediate"
    },
    "conversation_history": []
}
```

**Response:**
```json
{
    "detailed_analysis": {
        "vocabulary_analysis": {
            "new_words_learned": [
                {
                    "word": "agenda",
                    "usage_count": 5,
                    "context_accuracy": 90
                }
            ],
            "pronunciation_issues": [
                {
                    "word": "schedule",
                    "correct_pronunciation": "ˈʃɛdjuːl",
                    "user_pattern": "skɛdjuːl"
                }
            ]
        },
        "grammar_analysis": {
            "strengths": ["subject-verb agreement", "present tense"],
            "areas_to_improve": ["past perfect usage", "conditional sentences"]
        },
        "fluency_metrics": {
            "speaking_speed": "120 words/minute",
            "pause_patterns": "Natural in most cases",
            "hesitation_points": ["When discussing project timelines"]
        },
        "improvement_suggestions": [
            {
                "area": "Vocabulary",
                "suggestion": "Focus on synonyms for common meeting terms",
                "practice_exercises": ["Synonym matching", "Context usage"]
            }
        ]
    }
}
```

## Data Models

[Previous response content for data models]

## Error Response Format

[Previous response content for error response format]

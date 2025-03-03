# English Tutor API Documentation

## API Endpoints

### 1. Create Lesson

**Endpoint:** `POST /api/lesson/create`

创建新的课程场景，返回初始化的课程信息和系统提示。

**Request:**
```json
{
    "mode": "practice",  // "practice" or "study"
    "topic": "Job Interview Practice",
    "scene": {
        "description": "这是一个产品经理职位的面试。",
        "your_role": "你是一位面试官，是产品部门的高级经理。",
        "student_role": "学生是一位应聘产品经理职位的候选人。",
        "additional_info": "公司是一家成长期的科技公司，主要产品是企业SaaS软件。",
        "current_situation": "面试即将开始，候选人已经就座。"
    }
}
```

**Response:**
```json
{
    "lesson": {
        "mode": "practice",
        "topic": "Job Interview Practice",
        "scene": {
            "description": "这是一个产品经理职位的面试。",
            "your_role": "你是一位面试官，是产品部门的高级经理。",
            "student_role": "学生是一位应聘产品经理职位的候选人。",
            "additional_info": "公司是一家成长期的科技公司，主要产品是企业SaaS软件。",
            "current_situation": "面试即将开始，候选人已经就座。"
        }
    },
    "conversation_history": [
        {
            "role": "system",
            "content": "You are in a role-playing scenario..."
        }
    ]
}
```

### 2. Chat

**Endpoint:** `POST /api/lesson/chat`

进行对话交互。需要在每次请求中传入完整的课程信息和对话历史。

**Request:**
```json
{
    "lesson": {
        "mode": "practice",
        "topic": "Job Interview Practice",
        "scene": {
            "description": "这是一个产品经理职位的面试。",
            "your_role": "你是一位面试官，是产品部门的高级经理。",
            "student_role": "学生是一位应聘产品经理职位的候选人。",
            "additional_info": "公司是一家成长期的科技公司，主要产品是企业SaaS软件。",
            "current_situation": "面试即将开始，候选人已经就座。"
        }
    },
    "conversation_history": [
        {
            "role": "system",
            "content": "You are in a role-playing scenario..."
        },
        {
            "role": "user",
            "content": "你好，我想用中文可以吗"
        },
        {
            "role": "assistant",
            "content": "I understand you'd like to speak Chinese..."
        }
    ],
    "user_input": "Sorry, I'll try in English. My name is John."
}
```

**Response:**
```json
{
    "content": "Nice to meet you, John! I appreciate your willingness to communicate in English...",
    "conversation_history": [
        {
            "role": "system",
            "content": "You are in a role-playing scenario..."
        },
        {
            "role": "user",
            "content": "你好，我想用中文可以吗"
        },
        {
            "role": "assistant",
            "content": "I understand you'd like to speak Chinese..."
        },
        {
            "role": "user",
            "content": "Sorry, I'll try in English. My name is John."
        },
        {
            "role": "assistant",
            "content": "Nice to meet you, John! I appreciate your willingness to communicate in English..."
        }
    ]
}
```

## 数据模型

### Message
```json
{
    "role": "system" | "user" | "assistant",
    "content": "消息内容"
}
```

### SceneConfig
```json
{
    "description": "场景描述",
    "your_role": "AI助手的角色",
    "student_role": "学生的角色",
    "additional_info": "额外信息",
    "current_situation": "当前情况"
}
```

### Lesson
```json
{
    "mode": "study" | "practice",
    "topic": "课程主题",
    "scene": SceneConfig,  // practice模式必填
    "assessment_day": {}  // study模式必填
}
```

## Error Response Format

当发生错误时，API将返回：

```json
{
    "detail": "错误信息描述"
}
```

常见HTTP状态码：
- 200: 成功
- 400: 请求参数错误
- 500: 服务器内部错误

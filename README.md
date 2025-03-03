# AI English Tutor

一个基于AI的个性化英语学习平台，通过对话式交互提供定制化的英语学习体验。

## 功能特点

1. 个性化用户评估
   - 智能对话式评估系统
   - 支持中英文双语交互
   - 收集用户兴趣、目标和语言水平

2. AI驱动的课程生成
   - 个性化周课程计划
   - 情境化学习内容
   - 动态调整的学习目标

3. 智能学习追踪
   - 课后学习总结
   - 语言使用分析
   - 每周进度回顾

4. 持续优化系统
   - 个性化学习建议
   - 自适应课程调整
   - 定期学习评估

## 技术架构

### 后端 (Backend)
- Python 3.9+
- FastAPI
- MongoDB
- OpenAI GPT API

### 前端 (Frontend)
- React
- TypeScript
- Ant Design
- Axios

## 项目结构

```
ai-english-tutor/
├── backend/
│   ├── api/          # API endpoints
│   ├── models/       # 数据模型
│   ├── services/     # 业务逻辑
│   └── utils/        # 工具函数
├── frontend/
│   ├── src/
│   │   ├── components/   # UI组件
│   │   ├── pages/       # 页面
│   │   ├── services/    # API服务
│   │   └── utils/       # 工具函数
│   └── public/      # 静态资源
└── docs/           # 项目文档
```

## 开发环境设置

1. 后端设置
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. 前端设置
```bash
cd frontend
npm install
npm start
```

## API文档

API文档将在开发完成后提供，包括：
- 用户管理API
- 课程管理API
- 学习进度API
- AI对话API

## 环境变量

项目需要以下环境变量：
- `OPENAI_API_KEY`: OpenAI API密钥
- `MONGODB_URI`: MongoDB连接字符串
- `JWT_SECRET`: JWT认证密钥

## 贡献指南

欢迎提交Pull Request和Issue。请确保：
1. 代码符合项目的编码规范
2. 提供适当的测试用例
3. 更新相关文档

## 许可证

MIT License

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from api import lesson_api, assessment_api, tts_api
from api import google_auth_api

# 加载环境变量
load_dotenv()

app = FastAPI(title="AI English Tutor API")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该限制为具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(lesson_api.router)
app.include_router(assessment_api.router)
app.include_router(tts_api.router)
app.include_router(google_auth_api.router, prefix="/api/auth")
#app.include_router(asr_api.router)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return {"message": "Welcome to AI English Tutor API"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=9000, reload=True)

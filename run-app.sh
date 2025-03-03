#!/bin/bash

# 停止并删除已存在的容器（如果有）
CONTAINER_NAME="ai-english-tutor-app"
if [ "$(docker ps -q -f name=$CONTAINER_NAME)" ]; then
    echo "停止并删除已存在的容器..."
    docker stop $CONTAINER_NAME
    docker rm $CONTAINER_NAME
fi

# 运行应用容器
echo "启动 AI English Tutor 应用..."
docker run -d \
  --name $CONTAINER_NAME \
  -p 3000:3000 \
  -p 9000:9000 \
  ai-english-tutor:dev

echo "应用已启动:"
echo "- 前端: http://localhost:3000"
echo "- 后端 API: http://localhost:9000"
echo ""
echo "查看日志: docker logs -f $CONTAINER_NAME"
echo "停止应用: docker stop $CONTAINER_NAME"

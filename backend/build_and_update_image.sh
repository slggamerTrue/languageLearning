#!/bin/bash

# 设置变量
IMAGE_NAME="ai-english-tutor-backend"
IMAGE_TAG="latest"
FULL_IMAGE_NAME="${IMAGE_NAME}:${IMAGE_TAG}"

echo "开始构建Docker镜像: ${FULL_IMAGE_NAME}"

# 构建Docker镜像
docker build -t ${FULL_IMAGE_NAME} .

# 检查构建是否成功
if [ $? -eq 0 ]; then
    echo "Docker镜像构建成功: ${FULL_IMAGE_NAME}"
    
    # 可选：推送到Docker仓库
    # 取消下面的注释并替换为您的Docker仓库地址
    # DOCKER_REGISTRY="your-registry.com"
    # REGISTRY_IMAGE="${DOCKER_REGISTRY}/${FULL_IMAGE_NAME}"
    # docker tag ${FULL_IMAGE_NAME} ${REGISTRY_IMAGE}
    # docker push ${REGISTRY_IMAGE}
    # echo "镜像已推送到: ${REGISTRY_IMAGE}"
    
    echo "您可以使用以下命令运行容器:"
    echo "docker run -p 9000:9000 -e GOOGLE_CLIENT_ID=your_client_id -e GOOGLE_CLIENT_SECRET=your_client_secret ${FULL_IMAGE_NAME}"
else
    echo "Docker镜像构建失败"
    exit 1
fi

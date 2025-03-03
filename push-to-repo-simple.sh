#!/bin/bash

# 设置变量
IMAGE_NAME="ai-english-tutor"
REGISTRY="registry.cn-chengdu.aliyuncs.com/zpdemo"
TAG=$(date +"%Y%m%d%H%M")

# 显示信息
echo "========================================="
echo "推送镜像到阿里云容器镜像服务"
echo "镜像名称: $IMAGE_NAME"
echo "目标仓库: $REGISTRY"
echo "标签: $TAG"
echo "========================================="

# 确保本地镜像存在
if ! docker image inspect $IMAGE_NAME:latest >/dev/null 2>&1; then
  echo "错误: 本地镜像 $IMAGE_NAME:latest 不存在"
  echo "请先构建镜像，例如运行 ./build-dev.sh"
  exit 1
fi

# 提示输入阿里云用户名和密码
read -p "请输入阿里云容器镜像服务用户名: " USERNAME
read -s -p "请输入密码: " PASSWORD
echo

# 登录到阿里云容器镜像服务
echo "正在登录到阿里云容器镜像服务..."
echo "$PASSWORD" | docker login --username=$USERNAME --password-stdin $REGISTRY
if [ $? -ne 0 ]; then
  echo "登录失败，请确保输入了正确的凭据"
  exit 1
fi

# 标记镜像
echo "正在标记镜像..."
docker tag $IMAGE_NAME:latest $REGISTRY/$IMAGE_NAME:$TAG
docker tag $IMAGE_NAME:latest $REGISTRY/$IMAGE_NAME:latest

# 推送镜像
echo "正在推送镜像到 $REGISTRY..."
docker push $REGISTRY/$IMAGE_NAME:$TAG
docker push $REGISTRY/$IMAGE_NAME:latest

# 完成
echo "========================================="
echo "镜像推送完成!"
echo "镜像地址:"
echo "$REGISTRY/$IMAGE_NAME:$TAG"
echo "$REGISTRY/$IMAGE_NAME:latest"
echo "========================================="

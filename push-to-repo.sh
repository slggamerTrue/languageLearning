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
if ! docker image inspect $IMAGE_NAME:dev >/dev/null 2>&1; then
  echo "错误: 本地镜像 $IMAGE_NAME:dev 不存在"
  echo "请先构建镜像，例如运行 ./build-dev.sh"
  exit 1
fi

# 登录到阿里云容器镜像服务
echo "正在登录到阿里云容器镜像服务..."
docker login --username=$ALIYUN_USERNAME $REGISTRY
if [ $? -ne 0 ]; then
  echo "登录失败，请确保已设置正确的凭据"
  echo "您可以先运行: export ALIYUN_USERNAME=您的阿里云用户名"
  echo "然后再运行此脚本，系统将提示您输入密码"
  exit 1
fi

# 标记镜像
echo "正在标记镜像..."
docker tag $IMAGE_NAME:dev $REGISTRY/$IMAGE_NAME:$TAG
docker tag $IMAGE_NAME:dev $REGISTRY/$IMAGE_NAME:latest

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

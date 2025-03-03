#!/bin/bash

# 构建开发镜像
docker build -t ai-english-tutor:dev -f Dockerfile.dev .

echo "开发镜像构建完成: ai-english-tutor:dev"

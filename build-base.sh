#!/bin/bash

# 构建基础镜像
docker build -t ai-english-tutor-base:latest -f Dockerfile.base .

echo "基础镜像构建完成: ai-english-tutor-base:latest"

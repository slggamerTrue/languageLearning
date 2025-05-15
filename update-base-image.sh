#!/bin/bash

# 设置变量
BASE_IMAGE_NAME="ai-english-tutor-base"
BASE_IMAGE_TAG="latest"
FULL_BASE_IMAGE="${BASE_IMAGE_NAME}:${BASE_IMAGE_TAG}"
UPDATED_IMAGE_NAME="${BASE_IMAGE_NAME}-updated"
UPDATED_IMAGE_TAG="latest"
FULL_UPDATED_IMAGE="${UPDATED_IMAGE_NAME}:${UPDATED_IMAGE_TAG}"

echo "开始更新基础镜像: ${FULL_BASE_IMAGE} -> ${FULL_UPDATED_IMAGE}"

# 创建临时Dockerfile
cat > Dockerfile.update << EOF
FROM ${FULL_BASE_IMAGE}

# 安装google-auth库
RUN pip install --no-cache-dir google-auth==2.23.0

# 设置工作目录
WORKDIR /app
EOF

# 构建更新后的镜像
docker build -t ${FULL_UPDATED_IMAGE} -f Dockerfile.update .

# 检查构建是否成功
if [ $? -eq 0 ]; then
    echo "更新后的镜像构建成功: ${FULL_UPDATED_IMAGE}"
    
    # 重新标记为基础镜像
    docker tag ${FULL_UPDATED_IMAGE} ${FULL_BASE_IMAGE}
    echo "已将更新后的镜像标记为基础镜像: ${FULL_BASE_IMAGE}"
    
    # 删除临时镜像
    docker rmi ${FULL_UPDATED_IMAGE}
    echo "已删除临时镜像: ${FULL_UPDATED_IMAGE}"
    
    # 删除临时Dockerfile
    rm Dockerfile.update
    echo "已删除临时Dockerfile"
    
    echo "基础镜像更新完成，现在包含google-auth库"
else
    echo "更新镜像构建失败"
    # 删除临时Dockerfile
    rm Dockerfile.update
    exit 1
fi

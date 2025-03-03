# AI English Tutor 开发环境 Docker 配置

本文档提供了使用 Docker 进行 AI English Tutor 应用程序开发的指南，采用了基础镜像 + 开发镜像的两阶段构建方法，以加速开发过程中的构建。

## 两阶段构建流程

1. **基础镜像 (Base Image)**：包含所有依赖项，如 npm 包和 pip 包
2. **开发镜像 (Dev Image)**：基于基础镜像，仅添加最新代码

这种方法的优点是，当您只更改代码而不更改依赖项时，构建会非常快速，因为不需要重新安装依赖项。

## 构建和运行说明

### 第一步：构建基础镜像

当您首次设置项目或更新依赖项时，需要构建基础镜像：

```bash
./build-base.sh
```

这将创建一个名为 `ai-english-tutor-base:latest` 的 Docker 镜像，其中包含所有前端和后端依赖项。

### 第二步：构建开发镜像

每次更新代码后，运行以下命令构建开发镜像：

```bash
./build-dev.sh
```

这将创建一个名为 `ai-english-tutor:dev` 的 Docker 镜像，其中包含最新代码。

### 第三步：使用 Docker Compose 运行应用

```bash
docker-compose -f docker-compose.dev.yml up -d
```

这将启动应用程序和 MongoDB 容器。

## 何时重建基础镜像

在以下情况下，您需要重新构建基础镜像：

1. 更新了 `package.json`（添加/删除/更新 npm 包）
2. 更新了 `requirements.txt`（添加/删除/更新 pip 包）

## 何时重建开发镜像

在以下情况下，您需要重新构建开发镜像：

1. 更新了前端或后端代码
2. 更新了配置文件

## 访问应用

- 前端：http://localhost:3000
- 后端 API：http://localhost:9000

## 停止应用

```bash
docker-compose -f docker-compose.dev.yml down
```

## 查看日志

```bash
docker-compose -f docker-compose.dev.yml logs -f app
```

## 完整工作流示例

```bash
# 首次设置或更新依赖项
./build-base.sh

# 每次代码更改后
./build-dev.sh
docker-compose -f docker-compose.dev.yml up -d

# 查看日志
docker-compose -f docker-compose.dev.yml logs -f app

# 完成后停止应用
docker-compose -f docker-compose.dev.yml down
```

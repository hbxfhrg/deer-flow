# ================================================
# DeerFlow 前端 Dockerfile（生产环境）
# 使用 node 替代 nginx 来 serve 静态文件
# ================================================

# 第一阶段：构建前端
FROM node:18-alpine AS builder

WORKDIR /app

# 复制依赖文件
COPY package.json package-lock.json ./

# 安装依赖
RUN npm install --legacy-peer-deps

# 复制源代码
COPY . .

# 构建生产版本
RUN npm run build

# 第二阶段：运行环境（使用 node 提供静态文件服务）
FROM node:18-alpine

WORKDIR /app

# 安装 http-server
RUN npm install -g http-server

# 复制构建产物
COPY --from=builder /app/dist /app/dist

# 暴露端口
EXPOSE 80

# 启动命令（使用 http-server 提供静态文件服务）
CMD ["http-server", "dist", "-p", "80", "-c-1"]
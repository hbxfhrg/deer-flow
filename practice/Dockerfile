# ================================================
# DeerFlow 前端 Dockerfile（使用 Nginx）
# ================================================

# 第一阶段：构建前端
FROM docker.1ms.run/library/node:18-alpine AS builder

WORKDIR /app

# 复制依赖文件
COPY package.json package-lock.json ./

# 在容器内安装依赖
RUN npm install --legacy-peer-deps

# 复制源代码
COPY . .

# 构建生产版本
RUN npm run build

# 第二阶段：运行环境（使用 Nginx）
FROM docker.1ms.run/library/nginx:alpine

# 复制构建产物到 Nginx 静态文件目录
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制 Nginx 配置文件
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 80

# 启动命令（Nginx 默认会自动启动）
CMD ["nginx", "-g", "daemon off;"]
# 使用官方的 Python 3.13 镜像作为基础镜像
FROM python:3.13-slim

# 设置工作目录
WORKDIR /app

# 复制当前目录的内容到工作目录
COPY . /app

# 安装所需的 Python 包
RUN pip install --no-cache-dir -r requirements.txt

# 运行应用程序
CMD ["python", "app.py"] 
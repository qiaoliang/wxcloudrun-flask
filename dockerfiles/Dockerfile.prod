FROM python:3.12

# 安装 ca-certificates 以支持 HTTPS
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 拷贝依赖文件
COPY requirements.txt requirements-test.txt ./

# 拷贝src目录到/app目录下
COPY src/ /app/

# 创建用于SQLite数据库的目录并设置权限
RUN mkdir -p /app/data && chown -R 1000:1000 /app/data

# 创建日志目录
RUN mkdir -p /app/logs && chown -R 1000:1000 /app/logs

# 安装依赖
RUN pip install --user -r requirements.txt

# 设置环境变量
ENV ENV_TYPE=prod

# 暴露端口。
# 此处端口必须与「服务设置」-「流水线」以及「手动上传代码包」部署时填写的端口一致，否则会部署失败。
EXPOSE 8080

# 执行启动命令
# 注意：主程序已移至 main.py (已复制到/app目录)
# 写多行独立的CMD命令是错误写法！只有最后一行CMD命令会被执行，之前的都会被忽略，导致业务报错。
# 请参考[Docker官方文档之CMD命令](https://docs.docker.com/engine/reference/builder/#cmd)
CMD ["python3", "main.py", "0.0.0.0", "8080"]

# 使用官方 Python 3.8 镜像
FROM python:3.8

# 安装 ca-certificates 以支持 HTTPS
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 拷贝当前项目到/app目录下（.dockerignore中文件除外）
COPY . /app

# 安装依赖
RUN pip install --user -r requirements.txt

# 暴露端口。
# 此处端口必须与「服务设置」-「流水线」以及「手动上传代码包」部署时填写的端口一致，否则会部署失败。
EXPOSE 80

# 执行启动命令
# 写多行独立的CMD命令是错误写法！只有最后一行CMD命令会被执行，之前的都会被忽略，导致业务报错。
# 请参考[Docker官方文档之CMD命令](https://docs.docker.com/engine/reference/builder/#cmd)
CMD ["python3", "run.py", "0.0.0.0", "8080"]
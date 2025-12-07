# 后端环境的调试指南

本文档介绍如何调试安全守护后端服务的不同环境。

## 前置条件

1. 查看文档 `how-to-build-and-run.md` 了解如何构建和运行不同环境的容器。
2. 并确保容器已启动。
3. 确认容器的访问地址和端口是否正确，得到后台服务的URI，即 baseURI。
   不同容器，其访问地址和端口不同，例如 对于 function 环境，baseURI 就是 `http://localhost:9999`，
   对于 UAT 和 Prod 环境，baseURI 就是 就是 `http://localhost:8080`。

## 环境变量的确认

访问 $baseURI/env, 可以查看 json 和 toml 格式的环境变量名称，以及对应的数值。

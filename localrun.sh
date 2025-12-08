#!/usr/bin/env bash
source venv_py312/bin/activate
cd src
ENV_TYPE=function python3.12 main.py 0.0.0.0 9999

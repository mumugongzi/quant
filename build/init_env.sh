#!/bin/bash

# 初始化项目环境
CURDIR=$(cd $(dirname $0); pwd)
PROJ_DIR=$CURDIR/../
cd $PROJ_DIR
virtualenv --no-site-packages .env
source  .env/bin/activate
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple/ -r requirements.txt
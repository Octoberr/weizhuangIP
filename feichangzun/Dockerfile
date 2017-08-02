FROM python:3.5.3-alpine

COPY . /opt/app
WORKDIR /opt/app

RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.ustc.edu.cn/g' /etc/apk/repositories \
        && apk update && apk add tzdata \
        && ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime  \
        && echo "Asia/Shanghai" > /etc/timezone \
        && apk del tzdata \
        && apk add --no-cache gcc musl-dev g++ libxml2-dev libxslt-dev \
        && pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt

EXPOSE 8021


CMD python main.py

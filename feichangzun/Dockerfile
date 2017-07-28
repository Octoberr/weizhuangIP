FROM python:3.5.3-alpine

COPY . /opt/app
WORKDIR /opt/app

RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.ustc.edu.cn/g' /etc/apk/repositories \
 && apk add --no-cache gcc musl-dev &&\
    pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

CMD ["python","./weihzuangIP.py"]
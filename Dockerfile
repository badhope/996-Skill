FROM python:3.11-slim

LABEL maintainer="badhope"
LABEL description="Auto-SignIn - 多平台自动签到系统"

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/logs /app/data

ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

ENV PYTHONUNBUFFERED=1

CMD ["python", "main.py", "run"]

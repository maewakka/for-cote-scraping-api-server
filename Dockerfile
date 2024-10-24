# Python 3.9 슬림 이미지를 기반으로 함
FROM python:3.9-slim

# 빌드 도구와 필요한 라이브러리 설치
RUN apt-get update && \
    apt-get install -y build-essential libev-dev && \
    rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# 필요한 패키지들을 설치 (미리 requirements.txt 파일에 명시해두기)
COPY requirements.txt requirements.txt
RUN pip install --upgrade pip
RUN pip install --no-cache-dir flask
RUN pip install -r requirements.txt

# Flask 애플리케이션 소스 복사
COPY . .

EXPOSE 7000

# Flask 애플리케이션을 실행하는 명령 추가
CMD ["python", "app.py"]

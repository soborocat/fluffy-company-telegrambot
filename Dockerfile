FROM python:3.11-slim

WORKDIR /app

# 종속성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY app.py .

# 시간대 설정 (선택사항)
ENV TZ=Asia/Seoul

# 컨테이너 실행 시 앱 시작
CMD ["python", "app.py"]

# 베이스 이미지 선택 (Python 3.10)
FROM python:3.10

# 작업 디렉토리 설정
WORKDIR /app

# 현재 디렉토리의 모든 파일을 컨테이너로 복사
COPY . .

# 의존성 설치
RUN pip install --no-cache-dir -r requirements.txt

# 사용할 포트 설정 (예: 5002)
EXPOSE 5002

# 컨테이너가 실행될 때 기본 명령어
CMD ["python", "app.py"]
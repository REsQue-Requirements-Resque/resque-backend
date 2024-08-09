FROM python:3.12.3

WORKDIR /workspace

COPY . .

# 의존성 설치
RUN pip install --no-cache-dir -r requirements.txt

# FastAPI 애플리케이션 실행
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
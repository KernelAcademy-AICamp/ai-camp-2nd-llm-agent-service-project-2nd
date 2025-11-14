FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# Streamlit 의존성 설치
RUN pip install --no-cache-dir \
    streamlit==1.28.0 \
    requests==2.31.0 \
    plotly==5.18.0 \
    pandas==2.1.4

# 애플리케이션 파일 복사
COPY . .

# Streamlit 포트 노출
EXPOSE 8501

# 헬스체크
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Streamlit 실행
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
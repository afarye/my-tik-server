FROM mcr.microsoft.com/playwright/python:latest

WORKDIR /app

# Ensure the app package is importable when mounted into /app/app
ENV PYTHONPATH=/app:$PYTHONPATH

# Use a faster mirror for Python packages to reduce network stalls during builds
ENV PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple

# Copy only requirements from the config context and install them
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --default-timeout=1000 --retries 5 --prefer-binary -r /tmp/requirements.txt

# Copy config files into the image. The application code is mounted at runtime
# by docker-compose from ../app into /app/app, so we don't need to copy it here.
COPY . /app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["python3", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]


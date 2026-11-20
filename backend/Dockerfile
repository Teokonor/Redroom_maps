FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . ./
RUN chmod +x docker-entrypoint.sh

EXPOSE 8652

ENTRYPOINT ["sh", "docker-entrypoint.sh"]
CMD ["sh", "-c", "uvicorn app.api.server:app --host 0.0.0.0 --port 8652 --workers ${WEB_CONCURRENCY:-2} --no-access-log --proxy-headers --forwarded-allow-ips=*"]

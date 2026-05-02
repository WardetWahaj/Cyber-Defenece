FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY frontend/backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY cyberdefence_platform_v31.py /app/cyberdefence_platform_v31.py
COPY config.json /app/config.json
COPY data /app/data
COPY frontend/backend/api.py /app/api.py

EXPOSE 8000

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]

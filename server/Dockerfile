# =========================
# BASE (shared)
# =========================
FROM python:3.13-slim AS base
WORKDIR /app

# do not create .pyc files
ENV PYTHONDONTWRITEBYTECODE=1 

# print output immediately, do not buffer logs.
ENV PYTHONUNBUFFERED=1

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src

EXPOSE 8000

# =========================
# DEV: reload
# =========================
FROM base AS dev
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# =========================
# PROD: workers
# =========================
FROM base AS prod
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
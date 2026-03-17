# Docker Setup

> Requires Docker Desktop to be running. No repo clone or `.env` file needed.

## Pull Images

```bash
docker pull fidelioc/marketsafe-api:latest
```
```bash
docker pull fidelioc/marketsafe-db-init:latest
```
```bash
docker pull fidelioc/marketsafe-frontend:latest
```

## Run

### 1. MySQL

```bash
docker run -d --name marketsafe-db -e MYSQL_ROOT_PASSWORD=root -e MYSQL_DATABASE=marketsafe -e MYSQL_USER=marketsafe -e MYSQL_PASSWORD=marketsafe -p 3306:3306 mysql:8.4
```

### 2. DB Init (run after MySQL is healthy)

```bash
docker run --rm --name marketsafe-db-init -e MYSQL_ROOT_PASSWORD=root -e DB_HOST=host.docker.internal -e DB_PORT=3306 -e DB_NAME=marketsafe -e DB_MODE=prod fidelioc/marketsafe-db-init:latest
```

### 3. API

```bash
docker run -d --name marketsafe-api -e DB_HOST=host.docker.internal -e DB_PORT=3306 -e DB_NAME=marketsafe -e DB_USER=marketsafe -e DB_PASSWORD=marketsafe -e SECRET_KEY=change-me -e FRONTEND_URL=http://localhost:4200 -e CORS_ALLOWED_ORIGINS=http://localhost:4200 -e APP_ENV=prod -p 8000:8000 fidelioc/marketsafe-api:latest
```

### 4. Frontend

```bash
docker run -d --name marketsafe-frontend -e API_BASE_URL=http://localhost:8000 -e FRONTEND_URL=http://localhost:4200 -p 4200:4200 fidelioc/marketsafe-frontend:latest
```

## Teardown

```bash
docker rm -f marketsafe-db marketsafe-db-init marketsafe-api marketsafe-frontend
```

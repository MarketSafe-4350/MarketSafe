# https://docs.docker.com/get-started/docker-concepts/building-images/writing-a-dockerfile/

FROM python:3.13

WORKDIR /app

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# docker run --name marketsafe-api -p 8000:8000 marketsafe-api (run container)
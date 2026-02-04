FROM node:20-alpine

WORKDIR /app

COPY package*.json ./

RUN npm install

COPY . .

EXPOSE 4200

CMD ["npm", "start"]

# docker build -t marketsafe-frontend -f frontend/Dockerfile frontend (build image)
# docker run --name marketsafe-frontend -p 4200:4200 marketsafe-frontend (run container)

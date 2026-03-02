# =========================
# DEV: Angular dev server
# =========================
FROM node:20-alpine AS dev
WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
EXPOSE 4200
CMD ["npm", "run", "start:docker"]


# =========================
# PROD: Build Angular Prod
# =========================
FROM node:20-alpine AS build
WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build


# =========================
# PROD: Serve with Nginx
# =========================
FROM nginx:alpine AS prod

COPY --from=build /app/dist/frontend/browser /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
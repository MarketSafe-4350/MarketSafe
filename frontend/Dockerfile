FROM node:20-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install --ignore-scripts

# Copy application source
COPY . .

COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Expose Angular dev server port
EXPOSE 4200

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["npm", "run", "start:docker"]

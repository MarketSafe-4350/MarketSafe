FROM node:20-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install

# Copy application source
COPY . .

# Expose Angular dev server port
EXPOSE 4200

# Start frontend
CMD ["npm", "start"]

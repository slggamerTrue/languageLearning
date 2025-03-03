FROM node:18 AS frontend-build

WORKDIR /app/frontend

# Copy frontend package.json and package-lock.json
COPY frontend/package*.json ./

# Install frontend dependencies
RUN npm install

# Copy frontend source code
COPY frontend/ ./

# Build frontend
RUN npm run build

# Backend stage
FROM python:3.10-slim

WORKDIR /app

# Copy backend requirements
COPY backend/requirements.txt .

# Install backend dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ .

# Copy built frontend from the frontend-build stage
COPY --from=frontend-build /app/frontend/build /app/static

# Expose ports for frontend and backend
EXPOSE 3000 9000

# Create a script to start both services
RUN echo '#!/bin/bash\n\
# Start the backend server\n\
uvicorn main:app --host 0.0.0.0 --port 9000 &\n\
\n\
# Start a simple HTTP server for the frontend\n\
cd /app/static && python -m http.server 3000\n\
' > /app/start.sh

RUN chmod +x /app/start.sh

# Set environment variables
ENV MONGODB_URI=mongodb://mongo:27017
ENV JWT_SECRET=your-super-secret-key-change-this-in-production

# Start both services
CMD ["/app/start.sh"]

#!/bin/bash

# Create a custom Nginx configuration with extended timeouts
cat > /etc/nginx/conf.d/default.conf << 'EOL'
server {
    listen 80;
    server_name localhost;

    # Extended timeouts for API requests
    location /api/ {
        proxy_pass http://localhost:9000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        proxy_buffering off;
    }

    location / {
        root /app/static;
        try_files $uri $uri/ /index.html;
    }
}
EOL

# Start the backend server with extended timeout
uvicorn main:app --host 0.0.0.0 --port 9000 --timeout-keep-alive 300 &

# Start Nginx
nginx -g "daemon off;"

#!/bin/bash

sudo tee /etc/nginx/sites-available/mirror > /dev/null << 'EOF'
server {
    listen 80;
    server_name 3.87.145.119.nip.io;

    location /socket.io/ {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
    }

    location /create-room {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
    }

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/mirror /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo systemctl restart nginx
sudo certbot --nginx -d 3.87.145.119.nip.io --non-interactive --agree-tos -m admin@mirror-ai.com

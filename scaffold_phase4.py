import os

devops_files = {
    "docker-compose.yml": """version: '3.8'

services:
  db:
    image: postgres:15-alpine
    restart: always
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-postgres}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-password}
      POSTGRES_DB: ${POSTGRES_DB:-sales_intel}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    networks:
      - backend_network

  redis:
    image: redis:7-alpine
    restart: always
    ports:
      - "6379:6379"
    networks:
      - backend_network

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    restart: always
    environment:
      - DATABASE_URL=postgresql://${POSTGRES_USER:-postgres}:${POSTGRES_PASSWORD:-password}@db:5432/${POSTGRES_DB:-sales_intel}
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=${SECRET_KEY:-SUPER_SECRET_KEY_PRODUCTION}
    depends_on:
      - db
      - redis
    networks:
      - backend_network
      - proxy_network

  worker:
    build:
      context: ./backend
      dockerfile: Dockerfile.worker
    restart: always
    command: celery -A app.worker.celery_app worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql://${POSTGRES_USER:-postgres}:${POSTGRES_PASSWORD:-password}@db:5432/${POSTGRES_DB:-sales_intel}
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    depends_on:
      - db
      - redis
    networks:
      - backend_network

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    restart: always
    environment:
      - NEXT_PUBLIC_API_URL=https://api.yourdomain.com/api/v1
    networks:
      - proxy_network

  nginx:
    image: nginx:alpine
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./certbot/conf:/etc/letsencrypt
      - ./certbot/www:/var/www/certbot
    depends_on:
      - backend
      - frontend
    networks:
      - proxy_network

  prometheus:
    image: prom/prometheus
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
    networks:
      - backend_network

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    depends_on:
      - prometheus
    networks:
      - backend_network

volumes:
  postgres_data:

networks:
  backend_network:
  proxy_network:
""",

    "frontend/Dockerfile": """FROM node:20-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV production

COPY --from=builder /app/next.config.js ./
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

EXPOSE 3000
CMD ["npm", "start"]
""",

    "backend/Dockerfile.worker": """FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \\
    build-essential \\
    libpq-dev \\
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt celery redis

COPY . .

# Worker entrypoint handled in docker-compose command
""",

    "backend/app/worker.py": """import os
from celery import Celery

broker_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
result_backend = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

celery_app = Celery(
    "sales_intel_worker",
    broker=broker_url,
    backend=result_backend
)

celery_app.conf.task_routes = {
    "app.worker.train_model": "ml-queue",
    "app.worker.process_data": "data-queue"
}

@celery_app.task(name="app.worker.train_model")
def train_model(sku: str):
    # ML pipeline execution logic here
    return f"Model trained for {sku}"
""",

    "nginx/nginx.conf": """events {
    worker_connections 1024;
}

http {
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

    upstream frontend_servers {
        server frontend:3000;
    }

    upstream backend_servers {
        server backend:8000;
    }

    server {
        listen 80;
        server_name yourdomain.com;
        
        location /.well-known/acme-challenge/ {
            root /var/www/certbot;
        }

        location / {
            return 301 https://$host$request_uri;
        }
    }

    server {
        listen 443 ssl;
        server_name yourdomain.com;

        # ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
        # ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

        # Frontend Route
        location / {
            proxy_pass http://frontend_servers;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        # Backend API Route
        location /api/ {
            limit_req zone=api_limit burst=20 nodelay;
            proxy_pass http://backend_servers;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_addrs;
        }
    }
}
""",

    "monitoring/prometheus.yml": """global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'fastapi_backend'
    static_configs:
      - targets: ['backend:8000']
""",

    ".github/workflows/deploy.yml": """name: Production CI/CD

on:
  push:
    branches: [ "main" ]

jobs:
  test-and-build:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
        
    - name: Install backend dependencies
      run: |
        cd backend
        pip install -r requirements.txt pytest
        
    - name: Run Tests
      run: |
        cd backend
        pytest tests/
        
    - name: Build Docker Images
      run: |
        docker build -t sales-intel-backend ./backend
        docker build -t sales-intel-frontend ./frontend
        docker build -t sales-intel-worker -f ./backend/Dockerfile.worker ./backend

  deploy-production:
    needs: test-and-build
    runs-on: ubuntu-latest
    environment: production
    steps:
    - name: Deploy to Server
      uses: appleboy/ssh-action@master
      with:
        host: ${{ secrets.SERVER_IP }}
        username: ${{ secrets.SERVER_USER }}
        key: ${{ secrets.SSH_PRIVATE_KEY }}
        script: |
          cd /opt/sales-intel
          git pull origin main
          docker-compose -f docker-compose.yml down
          docker-compose -f docker-compose.yml up -d --build
"""
}

def create_phase4():
    for filepath, content in devops_files.items():
        os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

if __name__ == "__main__":
    create_phase4()
    print("Phase 4 setup (DevOps, Docker, CI/CD, Celery) completed successfully!")


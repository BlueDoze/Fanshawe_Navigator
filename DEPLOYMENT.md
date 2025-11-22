# Fanshawe Navigator - Deployment Guide

This guide covers various deployment strategies for the Fanshawe Navigator project, from simple development setups to production-ready infrastructure.

## 📋 Project Architecture

The project consists of two main services:
- **Backend**: Python FastAPI server (port 8000)
- **Frontend**: React application with Vite (port 3000 in dev)

## 🐳 Docker Deployment Options

### Option 1: Development with Docker Compose (Recommended for Team Dev)

**Benefits:**
- Consistent environment across all developers
- Easy setup for new team members
- Services auto-restart on code changes
- Isolated from local machine configuration

**File Structure:**
```
New_Project/
├── docker-compose.yml
├── .env
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── ... (Python code)
└── frontend/
    ├── Dockerfile
    ├── package.json
    └── ... (React code)
```

**Backend Dockerfile Example:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

**Frontend Dockerfile (Development):**
```dockerfile
FROM node:18-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install

# Copy application code
COPY . .

# Expose port
EXPOSE 3000

# Run development server
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
```

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
      - /app/__pycache__
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
    restart: unless-stopped

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    environment:
      - VITE_API_URL=http://localhost:8000
    depends_on:
      - backend
    restart: unless-stopped
```

**Usage:**
```bash
# Start all services
docker-compose up

# Start in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild after changes
docker-compose up --build
```

---

### Option 2: Production Docker Setup

**Production optimizations:**
- Multi-stage builds for smaller images
- Static file serving
- Production ASGI server (Gunicorn)
- Security hardening

**Backend Dockerfile (Production):**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy application
COPY . .

# Create non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Use Gunicorn with Uvicorn workers
CMD ["gunicorn", "api:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000"]
```

**Frontend Dockerfile (Production - Multi-stage):**
```dockerfile
# Build stage
FROM node:18-alpine AS build

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built files
COPY --from=build /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

**nginx.conf (for production frontend):**
```nginx
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

**docker-compose.prod.yml:**
```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    expose:
      - "8000"
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
    restart: always
    networks:
      - app-network

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: always
    networks:
      - app-network

networks:
  app-network:
    driver: bridge
```

**Usage:**
```bash
docker-compose -f docker-compose.prod.yml up -d
```

---

### Option 3: Single Container (Simplified Production)

Serve React build from FastAPI - simpler deployment, one container.

**Modified Backend Structure:**
```python
# In api.py, add:
from fastapi.staticfiles import StaticFiles

# Mount the built frontend
app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="frontend")
```

**Build process:**
```bash
# Build frontend
cd frontend
npm run build
cd ..

# Build single container
docker build -t fanshawe-navigator .
docker run -p 8000:8000 -e GEMINI_API_KEY=your_key fanshawe-navigator
```

---

## ☁️ Cloud Platform Deployments

### Vercel (Frontend Only - Easiest)

**Setup:**
1. Push code to GitHub
2. Connect Vercel to your repository
3. Configure build settings:
   - Framework: Vite
   - Root Directory: `frontend`
   - Build Command: `npm run build`
   - Output Directory: `dist`
4. Add environment variable: `VITE_API_URL=https://your-backend.com`

**Benefits:**
- Automatic deployments on Git push
- Free tier available
- CDN included
- SSL certificates automatic

### Railway.app (Full Stack)

**Setup:**
1. Install Railway CLI: `npm i -g @railway/cli`
2. Login: `railway login`
3. Initialize: `railway init`
4. Deploy: `railway up`

**railway.json:**
```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "numReplicas": 1,
    "restartPolicyType": "ON_FAILURE"
  }
}
```

**Benefits:**
- Easy deployment from Git
- Environment variable management
- Free tier ($5 credit/month)
- Auto-scaling available

### Render.com (Full Stack)

**Setup:**
1. Create account at render.com
2. Connect GitHub repository
3. Create Web Services:
   - **Backend**: Python service
     - Build Command: `pip install -r requirements.txt`
     - Start Command: `uvicorn api:app --host 0.0.0.0 --port $PORT`
   - **Frontend**: Static site
     - Build Command: `npm run build`
     - Publish Directory: `dist`

**Benefits:**
- Free tier for static sites
- Easy SSL setup
- Auto-deploy from Git
- Good documentation

### AWS Deployment (Professional)

**Architecture:**
- **Frontend**: S3 + CloudFront
- **Backend**: ECS Fargate or App Runner
- **Secrets**: AWS Secrets Manager
- **Logs**: CloudWatch

**Steps:**
1. Build Docker images
2. Push to ECR (Elastic Container Registry)
3. Create ECS task definition
4. Deploy to Fargate
5. Build React app and upload to S3
6. Configure CloudFront distribution

**Estimated Cost:**
- S3 + CloudFront: ~$1-5/month
- ECS Fargate: ~$10-30/month (always-on small instance)

### Azure Deployment

**Services:**
- **Frontend**: Azure Static Web Apps
- **Backend**: Azure Container Apps
- **Secrets**: Azure Key Vault

**Setup:**
```bash
# Install Azure CLI
az login

# Create resource group
az group create --name fanshawe-navigator-rg --location eastus

# Deploy container app
az containerapp up --name fanshawe-backend --resource-group fanshawe-navigator-rg --image your-image

# Deploy static web app
az staticwebapp create --name fanshawe-frontend --resource-group fanshawe-navigator-rg
```

---

## 🗄️ Database Options

Currently using JSON files. For production, consider:

### SQLite (Simplest)
- File-based, no server needed
- Good for < 100k users
- Easy to backup
- Docker volume mount for persistence

### PostgreSQL (Recommended)
- Robust, production-ready
- Add to docker-compose:

```yaml
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: fanshawe_nav
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:
```

### MongoDB (Document-based)
- Good for flexible schemas
- JSON-like data storage
- Docker setup similar to PostgreSQL

---

## 🔐 Environment Variables Management

### Development (.env file)
```bash
# .env
GEMINI_API_KEY=your_api_key_here
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname
ENVIRONMENT=development
```

### Production (Secrets Management)

**Docker Secrets:**
```yaml
services:
  backend:
    secrets:
      - gemini_api_key

secrets:
  gemini_api_key:
    file: ./secrets/gemini_key.txt
```

**Cloud Platforms:**
- Vercel: Project Settings → Environment Variables
- Railway: Project Settings → Variables
- AWS: Secrets Manager or Parameter Store
- Azure: Key Vault

---

## 🚀 CI/CD Pipeline

### GitHub Actions Example

**.github/workflows/deploy.yml:**
```yaml
name: Deploy

on:
  push:
    branches: [ main ]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Build Backend Docker Image
      run: docker build -t fanshawe-backend ./backend
    
    - name: Build Frontend
      run: |
        cd frontend
        npm install
        npm run build
    
    - name: Deploy to Production
      run: |
        # Add your deployment commands here
        # e.g., push to registry, update ECS, etc.
```

---

## 📊 Monitoring & Logging

### Development
- Docker logs: `docker-compose logs -f`
- FastAPI debug mode
- React dev tools

### Production
- **Sentry**: Error tracking
- **LogRocket**: Frontend monitoring
- **Datadog/New Relic**: Full-stack monitoring
- **CloudWatch/Azure Monitor**: Cloud-native monitoring

---

## 🔄 Recommended Deployment Path

### Phase 1: Development
```bash
docker-compose up
```
Easy local development with hot reload

### Phase 2: Testing/Staging
- Deploy to Render.com or Railway (free tier)
- Test with team
- Validate integrations

### Phase 3: Production
- Choose based on scale:
  - **Small (<1000 users)**: Render/Railway
  - **Medium (<10k users)**: Docker on VPS (DigitalOcean)
  - **Large (>10k users)**: AWS/Azure with auto-scaling

---

## 💰 Cost Estimates

### Free Tier Options
- Vercel (Frontend): Free
- Render (Backend): $7/month after free tier
- **Total: $0-7/month**

### Professional Setup
- AWS S3 + CloudFront: $5/month
- AWS ECS Fargate: $20/month
- RDS PostgreSQL: $15/month
- **Total: ~$40/month**

### Enterprise
- Multi-region deployment
- Auto-scaling
- 99.9% uptime SLA
- **Total: $200+/month**

---

## 🛠️ Quick Start Commands

### Docker Development
```bash
# Create .env file
echo "GEMINI_API_KEY=your_key" > .env

# Start services
docker-compose up

# Access:
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Production Build
```bash
# Build frontend
cd frontend && npm run build

# Build and push Docker images
docker build -t your-registry/fanshawe-backend ./backend
docker build -t your-registry/fanshawe-frontend ./frontend
docker push your-registry/fanshawe-backend
docker push your-registry/fanshawe-frontend
```

---

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Vite Production Build](https://vitejs.dev/guide/build.html)
- [AWS ECS Guide](https://docs.aws.amazon.com/ecs/)
- [Railway Documentation](https://docs.railway.app/)
- [Render Documentation](https://render.com/docs)

---

## 🔧 Troubleshooting

### Docker Issues
```bash
# Clear all containers and images
docker system prune -a

# Rebuild without cache
docker-compose build --no-cache

# View container logs
docker-compose logs backend
```

### Port Conflicts
```bash
# Check what's using a port
netstat -ano | findstr :8000

# Change ports in docker-compose.yml
ports:
  - "8001:8000"  # Host:Container
```

### Environment Variables Not Loading
```bash
# Check .env file exists
ls -la .env

# Verify in container
docker-compose exec backend env | grep GEMINI
```

---

**Next Steps:** Choose your deployment strategy based on your needs and budget. For learning/testing, start with Docker Compose locally, then deploy to Render or Railway for a public demo.

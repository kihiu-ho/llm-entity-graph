# 🚀 Deploy Agentic RAG Web UI to Claw Cloud

## Quick Start Deployment

### Prerequisites
- GitHub repository with your code
- Claw Cloud account at [console.run.claw.cloud](https://console.run.claw.cloud)

### 🎯 Option 1: Web Console Deployment (Recommended)

1. **Go to [console.run.claw.cloud](https://console.run.claw.cloud)**

2. **Click "Deploy from Git"**

3. **Repository Configuration:**
   - **Repository URL**: `https://github.com/your-username/llm-entity-graph.git`
   - **Branch**: `main`
   - **Build Context**: `/` (root directory)
   - **Dockerfile**: `Dockerfile.claw`

4. **Application Settings:**
   - **Application Name**: `agentic-rag-webui`
   - **Container Port**: `5000`
   - **Health Check Path**: `/health`

5. **Environment Variables** (click "Add Environment Variable"):
   ```
   WEB_UI_HOST=0.0.0.0
   WEB_UI_PORT=5000
   API_BASE_URL=https://your-api-server.claw.cloud
   APP_ENV=production
   LOG_LEVEL=INFO
   FLASK_ENV=production
   ```

6. **Resource Configuration:**
   - **CPU**: `500m` (0.5 cores)
   - **Memory**: `1Gi` (1GB)
   - **Min Replicas**: `1`
   - **Max Replicas**: `3`

7. **Click "Deploy"**

### 🎯 Option 2: Claw CLI Deployment

1. **Install Claw CLI:**
   ```bash
   npm install -g @claw/cli
   # or
   curl -sSL https://get.claw.cloud | bash
   ```

2. **Login:**
   ```bash
   claw login
   ```

3. **Deploy:**
   ```bash
   claw deploy
   ```

## 📋 Deployment Configurations

### Scenario 1: Web UI Only (External API)
Use this when you have a separate API server running elsewhere:

**Environment Variables:**
```bash
WEB_UI_HOST=0.0.0.0
WEB_UI_PORT=5000
API_BASE_URL=https://your-api-server.claw.cloud  # Update this!
APP_ENV=production
LOG_LEVEL=INFO
```

**Command:**
```bash
python web_ui/start.py --host 0.0.0.0 --port 5000 --skip-health-check --production
```

### Scenario 2: Combined API + Web UI
Use this to run both the API server and Web UI in one container:

**Environment Variables:**
```bash
WEB_UI_HOST=0.0.0.0
WEB_UI_PORT=5000
API_BASE_URL=http://localhost:8058
APP_ENV=production
LOG_LEVEL=INFO

# Database Configuration
DATABASE_URL=postgresql://user:pass@host:port/db
NEO4J_URI=neo4j+s://instance.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password

# LLM Configuration
LLM_PROVIDER=openai
LLM_API_KEY=your-openai-api-key
EMBEDDING_API_KEY=your-openai-api-key
LLM_CHOICE=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small
```

**Command:**
```bash
bash -c "python -m agent.api --host 0.0.0.0 --port 8058 & python web_ui/start.py --host 0.0.0.0 --port 5000 --api-url http://localhost:8058 --skip-health-check --production"
```

## 🔧 Configuration Files Created

The deployment preparation script created these files:

### `.clawrc` - Claw Configuration
```json
{
  "name": "agentic-rag-webui",
  "framework": "python",
  "python_version": "3.11",
  "port": 5000,
  "health_check": {
    "path": "/health",
    "port": 5000
  }
}
```

### `Dockerfile.claw` - Optimized Dockerfile
- Python 3.11 slim base image
- Optimized layer caching
- Non-root user for security
- Health check included

### `.env.claw` - Environment Template
Contains all necessary environment variables with comments

## 🧪 Testing Your Deployment

### 1. Local Testing with Docker
```bash
# Build and test locally
docker build -f Dockerfile.claw -t agentic-rag-webui .
docker run -p 5000:5000 -e API_BASE_URL=https://your-api.claw.cloud agentic-rag-webui
```

### 2. Local Testing with Docker Compose
```bash
# Update API_BASE_URL in docker-compose.yml first
docker-compose up
```

### 3. Production Testing
Once deployed, test these endpoints:

```bash
# Health check
curl https://your-app.claw.cloud/health

# Web interface
open https://your-app.claw.cloud
```

## 🔍 Monitoring and Troubleshooting

### Check Deployment Status
1. Go to [console.run.claw.cloud](https://console.run.claw.cloud)
2. Find your application
3. Check "Logs" tab for any errors
4. Monitor "Metrics" for performance

### Common Issues and Solutions

#### Build Failures
```bash
# Issue: Requirements not found
# Solution: Ensure requirements.txt files exist in correct locations
ls requirements.txt web_ui/requirements.txt
```

#### Runtime Errors
```bash
# Issue: Port binding errors
# Solution: Ensure host is 0.0.0.0 and port is 5000
WEB_UI_HOST=0.0.0.0
WEB_UI_PORT=5000
```

#### API Connection Issues
```bash
# Issue: Cannot connect to API
# Solution: Update API_BASE_URL to correct endpoint
API_BASE_URL=https://your-actual-api-server.claw.cloud
```

### Debug Commands
```bash
# Check environment variables
python -c "import os; print('API_BASE_URL:', os.getenv('API_BASE_URL'))"

# Test API connectivity
curl -X GET https://your-api-server.claw.cloud/health

# Check web UI health
curl -X GET https://your-webui.claw.cloud/health
```

## 🚀 Production Optimization

### Performance Tuning
```bash
# Gunicorn workers (add to environment)
GUNICORN_WORKERS=4
GUNICORN_TIMEOUT=120
GUNICORN_MAX_REQUESTS=1000
```

### Scaling Configuration
- **Auto-scaling**: Enable in claw.cloud console
- **Min replicas**: 1 (always have one instance)
- **Max replicas**: 3-5 (based on expected traffic)
- **CPU threshold**: 70% (scale up when CPU > 70%)

### Security Best Practices
- Use HTTPS (automatically provided by claw.cloud)
- Set secure environment variables
- Keep dependencies updated
- Monitor for security vulnerabilities

## 📞 Support and Resources

### Documentation
- **Claw Cloud Docs**: [docs.run.claw.cloud](https://docs.run.claw.cloud)
- **Web UI Guide**: `web_ui/README.md`
- **API Documentation**: `agent/README.md`

### Getting Help
1. **Check application logs** in claw.cloud console
2. **Review health endpoints** for status information
3. **Test API connectivity** separately
4. **Check environment variables** configuration

### Useful URLs
- **Claw Console**: [console.run.claw.cloud](https://console.run.claw.cloud)
- **Claw Documentation**: [docs.run.claw.cloud](https://docs.run.claw.cloud)
- **GitHub Repository**: Your repository URL

## 🎉 Success Checklist

After deployment, verify:
- ✅ Application builds successfully
- ✅ Health check endpoint responds
- ✅ Web interface loads correctly
- ✅ API connection status shows as connected
- ✅ Chat functionality works
- ✅ No errors in application logs

Your Agentic RAG Web UI should now be live at: `https://your-app.claw.cloud`

## 🔄 Updates and Maintenance

### Deploying Updates
1. **Push changes** to your GitHub repository
2. **Trigger redeploy** in claw.cloud console
3. **Monitor deployment** logs for any issues
4. **Test functionality** after deployment

### Monitoring
- Set up **log alerts** for errors
- Monitor **response times** and **uptime**
- Track **resource usage** and scale as needed
- Review **security updates** regularly

Happy deploying! 🚀

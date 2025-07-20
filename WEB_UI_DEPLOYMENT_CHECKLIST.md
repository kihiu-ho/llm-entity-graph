# 🌐 Web UI Deployment Checklist for Claw Cloud

## ✅ Pre-Deployment Validation

### Files Created ✅
- [x] `.clawrc` - Claw Cloud configuration
- [x] `Dockerfile.claw` - Optimized Dockerfile  
- [x] `.env.claw` - Environment template
- [x] `docker-compose.yml` - Local testing
- [x] `DEPLOY_TO_CLAW.md` - Deployment guide
- [x] `CLAW_CLOUD_DEPLOYMENT_GUIDE.md` - Comprehensive guide

### Required Files Present ✅
- [x] `web_ui/app.py` - Flask application
- [x] `web_ui/start.py` - Startup script
- [x] `web_ui/requirements.txt` - Web UI dependencies
- [x] `web_ui/templates/index.html` - HTML template
- [x] `web_ui/static/css/style.css` - Styling
- [x] `web_ui/static/js/app.js` - JavaScript
- [x] `requirements.txt` - Root dependencies

### Neo4j NVL Library Setup ✅
- [x] `web_ui/package.json` - Node.js dependencies including:
  - [x] `@neo4j-nvl/base` - Core NVL library
  - [x] `@neo4j-nvl/interaction-handlers` - DragNodeInteraction and other handlers
- [x] `web_ui/webpack.config.js` - Webpack configuration for bundling
- [x] `web_ui/src/nvl-bundle.js` - NVL bundle source with interaction handlers
- [x] `web_ui/static/js/dist/nvl.bundle.js` - Built NVL bundle (auto-generated)
- [x] `web_ui/static/js/neo4j-graph-visualization.js` - Graph visualization with DragNodeInteraction

## 🚀 Deployment Steps

### Step 1: Repository Setup
- [ ] Code committed to GitHub
- [ ] Repository is public or accessible to Claw Cloud
- [ ] All deployment files are in the repository

### Step 2: Claw Cloud Console
- [ ] Go to [console.run.claw.cloud](https://console.run.claw.cloud)
- [ ] Login to your account
- [ ] Click "Deploy from Git"

### Step 3: Repository Configuration
- [ ] **Repository URL**: `https://github.com/your-username/llm-entity-graph.git`
- [ ] **Branch**: `main`
- [ ] **Build Context**: `/` (root directory)
- [ ] **Dockerfile**: `Dockerfile.claw`

**Note**: The `Dockerfile.claw` includes:
- ✅ Node.js installation for Neo4j NVL library
- ✅ `npm install` to install `@neo4j-nvl/base` and `@neo4j-nvl/interaction-handlers`
- ✅ `npm run build` to create the NVL bundle with DragNodeInteraction
- ✅ Bundle verification to ensure proper build

### Step 4: Application Settings
- [ ] **Application Name**: `agentic-rag-webui`
- [ ] **Container Port**: `5000`
- [ ] **Health Check Path**: `/health`
- [ ] **Health Check Port**: `5000`
- [ ] **Initial Delay**: `30` seconds
- [ ] **Timeout**: `10` seconds

### Step 5: Environment Variables ⚠️ IMPORTANT
**Required Variables** (copy from `.env.claw`):
- [ ] `WEB_UI_HOST=0.0.0.0`
- [ ] `WEB_UI_PORT=5000`
- [ ] `API_BASE_URL=https://your-api-server.claw.cloud` ⚠️ **UPDATE THIS!**
- [ ] `APP_ENV=production`
- [ ] `LOG_LEVEL=INFO`
- [ ] `FLASK_ENV=production`

**Optional Variables**:
- [ ] `APP_TITLE="Your Company RAG Assistant"`
- [ ] `GUNICORN_WORKERS=4`
- [ ] `GUNICORN_TIMEOUT=120`

### Step 6: Resource Configuration
- [ ] **CPU**: `500m` (0.5 cores)
- [ ] **Memory**: `1Gi` (1GB)
- [ ] **Min Replicas**: `1`
- [ ] **Max Replicas**: `3`
- [ ] **Auto-scaling**: Enabled at 70% CPU

### Step 7: Deploy
- [ ] Click "Deploy" button
- [ ] Monitor build logs for errors
- [ ] Wait for "Deployment Successful" message
- [ ] Note the assigned URL: `https://your-app.claw.cloud`

## 🧪 Post-Deployment Testing

### Health Check
- [ ] Test: `curl https://your-app.claw.cloud/health`
- [ ] Expected: `{"status": "healthy", "timestamp": "..."}`
- [ ] Status: ✅ Pass / ❌ Fail

### Web Interface
- [ ] Open `https://your-app.claw.cloud` in browser
- [ ] Page loads without errors
- [ ] Chat interface is visible
- [ ] Connection status indicator shows
- [ ] No JavaScript console errors

### Chat Functionality
- [ ] Send test message: "Hello"
- [ ] Receive response (or appropriate error message)
- [ ] Check API connection status
- [ ] Verify error handling for API unavailable

### Performance
- [ ] Page load time < 3 seconds
- [ ] Chat response time < 10 seconds
- [ ] No memory leaks during extended use
- [ ] Mobile responsiveness works

## 🔧 Configuration Scenarios

### Scenario A: Web UI Only ✅ Recommended
**When**: You have a separate API server

**Configuration**:
```bash
API_BASE_URL=https://your-api-server.claw.cloud
```

**Benefits**: 
- Simpler deployment
- Independent scaling
- Easier troubleshooting

### Scenario B: Combined Deployment
**When**: You want API + Web UI in one container

**Additional Environment Variables**:
```bash
DATABASE_URL=postgresql://user:pass@host:port/db
NEO4J_URI=neo4j+s://instance.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password
LLM_PROVIDER=openai
LLM_API_KEY=your-openai-api-key
```

**Command Override**:
```bash
bash -c "python -m agent.api --host 0.0.0.0 --port 8058 & python web_ui/start.py --host 0.0.0.0 --port 5000 --api-url http://localhost:8058 --skip-health-check --production"
```

## 🚨 Troubleshooting Guide

### Build Failures
**Issue**: `pip install` fails
- [ ] Check `requirements.txt` files exist
- [ ] Verify Python version (3.11)
- [ ] Review build logs for specific errors

**Issue**: Dockerfile errors
- [ ] Verify `Dockerfile.claw` syntax
- [ ] Check file paths are correct
- [ ] Ensure base image is accessible

### Runtime Errors
**Issue**: Application won't start
- [ ] Check environment variables
- [ ] Verify port configuration (5000)
- [ ] Review application logs

**Issue**: Health check fails
- [ ] Test `/health` endpoint manually
- [ ] Check if app is binding to 0.0.0.0:5000
- [ ] Verify health check configuration

### API Connection Issues
**Issue**: "Cannot connect to API"
- [ ] Verify `API_BASE_URL` is correct
- [ ] Test API server separately
- [ ] Check network connectivity
- [ ] Verify API server is running

**Issue**: CORS errors
- [ ] Check API server CORS configuration
- [ ] Verify Web UI origin is allowed
- [ ] Test with browser dev tools

### Performance Issues
**Issue**: Slow response times
- [ ] Check resource limits (CPU/Memory)
- [ ] Monitor application metrics
- [ ] Consider increasing replicas
- [ ] Review gunicorn configuration

## 📊 Monitoring Setup

### Key Metrics
- [ ] **Response Time**: < 2 seconds
- [ ] **Error Rate**: < 1%
- [ ] **Uptime**: > 99.9%
- [ ] **CPU Usage**: < 70%
- [ ] **Memory Usage**: < 80%

### Alerts to Set Up
- [ ] Health check failures
- [ ] High error rates
- [ ] Resource usage spikes
- [ ] Deployment failures

### Log Monitoring
- [ ] Application errors
- [ ] API connection failures
- [ ] User interaction patterns
- [ ] Performance bottlenecks

## 🔄 Maintenance

### Regular Tasks
- [ ] **Daily**: Check application health
- [ ] **Weekly**: Review logs and metrics
- [ ] **Monthly**: Update dependencies
- [ ] **Quarterly**: Review resource allocation

### Update Process
1. [ ] Push changes to GitHub
2. [ ] Trigger redeploy in Claw console
3. [ ] Monitor deployment progress
4. [ ] Test functionality
5. [ ] Verify no regressions

## ✅ Success Criteria

Your Web UI deployment is successful when:
- [x] ✅ Build completes without errors
- [ ] ✅ Health check returns 200 OK
- [ ] ✅ Web interface loads correctly
- [ ] ✅ Chat functionality works
- [ ] ✅ API connection status is accurate
- [ ] ✅ No errors in logs
- [ ] ✅ Performance is acceptable
- [ ] ✅ Mobile interface works

## 📞 Quick Reference

### Important URLs
- **Claw Console**: [console.run.claw.cloud](https://console.run.claw.cloud)
- **Documentation**: [docs.run.claw.cloud](https://docs.run.claw.cloud)
- **Your Web UI**: `https://your-app.claw.cloud`

### Key Commands
```bash
# Health check
curl https://your-app.claw.cloud/health

# Local testing
docker-compose up

# Build locally
docker build -f Dockerfile.claw -t webui .
```

### Environment Variables Template
```bash
WEB_UI_HOST=0.0.0.0
WEB_UI_PORT=5000
API_BASE_URL=https://your-api-server.claw.cloud  # UPDATE THIS!
APP_ENV=production
LOG_LEVEL=INFO
FLASK_ENV=production
```

---

**Deployment Status**: ⏳ In Progress / ✅ Complete / ❌ Failed
**Deployment URL**: `https://your-app.claw.cloud`
**Last Updated**: `[Date]`

🚀 **Ready to deploy!** Follow this checklist for a successful Web UI deployment to Claw Cloud.

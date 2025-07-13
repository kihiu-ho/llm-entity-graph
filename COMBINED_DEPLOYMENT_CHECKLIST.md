# ✅ Combined API + Web UI Deployment Checklist

## 🎯 Pre-Deployment Setup

### Database Preparation
- [ ] **PostgreSQL Database Ready**
  - [ ] Database created and accessible
  - [ ] Connection string available: `postgresql://user:pass@host:port/db`
  - [ ] Test connection works
  
- [ ] **Neo4j Database Ready**
  - [ ] Neo4j AuraDB instance created
  - [ ] Connection details available: `neo4j+s://instance.databases.neo4j.io`
  - [ ] Username and password ready
  - [ ] Test connection works

### API Keys and Credentials
- [ ] **OpenAI API Key**
  - [ ] Valid API key obtained
  - [ ] Sufficient credits/quota available
  - [ ] Key tested with API calls
  
- [ ] **Environment Variables Prepared**
  - [ ] All required variables documented
  - [ ] Sensitive data secured
  - [ ] Test values validated

## 🚀 Deployment Configuration

### Repository Setup
- [ ] **Code Repository**
  - [ ] All code committed to GitHub
  - [ ] Repository is public or accessible to Claw Cloud
  - [ ] `Dockerfile.claw` present in root
  - [ ] `start_combined.sh` present and executable

### Claw Cloud Console Setup
- [ ] **Application Configuration**
  - [ ] Repository URL: `https://github.com/your-username/llm-entity-graph.git`
  - [ ] Branch: `main`
  - [ ] Build Context: `/`
  - [ ] Dockerfile: `Dockerfile.claw`
  - [ ] Application Name: `agentic-rag-combined`

### Resource Configuration
- [ ] **Container Settings**
  - [ ] Container Port: `5000`
  - [ ] Health Check Path: `/health`
  - [ ] Health Check Port: `5000`
  - [ ] CPU: `1000m` (1 core)
  - [ ] Memory: `2Gi` (2GB)
  - [ ] Min Replicas: `1`
  - [ ] Max Replicas: `2`

## ⚙️ Environment Variables

### Required Database Variables
- [ ] `DATABASE_URL=postgresql://user:password@host:port/database`
- [ ] `NEO4J_URI=neo4j+s://instance.databases.neo4j.io`
- [ ] `NEO4J_USERNAME=neo4j`
- [ ] `NEO4J_PASSWORD=your-neo4j-password`

### Required LLM Variables
- [ ] `LLM_PROVIDER=openai`
- [ ] `LLM_API_KEY=your-openai-api-key`
- [ ] `EMBEDDING_API_KEY=your-openai-api-key`
- [ ] `LLM_CHOICE=gpt-4o-mini`
- [ ] `EMBEDDING_MODEL=text-embedding-3-small`

### Application Configuration Variables
- [ ] `WEB_UI_HOST=0.0.0.0`
- [ ] `WEB_UI_PORT=5000`
- [ ] `API_BASE_URL=http://localhost:8058`
- [ ] `API_HOST=0.0.0.0`
- [ ] `API_PORT=8058`
- [ ] `APP_ENV=production`
- [ ] `LOG_LEVEL=INFO`
- [ ] `FLASK_ENV=production`

### Optional Performance Variables
- [ ] `GUNICORN_WORKERS=4`
- [ ] `GUNICORN_TIMEOUT=120`
- [ ] `GUNICORN_MAX_REQUESTS=1000`

## 🧪 Pre-Deployment Testing

### Local Testing with Docker
- [ ] **Build Test**
  ```bash
  docker build -f Dockerfile.claw -t combined-test .
  ```
  
- [ ] **Run Test** (with real environment variables)
  ```bash
  docker run -p 5000:5000 -p 8058:8058 \
    -e DATABASE_URL="your-db-url" \
    -e NEO4J_URI="your-neo4j-uri" \
    -e NEO4J_USERNAME="neo4j" \
    -e NEO4J_PASSWORD="your-password" \
    -e LLM_API_KEY="your-api-key" \
    combined-test
  ```

### Local Testing with Docker Compose
- [ ] **Update docker-compose.yml** with real credentials
- [ ] **Run Combined Stack**
  ```bash
  docker-compose up
  ```
- [ ] **Test Health Endpoints**
  ```bash
  curl http://localhost:5000/health
  curl http://localhost:8058/health
  ```

## 🚀 Deployment Execution

### Step 1: Deploy to Claw Cloud
- [ ] Click "Deploy" in Claw Cloud console
- [ ] Monitor build logs for errors
- [ ] Wait for "Deployment Successful" message
- [ ] Note assigned URL: `https://your-app.claw.cloud`

### Step 2: Monitor Startup
- [ ] Check application logs for startup messages:
  - [ ] `🚀 Starting Combined Agentic RAG API + Web UI`
  - [ ] `✅ All required environment variables are set`
  - [ ] `✅ API server is ready!`
  - [ ] `✅ Web UI server is ready!`
  - [ ] `🎉 Combined deployment started successfully!`

## 🧪 Post-Deployment Testing

### Health Checks
- [ ] **Web UI Health Check**
  ```bash
  curl https://your-app.claw.cloud/health
  ```
  Expected response:
  ```json
  {
    "status": "healthy",
    "timestamp": "2024-01-01T12:00:00Z",
    "api_status": "connected"
  }
  ```

### Web Interface Testing
- [ ] **Basic Functionality**
  - [ ] Open `https://your-app.claw.cloud` in browser
  - [ ] Page loads without errors
  - [ ] Chat interface is visible
  - [ ] Connection status shows "Connected"
  - [ ] No JavaScript console errors

### Chat Functionality Testing
- [ ] **Test Messages**
  - [ ] Send simple message: "Hello"
  - [ ] Send search query: "What documents do you have?"
  - [ ] Send relationship query: "What is the relation between X and Y?"
  - [ ] Verify responses are generated
  - [ ] Check response times are reasonable

### Database Connectivity Testing
- [ ] **PostgreSQL Connection**
  - [ ] Check logs for successful database connection
  - [ ] Verify no database connection errors
  
- [ ] **Neo4j Connection**
  - [ ] Check logs for successful graph database connection
  - [ ] Test graph search functionality

### Performance Testing
- [ ] **Response Times**
  - [ ] Page load time < 3 seconds
  - [ ] Chat response time < 10 seconds
  - [ ] Health check response < 1 second
  
- [ ] **Resource Usage**
  - [ ] Memory usage < 1.5GB
  - [ ] CPU usage < 80%
  - [ ] No memory leaks during extended use

## 🚨 Troubleshooting Checklist

### Build Issues
- [ ] **Requirements Issues**
  - [ ] Check `requirements.txt` files exist
  - [ ] Verify Python version compatibility
  - [ ] Review build logs for pip errors

### Runtime Issues
- [ ] **Environment Variables**
  - [ ] Verify all required variables are set
  - [ ] Check for typos in variable names
  - [ ] Validate database URLs and API keys

- [ ] **Database Connections**
  - [ ] Test PostgreSQL connection separately
  - [ ] Test Neo4j connection separately
  - [ ] Check firewall/network access

- [ ] **API Server Issues**
  - [ ] Check if API server starts successfully
  - [ ] Verify API health endpoint responds
  - [ ] Check for port conflicts

- [ ] **Web UI Issues**
  - [ ] Check if Web UI starts after API
  - [ ] Verify Web UI can connect to API
  - [ ] Check for CORS issues

## 📊 Monitoring Setup

### Key Metrics to Monitor
- [ ] **Application Health**
  - [ ] Health check success rate > 99%
  - [ ] Response time < 3 seconds
  - [ ] Error rate < 1%

- [ ] **Resource Usage**
  - [ ] CPU usage < 80%
  - [ ] Memory usage < 1.5GB
  - [ ] Disk usage monitoring

- [ ] **Database Performance**
  - [ ] Database connection pool health
  - [ ] Query response times
  - [ ] Connection error rates

### Alerts to Set Up
- [ ] Health check failures
- [ ] High error rates
- [ ] Resource usage spikes
- [ ] Database connection failures
- [ ] API key quota warnings

## ✅ Success Criteria

Your combined deployment is successful when:
- [ ] ✅ Build completes without errors
- [ ] ✅ Both API and Web UI start successfully
- [ ] ✅ Health checks return 200 OK
- [ ] ✅ Web interface loads and is responsive
- [ ] ✅ Chat functionality works correctly
- [ ] ✅ Database connections are established
- [ ] ✅ Search functionality works (vector, hybrid, graph)
- [ ] ✅ No critical errors in logs
- [ ] ✅ Performance metrics are acceptable
- [ ] ✅ Mobile interface works properly

## 🔄 Maintenance Tasks

### Regular Monitoring
- [ ] **Daily**: Check application health and logs
- [ ] **Weekly**: Review performance metrics and resource usage
- [ ] **Monthly**: Update dependencies and security patches
- [ ] **Quarterly**: Review and optimize resource allocation

### Update Process
- [ ] **Code Updates**
  1. [ ] Push changes to GitHub repository
  2. [ ] Trigger redeploy in Claw Cloud console
  3. [ ] Monitor deployment progress
  4. [ ] Test functionality after deployment
  5. [ ] Verify no regressions

## 📞 Support Information

### Quick Reference
- **Deployment URL**: `https://your-app.claw.cloud`
- **Health Check**: `https://your-app.claw.cloud/health`
- **Claw Console**: [console.run.claw.cloud](https://console.run.claw.cloud)
- **Documentation**: `COMBINED_DEPLOYMENT_GUIDE.md`

### Emergency Contacts
- [ ] Claw Cloud Support: [support documentation]
- [ ] Database Provider Support: [provider support]
- [ ] Development Team: [team contact]

---

**Deployment Status**: ⏳ In Progress / ✅ Complete / ❌ Failed
**Deployment Date**: `[Date]`
**Deployed By**: `[Name]`
**Version**: `[Git commit hash]`

🚀 **Ready for combined deployment!** This checklist ensures a successful deployment of both API and Web UI on the same server.

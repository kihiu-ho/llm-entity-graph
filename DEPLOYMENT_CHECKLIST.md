# Claw Run Cloud Deployment Checklist

## Pre-Deployment Setup

### ✅ 1. Database Setup
- [ ] **PostgreSQL Database**
  - [ ] Create PostgreSQL instance (Neon, Supabase, AWS RDS)
  - [ ] Note connection string: `postgresql://user:pass@host:port/db`
  - [ ] Test connection

- [ ] **Neo4j Database**
  - [ ] Create Neo4j AuraDB instance
  - [ ] Note connection details: URI, username, password
  - [ ] Test connection

### ✅ 2. API Keys
- [ ] **LLM Provider** (OpenAI, Anthropic, etc.)
  - [ ] Obtain API key
  - [ ] Test API access
  - [ ] Check rate limits and billing

- [ ] **Embedding Provider** (usually same as LLM)
  - [ ] Obtain API key (if different)
  - [ ] Test embedding API

### ✅ 3. Code Preparation
- [ ] **Repository**
  - [ ] Code is in Git repository
  - [ ] All sensitive data removed from code
  - [ ] `.env` files are in `.gitignore`

- [ ] **Docker Setup** (if using Docker deployment)
  - [ ] Test Docker build locally: `docker build -t agentic-rag-webui .`
  - [ ] Push to container registry
  - [ ] Note image URL

## Deployment Steps

### Option A: Docker Deployment

#### ✅ 1. Claw Cloud Setup
- [ ] **Account & Project**
  - [ ] Sign up at [run.claw.cloud](https://run.claw.cloud)
  - [ ] Access console at [console.run.claw.cloud](https://console.run.claw.cloud)

#### ✅ 2. Deploy Application
- [ ] **Basic Configuration**
  - [ ] Click "Deploy from Docker"
  - [ ] Enter image URL: `your-registry/agentic-rag-webui:latest`
  - [ ] Set application name: `agentic-rag-webui`
  - [ ] Set container port: `5000`
  - [ ] Enable internet access: ✅

- [ ] **Environment Variables**
  ```
  DATABASE_URL=postgresql://user:pass@host:port/db
  NEO4J_URI=neo4j+s://instance.databases.neo4j.io
  NEO4J_USERNAME=neo4j
  NEO4J_PASSWORD=your-password
  LLM_PROVIDER=openai
  LLM_API_KEY=your-openai-key
  EMBEDDING_API_KEY=your-openai-key
  APP_ENV=production
  PRODUCTION_MODE=true
  ```

- [ ] **Resource Configuration**
  - [ ] CPU: 1000m (1 core)
  - [ ] Memory: 2Gi (2GB)

#### ✅ 3. Deploy & Test
- [ ] Click "Deploy Application"
- [ ] Wait for deployment to complete
- [ ] Note the application URL: `https://your-app.claw.cloud`

### Option B: DevBox Deployment

#### ✅ 1. Create DevBox
- [ ] **DevBox Setup**
  - [ ] Click "DevBox" → "Create DevBox"
  - [ ] Select "Python" framework
  - [ ] Set resources: 1 CPU, 2GB RAM
  - [ ] Container port: `5000`
  - [ ] Enable internet access: ✅

#### ✅ 2. Development Setup
- [ ] **Connect IDE**
  - [ ] Click IDE dropdown (VSCode/Cursor)
  - [ ] Install DevBox plugin
  - [ ] Connect to remote environment

- [ ] **Code Setup**
  - [ ] Clone repository: `git clone <your-repo-url>`
  - [ ] Install dependencies: `pip install -r requirements.txt`
  - [ ] Install web UI deps: `pip install -r web_ui/requirements.txt`

#### ✅ 3. Configuration
- [ ] **Environment Setup**
  - [ ] Create `.env` file with your configuration
  - [ ] Test locally: `./start.sh`
  - [ ] Verify access via DevBox public URL

#### ✅ 4. Publish & Deploy
- [ ] **Publish Version**
  - [ ] In DevBox details, click "Publish Version"
  - [ ] Enter version info (e.g., v1.0)
  - [ ] Click "Deploy"

- [ ] **Production Deployment**
  - [ ] Click "Deploy" next to published version
  - [ ] Configure production environment variables
  - [ ] Set resource limits
  - [ ] Click "Deploy Application"

## Post-Deployment Verification

### ✅ 1. Health Checks
- [ ] **Web UI Health**
  - [ ] Visit: `https://your-app.claw.cloud/health`
  - [ ] Should return: `{"status": "healthy", ...}`

- [ ] **API Health** (if accessible)
  - [ ] Visit: `https://your-app.claw.cloud:8058/health`
  - [ ] Should return API health status

### ✅ 2. Functionality Tests
- [ ] **Basic Access**
  - [ ] Open: `https://your-app.claw.cloud`
  - [ ] Verify UI loads correctly
  - [ ] Check connection status in header

- [ ] **Chat Functionality**
  - [ ] Send a test message
  - [ ] Verify streaming response works
  - [ ] Check tool usage display

- [ ] **Document Access**
  - [ ] Check documents list in sidebar
  - [ ] Verify document loading

### ✅ 3. Performance & Monitoring
- [ ] **Resource Usage**
  - [ ] Check CPU/memory usage in Claw Cloud console
  - [ ] Monitor for any resource constraints

- [ ] **Logs**
  - [ ] Check application logs for errors
  - [ ] Verify no critical issues

- [ ] **Response Times**
  - [ ] Test chat response times
  - [ ] Verify acceptable performance

## Troubleshooting Common Issues

### ❌ Database Connection Issues
- [ ] Verify DATABASE_URL format
- [ ] Check database server accessibility
- [ ] Ensure SSL mode is correct
- [ ] Test connection from external tool

### ❌ Neo4j Connection Issues
- [ ] Verify Neo4j URI format (`neo4j+s://...`)
- [ ] Check username/password
- [ ] Ensure AuraDB instance is running
- [ ] Test connection from Neo4j Browser

### ❌ API Key Issues
- [ ] Verify API keys are correct
- [ ] Check API key permissions
- [ ] Verify sufficient credits/quota
- [ ] Test API access directly

### ❌ Application Startup Issues
- [ ] Check application logs in Claw Cloud console
- [ ] Verify all environment variables are set
- [ ] Check resource allocation (CPU/memory)
- [ ] Verify container port configuration

### ❌ Performance Issues
- [ ] Monitor resource usage
- [ ] Check database query performance
- [ ] Consider scaling up resources
- [ ] Review application logs for bottlenecks

## Security Checklist

### ✅ 1. Environment Variables
- [ ] All sensitive data in environment variables
- [ ] No API keys in code repository
- [ ] Environment variables properly set in Claw Cloud

### ✅ 2. Database Security
- [ ] Database uses SSL connections
- [ ] Database access restricted by IP (if possible)
- [ ] Strong database passwords

### ✅ 3. Application Security
- [ ] Dependencies are up to date
- [ ] No debug mode in production
- [ ] HTTPS enabled (automatic with Claw Cloud)

## Maintenance

### ✅ 1. Regular Updates
- [ ] Monitor for dependency updates
- [ ] Update API keys before expiration
- [ ] Review and update environment variables

### ✅ 2. Monitoring
- [ ] Set up monitoring alerts
- [ ] Regular health check reviews
- [ ] Performance monitoring

### ✅ 3. Backups
- [ ] Database backup strategy
- [ ] Configuration backup
- [ ] Disaster recovery plan

## Success Criteria

- [ ] ✅ Application accessible at public URL
- [ ] ✅ Health endpoints return healthy status
- [ ] ✅ Chat functionality works end-to-end
- [ ] ✅ Document browsing works
- [ ] ✅ No critical errors in logs
- [ ] ✅ Acceptable response times
- [ ] ✅ Resource usage within limits

## Support Resources

- **Claw Cloud Docs**: [docs.run.claw.cloud](https://docs.run.claw.cloud)
- **Claw Cloud Support**: [question.run.claw.cloud](https://question.run.claw.cloud)
- **Application Logs**: Available in Claw Cloud console
- **Health Endpoints**: `/health` for monitoring

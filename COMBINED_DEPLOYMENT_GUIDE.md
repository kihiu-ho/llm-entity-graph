# 🚀 Combined API + Web UI Deployment Guide for Claw Cloud

## Overview

This guide covers deploying both the Agentic RAG API server and Web UI in a single container on Claw Cloud. This approach simplifies deployment and reduces infrastructure complexity.

## 🎯 Quick Deployment

### Step 1: Access Claw Cloud Console
1. Go to [console.run.claw.cloud](https://console.run.claw.cloud)
2. Login to your account
3. Click "Deploy from Git"

### Step 2: Repository Configuration
- **Repository URL**: `https://github.com/your-username/llm-entity-graph.git`
- **Branch**: `main`
- **Build Context**: `/` (root directory)
- **Dockerfile**: `Dockerfile.claw`

### Step 3: Application Settings
- **Application Name**: `agentic-rag-combined`
- **Container Port**: `5000` (Web UI port)
- **Health Check Path**: `/health`
- **Health Check Port**: `5000`

### Step 4: Resource Configuration
- **CPU**: `1000m` (1 core)
- **Memory**: `2Gi` (2GB)
- **Min Replicas**: `1`
- **Max Replicas**: `2`

### Step 5: Environment Variables

#### Required Database Configuration
```bash
# PostgreSQL Database (REQUIRED)
DATABASE_URL=postgresql://username:password@host:port/database_name

# Neo4j Database (REQUIRED)
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-neo4j-password
```

#### Required LLM Configuration
```bash
# OpenAI Configuration (REQUIRED)
LLM_PROVIDER=openai
LLM_API_KEY=your-openai-api-key
EMBEDDING_API_KEY=your-openai-api-key
LLM_CHOICE=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small
```

#### Application Configuration
```bash
# Web UI Configuration
WEB_UI_HOST=0.0.0.0
WEB_UI_PORT=5000

# API Server Configuration
API_BASE_URL=http://localhost:8058
API_HOST=0.0.0.0
API_PORT=8058

# Application Environment
APP_ENV=production
LOG_LEVEL=INFO
FLASK_ENV=production
```

### Step 6: Deploy
1. Click "Deploy" button
2. Monitor build logs for any errors
3. Wait for deployment to complete
4. Note the assigned URL: `https://your-app.claw.cloud`

## 🧪 Testing Your Deployment

### Health Checks
```bash
# Web UI health check
curl https://your-app.claw.cloud/health

# Expected response
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "api_status": "connected"
}
```

### Web Interface
1. Open `https://your-app.claw.cloud` in your browser
2. Verify the chat interface loads
3. Check that the connection status shows "Connected"
4. Send a test message to verify functionality

### API Endpoints (Internal)
The API server runs internally on port 8058 and is accessible to the Web UI via `http://localhost:8058`.

## 🔧 Architecture

### Container Layout
```
Container (Claw Cloud)
├── API Server (port 8058)
│   ├── Agent endpoints
│   ├── Search functionality
│   ├── Database connections
│   └── LLM integration
└── Web UI (port 5000)
    ├── Chat interface
    ├── Document browser
    ├── Settings panel
    └── API proxy
```

### Process Management
The `start_combined.sh` script manages both processes:
1. Starts API server in background
2. Waits for API to be ready
3. Starts Web UI server
4. Monitors both processes
5. Handles graceful shutdown

### Communication Flow
```
User → Web UI (port 5000) → API Server (port 8058) → Databases/LLM
```

## 🛠️ Configuration Details

### Database Setup

#### PostgreSQL Database
You need a PostgreSQL database for storing documents and embeddings:
```bash
DATABASE_URL=postgresql://username:password@host:port/database_name
```

**Recommended providers:**
- Neon (neon.tech)
- Supabase (supabase.com)
- Railway (railway.app)
- Aiven (aiven.io)

#### Neo4j Database
You need a Neo4j database for the knowledge graph:
```bash
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password
```

**Recommended provider:**
- Neo4j AuraDB (neo4j.com/cloud/aura)

### LLM Configuration

#### OpenAI (Recommended)
```bash
LLM_PROVIDER=openai
LLM_API_KEY=sk-your-openai-api-key
EMBEDDING_API_KEY=sk-your-openai-api-key
LLM_CHOICE=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small
```

#### Alternative LLM Providers
```bash
# Anthropic Claude
LLM_PROVIDER=anthropic
LLM_API_KEY=your-anthropic-api-key

# Azure OpenAI
LLM_PROVIDER=azure
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-azure-api-key
```

## 🚨 Troubleshooting

### Build Issues

#### Missing Dependencies
```bash
# Error: pip install fails
# Solution: Check requirements.txt files exist
ls requirements.txt web_ui/requirements.txt
```

#### Docker Build Fails
```bash
# Error: Dockerfile syntax error
# Solution: Verify Dockerfile.claw syntax
docker build -f Dockerfile.claw -t test .
```

### Runtime Issues

#### API Server Won't Start
```bash
# Check environment variables
echo $DATABASE_URL
echo $NEO4J_URI
echo $LLM_API_KEY

# Check database connectivity
python -c "import psycopg2; print('PostgreSQL OK')"
python -c "from neo4j import GraphDatabase; print('Neo4j OK')"
```

#### Web UI Can't Connect to API
```bash
# Check if API is running
curl http://localhost:8058/health

# Check API URL configuration
echo $API_BASE_URL
```

#### Health Check Fails
```bash
# Test health endpoint
curl -v http://localhost:5000/health

# Check process status
ps aux | grep python
```

### Database Connection Issues

#### PostgreSQL Connection
```bash
# Test connection
python -c "
import os
import psycopg2
try:
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    print('✅ PostgreSQL connection successful')
    conn.close()
except Exception as e:
    print(f'❌ PostgreSQL connection failed: {e}')
"
```

#### Neo4j Connection
```bash
# Test connection
python -c "
import os
from neo4j import GraphDatabase
try:
    driver = GraphDatabase.driver(
        os.getenv('NEO4J_URI'),
        auth=(os.getenv('NEO4J_USERNAME'), os.getenv('NEO4J_PASSWORD'))
    )
    driver.verify_connectivity()
    print('✅ Neo4j connection successful')
    driver.close()
except Exception as e:
    print(f'❌ Neo4j connection failed: {e}')
"
```

## 📊 Monitoring

### Key Metrics
- **Response Time**: < 3 seconds
- **Memory Usage**: < 1.5GB
- **CPU Usage**: < 80%
- **Error Rate**: < 1%
- **Uptime**: > 99.9%

### Log Monitoring
Monitor these log patterns:
- `✅ API server is ready!`
- `✅ Web UI server is ready!`
- `🎉 Combined deployment started successfully!`
- Any `❌` error messages

### Health Monitoring
Set up alerts for:
- Health check failures
- High memory usage
- API connection errors
- Database connection failures

## 🔄 Updates and Maintenance

### Deploying Updates
1. Push changes to your GitHub repository
2. Trigger redeploy in Claw Cloud console
3. Monitor deployment logs
4. Test functionality after deployment

### Database Maintenance
- Regular backups of PostgreSQL database
- Monitor Neo4j database size and performance
- Update database credentials as needed

### Security Updates
- Regularly update Python dependencies
- Rotate API keys and database passwords
- Monitor for security vulnerabilities

## 📞 Support

### Getting Help
1. Check application logs in Claw Cloud console
2. Test database connections separately
3. Verify environment variables are set correctly
4. Review the troubleshooting section above

### Useful Commands
```bash
# Check environment
env | grep -E "(DATABASE|NEO4J|LLM|API|WEB_UI)"

# Test components
curl http://localhost:8058/health  # API health
curl http://localhost:5000/health  # Web UI health

# Process monitoring
ps aux | grep python
netstat -tlnp | grep -E "(5000|8058)"
```

## 🎉 Success Checklist

Your combined deployment is successful when:
- [ ] ✅ Build completes without errors
- [ ] ✅ Both API and Web UI start successfully
- [ ] ✅ Health checks return 200 OK
- [ ] ✅ Web interface loads and is responsive
- [ ] ✅ Chat functionality works correctly
- [ ] ✅ Database connections are established
- [ ] ✅ No critical errors in logs
- [ ] ✅ Performance metrics are acceptable

---

**Deployment URL**: `https://your-app.claw.cloud`
**Architecture**: Combined API + Web UI
**Resource Requirements**: 1 CPU, 2GB RAM
**External Dependencies**: PostgreSQL, Neo4j, OpenAI API

🚀 **Ready for combined deployment!**

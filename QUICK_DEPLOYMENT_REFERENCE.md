# 🚀 Quick Deployment Reference - Combined API + Web UI

## ⚡ Quick Start

### 1. Prerequisites Setup
```bash
# Required External Services:
✅ PostgreSQL Database (Neon, Supabase, Railway)
✅ Neo4j AuraDB Instance  
✅ OpenAI API Key with Credits
```

### 2. Deploy to Claw Cloud
```bash
# Option A: Web Console
🌐 Go to: console.run.claw.cloud
📂 Repository: https://github.com/your-username/llm-entity-graph.git
🐳 Dockerfile: Dockerfile.claw
⚙️ Port: 5000

# Option B: CLI
npm install -g @claw/cli
claw login
claw deploy
```

### 3. Environment Variables (Copy to Claw Console)
```bash
# === REQUIRED - UPDATE THESE! ===
DATABASE_URL=postgresql://user:password@host:port/database
NEO4J_URI=neo4j+s://instance.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-neo4j-password
LLM_API_KEY=your-openai-api-key
EMBEDDING_API_KEY=your-openai-api-key

# === APPLICATION CONFIG ===
WEB_UI_HOST=0.0.0.0
WEB_UI_PORT=5000
API_BASE_URL=http://localhost:8058
API_HOST=0.0.0.0
API_PORT=8058
APP_ENV=production
LOG_LEVEL=INFO
FLASK_ENV=production
LLM_PROVIDER=openai
LLM_CHOICE=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small
```

## 📋 Configuration Summary

| Setting | Value | Description |
|---------|-------|-------------|
| **App Name** | `agentic-rag-combined` | Application identifier |
| **Port** | `5000` | Web UI port (external) |
| **Health Check** | `/health` | Health endpoint |
| **CPU** | `1000m` | 1 CPU core |
| **Memory** | `2Gi` | 2GB RAM |
| **Replicas** | `1-2` | Auto-scaling range |

## 🧪 Testing Checklist

### After Deployment
```bash
# 1. Health Check
curl https://your-app.claw.cloud/health
# Expected: {"status": "healthy", "api_status": "connected"}

# 2. Web Interface
open https://your-app.claw.cloud
# Expected: Chat interface loads, shows "Connected"

# 3. Chat Test
# Send message: "Hello"
# Expected: AI response received
```

## 🔧 Architecture

```
Single Container on Claw Cloud
├── API Server (localhost:8058)
│   ├── /chat, /search endpoints
│   ├── PostgreSQL connection
│   ├── Neo4j connection
│   └── OpenAI integration
└── Web UI (0.0.0.0:5000)
    ├── Chat interface
    ├── Document browser
    └── Proxy to API
```

## 🚨 Troubleshooting

### Build Fails
```bash
# Check: requirements.txt files exist
ls requirements.txt web_ui/requirements.txt

# Check: Dockerfile syntax
docker build -f Dockerfile.claw -t test .
```

### Runtime Issues
```bash
# Check: Environment variables set
env | grep -E "(DATABASE|NEO4J|LLM)"

# Check: Database connectivity
# PostgreSQL: Test connection string
# Neo4j: Test AuraDB credentials
# OpenAI: Test API key
```

### Health Check Fails
```bash
# Check: Application logs in Claw console
# Look for: "🎉 Combined deployment started successfully!"
# Errors: Any lines starting with "❌"
```

## 📊 Expected Performance

| Metric | Expected Value |
|--------|----------------|
| **Startup Time** | 30-60 seconds |
| **Memory Usage** | 800MB - 1.5GB |
| **CPU Usage** | 20-60% |
| **Response Time** | < 5 seconds |
| **Health Check** | < 1 second |

## 🔗 Quick Links

| Resource | URL |
|----------|-----|
| **Claw Console** | [console.run.claw.cloud](https://console.run.claw.cloud) |
| **Deployment Guide** | `COMBINED_DEPLOYMENT_GUIDE.md` |
| **Checklist** | `COMBINED_DEPLOYMENT_CHECKLIST.md` |
| **Local Testing** | `docker-compose up` |

## 📞 Support

### Documentation Files
- `COMBINED_DEPLOYMENT_GUIDE.md` - Complete guide
- `COMBINED_DEPLOYMENT_CHECKLIST.md` - Step-by-step
- `COMBINED_DEPLOYMENT_SUMMARY.md` - Overview
- `.env.claw` - Environment template

### Validation
```bash
# Run validation script
python3 validate_combined_deployment.py
# Expected: 7/7 validations passed
```

### Emergency Commands
```bash
# Check deployment status
claw status

# View logs
claw logs

# Restart deployment
claw restart
```

## ✅ Success Indicators

Your deployment is working when you see:
- ✅ Build completes without errors
- ✅ Health check returns `{"status": "healthy"}`
- ✅ Web UI loads at `https://your-app.claw.cloud`
- ✅ Connection status shows "Connected"
- ✅ Chat messages get AI responses
- ✅ No critical errors in logs

## 🎯 Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| **Build fails** | Check requirements.txt files exist |
| **Health check fails** | Verify environment variables |
| **Can't connect to DB** | Check database URLs and credentials |
| **API errors** | Verify OpenAI API key and credits |
| **Slow responses** | Check resource allocation |

---

**🚀 Ready to Deploy!**
1. Set up databases and API keys
2. Copy environment variables to Claw Cloud
3. Deploy and test
4. Monitor and enjoy!

**Deployment URL**: `https://your-app.claw.cloud`

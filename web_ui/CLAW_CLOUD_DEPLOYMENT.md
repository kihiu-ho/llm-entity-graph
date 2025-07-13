# Deploying Web UI to Claw Cloud

This guide shows how to deploy the Agentic RAG Web UI specifically to claw.cloud platform.

## Quick Deployment Configuration

### Command and Arguments for Claw Cloud

When deploying to claw.cloud, use these settings:

#### **Option 1: Web UI Only (Recommended)**
```bash
# Command:
python

# Arguments:
web_ui/start.py --host 0.0.0.0 --port 5000 --skip-health-check --production

# Working Directory:
/app

# Container Port:
5000
```

#### **Option 2: Web UI with Custom API URL**
```bash
# Command:
python

# Arguments:
web_ui/start.py --host 0.0.0.0 --port 5000 --api-url https://your-api-server.claw.cloud --production

# Working Directory:
/app

# Container Port:
5000
```

#### **Option 3: Combined API + Web UI**
```bash
# Command:
bash

# Arguments:
-c "python -m agent.api & python web_ui/start.py --host 0.0.0.0 --port 5000 --api-url http://localhost:8058 --skip-health-check --production"

# Working Directory:
/app

# Container Port:
5000
```

## Environment Variables

Set these in the claw.cloud environment configuration:

### **Required for Web UI**
```bash
# Web UI Configuration
WEB_UI_HOST=0.0.0.0
WEB_UI_PORT=5000
API_BASE_URL=http://localhost:8058

# Application Environment
APP_ENV=production
LOG_LEVEL=INFO
```

### **Required for API Server (if running combined)**
```bash
# Database
DATABASE_URL=postgresql://user:pass@host:port/db

# Neo4j
NEO4J_URI=neo4j+s://instance.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password

# LLM Provider
LLM_PROVIDER=openai
LLM_API_KEY=your-openai-api-key
EMBEDDING_API_KEY=your-openai-api-key

# Models
LLM_CHOICE=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small
```

## Step-by-Step Deployment

### **Step 1: Prepare Your Repository**

1. **Ensure all files are committed:**
   ```bash
   git add .
   git commit -m "Prepare for claw.cloud deployment"
   git push origin main
   ```

2. **Verify web UI structure:**
   ```
   web_ui/
   ├── app.py
   ├── start.py
   ├── requirements.txt
   ├── templates/
   └── static/
   ```

### **Step 2: Create Claw Cloud Application**

1. **Go to [console.run.claw.cloud](https://console.run.claw.cloud)**

2. **Click "Deploy from Git"**

3. **Configure Repository:**
   - Repository URL: `https://github.com/your-username/llm-entity-graph.git`
   - Branch: `main`
   - Build Context: `/` (root directory)

### **Step 3: Configure Build Settings**

#### **Dockerfile (if using Docker deployment):**
Create `web_ui/Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
COPY web_ui/requirements.txt web_ui/
RUN pip install -r requirements.txt
RUN pip install -r web_ui/requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 5000

# Set working directory to web_ui
WORKDIR /app

# Start command
CMD ["python", "web_ui/start.py", "--host", "0.0.0.0", "--port", "5000", "--skip-health-check", "--production"]
```

#### **Or use Buildpack deployment:**
- **Framework**: Python
- **Python Version**: 3.11
- **Build Command**: `pip install -r requirements.txt && pip install -r web_ui/requirements.txt`
- **Start Command**: `python web_ui/start.py --host 0.0.0.0 --port 5000 --skip-health-check --production`

### **Step 4: Configure Application Settings**

#### **Basic Settings:**
- **Application Name**: `agentic-rag-webui`
- **Container Port**: `5000`
- **Enable Internet Access**: ✅ Yes
- **Enable Persistent Storage**: ❌ No (stateless web UI)

#### **Resource Configuration:**
- **CPU**: `500m` (0.5 cores) - start small
- **Memory**: `1Gi` (1GB) - sufficient for web UI
- **Auto-scaling**: 
  - Min replicas: 1
  - Max replicas: 3

#### **Health Check:**
- **Path**: `/health`
- **Port**: `5000`
- **Initial Delay**: `30s`
- **Timeout**: `10s`

### **Step 5: Set Environment Variables**

In the claw.cloud console, add these environment variables:

```bash
# Web UI Configuration
WEB_UI_HOST=0.0.0.0
WEB_UI_PORT=5000
API_BASE_URL=https://your-api-server.claw.cloud

# Application Settings
APP_ENV=production
LOG_LEVEL=INFO
FLASK_ENV=production

# Optional: Custom branding
APP_TITLE="Your Company RAG Assistant"
```

### **Step 6: Deploy**

1. **Click "Deploy"**
2. **Monitor build logs** for any errors
3. **Wait for deployment to complete**
4. **Test the application** using the provided URL

## Testing Your Deployment

### **Health Check**
```bash
curl https://your-app.claw.cloud/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### **Web Interface**
1. Open `https://your-app.claw.cloud` in your browser
2. Check that the interface loads correctly
3. Verify the connection status indicator
4. Test a simple chat message

## Deployment Scenarios

### **Scenario 1: Web UI Only (External API)**
Use this when you have a separate API server:

```bash
# Command: python
# Arguments: web_ui/start.py --host 0.0.0.0 --port 5000 --api-url https://your-api.claw.cloud --production
# Environment: API_BASE_URL=https://your-api.claw.cloud
```

### **Scenario 2: Combined Deployment**
Use this to run both API and Web UI in one container:

```bash
# Command: bash
# Arguments: -c "python -m agent.api --host 0.0.0.0 --port 8058 & python web_ui/start.py --host 0.0.0.0 --port 5000 --api-url http://localhost:8058 --skip-health-check --production"
# Ports: 5000 (primary), 8058 (internal)
```

### **Scenario 3: Development/Testing**
For testing with debug mode:

```bash
# Command: python
# Arguments: web_ui/start.py --host 0.0.0.0 --port 5000 --debug --skip-health-check
# Environment: APP_ENV=development
```

## Troubleshooting

### **Common Issues:**

1. **Build Failures:**
   ```bash
   # Check requirements.txt paths
   pip install -r requirements.txt
   pip install -r web_ui/requirements.txt
   ```

2. **Port Binding Issues:**
   ```bash
   # Ensure host is 0.0.0.0 for container deployment
   --host 0.0.0.0 --port 5000
   ```

3. **API Connection Issues:**
   ```bash
   # Check API_BASE_URL environment variable
   # Verify API server is accessible
   ```

4. **Static Files Not Loading:**
   ```bash
   # Ensure static files are included in build
   # Check Flask static file configuration
   ```

### **Debugging Commands:**

```bash
# Check if web UI starts locally
python web_ui/start.py --skip-health-check --debug

# Test API connectivity
curl -X GET https://your-api.claw.cloud/health

# Check environment variables
python -c "import os; print(os.environ.get('API_BASE_URL'))"
```

## Production Considerations

### **Performance:**
- Start with minimal resources (0.5 CPU, 1GB RAM)
- Monitor usage and scale up as needed
- Enable auto-scaling for traffic spikes

### **Security:**
- Use HTTPS (automatically provided by claw.cloud)
- Set secure environment variables
- Keep dependencies updated

### **Monitoring:**
- Monitor application logs in claw.cloud console
- Set up health check alerts
- Track response times and error rates

## Support

- **Claw Cloud Docs**: [docs.run.claw.cloud](https://docs.run.claw.cloud)
- **Web UI Issues**: Check application logs and health endpoints
- **API Connectivity**: Verify API server deployment and environment variables

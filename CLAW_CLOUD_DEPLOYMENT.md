# Deploying Agentic RAG Web UI to Claw Run Cloud

This guide walks you through deploying the Agentic RAG Web UI to Claw Run Cloud platform.

## Prerequisites

1. **Claw Cloud Account**: Sign up at [run.claw.cloud](https://run.claw.cloud)
2. **Database Setup**: PostgreSQL and Neo4j databases (cloud-hosted recommended)
3. **API Keys**: OpenAI or other LLM provider API keys
4. **Git Repository**: Your code should be in a Git repository

## Deployment Options

### Option 1: Deploy from Docker (Recommended)

#### Step 1: Build and Push Docker Image

1. **Build the Docker image locally:**
   ```bash
   docker build -t agentic-rag-webui .
   ```

2. **Tag for your registry:**
   ```bash
   docker tag agentic-rag-webui your-registry/agentic-rag-webui:latest
   ```

3. **Push to registry:**
   ```bash
   docker push your-registry/agentic-rag-webui:latest
   ```

#### Step 2: Deploy on Claw Cloud

1. **Go to Claw Cloud Console:**
   - Visit [console.run.claw.cloud](https://console.run.claw.cloud)
   - Click "Deploy from Docker"

2. **Configure the deployment:**
   - **Image**: `your-registry/agentic-rag-webui:latest`
   - **Application Name**: `agentic-rag-webui`
   - **Container Port**: `5000`
   - **Enable Internet Access**: ✅ Yes

3. **Set Environment Variables:**
   ```
   DATABASE_URL=postgresql://user:pass@host:port/db
   NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
   NEO4J_USERNAME=neo4j
   NEO4J_PASSWORD=your-password
   LLM_PROVIDER=openai
   LLM_API_KEY=your-openai-api-key
   EMBEDDING_API_KEY=your-openai-api-key
   APP_ENV=production
   ```

4. **Resource Configuration:**
   - **CPU**: 1000m (1 core)
   - **Memory**: 2Gi (2GB)

5. **Click Deploy**

### Option 2: Deploy from DevBox

#### Step 1: Create DevBox

1. **Go to Claw Cloud Console:**
   - Click "DevBox" → "Create DevBox"
   - Select "Python" framework
   - Configure resources (1 CPU, 2GB RAM)

2. **Network Settings:**
   - Container Port: `5000`
   - Enable Internet Access: ✅ Yes

#### Step 2: Connect and Setup

1. **Connect with your IDE:**
   - Click the IDE dropdown (VSCode/Cursor)
   - Install the DevBox plugin when prompted

2. **Clone your repository:**
   ```bash
   git clone https://github.com/your-username/llm-entity-graph.git
   cd llm-entity-graph
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install -r web_ui/requirements.txt
   ```

#### Step 3: Configure Environment

1. **Create environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` with your configuration:**
   ```bash
   nano .env
   ```

#### Step 4: Test and Deploy

1. **Test locally in DevBox:**
   ```bash
   # Start the combined service
   ./start.sh
   ```

2. **Access via DevBox public URL:**
   - Check the "Network" section in DevBox details
   - Click the "Public Address" link

3. **Publish Version:**
   - In DevBox details, click "Publish Version"
   - Enter version info (e.g., v1.0)
   - Click "Deploy"

4. **Deploy to Production:**
   - Click "Deploy" next to your published version
   - Configure production settings
   - Click "Deploy Application"

## Environment Variables Reference

### Required Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@host:port/database

# Neo4j
NEO4J_URI=neo4j+s://instance.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password

# LLM Provider
LLM_PROVIDER=openai
LLM_API_KEY=your-api-key
EMBEDDING_API_KEY=your-api-key
```

### Optional Variables

```bash
# Application
APP_ENV=production
LOG_LEVEL=INFO
WEB_UI_PORT=5000

# Models
LLM_CHOICE=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small

# Performance
CHUNK_SIZE=8000
MAX_SEARCH_RESULTS=10
```

## Database Setup

### PostgreSQL (Recommended: Neon, Supabase, or AWS RDS)

1. **Create database instance**
2. **Get connection string:**
   ```
   postgresql://user:password@host:port/database?sslmode=require
   ```
3. **Set DATABASE_URL environment variable**

### Neo4j (Recommended: Neo4j AuraDB)

1. **Create Neo4j AuraDB instance**
2. **Get connection details:**
   ```
   URI: neo4j+s://instance.databases.neo4j.io
   Username: neo4j
   Password: your-generated-password
   ```
3. **Set Neo4j environment variables**

## Monitoring and Troubleshooting

### Health Checks

The application includes health endpoints:
- Web UI: `https://your-app.claw.cloud/health`
- API: `https://your-app.claw.cloud:8058/health`

### Logs

View logs in Claw Cloud console:
1. Go to your application details
2. Click "Logs" tab
3. Monitor for errors or performance issues

### Common Issues

1. **Database Connection Errors:**
   - Verify DATABASE_URL format
   - Check database accessibility
   - Ensure SSL mode is correct

2. **Neo4j Connection Issues:**
   - Verify Neo4j URI format
   - Check credentials
   - Ensure instance is running

3. **API Key Issues:**
   - Verify API keys are correct
   - Check rate limits
   - Ensure sufficient credits

## Scaling

### Auto-scaling Configuration

In Claw Cloud console:
1. Go to application settings
2. Configure auto-scaling:
   - Min replicas: 1
   - Max replicas: 3
   - CPU threshold: 70%

### Performance Optimization

1. **Resource Allocation:**
   - Start with 1 CPU, 2GB RAM
   - Monitor usage and scale up if needed

2. **Database Optimization:**
   - Use connection pooling
   - Optimize queries
   - Consider read replicas for high traffic

## Security Considerations

1. **Environment Variables:**
   - Never commit API keys to Git
   - Use Claw Cloud's environment variable management

2. **Database Security:**
   - Use SSL connections
   - Restrict database access by IP if possible
   - Regular security updates

3. **Application Security:**
   - Keep dependencies updated
   - Monitor for security vulnerabilities
   - Use HTTPS (automatically provided by Claw Cloud)

## Cost Optimization

1. **Resource Right-sizing:**
   - Monitor actual usage
   - Adjust CPU/memory allocation
   - Use auto-scaling to handle traffic spikes

2. **Database Costs:**
   - Choose appropriate database tiers
   - Monitor storage usage
   - Consider data retention policies

## Support

- **Claw Cloud Documentation:** [docs.run.claw.cloud](https://docs.run.claw.cloud)
- **Claw Cloud Support:** [question.run.claw.cloud](https://question.run.claw.cloud)
- **Application Issues:** Check application logs and health endpoints

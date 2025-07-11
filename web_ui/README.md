# Web UI for Agentic RAG with Knowledge Graph

A modern, responsive web interface for the Agentic RAG system that provides an intuitive way to interact with the AI agent and its tools.

## Features

### 🚀 Core Functionality
- **Real-time streaming chat** - Live responses from the AI agent
- **Session management** - Persistent conversations across page reloads
- **Health monitoring** - Real-time API connection status
- **Tool usage display** - See which tools the agent used for each response

### ⚙️ Settings & Configuration
- **Environment settings** - Configure database connections, LLM providers, and ingestion settings
- **Connection testing** - Test PostgreSQL, Neo4j, and LLM connections before saving
- **Settings persistence** - Save configuration to .env file for easy deployment
- **Tabbed interface** - Organized settings across Database, LLM, and Ingestion tabs

### 📚 Document Management & Ingestion
- **Document browser** - View available documents in the knowledge base
- **Document metadata** - See document titles and information
- **File upload** - Drag-and-drop or browse to upload Markdown/text files
- **Ingestion progress** - Real-time progress tracking during document processing
- **Ingestion configuration** - Customize chunk size, overlap, and entity extraction settings
- **Batch processing** - Upload and process multiple files simultaneously

### 💬 Chat Features
- **Responsive design** - Works on desktop, tablet, and mobile
- **Auto-resizing input** - Text area grows with your message
- **Example queries** - Click to try suggested questions
- **Chat export** - Download conversation history as text file
- **Clear chat** - Start fresh conversations

### 🎨 User Experience
- **Modern UI** - Clean, professional interface
- **Toast notifications** - Helpful feedback messages
- **Loading indicators** - Clear visual feedback
- **Keyboard shortcuts** - Enter to send, Shift+Enter for new line

## Installation

### Prerequisites
- Python 3.8+
- The main Agentic RAG API server running (default: http://localhost:8058)

### Setup

1. **Install dependencies:**
   ```bash
   cd web_ui
   pip install -r requirements.txt
   ```

2. **Configure environment (optional):**
   Create a `.env` file in the `web_ui` directory:
   ```env
   API_BASE_URL=http://localhost:8058
   WEB_UI_PORT=5000
   WEB_UI_HOST=0.0.0.0
   ```

3. **Start the web UI:**
   ```bash
   python app.py
   ```

4. **Access the interface:**
   Open your browser to: http://localhost:5000

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `API_BASE_URL` | `http://localhost:8058` | Base URL of the Agentic RAG API |
| `WEB_UI_PORT` | `5000` | Port for the web UI server |
| `WEB_UI_HOST` | `0.0.0.0` | Host interface for the web UI |

### API Integration

The web UI communicates with the main Agentic RAG API through these endpoints:

- `GET /health` - Health status monitoring
- `POST /chat/stream` - Streaming chat responses
- `POST /search/{type}` - Direct search functionality
- `GET /documents` - Document listing

## Usage

### Initial Setup

1. **Configure Settings** - Click "Settings" to configure your environment
   - **Database Tab**: Set PostgreSQL and Neo4j connection strings
   - **LLM Tab**: Configure your LLM provider and API keys
   - **Ingestion Tab**: Set document processing preferences
   - **Test Connections**: Verify all connections work before saving

2. **Ingest Documents** - Click "Ingest Documents" to add content
   - Upload .md or .txt files via drag-and-drop or file browser
   - Configure chunk size, overlap, and entity extraction settings
   - Monitor real-time ingestion progress
   - Review processing results and statistics

### Starting a Conversation

1. **Check connection status** - The header shows API connection status
2. **Type your message** - Use the text area at the bottom
3. **Send message** - Click send button or press Enter
4. **View response** - Watch the AI agent respond in real-time
5. **See tools used** - Tool usage appears in the bottom-right corner



### Example Queries

Try these sample questions to get started:

- "What are Google's AI initiatives?"
- "Tell me about Microsoft's partnerships with OpenAI"
- "Compare OpenAI and Anthropic's approaches to AI safety"
- "What documents are available about tech companies?"

### Managing Conversations

- **Clear chat** - Use the "Clear Chat" button in the sidebar
- **Export chat** - Download conversation history with "Export Chat"
- **Session persistence** - Conversations continue across page reloads

## Architecture

### Frontend Components

- **HTML Template** (`templates/index.html`) - Main page structure
- **CSS Styles** (`static/css/style.css`) - Responsive styling
- **JavaScript App** (`static/js/app.js`) - Interactive functionality

### Backend Server

- **Flask Application** (`app.py`) - Web server and API proxy
- **Async Client** - Handles communication with main API
- **CORS Support** - Enables cross-origin requests

### Communication Flow

```
Browser ↔ Flask Web UI ↔ Agentic RAG API ↔ AI Agent + Tools
```

## Development

### File Structure

```
web_ui/
├── app.py                 # Flask web server
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── templates/
│   └── index.html        # Main HTML template
└── static/
    ├── css/
    │   └── style.css     # Styling
    └── js/
        └── app.js        # JavaScript functionality
```

### Customization

#### Styling
Edit `static/css/style.css` to customize the appearance:
- Colors and themes
- Layout and spacing
- Responsive breakpoints
- Animation effects

#### Functionality
Modify `static/js/app.js` to add features:
- New UI components
- Additional API endpoints
- Enhanced interactions
- Custom behaviors

#### Backend
Update `app.py` to extend server capabilities:
- New routes
- Additional API integrations
- Enhanced error handling
- Custom middleware

## Troubleshooting

### Common Issues

1. **Connection Failed**
   - Ensure the main API server is running on port 8058
   - Check the `API_BASE_URL` configuration
   - Verify network connectivity

2. **Streaming Not Working**
   - Check browser console for JavaScript errors
   - Ensure CORS is properly configured
   - Verify the API supports Server-Sent Events

3. **Search Results Empty**
   - Confirm documents are ingested in the knowledge base
   - Check search query formatting
   - Verify the selected search type is appropriate

4. **UI Not Loading**
   - Check Flask server logs for errors
   - Ensure all static files are present
   - Verify template rendering

### Debug Mode

Run with debug enabled for development:

```bash
export FLASK_DEBUG=1
python app.py
```

### Logs

Check the console output for:
- API connection status
- Request/response details
- Error messages
- Performance metrics

## Browser Support

- **Chrome** 80+
- **Firefox** 75+
- **Safari** 13+
- **Edge** 80+

## Security Considerations

- The web UI runs on localhost by default
- CORS is enabled for development convenience
- No authentication is implemented (relies on API security)
- Consider adding HTTPS for production deployments

## Contributing

To contribute to the web UI:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This web UI is part of the Agentic RAG project and follows the same license terms.

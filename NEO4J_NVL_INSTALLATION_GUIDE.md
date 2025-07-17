# Neo4j NVL Installation Guide

## Quick Installation for Your Flask Web UI

### **Step 1: Install Node.js and npm**

If you don't have Node.js installed:

```bash
# On macOS with Homebrew
brew install node

# On Ubuntu/Debian
sudo apt update
sudo apt install nodejs npm

# On Windows
# Download from https://nodejs.org/
```

### **Step 2: Install Neo4j NVL in your web_ui directory**

```bash
cd web_ui
npm install
```

This will install:
- `@neo4j-nvl/base@^0.3.8` - The Neo4j visualization library
- `webpack` and `webpack-cli` - For bundling

### **Step 3: Build the NVL bundle**

```bash
npm run build
```

This creates `static/js/dist/nvl.bundle.js` with the Neo4j NVL library.

### **Step 4: Update your HTML template**

Replace the CDN loading script with the bundled version:

```html
<!-- Remove the old CDN loading script -->
<!-- <script>console.log('🔍 Attempting to load NVL library...')...</script> -->

<!-- Add the bundled NVL library -->
<script src="{{ url_for('static', filename='js/dist/nvl.bundle.js') }}"></script>
```

### **Step 5: Update your JavaScript**

The bundled version provides a helper function:

```javascript
// In your neo4j-graph-visualization.js
initializeNVL() {
    try {
        const container = document.getElementById('graph-canvas');
        
        // Use the bundled helper function
        this.nvl = window.initializeNVL(container, {
            width: container.clientWidth || 800,
            height: container.clientHeight || 500,
            allowDynamicMinZoom: true,
            enableFitView: true
        });
        
        console.log('✅ NVL initialized successfully');
    } catch (error) {
        console.error('❌ Failed to initialize NVL:', error);
        this.createFallbackVisualization();
    }
}
```

## Alternative Installation Methods

### **Method 1: React Application (Recommended for new projects)**

```bash
# Create new React app
npx create-react-app neo4j-graph-ui
cd neo4j-graph-ui

# Install Neo4j NVL React wrapper
npm install @neo4j-nvl/react

# Usage in React component
import { NVL } from '@neo4j-nvl/react';

function GraphVisualization({ nodes, relationships }) {
  return (
    <NVL
      nodes={nodes}
      relationships={relationships}
      width={800}
      height={600}
    />
  );
}
```

### **Method 2: CDN (Less reliable)**

```html
<!-- Specific version (more reliable than latest) -->
<script src="https://unpkg.com/@neo4j-nvl/base@0.3.0/dist/index.js"></script>

<!-- Usage -->
<script>
const nvl = new NVL(container, options);
</script>
```

### **Method 3: Direct npm in existing project**

```bash
# In any JavaScript project
npm install @neo4j-nvl/base

# With bundler (webpack, rollup, etc.)
import { NVL } from '@neo4j-nvl/base';
```

## Troubleshooting

### **Common Issues:**

1. **"NVL is not defined"**
   ```bash
   # Make sure you built the bundle
   cd web_ui
   npm run build
   ```

2. **"Module not found"**
   ```bash
   # Install dependencies
   npm install
   ```

3. **Build errors**
   ```bash
   # Clear cache and reinstall
   rm -rf node_modules package-lock.json
   npm install
   npm run build
   ```

### **Verify Installation:**

```javascript
// Check in browser console
console.log('NVL available:', typeof window.NVL);
console.log('Helper available:', typeof window.initializeNVL);
```

## Development Workflow

### **For development (auto-rebuild on changes):**
```bash
npm run dev
```

### **For production (optimized build):**
```bash
npm run build
```

### **Complete setup from scratch:**
```bash
cd web_ui
npm run install-nvl  # Installs and builds everything
```

## File Structure After Installation

```
web_ui/
├── package.json              # npm configuration
├── webpack.config.js         # Build configuration
├── src/
│   └── nvl-bundle.js         # NVL bundle source
├── static/js/dist/
│   └── nvl.bundle.js         # Built bundle (auto-generated)
├── node_modules/             # npm packages (auto-generated)
└── templates/
    └── index.html            # Updated to use bundle
```

## Benefits of This Approach

### ✅ **Reliability**
- No CDN failures
- Guaranteed availability
- Works offline

### ✅ **Performance**
- Bundled and minified
- Single HTTP request
- Faster loading

### ✅ **Version Control**
- Exact version in package.json
- Reproducible builds
- Easy updates

### ✅ **Development**
- Source maps for debugging
- Hot reload during development
- Better error messages

## Next Steps

1. **Install**: Run `cd web_ui && npm install`
2. **Build**: Run `npm run build`
3. **Update HTML**: Replace CDN script with bundle
4. **Test**: Verify graph visualization works
5. **Deploy**: Include `static/js/dist/nvl.bundle.js` in deployment

This approach eliminates the CDN loading issues you've been experiencing and provides a much more reliable Neo4j graph visualization setup.

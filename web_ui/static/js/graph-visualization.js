/**
 * Neo4j Knowledge Graph Visualization
 * Uses D3.js to render interactive graph visualization
 */

class GraphVisualization {
    constructor() {
        this.svg = null;
        this.simulation = null;
        this.nodes = [];
        this.links = [];
        this.width = 800;
        this.height = 600;
        this.currentDepth = 3;
        this.currentEntity = null;
        
        // Color scheme for different node types
        this.nodeColors = {
            'Person': '#4CAF50',
            'Company': '#2196F3', 
            'Organization': '#FF9800',
            'Role': '#9C27B0',
            'Location': '#F44336',
            'Technology': '#607D8B',
            'Financial': '#795548',
            'default': '#757575'
        };
        
        // Initialize event listeners
        this.initializeEventListeners();
    }
    
    initializeEventListeners() {
        // Graph visualization button
        document.getElementById('visualize-graph').addEventListener('click', () => {
            this.openGraphModal();
        });
        
        // Refresh graph button
        document.getElementById('refresh-graph').addEventListener('click', () => {
            this.refreshGraph();
        });
        
        // Modal controls
        document.getElementById('close-graph-modal').addEventListener('click', () => {
            this.closeGraphModal();
        });
        
        document.getElementById('close-graph').addEventListener('click', () => {
            this.closeGraphModal();
        });
        
        // Graph controls
        document.getElementById('zoom-in').addEventListener('click', () => {
            this.zoomIn();
        });
        
        document.getElementById('zoom-out').addEventListener('click', () => {
            this.zoomOut();
        });
        
        document.getElementById('reset-zoom').addEventListener('click', () => {
            this.resetZoom();
        });
        
        document.getElementById('center-graph').addEventListener('click', () => {
            this.centerGraph();
        });
        
        // Export graph
        document.getElementById('export-graph').addEventListener('click', () => {
            this.exportGraph();
        });
        
        // Depth input change
        document.getElementById('graph-depth').addEventListener('change', (e) => {
            this.currentDepth = parseInt(e.target.value);
            document.getElementById('graph-depth-display').textContent = `Depth: ${this.currentDepth}`;
        });
        
        // Entity input enter key
        document.getElementById('graph-entity').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.openGraphModal();
            }
        });
    }
    
    async openGraphModal() {
        const entity = document.getElementById('graph-entity').value.trim();
        const depth = parseInt(document.getElementById('graph-depth').value);
        
        this.currentEntity = entity;
        this.currentDepth = depth;
        
        // Show modal
        document.getElementById('graph-modal').style.display = 'block';
        
        // Update depth display
        document.getElementById('graph-depth-display').textContent = `Depth: ${depth}`;
        
        // Load and render graph
        await this.loadAndRenderGraph(entity, depth);
    }
    
    closeGraphModal() {
        document.getElementById('graph-modal').style.display = 'none';
        this.clearGraph();
    }
    
    async loadAndRenderGraph(entity, depth) {
        this.showLoading();
        
        try {
            // Fetch graph data from API
            const graphData = await this.fetchGraphData(entity, depth);
            
            if (graphData && graphData.nodes && graphData.links) {
                this.renderGraph(graphData);
                this.hideLoading();
            } else {
                this.showError('No graph data found');
            }
        } catch (error) {
            console.error('Failed to load graph data:', error);
            this.showError('Failed to load graph data: ' + error.message);
        }
    }
    
    async fetchGraphData(entity, depth) {
        const params = new URLSearchParams({
            depth: depth.toString()
        });
        
        if (entity) {
            params.append('entity', entity);
        }
        
        const response = await fetch(`/api/graph/visualize?${params}`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        return await response.json();
    }
    
    renderGraph(data) {
        this.clearGraph();
        
        this.nodes = data.nodes || [];
        this.links = data.links || [];
        
        // Update stats
        document.getElementById('graph-nodes-count').textContent = `Nodes: ${this.nodes.length}`;
        document.getElementById('graph-edges-count').textContent = `Edges: ${this.links.length}`;
        
        // Create SVG
        const container = document.getElementById('graph-canvas');
        this.width = container.clientWidth || 800;
        this.height = container.clientHeight || 600;
        
        this.svg = d3.select('#graph-canvas')
            .append('svg')
            .attr('width', this.width)
            .attr('height', this.height);
        
        // Add zoom behavior
        const zoom = d3.zoom()
            .scaleExtent([0.1, 10])
            .on('zoom', (event) => {
                this.svg.select('.graph-group').attr('transform', event.transform);
            });
        
        this.svg.call(zoom);
        
        // Create main group for graph elements
        const g = this.svg.append('g').attr('class', 'graph-group');
        
        // Create force simulation
        this.simulation = d3.forceSimulation(this.nodes)
            .force('link', d3.forceLink(this.links).id(d => d.id).distance(100))
            .force('charge', d3.forceManyBody().strength(-300))
            .force('center', d3.forceCenter(this.width / 2, this.height / 2))
            .force('collision', d3.forceCollide().radius(30));
        
        // Create links
        const link = g.append('g')
            .attr('class', 'links')
            .selectAll('line')
            .data(this.links)
            .enter().append('line')
            .attr('stroke', '#999')
            .attr('stroke-opacity', 0.6)
            .attr('stroke-width', d => Math.sqrt(d.weight || 1));
        
        // Create link labels
        const linkLabel = g.append('g')
            .attr('class', 'link-labels')
            .selectAll('text')
            .data(this.links)
            .enter().append('text')
            .attr('class', 'link-label')
            .attr('text-anchor', 'middle')
            .attr('font-size', '10px')
            .attr('fill', '#666')
            .text(d => d.relationship || d.type || '');
        
        // Create nodes
        const node = g.append('g')
            .attr('class', 'nodes')
            .selectAll('circle')
            .data(this.nodes)
            .enter().append('circle')
            .attr('r', d => this.getNodeRadius(d))
            .attr('fill', d => this.getNodeColor(d))
            .attr('stroke', '#fff')
            .attr('stroke-width', 2)
            .call(this.drag());
        
        // Create node labels
        const nodeLabel = g.append('g')
            .attr('class', 'node-labels')
            .selectAll('text')
            .data(this.nodes)
            .enter().append('text')
            .attr('class', 'node-label')
            .attr('text-anchor', 'middle')
            .attr('dy', '.35em')
            .attr('font-size', '12px')
            .attr('font-weight', 'bold')
            .attr('fill', '#333')
            .text(d => this.getNodeLabel(d));
        
        // Add tooltips
        node.append('title')
            .text(d => this.getNodeTooltip(d));
        
        // Update positions on simulation tick
        this.simulation.on('tick', () => {
            link
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);
            
            linkLabel
                .attr('x', d => (d.source.x + d.target.x) / 2)
                .attr('y', d => (d.source.y + d.target.y) / 2);
            
            node
                .attr('cx', d => d.x)
                .attr('cy', d => d.y);
            
            nodeLabel
                .attr('x', d => d.x)
                .attr('y', d => d.y);
        });
        
        // Store references for zoom controls
        this.zoomBehavior = zoom;
    }
    
    getNodeRadius(node) {
        const baseRadius = 15;
        const importance = node.importance || 1;
        return baseRadius + (importance * 5);
    }
    
    getNodeColor(node) {
        const type = node.type || node.label || 'default';
        return this.nodeColors[type] || this.nodeColors.default;
    }
    
    getNodeLabel(node) {
        return node.name || node.label || node.id || 'Unknown';
    }
    
    getNodeTooltip(node) {
        let tooltip = `Name: ${this.getNodeLabel(node)}`;
        if (node.type) tooltip += `\nType: ${node.type}`;
        if (node.properties) {
            Object.entries(node.properties).forEach(([key, value]) => {
                tooltip += `\n${key}: ${value}`;
            });
        }
        return tooltip;
    }
    
    drag() {
        return d3.drag()
            .on('start', (event, d) => {
                if (!event.active) this.simulation.alphaTarget(0.3).restart();
                d.fx = d.x;
                d.fy = d.y;
            })
            .on('drag', (event, d) => {
                d.fx = event.x;
                d.fy = event.y;
            })
            .on('end', (event, d) => {
                if (!event.active) this.simulation.alphaTarget(0);
                d.fx = null;
                d.fy = null;
            });
    }
    
    // Zoom controls
    zoomIn() {
        if (this.svg && this.zoomBehavior) {
            this.svg.transition().call(this.zoomBehavior.scaleBy, 1.5);
        }
    }
    
    zoomOut() {
        if (this.svg && this.zoomBehavior) {
            this.svg.transition().call(this.zoomBehavior.scaleBy, 1 / 1.5);
        }
    }
    
    resetZoom() {
        if (this.svg && this.zoomBehavior) {
            this.svg.transition().call(this.zoomBehavior.transform, d3.zoomIdentity);
        }
    }
    
    centerGraph() {
        if (this.simulation) {
            this.simulation.alpha(0.3).restart();
        }
    }
    
    // Utility methods
    showLoading() {
        document.getElementById('graph-loading').style.display = 'flex';
        document.getElementById('graph-error').style.display = 'none';
        document.getElementById('graph-canvas').style.display = 'none';
    }
    
    hideLoading() {
        document.getElementById('graph-loading').style.display = 'none';
        document.getElementById('graph-error').style.display = 'none';
        document.getElementById('graph-canvas').style.display = 'block';
    }
    
    showError(message) {
        document.getElementById('graph-loading').style.display = 'none';
        document.getElementById('graph-error').style.display = 'flex';
        document.getElementById('graph-error').querySelector('p').textContent = message;
        document.getElementById('graph-canvas').style.display = 'none';
    }
    
    clearGraph() {
        if (this.svg) {
            this.svg.remove();
            this.svg = null;
        }
        if (this.simulation) {
            this.simulation.stop();
            this.simulation = null;
        }
    }
    
    async refreshGraph() {
        if (this.currentEntity !== null) {
            await this.loadAndRenderGraph(this.currentEntity, this.currentDepth);
        }
    }
    
    exportGraph() {
        if (!this.svg) return;
        
        // Create a new SVG element for export
        const svgNode = this.svg.node();
        const serializer = new XMLSerializer();
        const svgString = serializer.serializeToString(svgNode);
        
        // Create download link
        const blob = new Blob([svgString], { type: 'image/svg+xml' });
        const url = URL.createObjectURL(blob);
        
        const link = document.createElement('a');
        link.href = url;
        link.download = `knowledge-graph-${Date.now()}.svg`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        URL.revokeObjectURL(url);
    }
}

// Initialize graph visualization when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.graphVisualization = new GraphVisualization();
});

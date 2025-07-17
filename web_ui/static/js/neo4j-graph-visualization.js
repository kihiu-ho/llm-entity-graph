/**
 * Neo4j Knowledge Graph Visualization using NVL (Neo4j Visualization Library)
 * Provides native Neo4j graph rendering with advanced features
 */

class Neo4jGraphVisualization {
    constructor() {
        this.nvl = null;
        this.currentLimit = 50;
        this.currentEntity = null;
        this.graphData = { nodes: [], relationships: [] };
        
        // NVL configuration
        this.nvlConfig = {
            allowDynamicMinZoom: true,
            disableWebGL: false,
            maxZoom: 3,
            minZoom: 0.1,
            relationshipThreshold: 0.8,
            useWebGL: true,
            instanceId: 'neo4j-graph-viz',
            initialZoom: 1,
            layout: {
                type: 'force',
                options: {
                    linkDistance: 100,
                    linkStrength: 0.1,
                    repulsion: -1000,
                    iterations: 300
                }
            }
        };
        
        // Node styling configuration
        this.nodeStyles = {
            'Person': {
                color: '#4CAF50',  // Green for people
                size: 25,
                icon: '👤'
            },
            'Company': {
                color: '#2196F3',  // Blue for companies
                size: 30,
                icon: '🏢'
            },
            'Organization': {
                color: '#FF9800',
                size: 25,
                icon: '🏛️'
            },
            'Role': {
                color: '#9C27B0',
                size: 15,
                icon: '💼'
            },
            'Location': {
                color: '#F44336',
                size: 18,
                icon: '📍'
            },
            'Technology': {
                color: '#607D8B',
                size: 18,
                icon: '⚙️'
            },
            'Financial': {
                color: '#795548',
                size: 18,
                icon: '💰'
            },
            'default': {
                color: '#757575',
                size: 16,
                icon: '⚪'
            }
        };
        
        // Relationship styling
        this.relationshipStyles = {
            'WORKS_AT': { color: '#4CAF50', width: 2 },
            'HAS_ROLE': { color: '#9C27B0', width: 2 },
            'MEMBER_OF': { color: '#2196F3', width: 2 },
            'REPRESENTS': { color: '#FF9800', width: 2 },
            'CONNECTED_TO': { color: '#757575', width: 1 },
            'RELATED_TO': { color: '#757575', width: 1 },
            'default': { color: '#999999', width: 1 }
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
        
        // Limit input change
        document.getElementById('graph-limit').addEventListener('change', (e) => {
            this.currentLimit = parseInt(e.target.value);
            document.getElementById('graph-limit-display').textContent = `Limit: ${this.currentLimit}`;
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
        const limit = parseInt(document.getElementById('graph-limit').value);

        this.currentEntity = entity;
        this.currentLimit = limit;
        
        // Show modal
        document.getElementById('graph-modal').style.display = 'block';

        // Update limit display
        document.getElementById('graph-limit-display').textContent = `Limit: ${limit}`;

        // Initialize NVL if not already done
        if (!this.nvl) {
            this.initializeNVL();
        }

        // Load and render graph
        await this.loadAndRenderGraph(entity, limit);
    }
    
    closeGraphModal() {
        document.getElementById('graph-modal').style.display = 'none';
        if (this.nvl) {
            this.nvl.clearGraph();
        }
    }
    
    initializeNVL() {
        try {
            console.log('🔧 Initializing NVL...');
            console.log('🔍 Checking NVL availability...');
            console.log('📦 typeof NVL:', typeof NVL);
            console.log('📦 typeof window.NVL:', typeof window.NVL);
            console.log('📦 typeof window.Neo4jNVL:', typeof window.Neo4jNVL);

            // Option to skip NVL entirely for testing
            const skipNVL = window.location.search.includes('skipNVL=true');

            if (skipNVL) {
                console.log('🚫 Skipping NVL initialization (skipNVL=true in URL)');
                throw new Error('NVL skipped by user request');
            }

            // Try to use the NVL constructor directly
            let NVLConstructor = null;
            if (typeof window.NVL === 'function') {
                NVLConstructor = window.NVL;
                console.log('✅ Using window.NVL constructor');
            } else if (typeof window.Neo4jNVL === 'function') {
                NVLConstructor = window.Neo4jNVL;
                console.log('✅ Using window.Neo4jNVL constructor');
            } else if (typeof NVL === 'function') {
                NVLConstructor = NVL;
                console.log('✅ Using global NVL constructor');
            }

            if (!NVLConstructor) {
                console.error('❌ NVL constructor not found');
                throw new Error('NVL constructor not found. Make sure the NVL bundle loaded correctly.');
            }

            // Get the graph container
            const container = document.getElementById('graph-canvas');
            if (!container) {
                console.error('❌ Graph canvas container not found');
                throw new Error('Graph canvas container not found');
            }

            console.log('📦 Container found:', container);
            console.log('📦 Container dimensions:', {
                width: container.clientWidth,
                height: container.clientHeight,
                offsetWidth: container.offsetWidth,
                offsetHeight: container.offsetHeight
            });

            // Initialize NVL with correct constructor based on npm docs
            // new NVL(container, nodes, relationships, options, callbacks)
            const nodes = [];
            const relationships = [];
            const options = {
                layout: 'forceDirected',
                initialZoom: 0.5,
                allowDynamicMinZoom: true,
                maxZoom: 10,
                minZoom: 0.1,
                disableTelemetry: true,
                styling: {
                    nodeDefaultBorderColor: '#333',
                    selectedBorderColor: '#007bff',
                    relationshipDefaultColor: '#666',
                    selectedRelationshipColor: '#007bff'
                }
            };
            const callbacks = {
                onLayoutDone: () => {
                    console.log('📐 NVL Layout done');
                },
                onError: (error) => {
                    console.error('❌ NVL Error callback:', error);
                    this.showError('Graph visualization error: ' + error.message);
                }
            };

            console.log('🚀 Creating NVL instance with:');
            console.log('  - Container:', container);
            console.log('  - Nodes:', nodes);
            console.log('  - Relationships:', relationships);
            console.log('  - Options:', options);
            console.log('  - Callbacks:', callbacks);

            this.nvl = new NVLConstructor(container, nodes, relationships, options, callbacks);

            console.log('✅ NVL instance created successfully');
            console.log('🔍 NVL instance details:', {
                instance: this.nvl,
                type: typeof this.nvl,
                constructor: this.nvl.constructor.name,
                methods: Object.getOwnPropertyNames(Object.getPrototypeOf(this.nvl))
            });

            // Set up event listeners for interactions
            container.addEventListener('click', (evt) => {
                try {
                    console.log('🖱️ Container clicked:', evt);
                    if (this.nvl && typeof this.nvl.getHits === 'function') {
                        const hits = this.nvl.getHits(evt);
                        console.log('🎯 NVL hits:', hits);

                        if (hits && hits.nvlTargets) {
                            const { nvlTargets } = hits;
                            if (nvlTargets.nodes && nvlTargets.nodes.length > 0) {
                                console.log('🔵 Node clicked:', nvlTargets.nodes[0]);
                                this.onNodeClick(nvlTargets.nodes[0]);
                            } else if (nvlTargets.relationships && nvlTargets.relationships.length > 0) {
                                console.log('🔗 Relationship clicked:', nvlTargets.relationships[0]);
                                this.onRelationshipClick(nvlTargets.relationships[0]);
                            } else {
                                console.log('🖱️ Canvas clicked');
                                this.onCanvasClick();
                            }
                        }
                    } else {
                        console.warn('⚠️ NVL getHits method not available');
                    }
                } catch (e) {
                    console.warn('⚠️ Click event handling failed:', e);
                }
            });

            console.log('✅ NVL initialized successfully');
        } catch (error) {
            console.error('❌ Failed to initialize NVL:', error);
            console.error('❌ Error stack:', error.stack);
            console.log('🔄 Creating fallback visualization...');
            this.createFallbackVisualization();
        }
    }

    createFallbackVisualization() {
        console.log('🎨 Creating enhanced fallback visualization...');
        const container = document.getElementById('graph-canvas');
        if (!container) {
            console.error('❌ Graph canvas container not found for fallback');
            return;
        }

        // Clear container
        container.innerHTML = '';

        // Create an enhanced HTML-based graph visualization
        container.style.cssText = `
            display: flex;
            flex-direction: column;
            background: #ffffff;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 20px;
            font-family: Arial, sans-serif;
            height: 100%;
            min-height: 500px;
        `;

        const header = document.createElement('div');
        header.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; padding-bottom: 15px; border-bottom: 2px solid #e9ecef;">
                <h3 style="color: #495057; margin: 0;">📊 Knowledge Graph (Fallback View)</h3>
                <div style="display: flex; gap: 15px; font-size: 0.9em; color: #6c757d;">
                    <span><strong>Entities:</strong> <span id="fallback-nodes-count" style="color: #007bff;">0</span></span>
                    <span><strong>Relationships:</strong> <span id="fallback-relationships-count" style="color: #28a745;">0</span></span>
                </div>
            </div>
        `;

        const content = document.createElement('div');
        content.id = 'fallback-graph-content';
        content.style.cssText = `
            flex: 1;
            overflow-y: auto;
            background: #f8f9fa;
            border-radius: 6px;
            padding: 15px;
        `;
        content.innerHTML = '<p style="color: #6c757d; text-align: center; margin: 50px 0;">Loading graph data...</p>';

        container.appendChild(header);
        container.appendChild(content);

        // Mark as fallback mode
        this.fallbackMode = true;
        console.log('✅ Enhanced fallback visualization created');
    }

    renderFallbackGraph(data) {
        console.log('🎨 Rendering fallback graph with data:', data);

        if (!this.fallbackMode) {
            console.log('🔄 Not in fallback mode, creating fallback visualization first...');
            this.createFallbackVisualization();
        }

        // Update counts
        const nodesCount = document.getElementById('fallback-nodes-count');
        const relationshipsCount = document.getElementById('fallback-relationships-count');
        const content = document.getElementById('fallback-graph-content');

        if (nodesCount) nodesCount.textContent = data.nodes.length;
        if (relationshipsCount) relationshipsCount.textContent = data.relationships.length;

        if (content) {
            try {
                // Try to create a simple D3.js visualization if available
                if (typeof d3 !== 'undefined') {
                    console.log('📊 D3.js available, creating interactive fallback visualization');
                    this.renderD3FallbackGraph(data, content);
                } else {
                    console.log('📋 D3.js not available, using simple HTML fallback');
                    this.renderSimpleHTMLFallback(data, content);
                }
            } catch (error) {
                console.error('❌ Error in fallback rendering:', error);
                console.log('🔄 Using basic HTML fallback');
                this.renderSimpleHTMLFallback(data, content);
            }
        }

        console.log('✅ Fallback graph rendered successfully');
    }

    renderSimpleHTMLFallback(data, content) {
        console.log('📋 Creating simple HTML fallback visualization');

        let html = '<h4 style="color: #495057; margin-bottom: 10px;">📋 Graph Data Summary</h4>';

        // Show sample nodes
        if (data.nodes && data.nodes.length > 0) {
            html += '<h5 style="color: #6c757d; margin: 15px 0 5px 0;">🔵 Entities:</h5>';
            data.nodes.slice(0, 10).forEach((node, i) => {
                try {
                    const name = node.properties?.name || node.id || `Node ${i}`;
                    const labels = node.labels ? node.labels.join(', ') : 'Unknown';
                    html += `<div style="margin: 5px 0; padding: 8px; background: #e9ecef; border-radius: 4px; font-size: 0.9em;">
                        <strong>${name}</strong> <span style="color: #6c757d;">(${labels})</span>
                    </div>`;
                } catch (error) {
                    console.warn('⚠️ Error processing node:', error, node);
                    html += `<div style="margin: 5px 0; padding: 8px; background: #f8d7da; border-radius: 4px; font-size: 0.9em;">
                        <strong>Node ${i}</strong> <span style="color: #721c24;">(Error processing)</span>
                    </div>`;
                }
            });

            if (data.nodes.length > 10) {
                html += `<p style="color: #6c757d; font-style: italic;">... and ${data.nodes.length - 10} more entities</p>`;
            }
        }

        // Show sample relationships
        if (data.relationships && data.relationships.length > 0) {
            html += '<h5 style="color: #6c757d; margin: 15px 0 5px 0;">🔗 Relationships:</h5>';

            // Create a map of node IDs to names for relationship display
            const nodeMap = {};
            console.log('🔍 Building node map from data.nodes:', data.nodes);

            if (data.nodes) {
                data.nodes.forEach((node, index) => {
                    const nodeId = node.id;
                    const nodeName = node.properties?.name || node.id || 'Unknown';
                    nodeMap[nodeId] = nodeName;

                    if (index < 3) {
                        console.log(`📋 Node ${index} mapping: ${nodeId} → ${nodeName}`);
                    }
                });
            }

            console.log('🔍 Complete node map:', nodeMap);
            console.log('🔍 Processing relationships:', data.relationships);

            data.relationships.slice(0, 10).forEach((rel, i) => {
                try {
                    console.log(`🔍 Processing relationship ${i}:`, rel);

                    const type = rel.type || 'CONNECTED';
                    const fromId = rel.from || rel.startNodeId || 'Unknown';
                    const toId = rel.to || rel.endNodeId || 'Unknown';

                    console.log(`🔍 Relationship ${i} IDs: ${fromId} → ${toId}`);

                    // Get node names from the map, fallback to IDs
                    const fromName = nodeMap[fromId] || fromId;
                    const toName = nodeMap[toId] || toId;

                    console.log(`🔍 Relationship ${i} names: ${fromName} → ${toName}`);

                    // Truncate long names for display
                    const fromDisplay = fromName.length > 30 ? fromName.substring(0, 30) + '...' : fromName;
                    const toDisplay = toName.length > 30 ? toName.substring(0, 30) + '...' : toName;

                    html += `<div style="margin: 5px 0; padding: 8px; background: #fff3cd; border-radius: 4px; font-size: 0.9em;">
                        <strong>${type}</strong><br>
                        <span style="color: #6c757d; font-size: 0.8em;">${fromDisplay} → ${toDisplay}</span>
                    </div>`;
                } catch (error) {
                    console.warn('⚠️ Error processing relationship:', error, rel);
                    html += `<div style="margin: 5px 0; padding: 8px; background: #f8d7da; border-radius: 4px; font-size: 0.9em;">
                        <strong>Relationship ${i}</strong> <span style="color: #721c24;">(Error processing)</span>
                    </div>`;
                }
            });

            if (data.relationships.length > 10) {
                html += `<p style="color: #6c757d; font-style: italic;">... and ${data.relationships.length - 10} more relationships</p>`;
            }
        }

        html += '<p style="color: #6c757d; margin-top: 15px; font-size: 0.9em;">💡 This is a simplified view. For interactive graph visualization, the NVL library needs to load properly.</p>';

        content.innerHTML = html;
        console.log('✅ Simple HTML fallback rendered');
    }

    renderD3FallbackGraph(data, container) {
        console.log('📊 Creating D3.js fallback visualization');

        // Clear container and set up for D3
        container.innerHTML = '';
        container.style.cssText = `
            width: 100%;
            height: 400px;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            background: white;
            position: relative;
        `;

        // Create SVG
        const svg = d3.select(container)
            .append('svg')
            .attr('width', '100%')
            .attr('height', '400px');

        const width = container.clientWidth || 800;
        const height = 400;

        // Process data for D3
        const nodes = data.nodes.map(node => ({
            id: node.id,
            name: node.properties?.name || node.id,
            labels: node.labels || [],
            x: Math.random() * width,
            y: Math.random() * height
        }));

        const links = data.relationships.map(rel => ({
            source: rel.startNodeId || rel.from,
            target: rel.endNodeId || rel.to,
            type: rel.type || 'CONNECTED'
        }));

        // Create simple force simulation
        const simulation = d3.forceSimulation(nodes)
            .force('link', d3.forceLink(links).id(d => d.id).distance(100))
            .force('charge', d3.forceManyBody().strength(-300))
            .force('center', d3.forceCenter(width / 2, height / 2));

        // Add links
        const link = svg.append('g')
            .selectAll('line')
            .data(links)
            .enter().append('line')
            .attr('stroke', '#999')
            .attr('stroke-width', 2);

        // Add nodes
        const node = svg.append('g')
            .selectAll('circle')
            .data(nodes)
            .enter().append('circle')
            .attr('r', 8)
            .attr('fill', '#1f77b4')
            .attr('stroke', '#fff')
            .attr('stroke-width', 2);

        // Add labels
        const label = svg.append('g')
            .selectAll('text')
            .data(nodes)
            .enter().append('text')
            .text(d => d.name.length > 20 ? d.name.substring(0, 20) + '...' : d.name)
            .attr('font-size', '10px')
            .attr('dx', 12)
            .attr('dy', 4);

        // Update positions on simulation tick
        simulation.on('tick', () => {
            link
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);

            node
                .attr('cx', d => d.x)
                .attr('cy', d => d.y);

            label
                .attr('x', d => d.x)
                .attr('y', d => d.y);
        });

        console.log('✅ D3.js fallback visualization created');
    }

    async loadAndRenderGraph(entity, limit, query = null) {
        console.log('🚀 loadAndRenderGraph called with:', { entity, limit, query });
        this.showLoading();

        try {
            console.log('📡 Fetching graph data...');
            // Fetch graph data from API
            const graphData = await this.fetchGraphData(entity, limit, query);

            console.log('📊 Graph data received, checking content...');
            console.log('📊 Graph data summary:', {
                hasData: !!graphData,
                hasNodes: !!graphData?.nodes,
                nodeCount: graphData?.nodes ? graphData.nodes.length : 0,
                hasRelationships: !!graphData?.relationships,
                relationshipCount: graphData?.relationships ? graphData.relationships.length : 0,
                hasError: !!graphData?.error
            });

            if (graphData && (graphData.nodes || graphData.relationships)) {
                console.log('🎨 Data found, calling renderGraph...');
                this.renderGraph(graphData);
                this.hideLoading();

                // Log metadata if available
                if (graphData.metadata) {
                    console.log('📊 Graph metadata:', graphData.metadata);
                }
                console.log('✅ loadAndRenderGraph completed successfully');
            } else {
                console.warn('⚠️ No graph data found in response');
                console.log('📋 Full response:', graphData);
                this.hideLoading();
                this.showError('No graph data found');
            }
        } catch (error) {
            console.error('❌ Failed to load graph data:', error);
            console.error('❌ Error details:', {
                message: error.message,
                stack: error.stack
            });
            this.hideLoading();
            this.showError('Failed to load graph data: ' + error.message);
        }
    }
    
    async fetchGraphData(entity, limit, query = null) {
        const params = new URLSearchParams({
            limit: limit.toString()
        });

        if (query) {
            // Use hybrid search endpoint for queries
            params.append('query', query);
            const url = `/api/graph/hybrid/search?${params}`;
            console.log(`🌐 Fetching hybrid data from: ${url}`);

            const response = await fetch(url);
            console.log(`📡 Hybrid response status: ${response.status} ${response.statusText}`);

            if (!response.ok) {
                const errorText = await response.text();
                console.error(`❌ Hybrid API Error: ${response.status} - ${errorText}`);
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            console.log('📊 Hybrid API Response data received');
            console.log('📊 Hybrid data structure:', {
                nodes: data.nodes ? data.nodes.length : 'undefined',
                relationships: data.relationships ? data.relationships.length : 'undefined'
            });
            return data;
        } else {
            // Use direct Neo4j endpoint for entity-based searches
            if (entity) {
                params.append('entity', entity);
            }

            const url = `/api/graph/neo4j/visualize?${params}`;
            console.log(`🌐 Fetching Neo4j data from: ${url}`);

            const response = await fetch(url);
            console.log(`📡 Neo4j response status: ${response.status} ${response.statusText}`);

            if (!response.ok) {
                const errorText = await response.text();
                console.error(`❌ Neo4j API Error: ${response.status} - ${errorText}`);
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            console.log('📊 Neo4j API Response data received');
            console.log('📊 Neo4j data structure:', {
                nodes: data.nodes ? data.nodes.length : 'undefined',
                relationships: data.relationships ? data.relationships.length : 'undefined',
                metadata: data.metadata || 'undefined'
            });
            console.log('📊 Sample node:', data.nodes && data.nodes[0] ? data.nodes[0] : 'No nodes');
            console.log('📊 Sample relationship:', data.relationships && data.relationships[0] ? data.relationships[0] : 'No relationships');
            return data;
        }
    }
    
    renderGraph(data) {
        console.log('🎨 Starting renderGraph with data:', data);
        console.log('🔍 Data structure check:');
        console.log('  - data.nodes:', data.nodes ? data.nodes.length : 'undefined');
        console.log('  - data.relationships:', data.relationships ? data.relationships.length : 'undefined');
        console.log('  - data.links:', data.links ? data.links.length : 'undefined');

        // Check if we have any data at all
        if (!data || (!data.nodes && !data.relationships)) {
            console.error('❌ No data provided to renderGraph');
            this.showError('No graph data received from server');
            return;
        }

        if (!this.nvl) {
            console.warn('⚠️ NVL not initialized, using fallback visualization');
            this.renderFallbackGraph(data);
            return;
        }

        try {
            console.log('🔄 Processing graph data...');

            // Process and style the data
            const processedData = this.processGraphData(data);
            console.log('✅ Data processed successfully:', processedData);
            console.log('📊 Processed data details:');
            console.log('  - Nodes count:', processedData.nodes.length);
            console.log('  - Relationships count:', processedData.relationships.length);
            console.log('  - Sample node:', processedData.nodes[0]);
            console.log('  - Sample relationship:', processedData.relationships[0]);

            // Update stats in UI
            document.getElementById('graph-nodes-count').textContent = `Nodes: ${processedData.nodes.length}`;
            document.getElementById('graph-edges-count').textContent = `Edges: ${processedData.relationships.length}`;

            // Check if we have any data to render
            if (processedData.nodes.length === 0 && processedData.relationships.length === 0) {
                console.warn('⚠️ No data to render after processing');
                this.showError('No graph data found for the specified entity');
                return;
            }

            // Check graph canvas container
            const container = document.getElementById('graph-canvas');
            console.log('🔍 Graph canvas container:', container);

            // Check if container is visible and has dimensions
            const containerStyle = container ? getComputedStyle(container) : null;
            const dimensions = {
                width: container ? container.clientWidth : 'N/A',
                height: container ? container.clientHeight : 'N/A',
                display: containerStyle ? containerStyle.display : 'N/A',
                visibility: containerStyle ? containerStyle.visibility : 'N/A'
            };
            console.log('🔍 Container dimensions:', dimensions);

            // If container has zero dimensions, ensure it's properly sized
            if (container && (container.clientWidth === 0 || container.clientHeight === 0)) {
                console.warn('⚠️ Container has zero dimensions, fixing...');

                // Ensure the modal is visible first
                const modal = document.getElementById('graph-modal');
                if (modal) {
                    console.log('📐 Making modal visible for proper sizing');
                    modal.style.display = 'block';

                    // Force a reflow to ensure the modal is rendered
                    modal.offsetHeight;
                }

                // Ensure the graph container parent has proper dimensions
                const graphContainer = container.parentElement;
                if (graphContainer) {
                    graphContainer.style.width = '100%';
                    graphContainer.style.height = '500px';
                    graphContainer.style.minHeight = '500px';
                    graphContainer.style.display = 'block';
                }

                // Set explicit dimensions for the canvas container
                container.style.width = '100%';
                container.style.height = '500px';
                container.style.minHeight = '500px';
                container.style.display = 'block';
                container.style.position = 'relative';

                // Force a reflow to ensure dimensions are applied
                container.offsetHeight;

                console.log('📐 Updated container dimensions:', {
                    width: container.clientWidth,
                    height: container.clientHeight,
                    offsetWidth: container.offsetWidth,
                    offsetHeight: container.offsetHeight,
                    parentWidth: graphContainer ? graphContainer.clientWidth : 'N/A',
                    parentHeight: graphContainer ? graphContainer.clientHeight : 'N/A'
                });
            }

            // Try to render with NVL
            console.log('🚀 Attempting to render with NVL...');
            console.log('🔍 NVL instance check:', this.nvl);
            console.log('🔍 NVL type:', typeof this.nvl);
            console.log('🔍 NVL constructor:', this.nvl.constructor.name);

            this.renderWithNVL(processedData, container);
        } catch (error) {
            console.error('❌ Failed to render graph:', error);
            this.createFallbackVisualization();
        }

        console.log('✅ Graph rendering completed successfully');
    }

    renderWithNVL(processedData, container) {
        try {
            if (this.nvl) {
                // Get all available methods on the NVL instance
                const nvlMethods = Object.getOwnPropertyNames(Object.getPrototypeOf(this.nvl));
                console.log('🔍 All NVL methods:', nvlMethods);

                // Ensure container has proper dimensions before rendering
                if (container.clientWidth === 0 || container.clientHeight === 0) {
                    console.warn('⚠️ Container still has zero dimensions after initial fix');
                    console.log('🔄 Falling back to D3 visualization due to container sizing issues');
                    this.renderFallbackGraph(processedData);
                    return;
                }

                // Check available methods (use the correct NVL methods)
                const hasAddAndUpdate = typeof this.nvl.addAndUpdateElementsInGraph === 'function';
                const hasUpdateElements = typeof this.nvl.updateElementsInGraph === 'function';
                const hasAddElements = typeof this.nvl.addElementsToGraph === 'function';

                console.log('🔍 NVL method availability:');
                console.log('  - addAndUpdateElementsInGraph:', hasAddAndUpdate);
                console.log('  - updateElementsInGraph:', hasUpdateElements);
                console.log('  - addElementsToGraph:', hasAddElements);

                // Try different methods to render the graph
                let renderSuccess = false;

                // Method 1: Try addAndUpdateElementsInGraph (recommended for updating existing graph)
                if (hasAddAndUpdate) {
                    try {
                        console.log('📡 Calling nvl.addAndUpdateElementsInGraph with:', {
                            nodes: processedData.nodes.length,
                            relationships: processedData.relationships.length,
                            containerDimensions: {
                                width: container.clientWidth,
                                height: container.clientHeight
                            }
                        });

                        // Log sample data to verify captions
                        if (processedData.nodes.length > 0) {
                            console.log('📋 Sample node with caption:', {
                                id: processedData.nodes[0].id,
                                caption: processedData.nodes[0].caption,
                                color: processedData.nodes[0].color,
                                size: processedData.nodes[0].size
                            });
                        }
                        if (processedData.relationships.length > 0) {
                            console.log('📋 Sample relationship with caption:', {
                                id: processedData.relationships[0].id,
                                caption: processedData.relationships[0].caption,
                                color: processedData.relationships[0].color,
                                width: processedData.relationships[0].width
                            });
                        }

                        this.nvl.addAndUpdateElementsInGraph(processedData.nodes, processedData.relationships);
                        console.log('✅ nvl.addAndUpdateElementsInGraph called successfully');
                        renderSuccess = true;

                        // Try to fit the graph to view after a short delay
                        if (typeof this.nvl.fit === 'function') {
                            setTimeout(() => {
                                try {
                                    this.nvl.fit();
                                    console.log('✅ Graph fitted to view');
                                } catch (e) {
                                    console.warn('⚠️ Failed to fit graph:', e);
                                }
                            }, 500);
                        }

                    } catch (error) {
                        console.warn('⚠️ nvl.addAndUpdateElementsInGraph failed:', error);
                        console.warn('⚠️ Error details:', error.stack);
                    }
                } else if (hasAddElements) {
                    try {
                        console.log('📡 Calling nvl.addElementsToGraph...');
                        this.nvl.addElementsToGraph(processedData.nodes, processedData.relationships);
                        console.log('✅ nvl.addElementsToGraph called successfully');
                        renderSuccess = true;
                    } catch (error) {
                        console.warn('⚠️ nvl.addElementsToGraph failed:', error);
                    }
                }

                if (!renderSuccess) {
                    console.warn('⚠️ All NVL render methods failed or unavailable, using fallback');
                    this.renderFallbackGraph(processedData);
                } else {
                    // Try to fit the view if available
                    if (typeof this.nvl.fit === 'function') {
                        try {
                            console.log('📐 Calling nvl.fit() to adjust view');
                            this.nvl.fit();
                        } catch (error) {
                            console.warn('⚠️ nvl.fit() failed:', error);
                        }
                    }
                }

            } else {
                console.log('⚠️ NVL not available, using fallback visualization');
                this.renderFallbackGraph(processedData);
            }
        } catch (error) {
            console.error('❌ Failed to render with NVL:', error);
            console.error('❌ Error stack:', error.stack);
            console.log('🔄 Falling back to D3 visualization');
            this.renderFallbackGraph(processedData);
        }
    }
    
    processGraphData(data) {
        console.log('🔄 processGraphData called with:', data);
        console.log('🔍 Input data structure:');
        console.log('  - data.nodes:', data.nodes ? `Array(${data.nodes.length})` : 'undefined');
        console.log('  - data.relationships:', data.relationships ? `Array(${data.relationships.length})` : 'undefined');
        console.log('  - data.links:', data.links ? `Array(${data.links.length})` : 'undefined');

        // Process nodes
        const rawNodes = data.nodes || [];
        console.log(`📊 Processing ${rawNodes.length} nodes...`);

        const nodes = rawNodes.map((node, index) => {
            const nodeType = node.labels?.[0] || node.type || 'default';
            const style = this.nodeStyles[nodeType] || this.nodeStyles.default;

            // Extract entity name
            const entityName = node.properties?.name || node.properties?.title || node.name || `Node ${node.id}`;

            const processedNode = {
                id: node.id || node.elementId,
                labels: node.labels || [nodeType],
                properties: {
                    name: entityName,
                    ...node.properties
                },
                // NVL-specific styling (based on reference example)
                color: style.color,
                size: style.size,
                caption: entityName, // Simple caption property for entity name
                style: {
                    color: style.color,
                    size: style.size,
                    icon: style.icon
                }
            };

            if (index < 3) {
                console.log(`📋 Processed node ${index}:`, processedNode);
                console.log(`📋 Node caption:`, processedNode.caption);
                console.log(`📋 Node color:`, processedNode.color);
                console.log(`📋 Node size:`, processedNode.size);
            }

            return processedNode;
        });

        // Process relationships - NVL expects 'from' and 'to' properties
        const rawRelationships = data.relationships || data.links || [];
        console.log(`📊 Processing ${rawRelationships.length} relationships...`);

        const relationships = rawRelationships.map((rel, index) => {
            const relType = rel.type || rel.relationship || 'CONNECTED_TO';
            const style = this.relationshipStyles[relType] || this.relationshipStyles.default;

            const processedRel = {
                id: rel.id || rel.elementId || `${rel.startNodeId || rel.source}-${rel.endNodeId || rel.target}`,
                type: relType,
                from: rel.startNodeId || rel.source,
                to: rel.endNodeId || rel.target,
                properties: rel.properties || {},
                // NVL-specific styling (based on reference example)
                color: style.color,
                width: style.width,
                caption: relType.replace(/_/g, ' '), // Simple caption property for relationship label
                style: {
                    color: style.color,
                    width: style.width
                }
            };

            if (index < 3) {
                console.log(`📋 Processed relationship ${index}:`, processedRel);
                console.log(`📋 Relationship caption:`, processedRel.caption);
                console.log(`📋 Relationship color:`, processedRel.color);
                console.log(`📋 Relationship width:`, processedRel.width);
            }

            return processedRel;
        });

        const result = { nodes, relationships };

        console.log('✅ processGraphData completed:', {
            inputNodes: rawNodes.length,
            inputRelationships: rawRelationships.length,
            outputNodes: nodes.length,
            outputRelationships: relationships.length
        });

        return result;
    }

    renderFallbackGraph(data) {
        console.log('🎨 Rendering fallback graph visualization');

        const container = document.getElementById('graph-canvas');
        container.innerHTML = ''; // Clear existing content

        // Create a simple HTML-based visualization
        const graphDiv = document.createElement('div');
        graphDiv.style.cssText = `
            padding: 20px;
            font-family: Arial, sans-serif;
            background: white;
            height: 100%;
            overflow-y: auto;
        `;

        // Add title
        const title = document.createElement('h3');
        title.textContent = 'Knowledge Graph (Fallback View)';
        title.style.cssText = 'margin: 0 0 20px 0; color: #333;';
        graphDiv.appendChild(title);

        // Add nodes section
        if (data.nodes && data.nodes.length > 0) {
            const nodesSection = document.createElement('div');
            nodesSection.innerHTML = `<h4 style="color: #2196F3; margin: 15px 0 10px 0;">Entities (${data.nodes.length})</h4>`;

            data.nodes.forEach(node => {
                const nodeDiv = document.createElement('div');
                const nodeType = node.labels?.[0] || 'Unknown';
                const nodeName = node.properties?.name || node.id;
                const nodeStyle = this.nodeStyles[nodeType] || this.nodeStyles.default;
                const nodeColor = nodeStyle.color;

                nodeDiv.style.cssText = `
                    margin: 8px 0;
                    padding: 10px;
                    border-left: 4px solid ${nodeColor};
                    background: #f8f9fa;
                    border-radius: 4px;
                    cursor: pointer;
                `;

                nodeDiv.innerHTML = `
                    <strong style="color: ${nodeColor};">${nodeName}</strong>
                    <span style="color: #666; margin-left: 10px;">(${nodeType})</span>
                `;

                nodeDiv.addEventListener('click', () => {
                    this.onNodeClick(node);
                });

                nodesSection.appendChild(nodeDiv);
            });

            graphDiv.appendChild(nodesSection);
        }

        // Add relationships section
        if (data.relationships && data.relationships.length > 0) {
            const relsSection = document.createElement('div');
            relsSection.innerHTML = `<h4 style="color: #9C27B0; margin: 15px 0 10px 0;">Relationships (${data.relationships.length})</h4>`;

            data.relationships.forEach(rel => {
                const relDiv = document.createElement('div');
                const relColor = this.relationshipStyles[rel.type]?.color || '#999';

                // Find node names
                const fromNode = data.nodes.find(n => n.id === rel.from);
                const toNode = data.nodes.find(n => n.id === rel.to);
                const fromName = fromNode?.properties?.name || rel.from;
                const toName = toNode?.properties?.name || rel.to;

                relDiv.style.cssText = `
                    margin: 8px 0;
                    padding: 10px;
                    border-left: 4px solid ${relColor};
                    background: #f8f9fa;
                    border-radius: 4px;
                    cursor: pointer;
                `;

                relDiv.innerHTML = `
                    <span style="font-weight: bold;">${fromName}</span>
                    <span style="color: ${relColor}; margin: 0 10px;">→ ${rel.type} →</span>
                    <span style="font-weight: bold;">${toName}</span>
                `;

                relDiv.addEventListener('click', () => {
                    this.onRelationshipClick(rel);
                });

                relsSection.appendChild(relDiv);
            });

            graphDiv.appendChild(relsSection);
        }

        // Add message if no data
        if ((!data.nodes || data.nodes.length === 0) && (!data.relationships || data.relationships.length === 0)) {
            const noDataDiv = document.createElement('div');
            noDataDiv.style.cssText = 'text-align: center; color: #666; padding: 40px;';
            noDataDiv.innerHTML = `
                <i class="fas fa-info-circle" style="font-size: 2rem; margin-bottom: 10px;"></i>
                <p>No graph data available for the specified entity.</p>
            `;
            graphDiv.appendChild(noDataDiv);
        }

        container.appendChild(graphDiv);
        console.log('✅ Fallback graph rendered');
    }

    // Event handlers
    onNodeClick(node) {
        console.log('Node clicked:', node);
        
        // Show node details in a tooltip or sidebar
        this.showNodeDetails(node);
        
        // Optionally expand the graph from this node
        // this.expandFromNode(node);
    }
    
    onRelationshipClick(relationship) {
        console.log('Relationship clicked:', relationship);
        this.showRelationshipDetails(relationship);
    }
    
    onCanvasClick() {
        // Clear any selections or details
        this.clearSelections();
    }
    
    showNodeDetails(node) {
        console.log('🔍 showNodeDetails called with node:', node);

        // Handle different node structures (NVL vs fallback)
        let nodeData, properties, labels, name;

        if (node.data) {
            // NVL node structure
            nodeData = node.data;
            properties = nodeData.properties || {};
            labels = nodeData.labels || [];
            name = properties.name || properties.title || nodeData.id || 'Unknown';
        } else {
            // Direct node structure
            nodeData = node;
            properties = node.properties || {};
            labels = node.labels || [];
            name = properties.name || properties.title || node.id || 'Unknown';
        }

        console.log('🔍 Extracted node data:', { name, labels, properties });

        // Create a simple tooltip or use existing UI elements
        const details = `
            <strong>${name}</strong><br>
            Type: ${labels.join(', ')}<br>
            ${Object.entries(properties)
                .filter(([key]) => key !== 'name' && key !== 'title')
                .map(([key, value]) => `${key}: ${value}`)
                .join('<br>')}
        `;
        
        // You could show this in a tooltip, sidebar, or modal
        console.log('Node details:', details);
    }
    
    showRelationshipDetails(relationship) {
        const details = `
            <strong>${relationship.type}</strong><br>
            ${Object.entries(relationship.properties)
                .map(([key, value]) => `${key}: ${value}`)
                .join('<br>')}
        `;
        
        console.log('Relationship details:', details);
    }
    
    clearSelections() {
        // Clear any UI selections
    }
    
    // Graph controls
    zoomIn() {
        if (this.nvl && typeof this.nvl.setZoom === 'function') {
            try {
                const currentZoom = this.nvl.getScale();
                const newZoom = currentZoom * 1.2;
                this.nvl.setZoom(newZoom);
                console.log(`🔍 Zoomed in from ${currentZoom} to ${newZoom}`);
            } catch (error) {
                console.warn('⚠️ Zoom in failed:', error);
            }
        }
    }

    zoomOut() {
        if (this.nvl && typeof this.nvl.setZoom === 'function') {
            try {
                const currentZoom = this.nvl.getScale();
                const newZoom = currentZoom * 0.8;
                this.nvl.setZoom(newZoom);
                console.log(`🔍 Zoomed out from ${currentZoom} to ${newZoom}`);
            } catch (error) {
                console.warn('⚠️ Zoom out failed:', error);
            }
        }
    }

    resetZoom() {
        if (this.nvl && typeof this.nvl.resetZoom === 'function') {
            try {
                this.nvl.fit();
                console.log('🔍 Zoom reset to default');
            } catch (error) {
                console.warn('⚠️ Reset zoom failed:', error);
            }
        }
    }
    
    centerGraph() {
        if (this.nvl) {
            this.nvl.fit();
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
    
    async refreshGraph() {
        if (this.currentEntity !== null) {
            await this.loadAndRenderGraph(this.currentEntity, this.currentDepth);
        }
    }

    // Method to visualize graph from chat query
    async visualizeFromQuery(query, depth = 3) {
        this.currentEntity = '';
        this.currentDepth = depth;

        // Update UI
        document.getElementById('graph-entity').value = '';
        document.getElementById('graph-depth').value = depth;
        document.getElementById('graph-depth-display').textContent = `Depth: ${depth}`;

        // Show modal
        document.getElementById('graph-modal').style.display = 'block';

        // Initialize NVL if not already done
        if (!this.nvl) {
            this.initializeNVL();
        }

        // Load and render graph with query
        await this.loadAndRenderGraph('', depth, query);
    }
    
    exportGraph() {
        if (!this.nvl) return;
        
        try {
            // Export as PNG using NVL's built-in functionality
            this.nvl.exportToPNG(`knowledge-graph-${Date.now()}.png`);
        } catch (error) {
            console.error('Failed to export graph:', error);
            
            // Fallback: export the current graph data as JSON
            const dataStr = JSON.stringify(this.graphData, null, 2);
            const blob = new Blob([dataStr], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            
            const link = document.createElement('a');
            link.href = url;
            link.download = `knowledge-graph-data-${Date.now()}.json`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            URL.revokeObjectURL(url);
        }
    }
}

// Initialize graph visualization when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 DOM loaded, initializing graph visualization...');
    console.log('🔍 Checking for NVL library...');
    console.log('📦 typeof NVL:', typeof NVL);
    console.log('📦 typeof window.NVL:', typeof window.NVL);
    console.log('📦 NVL object:', typeof NVL !== 'undefined' ? NVL : 'undefined');
    console.log('📦 window.NVL object:', typeof window.NVL !== 'undefined' ? window.NVL : 'undefined');

    // Check all possible NVL variations
    const nvlVariations = ['NVL', 'nvl', 'Neo4jVisualizationLibrary', 'neo4jNVL'];
    nvlVariations.forEach(variation => {
        console.log(`📦 window.${variation}:`, typeof window[variation] !== 'undefined' ? window[variation] : 'undefined');
    });

    // Wait for NVL to be available
    if (typeof NVL !== 'undefined') {
        console.log('✅ NVL found, creating Neo4jGraphVisualization...');
        try {
            window.neo4jGraphVisualization = new Neo4jGraphVisualization();
            console.log('✅ Neo4jGraphVisualization created successfully');
        } catch (error) {
            console.error('❌ Failed to create Neo4jGraphVisualization:', error);
            console.error('❌ Error stack:', error.stack);
        }
    } else if (typeof window.NVL !== 'undefined') {
        console.log('✅ window.NVL found, using that...');
        window.NVL = window.NVL;  // Make it globally available
        try {
            window.neo4jGraphVisualization = new Neo4jGraphVisualization();
            console.log('✅ Neo4jGraphVisualization created successfully with window.NVL');
        } catch (error) {
            console.error('❌ Failed to create Neo4jGraphVisualization with window.NVL:', error);
            console.error('❌ Error stack:', error.stack);
        }
    } else {
        console.log('⏳ NVL not found, retrying in 3 seconds...');
        // Retry after a longer delay
        setTimeout(() => {
            console.log('🔄 Retry: Checking for NVL again...');
            console.log('🔄 typeof NVL:', typeof NVL);
            console.log('🔄 typeof window.NVL:', typeof window.NVL);

            if (typeof NVL !== 'undefined' || typeof window.NVL !== 'undefined') {
                console.log('✅ NVL found on retry, creating Neo4jGraphVisualization...');
                try {
                    if (typeof window.NVL !== 'undefined' && typeof NVL === 'undefined') {
                        window.NVL = window.NVL;  // Make it globally available
                    }
                    window.neo4jGraphVisualization = new Neo4jGraphVisualization();
                    console.log('✅ Neo4jGraphVisualization created successfully on retry');
                } catch (error) {
                    console.error('❌ Failed to create Neo4jGraphVisualization on retry:', error);
                    console.error('❌ Error stack:', error.stack);
                }
            } else {
                console.error('❌ NVL library still not loaded after retry');
                console.log('📋 Available globals containing "nvl" or "NVL":',
                    Object.keys(window).filter(k => k.toLowerCase().includes('nvl')));
                console.log('📋 All script tags:',
                    Array.from(document.querySelectorAll('script')).map(s => s.src));

                // Create a fallback visualization without NVL
                console.log('🔄 Creating fallback visualization without NVL...');
                try {
                    window.neo4jGraphVisualization = new Neo4jGraphVisualization();
                    console.log('✅ Fallback visualization created');
                } catch (error) {
                    console.error('❌ Failed to create fallback visualization:', error);
                    console.error('❌ Error stack:', error.stack);
                }
            }
        }, 3000);
    }
});

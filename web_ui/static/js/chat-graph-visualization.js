/**
 * Chat Graph Visualization Component
 * Renders Neo4j graphs inline with chat messages
 */

class ChatGraphVisualization {
    constructor() {
        this.graphInstances = new Map(); // Track graph instances by message ID
        this.graphCounter = 0;
        console.log('🎯 ChatGraphVisualization initialized');
    }

    /**
     * Create a graph visualization container for a chat message
     * @param {HTMLElement} messageElement - The message element to add graph to
     * @param {Object} graphData - Graph data with nodes and relationships
     * @param {string} messageId - Unique identifier for this message
     */
    createInlineGraph(messageElement, graphData, messageId = null) {
        try {
            // Generate unique ID if not provided
            if (!messageId) {
                messageId = `chat-graph-${++this.graphCounter}`;
            }

            console.log('🎯 Creating inline graph for message:', messageId);
            console.log('📊 Graph data:', graphData);

            // Create graph container
            const graphContainer = document.createElement('div');
            graphContainer.className = 'chat-graph-container';
            graphContainer.id = `${messageId}-container`;

            // Create graph header
            const graphHeader = document.createElement('div');
            graphHeader.className = 'chat-graph-header';
            graphHeader.innerHTML = `
                <div class="graph-title">
                    <i class="fas fa-project-diagram"></i>
                    <span>Knowledge Graph Visualization</span>
                </div>
                <div class="graph-stats">
                    <span class="node-count">${graphData.nodes?.length || 0} nodes</span>
                    <span class="relationship-count">${graphData.relationships?.length || 0} relationships</span>
                </div>
            `;

            // Create graph canvas
            const graphCanvas = document.createElement('div');
            graphCanvas.className = 'chat-graph-canvas';
            graphCanvas.id = messageId;
            graphCanvas.style.width = '100%';
            graphCanvas.style.height = '400px';
            graphCanvas.style.border = '1px solid #ddd';
            graphCanvas.style.borderRadius = '8px';
            graphCanvas.style.backgroundColor = '#ffffff';

            // Create graph controls
            const graphControls = document.createElement('div');
            graphControls.className = 'chat-graph-controls';
            graphControls.innerHTML = `
                <button class="graph-control-btn" onclick="chatGraphViz.resetZoom('${messageId}')">
                    <i class="fas fa-search-minus"></i> Reset Zoom
                </button>
                <button class="graph-control-btn primary" onclick="chatGraphViz.showChatGraphDetails('${messageId}')">
                    <i class="fas fa-database"></i> Query Details
                </button>
                <button class="graph-control-btn" onclick="chatGraphViz.fitGraph('${messageId}')">
                    <i class="fas fa-expand-arrows-alt"></i> Fit View
                </button>
            `;

            // Assemble the graph component
            graphContainer.appendChild(graphHeader);
            graphContainer.appendChild(graphCanvas);
            graphContainer.appendChild(graphControls);

            // Store graph data for later access by details modal
            graphContainer.graphData = graphData;

            // Add message ID attribute for easy lookup
            messageElement.setAttribute('data-message-id', messageId);

            // Add to message
            const messageContent = messageElement.querySelector('.message-content');
            if (messageContent) {
                messageContent.appendChild(graphContainer);
            } else {
                messageElement.appendChild(graphContainer);
            }

            // Initialize the graph visualization
            this.initializeGraph(messageId, graphData);

            return graphContainer;

        } catch (error) {
            console.error('❌ Failed to create inline graph:', error);
            this.showGraphError(messageElement, error.message);
        }
    }

    /**
     * Initialize the Neo4j NVL graph visualization
     * @param {string} containerId - Container ID for the graph
     * @param {Object} graphData - Graph data with nodes and relationships
     */
    async initializeGraph(containerId, graphData) {
        try {
            console.log('🎯 Initializing graph for container:', containerId);

            // Wait for NVL to be available
            if (typeof window.NVL === 'undefined') {
                console.warn('⚠️ NVL not available, waiting...');
                await this.waitForNVL();
            }

            const container = document.getElementById(containerId);
            if (!container) {
                throw new Error(`Container ${containerId} not found`);
            }

            // Debug: Log raw graph data before validation
            console.log('📊 Raw graph data received:', graphData);
            console.log('📊 Raw nodes count:', graphData?.nodes?.length || 0);
            console.log('📊 Raw relationships count:', graphData?.relationships?.length || 0);
            console.log('📊 Raw relationships data:', graphData?.relationships);

            // Validate and prepare graph data
            const validatedData = this.validateGraphData(graphData);

            // Debug: Log validated data
            console.log('📊 Validated graph data:', validatedData.nodes.length, 'nodes,', validatedData.relationships.length, 'relationships');
            console.log('📊 Final nodes:', validatedData.nodes);
            console.log('📊 Final relationships:', validatedData.relationships);

            if (!validatedData.nodes.length) {
                this.showEmptyGraphMessage(container);
                return;
            }

            // Create NVL instance - handle both module and constructor formats
            let NVLConstructor = window.NVL;

            // If NVL is a module, get the default export or constructor
            if (typeof NVLConstructor === 'object' && NVLConstructor.default) {
                NVLConstructor = NVLConstructor.default;
            } else if (typeof NVLConstructor === 'object' && NVLConstructor.NVL) {
                NVLConstructor = NVLConstructor.NVL;
            } else if (typeof NVLConstructor === 'object') {
                // Try to find the constructor in the module
                const keys = Object.keys(NVLConstructor);
                for (const key of keys) {
                    if (typeof NVLConstructor[key] === 'function' && key.includes('NVL')) {
                        NVLConstructor = NVLConstructor[key];
                        break;
                    }
                }
            }

            console.log('🔧 Using NVL constructor:', typeof NVLConstructor, NVLConstructor);

            // Format nodes for NVL (exactly following reference StyleExample.js pattern)
            const nodes = validatedData.nodes.map(node => {
                const nodeType = node.labels && node.labels.length > 0 ? node.labels[0] : 'Entity';
                const entityName = node.properties?.name || node.id || 'Unknown';

                // Color mapping for different entity types
                const nodeColors = {
                    'Person': '#4CAF50',      // Green for persons
                    'Company': '#2196F3',     // Blue for companies
                    'Organization': '#FF9800', // Orange for organizations
                    'Entity': '#9C27B0',      // Purple for generic entities
                    'default': '#757575'      // Gray for unknown types
                };

                return {
                    id: node.id,                                    // Required: node ID
                    color: nodeColors[nodeType] || nodeColors.default, // Required: node color
                    caption: entityName,                            // Required: entity name as caption
                    size: 40,                                       // Required: node size
                    selected: false,                                // Required: selection state
                    hovered: false                                  // Required: hover state
                };
            });

            // Format relationships for NVL (exactly following reference StyleExample.js pattern)
            const rels = validatedData.relationships.map(rel => ({
                id: rel.id,                                         // Required: relationship ID
                from: rel.startNode || rel.startNodeId,            // Required: source node ID
                to: rel.endNode || rel.endNodeId,                  // Required: target node ID
                color: '#666666',                                   // Required: relationship color
                caption: rel.type || 'RELATED_TO',                 // Required: relationship type as caption
                width: 2,                                           // Required: relationship width
                selected: false,                                    // Required: selection state
                hovered: false                                      // Required: hover state
            }));

            console.log('🔧 NVL formatted nodes:', nodes);
            console.log('🔧 NVL formatted relationships:', rels);

            // Create NVL instance (exactly following reference StyleExample.js pattern)
            const nvl = new NVLConstructor(container, nodes, rels, {
                layout: 'forceDirected',                           // Use force-directed layout
                initialZoom: 0.8,                                  // Set initial zoom
                styling: {
                    nodeDefaultBorderColor: '#ffffff',             // White border for nodes
                    selectedBorderColor: '#4CAF50'                 // Green border when selected
                }
            });

            console.log('✅ NVL graph created with StyleExample.js pattern');

            // Add enhanced interactions
            this.addGraphInteractions(nvl, containerId, validatedData);

            // Store the graph instance
            this.graphInstances.set(containerId, nvl);

            console.log('✅ Chat graph initialized successfully:', containerId);

        } catch (error) {
            console.error('❌ Failed to initialize graph:', error);
            console.log('🔄 Falling back to simple graph visualization...');

            // Fallback to simple graph visualization
            this.createSimpleGraphVisualization(containerId, validatedData);
        }
    }

    /**
     * Add enhanced interactions to the graph using Neo4j NVL interaction handlers
     * @param {Object} nvl - NVL graph instance
     * @param {string} containerId - Container ID
     * @param {Object} graphData - Graph data
     */
    addGraphInteractions(nvl, containerId, graphData) {
        try {
            console.log('🎮 Adding Neo4j NVL interaction handlers to graph:', containerId);

            // Check if interaction handlers are available
            if (typeof window.NVLInteractions === 'undefined') {
                console.warn('⚠️ NVL interaction handlers not available, falling back to basic interactions');
                this.addBasicInteractions(nvl, containerId, graphData);
                return;
            }

            // Enable simplified interactions by default for chat graphs
            console.log('🎮 Using simplified interaction setup for chat graph following PlainInteractionModulesExampleCode.js pattern...');

            const {
                ZoomInteraction,
                PanInteraction,
                DragNodeInteraction,
                ClickInteraction,
                HoverInteraction
            } = window.NVLInteractions;

            // Add core interaction handlers following the PlainInteractionModulesExampleCode.js pattern
            console.log('🎮 Adding ZoomInteraction...');
            new ZoomInteraction(nvl);

            console.log('🎮 Adding PanInteraction...');
            new PanInteraction(nvl);

            console.log('🎮 Adding DragNodeInteraction...');
            new DragNodeInteraction(nvl);

            console.log('🎮 Adding ClickInteraction with selectOnClick...');
            const clickInteraction = new ClickInteraction(nvl, {
                selectOnClick: true
            });

            console.log('🎮 Adding HoverInteraction with shadow...');
            const hoverInteraction = new HoverInteraction(nvl, {
                drawShadowOnHover: true
            });

            // Add custom event handlers for our application-specific functionality
            this.addCustomEventHandlers(nvl, containerId, graphData);

            // Store interaction instances for potential cleanup
            this.storeInteractionInstances(containerId, {
                zoom: ZoomInteraction,
                pan: PanInteraction,
                drag: DragNodeInteraction,
                click: clickInteraction,
                hover: hoverInteraction
            });

            console.log('✅ All Neo4j NVL interaction handlers added successfully:', containerId);

        } catch (error) {
            console.error('❌ Failed to add NVL interaction handlers:', error);
            console.log('🔄 Falling back to basic interactions...');
            this.addBasicInteractions(nvl, containerId, graphData);
        }
    }

    /**
     * Add custom event handlers for application-specific functionality
     * @param {Object} nvl - NVL graph instance
     * @param {string} containerId - Container ID
     * @param {Object} graphData - Graph data
     */
    addCustomEventHandlers(nvl, containerId, graphData) {
        try {
            // Try to use NVL's event system for custom handlers
            if (nvl && typeof nvl.on === 'function') {
                console.log('🎮 Adding custom event handlers using NVL events...');

                // Node click handler for showing details
                nvl.on('nodeClick', (event) => {
                    console.log('🎯 Node clicked:', event);
                    const node = this.findNodeById(event.nodeId, graphData);
                    if (node) {
                        this.showNodeDetails(node, containerId);
                    }
                });

                // Relationship click handler for showing details
                nvl.on('relationshipClick', (event) => {
                    console.log('🎯 Relationship clicked:', event);
                    const relationship = this.findRelationshipById(event.relationshipId, graphData);
                    if (relationship) {
                        this.showRelationshipDetails(relationship, containerId);
                    }
                });

                // Node hover handler for showing tooltips
                nvl.on('nodeHover', (event) => {
                    const node = this.findNodeById(event.nodeId, graphData);
                    if (node) {
                        this.showNodeTooltip(node, {x: event.x, y: event.y}, containerId);
                    }
                });

                // Node selection handler
                nvl.on('nodeSelect', (event) => {
                    console.log('🎯 Node selected:', event);
                    // Could add selection-specific functionality here
                });

                console.log('✅ Custom event handlers added using NVL events');
            } else {
                console.log('🎮 NVL events not available, using container-based event handling...');
                this.addContainerEventHandlers(containerId, graphData);
            }

        } catch (error) {
            console.warn('⚠️ Could not add custom event handlers:', error);
            this.addContainerEventHandlers(containerId, graphData);
        }
    }

    /**
     * Add basic interactions as fallback
     * @param {Object} nvl - NVL graph instance
     * @param {string} containerId - Container ID
     * @param {Object} graphData - Graph data
     */
    addBasicInteractions(nvl, containerId, graphData) {
        console.log('🎮 Adding basic fallback interactions...');

        // Try to use NVL event handlers if available
        if (nvl && typeof nvl.on === 'function') {
            this.addCustomEventHandlers(nvl, containerId, graphData);
        } else {
            this.addContainerEventHandlers(containerId, graphData);
        }
    }

    /**
     * Add container-based event handlers as fallback
     * @param {string} containerId - Container ID
     * @param {Object} graphData - Graph data
     */
    addContainerEventHandlers(containerId, graphData) {
        const container = document.getElementById(containerId);
        if (!container) return;

        console.log('🎮 Adding container-based event handlers...');

        container.addEventListener('click', (event) => {
            const target = event.target;

            // Look for node elements
            if (target.tagName === 'circle' || target.tagName === 'text') {
                const nodeElement = target.closest('g[data-node-id]') || target.closest('g.node');
                if (nodeElement) {
                    const nodeId = nodeElement.getAttribute('data-node-id') || nodeElement.id;
                    const node = this.findNodeById(nodeId, graphData);
                    if (node) {
                        this.showNodeDetails(node, containerId);
                    }
                }
            }

            // Look for relationship elements
            if (target.tagName === 'path' || target.tagName === 'line') {
                const relElement = target.closest('g[data-relationship-id]') || target.closest('g.relationship');
                if (relElement) {
                    const relId = relElement.getAttribute('data-relationship-id') || relElement.id;
                    const relationship = this.findRelationshipById(relId, graphData);
                    if (relationship) {
                        this.showRelationshipDetails(relationship, containerId);
                    }
                }
            }
        });

        console.log('✅ Container-based event handlers added');
    }

    /**
     * Store interaction instances for potential cleanup
     * @param {string} containerId - Container ID
     * @param {Object} interactions - Interaction instances
     */
    storeInteractionInstances(containerId, interactions) {
        if (!this.interactionInstances) {
            this.interactionInstances = new Map();
        }
        this.interactionInstances.set(containerId, interactions);
        console.log('📦 Stored interaction instances for:', containerId);
    }

    /**
     * Find node by ID in graph data
     * @param {string} nodeId - Node ID
     * @param {Object} graphData - Graph data
     * @returns {Object|null} Node object
     */
    findNodeById(nodeId, graphData) {
        const nodes = graphData.nodes || [];
        return nodes.find(node => node.id === nodeId || node.elementId === nodeId) || null;
    }

    /**
     * Find relationship by ID in graph data
     * @param {string} relId - Relationship ID
     * @param {Object} graphData - Graph data
     * @returns {Object|null} Relationship object
     */
    findRelationshipById(relId, graphData) {
        const relationships = graphData.relationships || [];
        return relationships.find(rel => rel.id === relId || rel.elementId === relId) || null;
    }

    /**
     * Show detailed node information
     * @param {Object} node - Node data
     * @param {string} containerId - Container ID
     */
    showNodeDetails(node, containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;

        // Remove existing details
        const existingDetails = container.querySelector('.node-details-popup');
        if (existingDetails) {
            existingDetails.remove();
        }

        // Create details popup
        const detailsPopup = document.createElement('div');
        detailsPopup.className = 'node-details-popup';
        detailsPopup.innerHTML = `
            <div class="details-header">
                <h4><i class="fas fa-circle"></i> ${node.properties?.name || node.id || 'Unknown'}</h4>
                <button class="close-details" onclick="this.parentElement.parentElement.remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="details-content">
                <div class="detail-item">
                    <strong>Type:</strong> ${node.labels?.join(', ') || 'Unknown'}
                </div>
                ${node.properties?.company ? `
                    <div class="detail-item">
                        <strong>Company:</strong> ${node.properties.company}
                    </div>
                ` : ''}
                ${node.properties?.position ? `
                    <div class="detail-item">
                        <strong>Position:</strong> ${node.properties.position}
                    </div>
                ` : ''}
                ${node.properties?.summary ? `
                    <div class="detail-item">
                        <strong>Summary:</strong> ${node.properties.summary.substring(0, 200)}${node.properties.summary.length > 200 ? '...' : ''}
                    </div>
                ` : ''}
                <div class="detail-item">
                    <strong>ID:</strong> ${node.id}
                </div>
            </div>
        `;

        container.appendChild(detailsPopup);

        // Auto-remove after 10 seconds
        setTimeout(() => {
            if (detailsPopup.parentElement) {
                detailsPopup.remove();
            }
        }, 10000);
    }

    /**
     * Show detailed relationship information
     * @param {Object} relationship - Relationship data
     * @param {string} containerId - Container ID
     */
    showRelationshipDetails(relationship, containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;

        // Remove existing details
        const existingDetails = container.querySelector('.relationship-details-popup');
        if (existingDetails) {
            existingDetails.remove();
        }

        // Create details popup
        const detailsPopup = document.createElement('div');
        detailsPopup.className = 'relationship-details-popup';
        detailsPopup.innerHTML = `
            <div class="details-header">
                <h4><i class="fas fa-arrow-right"></i> ${relationship.type || 'RELATED_TO'}</h4>
                <button class="close-details" onclick="this.parentElement.parentElement.remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="details-content">
                <div class="detail-item">
                    <strong>Type:</strong> ${relationship.type || 'RELATED_TO'}
                </div>
                ${relationship.properties?.detail ? `
                    <div class="detail-item">
                        <strong>Detail:</strong> ${relationship.properties.detail}
                    </div>
                ` : ''}
                ${relationship.properties?.extraction_method ? `
                    <div class="detail-item">
                        <strong>Source:</strong> ${relationship.properties.extraction_method}
                    </div>
                ` : ''}
                <div class="detail-item">
                    <strong>ID:</strong> ${relationship.id}
                </div>
            </div>
        `;

        container.appendChild(detailsPopup);

        // Auto-remove after 8 seconds
        setTimeout(() => {
            if (detailsPopup.parentElement) {
                detailsPopup.remove();
            }
        }, 8000);
    }

    /**
     * Show node tooltip on hover
     * @param {Object} node - Node data
     * @param {Object} position - Mouse position
     * @param {string} containerId - Container ID
     */
    showNodeTooltip(node, position, containerId) {
        // Simple tooltip implementation
        const container = document.getElementById(containerId);
        if (!container) return;

        // Remove existing tooltip
        const existingTooltip = container.querySelector('.graph-tooltip');
        if (existingTooltip) {
            existingTooltip.remove();
        }

        // Create tooltip
        const tooltip = document.createElement('div');
        tooltip.className = 'graph-tooltip';
        tooltip.innerHTML = `
            <strong>${node.properties?.name || node.id || 'Unknown'}</strong><br>
            Type: ${node.labels?.join(', ') || 'Unknown'}
            ${node.properties?.company ? `<br>Company: ${node.properties.company}` : ''}
        `;

        container.appendChild(tooltip);

        // Auto-remove after 3 seconds
        setTimeout(() => {
            if (tooltip.parentElement) {
                tooltip.remove();
            }
        }, 3000);
    }

    /**
     * Show relationship tooltip on hover
     * @param {Object} relationship - Relationship data
     * @param {Object} position - Mouse position
     * @param {string} containerId - Container ID
     */
    showRelationshipTooltip(relationship, position, containerId) {
        // Simple tooltip implementation
        const container = document.getElementById(containerId);
        if (!container) return;

        // Remove existing tooltip
        const existingTooltip = container.querySelector('.graph-tooltip');
        if (existingTooltip) {
            existingTooltip.remove();
        }

        // Create tooltip
        const tooltip = document.createElement('div');
        tooltip.className = 'graph-tooltip';
        tooltip.innerHTML = `
            <strong>${relationship.type || 'RELATED_TO'}</strong>
            ${relationship.properties?.detail ? `<br>${relationship.properties.detail}` : ''}
        `;

        container.appendChild(tooltip);

        // Auto-remove after 3 seconds
        setTimeout(() => {
            if (tooltip.parentElement) {
                tooltip.remove();
            }
        }, 3000);
    }

    /**
     * Validate and format graph data for NVL
     * @param {Object} graphData - Raw graph data
     * @returns {Object} Validated graph data
     */
    validateGraphData(graphData) {
        const nodes = [];
        const relationships = [];
        const nodeIdMap = new Map(); // Track node IDs for validation

        console.log('🔍 Raw graph data:', graphData);

        // Process nodes
        if (graphData.nodes && Array.isArray(graphData.nodes)) {
            graphData.nodes.forEach((node, index) => {
                if (node && (node.id || node.uuid)) {
                    const nodeId = node.id || node.uuid || `node-${index}`;
                    const processedNode = {
                        id: nodeId,
                        properties: {
                            name: node.name || node.properties?.name || `Node ${index + 1}`,
                            type: node.type || node.labels?.[0] || 'Unknown',
                            ...node.properties
                        },
                        labels: node.labels || [node.type || 'Entity']
                    };

                    nodes.push(processedNode);
                    nodeIdMap.set(nodeId, processedNode);
                    console.log(`✅ Added node: ${nodeId}`, processedNode);
                }
            });
        }

        // Process relationships - validate that referenced nodes exist
        if (graphData.relationships && Array.isArray(graphData.relationships)) {
            console.log(`🔍 Processing ${graphData.relationships.length} relationships`);

            graphData.relationships.forEach((rel, index) => {
                console.log(`🔍 Relationship ${index}:`, rel);

                // Check for relationship node references (multiple possible property names)
                const startNodeId = rel.startNode || rel.startNodeId || rel.source;
                const endNodeId = rel.endNode || rel.endNodeId || rel.target;

                console.log(`🔍 Extracted IDs: startNode='${startNodeId}', endNode='${endNodeId}'`);
                console.log(`🔍 Available node IDs:`, Array.from(nodeIdMap.keys()));

                // Validate that we have both node IDs
                if (startNodeId && endNodeId) {
                    // Check if both nodes exist
                    if (nodeIdMap.has(startNodeId) && nodeIdMap.has(endNodeId)) {
                        const processedRel = {
                            id: rel.id || `rel-${index}`,
                            startNode: startNodeId,      // Use startNode for consistency
                            endNode: endNodeId,          // Use endNode for consistency
                            startNodeId: startNodeId,    // Keep for backward compatibility
                            endNodeId: endNodeId,        // Keep for backward compatibility
                            type: rel.type || 'RELATES_TO',
                            properties: rel.properties || {}
                        };

                        relationships.push(processedRel);
                        console.log(`✅ Added relationship: ${startNodeId} -> ${endNodeId}`, processedRel);
                    } else {
                        console.warn(`⚠️ Skipping relationship - missing nodes: ${startNodeId} (exists: ${nodeIdMap.has(startNodeId)}) -> ${endNodeId} (exists: ${nodeIdMap.has(endNodeId)})`);
                    }
                } else {
                    console.warn(`⚠️ Skipping relationship - missing node IDs: startNode='${startNodeId}', endNode='${endNodeId}'`, rel);
                }
            });
        } else {
            console.warn('⚠️ No relationships array found in graph data');
        }

        console.log(`📊 Validated graph data: ${nodes.length} nodes, ${relationships.length} relationships`);
        console.log('📊 Final nodes:', nodes);
        console.log('📊 Final relationships:', relationships);

        return { nodes, relationships };
    }

    createSimpleGraphVisualization(containerId, graphData) {
        const container = document.getElementById(containerId);
        if (!container) return;

        console.log('🎨 Creating simple graph visualization...');

        // Clear container
        container.innerHTML = '';

        // Create simple graph display
        const simpleGraph = document.createElement('div');
        simpleGraph.className = 'simple-graph-visualization';
        simpleGraph.style.cssText = `
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 8px;
            color: white;
            text-align: center;
            min-height: 200px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
        `;

        // Add title
        const title = document.createElement('h3');
        title.textContent = '📊 Knowledge Graph Summary';
        title.style.cssText = 'margin: 0 0 20px 0; font-size: 1.2em;';
        simpleGraph.appendChild(title);

        // Add statistics
        const stats = document.createElement('div');
        stats.style.cssText = 'margin-bottom: 20px; font-size: 1.1em;';
        stats.innerHTML = `
            <div style="margin-bottom: 10px;">
                <strong>${graphData.nodes.length}</strong> entities found
            </div>
            <div>
                <strong>${graphData.relationships.length}</strong> relationships discovered
            </div>
        `;
        simpleGraph.appendChild(stats);

        // Add node list
        if (graphData.nodes.length > 0) {
            const nodeList = document.createElement('div');
            nodeList.style.cssText = 'margin-top: 20px; text-align: left; max-width: 400px;';

            const nodeTitle = document.createElement('h4');
            nodeTitle.textContent = '🏷️ Entities:';
            nodeTitle.style.cssText = 'margin: 0 0 10px 0; text-align: center;';
            nodeList.appendChild(nodeTitle);

            graphData.nodes.forEach(node => {
                const nodeItem = document.createElement('div');
                nodeItem.style.cssText = `
                    background: rgba(255, 255, 255, 0.2);
                    padding: 8px 12px;
                    margin: 5px 0;
                    border-radius: 4px;
                    border-left: 4px solid #fff;
                `;
                nodeItem.innerHTML = `
                    <strong>${node.properties.name}</strong>
                    <br><small>${node.properties.type || 'Entity'}</small>
                `;
                nodeList.appendChild(nodeItem);
            });

            simpleGraph.appendChild(nodeList);
        }

        container.appendChild(simpleGraph);
        console.log('✅ Simple graph visualization created successfully');
    }

    /**
     * Wait for NVL library to be available
     */
    async waitForNVL(maxWait = 5000) {
        const startTime = Date.now();
        while (typeof window.NVL === 'undefined' && (Date.now() - startTime) < maxWait) {
            await new Promise(resolve => setTimeout(resolve, 100));
        }
        if (typeof window.NVL === 'undefined') {
            throw new Error('NVL library not available after waiting');
        }
    }

    /**
     * Show error message in graph container
     */
    showGraphError(container, message) {
        if (container) {
            container.innerHTML = `
                <div class="graph-error">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>Failed to load graph visualization</p>
                    <small>${message}</small>
                </div>
            `;
        }
    }

    /**
     * Show empty graph message
     */
    showEmptyGraphMessage(container) {
        if (container) {
            container.innerHTML = `
                <div class="graph-empty">
                    <i class="fas fa-project-diagram"></i>
                    <p>No graph data available</p>
                </div>
            `;
        }
    }

    /**
     * Fit graph to view
     */
    fitGraph(containerId) {
        const nvl = this.graphInstances.get(containerId);
        if (nvl && typeof nvl.fit === 'function') {
            nvl.fit();
            console.log('🎯 Graph fitted to view:', containerId);
        }
    }

    /**
     * Reset graph zoom
     */
    resetZoom(containerId) {
        const nvl = this.graphInstances.get(containerId);
        if (nvl && typeof nvl.resetZoom === 'function') {
            nvl.resetZoom();
            console.log('🎯 Graph zoom reset:', containerId);
        }
    }

    /**
     * Show chat graph details modal with Neo4j query parameters
     */
    showChatGraphDetails(messageId) {
        console.log('🔍 Opening chat graph details for:', messageId);

        // Get the graph data for this message
        const graphData = this.getGraphDataForMessage(messageId);

        // Create and show the chat graph details modal
        this.createChatGraphDetailsModal(messageId, graphData);
    }

    /**
     * Get graph data for a specific message
     */
    getGraphDataForMessage(messageId) {
        // Try to find the graph data from the message element
        const messageElement = document.querySelector(`[data-message-id="${messageId}"]`);
        if (messageElement) {
            const graphContainer = messageElement.querySelector('.chat-graph-container');
            if (graphContainer && graphContainer.graphData) {
                return graphContainer.graphData;
            }
        }
        return null;
    }

    /**
     * Create and show chat graph details modal
     */
    createChatGraphDetailsModal(messageId, graphData) {
        // Remove existing modal if present
        const existingModal = document.getElementById('chat-graph-details-modal');
        if (existingModal) {
            existingModal.remove();
        }

        // Create modal HTML
        const modal = document.createElement('div');
        modal.id = 'chat-graph-details-modal';
        modal.className = 'modal';
        modal.style.display = 'block';

        const nodeCount = graphData?.nodes?.length || 0;
        const relCount = graphData?.relationships?.length || 0;

        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3><i class="fas fa-database"></i> Entity Query Builder - Auto-Generated from Chat Answer</h3>
                    <span class="close" onclick="this.parentElement.parentElement.parentElement.remove()">&times;</span>
                </div>
                <div class="modal-body">
                    <div class="graph-summary">
                        <h4>Current Graph Summary</h4>
                        <div class="summary-stats">
                            <div class="stat-item">
                                <i class="fas fa-circle"></i>
                                <span><strong>${nodeCount}</strong> Nodes</span>
                            </div>
                            <div class="stat-item">
                                <i class="fas fa-arrow-right"></i>
                                <span><strong>${relCount}</strong> Relationships</span>
                            </div>
                        </div>
                    </div>

                    <div class="entities-from-answer">
                        <h4><i class="fas fa-tags"></i> Entities from Chat Answer (${graphData.nodes?.length || 0} total)</h4>
                        <div class="entity-list">
                            ${this.generateEntityButtons(graphData)}
                        </div>
                        <small>Click an entity button to auto-fill the query form</small>
                    </div>

                    <div class="suggested-queries">
                        <h4><i class="fas fa-lightbulb"></i> Suggested Queries</h4>
                        <div class="query-suggestions">
                            ${this.generateSuggestedQueries(graphData)}
                        </div>
                        <small>Click a suggested query to auto-fill the form</small>
                    </div>

                    <div class="query-section">
                        <h4><i class="fas fa-database"></i> Custom Neo4j Query</h4>
                        <form id="chat-graph-query-form">
                            <div class="form-group">
                                <label for="chat-detail-entity">Entity Name:</label>
                                <input type="text" id="chat-detail-entity" placeholder="Enter entity name or click entity button above">
                            </div>
                            <div class="form-row">
                                <div class="form-group">
                                    <label for="chat-detail-limit">Limit:</label>
                                    <input type="number" id="chat-detail-limit" value="50" min="10" max="200">
                                </div>
                                <div class="form-group">
                                    <label for="chat-detail-depth">Depth:</label>
                                    <input type="number" id="chat-detail-depth" value="2" min="1" max="5">
                                </div>
                            </div>
                            <div class="form-group">
                                <label for="chat-detail-query">Custom Cypher Query:</label>
                                <textarea id="chat-detail-query" placeholder="Enter custom Cypher query (optional)" rows="4"></textarea>
                                <small>Leave empty to use standard entity-based query</small>
                            </div>
                            <div class="form-actions">
                                <button type="submit" class="action-btn">
                                    <i class="fas fa-search"></i> Execute Query
                                </button>
                                <button type="button" class="action-btn secondary" onclick="this.parentElement.parentElement.parentElement.parentElement.parentElement.remove()">
                                    <i class="fas fa-times"></i> Cancel
                                </button>
                            </div>
                        </form>
                    </div>

                    <div id="chat-detail-results" class="detail-results" style="display: none;">
                        <h4>Query Results:</h4>
                        <div id="chat-detail-graph-container" class="detail-graph-container"></div>
                        <div id="chat-detail-stats" class="detail-stats"></div>
                    </div>
                </div>
            </div>
        `;

        // Add to document
        document.body.appendChild(modal);

        // Set up form submission
        const form = document.getElementById('chat-graph-query-form');
        form.onsubmit = async (e) => {
            e.preventDefault();
            await this.executeChatGraphQuery();
        };

        // Auto-populate with first entity if available
        this.autoPopulateFirstEntity(graphData);

        console.log('✅ Chat graph details modal created');
    }

    /**
     * Auto-populate the form with the first entity from the graph
     * @param {Object} graphData - Graph data with nodes and relationships
     */
    autoPopulateFirstEntity(graphData) {
        if (!graphData || !graphData.nodes || graphData.nodes.length === 0) {
            return;
        }

        // Find the first entity with a name
        const firstEntity = graphData.nodes.find(node => node.properties?.name);
        if (firstEntity) {
            const entityName = firstEntity.properties.name;
            const entityType = firstEntity.labels?.[0] || 'Entity';

            // Populate the entity input field
            const entityInput = document.getElementById('chat-detail-entity');
            if (entityInput) {
                entityInput.value = entityName;
                entityInput.placeholder = `Auto-filled: ${entityName}`;
            }

            // Generate a default query for this entity
            const defaultQuery = `MATCH (n)-[r]-(connected) WHERE n.name CONTAINS '${entityName}' RETURN n, r, connected LIMIT 20`;
            const queryInput = document.getElementById('chat-detail-query');
            if (queryInput) {
                queryInput.placeholder = `Auto-generated query for ${entityName}`;
            }

            console.log(`✅ Auto-populated form with entity: ${entityName} (${entityType})`);
        }
    }

    /**
     * Generate entity buttons from graph data
     * @param {Object} graphData - Graph data with nodes and relationships
     * @returns {string} HTML for entity buttons
     */
    generateEntityButtons(graphData) {
        if (!graphData || !graphData.nodes || graphData.nodes.length === 0) {
            return '<p class="no-entities">No entities found in this graph</p>';
        }

        const entities = [];
        const seenNames = new Set();

        // Extract unique entity names from nodes
        graphData.nodes.forEach(node => {
            const name = node.properties?.name || node.id;
            if (name && !seenNames.has(name)) {
                seenNames.add(name);
                entities.push({
                    name: name,
                    type: node.labels?.[0] || 'Entity',
                    labels: node.labels || []
                });
            }
        });

        // Sort entities by type and name
        entities.sort((a, b) => {
            if (a.type !== b.type) {
                return a.type.localeCompare(b.type);
            }
            return a.name.localeCompare(b.name);
        });

        // Generate buttons HTML
        const buttonsHtml = entities.map(entity => {
            const typeClass = entity.type.toLowerCase().replace(/\s+/g, '-');
            const typeIcon = this.getEntityTypeIcon(entity.type);

            return `
                <button class="entity-btn entity-${typeClass}"
                        onclick="chatGraphViz.selectEntity('${entity.name.replace(/'/g, "\\'")}', '${entity.type}')"
                        title="${entity.labels.join(', ')}">
                    <i class="${typeIcon}"></i>
                    <span class="entity-name">${entity.name}</span>
                    <span class="entity-type">${entity.type}</span>
                </button>
            `;
        }).join('');

        return buttonsHtml || '<p class="no-entities">No named entities found</p>';
    }

    /**
     * Get icon for entity type
     * @param {string} type - Entity type
     * @returns {string} Font Awesome icon class
     */
    getEntityTypeIcon(type) {
        const typeMap = {
            'person': 'fas fa-user',
            'company': 'fas fa-building',
            'organization': 'fas fa-sitemap',
            'entity': 'fas fa-circle',
            'location': 'fas fa-map-marker-alt',
            'event': 'fas fa-calendar',
            'technology': 'fas fa-microchip',
            'product': 'fas fa-box'
        };

        return typeMap[type.toLowerCase()] || 'fas fa-tag';
    }

    /**
     * Generate suggested queries based on graph data
     * @param {Object} graphData - Graph data with nodes and relationships
     * @returns {string} HTML for suggested queries
     */
    generateSuggestedQueries(graphData) {
        if (!graphData || !graphData.nodes || graphData.nodes.length === 0) {
            return '<p class="no-suggestions">No entities available for query suggestions</p>';
        }

        const suggestions = [];
        const entities = [];
        const seenNames = new Set();

        // Extract unique entities
        graphData.nodes.forEach(node => {
            const name = node.properties?.name || node.id;
            if (name && !seenNames.has(name)) {
                seenNames.add(name);
                entities.push({
                    name: name,
                    type: node.labels?.[0] || 'Entity',
                    labels: node.labels || []
                });
            }
        });

        // Generate different types of suggested queries
        entities.slice(0, 3).forEach(entity => {
            // 1. Entity relationships query
            suggestions.push({
                title: `${entity.name} Relationships`,
                description: `Find all relationships for ${entity.name}`,
                query: `MATCH (n)-[r]-(connected) WHERE n.name CONTAINS '${entity.name}' RETURN n, r, connected LIMIT 20`,
                type: 'relationships',
                entity: entity.name
            });

            // 2. Entity details query
            suggestions.push({
                title: `${entity.name} Details`,
                description: `Get detailed information about ${entity.name}`,
                query: `MATCH (n) WHERE n.name CONTAINS '${entity.name}' RETURN n, labels(n) as labels, properties(n) as props LIMIT 10`,
                type: 'details',
                entity: entity.name
            });
        });

        // 3. If we have multiple entities, suggest relationship queries between them
        if (entities.length >= 2) {
            const entity1 = entities[0];
            const entity2 = entities[1];
            suggestions.push({
                title: `${entity1.name} ↔ ${entity2.name}`,
                description: `Find connections between ${entity1.name} and ${entity2.name}`,
                query: `MATCH path = (a)-[*1..3]-(b) WHERE a.name CONTAINS '${entity1.name}' AND b.name CONTAINS '${entity2.name}' RETURN path LIMIT 10`,
                type: 'connection',
                entity: `${entity1.name}, ${entity2.name}`
            });
        }

        // 4. General network query
        if (entities.length > 0) {
            suggestions.push({
                title: 'Network Overview',
                description: 'Show the broader network around these entities',
                query: `MATCH (n)-[r]-(connected) WHERE n.name IN [${entities.slice(0, 3).map(e => `'${e.name}'`).join(', ')}] RETURN n, r, connected LIMIT 30`,
                type: 'network',
                entity: 'Multiple entities'
            });
        }

        // Generate HTML for suggestions
        const suggestionsHtml = suggestions.slice(0, 6).map(suggestion => {
            const typeClass = suggestion.type.toLowerCase();
            const typeIcon = this.getSuggestionTypeIcon(suggestion.type);

            return `
                <div class="query-suggestion ${typeClass}"
                     onclick="chatGraphViz.applySuggestedQuery('${suggestion.query.replace(/'/g, "\\'")}', '${suggestion.entity.replace(/'/g, "\\'")}')">
                    <div class="suggestion-header">
                        <i class="${typeIcon}"></i>
                        <span class="suggestion-title">${suggestion.title}</span>
                    </div>
                    <div class="suggestion-description">${suggestion.description}</div>
                    <div class="suggestion-preview">
                        <code>${suggestion.query.length > 80 ? suggestion.query.substring(0, 80) + '...' : suggestion.query}</code>
                    </div>
                </div>
            `;
        }).join('');

        return suggestionsHtml || '<p class="no-suggestions">No query suggestions available</p>';
    }

    /**
     * Get icon for suggestion type
     * @param {string} type - Suggestion type
     * @returns {string} Font Awesome icon class
     */
    getSuggestionTypeIcon(type) {
        const typeMap = {
            'relationships': 'fas fa-project-diagram',
            'details': 'fas fa-info-circle',
            'connection': 'fas fa-link',
            'network': 'fas fa-sitemap'
        };
        return typeMap[type.toLowerCase()] || 'fas fa-search';
    }

    /**
     * Apply a suggested query to the form
     * @param {string} query - The Cypher query
     * @param {string} entity - The entity name
     */
    applySuggestedQuery(query, entity) {
        console.log('🎯 Applying suggested query:', query);

        // Populate the query textarea
        const queryInput = document.getElementById('chat-detail-query');
        if (queryInput) {
            queryInput.value = query;
        }

        // Populate the entity input if it's a single entity
        const entityInput = document.getElementById('chat-detail-entity');
        if (entityInput && !entity.includes(',')) {
            entityInput.value = entity;
        }

        // Highlight the selected suggestion
        document.querySelectorAll('.query-suggestion').forEach(suggestion => {
            suggestion.classList.remove('selected');
        });
        event.target.closest('.query-suggestion').classList.add('selected');

        console.log('✅ Suggested query applied');
    }

    /**
     * Select an entity and populate the query form
     * @param {string} entityName - Name of the entity
     * @param {string} entityType - Type of the entity
     */
    selectEntity(entityName, entityType) {
        console.log('🎯 Selected entity:', entityName, 'Type:', entityType);

        // Populate the entity input field
        const entityInput = document.getElementById('chat-detail-entity');
        if (entityInput) {
            entityInput.value = entityName;
            entityInput.focus();
        }

        // Highlight the selected button
        document.querySelectorAll('.entity-btn').forEach(btn => {
            btn.classList.remove('selected');
        });

        event.target.closest('.entity-btn').classList.add('selected');

        console.log('✅ Entity selected and form populated');
    }

    /**
     * Execute custom query from chat graph details modal
     */
    async executeChatGraphQuery() {
        const entity = document.getElementById('chat-detail-entity').value.trim();
        const limit = parseInt(document.getElementById('chat-detail-limit').value) || 50;
        const depth = parseInt(document.getElementById('chat-detail-depth').value) || 2;
        const customQuery = document.getElementById('chat-detail-query').value.trim();

        const resultsDiv = document.getElementById('chat-detail-results');
        const graphContainer = document.getElementById('chat-detail-graph-container');
        const statsDiv = document.getElementById('chat-detail-stats');

        try {
            resultsDiv.style.display = 'block';
            graphContainer.innerHTML = '<div style="display: flex; align-items: center; justify-content: center; height: 100%; color: #666;"><i class="fas fa-spinner fa-spin" style="margin-right: 10px;"></i>Loading...</div>';

            let graphData;

            if (customQuery) {
                // Execute custom Cypher query
                const response = await fetch('/api/graph/neo4j/custom', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        query: customQuery,
                        limit: limit
                    })
                });

                if (!response.ok) {
                    const errorText = await response.text();
                    console.error('Server error response:', errorText);
                    throw new Error(`HTTP ${response.status}: ${response.statusText} - ${errorText}`);
                }

                graphData = await response.json();
            } else {
                // Use standard visualization endpoint
                const params = new URLSearchParams({
                    limit: limit.toString()
                });

                if (entity) {
                    params.append('entity', entity);
                }

                const response = await fetch(`/api/graph/neo4j/visualize?${params}`);

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }

                graphData = await response.json();
            }

            // Display stats
            statsDiv.innerHTML = `
                <div><strong>Nodes:</strong> ${graphData.nodes?.length || 0}</div>
                <div><strong>Relationships:</strong> ${graphData.relationships?.length || 0}</div>
                <div><strong>Query Time:</strong> ${graphData.query_time || 'N/A'}</div>
            `;

            // Render graph in the detail container
            this.renderChatDetailGraph(graphContainer, graphData);

        } catch (error) {
            console.error('Chat graph query failed:', error);
            graphContainer.innerHTML = `
                <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; color: #d32f2f;">
                    <i class="fas fa-exclamation-triangle" style="font-size: 2rem; margin-bottom: 10px;"></i>
                    <p>Query failed: ${error.message}</p>
                </div>
            `;
        }
    }

    /**
     * Render graph in chat detail modal
     */
    renderChatDetailGraph(container, graphData) {
        if (!graphData.nodes || graphData.nodes.length === 0) {
            container.innerHTML = `
                <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; color: #666;">
                    <i class="fas fa-project-diagram" style="font-size: 2rem; margin-bottom: 10px;"></i>
                    <p>No graph data to display</p>
                </div>
            `;
            return;
        }

        // Clear container
        container.innerHTML = '';

        // Create a unique container ID for this detail graph
        const detailGraphId = 'chat-detail-graph-' + Date.now();
        container.innerHTML = `<div id="${detailGraphId}" style="width: 100%; height: 100%;"></div>`;

        try {
            // Use the same NVL rendering logic as the main graph
            const detailContainer = document.getElementById(detailGraphId);

            // Format data for NVL
            const nodes = graphData.nodes.map(node => ({
                id: node.id,
                labels: node.labels || [],
                properties: node.properties || {},
                selected: false,
                hovered: false
            }));

            const relationships = graphData.relationships.map(rel => ({
                id: rel.id,
                startNodeId: rel.startNodeId,
                endNodeId: rel.endNodeId,
                type: rel.type,
                properties: rel.properties || {},
                selected: false,
                hovered: false
            }));

            // Create NVL instance for detail view
            if (typeof NVL !== 'undefined') {
                const detailNvl = new NVL(detailContainer, nodes, relationships, {
                    layout: 'forceDirected',
                    initialZoom: 0.8,
                    styling: {
                        nodeDefaultBorderColor: '#ffffff',
                        selectedBorderColor: '#4CAF50'
                    }
                });

                console.log('✅ Chat detail graph rendered successfully');
            } else {
                // Fallback to simple visualization
                this.createSimpleGraphVisualization(detailGraphId, graphData);
            }

        } catch (error) {
            console.error('Failed to render chat detail graph:', error);
            container.innerHTML = `
                <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; color: #d32f2f;">
                    <i class="fas fa-exclamation-triangle" style="font-size: 2rem; margin-bottom: 10px;"></i>
                    <p>Failed to render graph: ${error.message}</p>
                </div>
            `;
        }
    }

    /**
     * Clean up graph instance
     */
    destroyGraph(containerId) {
        const nvl = this.graphInstances.get(containerId);
        if (nvl && typeof nvl.destroy === 'function') {
            nvl.destroy();
            this.graphInstances.delete(containerId);
            console.log('🎯 Graph destroyed:', containerId);
        }
    }
}

// Create global instance
window.chatGraphViz = new ChatGraphVisualization();

console.log('✅ Chat Graph Visualization component loaded');

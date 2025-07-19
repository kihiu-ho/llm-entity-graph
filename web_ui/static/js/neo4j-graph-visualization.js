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
            try {
                // NVL doesn't have clearGraph, use restart instead
                if (typeof this.nvl.restart === 'function') {
                    this.nvl.restart();
                    console.log('✅ NVL graph cleared using restart()');
                } else if (typeof this.nvl.clear === 'function') {
                    this.nvl.clear();
                    console.log('✅ NVL graph cleared using clear()');
                } else {
                    console.log('ℹ️ No clear method available, graph will remain');
                }
            } catch (error) {
                console.warn('⚠️ Failed to clear NVL graph:', error);
            }
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
                // Enable interactions including dragging
                interactions: {
                    nodeClick: true,
                    nodeDrag: true,
                    nodeHover: true,
                    relationshipClick: true,
                    relationshipHover: true,
                    canvasClick: true,
                    canvasDrag: true,
                    zoom: true,
                    pan: true
                },
                // Layout configuration for better dragging
                layoutConfiguration: {
                    forceDirected: {
                        enableDragging: true,
                        nodeRepulsion: 1000,
                        linkDistance: 100,
                        linkStrength: 0.1,
                        gravity: 0.1,
                        theta: 0.8,
                        alpha: 0.1,
                        alphaDecay: 0.02,
                        velocityDecay: 0.4
                    }
                },
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

            // Set up NVL interaction modules
            this.setupNVLInteractions();

            console.log('✅ NVL initialized successfully');
        } catch (error) {
            console.error('❌ Failed to initialize NVL:', error);
            console.error('❌ Error stack:', error.stack);
            console.log('🔄 Creating fallback visualization...');
            this.createFallbackVisualization();
        }
    }

    setupNVLInteractions() {
        try {
            console.log('🎮 Setting up NVL interaction modules...');

            // Check if NVL has interaction modules
            const NVLClass = window.NVL || window.Neo4jNVL;
            if (!NVLClass) {
                console.log('⚠️ NVL class not found, using fallback interactions');
                this.setupFallbackInteractions();
                return;
            }

            console.log('🔍 Checking for interaction modules...');
            console.log('  - NVLClass:', typeof NVLClass);
            console.log('  - NVLClass.ZoomInteraction:', typeof NVLClass.ZoomInteraction);
            console.log('  - NVLClass.PanInteraction:', typeof NVLClass.PanInteraction);
            console.log('  - NVLClass.DragNodeInteraction:', typeof NVLClass.DragNodeInteraction);
            console.log('  - NVLClass.ClickInteraction:', typeof NVLClass.ClickInteraction);
            console.log('  - NVLClass.HoverInteraction:', typeof NVLClass.HoverInteraction);
            console.log('  - NVLClass.LassoInteraction:', typeof NVLClass.LassoInteraction);

            // Check if interaction handlers are available in different locations
            console.log('🔍 Checking alternative interaction locations...');
            console.log('  - window.NVLInteractions:', typeof window.NVLInteractions);
            console.log('  - window.NVLInteractions.DragNodeInteraction:', typeof window.NVLInteractions?.DragNodeInteraction);
            console.log('  - window.Neo4jNVL.DragNodeInteraction:', typeof window.Neo4jNVL?.DragNodeInteraction);
            console.log('  - window.NVL.DragNodeInteraction:', typeof window.NVL?.DragNodeInteraction);

            // Set up interactions using proper NVL API
            this.interactions = [];

            // Try to get interaction handlers from different locations
            const InteractionHandlers = window.NVLInteractions || NVLClass || {};

            // 1. Set up zoom interaction
            const ZoomInteraction = InteractionHandlers.ZoomInteraction || NVLClass.ZoomInteraction || window.NVL?.ZoomInteraction;
            if (ZoomInteraction) {
                try {
                    const zoomInteraction = new ZoomInteraction(this.nvl);
                    zoomInteraction.updateCallback('onZoom', (zoomLevel) => {
                        console.log('🔍 Zoom level:', zoomLevel);
                        this.onZoom(zoomLevel);
                    });
                    this.interactions.push(zoomInteraction);
                    console.log('✅ Zoom interaction enabled');
                } catch (error) {
                    console.warn('⚠️ Failed to setup zoom interaction:', error);
                }
            }

            // 2. Set up pan interaction
            const PanInteraction = InteractionHandlers.PanInteraction || NVLClass.PanInteraction || window.NVL?.PanInteraction;
            if (PanInteraction) {
                try {
                    const panInteraction = new PanInteraction(this.nvl);
                    panInteraction.updateCallback('onPan', (panning) => {
                        console.log('🖱️ Panning:', panning);
                        this.onPan(panning);
                    });
                    this.interactions.push(panInteraction);
                    console.log('✅ Pan interaction enabled');
                } catch (error) {
                    console.warn('⚠️ Failed to setup pan interaction:', error);
                }
            }

            // 3. Set up drag node interaction
            const DragNodeInteraction = InteractionHandlers.DragNodeInteraction || NVLClass.DragNodeInteraction || window.NVL?.DragNodeInteraction;
            if (DragNodeInteraction) {
                try {
                    const dragInteraction = new DragNodeInteraction(this.nvl);
                    dragInteraction.updateCallback('onDrag', (nodes) => {
                        console.log('🎯 Dragged nodes:', nodes);
                        this.onDragNodes(nodes);
                    });
                    dragInteraction.updateCallback('onDragStart', (nodes) => {
                        console.log('🎯 Started dragging nodes:', nodes);
                        this.onDragStart(nodes);
                    });
                    dragInteraction.updateCallback('onDragEnd', (nodes) => {
                        console.log('🎯 Finished dragging nodes:', nodes);
                        this.onDragEnd(nodes);
                    });
                    this.interactions.push(dragInteraction);
                    console.log('✅ Drag node interaction enabled');
                } catch (error) {
                    console.warn('⚠️ Failed to setup drag interaction:', error);
                }
            }

            // 4. Set up click interaction
            const ClickInteraction = InteractionHandlers.ClickInteraction || NVLClass.ClickInteraction || window.NVL?.ClickInteraction;
            if (ClickInteraction) {
                try {
                    const clickInteraction = new ClickInteraction(this.nvl);
                    clickInteraction.updateCallback('onNodeClick', (node) => {
                        console.log('🔵 Node clicked:', node);
                        this.onNodeClick(node);
                    });
                    clickInteraction.updateCallback('onRelationshipClick', (relationship) => {
                        console.log('🔗 Relationship clicked:', relationship);
                        this.onRelationshipClick(relationship);
                    });
                    clickInteraction.updateCallback('onCanvasClick', (event) => {
                        console.log('🖱️ Canvas clicked:', event);
                        this.onCanvasClick(event);
                    });
                    clickInteraction.updateCallback('onNodeDoubleClick', (node) => {
                        console.log('🔵 Node double-clicked:', node);
                        this.onNodeDoubleClick(node);
                    });
                    clickInteraction.updateCallback('onRelationshipDoubleClick', (relationship) => {
                        console.log('🔗 Relationship double-clicked:', relationship);
                        this.onRelationshipDoubleClick(relationship);
                    });
                    this.interactions.push(clickInteraction);
                    console.log('✅ Click interaction enabled with custom handlers');
                } catch (error) {
                    console.warn('⚠️ Failed to setup click interaction:', error);
                }
            }

            // 5. Set up hover interaction
            const HoverInteraction = InteractionHandlers.HoverInteraction || NVLClass.HoverInteraction || window.NVL?.HoverInteraction;
            if (HoverInteraction) {
                try {
                    const hoverInteraction = new HoverInteraction(this.nvl);
                    hoverInteraction.updateCallback('onHover', (element, hitElements, event) => {
                        console.log('🎯 Hovered element:', element);
                        console.log('🎯 Hit elements:', hitElements);
                        this.onHover(element, hitElements, event);
                    });
                    this.interactions.push(hoverInteraction);
                    console.log('✅ Hover interaction enabled');
                } catch (error) {
                    console.warn('⚠️ Failed to setup hover interaction:', error);
                }
            }

            // 6. Set up lasso interaction
            const LassoInteraction = InteractionHandlers.LassoInteraction || NVLClass.LassoInteraction || window.NVL?.LassoInteraction;
            if (LassoInteraction) {
                try {
                    const lassoInteraction = new LassoInteraction(this.nvl);
                    lassoInteraction.updateCallback('onLassoSelect', ({ nodes, rels }) => {
                        console.log('🎯 Lasso selected elements:', nodes, rels);
                        this.onLassoSelect(nodes, rels);
                    });
                    this.interactions.push(lassoInteraction);
                    console.log('✅ Lasso interaction enabled');
                } catch (error) {
                    console.warn('⚠️ Failed to setup lasso interaction:', error);
                }
            }

            console.log(`🎮 ${this.interactions.length} NVL interactions set up successfully`);

            // If no interactions were set up, use fallback
            if (this.interactions.length === 0) {
                console.log('⚠️ No NVL interactions available, using fallback...');
                this.setupFallbackInteractions();
            }

        } catch (error) {
            console.error('❌ Failed to setup NVL interactions:', error);
            console.log('🔄 Setting up fallback interactions...');
            this.setupFallbackInteractions();
        }
    }

    setupFallbackInteractions() {
        console.log('🎮 Setting up fallback interaction handlers...');

        const container = document.getElementById('graph-canvas');
        if (!container) {
            console.error('❌ Graph canvas container not found for interactions');
            return;
        }

        // Set up comprehensive event listeners for all interactions
        this.setupClickInteraction(container);
        this.setupHoverInteraction(container);
        // Note: NVL has built-in drag functionality enabled via nodeDrag: true
        // We don't need custom drag handlers as they interfere with NVL's native dragging
        console.log('🎯 NVL built-in drag functionality is enabled via nodeDrag: true');
        // this.setupDragInteraction(container); // Disabled to allow NVL native dragging
        this.setupZoomInteraction(container);

        console.log('✅ Fallback interactions set up successfully');
    }

    // Helper methods for enhanced drag functionality
    updateNodePositionInData(nodeId, deltaX, deltaY) {
        // Find the node in our current data and update its position
        if (this.currentGraphData && this.currentGraphData.nodes) {
            const node = this.currentGraphData.nodes.find(n => n.id === nodeId);
            if (node) {
                // Update node position if it has position data
                if (node.x !== undefined && node.y !== undefined) {
                    node.x += deltaX;
                    node.y += deltaY;
                    console.log(`🎯 Updated node ${nodeId} position to (${node.x}, ${node.y})`);

                    // Try to re-render with updated data
                    if (typeof this.nvl.updateElementsInGraph === 'function') {
                        this.nvl.updateElementsInGraph([node], []);
                        return true;
                    }
                } else {
                    console.log(`🎯 Node ${nodeId} has no position data to update`);
                }
            }
        }
        return false;
    }

    storeDragDelta(nodeId, deltaX, deltaY) {
        // Store drag deltas for potential future use or visual feedback
        if (!this.dragDeltas) {
            this.dragDeltas = new Map();
        }

        const currentDelta = this.dragDeltas.get(nodeId) || { x: 0, y: 0 };
        currentDelta.x += deltaX;
        currentDelta.y += deltaY;
        this.dragDeltas.set(nodeId, currentDelta);

        console.log(`🎯 Stored drag delta for ${nodeId}: (${currentDelta.x}, ${currentDelta.y})`);

        // Provide visual feedback that drag is being tracked
        this.showDragFeedback(nodeId, currentDelta);
    }

    showDragFeedback(nodeId, delta) {
        // Visual feedback for drag operations
        console.log(`🎯 Drag feedback: Node ${nodeId} moved by (${delta.x}, ${delta.y})`);

        // Could implement visual indicators here, such as:
        // - Highlighting the dragged node
        // - Showing drag trail
        // - Updating a status indicator
    }

    setupClickInteraction(container) {
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
    }

    setupHoverInteraction(container) {
        container.addEventListener('mousemove', (evt) => {
            try {
                if (this.nvl && typeof this.nvl.getHits === 'function') {
                    const hits = this.nvl.getHits(evt);
                    if (hits && hits.nvlTargets) {
                        const { nvlTargets } = hits;
                        if (nvlTargets.nodes && nvlTargets.nodes.length > 0) {
                            container.style.cursor = 'pointer';
                            this.onNodeHover(nvlTargets.nodes[0], evt);
                        } else if (nvlTargets.relationships && nvlTargets.relationships.length > 0) {
                            container.style.cursor = 'pointer';
                            this.onRelationshipHover(nvlTargets.relationships[0], evt);
                        } else {
                            container.style.cursor = 'default';
                        }
                    }
                }
            } catch (e) {
                // Silently handle hover errors to avoid spam
            }
        });
    }

    setupDragInteraction(container) {
        let isDragging = false;
        let dragStartPos = null;
        let draggedNode = null;

        // Log available NVL methods for debugging drag functionality
        if (this.nvl) {
            const nvlMethods = Object.getOwnPropertyNames(Object.getPrototypeOf(this.nvl));
            const dragRelatedMethods = nvlMethods.filter(method =>
                method.toLowerCase().includes('node') ||
                method.toLowerCase().includes('position') ||
                method.toLowerCase().includes('move') ||
                method.toLowerCase().includes('drag') ||
                method.toLowerCase().includes('layout')
            );
            console.log('🎯 Available drag-related NVL methods:', dragRelatedMethods);
        }

        container.addEventListener('mousedown', (evt) => {
            try {
                if (this.nvl && typeof this.nvl.getHits === 'function') {
                    const hits = this.nvl.getHits(evt);
                    console.log('🎯 Drag mousedown hits:', hits);

                    if (hits && hits.nvlTargets && hits.nvlTargets.nodes && hits.nvlTargets.nodes.length > 0) {
                        isDragging = true;
                        draggedNode = hits.nvlTargets.nodes[0];
                        dragStartPos = { x: evt.clientX, y: evt.clientY };
                        container.style.cursor = 'grabbing';
                        evt.preventDefault();

                        // Extract node data properly
                        const nodeData = draggedNode.data || draggedNode;
                        const nodeName = nodeData.properties?.name || nodeData.id || 'Unknown';
                        console.log(`🎯 Started dragging node: ${nodeName}`);
                    } else {
                        console.log('🎯 No nodes found for dragging');
                    }
                } else {
                    console.log('🎯 NVL getHits not available for drag');
                }
            } catch (e) {
                console.warn('⚠️ Drag start failed:', e);
            }
        });

        container.addEventListener('mousemove', (evt) => {
            if (isDragging && draggedNode && dragStartPos) {
                try {
                    const deltaX = evt.clientX - dragStartPos.x;
                    const deltaY = evt.clientY - dragStartPos.y;

                    // Update drag position
                    dragStartPos = { x: evt.clientX, y: evt.clientY };

                    // Extract node data properly
                    const nodeData = draggedNode.data || draggedNode;
                    const nodeId = nodeData.id;

                    console.log(`🎯 Dragging node ${nodeId} by (${deltaX}, ${deltaY})`);

                    // Try different NVL methods for updating node position
                    if (this.nvl) {
                        let positionUpdated = false;

                        // Method 1: Try direct position update methods
                        if (typeof this.nvl.updateNodePosition === 'function') {
                            this.nvl.updateNodePosition(nodeId, deltaX, deltaY);
                            positionUpdated = true;
                        } else if (typeof this.nvl.moveNode === 'function') {
                            this.nvl.moveNode(nodeId, deltaX, deltaY);
                            positionUpdated = true;
                        } else if (typeof this.nvl.setNodePosition === 'function') {
                            // Calculate absolute position if needed
                            this.nvl.setNodePosition(nodeId, evt.clientX, evt.clientY);
                            positionUpdated = true;
                        }

                        // Method 2: Try updating node data and re-rendering
                        if (!positionUpdated && typeof this.nvl.updateElementsInGraph === 'function') {
                            try {
                                // Update the node's position in our data and re-render
                                this.updateNodePositionInData(nodeId, deltaX, deltaY);
                                positionUpdated = true;
                            } catch (error) {
                                console.warn('⚠️ Failed to update node position via data update:', error);
                            }
                        }

                        // Method 3: Try force layout manipulation
                        if (!positionUpdated && typeof this.nvl.getLayout === 'function') {
                            try {
                                const layout = this.nvl.getLayout();
                                if (layout && typeof layout.setNodePosition === 'function') {
                                    layout.setNodePosition(nodeId, evt.clientX, evt.clientY);
                                    positionUpdated = true;
                                }
                            } catch (error) {
                                console.warn('⚠️ Failed to update node position via layout:', error);
                            }
                        }

                        if (!positionUpdated) {
                            // Store the drag delta for visual feedback even if we can't update position
                            this.storeDragDelta(nodeId, deltaX, deltaY);
                        }
                    }

                    evt.preventDefault();
                } catch (e) {
                    console.warn('⚠️ Drag move failed:', e);
                }
            }
        });

        container.addEventListener('mouseup', (evt) => {
            if (isDragging) {
                const nodeData = draggedNode?.data || draggedNode;
                const nodeName = nodeData?.properties?.name || nodeData?.id || 'Unknown';
                console.log(`🎯 Finished dragging node: ${nodeName}`);

                isDragging = false;
                draggedNode = null;
                dragStartPos = null;
                container.style.cursor = 'default';
            }
        });

        // Handle mouse leave to stop dragging
        container.addEventListener('mouseleave', (evt) => {
            if (isDragging) {
                console.log('🎯 Drag cancelled (mouse left container)');
                isDragging = false;
                draggedNode = null;
                dragStartPos = null;
                container.style.cursor = 'default';
            }
        });
    }

    setupZoomInteraction(container) {
        container.addEventListener('wheel', (evt) => {
            try {
                if (this.nvl && typeof this.nvl.zoom === 'function') {
                    const zoomDelta = evt.deltaY > 0 ? 0.9 : 1.1;
                    this.nvl.zoom(zoomDelta);
                    evt.preventDefault();
                    console.log('🔍 Zoom:', zoomDelta);
                } else if (this.nvl && typeof this.nvl.setZoom === 'function') {
                    // Alternative zoom method
                    const currentZoom = this.nvl.getZoom ? this.nvl.getZoom() : 1;
                    const zoomDelta = evt.deltaY > 0 ? 0.9 : 1.1;
                    this.nvl.setZoom(currentZoom * zoomDelta);
                    evt.preventDefault();
                }
            } catch (e) {
                console.warn('⚠️ Zoom failed:', e);
            }
        });
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

        // Add drag behavior
        const drag = d3.drag()
            .on('start', (event, d) => {
                if (!event.active) simulation.alphaTarget(0.3).restart();
                d.fx = d.x;
                d.fy = d.y;
            })
            .on('drag', (event, d) => {
                d.fx = event.x;
                d.fy = event.y;
            })
            .on('end', (event, d) => {
                if (!event.active) simulation.alphaTarget(0);
                d.fx = null;
                d.fy = null;
            });

        // Add nodes with drag behavior
        const node = svg.append('g')
            .selectAll('circle')
            .data(nodes)
            .enter().append('circle')
            .attr('r', 8)
            .attr('fill', '#1f77b4')
            .attr('stroke', '#fff')
            .attr('stroke-width', 2)
            .style('cursor', 'grab')
            .call(drag)
            .on('mouseover', function(event, d) {
                d3.select(this).style('cursor', 'grab');
            })
            .on('mousedown', function(event, d) {
                d3.select(this).style('cursor', 'grabbing');
            })
            .on('mouseup', function(event, d) {
                d3.select(this).style('cursor', 'grab');
            });

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

            // Add a small delay to ensure DOM is fully updated
            setTimeout(() => {
                this.renderWithNVL(processedData, container);
            }, 100);
        } catch (error) {
            console.error('❌ Failed to render graph:', error);
            this.createFallbackVisualization();
        }

        console.log('✅ Graph rendering completed successfully');
    }

    validateGraphData(nodes, relationships) {
        console.log('🔍 Validating graph data...');
        console.log(`📊 Input: ${nodes.length} nodes, ${relationships.length} relationships`);

        // Create a Set of all node IDs for fast lookup
        const nodeIds = new Set(nodes.map(n => n.id));
        console.log('📋 Available node IDs:', Array.from(nodeIds).slice(0, 5), '...');

        // Filter relationships to only include those where both nodes exist
        const validRelationships = [];
        const orphanedRelationships = [];

        relationships.forEach(rel => {
            const fromExists = nodeIds.has(rel.from);
            const toExists = nodeIds.has(rel.to);

            if (fromExists && toExists) {
                validRelationships.push(rel);
            } else {
                orphanedRelationships.push({
                    id: rel.id,
                    from: rel.from,
                    to: rel.to,
                    fromExists,
                    toExists,
                    type: rel.type
                });
            }
        });

        // Log validation results
        console.log(`✅ Valid relationships: ${validRelationships.length}`);
        if (orphanedRelationships.length > 0) {
            console.warn(`⚠️ Filtered ${orphanedRelationships.length} orphaned relationships:`);
            orphanedRelationships.slice(0, 5).forEach(rel => {
                console.warn(`  - ${rel.type}: ${rel.from} -> ${rel.to} (from exists: ${rel.fromExists}, to exists: ${rel.toExists})`);
            });
            if (orphanedRelationships.length > 5) {
                console.warn(`  ... and ${orphanedRelationships.length - 5} more`);
            }
        }

        return {
            nodes,
            relationships: validRelationships,
            stats: {
                originalNodes: nodes.length,
                originalRelationships: relationships.length,
                validRelationships: validRelationships.length,
                orphanedRelationships: orphanedRelationships.length
            }
        };
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
                        // Validate and clean the graph data first
                        const validatedData = this.validateGraphData(processedData.nodes, processedData.relationships);
                        console.log('📊 Data validation completed:', validatedData.stats);

                        console.log('📡 Calling nvl.addAndUpdateElementsInGraph with:', {
                            nodes: validatedData.nodes.length,
                            relationships: validatedData.relationships.length,
                            containerDimensions: {
                                width: container.clientWidth,
                                height: container.clientHeight
                            }
                        });

                        // Log sample data to verify captions
                        if (validatedData.nodes.length > 0) {
                            console.log('📋 Sample node with caption:', {
                                id: validatedData.nodes[0].id,
                                caption: validatedData.nodes[0].caption,
                                color: validatedData.nodes[0].color,
                                size: validatedData.nodes[0].size
                            });
                        }
                        if (validatedData.relationships.length > 0) {
                            console.log('📋 Sample relationship with caption:', {
                                id: validatedData.relationships[0].id,
                                caption: validatedData.relationships[0].caption,
                                color: validatedData.relationships[0].color,
                                width: validatedData.relationships[0].width
                            });
                        }

                        this.nvl.addAndUpdateElementsInGraph(validatedData.nodes, validatedData.relationships);
                        console.log('✅ nvl.addAndUpdateElementsInGraph called successfully');
                        renderSuccess = true;

                        // Store current graph data for drag operations
                        this.currentGraphData = {
                            nodes: validatedData.nodes,
                            relationships: validatedData.relationships
                        };
                        console.log('📊 Stored current graph data for drag operations');

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
                        // Validate and clean the graph data first
                        const validatedData = this.validateGraphData(processedData.nodes, processedData.relationships);
                        console.log('📊 Data validation completed for addElementsToGraph:', validatedData.stats);

                        console.log('📡 Calling nvl.addElementsToGraph...');
                        this.nvl.addElementsToGraph(validatedData.nodes, validatedData.relationships);
                        console.log('✅ nvl.addElementsToGraph called successfully');
                        renderSuccess = true;

                        // Store current graph data for drag operations
                        this.currentGraphData = {
                            nodes: validatedData.nodes,
                            relationships: validatedData.relationships
                        };
                        console.log('📊 Stored current graph data for drag operations');
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

                // Get relationship type with fallbacks
                const relType = rel.type || rel.relationship_type || rel.name || 'RELATES_TO';
                const relColor = this.relationshipStyles[relType]?.color || '#999';

                // Find node names - handle different relationship data formats
                let fromNodeId, toNodeId, fromName, toName;

                // Handle Neo4j format (from/to) vs agent format (startNodeId/endNodeId)
                if (rel.from && rel.to) {
                    // Neo4j format
                    fromNodeId = rel.from;
                    toNodeId = rel.to;
                } else if (rel.startNodeId && rel.endNodeId) {
                    // Agent format
                    fromNodeId = rel.startNodeId;
                    toNodeId = rel.endNodeId;
                } else {
                    // Fallback: try to extract from properties or use relationship type
                    fromNodeId = rel.source || rel.source_entity || 'unknown';
                    toNodeId = rel.target || rel.target_entity || 'unknown';
                }

                // Find nodes by ID
                const fromNode = data.nodes.find(n => n.id === fromNodeId);
                const toNode = data.nodes.find(n => n.id === toNodeId);

                // Get names with multiple fallback options
                fromName = fromNode?.properties?.name || fromNode?.name || rel.source_entity || rel.source || fromNodeId;
                toName = toNode?.properties?.name || toNode?.name || rel.target_entity || rel.target || toNodeId;

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
                    <span style="color: ${relColor}; margin: 0 10px;">→ ${relType} →</span>
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
        console.log('🔵 Node clicked:', node);

        // Select the node if NVL supports it
        if (this.nvl && typeof this.nvl.selectNodes === 'function') {
            this.nvl.selectNodes([node.id]);
        }

        // Show node details in a tooltip or sidebar
        this.showNodeDetails(node);

        // Log detailed node information
        console.log('📋 Node details:', {
            id: node.id,
            labels: node.labels,
            properties: node.properties
        });
    }

    onRelationshipClick(relationship) {
        console.log('🔗 Relationship clicked:', relationship);

        // Select the relationship if NVL supports it
        if (this.nvl && typeof this.nvl.selectRelationships === 'function') {
            this.nvl.selectRelationships([relationship.id]);
        }

        this.showRelationshipDetails(relationship);

        // Log detailed relationship information
        console.log('📋 Relationship details:', {
            id: relationship.id,
            type: relationship.type,
            properties: relationship.properties,
            from: relationship.startNodeId,
            to: relationship.endNodeId
        });
    }

    onCanvasClick() {
        console.log('🖱️ Canvas clicked');

        // Clear selections if NVL supports it
        if (this.nvl && typeof this.nvl.clearSelection === 'function') {
            this.nvl.clearSelection();
        }

        // Clear any selections or details
        this.clearSelections();
    }

    onNodeClick(node, evt) {
        console.log('🔵 Node clicked:', node);

        // Extract node data from NVL event structure
        let nodeData = null;
        if (node && node.data) {
            nodeData = node.data;
        } else if (node && (node.properties || node.id)) {
            nodeData = node;
        }

        if (nodeData) {
            const name = nodeData.properties?.name || nodeData.properties?.id || nodeData.id || 'Unknown';
            const labels = nodeData.labels ? nodeData.labels.join(', ') : 'Unknown';
            console.log(`🔵 Node: ${name} (${labels})`);

            // Show node details in a simple way
            this.showNodeDetails(nodeData);
        } else {
            console.log('🔵 Node: No valid data found');
        }
    }

    onRelationshipClick(relationship, evt) {
        console.log('🔗 Relationship clicked:', relationship);

        // Extract relationship data from NVL event structure
        let relData = null;
        if (relationship && relationship.data) {
            relData = relationship.data;
        } else if (relationship && (relationship.type || relationship.id)) {
            relData = relationship;
        }

        if (relData) {
            const type = relData.type || 'Unknown';
            console.log(`🔗 Relationship: ${type}`);

            // Show relationship details
            this.showRelationshipDetails(relData);
        } else {
            console.log('🔗 Relationship: No valid data found');
        }
    }

    onNodeHover(node, evt) {
        // Extract node data from NVL event structure
        let nodeData = null;
        if (node && node.data) {
            nodeData = node.data;
        } else if (node && (node.properties || node.id)) {
            nodeData = node;
        }

        if (nodeData && nodeData.properties) {
            const name = nodeData.properties.name || nodeData.properties.id || nodeData.id || 'Unknown';
            const labels = nodeData.labels ? nodeData.labels.join(', ') : 'Unknown';
            console.log(`🔵 Node hovered: ${name} (${labels})`);
        } else {
            console.log('🔵 Node hovered: undefined or no properties');
        }
    }

    onRelationshipHover(relationship, evt) {
        // Extract relationship data from NVL event structure
        let relData = null;
        if (relationship && relationship.data) {
            relData = relationship.data;
        } else if (relationship && (relationship.type || relationship.id)) {
            relData = relationship;
        }

        if (relData) {
            const type = relData.type || 'Unknown';
            console.log(`🔗 Relationship hovered: ${type}`);
        } else {
            console.log('🔗 Relationship hovered: undefined');
        }
    }

    onCanvasHover(evt) {
        // Optional: handle canvas hover
    }

    showNodeDetails(node) {
        // Create a simple details display
        const detailsContainer = document.getElementById('node-details');
        if (detailsContainer) {
            const name = node.properties?.name || node.properties?.id || node.id;
            const labels = node.labels ? node.labels.join(', ') : 'Unknown';

            detailsContainer.innerHTML = `
                <h4>Node Details</h4>
                <p><strong>Name:</strong> ${name}</p>
                <p><strong>Type:</strong> ${labels}</p>
                <p><strong>ID:</strong> ${node.id}</p>
            `;
            detailsContainer.style.display = 'block';
        }
    }

    showRelationshipDetails(relationship) {
        // Create a simple details display
        const detailsContainer = document.getElementById('relationship-details');
        if (detailsContainer) {
            const type = relationship.type || 'Unknown';

            detailsContainer.innerHTML = `
                <h4>Relationship Details</h4>
                <p><strong>Type:</strong> ${type}</p>
                <p><strong>ID:</strong> ${relationship.id}</p>
            `;
            detailsContainer.style.display = 'block';
        }
    }

    // Additional event handlers for comprehensive interaction support

    onNodeDoubleClick(node) {
        console.log('🔵 Node double-clicked:', node);
        if (node && node.properties) {
            const name = node.properties.name || node.properties.id || node.id;
            console.log(`🔵 Double-clicked node: ${name}`);

            // Expand node or show detailed view
            this.expandNode(node);
        }
    }

    onRelationshipDoubleClick(relationship) {
        console.log('🔗 Relationship double-clicked:', relationship);
        if (relationship) {
            const type = relationship.type || 'Unknown';
            console.log(`🔗 Double-clicked relationship: ${type}`);

            // Show detailed relationship view
            this.expandRelationship(relationship);
        }
    }

    onZoom(zoomLevel) {
        console.log('🔍 Zoom changed to:', zoomLevel);
        // Update UI elements based on zoom level
        this.updateZoomUI(zoomLevel);
    }

    onPan(panning) {
        console.log('🖱️ Pan changed:', panning);
        // Update UI elements based on panning
        this.updatePanUI(panning);
    }

    onDragNodes(nodes) {
        console.log('🎯 Dragging nodes:', nodes);
        if (nodes && nodes.length > 0) {
            const nodeNames = nodes.map(n => n.properties?.name || n.id || 'Unknown').slice(0, 3);
            const displayText = nodeNames.length > 3 ?
                `${nodeNames.join(', ')} and ${nodes.length - 3} more` :
                nodeNames.join(', ');
            console.log(`🎯 Dragging: ${displayText}`);

            // Update real-time drag feedback
            const selectionInfo = document.getElementById('selection-info');
            if (selectionInfo) {
                selectionInfo.innerHTML = `🎯 Dragging: ${displayText}`;
                selectionInfo.style.display = 'block';
            }

            // Update zoom indicator with drag info
            const zoomIndicator = document.getElementById('zoom-indicator');
            if (zoomIndicator) {
                zoomIndicator.innerHTML = `Dragging ${nodes.length} node(s)`;
            }
        }
    }

    onDragStart(nodes) {
        console.log('🎯 Started dragging nodes:', nodes);
        if (nodes && nodes.length > 0) {
            const nodeNames = nodes.map(n => n.properties?.name || n.id).join(', ');
            console.log(`🎯 Started dragging: ${nodeNames}`);

            // Visual feedback for drag start
            this.showDragFeedback(nodes, true);
        }
    }

    onDragEnd(nodes) {
        console.log('🎯 Finished dragging nodes:', nodes);
        if (nodes && nodes.length > 0) {
            const nodeNames = nodes.map(n => n.properties?.name || n.id).join(', ');
            console.log(`🎯 Finished dragging: ${nodeNames}`);

            // Visual feedback for drag end
            this.showDragFeedback(nodes, false);
        }
    }

    onHover(element, hitElements, event) {
        console.log('🎯 Hover event:', element, hitElements);

        if (element) {
            if (element.type === 'node') {
                this.onNodeHover(element);
            } else if (element.type === 'relationship') {
                this.onRelationshipHover(element);
            }
        }

        // Show hover tooltip
        this.showHoverTooltip(element, event);
    }

    onLassoSelect(nodes, relationships) {
        console.log('🎯 Lasso selected:', nodes, relationships);

        if (nodes && nodes.length > 0) {
            const nodeNames = nodes.map(n => n.properties?.name || n.id).join(', ');
            console.log(`🎯 Selected nodes: ${nodeNames}`);
        }

        if (relationships && relationships.length > 0) {
            const relTypes = relationships.map(r => r.type || 'Unknown').join(', ');
            console.log(`🎯 Selected relationships: ${relTypes}`);
        }

        // Update selection UI
        this.updateSelectionUI(nodes, relationships);
    }

    // Helper methods for enhanced interaction functionality

    expandNode(node) {
        console.log('🔍 Expanding node:', node);
        // Could implement node expansion logic here
        // For example, load related nodes or show detailed properties
        this.showNodeDetails(node);
    }

    expandRelationship(relationship) {
        console.log('🔍 Expanding relationship:', relationship);
        // Could implement relationship expansion logic here
        this.showRelationshipDetails(relationship);
    }

    updateZoomUI(zoomLevel) {
        // Update zoom indicator in UI
        const zoomIndicator = document.querySelector('.zoom-indicator');
        if (zoomIndicator) {
            zoomIndicator.textContent = `Zoom: ${Math.round(zoomLevel * 100)}%`;
        }
    }

    updatePanUI(panning) {
        // Update pan indicator in UI if needed
        console.log('📍 Pan position updated:', panning);
    }

    showDragFeedback(nodes, isDragging) {
        // Visual feedback during drag operations
        if (isDragging) {
            console.log('🎯 Showing drag feedback for nodes');

            // Update selection info panel
            const selectionInfo = document.getElementById('selection-info');
            if (selectionInfo && nodes && nodes.length > 0) {
                const nodeNames = nodes.map(n => n.properties?.name || n.id || 'Unknown').slice(0, 3);
                const displayText = nodeNames.length > 3 ?
                    `${nodeNames.join(', ')} and ${nodes.length - 3} more` :
                    nodeNames.join(', ');
                selectionInfo.innerHTML = `🎯 Dragging: ${displayText}`;
                selectionInfo.style.display = 'block';
            }

            // Could add visual indicators like highlighting
            console.log(`🎯 Drag started for ${nodes.length} node(s)`);
        } else {
            console.log('🎯 Hiding drag feedback for nodes');

            // Hide selection info panel
            const selectionInfo = document.getElementById('selection-info');
            if (selectionInfo) {
                selectionInfo.style.display = 'none';
            }

            // Remove visual indicators
            console.log(`🎯 Drag ended for ${nodes.length} node(s)`);
        }
    }

    showHoverTooltip(element, event) {
        // Show tooltip on hover
        if (element && event) {
            const tooltip = document.getElementById('graph-tooltip');
            if (tooltip) {
                let content = '';
                if (element.type === 'node') {
                    const name = element.properties?.name || element.id;
                    const labels = element.labels ? element.labels.join(', ') : 'Unknown';
                    content = `<strong>${name}</strong><br>Type: ${labels}`;
                } else if (element.type === 'relationship') {
                    const type = element.type || 'Unknown';
                    content = `<strong>${type}</strong><br>Relationship`;
                }

                tooltip.innerHTML = content;
                tooltip.style.display = 'block';
                tooltip.style.left = event.clientX + 10 + 'px';
                tooltip.style.top = event.clientY + 10 + 'px';
            }
        } else {
            // Hide tooltip
            const tooltip = document.getElementById('graph-tooltip');
            if (tooltip) {
                tooltip.style.display = 'none';
            }
        }
    }

    updateSelectionUI(nodes, relationships) {
        // Update UI to show selection information
        const selectionInfo = document.getElementById('selection-info');
        if (selectionInfo) {
            const nodeCount = nodes ? nodes.length : 0;
            const relCount = relationships ? relationships.length : 0;
            selectionInfo.innerHTML = `
                <strong>Selection:</strong>
                ${nodeCount} nodes, ${relCount} relationships
            `;
            selectionInfo.style.display = nodeCount > 0 || relCount > 0 ? 'block' : 'none';
        }
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
        if (!relationship) {
            console.log('No relationship data to show');
            return;
        }

        const type = relationship.type || 'Unknown';
        let propertiesHtml = '';

        if (relationship.properties && typeof relationship.properties === 'object') {
            try {
                propertiesHtml = Object.entries(relationship.properties)
                    .map(([key, value]) => `${key}: ${value}`)
                    .join('<br>');
            } catch (error) {
                console.warn('Error processing relationship properties:', error);
                propertiesHtml = 'Properties unavailable';
            }
        } else {
            propertiesHtml = 'No properties available';
        }

        const details = `
            <strong>${type}</strong><br>
            ${propertiesHtml}
        `;

        console.log('Relationship details:', details);

        // Update the details container if it exists
        const detailsContainer = document.getElementById('relationship-details');
        if (detailsContainer) {
            detailsContainer.innerHTML = `
                <h4>Relationship Details</h4>
                <p><strong>Type:</strong> ${type}</p>
                <p><strong>ID:</strong> ${relationship.id || 'Unknown'}</p>
                ${propertiesHtml !== 'No properties available' ? `<p><strong>Properties:</strong><br>${propertiesHtml}</p>` : ''}
            `;
            detailsContainer.style.display = 'block';
        }
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

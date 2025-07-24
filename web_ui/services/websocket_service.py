"""
WebSocket Service - Real-time communication for document processing updates
Provides WebSocket endpoints for live progress tracking and notifications
"""

import json
import logging
import asyncio
from typing import Dict, List, Set, Optional, Any
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class WebSocketConnection:
    """Represents a WebSocket connection."""
    websocket: WebSocket
    user_id: str
    connection_id: str
    connected_at: datetime
    last_ping: datetime
    subscriptions: Set[str]  # Topics the connection is subscribed to


class WebSocketManager:
    """Manages WebSocket connections and message broadcasting."""
    
    def __init__(self):
        # Active connections by user ID
        self.connections: Dict[str, List[WebSocketConnection]] = {}
        
        # Connections by connection ID for quick lookup
        self.connection_lookup: Dict[str, WebSocketConnection] = {}
        
        # Topic subscriptions
        self.topic_subscribers: Dict[str, Set[str]] = {}  # topic -> set of connection_ids
        
        # Statistics
        self.total_connections = 0
        self.messages_sent = 0
        
        # Heartbeat task
        self.heartbeat_task = None
        self._running = False
    
    async def start(self):
        """Start the WebSocket manager."""
        if not self._running:
            self._running = True
            self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            logger.info("WebSocket manager started")
    
    async def stop(self):
        """Stop the WebSocket manager."""
        self._running = False
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
        
        # Close all connections
        for connections in self.connections.values():
            for conn in connections:
                try:
                    await conn.websocket.close()
                except Exception:
                    pass
        
        self.connections.clear()
        self.connection_lookup.clear()
        self.topic_subscribers.clear()
        
        logger.info("WebSocket manager stopped")
    
    async def connect(self, websocket: WebSocket, user_id: str, connection_id: str) -> WebSocketConnection:
        """Register a new WebSocket connection."""
        await websocket.accept()
        
        connection = WebSocketConnection(
            websocket=websocket,
            user_id=user_id,
            connection_id=connection_id,
            connected_at=datetime.now(),
            last_ping=datetime.now(),
            subscriptions=set()
        )
        
        # Add to user connections
        if user_id not in self.connections:
            self.connections[user_id] = []
        self.connections[user_id].append(connection)
        
        # Add to lookup
        self.connection_lookup[connection_id] = connection
        
        self.total_connections += 1
        
        logger.info(f"WebSocket connected: user={user_id}, connection={connection_id}")
        
        # Send welcome message
        await self.send_to_connection(connection_id, {
            "type": "connection_established",
            "connection_id": connection_id,
            "server_time": datetime.now().isoformat(),
            "message": "WebSocket connection established"
        })
        
        return connection
    
    async def disconnect(self, connection_id: str):
        """Unregister a WebSocket connection."""
        connection = self.connection_lookup.get(connection_id)
        if not connection:
            return
        
        user_id = connection.user_id
        
        # Remove from user connections
        if user_id in self.connections:
            try:
                self.connections[user_id].remove(connection)
                if not self.connections[user_id]:
                    del self.connections[user_id]
            except ValueError:
                pass
        
        # Remove from lookup
        if connection_id in self.connection_lookup:
            del self.connection_lookup[connection_id]
        
        # Remove from topic subscriptions
        for topic, subscribers in self.topic_subscribers.items():
            subscribers.discard(connection_id)
        
        logger.info(f"WebSocket disconnected: user={user_id}, connection={connection_id}")
    
    async def send_to_user(self, user_id: str, message: Dict[str, Any]) -> int:
        """Send message to all connections for a specific user."""
        sent_count = 0
        
        if user_id in self.connections:
            connections_to_remove = []
            
            for connection in self.connections[user_id]:
                try:
                    await connection.websocket.send_text(json.dumps(message))
                    sent_count += 1
                    self.messages_sent += 1
                except Exception as e:
                    logger.error(f"Error sending message to user {user_id}: {e}")
                    connections_to_remove.append(connection)
            
            # Remove failed connections
            for connection in connections_to_remove:
                await self.disconnect(connection.connection_id)
        
        return sent_count
    
    async def send_to_connection(self, connection_id: str, message: Dict[str, Any]) -> bool:
        """Send message to a specific connection."""
        connection = self.connection_lookup.get(connection_id)
        if not connection:
            return False
        
        try:
            await connection.websocket.send_text(json.dumps(message))
            self.messages_sent += 1
            return True
        except Exception as e:
            logger.error(f"Error sending message to connection {connection_id}: {e}")
            await self.disconnect(connection_id)
            return False
    
    async def broadcast_to_topic(self, topic: str, message: Dict[str, Any]) -> int:
        """Broadcast message to all subscribers of a topic."""
        sent_count = 0
        
        if topic in self.topic_subscribers:
            connections_to_remove = []
            
            for connection_id in self.topic_subscribers[topic].copy():
                connection = self.connection_lookup.get(connection_id)
                if connection:
                    try:
                        await connection.websocket.send_text(json.dumps(message))
                        sent_count += 1
                        self.messages_sent += 1
                    except Exception as e:
                        logger.error(f"Error broadcasting to topic {topic}: {e}")
                        connections_to_remove.append(connection_id)
                else:
                    connections_to_remove.append(connection_id)
            
            # Remove failed connections
            for connection_id in connections_to_remove:
                await self.disconnect(connection_id)
        
        return sent_count
    
    async def subscribe_to_topic(self, connection_id: str, topic: str) -> bool:
        """Subscribe a connection to a topic."""
        connection = self.connection_lookup.get(connection_id)
        if not connection:
            return False
        
        connection.subscriptions.add(topic)
        
        if topic not in self.topic_subscribers:
            self.topic_subscribers[topic] = set()
        self.topic_subscribers[topic].add(connection_id)
        
        logger.debug(f"Connection {connection_id} subscribed to topic {topic}")
        return True
    
    async def unsubscribe_from_topic(self, connection_id: str, topic: str) -> bool:
        """Unsubscribe a connection from a topic."""
        connection = self.connection_lookup.get(connection_id)
        if not connection:
            return False
        
        connection.subscriptions.discard(topic)
        
        if topic in self.topic_subscribers:
            self.topic_subscribers[topic].discard(connection_id)
            if not self.topic_subscribers[topic]:
                del self.topic_subscribers[topic]
        
        logger.debug(f"Connection {connection_id} unsubscribed from topic {topic}")
        return True
    
    async def handle_message(self, connection_id: str, message: str):
        """Handle incoming WebSocket message."""
        connection = self.connection_lookup.get(connection_id)
        if not connection:
            return
        
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == "ping":
                # Handle ping/pong
                connection.last_ping = datetime.now()
                await self.send_to_connection(connection_id, {
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                })
            
            elif message_type == "subscribe":
                # Subscribe to topic
                topic = data.get("topic")
                if topic:
                    await self.subscribe_to_topic(connection_id, topic)
                    await self.send_to_connection(connection_id, {
                        "type": "subscription_confirmed",
                        "topic": topic
                    })
            
            elif message_type == "unsubscribe":
                # Unsubscribe from topic
                topic = data.get("topic")
                if topic:
                    await self.unsubscribe_from_topic(connection_id, topic)
                    await self.send_to_connection(connection_id, {
                        "type": "unsubscription_confirmed",
                        "topic": topic
                    })
            
            elif message_type == "get_status":
                # Send connection status
                await self.send_to_connection(connection_id, {
                    "type": "status",
                    "connection_id": connection_id,
                    "user_id": connection.user_id,
                    "connected_at": connection.connected_at.isoformat(),
                    "subscriptions": list(connection.subscriptions),
                    "server_time": datetime.now().isoformat()
                })
            
            else:
                logger.warning(f"Unknown message type: {message_type}")
        
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON message from connection {connection_id}")
        except Exception as e:
            logger.error(f"Error handling message from connection {connection_id}: {e}")
    
    async def _heartbeat_loop(self):
        """Periodic heartbeat to check connection health."""
        while self._running:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                
                current_time = datetime.now()
                stale_connections = []
                
                # Find stale connections (no ping in 60 seconds)
                for connection_id, connection in self.connection_lookup.items():
                    if (current_time - connection.last_ping).total_seconds() > 60:
                        stale_connections.append(connection_id)
                
                # Remove stale connections
                for connection_id in stale_connections:
                    logger.info(f"Removing stale connection: {connection_id}")
                    await self.disconnect(connection_id)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get WebSocket manager statistics."""
        return {
            "total_connections": len(self.connection_lookup),
            "users_connected": len(self.connections),
            "topics": len(self.topic_subscribers),
            "messages_sent": self.messages_sent,
            "connections_by_user": {
                user_id: len(connections) 
                for user_id, connections in self.connections.items()
            },
            "topic_subscribers": {
                topic: len(subscribers)
                for topic, subscribers in self.topic_subscribers.items()
            }
        }


# Global WebSocket manager instance
websocket_manager = WebSocketManager()


# WebSocket message types for document processing
class DocumentProcessingMessages:
    """Standard message types for document processing."""
    
    @staticmethod
    def job_created(job_id: str, filename: str) -> Dict[str, Any]:
        return {
            "type": "job_created",
            "job_id": job_id,
            "filename": filename,
            "timestamp": datetime.now().isoformat()
        }
    
    @staticmethod
    def job_progress(job_id: str, status: str, progress: float, stage: str, stage_progress: float) -> Dict[str, Any]:
        return {
            "type": "job_progress",
            "job_id": job_id,
            "status": status,
            "progress": progress,
            "stage": stage,
            "stage_progress": stage_progress,
            "timestamp": datetime.now().isoformat()
        }
    
    @staticmethod
    def job_completed(job_id: str, session_id: str, entities_count: int, relationships_count: int) -> Dict[str, Any]:
        return {
            "type": "job_completed",
            "job_id": job_id,
            "session_id": session_id,
            "entities_count": entities_count,
            "relationships_count": relationships_count,
            "timestamp": datetime.now().isoformat()
        }
    
    @staticmethod
    def job_failed(job_id: str, error_message: str) -> Dict[str, Any]:
        return {
            "type": "job_failed",
            "job_id": job_id,
            "error_message": error_message,
            "timestamp": datetime.now().isoformat()
        }
    
    @staticmethod
    def conflicts_detected(session_id: str, conflicts_count: int) -> Dict[str, Any]:
        return {
            "type": "conflicts_detected",
            "session_id": session_id,
            "conflicts_count": conflicts_count,
            "timestamp": datetime.now().isoformat()
        }
    
    @staticmethod
    def entities_approved(session_id: str, approved_count: int) -> Dict[str, Any]:
        return {
            "type": "entities_approved",
            "session_id": session_id,
            "approved_count": approved_count,
            "timestamp": datetime.now().isoformat()
        }
    
    @staticmethod
    def ingestion_completed(session_id: str, ingested_entities: int, ingested_relationships: int) -> Dict[str, Any]:
        return {
            "type": "ingestion_completed",
            "session_id": session_id,
            "ingested_entities": ingested_entities,
            "ingested_relationships": ingested_relationships,
            "timestamp": datetime.now().isoformat()
        }
    
    @staticmethod
    def system_notification(message: str, level: str = "info") -> Dict[str, Any]:
        return {
            "type": "system_notification",
            "message": message,
            "level": level,  # info, warning, error, success
            "timestamp": datetime.now().isoformat()
        }

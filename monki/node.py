import asyncio
import hashlib
import os
import socket
import json
from pathlib import Path
from typing import Dict, Optional, Tuple

class Node:
    def __init__(self, node_id: str, host: str, port: int, storage_dir: str):
        self.node_id = node_id
        self.host = host
        self.port = port
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True, parents=True)
        self.connected_nodes: Dict[str, Tuple[str, int]] = {}
        
    async def start(self):
        server = await asyncio.start_server(
            self.handle_connection, self.host, self.port
        )
        addr = server.sockets[0].getsockname()
        print(f"Node {self.node_id} serving on {addr}")
        
        async with server:
            await server.serve_forever()
    
    async def handle_connection(self, reader, writer):
        addr = writer.get_extra_info('peername')
        print(f"Connection from {addr}")
        
        try:
            while True:
                data = await reader.readline()
                if not data:
                    break
                    
                message = data.decode().strip()
                if not message:
                    continue
                    
                parts = message.split()
                command = parts[0].upper()
                
                if command == "PING":
                    response = "OK\r\n"
                elif command == "PUT" and len(parts) >= 3:
                    chunk_id = parts[1]
                    size = int(parts[2])
                    chunk_data = await reader.readexactly(size)
                    
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(
                        None, self._save_chunk, chunk_id, chunk_data
                    )
                    response = "OK\r\n"
                elif command == "GET" and len(parts) >= 2:
                    chunk_id = parts[1]
                    loop = asyncio.get_event_loop()
                    chunk_data = await loop.run_in_executor(
                        None, self._load_chunk, chunk_id
                    )
                    
                    if chunk_data:
                        response = f"OK {len(chunk_data)}\r\n"
                        writer.write(response.encode())
                        writer.write(chunk_data)
                        await writer.drain()
                        continue
                    else:
                        response = "ERROR Chunk not found\r\n"
                elif command == "JOIN" and len(parts) >= 4:
                    node_id = parts[1]
                    node_host = parts[2]
                    node_port = int(parts[3])
                    self.connected_nodes[node_id] = (node_host, node_port)
                    response = "OK\r\n"
                else:
                    response = "ERROR Invalid command\r\n"
                
                writer.write(response.encode())
                await writer.drain()
        except asyncio.IncompleteReadError:
            pass
        except Exception as e:
            print(f"Error handling connection: {e}")
        finally:
            writer.close()
            await writer.wait_closed()
            print(f"Connection closed from {addr}")
    
    def _save_chunk(self, chunk_id: str, data: bytes) -> None:
        chunk_path = self.storage_dir / chunk_id
        with open(chunk_path, 'wb') as f:
            f.write(data)
    
    def _load_chunk(self, chunk_id: str) -> Optional[bytes]:
        chunk_path = self.storage_dir / chunk_id
        if not chunk_path.exists():
            return None
        with open(chunk_path, 'rb') as f:
            return f.read()

    async def connect_to_node(self, node_id: str, host: str, port: int) -> bool:
        try:
            reader, writer = await asyncio.open_connection(host, port)
            message = f"JOIN {self.node_id} {self.host} {self.port}\r\n"
            writer.write(message.encode())
            await writer.drain()
            
            response = await reader.readline()
            writer.close()
            await writer.wait_closed()
            
            return response.decode().strip() == "OK"
        except Exception as e:
            print(f"Failed to connect to node {node_id} at {host}:{port}: {e}")
            return False
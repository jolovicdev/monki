import asyncio
import hashlib
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional

class Client:
    def __init__(self, chunk_size: int = 1024 * 1024):
        self.nodes: Dict[str, Tuple[str, int]] = {}
        self.chunk_size = chunk_size
    
    def add_node(self, node_id: str, host: str, port: int) -> None:
        self.nodes[node_id] = (host, port)
    
    def _calculate_chunk_id(self, data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()
    
    def _select_node_for_chunk(self, chunk_id: str) -> Optional[Tuple[str, int]]:
        if not self.nodes:
            return None
        
        hash_value = int(chunk_id, 16)
        node_ids = sorted(self.nodes.keys())
        node_idx = hash_value % len(node_ids)
        
        selected_node_id = node_ids[node_idx]
        return self.nodes[selected_node_id]
    
    async def upload_file(self, file_path: str) -> Dict[str, List[str]]:
        chunk_locations = {}
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File {file_path} not found")
        
        file_size = file_path.stat().st_size
        total_chunks = (file_size + self.chunk_size - 1) // self.chunk_size
        
        with open(file_path, 'rb') as f:
            for chunk_index in range(total_chunks):
                chunk_data = f.read(self.chunk_size)
                chunk_id = self._calculate_chunk_id(chunk_data)
                
                node_host, node_port = self._select_node_for_chunk(chunk_id)
                success = await self._upload_chunk(chunk_id, chunk_data, node_host, node_port)
                
                if success:
                    if str(chunk_index) not in chunk_locations:
                        chunk_locations[str(chunk_index)] = []
                    chunk_locations[str(chunk_index)].append(chunk_id)
        
        return {
            "filename": file_path.name,
            "size": file_size,
            "chunks": chunk_locations
        }
    
    async def _upload_chunk(self, chunk_id: str, data: bytes, host: str, port: int) -> bool:
        try:
            reader, writer = await asyncio.open_connection(host, port)
            
            message = f"PUT {chunk_id} {len(data)}\r\n"
            writer.write(message.encode())
            writer.write(data)
            await writer.drain()
            
            response = await reader.readline()
            writer.close()
            await writer.wait_closed()
            
            return response.decode().strip() == "OK"
        except Exception as e:
            print(f"Failed to upload chunk {chunk_id}: {e}")
            return False
    
    async def download_file(self, file_metadata: Dict, output_path: str) -> bool:
        output_path = Path(output_path)
        if output_path.exists() and output_path.is_dir():
            output_path = output_path / file_metadata["filename"]
        
        chunks = []
        for chunk_index in sorted(file_metadata["chunks"].keys(), key=int):
            chunk_ids = file_metadata["chunks"][chunk_index]
            if not chunk_ids:
                print(f"Missing chunk at index {chunk_index}")
                return False
            
            chunk_id = chunk_ids[0]
            node = self._select_node_for_chunk(chunk_id)
            if not node:
                print(f"No node available for chunk {chunk_id}")
                return False
            
            node_host, node_port = node
            chunk_data = await self._download_chunk(chunk_id, node_host, node_port)
            if chunk_data is None:
                print(f"Failed to download chunk {chunk_id}")
                return False
            
            chunks.append(chunk_data)
        
        with open(output_path, 'wb') as f:
            for chunk in chunks:
                f.write(chunk)
        
        return True
    
    async def _download_chunk(self, chunk_id: str, host: str, port: int) -> Optional[bytes]:
        try:
            reader, writer = await asyncio.open_connection(host, port)
            
            message = f"GET {chunk_id}\r\n"
            writer.write(message.encode())
            await writer.drain()
            
            response_line = await reader.readline()
            response = response_line.decode().strip()
            
            if response.startswith("OK"):
                parts = response.split()
                size = int(parts[1])
                chunk_data = await reader.readexactly(size)
                
                writer.close()
                await writer.wait_closed()
                return chunk_data
            else:
                writer.close()
                await writer.wait_closed()
                return None
        except Exception as e:
            print(f"Failed to download chunk {chunk_id}: {e}")
            return None
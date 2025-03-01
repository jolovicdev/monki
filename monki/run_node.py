import asyncio
import argparse
import os
import socket
import sys
from pathlib import Path

from .node import Node

def parse_args():
    parser = argparse.ArgumentParser(description="Start a Monki storage node")
    parser.add_argument("--node-id", help="Unique ID for this node", default=socket.gethostname())
    parser.add_argument("--host", help="Host to listen on", default="127.0.0.1")
    parser.add_argument("--port", help="Port to listen on", type=int, default=8000)
    parser.add_argument("--storage-dir", help="Directory to store chunks", 
                        default=str(Path.home() / ".monki" / "storage"))
    parser.add_argument("--join", help="Node to join (host:port)", default=None)
    
    return parser.parse_args()

async def main():
    args = parse_args()
    
    storage_dir = Path(args.storage_dir)
    if not storage_dir.exists():
        storage_dir.mkdir(parents=True)
    
    node = Node(args.node_id, args.host, args.port, args.storage_dir)
    
    if args.join:
        join_host, join_port = args.join.split(":")
        join_port = int(join_port)
        
        success = await node.connect_to_node("remote", join_host, join_port)
        if not success:
            print(f"Failed to join node at {join_host}:{join_port}")
    
    await node.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Node stopped")
        sys.exit(0)
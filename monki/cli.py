import asyncio
import argparse
import json
import sys
from pathlib import Path

from .client import Client

def parse_args():
    parser = argparse.ArgumentParser(description="Monki distributed storage client")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    upload_parser = subparsers.add_parser("upload", help="Upload a file")
    upload_parser.add_argument("file", help="File to upload")
    upload_parser.add_argument("--node", help="Node to connect to (host:port)", required=True, action="append")
    upload_parser.add_argument("--output", help="Output file to save metadata", default=None)
    
    download_parser = subparsers.add_parser("download", help="Download a file")
    download_parser.add_argument("metadata", help="Metadata file")
    download_parser.add_argument("--node", help="Node to connect to (host:port)", required=True, action="append")
    download_parser.add_argument("--output", help="Output directory", default=".")
    
    return parser.parse_args()

async def main():
    args = parse_args()
    
    if not args.command:
        print("Please specify a command: upload or download")
        sys.exit(1)
    
    client = Client()
    
    for i, node_str in enumerate(args.node):
        host, port = node_str.split(":")
        client.add_node(f"node{i}", host, int(port))
    
    if args.command == "upload":
        file_path = args.file
        metadata = await client.upload_file(file_path)
        
        if args.output:
            output_path = args.output
        else:
            output_path = f"{file_path}.monki"
        
        with open(output_path, "w") as f:
            json.dump(metadata, f, indent=2)
        
        print(f"File uploaded. Metadata saved to {output_path}")
    
    elif args.command == "download":
        metadata_path = args.metadata
        with open(metadata_path, "r") as f:
            metadata = json.load(f)
        
        output_path = args.output
        success = await client.download_file(metadata, output_path)
        
        if success:
            if Path(output_path).is_dir():
                output_file = Path(output_path) / metadata["filename"]
            else:
                output_file = output_path
            print(f"File downloaded to {output_file}")
        else:
            print("Failed to download file")
            sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Operation cancelled")
        sys.exit(0)
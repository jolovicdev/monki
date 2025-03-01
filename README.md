# Monki - Lightweight Distributed Storage System

Monki is a dependency-free distributed storage system built in Python. It uses asyncio for concurrent operations and splits files into chunks that are distributed across multiple nodes.

## Features

- Pure Python implementation with no external dependencies
- Distributed storage with consistent hashing
- Asynchronous I/O for fast performance
- Simple text-based protocol over TCP
- Lightweight and easy to deploy

## Installation

```bash
# Install from source
pip install -e .
```

## Running a Storage Node

```bash
# Start a standalone node
python3 -m monki.run_node --port 8000 --storage-dir /path/to/storage

# Join an existing network
python3 -m monki.run_node --port 8001 --join 127.0.0.1:8000
```

## Using the Client

### Upload a File

```bash
python3 -m monki.cli upload path/to/file --node 127.0.0.1:8000 --node 127.0.0.1:8001
```

This will split the file into chunks, distribute them across the specified nodes, and save a metadata file with the `.monki` extension.

### Download a File

```bash
python3 -m monki.cli download path/to/file.monki --node 127.0.0.1:8000 --node 127.0.0.1:8001
```

This will download the chunks from the nodes and reassemble the file.

## Protocol

Monki uses a simple text-based protocol:

- `PUT <chunk_id> <size>\r\n<data>` - Store a chunk
- `GET <chunk_id>\r\n` - Retrieve a chunk
- `PING\r\n` - Check node health
- `JOIN <node_id> <host> <port>\r\n` - Join a node to the network

## Architecture

1. Files are split into fixed-size chunks (default 1MB)
2. Each chunk is hashed and assigned to a node using consistent hashing
3. The client stores metadata about the file and its chunks
4. Chunks can be retrieved in parallel for fast downloads

## Running Tests

```bash
python -m unittest discover -s tests
```
import asyncio
import os
import tempfile
import unittest
from pathlib import Path

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from monki.node import Node

class TestNode(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.storage_dir = Path(self.test_dir.name)
        
    def tearDown(self):
        self.test_dir.cleanup()
    
    def test_node_init(self):
        node = Node("test", "127.0.0.1", 8000, str(self.storage_dir))
        self.assertEqual(node.node_id, "test")
        self.assertEqual(node.host, "127.0.0.1")
        self.assertEqual(node.port, 8000)
        self.assertEqual(node.storage_dir, self.storage_dir)
        self.assertEqual(node.connected_nodes, {})
    
    def test_save_and_load_chunk(self):
        node = Node("test", "127.0.0.1", 8000, str(self.storage_dir))
        
        test_data = b"This is test data"
        chunk_id = "test_chunk"
        
        node._save_chunk(chunk_id, test_data)
        loaded_data = node._load_chunk(chunk_id)
        
        self.assertEqual(loaded_data, test_data)
        
        missing_data = node._load_chunk("nonexistent")
        self.assertIsNone(missing_data)

if __name__ == "__main__":
    unittest.main()
"""
EarthScape Climate Agency - Hadoop Distributed File System (HDFS) Cluster Simulator
Simulates NameNode metadata management, DataNode block allocation, replication (3x),
fault tolerance, block health reporting, and scalable partitioned data access.
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
import json
import os
import hashlib
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
PARTITIONS_DIR = PROCESSED_DIR / "hdfs_partitions"
HDFS_META_FILE = PROCESSED_DIR / "hdfs_cluster_state.json"


class HDFSClusterManager:
    """
    Simulates a distributed HDFS storage cluster for EarthScape Climate Agency.
    """

    def __init__(self, replication_factor: int = 3, block_size_mb: int = 64):
        self.replication_factor = replication_factor
        self.block_size_mb = block_size_mb
        self.namenode = {
            "cluster_id": "HDFS-EARTHSCAPE-01",
            "namenode_uri": "hdfs://namenode.earthscape.internal:9000",
            "status": "HEALTHY",
            "active_since": "2024-01-01T00:00:00Z"
        }
        self.datanodes = [
            {"node_id": "DN-01-NORTH", "host": "10.0.1.101", "rack": "/rack-1", "capacity_gb": 500, "status": "ONLINE", "healthy_blocks": 0},
            {"node_id": "DN-02-WEST", "host": "10.0.1.102", "rack": "/rack-1", "capacity_gb": 500, "status": "ONLINE", "healthy_blocks": 0},
            {"node_id": "DN-03-SOUTH", "host": "10.0.1.103", "rack": "/rack-2", "capacity_gb": 500, "status": "ONLINE", "healthy_blocks": 0},
            {"node_id": "DN-04-EAST", "host": "10.0.1.104", "rack": "/rack-2", "capacity_gb": 500, "status": "ONLINE", "healthy_blocks": 0},
        ]
        self.blocks: List[Dict[str, Any]] = []

    def scan_and_register_blocks(self) -> Dict[str, Any]:
        """
        Scans all physical partitioned data files, generates HDFS block IDs,
        computes block checksums, and distributes replica locations across DataNodes.
        """
        self.blocks = []
        node_idx = 0
        num_nodes = len(self.datanodes)

        if not PARTITIONS_DIR.exists():
            return self.get_cluster_status()

        block_files = sorted(list(PARTITIONS_DIR.glob("**/*.csv")))
        total_size_bytes = 0

        for file_path in block_files:
            size_bytes = file_path.stat().st_size
            total_size_bytes += size_bytes
            
            # Generate deterministic block ID
            rel_path = file_path.relative_to(PROCESSED_DIR).as_posix()
            block_id = f"blk_{hashlib.md5(rel_path.encode()).hexdigest()[:12]}"
            
            # Assign replicas across different racks
            replicas = []
            for r in range(self.replication_factor):
                target_node = self.datanodes[(node_idx + r) % num_nodes]["node_id"]
                replicas.append(target_node)
            node_idx = (node_idx + 1) % num_nodes

            # Extract partition tags
            parts = file_path.parent.name.split("=")
            zone_id = parts[1] if len(parts) == 2 else "UNKNOWN"
            year = file_path.stem.split("_")[-1]

            self.blocks.append({
                "block_id": block_id,
                "hdfs_path": f"/climate/data/{rel_path}",
                "local_path": str(file_path),
                "zone_id": zone_id,
                "year": year,
                "size_bytes": size_bytes,
                "size_kb": round(size_bytes / 1024.0, 2),
                "replicas": replicas,
                "status": "HEALTHY",
                "checksum": hashlib.sha256(file_path.read_bytes()).hexdigest()[:16]
            })

        # Update datanode block counts
        for dn in self.datanodes:
            node_id = dn["node_id"]
            count = sum(1 for b in self.blocks if node_id in b["replicas"])
            dn["healthy_blocks"] = count
            dn["used_mb"] = round(sum(b["size_bytes"] for b in self.blocks if node_id in b["replicas"]) / (1024 * 1024), 2)

        cluster_state = self.get_cluster_status()
        
        # Save to disk
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        with open(HDFS_META_FILE, "w", encoding="utf-8") as f:
            json.dump(cluster_state, f, indent=2)

        return cluster_state

    def get_cluster_status(self) -> Dict[str, Any]:
        """
        Returns full HDFS health, capacity, replication status, and topology report.
        """
        total_capacity_gb = sum(dn["capacity_gb"] for dn in self.datanodes)
        total_used_bytes = sum(b["size_bytes"] * len(b["replicas"]) for b in self.blocks)
        total_used_mb = round(total_used_bytes / (1024 * 1024), 2)
        total_used_gb = round(total_used_mb / 1024.0, 4)

        return {
            "namenode": self.namenode,
            "datanodes": self.datanodes,
            "total_blocks": len(self.blocks),
            "replication_factor": self.replication_factor,
            "total_capacity_gb": total_capacity_gb,
            "used_storage_mb": total_used_mb,
            "used_storage_gb": total_used_gb,
            "free_storage_gb": round(total_capacity_gb - total_used_gb, 2),
            "storage_utilization_pct": round((total_used_gb / total_capacity_gb) * 100.0, 4),
            "under_replicated_blocks": 0,
            "corrupt_blocks": 0,
            "blocks_summary": self.blocks[:15]  # Preview for fast payload
        }

    def list_all_blocks(self) -> List[Dict[str, Any]]:
        """
        Returns all registered HDFS blocks.
        """
        if not self.blocks and HDFS_META_FILE.exists():
            with open(HDFS_META_FILE, "r", encoding="utf-8") as f:
                state = json.load(f)
                return state.get("blocks_summary", [])
        return self.blocks


if __name__ == "__main__":
    hdfs = HDFSClusterManager()
    status = hdfs.scan_and_register_blocks()
    print("HDFS Cluster Status:")
    print(json.dumps(status, indent=2))

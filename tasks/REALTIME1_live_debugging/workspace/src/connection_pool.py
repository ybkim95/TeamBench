"""
Connection Pool Manager - Contains a subtle race condition
"""
import threading
import time
import random
from typing import Optional, List
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Connection:
    id: str
    created_at: datetime
    last_used: datetime
    is_active: bool
    
class ConnectionPool:
    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self.connections: List[Connection] = []
        self.lock = threading.Lock()  # Bug: Single lock causes contention
        self.stats = {"requests": 0, "failures": 0, "active": 0}
        
    def get_connection(self, timeout: float = 1.0) -> Optional[Connection]:
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            with self.lock:  # Problem: Lock held during entire connection creation
                self.stats["requests"] += 1
                
                # Try to find available connection
                for conn in self.connections:
                    if not conn.is_active:
                        conn.is_active = True
                        conn.last_used = datetime.now()
                        self.stats["active"] += 1
                        return conn
                
                # Create new if under limit
                if len(self.connections) < self.max_size:
                    # BUG: Connection creation inside lock causes blocking
                    time.sleep(random.uniform(0.01, 0.05))  # Simulate DB handshake
                    
                    new_conn = Connection(
                        id=f"conn_{len(self.connections)}",
                        created_at=datetime.now(),
                        last_used=datetime.now(),
                        is_active=True
                    )
                    self.connections.append(new_conn)
                    self.stats["active"] += 1
                    return new_conn
            
            # Wait before retry (but this rarely helps)
            time.sleep(0.01)
        
        # Timeout - this is where errors occur
        self.stats["failures"] += 1
        raise TimeoutError("Could not acquire connection")
    
    def release_connection(self, conn: Connection):
        with self.lock:
            conn.is_active = False
            self.stats["active"] -= 1
    
    def health_check(self) -> dict:
        with self.lock:
            return {
                "pool_size": len(self.connections),
                "active_connections": self.stats["active"],
                "total_requests": self.stats["requests"],
                "failed_requests": self.stats["failures"],
                "utilization": self.stats["active"] / self.max_size * 100
            }

# Global pool instance (another antipattern)
pool = ConnectionPool()
"""
Multi-turn State Management System for TeamBench
Enables tasks to maintain and evolve state across agent turns
"""

import json
import time
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from dataclasses import dataclass, asdict, field
from enum import Enum

class StateType(Enum):
    """Types of state that can be managed"""
    REALTIME = "realtime"  # Time-sensitive, expires
    PERSISTENT = "persistent"  # Survives across runs  
    CONTEXTUAL = "contextual"  # Based on previous actions
    ADVERSARIAL = "adversarial"  # Opponent/defender state
    RESOURCE = "resource"  # Tracks limited resources

@dataclass
class TurnState:
    """State for a single turn"""
    turn_number: int
    timestamp: str
    agent_role: str
    action_taken: Dict[str, Any]
    state_changes: Dict[str, Any]
    metrics: Dict[str, float]
    
@dataclass 
class TaskState:
    """Complete state for a multi-turn task"""
    task_id: str
    state_type: StateType
    created_at: str
    updated_at: str
    turn_history: List[TurnState] = field(default_factory=list)
    global_state: Dict[str, Any] = field(default_factory=dict)
    resource_limits: Dict[str, int] = field(default_factory=dict)
    time_constraints: Dict[str, float] = field(default_factory=dict)
    checkpoints: List[Dict[str, Any]] = field(default_factory=list)
    
class StateManager:
    """Manages state across multi-turn agent interactions"""
    
    def __init__(self, task_id: str, workspace_dir: str, state_type: StateType = StateType.CONTEXTUAL):
        self.task_id = task_id
        self.workspace_dir = Path(workspace_dir)
        self.state_type = state_type
        self.state_file = self.workspace_dir / ".state" / f"{task_id}_state.json"
        self.state_file.parent.mkdir(exist_ok=True, parents=True)
        
        # Initialize or load state
        self.state = self._load_or_init_state()
        
        # State evolution functions by type
        self.evolvers = {
            StateType.REALTIME: self._evolve_realtime,
            StateType.ADVERSARIAL: self._evolve_adversarial,
            StateType.RESOURCE: self._evolve_resource,
            StateType.CONTEXTUAL: self._evolve_contextual,
            StateType.PERSISTENT: self._evolve_persistent
        }
        
    def _load_or_init_state(self) -> TaskState:
        """Load existing state or initialize new"""
        if self.state_file.exists():
            with open(self.state_file) as f:
                data = json.load(f)
                # Reconstruct from dict
                state = TaskState(
                    task_id=data["task_id"],
                    state_type=StateType(data["state_type"]),
                    created_at=data["created_at"],
                    updated_at=data["updated_at"],
                    turn_history=[TurnState(**turn) for turn in data.get("turn_history", [])],
                    global_state=data.get("global_state", {}),
                    resource_limits=data.get("resource_limits", {}),
                    time_constraints=data.get("time_constraints", {}),
                    checkpoints=data.get("checkpoints", [])
                )
                return state
        else:
            now = datetime.now(timezone.utc).isoformat()
            return TaskState(
                task_id=self.task_id,
                state_type=self.state_type,
                created_at=now,
                updated_at=now
            )
    
    def save_state(self):
        """Persist state to disk"""
        self.state.updated_at = datetime.now(timezone.utc).isoformat()
        
        # Convert to dict for JSON serialization
        state_dict = {
            "task_id": self.state.task_id,
            "state_type": self.state.state_type.value,
            "created_at": self.state.created_at,
            "updated_at": self.state.updated_at,
            "turn_history": [asdict(turn) for turn in self.state.turn_history],
            "global_state": self.state.global_state,
            "resource_limits": self.state.resource_limits,
            "time_constraints": self.state.time_constraints,
            "checkpoints": self.state.checkpoints
        }
        
        with open(self.state_file, 'w') as f:
            json.dump(state_dict, f, indent=2)
    
    def record_turn(self, agent_role: str, action: Dict[str, Any], metrics: Optional[Dict[str, float]] = None):
        """Record a turn and evolve state accordingly"""
        turn_number = len(self.state.turn_history) + 1
        
        # Evolve state based on type
        state_changes = self.evolvers[self.state.state_type](action, turn_number)
        
        turn = TurnState(
            turn_number=turn_number,
            timestamp=datetime.now(timezone.utc).isoformat(),
            agent_role=agent_role,
            action_taken=action,
            state_changes=state_changes,
            metrics=metrics or {}
        )
        
        self.state.turn_history.append(turn)
        self.save_state()
        
        return state_changes
    
    def _evolve_realtime(self, action: Dict[str, Any], turn: int) -> Dict[str, Any]:
        """Evolve state for real-time tasks"""
        changes = {}
        
        # Simulate system load changes over time
        current_load = self.state.global_state.get("system_load", 50)
        if turn <= 3:
            new_load = min(100, current_load + 10)  # Load increases
        elif turn <= 6:
            new_load = min(100, current_load + 20)  # Spike
        else:
            # Load depends on actions taken
            if "circuit_breaker" in str(action):
                new_load = max(20, current_load - 30)
            else:
                new_load = min(100, current_load + 5)
        
        self.state.global_state["system_load"] = new_load
        changes["system_load"] = new_load
        
        # Simulate error rates based on load
        error_rate = min(50, new_load - 50) if new_load > 80 else 0
        self.state.global_state["error_rate"] = error_rate
        changes["error_rate"] = error_rate
        
        # Check for cascade failure
        if new_load >= 95 and turn > 5:
            self.state.global_state["cascade_failure"] = True
            changes["cascade_failure"] = True
            
        return changes
    
    def _evolve_adversarial(self, action: Dict[str, Any], turn: int) -> Dict[str, Any]:
        """Evolve state for adversarial tasks"""
        changes = {}
        
        # Track discovered backdoors
        backdoors = self.state.global_state.get("backdoors_found", [])
        
        # Check if action discovers a backdoor
        action_str = json.dumps(action).lower()
        backdoor_keywords = {
            "lodash_es": "npm_typosquatting",
            "node:18-alpine": "docker_poisoning",
            "deploy.yml": "github_action_malware",
            "build.sh": "build_script_exfil",
            "cryptominer": "cryptomining"
        }
        
        for keyword, backdoor_name in backdoor_keywords.items():
            if keyword in action_str and backdoor_name not in backdoors:
                backdoors.append(backdoor_name)
                changes[f"discovered_{backdoor_name}"] = True
        
        self.state.global_state["backdoors_found"] = backdoors
        changes["total_backdoors_found"] = len(backdoors)
        
        # Check removal order (critical for deadman switch)
        removed = self.state.global_state.get("backdoors_removed", [])
        correct_order = ["cryptomining", "build_script_exfil", "github_action_malware", 
                        "npm_typosquatting", "docker_poisoning"]
        
        if "remove" in action_str or "clean" in action_str:
            # Determine what's being removed
            for backdoor in backdoors:
                if backdoor not in removed and backdoor in action_str:
                    # Check if order is correct
                    expected_index = len(removed)
                    actual_index = correct_order.index(backdoor) if backdoor in correct_order else -1
                    
                    if actual_index == expected_index:
                        removed.append(backdoor)
                        changes[f"removed_{backdoor}"] = "correct_order"
                    else:
                        # Wrong order - trigger deadman switch
                        self.state.global_state["deadman_triggered"] = True
                        changes["deadman_triggered"] = True
                        changes["data_loss"] = "catastrophic"
        
        self.state.global_state["backdoors_removed"] = removed
        
        return changes
    
    def _evolve_resource(self, action: Dict[str, Any], turn: int) -> Dict[str, Any]:
        """Evolve state for resource-constrained tasks"""  
        changes = {}
        
        # Track resource consumption
        resources = {
            "api_calls": self.state.resource_limits.get("api_calls", 100),
            "memory_mb": self.state.resource_limits.get("memory_mb", 4096),
            "cpu_seconds": self.state.resource_limits.get("cpu_seconds", 300),
            "network_mb": self.state.resource_limits.get("network_mb", 1024)
        }
        
        # Deduct based on action
        action_str = json.dumps(action).lower()
        
        if "api" in action_str or "request" in action_str:
            resources["api_calls"] -= 1
            changes["api_calls_remaining"] = resources["api_calls"]
            
        if "process" in action_str or "analyze" in action_str:
            resources["cpu_seconds"] -= 10
            changes["cpu_seconds_remaining"] = resources["cpu_seconds"]
            
        if "download" in action_str or "fetch" in action_str:
            resources["network_mb"] -= 50
            changes["network_mb_remaining"] = resources["network_mb"]
        
        # Check for resource exhaustion
        for resource, value in resources.items():
            if value <= 0:
                self.state.global_state[f"{resource}_exhausted"] = True
                changes[f"{resource}_exhausted"] = True
                
        self.state.resource_limits = resources
        
        return changes
    
    def _evolve_contextual(self, action: Dict[str, Any], turn: int) -> Dict[str, Any]:
        """Evolve state based on context and history"""
        changes = {}
        
        # Build context from history
        context = {
            "turns_elapsed": turn,
            "actions_taken": len(self.state.turn_history),
            "last_action": self.state.turn_history[-1].action_taken if self.state.turn_history else None
        }
        
        # Pattern detection
        if turn > 3:
            recent_actions = [t.action_taken for t in self.state.turn_history[-3:]]
            
            # Detect loops
            if len(set(str(a) for a in recent_actions)) == 1:
                self.state.global_state["stuck_in_loop"] = True
                changes["stuck_in_loop"] = True
                
            # Detect progress
            if all("fix" in str(a) or "implement" in str(a) for a in recent_actions):
                self.state.global_state["making_progress"] = True
                changes["making_progress"] = True
        
        self.state.global_state["context"] = context
        return changes
    
    def _evolve_persistent(self, action: Dict[str, Any], turn: int) -> Dict[str, Any]:
        """Evolve persistent state (minimal changes)"""
        return {
            "turn": turn,
            "last_update": datetime.now(timezone.utc).isoformat()
        }
    
    def create_checkpoint(self, name: str, metadata: Optional[Dict[str, Any]] = None):
        """Create a checkpoint for rollback"""
        checkpoint = {
            "name": name,
            "turn": len(self.state.turn_history),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "global_state_snapshot": self.state.global_state.copy(),
            "metadata": metadata or {}
        }
        self.state.checkpoints.append(checkpoint)
        self.save_state()
        
    def rollback_to_checkpoint(self, name: str) -> bool:
        """Rollback state to a named checkpoint"""
        for checkpoint in reversed(self.state.checkpoints):
            if checkpoint["name"] == name:
                # Restore global state
                self.state.global_state = checkpoint["global_state_snapshot"].copy()
                
                # Trim turn history
                target_turn = checkpoint["turn"]
                self.state.turn_history = self.state.turn_history[:target_turn]
                
                self.save_state()
                return True
        return False
    
    def get_current_state(self) -> Dict[str, Any]:
        """Get current state summary"""
        return {
            "task_id": self.state.task_id,
            "state_type": self.state.state_type.value,
            "turn": len(self.state.turn_history),
            "global_state": self.state.global_state,
            "resource_limits": self.state.resource_limits,
            "last_action": self.state.turn_history[-1].action_taken if self.state.turn_history else None,
            "checkpoints": [cp["name"] for cp in self.state.checkpoints]
        }
    
    def inject_event(self, event: Dict[str, Any]):
        """Inject an external event into the state"""
        self.state.global_state["last_external_event"] = event
        self.state.global_state["external_event_time"] = datetime.now(timezone.utc).isoformat()
        
        # Process event based on type
        if event.get("type") == "system_failure":
            self.state.global_state["system_status"] = "degraded"
        elif event.get("type") == "attack_detected":
            self.state.global_state["security_alert"] = True
        elif event.get("type") == "resource_spike":
            for resource, value in event.get("resources", {}).items():
                if resource in self.state.resource_limits:
                    self.state.resource_limits[resource] = max(0, self.state.resource_limits[resource] - value)
        
        self.save_state()
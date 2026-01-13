"""Automation orchestrator."""

from typing import Dict, Any, List, Optional

from backend.automation.isolation.network_isolation import NetworkIsolation
from backend.automation.isolation.device_quarantine import DeviceQuarantine
from backend.automation.isolation.traffic_blocking import TrafficBlocking
from backend.automation.failover.backup_activator import BackupActivator
from backend.automation.failover.circuit_breaker import CircuitBreaker
from backend.automation.workflow.approval_workflow import ApprovalWorkflow, ApprovalStatus
from backend.common.logging import get_logger

logger = get_logger(__name__)


class AutomationOrchestrator:
    """Orchestrator for automation actions."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize automation orchestrator."""
        self.config = config or {}
        
        # Initialize components
        self.network_isolation = NetworkIsolation(config.get("isolation", {}))
        self.device_quarantine = DeviceQuarantine(config.get("quarantine", {}))
        self.traffic_blocking = TrafficBlocking(config.get("traffic_blocking", {}))
        self.backup_activator = BackupActivator(config.get("failover", {}))
        self.approval_workflow = ApprovalWorkflow(config.get("approval", {}))
        
        # Circuit breakers for different systems
        self.circuit_breakers = {
            "isolation": CircuitBreaker("isolation", failure_threshold=5),
            "failover": CircuitBreaker("failover", failure_threshold=3),
        }
    
    async def handle_threat(self, detection: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle detected threat with automated actions.
        
        Args:
            detection: Detection result
        
        Returns:
            Automation result
        """
        result = {
            "success": False,
            "actions": [],
            "approvals": [],
            "errors": [],
        }
        
        try:
            attack_type = detection.get("attack_type")
            severity = detection.get("severity", "medium")
            source_ip = detection.get("source_ip") or detection.get("ip")
            
            logger.warning(
                f"Handling threat: {attack_type} from {source_ip} "
                f"(severity: {severity})"
            )
            
            # Determine actions based on attack type and severity
            actions = self._determine_actions(attack_type, severity)
            
            # Execute actions (with approval if required)
            for action in actions:
                action_result = await self._execute_action(action, detection)
                result["actions"].append(action_result)
                
                if action_result.get("requires_approval"):
                    result["approvals"].append(action_result.get("approval_id"))
            
            # Check if any actions succeeded
            result["success"] = any(a.get("success") for a in result["actions"])
            
            logger.info(f"Threat handling completed: {len(result['actions'])} actions")
        
        except Exception as e:
            logger.error(f"Error handling threat: {e}", exc_info=True)
            result["errors"].append(str(e))
        
        return result
    
    def _determine_actions(
        self,
        attack_type: str,
        severity: str
    ) -> List[Dict[str, Any]]:
        """Determine actions to take based on attack type and severity."""
        actions = []
        
        # Always isolate network for high/critical severity
        if severity in ["high", "critical"]:
            actions.append({
                "type": "network_isolation",
                "auto_approve": severity == "critical",
            })
            
            actions.append({
                "type": "device_quarantine",
                "auto_approve": severity == "critical",
            })
        
        # Specific actions for attack types
        if attack_type == "ddos":
            actions.append({
                "type": "traffic_blocking",
                "auto_approve": True,
            })
        
        elif attack_type in ["ransomware", "scada_attack"]:
            actions.append({
                "type": "failover",
                "auto_approve": True,
            })
        
        elif attack_type == "insider_threat":
            actions.append({
                "type": "device_quarantine",
                "auto_approve": False,  # Always require approval for insider threats
            })
        
        return actions
    
    async def _execute_action(
        self,
        action: Dict[str, Any],
        detection: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute an automation action."""
        action_type = action["type"]
        auto_approve = action.get("auto_approve", False)
        
        result = {
            "type": action_type,
            "success": False,
            "requires_approval": False,
        }
        
        try:
            # Request approval if needed
            if not auto_approve and self.approval_workflow.require_approval:
                approval = await self.approval_workflow.request_approval(
                    action=action_type,
                    action_params=detection,
                    reason=f"{detection.get('attack_type')} attack detected",
                    severity=detection.get("severity", "medium"),
                    auto_approve=False
                )
                
                if approval.get("status") == "pending":
                    result["requires_approval"] = True
                    result["approval_id"] = approval.get("approval_id")
                    return result
            
            # Execute action
            if action_type == "network_isolation":
                isolation_result = await self.network_isolation.isolate(detection)
                result["success"] = isolation_result.get("success", False)
                result["details"] = isolation_result
            
            elif action_type == "device_quarantine":
                device_id = detection.get("source_ip") or detection.get("ip") or detection.get("user")
                if device_id:
                    quarantine_result = await self.device_quarantine.quarantine_device(
                        device_id=device_id,
                        reason=f"{detection.get('attack_type')} attack",
                        metadata=detection
                    )
                    result["success"] = quarantine_result
            
            elif action_type == "traffic_blocking":
                block_result = await self.traffic_blocking.block_traffic(
                    source_ip=detection.get("source_ip") or detection.get("ip"),
                    port=detection.get("port"),
                    protocol=detection.get("protocol", "tcp"),
                    reason=f"{detection.get('attack_type')} attack"
                )
                result["success"] = block_result
            
            elif action_type == "failover":
                system_name = detection.get("system") or "default"
                failover_result = await self.backup_activator.activate_backup(
                    system_name=system_name,
                    reason=f"{detection.get('attack_type')} attack"
                )
                result["success"] = failover_result.get("success", False)
                result["details"] = failover_result
        
        except Exception as e:
            logger.error(f"Error executing action {action_type}: {e}", exc_info=True)
            result["error"] = str(e)
        
        return result
    
    async def execute_approved_action(self, approval_id: str) -> Dict[str, Any]:
        """Execute an approved action."""
        approval = self.approval_workflow.get_approval(approval_id)
        
        if not approval:
            return {
                "success": False,
                "error": "Approval not found",
            }
        
        if approval["status"] != ApprovalStatus.APPROVED.value:
            return {
                "success": False,
                "error": f"Approval status is {approval['status']}",
            }
        
        # Execute the action
        action_type = approval["action"]
        action_params = approval["action_params"]
        
        return await self._execute_action(
            {"type": action_type, "auto_approve": True},
            action_params
        )

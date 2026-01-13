"""Alert escalation rules."""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from backend.common.logging import get_logger

logger = get_logger(__name__)


class EscalationRule:
    """Escalation rule."""
    
    def __init__(
        self,
        name: str,
        conditions: Dict[str, Any],
        actions: List[Dict[str, Any]],
        timeout_seconds: int = 300
    ):
        """
        Initialize escalation rule.
        
        Args:
            name: Rule name
            conditions: Conditions to match (severity, source, etc.)
            actions: Actions to take (channels, recipients)
            timeout_seconds: Timeout before escalation
        """
        self.name = name
        self.conditions = conditions
        self.actions = actions
        self.timeout_seconds = timeout_seconds
    
    def matches(self, alert: Dict[str, Any]) -> bool:
        """Check if rule matches alert."""
        for key, value in self.conditions.items():
            if alert.get(key) != value:
                return False
        return True


class EscalationManager:
    """Manager for alert escalation."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize escalation manager."""
        self.config = config or {}
        self.rules: List[EscalationRule] = []
        
        # Load rules from config
        if config and "rules" in config:
            for rule_config in config["rules"]:
                rule = EscalationRule(
                    name=rule_config.get("name", "default"),
                    conditions=rule_config.get("conditions", {}),
                    actions=rule_config.get("actions", []),
                    timeout_seconds=rule_config.get("timeout_seconds", 300)
                )
                self.rules.append(rule)
    
    def get_escalation_actions(
        self,
        alert: Dict[str, Any],
        level: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get escalation actions for alert.
        
        Args:
            alert: Alert dictionary
            level: Escalation level (0 = initial, 1+ = escalated)
        
        Returns:
            List of actions to take
        """
        actions = []
        
        for rule in self.rules:
            if rule.matches(alert):
                # Check if timeout has passed
                created_at = datetime.fromisoformat(alert.get("created_at", datetime.utcnow().isoformat()))
                elapsed = (datetime.utcnow() - created_at).total_seconds()
                
                if elapsed >= rule.timeout_seconds * (level + 1):
                    actions.extend(rule.actions)
        
        return actions
    
    def add_rule(self, rule: EscalationRule) -> None:
        """Add escalation rule."""
        self.rules.append(rule)
        logger.info(f"Escalation rule added: {rule.name}")

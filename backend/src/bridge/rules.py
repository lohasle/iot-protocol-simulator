"""
Bridge Rules Engine
Event-driven rule processing
"""

import asyncio
import json
import re
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from loguru import logger


class ConditionOperator(Enum):
    """Condition Operators"""
    EQUALS = "eq"
    NOT_EQUALS = "ne"
    GREATER_THAN = "gt"
    LESS_THAN = "lt"
    GREATER_THAN_OR_EQUAL = "gte"
    LESS_THAN_OR_EQUAL = "lte"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    REGEX = "regex"
    IN = "in"
    NOT_IN = "not_in"
    BETWEEN = "between"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"


class ActionType(Enum):
    """Action Types"""
    SEND_COMMAND = "send_command"
    PUBLISH_MESSAGE = "publish_message"
    SET_VALUE = "set_value"
    SEND_ALERT = "send_alert"
    LOG = "log"
    CALL_WEBHOOK = "webhook"
    DELAY = "delay"
    THROTTLE = "throttle"
    TRIGGER_RULE = "trigger_rule"
    CREATE_EVENT = "create_event"


@dataclass
class Condition:
    """Rule Condition"""
    field: str
    operator: ConditionOperator
    value: Any = None
    second_value: Any = None
    
    def evaluate(self, data: Any) -> bool:
        """Evaluate condition against data"""
        field_value = data
        for part in self.field.split('.'):
            if isinstance(field_value, dict):
                field_value = field_value.get(part)
            elif hasattr(field_value, part):
                field_value = getattr(field_value, part)
            else:
                field_value = None
                break
        
        try:
            if self.operator == ConditionOperator.EQUALS:
                return field_value == self.value
            elif self.operator == ConditionOperator.NOT_EQUALS:
                return field_value != self.value
            elif self.operator == ConditionOperator.GREATER_THAN:
                return field_value > self.value
            elif self.operator == ConditionOperator.LESS_THAN:
                return field_value < self.value
            elif self.operator == ConditionOperator.GREATER_THAN_OR_EQUAL:
                return field_value >= self.value
            elif self.operator == ConditionOperator.LESS_THAN_OR_EQUAL:
                return field_value <= self.value
            elif self.operator == ConditionOperator.CONTAINS:
                return str(self.value) in str(field_value)
            elif self.operator == ConditionOperator.REGEX:
                return bool(re.match(self.value, str(field_value)))
            elif self.operator == ConditionOperator.BETWEEN:
                return self.value <= field_value <= self.second_value
            elif self.operator == ConditionOperator.IS_NULL:
                return field_value is None
            elif self.operator == ConditionOperator.IS_NOT_NULL:
                return field_value is not None
        except Exception as e:
            logger.debug(f"Condition evaluation error: {e}")
            return False
        
        return False


@dataclass
class Action:
    """Rule Action"""
    type: ActionType
    params: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    
    async def execute(self, context: Dict[str, Any], executor: 'RulesEngine'):
        """Execute action"""
        if not self.enabled:
            return
        
        try:
            if self.type == ActionType.LOG:
                message = self.params.get("message", "Rule triggered")
                level = self.params.get("level", "info")
                logger.log(getattr(logger, level.upper()), f"[RULE] {message}")
            
            elif self.type == ActionType.PUBLISH_MESSAGE:
                topic = self.params.get("topic")
                payload = self.params.get("payload", {})
                logger.info(f"Publishing to {topic}: {payload}")
            
            elif self.type == ActionType.SEND_ALERT:
                severity = self.params.get("severity", "warning")
                title = self.params.get("title", "Rule Alert")
                message = self.params.get("message", "")
                logger.warning(f"[ALERT {severity}] {title}: {message}")
            
            elif self.type == ActionType.DELAY:
                delay = self.params.get("milliseconds", 0)
                await asyncio.sleep(delay / 1000)
            
            elif self.type == ActionType.CREATE_EVENT:
                event_type = self.params.get("type")
                logger.info(f"Creating event: {event_type}")
            
            elif self.type == ActionType.TRIGGER_RULE:
                rule_name = self.params.get("rule")
                await executor.trigger(rule_name, context)
            
            elif self.type == ActionType.WEBHOOK:
                url = self.params.get("url")
                method = self.params.get("method", "POST")
                logger.info(f"Calling webhook: {method} {url}")
            
        except Exception as e:
            logger.error(f"Action execution error: {e}")


@dataclass
class Rule:
    """Automation Rule"""
    name: str
    description: str = ""
    enabled: bool = True
    priority: int = 0
    conditions: List[Condition] = field(default_factory=list)
    condition_logic: str = "AND"
    actions: List[Action] = field(default_factory=list)
    cooldown_seconds: int = 0
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0
    
    def evaluate(self, data: Any) -> bool:
        """Evaluate all conditions"""
        if not self.enabled:
            return False
        
        if self.last_triggered and self.cooldown_seconds > 0:
            if datetime.utcnow() - self.last_triggered < timedelta(seconds=self.cooldown_seconds):
                return False
        
        if not self.conditions:
            return True
        
        if self.condition_logic == "AND":
            return all(c.evaluate(data) for c in self.conditions)
        elif self.condition_logic == "OR":
            return any(c.evaluate(data) for c in self.conditions)
        
        return False


class RulesEngine:
    """Rules Processing Engine"""
    
    def __init__(self):
        self.rules: Dict[str, Rule] = {}
        self._running = False
        self._variables: Dict[str, Any] = {}
        self._stats = {
            "rules_triggered": 0,
            "conditions_evaluated": 0,
            "actions_executed": 0,
            "errors": 0
        }
    
    def add_rule(self, rule: Rule):
        """Add a rule"""
        self.rules[rule.name] = rule
        logger.info(f"Added rule: {rule.name}")
    
    def remove_rule(self, name: str):
        """Remove a rule"""
        if name in self.rules:
            del self.rules[name]
    
    def get_rule(self, name: str) -> Optional[Rule]:
        """Get rule by name"""
        return self.rules.get(name)
    
    def list_rules(self) -> List[Dict]:
        """List all rules"""
        return [
            {
                "name": name,
                "enabled": rule.enabled,
                "priority": rule.priority,
                "conditions": len(rule.conditions),
                "actions": len(rule.actions),
                "trigger_count": rule.trigger_count
            }
            for name, rule in self.rules.items()
        ]
    
    def set_variable(self, name: str, value: Any):
        """Set engine variable"""
        self._variables[name] = value
    
    def get_variable(self, name: str, default: Any = None) -> Any:
        """Get engine variable"""
        return self._variables.get(name, default)
    
    async def start(self):
        """Start rules engine"""
        self._running = True
        logger.info(f"Rules engine started with {len(self.rules)} rules")
    
    def stop(self):
        """Stop rules engine"""
        self._running = False
        logger.info("Rules engine stopped")
    
    async def evaluate_data(self, data: Any, source: str = "unknown"):
        """Evaluate data against all rules"""
        if not self._running:
            return
        
        context = {
            "data": data,
            "source": source,
            "variables": self._variables,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        for name, rule in sorted(self.rules.items(), key=lambda x: -x[1].priority):
            if rule.evaluate(data):
                self._stats["rules_triggered"] += 1
                rule.trigger_count += 1
                rule.last_triggered = datetime.utcnow()
                
                logger.info(f"Rule triggered: {name}")
                
                for action in rule.actions:
                    await action.execute(context, self)
                    self._stats["actions_executed"] += 1
    
    async def trigger(self, rule_name: str, context: Dict[str, Any] = None):
        """Manually trigger a rule"""
        rule = self.rules.get(rule_name)
        if not rule or not rule.enabled:
            return
        
        rule.trigger_count += 1
        rule.last_triggered = datetime.utcnow()
        
        ctx = context or {"data": None, "source": "manual", "variables": self._variables}
        
        for action in rule.actions:
            await action.execute(ctx, self)
            self._stats["actions_executed"] += 1
    
    def get_stats(self) -> dict:
        """Get engine statistics"""
        return {
            **self._stats,
            "total_rules": len(self.rules),
            "enabled_rules": sum(1 for r in self.rules.values() if r.enabled)
        }


# Factory function
def create_rules_engine() -> RulesEngine:
    """Create a new rules engine"""
    return RulesEngine()

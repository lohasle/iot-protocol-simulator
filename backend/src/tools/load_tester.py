"""
Load Tester
Performance and load testing for IoT protocols
"""

import asyncio
import json
import random
import statistics
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from loguru import logger


class LoadTestType(Enum):
    """Load Test Types"""
    RAMP_UP = "ramp_up"
    SPIKE = "spike"
    SOAK = "soak"
    STRESS = "stress"
    BURST = "burst"


@dataclass
class LoadTestConfig:
    """Load Test Configuration"""
    test_type: LoadTestType
    target_protocol: str
    target_host: str
    target_port: int
    initial_users: int = 10
    max_users: int = 1000
    ramp_up_duration_seconds: int = 60
    test_duration_seconds: int = 300
    think_time_ms: int = 100
    burst_size: int = 10
    
    def to_dict(self) -> dict:
        return {
            "test_type": self.test_type.value,
            "target_protocol": self.target_protocol,
            "target_host": self.target_host,
            "target_port": self.target_port,
            "initial_users": self.initial_users,
            "max_users": self.max_users,
            "ramp_up_duration_seconds": self.ramp_up_duration_seconds,
            "test_duration_seconds": self.test_duration_seconds,
            "think_time_ms": self.think_time_ms,
            "burst_size": self.burst_size
        }


@dataclass
class LoadTestResult:
    """Load Test Result"""
    test_id: str
    config: LoadTestConfig
    start_time: datetime
    end_time: Optional[datetime]
    
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time_ms: float = 0.0
    min_response_time_ms: float = 0.0
    max_response_time_ms: float = 0.0
    p95_response_time_ms: float = 0.0
    p99_response_time_ms: float = 0.0
    requests_per_second: float = 0.0
    errors_per_second: float = 0.0
    
    response_times: List[float] = field(default_factory=list)
    throughput_history: List[dict] = field(default_factory=list)
    error_history: List[dict] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "test_id": self.test_id,
            "config": self.config.to_dict(),
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "metrics": {
                "total_requests": self.total_requests,
                "successful_requests": self.successful_requests,
                "failed_requests": self.failed_requests,
                "success_rate": self.successful_requests / max(1, self.total_requests) * 100,
                "avg_response_time_ms": self.avg_response_time_ms,
                "min_response_time_ms": self.min_response_time_ms,
                "max_response_time_ms": self.max_response_time_ms,
                "p95_response_time_ms": self.p95_response_time_ms,
                "p99_response_time_ms": self.p99_response_time_ms,
                "requests_per_second": self.requests_per_second,
                "errors_per_second": self.errors_per_second
            },
            "samples": len(self.response_times)
        }


class LoadTester:
    """Load Testing Engine"""
    
    def __init__(self):
        self._running = False
        self._current_test: Optional[LoadTestResult] = None
        self._test_id: Optional[str] = None
        self._users: List[asyncio.Task] = []
        
        # Protocol handlers
        self._handlers = {
            "mqtt": self._handle_mqtt,
            "tcp": self._handle_tcp,
            "http": self._handle_http,
            "modbus": self._handle_modbus
        }
    
    async def start_test(self, config: LoadTestConfig) -> str:
        """Start load test"""
        import hashlib
        self._test_id = hashlib.md5(f"{datetime.utcnow().isoformat()}".encode()).hexdigest()[:12]
        
        self._current_test = LoadTestResult(
            test_id=self._test_id,
            config=config,
            start_time=datetime.utcnow(),
            end_time=None
        )
        
        self._running = True
        logger.info(f"Starting load test: {self._test_id}")
        
        # Start test based on type
        if config.test_type == LoadTestType.RAMP_UP:
            await self._ramp_up_test(config)
        elif config.test_type == LoadTestType.SPIKE:
            await self._spike_test(config)
        elif config.test_type == LoadTestType.SOAK:
            await self._soak_test(config)
        elif config.test_type == LoadTestType.STRESS:
            await self._stress_test(config)
        elif config.test_type == LoadTestType.BURST:
            await self._burst_test(config)
        
        # Calculate final metrics
        self._calculate_metrics()
        self._current_test.end_time = datetime.utcnow()
        
        logger.info(f"Load test completed: {self._test_id}")
        return self._test_id
    
    def stop_test(self):
        """Stop current test"""
        self._running = False
        for user in self._users:
            user.cancel()
        self._users.clear()
    
    async def _ramp_up_test(self, config: LoadTestConfig):
        """Ramp up load test"""
        ramp_steps = 10
        users_per_step = (config.max_users - config.initial_users) // ramp_steps
        step_duration = config.ramp_up_duration_seconds // ramp_steps
        
        current_users = config.initial_users
        
        # Ramp up phase
        for _ in range(ramp_steps):
            if not self._running:
                break
            
            current_users += users_per_step
            await self._spawn_users(current_users, config)
            await asyncio.sleep(step_duration)
        
        # Sustained phase
        await asyncio.sleep(config.test_duration_seconds - config.ramp_up_duration_seconds)
    
    async def _spike_test(self, config: LoadTestConfig):
        """Spike load test"""
        # Initial low load
        await self._spawn_users(config.initial_users, config)
        await asyncio.sleep(30)
        
        # Spike to max
        if self._running:
            await self._spawn_users(config.max_users, config)
            await asyncio.sleep(config.test_duration_seconds // 3)
        
        # Cool down
        if self._running:
            remaining = self._users[::2]
            self._users = remaining
            await asyncio.sleep(config.test_duration_seconds * 2 // 3)
    
    async def _soak_test(self, config: LoadTestConfig):
        """Soak/ endurance test"""
        users = config.max_users // 2
        await self._spawn_users(users, config)
        await asyncio.sleep(config.test_duration_seconds)
    
    async def _stress_test(self, config: LoadTestConfig):
        """Stress test to failure"""
        users = config.initial_users
        
        while users <= config.max_users and self._running:
            await self._spawn_users(users, config)
            await asyncio.sleep(config.test_duration_seconds // 5)
            users += config.max_users // 5
    
    async def _burst_test(self, config: LoadTestConfig):
        """Burst traffic test"""
        for _ in range(config.test_duration_seconds // 10):
            if not self._running:
                break
            
            # Burst
            await self._spawn_users(config.burst_size, config)
            await asyncio.sleep(1)
            
            # Cooldown
            self._users = self._users[:-config.burst_size // 2]
            await asyncio.sleep(9)
    
    async def _spawn_users(self, count: int, config: LoadTestConfig):
        """Spawn virtual users"""
        # Remove excess users
        while len(self._users) > count:
            self._users.pop().cancel()
        
        # Add new users
        while len(self._users) < count:
            task = asyncio.create_task(
                self._virtual_user(config)
            )
            self._users.append(task)
    
    async def _virtual_user(self, config: LoadTestConfig):
        """Virtual user simulation"""
        while self._running:
            try:
                # Execute request
                start = datetime.utcnow()
                handler = self._handlers.get(config.target_protocol, self._handle_generic)
                success = await handler(config)
                end = datetime.utcnow()
                
                response_time = (end - start).total_seconds() * 1000
                
                # Record result
                if self._current_test:
                    self._current_test.total_requests += 1
                    self._current_test.response_times.append(response_time)
                    
                    if success:
                        self._current_test.successful_requests += 1
                    else:
                        self._current_test.failed_requests += 1
                
                # Think time
                await asyncio.sleep(config.think_time_ms / 1000)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.debug(f"User error: {e}")
    
    async def _handle_mqtt(self, config: LoadTestConfig) -> bool:
        """Simulate MQTT request"""
        await asyncio.sleep(random.uniform(5, 20))  # Simulated latency
        return random.random() > 0.05  # 95% success
    
    async def _handle_tcp(self, config: LoadTestConfig) -> bool:
        """Simulate TCP request"""
        await asyncio.sleep(random.uniform(1, 10))
        return random.random() > 0.02
    
    async def _handle_http(self, config: LoadTestConfig) -> bool:
        """Simulate HTTP request"""
        await asyncio.sleep(random.uniform(10, 50))
        return random.random() > 0.03
    
    async def _handle_modbus(self, config: LoadTestConfig) -> bool:
        """Simulate Modbus request"""
        await asyncio.sleep(random.uniform(2, 15))
        return random.random() > 0.01
    
    async def _handle_generic(self, config: LoadTestConfig) -> bool:
        """Generic handler"""
        await asyncio.sleep(random.uniform(1, 100))
        return random.random() > 0.05
    
    def _calculate_metrics(self):
        """Calculate test metrics"""
        if not self._current_test:
            return
        
        times = self._current_test.response_times
        
        if times:
            self._current_test.avg_response_time_ms = statistics.mean(times)
            self._current_test.min_response_time_ms = min(times)
            self._current_test.max_response_time_ms = max(times)
            
            sorted_times = sorted(times)
            self._current_test.p95_response_time_ms = sorted_times[int(len(sorted_times) * 0.95)]
            self._current_test.p99_response_time_ms = sorted_times[int(len(sorted_times) * 0.99)]
        
        if self._current_test.total_requests > 0:
            duration = (self._current_test.end_time - self._current_test.start_time).total_seconds()
            self._current_test.requests_per_second = self._current_test.total_requests / max(1, duration)
            self._current_test.errors_per_second = self._current_test.failed_requests / max(1, duration)
    
    def get_test_result(self, test_id: str = None) -> Optional[dict]:
        """Get test result"""
        if test_id == self._test_id and self._current_test:
            return self._current_test.to_dict()
        return None
    
    def get_current_status(self) -> dict:
        """Get current test status"""
        return {
            "running": self._running,
            "test_id": self._test_id,
            "active_users": len(self._users),
            "requests": self._current_test.total_requests if self._current_test else 0,
            "success_rate": (
                self._current_test.successful_requests / max(1, self._current_test.total_requests) * 100
                if self._current_test else 0
            )
        }
    
    def create_preset_tests(self) -> List[LoadTestConfig]:
        """Create preset test configurations"""
        return [
            LoadTestConfig(
                test_type=LoadTestType.RAMP_UP,
                target_protocol="mqtt",
                target_host="localhost",
                target_port=1883,
                initial_users=50,
                max_users=500,
                ramp_up_duration_seconds=120,
                test_duration_seconds=300
            ),
            LoadTestConfig(
                test_type=LoadTestType.SPIKE,
                target_protocol="tcp",
                target_host="localhost",
                target_port=8080,
                initial_users=10,
                max_users=1000,
                test_duration_seconds=180
            ),
            LoadTestConfig(
                test_type=LoadTestType.SOAK,
                target_protocol="mqtt",
                target_host="localhost",
                target_port=1883,
                initial_users=100,
                max_users=100,
                test_duration_seconds=600
            )
        ]


# Factory function
def create_load_tester() -> LoadTester:
    """Create load tester"""
    return LoadTester()

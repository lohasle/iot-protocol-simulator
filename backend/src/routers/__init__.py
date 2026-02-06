# Re-export routers for easy import
from .devices import router as devices
from .packets import router as packets
from .protocols import router as protocols
from .simulation import router as simulation
from .metrics import router as metrics
from .alerts import router as alerts

__all__ = ["devices", "packets", "protocols", "simulation", "metrics", "alerts"]

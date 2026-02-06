# IoT Protocol Simulator

🌐 **World-class IoT Protocol Debugging Platform**

A comprehensive IoT protocol simulation platform supporting multiple industrial and IoT protocols with network simulation, fault injection, and real-time monitoring.

## ✨ Features

### 🔧 Protocol Simulation
- **Modbus TCP/RTU** - Complete protocol stack with device simulation
- **MQTT Broker + Client** - Full-featured message broker
- **OPC UA Server/Client** - Industrial interoperability standard
- **BACnet IP/MS-TP** - Building automation protocol
- **CoAP Server** - Constrained Application Protocol
- **TCP Connection** - Raw TCP simulation with connection pooling

### 🌉 Unified Bridge Engine
- Protocol-to-protocol bridging (Modbus → MQTT, OPC UA → BACnet, etc.)
- JSON/YAML mapping configurations
- Real-time data transformation
- Event-driven rules engine

### 📊 Network Simulation
- **1000+ Device Simulation** - High-scale load testing
- **Latency/Packet Loss** - Network condition simulation
- **Topology Visualization** - D3.js interactive network graph
- **Connection Pooling** - Efficient resource management

### 🛠️ Testing Tools
- **Packet Capturer** - Wireshark-style packet analysis
- **Fault Injector** - Network failure simulation
- **Traffic Replayer** - Record and playback traffic
- **Load Tester** - Performance and stress testing

### 📈 Real-time Monitoring
- **WebSocket Live Feed** - Sub-second latency updates
- **Protocol Status Dashboard** - Connection/message statistics
- **Alert System** - Threshold-based notifications
- **Metrics Visualization** - Throughput, latency, error rates

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 18+
- Python 3.11+

### Local Development

```bash
# Clone the repository
git clone https://github.com/your-org/iot-protocol-simulator.git
cd iot-protocol-simulator

# Start with Docker Compose
docker-compose up -d

# Or run separately
# Backend
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn src.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

### Access
- **Web UI**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **MQTT Broker**: mqtt://localhost:1883
- **Metrics**: http://localhost:9090

## 📁 Project Structure

```
iot-protocol-simulator/
├── backend/
│   ├── src/
│   │   ├── protocols/          # Protocol implementations
│   │   │   ├── modbus.py       # Modbus TCP/RTU
│   │   │   ├── mqtt.py         # MQTT Broker/Client
│   │   │   ├── opcua.py        # OPC UA Server
│   │   │   ├── bacnet.py       # BACnet IP
│   │   │   ├── coap.py         # CoAP Server
│   │   │   └── tcp.py          # TCP simulation
│   │   ├── bridge/             # Bridge engine
│   │   │   ├── engine.py       # Main bridge
│   │   │   ├── mapper.py       # Data mapping
│   │   │   ├── event_bus.py    # Redis/ZeroMQ bus
│   │   │   └── rules.py        # Rule engine
│   │   ├── simulation/         # Network simulation
│   │   │   ├── network.py      # Topology/load
│   │   │   └── latency.py      # Network conditions
│   │   ├── tools/              # Testing tools
│   │   │   ├── capturer.py     # Packet capture
│   │   │   ├── fault_injector.py
│   │   │   ├── replayer.py     # Traffic replay
│   │   │   └── load_tester.py  # Load testing
│   │   ├── routers/            # API endpoints
│   │   ├── models/              # Pydantic schemas
│   │   └── services/            # Business logic
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── protocols/       # Protocol panels
│   │   │   ├── topology/        # D3.js graphs
│   │   │   ├── debug/           # Packet capture
│   │   │   └── ...
│   │   ├── hooks/               # React hooks
│   │   │   └── useProtocol.ts
│   │   ├── services/
│   │   │   └── websocket.ts
│   │   └── pages/               # App pages
│   └── package.json
├── docker-compose.yml
└── README.md
```

## 📖 API Examples

### Start a Protocol Server

```python
# Start Modbus server
POST /api/v1/protocols/modbus/start
{
  "host": "0.0.0.0",
  "port": 502,
  "simulate_registers": true,
  "register_count": 100
}
```

### Create a Bridge

```python
# Create Modbus to MQTT bridge
POST /api/v1/bridge/rules
{
  "name": "modbus-to-mqtt",
  "mappings": [
    {
      "source_protocol": "modbus",
      "source_topic": "holding-registers",
      "target_protocol": "mqtt",
      "target_topic": "sensors/data",
      "transform": {
        "field_mappings": [
          {"source": "value", "target": "sensor_value", "type": "float"}
        ]
      }
    }
  ]
}
```

### Inject Fault

```python
# Inject 25% packet loss
POST /api/v1/faults
{
  "type": "packet_loss",
  "target": "network",
  "parameters": {"percent": 25},
  "probability": 0.3
}
```

## 🎨 UI Pages

| Page | Route | Description |
|------|-------|-------------|
| Dashboard | `/` | Real-time metrics & monitoring |
| Topology | `/topology` | Network visualization |
| Protocols | `/protocols` | Protocol configuration |
| Devices | `/devices` | Device management |
| Debug | `/debug` | Packet capture & analysis |
| Settings | `/settings` | System configuration |

## 🐳 Docker Services

```yaml
frontend:    # React UI (port 3000)
backend:     # FastAPI (port 8000)
redis:       # Event bus (port 6379)
mosquitto:   # MQTT Broker (port 1883)
postgres:    # Configuration DB (port 5432)
prometheus:  # Metrics (port 9090)
grafana:     # Dashboards (port 3100)
```

## ✅ Acceptance Criteria

- [x] Modbus/MQTT/OPC UA protocol simulation
- [x] Unified bridging (Modbus → MQTT, etc.)
- [x] 1000+ device simulation
- [x] Real-time monitoring dashboard
- [x] Fault injection capabilities
- [x] Docker one-click deployment

## 📝 License

MIT License - See LICENSE file

---

**Version**: 1.0.0  
**Last Updated**: 2026-02-06

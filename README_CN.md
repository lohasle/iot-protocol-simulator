# IoT 协议模拟器

<p align="center">
  <strong>🌐 世界级 IoT 协议调试平台</strong>
</p>

<p align="center">
  支持多种工业和 IoT 协议的综合模拟平台，提供网络模拟、故障注入和实时监控功能
</p>

<p align="center">
  <a href="#功能特性">功能特性</a> •
  <a href="#快速开始">快速开始</a> •
  <a href="#项目结构">项目结构</a> •
  <a href="#api示例">API示例</a>
</p>

---

## ✨ 功能特性

### 🔧 协议模拟

| 协议 | 说明 | 功能 |
|------|------|------|
| **Modbus TCP/RTU** | 完整协议栈 | 设备模拟 |
| **MQTT** | Broker + Client | 完整消息代理 |
| **OPC UA** | Server/Client | 工业互操作标准 |
| **BACnet** | IP/MS-TP | 楼宇自动化协议 |
| **CoAP** | Server | 受限应用协议 |
| **TCP** | 原始 TCP | 连接池模拟 |

### 🌉 统一桥接引擎

- 协议到协议桥接（Modbus → MQTT，OPC UA → BACnet 等）
- JSON/YAML 映射配置
- 实时数据转换
- 事件驱动规则引擎

### 📊 网络模拟

- **1000+ 设备模拟** - 大规模负载测试
- **延迟/丢包** - 网络条件模拟
- **拓扑可视化** - D3.js 交互式网络图
- **连接池** - 高效资源管理

### 🛠️ 测试工具

| 工具 | 功能 |
|------|------|
| **包捕获器** | Wireshark 风格包分析 |
| **故障注入器** | 网络故障模拟 |
| **流量重放器** | 录制和回放流量 |
| **负载测试器** | 性能和压力测试 |

### 📈 实时监控

- **WebSocket 实时推送** - 亚秒级延迟更新
- **协议状态仪表板** - 连接/消息统计
- **告警系统** - 阈值触发通知
- **指标可视化** - 吞吐量、延迟、错误率

---

## 🚀 快速开始

### 前置要求

- Docker & Docker Compose
- Node.js 18+
- Python 3.11+

### 本地开发

```bash
# 克隆仓库
git clone https://github.com/lohasle/iot-protocol-simulator.git
cd iot-protocol-simulator

# 使用 Docker Compose 启动
docker-compose up -d

# 或分别运行
# 后端
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn src.main:app --reload

# 前端
cd frontend
npm install
npm run dev
```

### 访问地址

| 服务 | 地址 |
|------|------|
| Web UI | http://localhost:3000 |
| API 文档 | http://localhost:8000/docs |
| MQTT Broker | mqtt://localhost:1883 |
| Metrics | http://localhost:9090 |

---

## 📁 项目结构

```
iot-protocol-simulator/
├── backend/
│   ├── src/
│   │   ├── protocols/          # 协议实现
│   │   │   ├── modbus.py       # Modbus TCP/RTU
│   │   │   ├── mqtt.py         # MQTT Broker/Client
│   │   │   ├── opcua.py        # OPC UA Server
│   │   │   ├── bacnet.py       # BACnet IP
│   │   │   ├── coap.py         # CoAP Server
│   │   │   └── tcp.py          # TCP 模拟
│   │   ├── bridge/             # 桥接引擎
│   │   │   ├── engine.py       # 主桥接
│   │   │   ├── mapper.py       # 数据映射
│   │   │   ├── event_bus.py    # Redis/ZeroMQ
│   │   │   └── rules.py        # 规则引擎
│   │   ├── simulation/         # 网络模拟
│   │   │   ├── network.py      # 拓扑/负载
│   │   │   └── latency.py      # 网络条件
│   │   ├── tools/              # 测试工具
│   │   │   ├── capturer.py     # 包捕获
│   │   │   ├── fault_injector.py
│   │   │   ├── replayer.py     # 流量重放
│   │   │   └── load_tester.py  # 负载测试
│   │   ├── routers/            # API 端点
│   │   ├── models/             # Pydantic 模型
│   │   └── services/           # 业务逻辑
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── protocols/      # 协议面板
│   │   │   ├── topology/       # D3.js 图形
│   │   │   └── debug/          # 包捕获
│   │   ├── hooks/
│   │   │   └── useProtocol.ts
│   │   ├── services/
│   │   │   └── websocket.ts
│   │   └── pages/
│   └── package.json
├── docker-compose.yml
└── README.md
```

---

## 📖 API 示例

### 启动协议服务器

```bash
# 启动 Modbus 服务器
POST /api/v1/protocols/modbus/start
{
  "host": "0.0.0.0",
  "port": 502,
  "simulate_registers": true,
  "register_count": 100
}
```

### 创建桥接

```bash
# 创建 Modbus 到 MQTT 桥接
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

### 注入故障

```bash
# 注入 25% 丢包率
POST /api/v1/faults
{
  "type": "packet_loss",
  "target": "network",
  "parameters": {"percent": 25},
  "probability": 0.3
}
```

---

## 🎨 UI 页面

| 页面 | 路由 | 说明 |
|------|------|------|
| 仪表板 | `/` | 实时指标和监控 |
| 拓扑 | `/topology` | 网络可视化 |
| 协议 | `/protocols` | 协议配置 |
| 设备 | `/devices` | 设备管理 |
| 调试 | `/debug` | 包捕获和分析 |
| 设置 | `/settings` | 系统配置 |

---

## 🐳 Docker 服务

```yaml
frontend:    # React UI (端口 3000)
backend:     # FastAPI (端口 8000)
redis:       # 事件总线 (端口 6379)
mosquitto:   # MQTT Broker (端口 1883)
postgres:    # 配置数据库 (端口 5432)
prometheus:  # 指标 (端口 9090)
grafana:     # 仪表板 (端口 3100)
```

---

## ✅ 功能清单

- [x] Modbus/MQTT/OPC UA 协议模拟
- [x] 统一桥接（Modbus → MQTT 等）
- [x] 1000+ 设备模拟
- [x] 实时监控仪表板
- [x] 故障注入能力
- [x] Docker 一键部署

---

## 📄 许可证

MIT License

---

**版本**: 1.0.0  
**最后更新**: 2026-02-14

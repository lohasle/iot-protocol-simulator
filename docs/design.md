# IoT 协议模拟器 - 详细设计文档

## 1. 系统架构

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        前端 (React + TypeScript)                 │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ Dashboard │  │  Devices  │  │ Topology │  │   Debug  │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
├─────────────────────────────────────────────────────────────────┤
│                    WebSocket / REST API                         │
├─────────────────────────────────────────────────────────────────┤
│                        后端 (FastAPI)                            │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │  协议引擎  │  │ 设备管理  │  │  数据存储  │  │ 任务调度  │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
├─────────────────────────────────────────────────────────────────┤
│                      数据存储 (PostgreSQL)                       │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 技术栈

#### 前端技术
- **框架**: React 18 + TypeScript
- **状态管理**: Redux Toolkit
- **UI 组件**: 自定义组件库 (基于 CSS Variables)
- **可视化**: D3.js, Chart.js
- **通信**: Socket.IO Client, Axios
- **样式**: CSS Modules + CSS Variables

#### 后端技术
- **框架**: FastAPI (Python 3.11+)
- **ORM**: SQLAlchemy 2.0
- **数据库**: PostgreSQL 15+
- **缓存**: Redis 7
- **消息队列**: Celery + RabbitMQ
- **异步**: asyncio, aiohttp

## 2. 数据模型

### 2.1 核心实体

```python
# 设备模型
class Device:
    id: str
    name: str
    type: DeviceType  # PLC, Sensor, Actuator, Gateway
    protocols: List[ProtocolType]
    status: DeviceStatus
    config: Dict
    created_at: datetime
    updated_at: datetime

# 协议模型
class Protocol:
    id: str
    type: ProtocolType  # ModbusTCP, ModbusRTU, OPCUA, MQTT, etc.
    config: ProtocolConfig
    enabled: bool

# 拓扑连接模型
class Connection:
    id: str
    source_device_id: str
    target_device_id: str
    latency_ms: int
    packet_loss_percent: float
    bandwidth_kbps: int
    status: ConnectionStatus

# 模拟任务模型
class SimulationTask:
    id: str
    device_id: str
    protocol_id: str
    schedule: str  # cron expression
    data_generator: DataGeneratorConfig
    status: TaskStatus
```

### 2.2 协议配置结构

```yaml
modbus_tcp:
  host: "192.168.1.10"
  port: 502
  unit_id: 1
  timeout_ms: 1000
  max_retries: 3

opcua:
  endpoint: "opc.tcp://localhost:4840"
  security_policy: "Basic256Sha256"
  security_mode: "SignAndEncrypt"
  certificate: null
  private_key: null

mqtt:
  broker_host: "localhost"
  broker_port: 1883
  client_id: "simulator"
  username: null
  password: null
  topic_prefix: "/iot/simulator"
  qos: 1
```

## 3. API 设计

### 3.1 REST API

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/v1/devices` | GET | 获取设备列表 |
| `/api/v1/devices` | POST | 创建设备 |
| `/api/v1/devices/{id}` | GET | 获取设备详情 |
| `/api/v1/devices/{id}` | PUT | 更新设备 |
| `/api/v1/devices/{id}` | DELETE | 删除设备 |
| `/api/v1/protocols` | GET | 获取协议列表 |
| `/api/v1/protocols/{id}/config` | PUT | 更新协议配置 |
| `/api/v1/topology` | GET | 获取拓扑结构 |
| `/api/v1/topology` | PUT | 更新拓扑 |
| `/api/v1/simulation/start` | POST | 开始模拟 |
| `/api/v1/simulation/stop` | POST | 停止模拟 |
| `/api/v1/packets` | GET | 获取数据包列表 |
| `/api/v1/metrics` | GET | 获取监控指标 |

### 3.2 WebSocket API

| 事件 | 方向 | 描述 |
|------|------|------|
| `connect` | Client→Server | 建立连接 |
| `device:status` | Server→Client | 设备状态更新 |
| `packet:capture` | Server→Client | 捕获的数据包 |
| `metric:update` | Server→Client | 实时指标更新 |
| `alert:new` | Server→Client | 新警报 |
| `simulation:log` | Server→Client | 模拟日志 |

## 4. 功能模块

### 4.1 协议引擎

#### Modbus 支持
- 功能码: FC01-FC04 (读写线圈/寄存器)
- 批量读取优化
- 响应超时处理

#### OPC UA 支持
- 安全模式: None, Sign, SignAndEncrypt
- 认证: Anonymous, UserName, Certificate
- 节点浏览和读写
- 订阅和发布

#### MQTT 支持
- Broker 模拟
- QoS 0/1/2
- Retained Messages
- Last Will and Testament

### 4.2 设备模拟

#### 数据生成器
- **随机模式**: 随机数值生成
- **周期模式**: 定时发送固定模式数据
- **脚本模式**: 自定义 Python 脚本
- **回放模式**: 播放历史数据

#### 故障注入
- 延迟注入 (0-1000ms)
- 丢包率 (0-100%)
- 数据损坏
- 连接断开
- 超时模拟

### 4.3 拓扑管理

#### 可视化特性
- 自动布局算法
- 缩放和漫游
- 节点分组
- 连接类型标识

#### 模拟网络条件
- 带宽限制
- 延迟模拟
- 丢包模拟
- 抖动 (Jitter)

## 5. 用户界面

### 5.1 设计原则

1. **一致性**: 统一的视觉语言和交互模式
2. **效率**: 快速访问常用功能
3. **反馈**: 清晰的系统状态反馈
4. **可访问性**: 支持键盘操作和辅助功能
5. **响应式**: 适配不同屏幕尺寸

### 5.2 主题配置

```css
:root {
  /* 暗黑主题 (默认) */
  --bg-primary: #0f172a;
  --bg-secondary: #1e293b;
  --text-primary: #f1f5f9;
  --accent: #6366f1;
}

/* 亮色主题 (可选) */
[data-theme="light"] {
  --bg-primary: #f8fafc;
  --bg-secondary: #ffffff;
  --text-primary: #0f172a;
  --accent: #4f46e5;
}
```

## 6. 部署架构

### 6.1 Docker Compose

```yaml
version: '3.8'

services:
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=http://localhost:8000

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/iot_sim
      - REDIS_URL=redis://cache:6379
    depends_on:
      - db
      - cache

  db:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=iot_sim

  cache:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

## 7. 开发计划

### Phase 1: 原型验证 (当前)
- [x] HTML/CSS/JS 原型
- [x] 交互流程设计
- [x] 设计规范文档

### Phase 2: 前端开发
- [ ] React 项目初始化
- [ ] 组件库开发
- [ ] 页面开发
- [ ] 状态管理

### Phase 3: 后端开发
- [ ] FastAPI 项目初始化
- [ ] 数据库模型
- [ ] API 开发
- [ ] 协议引擎

### Phase 4: 集成测试
- [ ] 单元测试
- [ ] 集成测试
- [ ] 性能测试
- [ ] 用户验收测试

## 8. 参考资料

### 设计灵感
- [ThingsBoard](https://thingsboard.io/) - IoT 平台参考
- [FUXA](https://www.fuxa.org/) - Web-based HMI/SCADA
- [Notion](https://www.notion.so/) - UI 设计风格

### 技术文档
- [Modbus Protocol](https://modbus.org/)
- [OPC UA Specification](https://opcfoundation.org/)
- [MQTT Protocol](https://mqtt.org/)

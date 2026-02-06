/**
 * IoT Protocol Simulator - Interactive Application
 * Handles UI interactions, navigation, drag-drop, and real-time updates
 */

// ========== Application State ==========
const AppState = {
    currentPage: 'dashboard',
    simulationRunning: false,
    selectedDevice: null,
    activeDevices: 24,
    msgRate: 1200,
    load: 34,
    packets: [],
    alerts: [],
    websocket: null
};

// ========== DOM Elements ==========
const elements = {};

// ========== Initialize Application ==========
document.addEventListener('DOMContentLoaded', () => {
    initializeElements();
    bindEvents();
    initializeCharts();
    initializeWebSocket();
    startRealTimeUpdates();
    loadSamplePackets();
});

function initializeElements() {
    // Navigation
    elements.navButtons = document.querySelectorAll('.nav-btn');
    elements.pages = document.querySelectorAll('.page');

    // Panels
    elements.panelToggles = document.querySelectorAll('.panel-toggle');
    elements.deviceItems = document.querySelectorAll('.device-item');

    // Toolbar actions
    elements.playButton = document.querySelector('[title="运行模拟"]');
    elements.stopButton = document.querySelector('[title="停止模拟"]');

    // Dashboard metrics
    elements.activeDevices = document.getElementById('active-devices');
    elements.msgRate = document.getElementById('msg-rate');
    elements.load = document.getElementById('load');

    // Debug controls
    elements.btnStartCapture = document.getElementById('btnStartCapture');
    elements.btnStopCapture = document.getElementById('btnStopCapture');
    elements.btnClear = document.getElementById('btnClear');
    elements.packetList = document.getElementById('packetList');
    elements.filterInput = document.querySelector('.filter-input');

    // Device modeling
    elements.deviceCanvas = document.getElementById('deviceCanvas');
    elements.paletteItems = document.querySelectorAll('.palette-item');

    // Connection status
    elements.wsStatus = document.getElementById('ws-status');
}

function bindEvents() {
    // Navigation
    elements.navButtons.forEach(btn => {
        btn.addEventListener('click', () => switchPage(btn.dataset.page));
    });

    // Panel toggles
    elements.panelToggles.forEach(toggle => {
        toggle.addEventListener('click', () => togglePanel(toggle));
    });

    // Device selection
    elements.deviceItems.forEach(item => {
        item.addEventListener('click', () => selectDevice(item));
    });

    // Drag and drop for palette items
    elements.paletteItems.forEach(item => {
        item.addEventListener('dragstart', handleDragStart);
        item.addEventListener('dragend', handleDragEnd);
    });

    // Device canvas drop zone
    if (elements.deviceCanvas) {
        elements.deviceCanvas.addEventListener('dragover', handleDragOver);
        elements.deviceCanvas.addEventListener('drop', handleDrop);
    }

    // Debug controls
    if (elements.btnStartCapture) {
        elements.btnStartCapture.addEventListener('click', startCapture);
    }
    if (elements.btnStopCapture) {
        elements.btnStopCapture.addEventListener('click', stopCapture);
    }
    if (elements.btnClear) {
        elements.btnClear.addEventListener('click', clearPackets);
    }

    // Filter input
    if (elements.filterInput) {
        elements.filterInput.addEventListener('input', filterPackets);
    }

    // Simulation controls
    if (elements.playButton) {
        elements.playButton.addEventListener('click', toggleSimulation);
    }
    if (elements.stopButton) {
        elements.stopButton.addEventListener('click', stopSimulation);
    }

    // Tab buttons in comparison card
    document.querySelectorAll('.btn-tab').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.btn-tab').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
        });
    });

    // Add device button
    document.querySelector('.btn-add-device')?.addEventListener('click', showAddDeviceModal);

    // Topology node interactions
    document.querySelectorAll('.topology-node').forEach(node => {
        node.addEventListener('click', () => selectTopologyNode(node));
    });

    // Protocol selector
    document.querySelectorAll('.protocol-tab').forEach(tab => {
        tab.addEventListener('click', () => switchProtocolTab(tab));
    });
}

// ========== WebSocket Connection ==========
function initializeWebSocket() {
    const wsUrl = `ws://${window.location.hostname}:8000/ws`;

    try {
        AppState.websocket = new WebSocket(wsUrl);

        AppState.websocket.onopen = () => {
            console.log('WebSocket connected');
            updateConnectionStatus('connected');
            sendWsMessage({ type: 'subscribe', channels: ['metrics', 'packets', 'alerts'] });
        };

        AppState.websocket.onclose = () => {
            console.log('WebSocket disconnected');
            updateConnectionStatus('disconnected');
            setTimeout(initializeWebSocket, 3000);
        };

        AppState.websocket.onerror = (error) => {
            console.error('WebSocket error:', error);
            updateConnectionStatus('error');
        };

        AppState.websocket.onmessage = (event) => {
            handleWsMessage(JSON.parse(event.data));
        };
    } catch (error) {
        console.warn('WebSocket connection failed, running in standalone mode');
        updateConnectionStatus('offline');
    }
}

function updateConnectionStatus(status) {
    if (elements.wsStatus) {
        const statusText = {
            connected: '🟢 已连接',
            disconnected: '🔴 断开',
            connecting: '🟡 连接中...',
            error: '🔴 错误',
            offline: '⚪ 离线模式'
        };
        elements.wsStatus.textContent = statusText[status] || status;
        elements.wsStatus.className = `ws-status ${status}`;
    }
}

function sendWsMessage(message) {
    if (AppState.websocket && AppState.websocket.readyState === WebSocket.OPEN) {
        AppState.websocket.send(JSON.stringify(message));
    }
}

function handleWsMessage(data) {
    switch (data.type) {
        case 'metric':
            updateMetricValue(data.metric, data.value);
            break;
        case 'packet':
            addPacketToList(data.packet);
            break;
        case 'alert':
            addAlert(data.alert);
            break;
        case 'device_status':
            updateDeviceStatus(data.device);
            break;
        default:
            console.log('Unknown message type:', data.type);
    }
}

function updateMetricValue(metric, value) {
    switch (metric) {
        case 'active_devices':
            AppState.activeDevices = value;
            if (elements.activeDevices) elements.activeDevices.textContent = value;
            break;
        case 'msg_rate':
            AppState.msgRate = value;
            const formatted = value >= 1000 ? (value / 1000).toFixed(1) + 'K' : value;
            if (elements.msgRate) elements.msgRate.textContent = formatted;
            break;
        case 'load':
            AppState.load = value;
            if (elements.load) {
                elements.load.textContent = value + '%';
                elements.load.style.color = value > 80 ? 'var(--error)' : 'var(--text-primary)';
            }
            break;
    }
}

function updateDeviceStatus(device) {
    const deviceEl = document.querySelector(`[data-device-id="${device.id}"]`);
    if (deviceEl) {
        const statusDot = deviceEl.querySelector('.device-status-indicator');
        if (statusDot) {
            statusDot.style.background = device.status === 'online' ? 'var(--success)' : 'var(--error)';
        }
    }
}

function addAlert(alert) {
    AppState.alerts.unshift({ ...alert, time: '刚刚' });
    if (AppState.alerts.length > 10) AppState.alerts.pop();
    renderAlerts();
}

function renderAlerts() {
    const alertList = document.querySelector('.alert-list');
    if (!alertList) return;

    const icons = { critical: '🚨', warning: '⚠️', info: 'ℹ️', success: '✅' };

    alertList.innerHTML = AppState.alerts.map(alert => `
        <div class="alert-item ${alert.type}">
            <span class="alert-icon">${icons[alert.type] || 'ℹ️'}</span>
            <div class="alert-content">
                <span class="alert-title">${alert.title}</span>
                <span class="alert-desc">${alert.description}</span>
            </div>
            <span class="alert-time">${alert.time}</span>
        </div>
    `).join('');
}

// ========== Page Navigation ==========
function switchPage(pageName) {
    elements.navButtons.forEach(btn => {
        btn.classList.toggle('active', btn.dataset.page === pageName);
    });

    elements.pages.forEach(page => {
        page.classList.toggle('active', page.id === `page-${pageName}`);
    });

    AppState.currentPage = pageName;

    sendWsMessage({ type: 'navigation', page: pageName });

    if (pageName === 'dashboard') {
        refreshDashboard();
    } else if (pageName === 'topology') {
        initializeTopology();
    } else if (pageName === 'debug') {
        initializeDebugView();
    } else if (pageName === 'devices') {
        initializeDevicesView();
    }
}

function switchProtocolTab(tab) {
    document.querySelectorAll('.protocol-tab').forEach(t => t.classList.remove('active'));
    tab.classList.add('active');

    const protocol = tab.dataset.protocol;
    const protocolContent = document.querySelector('.protocol-content');
    if (protocolContent) {
        const configs = {
            modbus: `<div class="config-section"><h4>Modbus TCP</h4>
                <div class="form-group"><label>从站地址</label><input type="text" value="1" class="form-input"></div>
                <div class="form-group"><label>端口</label><input type="number" value="502" class="form-input"></div>
            </div>`,
            mqtt: `<div class="config-section"><h4>MQTT</h4>
                <div class="form-group"><label>Broker</label><input type="text" value="localhost" class="form-input"></div>
                <div class="form-group"><label>端口</label><input type="number" value="1883" class="form-input"></div>
            </div>`,
            opcua: `<div class="config-section"><h4>OPC UA</h4>
                <div class="form-group"><label>端点</label><input type="text" value="opc.tcp://localhost:4840" class="form-input"></div>
            </div>`,
            bacnet: `<div class="config-section"><h4>BACnet</h4>
                <div class="form-group"><label>设备ID</label><input type="number" value="1001" class="form-input"></div>
            </div>`,
            coap: `<div class="config-section"><h4>CoAP</h4>
                <div class="form-group"><label>服务器</label><input type="text" value="localhost" class="form-input"></div>
            </div>`
        };
        protocolContent.innerHTML = configs[protocol] || '<p>请选择协议</p>';
    }
}

// ========== Panel Toggles ==========
function togglePanel(toggle) {
    const panel = toggle.closest('.panel');
    const content = panel.querySelector('.panel-content');
    const isExpanded = !panel.classList.contains('collapsed');

    if (isExpanded) {
        panel.classList.add('collapsed');
        content.style.display = 'none';
        toggle.textContent = '+';
    } else {
        panel.classList.remove('collapsed');
        content.style.display = 'block';
        toggle.textContent = '−';
    }
}

// ========== Device Selection ==========
function selectDevice(item) {
    elements.deviceItems.forEach(i => i.classList.remove('selected'));
    item.classList.add('selected');
    AppState.selectedDevice = item.dataset.id;
    showDeviceProperties(item);

    sendWsMessage({ type: 'device_select', deviceId: item.dataset.id });
}

function showDeviceProperties(deviceItem) {
    const propertiesPanel = document.querySelector('.device-properties');
    if (propertiesPanel) {
        propertiesPanel.innerHTML = `
            <h4>设备属性</h4>
            <div class="property-item"><span class="label">名称:</span><span class="value">${deviceItem.querySelector('.device-name')?.textContent || deviceItem.dataset.id}</span></div>
            <div class="property-item"><span class="label">类型:</span><span class="value">${deviceItem.dataset.type || 'Unknown'}</span></div>
            <div class="property-item"><span class="label">状态:</span><span class="value status-online">在线</span></div>
            <div class="property-item"><span class="label">地址:</span><span class="value">192.168.1.${Math.floor(Math.random() * 255)}</span></div>
        `;
    }
}

// ========== Drag and Drop ==========
function handleDragStart(e) {
    e.dataTransfer.setData('deviceType', e.target.dataset.deviceType);
    e.dataTransfer.setData('icon', e.target.querySelector('.palette-icon')?.textContent);
    e.target.classList.add('dragging');
}

function handleDragEnd(e) {
    e.target.classList.remove('dragging');
}

function handleDragOver(e) {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'copy';
}

function handleDrop(e) {
    e.preventDefault();
    const deviceType = e.dataTransfer.getData('deviceType');
    const icon = e.dataTransfer.getData('icon');

    if (deviceType && elements.deviceCanvas) {
        createDeviceOnCanvas(deviceType, e.offsetX, e.offsetY, icon);
    }
}

function createDeviceOnCanvas(type, x, y, icon = '📦') {
    const canvas = elements.deviceCanvas;
    const placeholder = canvas.querySelector('.canvas-placeholder');

    if (placeholder) {
        placeholder.remove();
    }

    const deviceId = `device-${Date.now()}`;
    const deviceEl = document.createElement('div');
    deviceEl.className = 'device-on-canvas';
    deviceEl.dataset.deviceId = deviceId;
    deviceEl.dataset.deviceType = type;
    deviceEl.style.cssText = `position: absolute; left: ${x}px; top: ${y}px; width: 100px; height: 100px; background: var(--bg-primary); border: 2px solid var(--primary); border-radius: 8px; display: flex; flex-direction: column; align-items: center; justify-content: center; cursor: move; transition: all 0.2s ease; user-select: none;`;

    const labels = { plc: 'PLC', sensor: '传感器', actuator: '执行器', gateway: '网关', server: '服务器' };
    const protocols = { plc: 'Modbus, BACnet', sensor: 'MQTT, CoAP', actuator: 'Modbus, OPC UA', gateway: '多协议', server: 'OPC UA' };

    deviceEl.innerHTML = `
        <span style="font-size: 28px;">${icon}</span>
        <span style="font-size: 12px; margin-top: 8px; font-weight: 500;">${labels[type] || type}</span>
        <span style="font-size: 10px; color: var(--text-secondary); margin-top: 4px;">${protocols[type] || ''}</span>
        <span class="device-status-indicator" style="position: absolute; top: 6px; right: 6px; width: 8px; height: 8px; border-radius: 50%; background: var(--success);"></span>
    `;

    deviceEl.addEventListener('mouseenter', () => {
        deviceEl.style.boxShadow = '0 0 20px var(--primary-muted)';
        deviceEl.style.transform = 'scale(1.05)';
    });

    deviceEl.addEventListener('mouseleave', () => {
        deviceEl.style.boxShadow = 'none';
        deviceEl.style.transform = 'scale(1)';
    });

    deviceEl.addEventListener('click', () => {
        document.querySelectorAll('.device-on-canvas').forEach(d => d.style.borderColor = 'var(--primary)');
        deviceEl.style.borderColor = 'var(--accent)';
        showDeviceProperties(deviceEl);
    });

    makeElementDraggable(deviceEl);

    sendWsMessage({ type: 'device_create', device: { id: deviceId, type, x, y } });

    canvas.appendChild(deviceEl);
}

function makeElementDraggable(el) {
    let isDragging = false;
    let startX, startY, initialX, initialY;

    el.addEventListener('mousedown', startDrag);

    function startDrag(e) {
        if (e.button !== 0) return;
        isDragging = true;
        startX = e.clientX;
        startY = e.clientY;
        initialX = el.offsetLeft;
        initialY = el.offsetTop;
        el.style.zIndex = '100';
        document.addEventListener('mousemove', drag);
        document.addEventListener('mouseup', stopDrag);
    }

    function drag(e) {
        if (!isDragging) return;
        const dx = e.clientX - startX;
        const dy = e.clientY - startY;
        el.style.left = `${initialX + dx}px`;
        el.style.top = `${initialY + dy}px`;
        sendWsMessage({ type: 'device_move', deviceId: el.dataset.deviceId, x: initialX + dx, y: initialY + dy });
    }

    function stopDrag() {
        isDragging = false;
        el.style.zIndex = '';
        document.removeEventListener('mousemove', drag);
        document.removeEventListener('mouseup', stopDrag);
    }
}

// ========== Charts ==========
function initializeCharts() {
    const flowCanvas = document.getElementById('flowChart');
    if (flowCanvas) {
        drawFlowChart(flowCanvas);
    }
    initializeThroughputChart();
}

function drawFlowChart(canvas) {
    const ctx = canvas.getContext('2d');
    const width = canvas.parentElement.clientWidth || 400;
    const height = 200;
    canvas.width = width;
    canvas.height = height;
    let offset = 0;

    function animate() {
        ctx.clearRect(0, 0, width, height);
        ctx.strokeStyle = 'rgba(99, 102, 241, 0.1)';
        ctx.lineWidth = 1;

        for (let x = 0; x < width; x += 40) {
            ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, height); ctx.stroke();
        }
        for (let y = 0; y < height; y += 40) {
            ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(width, y); ctx.stroke();
        }

        ctx.strokeStyle = '#6366f1';
        ctx.lineWidth = 2;
        ctx.setLineDash([10, 10]);
        ctx.lineDashOffset = -offset;

        for (let y = 30; y < height; y += 50) {
            ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(width, y); ctx.stroke();
        }

        const nodePositions = [
            { x: 50, y: 50, icon: '🏭' },
            { x: width / 2, y: 50, icon: '🌉' },
            { x: width - 100, y: 100, icon: '☁️' },
            { x: width / 2, y: 150, icon: '📊' }
        ];

        nodePositions.forEach(node => {
            ctx.fillStyle = '#1e293b';
            ctx.beginPath(); ctx.arc(node.x, node.y, 25, 0, Math.PI * 2); ctx.fill();
            ctx.strokeStyle = '#6366f1'; ctx.lineWidth = 2; ctx.stroke();
        });

        offset = (offset + 1) % 20;
        requestAnimationFrame(animate);
    }

    animate();
}

function initializeThroughputChart() {
    const chartContainer = document.getElementById('throughputChart');
    if (!chartContainer) return;

    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('width', '100%');
    svg.setAttribute('height', '100%');
    svg.setAttribute('viewBox', '0 0 400 150');
    svg.style.overflow = 'visible';

    const data = Array.from({ length: 20 }, () => Math.random() * 100);
    const area = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');

    function updateChart() {
        const width = 400;
        const height = 150;
        const padding = 20;

        data.shift();
        data.push(Math.random() * 100 + (AppState.simulationRunning ? 50 : 0));

        const areaPoints = data.map((value, index) => {
            const x = (index / (data.length - 1)) * (width - padding * 2) + padding;
            const y = height - (value / 150) * (height - padding * 2) - padding;
            return `${x},${y}`;
        });

        area.setAttribute('d', `M${padding},${height - padding} L${areaPoints.join(' L')} L${width - padding},${height - padding} Z`);
        area.setAttribute('fill', 'rgba(99, 102, 241, 0.2)');

        const linePoints = data.map((value, index) => {
            const x = (index / (data.length - 1)) * (width - padding * 2) + padding;
            const y = height - (value / 150) * (height - padding * 2) - padding;
            return `${x},${y}`;
        });

        path.setAttribute('d', `M${linePoints.join(' L')}`);
        path.setAttribute('fill', 'none');
        path.setAttribute('stroke', '#6366f1');
        path.setAttribute('stroke-width', '2');

        svg.innerHTML = '';
        svg.appendChild(area);
        svg.appendChild(path);
    }

    updateChart();
    setInterval(updateChart, 1000);
    chartContainer.appendChild(svg);
}

// ========== Real-time Updates ==========
function startRealTimeUpdates() {
    setInterval(() => {
        if (!AppState.websocket || AppState.websocket.readyState !== WebSocket.OPEN) {
            updateMetricsLocal();
        }
    }, 2000);

    setInterval(() => {
        if (AppState.simulationRunning) {
            generateRandomPacket();
        }
    }, 5000);

    setInterval(() => {
        if (Math.random() > 0.7) {
            generateRandomAlert();
        }
    }, 30000);
}

function updateMetricsLocal() {
    const devicesChange = Math.floor(Math.random() * 3) - 1;
    AppState.activeDevices = Math.max(0, AppState.activeDevices + devicesChange);
    if (elements.activeDevices) elements.activeDevices.textContent = AppState.activeDevices;

    const rateChange = Math.floor(Math.random() * 100) - 50;
    AppState.msgRate = Math.max(100, AppState.msgRate + rateChange);
    const rateFormatted = AppState.msgRate >= 1000 ? (AppState.msgRate / 1000).toFixed(1) + 'K' : AppState.msgRate;
    if (elements.msgRate) elements.msgRate.textContent = rateFormatted;

    const loadChange = Math.floor(Math.random() * 5) - 2;
    AppState.load = Math.max(5, Math.min(95, AppState.load + loadChange));
    if (elements.load) {
        elements.load.textContent = AppState.load + '%';
        elements.load.style.color = AppState.load > 80 ? 'var(--error)' : 'var(--text-primary)';
    }
}

// ========== Packet Capture ==========
function loadSamplePackets() {
    const samplePackets = [
        { time: new Date().toLocaleTimeString('zh-CN', { hour12: false }) + '.123', source: '192.168.1.10', destination: '192.168.1.100', protocol: 'Modbus', length: 62, info: 'Read Holding Registers (FC03)' },
        { time: new Date().toLocaleTimeString('zh-CN', { hour12: false }) + '.156', source: '192.168.1.100', destination: '192.168.1.10', protocol: 'Modbus', length: 67, info: 'Response: 10 registers' },
        { time: new Date().toLocaleTimeString('zh-CN', { hour12: false }) + '.234', source: '192.168.2.50', destination: '192.168.1.100', protocol: 'MQTT', length: 128, info: 'PUBLISH /sensors/temp' },
        { time: new Date().toLocaleTimeString('zh-CN', { hour12: false }) + '.345', source: '192.168.1.100', destination: 'cloud.iot.com', protocol: 'OPC UA', length: 256, info: 'Publish Request (Subscription)' },
        { time: new Date().toLocaleTimeString('zh-CN', { hour12: false }) + '.456', source: '192.168.3.20', destination: '192.168.1.100', protocol: 'BACnet', length: 88, info: 'Who-Is Request' },
        { time: new Date().toLocaleTimeString('zh-CN', { hour12: false }) + '.567', source: '192.168.1.100', destination: '192.168.3.20', protocol: 'BACnet', length: 102, info: 'I-Am Response' }
    ];

    samplePackets.forEach(packet => addPacketToList(packet));
}

function addPacketToList(packet) {
    if (!elements.packetList) return;

    const row = document.createElement('div');
    row.className = 'packet-row';
    row.innerHTML = `
        <span class="col-time">${packet.time}</span>
        <span class="col-source">${packet.source}</span>
        <span class="col-destination">${packet.destination}</span>
        <span class="col-protocol">${packet.protocol}</span>
        <span class="col-length">${packet.length}</span>
        <span class="col-info">${packet.info}</span>
    `;

    row.addEventListener('click', () => selectPacket(row, packet));
    elements.packetList.appendChild(row);

    while (elements.packetList.children.length > 100) {
        elements.packetList.removeChild(elements.packetList.firstChild);
    }

    elements.packetList.scrollTop = elements.packetList.scrollHeight;
}

function generateRandomPacket() {
    const protocols = ['Modbus', 'MQTT', 'OPC UA', 'BACnet', 'CoAP'];
    const sources = ['192.168.1.10', '192.168.2.50', '192.168.1.100', '192.168.3.20'];
    const destinations = ['192.168.1.100', 'cloud.iot.com', '192.168.1.10', '192.168.2.1'];

    const packet = {
        time: new Date().toLocaleTimeString('zh-CN', { hour12: false }) + '.' + Math.floor(Math.random() * 999).toString().padStart(3, '0'),
        source: sources[Math.floor(Math.random() * sources.length)],
        destination: destinations[Math.floor(Math.random() * destinations.length)],
        protocol: protocols[Math.floor(Math.random() * protocols.length)],
        length: Math.floor(Math.random() * 500) + 50,
        info: getRandomPacketInfo()
    };

    sendWsMessage({ type: 'packet', packet });
    addPacketToList(packet);
}

function getRandomPacketInfo() {
    const infos = {
        Modbus: ['Read Holding Registers (FC03)', 'Write Single Register (FC06)', 'Read Input Registers (FC04)', 'Write Multiple Registers (FC10)'],
        MQTT: ['PUBLISH /sensors/temp', 'CONNECT Protocol', 'PINGREQ', 'SUBSCRIBE /sensors/#'],
        'OPC UA': ['Publish Request (Subscription)', 'Data Change Notification', 'Browse Request', 'Read Request'],
        BACnet: ['Who-Is Request', 'I-Am Response', 'Read Property Request', 'Write Property Request'],
        CoAP: ['GET /status', 'POST /control', 'PUT /config', 'DELETE /log']
    };

    const protocolList = Object.keys(infos);
    const protocol = protocolList[Math.floor(Math.random() * protocolList.length)];
    const protoInfos = infos[protocol] || infos['Modbus'];
    return protoInfos[Math.floor(Math.random() * protoInfos.length)];
}

function selectPacket(row, packet) {
    document.querySelectorAll('.packet-row').forEach(r => r.classList.remove('selected'));
    row.classList.add('selected');
    updateHexView(packet);
}

function updateHexView(packet) {
    const hexView = document.querySelector('.hex-view');
    if (hexView) {
        const data = Array.from({ length: 64 }, () =>
            Math.floor(Math.random() * 256).toString(16).padStart(2, '0').toUpperCase()
        );

        let html = '';
        for (let i = 0; i < 64; i += 16) {
            const offset = i.toString(16).padStart(4, '0').toUpperCase();
            const hexPart1 = data.slice(i, i + 8).join(' ');
            const hexPart2 = data.slice(i + 8, i + 16).join(' ');
            const asciiPart = data.slice(i, i + 16).map(b => {
                const charCode = parseInt(b, 16);
                return charCode >= 32 && charCode <= 126 ? String.fromCharCode(charCode) : '.';
            }).join('');

            html += `${offset}  ${hexPart1}  ${hexPart2}   ${asciiPart}\n`;
        }

        hexView.textContent = html;
    }
}

function filterPackets() {
    if (!elements.filterInput) return;
    const filter = elements.filterInput.value.toLowerCase();
    document.querySelectorAll('.packet-row').forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(filter) ? '' : 'none';
    });
}

// ========== Capture Controls ==========
let captureInterval = null;

function startCapture() {
    AppState.simulationRunning = true;
    elements.btnStartCapture?.classList.add('btn-start');
    elements.btnStartCapture.innerHTML = '<span class="btn-icon">⏸️</span> 捕获中...';

    sendWsMessage({ type: 'capture_start' });

    captureInterval = setInterval(() => {
        if (Math.random() > 0.3) {
            generateRandomPacket();
        }
    }, 500);
}

function stopCapture() {
    AppState.simulationRunning = false;
    elements.btnStartCapture?.classList.remove('btn-start');
    elements.btnStartCapture.innerHTML = '<span class="btn-icon">▶️</span> 开始捕获';

    sendWsMessage({ type: 'capture_stop' });

    if (captureInterval) {
        clearInterval(captureInterval);
        captureInterval = null;
    }
}

function clearPackets() {
    if (elements.packetList) {
        elements.packetList.innerHTML = '';
    }
    sendWsMessage({ type: 'capture_clear' });
}

// ========== Simulation Controls ==========
function toggleSimulation() {
    if (AppState.simulationRunning) {
        stopSimulation();
    } else {
        startSimulation();
    }
}

function startSimulation() {
    AppState.simulationRunning = true;

    if (elements.playButton) {
        elements.playButton.innerHTML = `<svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><rect y="6" x="6" width="12" height="12"/></svg>`;
        elements.playButton.title = '停止模拟';
    }

    sendWsMessage({ type: 'simulation_start' });
    startCapture();
}

function stopSimulation() {
    AppState.simulationRunning = false;

    if (elements.playButton) {
        elements.playButton.innerHTML = `<svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>`;
        elements.playButton.title = '运行模拟';
    }

    sendWsMessage({ type: 'simulation_stop' });
    stopCapture();
}

// ========== Topology ==========
function initializeTopology() {
    console.log('Topology view initialized');
}

function selectTopologyNode(node) {
    document.querySelectorAll('.topology-node').forEach(n => {
        const rect = n.querySelector('rect');
        if (rect) rect.style.stroke = '#6366f1';
    });
    node.querySelector('rect').style.stroke = '#f59e0b';
}

// ========== Dashboard ==========
function refreshDashboard() {
    console.log('Dashboard refreshed');
}

function initializeDebugView() {
    console.log('Debug view initialized');
}

function initializeDevicesView() {
    console.log('Devices view initialized');
}

// ========== Alerts ==========
function generateRandomAlert() {
    const alertTypes = ['critical', 'warning', 'info'];
    const titles = ['温度过高', '连接不稳定', '设备上线', '内存使用率高', '网络延迟增加'];
    const descs = ['设备温度超过安全阈值', '检测到异常丢包率', '设备已重新连接网络', 'CPU 使用率超过 80%', '响应时间增加 50ms'];

    const alert = {
        type: alertTypes[Math.floor(Math.random() * alertTypes.length)],
        title: titles[Math.floor(Math.random() * titles.length)],
        description: descs[Math.floor(Math.random() * descs.length)]
    };

    addAlert(alert);
    sendWsMessage({ type: 'alert', alert });
}

// ========== Modal ==========
function showAddDeviceModal() {
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal">
            <div class="modal-header">
                <h3>添加设备</h3>
                <button class="modal-close">&times;</button>
            </div>
            <div class="modal-body">
                <div class="form-group">
                    <label>设备名称</label>
                    <input type="text" class="form-input" placeholder="输入设备名称">
                </div>
                <div class="form-group">
                    <label>设备类型</label>
                    <select class="form-select">
                        <option>PLC</option>
                        <option>传感器</option>
                        <option>执行器</option>
                        <option>网关</option>
                    </select>
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn-secondary">取消</button>
                <button class="btn-primary">添加</button>
            </div>
        </div>
    `;

    modal.querySelector('.modal-close').addEventListener('click', () => modal.remove());
    modal.querySelector('.btn-secondary').addEventListener('click', () => modal.remove());
    modal.addEventListener('click', (e) => {
        if (e.target === modal) modal.remove();
    });

    document.body.appendChild(modal);
}

// ========== Utility Functions ==========
function formatNumber(num) {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toString();
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func(...args), wait);
    };
}

// ========== Export ==========
window.AppState = AppState;
window.elements = elements;
window.switchPage = switchPage;
window.toggleSimulation = toggleSimulation;

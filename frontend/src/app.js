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
    alerts: []
};

// ========== DOM Elements ==========
const elements = {};

// ========== Initialize Application ==========
document.addEventListener('DOMContentLoaded', () => {
    initializeElements();
    bindEvents();
    initializeCharts();
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
}

// ========== Page Navigation ==========
function switchPage(pageName) {
    // Update nav buttons
    elements.navButtons.forEach(btn => {
        btn.classList.toggle('active', btn.dataset.page === pageName);
    });

    // Update pages
    elements.pages.forEach(page => {
        page.classList.toggle('active', page.id === `page-${pageName}`);
    });

    AppState.currentPage = pageName;

    // Initialize page-specific features
    if (pageName === 'dashboard') {
        refreshDashboard();
    } else if (pageName === 'topology') {
        initializeTopology();
    } else if (pageName === 'debug') {
        initializeDebugView();
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
}

function showDeviceProperties(deviceItem) {
    // Update right panel with device properties
    console.log('Selected device:', deviceItem.dataset.id);
}

// ========== Drag and Drop ==========
function handleDragStart(e) {
    e.dataTransfer.setData('deviceType', e.target.dataset.deviceType);
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

    if (deviceType && elements.deviceCanvas) {
        createDeviceOnCanvas(deviceType, e.offsetX, e.offsetY);
    }
}

function createDeviceOnCanvas(type, x, y) {
    const canvas = elements.deviceCanvas;
    const placeholder = canvas.querySelector('.canvas-placeholder');

    if (placeholder) {
        placeholder.remove();
    }

    const deviceEl = document.createElement('div');
    deviceEl.className = 'device-on-canvas';
    deviceEl.style.cssText = `
        position: absolute;
        left: ${x}px;
        top: ${y}px;
        width: 100px;
        height: 100px;
        background: var(--bg-primary);
        border: 2px solid var(--primary);
        border-radius: 8px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        cursor: move;
        transition: all 0.2s ease;
    `;

    const icons = {
        plc: '🏭',
        sensor: '🌡️',
        actuator: '⚙️',
        gateway: '🌉'
    };

    const labels = {
        plc: 'PLC',
        sensor: '传感器',
        actuator: '执行器',
        gateway: '网关'
    };

    deviceEl.innerHTML = `
        <span style="font-size: 28px;">${icons[type] || '📦'}</span>
        <span style="font-size: 12px; margin-top: 8px;">${labels[type] || type}</span>
    `;

    deviceEl.addEventListener('mouseenter', () => {
        deviceEl.style.boxShadow = '0 0 20px var(--primary-muted)';
    });

    deviceEl.addEventListener('mouseleave', () => {
        deviceEl.style.boxShadow = 'none';
    });

    // Make draggable on canvas
    makeElementDraggable(deviceEl);

    canvas.appendChild(deviceEl);
}

function makeElementDraggable(el) {
    let isDragging = false;
    let startX, startY, initialX, initialY;

    el.addEventListener('mousedown', startDrag);

    function startDrag(e) {
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
    // Initialize flow chart
    const flowCanvas = document.getElementById('flowChart');
    if (flowCanvas) {
        drawFlowChart(flowCanvas);
    }
}

function drawFlowChart(canvas) {
    const ctx = canvas.getContext('2d');
    const width = canvas.parentElement.clientWidth;
    const height = 200;

    canvas.width = width;
    canvas.height = height;

    // Draw animated flow lines
    let offset = 0;

    function animate() {
        ctx.clearRect(0, 0, width, height);

        // Draw grid
        ctx.strokeStyle = 'rgba(99, 102, 241, 0.1)';
        ctx.lineWidth = 1;

        for (let x = 0; x < width; x += 40) {
            ctx.beginPath();
            ctx.moveTo(x, 0);
            ctx.lineTo(x, height);
            ctx.stroke();
        }

        for (let y = 0; y < height; y += 40) {
            ctx.beginPath();
            ctx.moveTo(0, y);
            ctx.lineTo(width, y);
            ctx.stroke();
        }

        // Draw flow lines
        ctx.strokeStyle = '#6366f1';
        ctx.lineWidth = 2;
        ctx.setLineDash([10, 10]);
        ctx.lineDashOffset = -offset;

        for (let y = 30; y < height; y += 50) {
            ctx.beginPath();
            ctx.moveTo(0, y);
            ctx.lineTo(width, y);
            ctx.stroke();
        }

        // Draw nodes
        const nodePositions = [
            { x: 50, y: 50, icon: '🏭' },
            { x: width / 2, y: 50, icon: '🌉' },
            { x: width - 100, y: 100, icon: '☁️' },
            { x: width / 2, y: 150, icon: '📊' }
        ];

        nodePositions.forEach(node => {
            ctx.fillStyle = '#1e293b';
            ctx.beginPath();
            ctx.arc(node.x, node.y, 25, 0, Math.PI * 2);
            ctx.fill();
            ctx.strokeStyle = '#6366f1';
            ctx.lineWidth = 2;
            ctx.stroke();
        });

        offset = (offset + 1) % 20;
        requestAnimationFrame(animate);
    }

    animate();
}

// ========== Real-time Updates ==========
function startRealTimeUpdates() {
    setInterval(updateMetrics, 2000);
    setInterval(generateRandomPacket, 5000);
    setInterval(updateAlerts, 30000);
}

function updateMetrics() {
    // Update active devices
    const devicesChange = Math.floor(Math.random() * 3) - 1;
    AppState.activeDevices = Math.max(0, AppState.activeDevices + devicesChange);
    elements.activeDevices.textContent = AppState.activeDevices;

    // Update message rate
    const rateChange = Math.floor(Math.random() * 100) - 50;
    AppState.msgRate = Math.max(100, AppState.msgRate + rateChange);
    const rateFormatted = AppState.msgRate >= 1000
        ? (AppState.msgRate / 1000).toFixed(1) + 'K'
        : AppState.msgRate;
    elements.msgRate.textContent = rateFormatted;

    // Update load
    const loadChange = Math.floor(Math.random() * 5) - 2;
    AppState.load = Math.max(5, Math.min(95, AppState.load + loadChange));
    elements.load.textContent = AppState.load + '%';

    // Color code based on value
    elements.load.style.color = AppState.load > 80 ? 'var(--error)' : 'var(--text-primary)';
}

// ========== Packet Capture ==========
function loadSamplePackets() {
    const samplePackets = [
        {
            time: new Date().toLocaleTimeString('zh-CN', { hour12: false }) + '.123',
            source: '192.168.1.10',
            destination: '192.168.1.100',
            protocol: 'Modbus',
            length: 62,
            info: 'Read Holding Registers (FC03)'
        },
        {
            time: new Date().toLocaleTimeString('zh-CN', { hour12: false }) + '.156',
            source: '192.168.1.100',
            destination: '192.168.1.10',
            protocol: 'Modbus',
            length: 67,
            info: 'Response: 10 registers'
        },
        {
            time: new Date().toLocaleTimeString('zh-CN', { hour12: false }) + '.234',
            source: '192.168.2.50',
            destination: '192.168.1.100',
            protocol: 'MQTT',
            length: 128,
            info: 'PUBLISH /sensors/temp'
        },
        {
            time: new Date().toLocaleTimeString('zh-CN', { hour12: false }) + '.345',
            source: '192.168.1.100',
            destination: 'cloud.iot.com',
            protocol: 'OPC UA',
            length: 256,
            info: 'Publish Request (Subscription)'
        }
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
    elements.packetList.scrollTop = elements.packetList.scrollHeight;
}

function generateRandomPacket() {
    if (!AppState.simulationRunning) return;

    const protocols = ['Modbus', 'MQTT', 'OPC UA', 'HTTP'];
    const sources = ['192.168.1.10', '192.168.2.50', '192.168.1.100'];
    const destinations = ['192.168.1.100', 'cloud.iot.com', '192.168.1.10'];

    const packet = {
        time: new Date().toLocaleTimeString('zh-CN', { hour12: false }) + '.' + Math.floor(Math.random() * 999),
        source: sources[Math.floor(Math.random() * sources.length)],
        destination: destinations[Math.floor(Math.random() * destinations.length)],
        protocol: protocols[Math.floor(Math.random() * protocols.length)],
        length: Math.floor(Math.random() * 500) + 50,
        info: getRandomPacketInfo()
    };

    addPacketToList(packet);
}

function getRandomPacketInfo() {
    const infos = [
        'Read Holding Registers (FC03)',
        'Write Single Register (FC06)',
        'PUBLISH /sensors/temp',
        'CONNECT Protocol',
        'Publish Request (Subscription)',
        'Data Change Notification',
        'Browse Request',
        'TCP Keep-Alive'
    ];
    return infos[Math.floor(Math.random() * infos.length)];
}

function selectPacket(row, packet) {
    document.querySelectorAll('.packet-row').forEach(r => r.classList.remove('selected'));
    row.classList.add('selected');

    // Update hex view (simulated)
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
            const asciiPart = data.slice(i, i + 16)
                .map(b => {
                    const charCode = parseInt(b, 16);
                    return charCode >= 32 && charCode <= 126 ? String.fromCharCode(charCode) : '.';
                })
                .join('');

            html += `${offset}  ${hexPart1}  ${hexPart2}   ${asciiPart}\n`;
        }

        hexView.textContent = html;
    }
}

function filterPackets() {
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

    captureInterval = setInterval(() => {
        if (Math.random() > 0.5) {
            generateRandomPacket();
        }
    }, 500);
}

function stopCapture() {
    AppState.simulationRunning = false;
    elements.btnStartCapture?.classList.remove('btn-start');
    elements.btnStartCapture.innerHTML = '<span class="btn-icon">▶️</span> 开始捕获';

    if (captureInterval) {
        clearInterval(captureInterval);
        captureInterval = null;
    }
}

function clearPackets() {
    if (elements.packetList) {
        elements.packetList.innerHTML = '';
    }
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
    elements.playButton.innerHTML = `
        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
            <rect x="6" y="6" width="12" height="12"/>
        </svg>
    `;
    startCapture();
}

function stopSimulation() {
    AppState.simulationRunning = false;
    elements.playButton.innerHTML = `
        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
            <path d="M8 5v14l11-7z"/>
        </svg>
    `;
    stopCapture();
}

// ========== Topology ==========
function initializeTopology() {
    // D3.js or SVG interactions are initialized here
    console.log('Topology view initialized');
}

function selectTopologyNode(node) {
    document.querySelectorAll('.topology-node').forEach(n => {
        n.querySelector('rect').style.stroke = '#6366f1';
    });
    node.querySelector('rect').style.stroke = '#f59e0b';
}

// ========== Dashboard ==========
function refreshDashboard() {
    // Refresh dashboard widgets
    console.log('Dashboard refreshed');
}

// ========== Alerts ==========
function updateAlerts() {
    // Generate new alerts occasionally
    const alertTypes = ['critical', 'warning', 'info'];
    const newAlert = {
        type: alertTypes[Math.floor(Math.random() * alertTypes.length)],
        title: getRandomAlertTitle(),
        desc: getRandomAlertDesc(),
        time: '刚刚'
    };

    // Add to alerts list
    console.log('New alert:', newAlert);
}

function getRandomAlertTitle() {
    const titles = [
        '温度过高',
        '连接不稳定',
        '设备上线',
        '内存使用率高',
        '网络延迟增加'
    ];
    return titles[Math.floor(Math.random() * titles.length)];
}

function getRandomAlertDesc() {
    const descs = [
        '设备温度超过安全阈值',
        '检测到异常丢包率',
        '设备已重新连接网络',
        'CPU 使用率超过 80%',
        '响应时间增加 50ms'
    ];
    return descs[Math.floor(Math.random() * descs.length)];
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
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// ========== Export for debugging ==========
window.AppState = AppState;
window.elements = elements;

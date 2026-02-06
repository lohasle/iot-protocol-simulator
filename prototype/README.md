# IoT Protocol Simulator - Prototype

Interactive prototype for the IoT Protocol Simulator with drag-and-drop functionality, real-time data simulation, and WebSocket communication.

## Features

- **Drag and Drop**: Drag devices from palette to canvas
- **Page Navigation**: Dashboard, Topology, Debug views
- **Real-time Simulation**: Live metrics and packet capture
- **WebSocket Integration**: Real-time data updates
- **Multiple Protocols**: Modbus, MQTT, OPC UA, BACnet, CoAP

## Quick Start

1. Open `index.html` in a modern web browser
2. Navigate using the sidebar
3. Drag devices from the palette to the canvas
4. Click "开始捕获" to start packet simulation
5. Watch real-time metrics and alerts

## Files

- `index.html` - Main HTML structure
- `styles.css` - Styling with dark theme
- `app.js` - Application logic (drag-drop, WebSocket, simulation)

## Browser Compatibility

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Screenshots

### Dashboard View
Real-time metrics dashboard showing active devices, message rate, and system load.

### Topology View
Drag-and-drop network topology builder with visual device placement.

### Debug View
Packet capture and analysis with hex view and protocol decoding.

## Protocol Support

| Protocol | Port | Status |
|----------|------|--------|
| Modbus TCP | 502 | ✅ Supported |
| MQTT | 1883 | ✅ Supported |
| OPC UA | 4840 | ✅ Supported |
| BACnet | 47808 | ✅ Supported |
| CoAP | 5683 | ✅ Supported |

## API Integration

The prototype can connect to a backend server for real-time data:

```javascript
// WebSocket connection
const ws = new WebSocket('ws://localhost:8000/ws');

// Subscribe to channels
ws.send(JSON.stringify({
  type: 'subscribe',
  channels: ['metrics', 'packets', 'alerts']
}));
```

## Development

To modify the prototype:

1. Edit `styles.css` for styling changes
2. Edit `app.js` for logic changes
3. Refresh the browser to see changes

## License

MIT License

const WebSocket = require('ws');

const websocketURL = "wss://proxy.wynd.network:4650/";
const user_id = '2gxV6b5xWXwFac55zt55B4TFdJ6'; // replace with actual user_id

function connectToWebSocket() {
    const ws = new WebSocket(websocketURL);

    ws.on('open', function open() {
        console.log('connected');
        const authMessage = JSON.stringify({
            action: 'AUTH',
            data: {
                user_id: user_id,
                device_id: generateDeviceId(),
            }
        });
        ws.send(authMessage);
    });

    ws.on('message', function incoming(data) {
        const message = JSON.parse(data);
        console.log('Received message:', message);

        if (message.action === 'PONG') {
            console.log('PONG received');
        }
    });

    ws.on('close', function close() {
        console.log('disconnected');
    });

    ws.on('error', function error(err) {
        console.error('WebSocket error:', err);
    });

    setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
            const pingMessage = JSON.stringify({
                action: 'PING'
            });
            ws.send(pingMessage);
        }
    }, 30000); // send PING every 30 seconds
}

function generateDeviceId() {
    return 'device-' + Math.random().toString(36).substr(2, 16);
}

// Connect to the WebSocket without using a proxy
connectToWebSocket();

from nicegui import ui
from aiohttp import web
import asyncio
import threading
import json

connected_websockets = []

# --- WebSocket signaling server --- #
async def signaling_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    connected_websockets.append(ws)

    async for msg in ws:
        if msg.type == web.WSMsgType.TEXT:
            for peer in connected_websockets:
                if peer != ws:
                    await peer.send_str(msg.data)

    connected_websockets.remove(ws)
    return ws

def start_signaling_server():
    app = web.Application()
    app.router.add_get('/ws', signaling_handler)
    web.run_app(app, port=8765)

# --- Run signaling server in separate thread --- #
threading.Thread(target=start_signaling_server, daemon=True).start()

# --- NiceGUI Frontend with embedded JS WebRTC --- #
@ui.page('/')
def index():
    ui.label('🎙 Real-time Voice Chat (Python + WebRTC + NiceGUI)').classes('text-2xl font-bold')

    ui.add_body_html('''
<button onclick="start()">🎤 Connect Voice Chat</button>
<script>
let ws, peer;

function start() {
    ws = new WebSocket('ws://localhost:8765/ws');
    peer = new RTCPeerConnection({iceServers: [{urls: 'stun:stun.l.google.com:19302'}]});

    navigator.mediaDevices.getUserMedia({ audio: true }).then(stream => {
        stream.getTracks().forEach(track => peer.addTrack(track, stream));

        peer.ontrack = (event) => {
            const audio = document.createElement('audio');
            audio.srcObject = event.streams[0];
            audio.autoplay = true;
            audio.controls = true;
            document.body.appendChild(audio);
        };

        peer.onicecandidate = (event) => {
            if (event.candidate) {
                ws.send(JSON.stringify({ type: 'ice', candidate: event.candidate }));
            }
        };

        peer.createOffer().then(offer => {
            peer.setLocalDescription(offer);
            ws.send(JSON.stringify({ type: 'offer', offer }));
        });
    });

    ws.onmessage = async (message) => {
        const data = JSON.parse(message.data);

        if (data.type === 'offer') {
            await peer.setRemoteDescription(new RTCSessionDescription(data.offer));
            const answer = await peer.createAnswer();
            await peer.setLocalDescription(answer);
            ws.send(JSON.stringify({ type: 'answer', answer }));
        } else if (data.type === 'answer') {
            await peer.setRemoteDescription(new RTCSessionDescription(data.answer));
        } else if (data.type === 'ice') {
            if (data.candidate) {
                await peer.addIceCandidate(new RTCIceCandidate(data.candidate));
            }
        }
    };
}
</script>
''')

# --- Run app --- #
ui.run(title='Python Voice Chat', reload=False)

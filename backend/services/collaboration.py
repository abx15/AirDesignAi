import socketio
import logging

logger = logging.getLogger(__name__)

# Initialize Socket.io Async Server
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
socket_app = socketio.ASGIApp(sio)

@sio.event
async def connect(sid, environ):
    logger.info(f"Client connected: {sid}")

@sio.event
async def disconnect(sid):
    logger.info(f"Client disconnected: {sid}")

@sio.event
async def join_room(sid, data):
    room_id = data.get('roomId')
    user_id = data.get('userId')
    if room_id:
        sio.enter_room(sid, room_id)
        logger.info(f"User {user_id} joined room {room_id}")
        await sio.emit('user_joined', {'userId': user_id, 'sid': sid}, room=room_id, skip_sid=sid)

@sio.event
async def leave_room(sid, data):
    room_id = data.get('roomId')
    if room_id:
        sio.leave_room(sid, room_id)
        logger.info(f"Client {sid} left room {room_id}")

@sio.event
async def sync_cursor(sid, data):
    # data: { roomId, userId, landmarks }
    room_id = data.get('roomId')
    if room_id:
        await sio.emit('cursor_updated', data, room=room_id, skip_sid=sid)

@sio.event
async def object_update(sid, data):
    # data: { roomId, objectId, updates }
    room_id = data.get('roomId')
    if room_id:
        await sio.emit('object_patched', data, room=room_id, skip_sid=sid)

@sio.event
async def object_create(sid, data):
    # data: { roomId, object }
    room_id = data.get('roomId')
    if room_id:
        await sio.emit('object_added', data, room=room_id, skip_sid=sid)

@sio.event
async def object_delete(sid, data):
    # data: { roomId, objectId }
    room_id = data.get('roomId')
    if room_id:
        await sio.emit('object_removed', data, room=room_id, skip_sid=sid)

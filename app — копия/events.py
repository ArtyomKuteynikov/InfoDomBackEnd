from flask import session, url_for
from flask_socketio import emit, join_room, leave_room
from app import socketio
from app import db
from .models import Messages, User


@socketio.on('joined', namespace='/chat')
def joined(message):
    """Sent by clients when they enter a room.
    A status message is broadcast to all people in the room."""
    room = session.get('room')
    join_room(room)


@socketio.on('text', namespace='/chat')
def text(message):
    try:
        """Sent by a client when the user entered a new message.
        The message is sent to all people in the room."""
        room = session.get('room')
        print(message)
        new_msg = Messages(author=message['author'], chat_id=message['chat'], text=message['msg'])
        db.session.add(new_msg)
        db.session.commit()
        user = User.query.filter_by(id=message['author']).first()
        avatar = url_for('static', filename='profile_photos/'+user.photo)
        sent = new_msg.timestamp.strftime('%H:%M')
        emit('message', {'author': message['author'], 'msg': message['msg'], 'avatar': avatar, 'time': sent}, room=room)
    except Exception as e:
        print(e)


@socketio.on('left', namespace='/chat')
def left(message):
    """Sent by clients when they leave a room.
    A status message is broadcast to all people in the room."""
    room = session.get('room')
    leave_room(room)


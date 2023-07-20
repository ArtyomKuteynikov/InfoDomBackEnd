from flask import session, url_for
from flask_socketio import emit, join_room, leave_room
from app import socketio
from app import db
from .models import Messages, User
import base64
from PIL import Image
from io import BytesIO
from os import getcwd
import re


@socketio.on('joined', namespace='/chat')
def joined(message):
    """Sent by clients when they enter a room.
    A status message is broadcast to all people in the room."""
    room = session.get('room')
    join_room(room)


@socketio.on('text', namespace='/chat')
def text(message):
    print(1)
    """Sent by a client when the user entered a new message.
    The message is sent to all people in the room."""
    room = session.get('room')
    print(message)
    # im = Image.open(message['image'])
    # im.save(f"{getcwd()}/app/static/profile_photos/{user.id}.png")
    new_msg = Messages(author=message['author'], chat_id=message['chat'], text=message['msg'])
    db.session.add(new_msg)
    db.session.commit()
    if message['image']:
        print('img')
        image_data = re.sub('^data:image/.+;base64,', '', message['image'])
        im = Image.open(BytesIO(base64.b64decode(image_data)))
        im.save(f"{getcwd()}/app/static/messages/{new_msg.id}.png")
        _ = Messages.query.filter_by(id=new_msg.id).update(
            {'image': f'{new_msg.id}.png'})
        db.session.commit()
    user = User.query.filter_by(id=message['author']).first()
    avatar = url_for('static', filename='profile_photos/' + user.photo)
    sent = new_msg.timestamp.strftime('%H:%M')
    if new_msg.image:
        emit('message',
             {'author': message['author'], 'msg': message['msg'], 'avatar': avatar, 'time': sent, 'id': new_msg.id,
              'image': url_for('static', filename='messages/' + new_msg.image)}, room=room)
    else:
        emit('message',
             {'author': message['author'], 'msg': message['msg'], 'avatar': avatar, 'time': sent, 'id': new_msg.id,
              'image': ''}, room=room)
    try:
        pass
    except Exception as e:
        print('ERROR', e)


@socketio.on('left', namespace='/chat')
def left(message):
    """Sent by clients when they leave a room.
    A status message is broadcast to all people in the room."""
    room = session.get('room')
    leave_room(room)

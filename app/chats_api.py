# api.py
import datetime
import json
from flask import Blueprint, request, current_app, url_for, redirect
from werkzeug.security import generate_password_hash
import base64
from PIL import Image
from io import BytesIO
from . import db
from .models import User, Codes, JK, Points, Promotions, PointsTypes, News, Addresses, Complaints, ChatRooms, Messages
from iqsms_rest import Gate
import random
import time
from .config import *
from dadata import Dadata
from os import getcwd
from .api import action

api = Blueprint('chats_api', __name__)

'''
if int(id) != user.id:
        chats = ChatRooms.query.filter_by(user1=id, user2=user.id).all() + \
                ChatRooms.query.filter_by(user2=id, user1=user.id).all()
        if chats:
            chat = chats[0]
        else:
            new_chat = ChatRooms(type='personal', user2=id, user1=user.id)
            db.session.add(new_chat)
            db.session.commit()
            chat = new_chat
        return redirect(url_for('main.personal_chat', id=chat.id))
    else:
        user = User.query.filter_by(id=id).first()
        if user.is_uk:
            return redirect(url_for('main.uk', id=id))
        return redirect(url_for('main.user', id=id))
'''


@api.route('/api/personal_chats', methods=['GET'])
def personal_chats():
    """
   ---
   get:
     summary: Все личные чаты пользователя чаты
     parameters:
         - in: query
           name: token
           schema:
             type: string
             example: 5zqxZa16b0vEE1sx$9a74b2452862f8b0061a5356079f69c3b83af9aec7430d070901f745b984a3f9
           description: token
         - in: query
           name: OS
           schema:
             type: string
             example: Android
           description: OS
         - in: query
           name: DeviceID
           schema:
             type: string
             example: Gnx786nzdg758
           description: DeviceID
     responses:
       '200':
         description: Результат
         content:
           application/json:
             schema:      # Request body contents
               type: object
               properties:
                   chat_rooms:
                     type: array
                     items:
                       type: object
                       properties:
                           id:
                             type: integer
                           phone:
                             type: string
                           status:
                             type: string
                           user:
                             type: string
                           profile_photo:
                             type: string
                           last_updated:
                             type: string
                           last_message_timestamp:
                             type: number
                           unread:
                             type: integer
       '400':
         description: Не передан обязательный параметр
         content:
           application/json:
             schema: ErrorSchema
       '401':
         description: Неверный токен
         content:
           application/json:
             schema: ErrorSchema
       '403':
         description: Пользователь заблокирован
         content:
           application/json:
             schema: ErrorSchema
     tags:
       - chats
    """
    try:
        token = request.args.get('token')
        user = User.query.filter_by(token=token).first()
        if not user:
            return current_app.response_class(
                response=json.dumps(
                    {'error': f'USER DOES NOT EXIST'}
                ),
                status=403,
                mimetype='application/json'
            )
        if user.status == "blocked":
            return current_app.response_class(
                response=json.dumps(
                    {'error': "USER BLOCKED"}
                ),
                status=403,
                mimetype='application/json'
            )
        deviceId = request.args.get('DeviceId')
        os = request.args.get('os')
        action(token, deviceId, os)
        chat_rooms = []
        chats = ChatRooms.query.filter_by(type="personal", user1=user.id).all() + ChatRooms.query.filter_by(
            type="personal", user2=user.id).all()
        for i in chats:
            if Messages.query.filter_by(chat_id=i.id).all():
                last_message = Messages.query.filter_by(chat_id=i.id).all()[-1]
            else:
                last_message = 0
            user = i.user1 if i.user1 != user.id else i.user2
            user = User.query.filter_by(id=user).first()
            unread = len(Messages.query.filter_by(chat_id=i.id, read=0).all()) - len(
                Messages.query.filter_by(author=user.id, chat_id=i.id, read=0).all())
            if last_message:
                chat_rooms.append({
                    'id': i.id,
                    'phone': user.phone,
                    'status': user.status,
                    'user': f'{user.name} {user.surname}' if not user.org else f'{user.org_name}',
                    'profile_photo': url_for('static', filename=f'profile_photos/{user.photo}'),
                    'last_updated': datetime.datetime.fromtimestamp(user.last_updated).strftime('%H:%M'),
                    'last_message_timestamp': last_message.timestamp.timestamp(),
                    'unread': unread,
                })
            else:
                chat_rooms.append({
                    'id': i.id,
                    'phone': user.phone,
                    'status': user.status,
                    'user': f'{user.name} {user.surname}' if not user.org else f'{user.org_name}',
                    'profile_photo': url_for('static', filename=f'profile_photos/{user.photo}'),
                    'last_updated': datetime.datetime.fromtimestamp(user.last_updated).strftime('%H:%M'),
                    'last_message_timestamp': datetime.datetime.now().timestamp(),
                    'unread': unread
                })
        chat_rooms = sorted(chat_rooms, key=lambda x: x['last_message_timestamp'])
        return current_app.response_class(
            response=json.dumps(
                {'chat_rooms': chat_rooms}
            ),
            status=200,
            mimetype='application/json'
        )
    except Exception as e:
        return current_app.response_class(
            response=json.dumps(
                {'error': f'ERROR: {e}!'}
            ),
            status=400,
            mimetype='application/json'
        )


@api.route('/api/chat_messages', methods=['GET'])
def chat_messages():
    """
   ---
   get:
     summary: Сообщения в чате
     parameters:
         - in: query
           name: chat_id
           schema:
             type: integer
             example: 1
           description: chat_id
         - in: query
           name: token
           schema:
             type: string
             example: 5zqxZa16b0vEE1sx$9a74b2452862f8b0061a5356079f69c3b83af9aec7430d070901f745b984a3f9
           description: token
         - in: query
           name: OS
           schema:
             type: string
             example: Android
           description: OS
         - in: query
           name: DeviceID
           schema:
             type: string
             example: Gnx786nzdg758
           description: DeviceID
     responses:
       '200':
         description: Результат
         content:
           application/json:
             schema:      # Request body contents
               type: object
               properties:
                   messages:
                     type: array
                     items:
                       type: object
                       properties:
                           id:
                             type: integer
                           profile_photo:
                             type: string
                           text:
                             type: string
                           time:
                             type: string
                           timestamp:
                             type: number
                           author:
                             type: integer
                           name:
                             type: string
                           image:
                             type: string
                   profile_photo:
                     type: string
                   name:
                     type: string
                   chat_id:
                     type: string
       '400':
         description: Не передан обязательный параметр
         content:
           application/json:
             schema: ErrorSchema
       '401':
         description: Неверный токен
         content:
           application/json:
             schema: ErrorSchema
       '403':
         description: Пользователь заблокирован
         content:
           application/json:
             schema: ErrorSchema
     tags:
       - chats
    """
    try:
        chat_id = request.args.get('chat_id')
        token = request.args.get('token')
        user = User.query.filter_by(token=token).first()
        if not user:
            return current_app.response_class(
                response=json.dumps(
                    {'error': f'USER DOES NOT EXIST'}
                ),
                status=403,
                mimetype='application/json'
            )
        if user.status == "blocked":
            return current_app.response_class(
                response=json.dumps(
                    {'error': "USER BLOCKED"}
                ),
                status=403,
                mimetype='application/json'
            )
        deviceId = request.args.get('DeviceId')
        os = request.args.get('os')
        action(token, deviceId, os)
        chat = ChatRooms.query.filter_by(id=chat_id).first()
        if user.id not in [chat.user1, chat.user2]:
            return current_app.response_class(
                response=json.dumps(
                    {'error': f'WRONG CHAT'}
                ),
                status=401,
                mimetype='application/json'
            )
        user = chat.user1 if chat.user1 != user.id else chat.user2
        user = User.query.filter_by(id=user).first()
        msgs = []
        messages = Messages.query.filter_by(chat_id=chat_id).all()
        for i in messages:
            author = User.query.filter_by(id=i.author).first()
            msgs.append({
                'id': i.id,
                'profile_photo': url_for('static', filename=f'profile_photos/{author.photo}') if author.photo else '',
                'text': i.text,
                'time': i.timestamp.strftime('%H:%M'),
                'timestamp': i.timestamp.timestamp(),
                'author': i.author,
                'name': f'{author.name} {author.surname}' if not author.org else author.org_name,
                'image': url_for('static', filename=f'messages/{i.image}') if i.image else ''
            })
        _ = Messages.query.filter_by(chat_id=chat_id, read=0, author=user.id).update({'read': 1})
        db.session.commit()
        return current_app.response_class(
            response=json.dumps(
                {
                    'messages': msgs,
                    'profile_photo': url_for('static', filename=f'profile_photos/{user.photo}'),
                    'name': f'{user.name} {user.surname}' if not user.org else user.org_name,
                    'chat_id': chat_id
                }
            ),
            status=200,
            mimetype='application/json'
        )
    except Exception as e:
        return current_app.response_class(
            response=json.dumps(
                {'error': f'ERROR: {e}!'}
            ),
            status=400,
            mimetype='application/json'
        )


@api.route('/api/jk_chat', methods=['GET'])
def jk_chat():
    """
    ---
   get:
     summary: Сообщения в чате ЖК
     parameters:
         - in: query
           name: token
           schema:
             type: string
             example: 5zqxZa16b0vEE1sx$9a74b2452862f8b0061a5356079f69c3b83af9aec7430d070901f745b984a3f9
           description: token
         - in: query
           name: OS
           schema:
             type: string
             example: Android
           description: OS
         - in: query
           name: DeviceID
           schema:
             type: string
             example: Gnx786nzdg758
           description: DeviceID
     responses:
       '200':
         description: Результат
         content:
           application/json:
             schema:      # Request body contents
               type: object
               properties:
                   messages:
                     type: array
                     items:
                       type: object
                       properties:
                           id:
                             type: integer
                           profile_photo:
                             type: string
                           text:
                             type: string
                           time:
                             type: string
                           timestamp:
                             type: number
                           author:
                             type: integer
                           name:
                             type: string
                           image:
                             type: string
                   profile_photo:
                     type: string
                   name:
                     type: string
                   chat_id:
                     type: integer
                   users:
                     type: integer
                   online:
                     type: integer
       '400':
         description: Не передан обязательный параметр
         content:
           application/json:
             schema: ErrorSchema
       '401':
         description: Неверный токен
         content:
           application/json:
             schema: ErrorSchema
       '403':
         description: Пользователь заблокирован
         content:
           application/json:
             schema: ErrorSchema
     tags:
       - chats
    """
    try:
        token = request.args.get('token')
        user = User.query.filter_by(token=token).first()
        if not user:
            return current_app.response_class(
                response=json.dumps(
                    {'error': f'USER DOES NOT EXIST'}
                ),
                status=403,
                mimetype='application/json'
            )
        if user.status == "blocked":
            return current_app.response_class(
                response=json.dumps(
                    {'error': "USER BLOCKED"}
                ),
                status=403,
                mimetype='application/json'
            )
        deviceId = request.args.get('DeviceId')
        os = request.args.get('os')
        action(token, deviceId, os)
        jk = JK.query.filter_by(id=user.jk).first()
        if not jk:
            return current_app.response_class(
                response=json.dumps(
                    {'error': f'JK NOT MODERATED'}
                ),
                status=400,
                mimetype='application/json'
            )
        chat = ChatRooms.query.filter_by(jk=user.jk).first()
        msgs = []
        messages = Messages.query.filter_by(chat_id=chat.id).all()
        for i in messages:
            author = User.query.filter_by(id=i.author).first()
            msgs.append({
                'id': i.id,
                'profile_photo': url_for('static', filename=f'profile_photos/{author.photo}') if author.photo else '',
                'text': i.text,
                'time': i.timestamp.strftime('%H:%M'),
                'timestamp': i.timestamp.timestamp(),
                'author': i.author,
                'name': f'{author.name} {author.surname}' if not author.org else author.org_name,
                'image': url_for('static', filename=f'messages/{i.image}') if i.image else ''
            })
        db.session.commit()
        return current_app.response_class(
            response=json.dumps(
                {
                    'messages': msgs,
                    'profile_photo': url_for('static', filename=f'jk/{jk.photo if jk.photo else "default_org.png"}'),
                    'name': jk.name,
                    'chat_id': chat.id,
                    'users': len(User.query.filter_by(jk=jk.id).all()),
                    'online': len(User.query.filter_by(jk=jk.id, status='active').all()),
                }
            ),
            status=200,
            mimetype='application/json'
        )
    except Exception as e:
        return current_app.response_class(
            response=json.dumps(
                {'error': f'ERROR: {e}!'}
            ),
            status=400,
            mimetype='application/json'
        )


@api.route('/api/jk_chat_members', methods=['GET'])
def jk_chat_members():
    """
    ---
   get:
     summary: Юзеры в чате ЖК
     parameters:
         - in: query
           name: token
           schema:
             type: string
             example: 5zqxZa16b0vEE1sx$9a74b2452862f8b0061a5356079f69c3b83af9aec7430d070901f745b984a3f9
           description: token
         - in: query
           name: OS
           schema:
             type: string
             example: Android
           description: OS
         - in: query
           name: DeviceID
           schema:
             type: string
             example: Gnx786nzdg758
           description: DeviceID
     responses:
       '200':
         description: Результат
         content:
           application/json:
             schema:      # Request body contents
               type: object
               properties:
                   members:
                     type: array
                     items:
                       type: object
                       properties:
                           id:
                             type: integer
                           phone:
                             type: string
                           status:
                             type: string
                           user:
                             type: string
                           profile_photo:
                             type: string
                           last_updated:
                             type: string
                   profile_photo:
                     type: string
                   name:
                     type: string
                   chat_id:
                     type: integer
                   users:
                     type: integer
                   online:
                     type: integer
       '400':
         description: Не передан обязательный параметр
         content:
           application/json:
             schema: ErrorSchema
       '401':
         description: Неверный токен
         content:
           application/json:
             schema: ErrorSchema
       '403':
         description: Пользователь заблокирован
         content:
           application/json:
             schema: ErrorSchema
     tags:
       - chats
    """
    try:
        token = request.args.get('token')
        user = User.query.filter_by(token=token).first()
        if not user:
            return current_app.response_class(
                response=json.dumps(
                    {'error': f'USER DOES NOT EXIST'}
                ),
                status=403,
                mimetype='application/json'
            )
        if user.status == "blocked":
            return current_app.response_class(
                response=json.dumps(
                    {'error': "USER BLOCKED"}
                ),
                status=403,
                mimetype='application/json'
            )
        deviceId = request.args.get('DeviceId')
        os = request.args.get('os')
        action(token, deviceId, os)
        jk = JK.query.filter_by(id=user.jk).first()
        if not jk:
            return current_app.response_class(
                response=json.dumps(
                    {'error': f'JK NOT MODERATED'}
                ),
                status=400,
                mimetype='application/json'
            )
        chat = ChatRooms.query.filter_by(jk=user.jk).first()
        members_ = User.query.filter_by(jk=jk.id).all()
        members = []
        for i in members_:
            members.append(
                {
                    'id': i.id,
                    'phone': i.phone,
                    'status': i.status,
                    'user': f'{i.name} {i.surname}' if not i.org else f'{i.org_name}',
                    'profile_photo': url_for('static', filename=f'profile_photos/{i.photo}'),
                    'last_updated': datetime.datetime.fromtimestamp(i.last_updated).strftime('%H:%M'),
                }
            )
        return current_app.response_class(
            response=json.dumps(
                {
                    'members': members,
                    'profile_photo': url_for('static', filename=f'jk/{jk.photo if jk.photo else "default_org.png"}'),
                    'name': jk.name,
                    'chat_id': chat.id,
                    'users': len(User.query.filter_by(jk=jk.id).all()),
                    'online': len(User.query.filter_by(jk=jk.id, status='active').all()),
                }
            ),
            status=200,
            mimetype='application/json'
        )
    except Exception as e:
        return current_app.response_class(
            response=json.dumps(
                {'error': f'ERROR: {e}!'}
            ),
            status=400,
            mimetype='application/json'
        )


@api.route('/api/delete_msg', methods=['GET'])
def delete_msg():
    """
   ---
   get:
     summary: Удалить свое сообщение
     parameters:
         - in: query
           name: msg_id
           schema:
             type: integer
             example: 1
           description: msg_id
         - in: query
           name: token
           schema:
             type: string
             example: 5zqxZa16b0vEE1sx$9a74b2452862f8b0061a5356079f69c3b83af9aec7430d070901f745b984a3f9
           description: token
         - in: query
           name: OS
           schema:
             type: string
             example: Android
           description: OS
         - in: query
           name: DeviceID
           schema:
             type: string
             example: Gnx786nzdg758
           description: DeviceID
     responses:
       '200':
         description: Результат
         content:
           application/json:
             schema:      # Request body contents
               type: object
               properties:
                   status:
                     type: string
       '400':
         description: Не передан обязательный параметр
         content:
           application/json:
             schema: ErrorSchema
       '401':
         description: Неверный токен
         content:
           application/json:
             schema: ErrorSchema
       '403':
         description: Пользователь заблокирован
         content:
           application/json:
             schema: ErrorSchema
     tags:
       - chats
    """
    try:
        msg_id = request.args.get('msg_id')
        token = request.args.get('token')
        user = User.query.filter_by(token=token).first()
        if not user:
            return current_app.response_class(
                response=json.dumps(
                    {'error': f'USER DOES NOT EXIST'}
                ),
                status=403,
                mimetype='application/json'
            )
        if user.status == "blocked":
            return current_app.response_class(
                response=json.dumps(
                    {'error': "USER BLOCKED"}
                ),
                status=403,
                mimetype='application/json'
            )
        deviceId = request.args.get('DeviceId')
        os = request.args.get('os')
        action(token, deviceId, os)
        msg = Messages.query.filter_by(id=msg_id).first()
        if not msg:
            return current_app.response_class(
                response=json.dumps(
                    {
                        'status': 'MESSAGE NOT FOUND',
                    }
                ),
                status=200,
                mimetype='application/json'
            )
        if msg.author == user.id:
            _ = Messages.query.filter_by(id=msg_id).delete()
            db.session.commit()
            return current_app.response_class(
                response=json.dumps(
                    {
                        'status': 'ok',
                    }
                ),
                status=200,
                mimetype='application/json'
            )
        else:
            return current_app.response_class(
                response=json.dumps(
                    {'error': "YOU CANNOT DELETE THIS MSG"}
                ),
                status=403,
                mimetype='application/json'
            )
    except Exception as e:
        return current_app.response_class(
            response=json.dumps(
                {'error': f'ERROR: {e}!'}
            ),
            status=400,
            mimetype='application/json'
        )


@api.route('/api/connect', methods=['GET'])
def connect():
    """
    ---
   get:
     summary: Перейти в чат с пользователем
     parameters:
         - in: query
           name: user_id
           schema:
             type: integer
             example: 2
           description: user_id
         - in: query
           name: token
           schema:
             type: string
             example: 5zqxZa16b0vEE1sx$9a74b2452862f8b0061a5356079f69c3b83af9aec7430d070901f745b984a3f9
           description: token
         - in: query
           name: OS
           schema:
             type: string
             example: Android
           description: OS
         - in: query
           name: DeviceID
           schema:
             type: string
             example: Gnx786nzdg758
           description: DeviceID
     responses:
       '200':
         description: Результат
         content:
           application/json:
             schema:      # Request body contents
               type: object
               properties:
                   messages:
                     type: array
                     items:
                       type: object
                       properties:
                           id:
                             type: integer
                           profile_photo:
                             type: string
                           text:
                             type: string
                           time:
                             type: string
                           timestamp:
                             type: number
                           author:
                             type: integer
                           name:
                             type: string
                           image:
                             type: string
                   profile_photo:
                     type: string
                   name:
                     type: string
                   chat_id:
                     type: string
       '400':
         description: Не передан обязательный параметр
         content:
           application/json:
             schema: ErrorSchema
       '401':
         description: Неверный токен
         content:
           application/json:
             schema: ErrorSchema
       '403':
         description: Пользователь заблокирован
         content:
           application/json:
             schema: ErrorSchema
     tags:
       - chats
    """
    try:
        user_id = request.args.get('user_id')
        token = request.args.get('token')
        user = User.query.filter_by(token=token).first()
        if not user:
            return current_app.response_class(
                response=json.dumps(
                    {'error': f'USER DOES NOT EXIST'}
                ),
                status=403,
                mimetype='application/json'
            )
        if user.status == "blocked":
            return current_app.response_class(
                response=json.dumps(
                    {'error': "USER BLOCKED"}
                ),
                status=403,
                mimetype='application/json'
            )
        deviceId = request.args.get('DeviceId')
        os = request.args.get('os')
        action(token, deviceId, os)
        chats = ChatRooms.query.filter_by(user1=user_id, user2=user.id).all() + \
                ChatRooms.query.filter_by(user2=user_id, user1=user.id).all()
        if chats:
            chat = chats[0]
        else:
            new_chat = ChatRooms(type='personal', user2=user_id, user1=user.id)
            db.session.add(new_chat)
            db.session.commit()
            chat = new_chat
        return redirect(url_for('chats_api.chat_messages', chat_id=chat.id, token=token, DeviceId=deviceId, os=os))
    except Exception as e:
        return current_app.response_class(
            response=json.dumps(
                {'error': f'ERROR: {e}!'}
            ),
            status=400,
            mimetype='application/json'
        )

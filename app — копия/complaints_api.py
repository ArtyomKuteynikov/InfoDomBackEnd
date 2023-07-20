# api.py
import datetime
import json
from flask import Blueprint, request, current_app
from werkzeug.security import generate_password_hash
import base64
from PIL import Image
from io import BytesIO
from . import db
from .models import User, Codes, JK, Points, Promotions, PointsTypes, News, Addresses, Complaints
from iqsms_rest import Gate
import random
import time
from .config import *
from dadata import Dadata
from os import getcwd
from .api import action

api = Blueprint('complaints_api', __name__)


@api.route('/api/complain', methods=['POST'])
def complain():
    """
        ---
        post:
          summary: Разместить жалобу
          parameters:
              - in: query
                name: token
                schema:
                  type: string
                  example: inHMylyABcnlhUR6$ecae409c0045c77e815d4399aeab0cc7f219225770145f0a6b64dc35c08627be
                description: Токен
              - in: query
                name: OS
                schema:
                  type: string
                  example: Android
                description: Операционная система
              - in: query
                name: DeviceID
                schema:
                  type: string
                  example: Gnx786nzdg758
                description: DeviceID
              - in: query
                name: type
                schema:
                  type: string
                  example: promotion
                description: promotion - объявление, new - новость, profile - профиль, message_personal - сообщение личный чат, message_jk - сообщение чат жк
              - in: query
                name: message_id
                schema:
                  type: integer
                  example: 0
                description: ID сообщения
              - in: query
                name: promotion_id
                schema:
                  type: integer
                  example: 1
                description: ID объявления
              - in: query
                name: new_id
                schema:
                  type: integer
                  example: 0
                description: ID новости
              - in: query
                name: profile_id
                schema:
                  type: integer
                  example: 0
                description: ID профиля
          requestBody:
            required: true
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    text:
                        type: string
                  example:   # Sample object
                    text: Меня это обижает
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
                    example:   # Sample object
                      status: ok
            '401':
              description: Пользователь не найден
              content:
                application/json:
                  schema: ErrorSchema
            '403':
              description: Пользователь заблокирован
              content:
                application/json:
                  schema: ErrorSchema
            '400':
              description: Не передан обязательный параметр
              content:
                application/json:
                  schema: ErrorSchema
        tags:
            - complaints
        """
    try:
        token = request.args.get('token')
        type = request.args.get('type')
        message_id = request.args.get('message_id')
        promotion_id = request.args.get('promotion_id')
        new_id = request.args.get('new_id')
        profile_id = request.args.get('profile_id')
        text = request.json.get('text')
        user = User.query.filter_by(token=token).first()
        if user:
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
            new_new = Complaints(from_user=user.id, type=type, text=text, message_id=message_id, profile_id=profile_id,
                           promotion_id=promotion_id, new_id=new_id)
            db.session.add(new_new)
            db.session.commit()
            return current_app.response_class(
                response=json.dumps(
                    {'status': 'ok'}
                ),
                status=200,
                mimetype='application/json'
            )
        else:
            return current_app.response_class(
                response=json.dumps(
                    {'error': 'User not found'}
                ),
                status=401,
                mimetype='application/json'
            )
    except Exception as e:
        print(e)
        return current_app.response_class(
            response=json.dumps(
                {'error': f'ERROR: {e}!'}
            ),
            status=400,
            mimetype='application/json'
        )

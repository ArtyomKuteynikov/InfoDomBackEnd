# api.py
import datetime
import json
from flask import Blueprint, request, current_app, url_for
from werkzeug.security import generate_password_hash
import base64
from PIL import Image
from io import BytesIO
from . import db
from .models import User, Codes, JK, Points, Promotions, PointsTypes, News, Addresses
from iqsms_rest import Gate
import random
import time
from .config import *
from dadata import Dadata
from os import getcwd

auth_api = Blueprint('auth_api', __name__)


def action(token, deviceId, os):
    if User.query.filter_by(token=token).first():
        print(2)
        if User.query.filter_by(token=token).first().status in ['inactive', 'active']:
            _ = User.query.filter_by(token=token).update(
                {'deviceId': deviceId, 'os': os, 'last_updated': int(time.time()), 'status': 'active'})
            db.session.commit()


@auth_api.route('/api/auth')
def auth():
    """
    ---
    get:
      summary: Проверка номера телефона
      parameters:
          - in: query
            name: phone
            schema:
              description: Phone number
              type: string
              example: 79151290127
            description: Номер телефона
      responses:
        '200':
          description: Результат
          content:
            application/json:
              schema:      # Request body contents
                  type: object
                  properties:
                    result:
                      type: boolean
                  example:   # Sample object
                    result: true
        '400':
          description: Не передан обязательный параметр
          content:
            application/json:
              schema: ErrorSchema
      tags:
        - auth
    """
    try:
        phone = request.args.get('phone')
        if User.query.filter_by(phone=phone).first():
            return current_app.response_class(
                response=json.dumps(
                    {'result': True}
                ),
                status=200,
                mimetype='application/json'
            )
        else:
            return current_app.response_class(
                response=json.dumps(
                    {'result': False}
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


@auth_api.route('/api/send-code')
def send_code():
    """
    ---
    get:
      summary: Отправить код подтверждения
      parameters:
          - in: query
            name: phone
            schema:
              description: Phone number
              type: string
              example: 79151290127
            description: Номер телефона
      responses:
        '200':
          description: Результат
          content:
            application/json:
              schema:      # Request body contents
                  type: object
                  properties:
                    result:
                      type: string
                    status:
                        type: string
                  example:   # Sample object
                    result: Сообщение отправлено
                    status: ok
        '400':
          description: Не передан обязательный параметр
          content:
            application/json:
              schema: ErrorSchema
      tags:
        - auth
    """
    try:
        phone = request.args.get('phone')
        if phone == "79151290127":
            code = 1234
            new_code = Codes(code=code, phone=phone)
            db.session.add(new_code)
            db.session.commit()
            # sender = Gate(SMS_LOGIN, SMS_PASSWORD)
            status = 'accepted;1234'
        else:
            code = random.randint(1001, 9999)
            new_code = Codes(code=code, phone=phone)
            db.session.add(new_code)
            db.session.commit()
            sender = Gate(SMS_LOGIN, SMS_PASSWORD)
            status = sender.send_message(phone, f'Ваш код для авторизации в приложении\n{code}', 'SMS DUCKOHT')
        if status.split(';')[0] == 'accepted':
            return current_app.response_class(
                response=json.dumps(
                    {'result': status,
                     'status': 'ok'}
                ),
                status=200,
                mimetype='application/json'
            )
        else:
            return current_app.response_class(
                response=json.dumps(
                    {'result': status,
                     'status': 'error'}
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


@auth_api.route('/api/check-code')
def check_code():
    """
    ---
    get:
      summary: Проверить код подтверждения
      parameters:
          - in: query
            name: code
            schema:
              type: string
              example: 1234
            description: SMS код
          - in: query
            name: phone
            schema:
              type: string
              example: 79151290127
            description: Номер телефона
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
      responses:
        '200':
          description: Результат
          content:
            application/json:
              schema:      # Request body contents
                  type: object
                  properties:
                    status:
                        type: bool
                    user:
                        type: string
                  example:   # Sample object
                    status: true
                    user: inHMylyABcnlhUR6$ecae409c0045c77e815d4399aeab0cc7f219225770145f0a6b64dc35c08627be

        '403':
          description: Пользователь заблокирован
          content:
            application/json:
              schema: ErrorSchema

        '401':
          description: Неверный код
          content:
            application/json:
              schema: ErrorSchema
        '400':
          description: Не передан обязательный параметр
          content:
            application/json:
              schema: ErrorSchema
      tags:
        - auth
    """
    try:
        phone = request.args.get('phone')
        if User.query.filter_by(phone=phone).first():
            user = User.query.filter_by(phone=phone).first()
            if User.query.filter_by(phone=phone).first().status == "blocked":
                return current_app.response_class(
                    response=json.dumps(
                        {'error': "USER BLOCKED"}
                    ),
                    status=403,
                    mimetype='application/json'
                )
            else:
                deviceId = request.args.get('DeviceId')
                os = request.args.get('os')
                action(user.token, deviceId, os)
            token = user.token
        else:
            token = None
        code = request.args.get('code')
        if Codes.query.filter_by(phone=phone).first():
            if token:
                if datetime.datetime.fromtimestamp(time.time()).day > datetime.datetime.fromtimestamp(
                        user.last_updated).day:
                    new_points = Points(user_id=User.query.filter_by(phone=phone).first().id, side=1, quantity=1,
                                        type=3, timestamp=time.time())
                    points = User.query.filter_by(phone=phone).first().points
                    if not points:
                        points = 0
                    User.query.filter_by(phone=phone).update({'points': float(points) + 1})
                    db.session.add(new_points)
                    db.session.commit()
            if Codes.query.filter_by(phone=phone).all()[-1].code == code:
                return current_app.response_class(
                    response=json.dumps(
                        {'status': True,
                         'user': token}
                    ),
                    status=200,
                    mimetype='application/json'
                )
            else:
                return current_app.response_class(
                    response=json.dumps(
                        {'status': False,
                         'user': None}
                    ),
                    status=200,
                    mimetype='application/json'
                )
        else:
            return current_app.response_class(
                response=json.dumps(
                    {'error': "Invalid code"}
                ),
                status=401,
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


@auth_api.route('/api/get-jk')
def get_jk():
    """
    ---
    get:
      summary: Получить информацию о ЖК по адресу
      parameters:
          - in: query
            name: address
            schema:
              description: Адрес
              type: string
              example: 108804, г Москва, поселение Кокошкино, Новомосковский округ, дп Кокошкино, ул Пушкина, д 5
            description: Адрес
      responses:
        '200':
          description: Результат
          content:
            application/json:
              schema:      # Request body contents
                  type: object
                  properties:
                    jk_id:
                        type: integer
                    jk_name:
                        type: string
                  example:   # Sample object
                    jk_id: 1
                    jk_name: "ЖК Паруса"
        '404':
          description: ЖК не найден
          content:
            application/json:
              schema: ErrorSchema
        '400':
          description: Не передан обязательный параметр
          content:
            application/json:
              schema: ErrorSchema
      tags:
        - auth
    """
    try:
        address = request.args.get('address')
        jk = Addresses.query.filter_by(name=address).first()
        if jk:
            jk = JK.query.filter_by(id=jk.jk_id).first()
            return current_app.response_class(
                response=json.dumps(
                    {'jk_id': jk.id,
                     'jk_name': jk.name}
                ),
                status=200,
                mimetype='application/json'
            )
        else:
            return current_app.response_class(
                response=json.dumps(
                    {'error': f'ЖК не найден'}
                ),
                status=404,
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


@auth_api.route('/api/get-addresses')
def get_addresses():
    """
    ---
    get:
      summary: Получить информацию о ЖК по адресу
      parameters:
          - in: query
            name: address
            schema:
              description: Адрес
              type: string
              example: Россия, г. Москва, ул. Госпитальный вал, д. 3
            description: Адрес
      responses:
        '200':
          description: Результат
          content:
            application/json:
              schema:      # Request body contents
                  type: object
                  properties:
                    list:
                        type: array
                        items:
                            name:
                                type: string
        '404':
          description: ЖК не найден
          content:
            application/json:
              schema: ErrorSchema
        '400':
          description: Не передан обязательный параметр
          content:
            application/json:
              schema: ErrorSchema
      tags:
        - auth
    """
    try:
        address = request.args.get('address')
        dadata = Dadata(DADATA)
        result = dadata.suggest("address", address, 10)
        addresses = []
        for i in result:
            addresses.append({
                'name': i['unrestricted_value']
            })
        return current_app.response_class(
            response=json.dumps(
                {'list': addresses}
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


@auth_api.route('/api/sign_up', methods=['GET', 'POST'])
def sign_up():
    """
    ---
    post:
      summary: Регистрация
      parameters:
          - in: query
            name: org
            schema:
              description: организация или жилец(1 если организация, 0 если жилец)
              type: integer
              example: 1
            description: организация или жилец(1 если организация, 0 если жилец)
          - in: query
            name: phone
            schema:
              description: номер телефона
              type: string
              example: 79151290127
            description: номер телефона
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
      requestBody:
        content:
          application/json:
              schema:
                type: object
                properties:
                    name:
                        type: string
                    surname:
                        type: string
                    second_name:
                        type: string
                    address:
                        type: string
                    jk:
                        type: string
                    jk_exist:
                        type: integer
                    inn:
                        type: string
                    org_name:
                        type: string
                    is_uk:
                        type: integer
                example:   # Sample object
                    name: Иван
                    surname: Иванов
                    second_name: Иванович
                    address: 108804, г Москва, поселение Кокошкино, Новомосковский округ, дп Кокошкино, ул Пушкина, д 5
                    jk_exist: 1
                    jk: 1
                    inn: 86869878978
                    org_name: ООО Ромашка
                    is_uk: 0
      responses:
        '200':
          description: Результат
          content:
            application/json:
              schema:      # Request body contents
                  type: object
                  properties:
                    token:
                        type: string
                  example:   # Sample object
                    token: inHMylyABcnlhUR6$ecae409c0045c77e815d4399aeab0cc7f219225770145f0a6b64dc35c08627be
        '403':
          description: Пользователь с таким телефоном уже существует
          content:
            application/json:
              schema: ErrorSchema
        '400':
          description: Не передан обязательный параметр
          content:
            application/json:
              schema: ErrorSchema
      tags:
        - auth
    """
    try:
        phone = request.args.get('phone')
        name = request.json.get('name')
        surname = request.json.get('surname')
        org = int(request.args.get('org'))
        address = request.json.get('address')
        jk_exist = int(request.json.get('jk_exist'))
        jk = request.json.get('jk')
        if org:
            second_name = request.json.get('second_name')
            inn = request.json.get('inn')
            org_name = request.json.get('org_name')
            is_uk = request.json.get('is_uk')
        if User.query.filter_by(phone=phone).first():
            return current_app.response_class(
                response=json.dumps(
                    {'error': f'USER EXIST'}
                ),
                status=403,
                mimetype='application/json'
            )
        if not jk_exist:
            dadata = Dadata(DADATA)
            result = dadata.suggest("address", address, 10)[0]['data']
            new_jk = JK(name=request.json.get('jk'), city=result['city'], moderated=0)
            db.session.add(new_jk)
            db.session.commit()
            jk = new_jk.id
            new_address = Addresses(name=address, city=result['city'], street=result['street'], jk_id=jk)
            db.session.add(new_address)
            db.session.commit()
        token = generate_password_hash(phone, method='sha256').replace('sha256$', '')
        if org:
            if is_uk:
                new_user = User(phone=phone, name=name, surname=surname, second_name=second_name, org=1, address=address,
                                inn=inn, org_name=org_name, status="active", token=token, jk=jk, points=10, is_uk=is_uk,
                                registered=int(time.time()), photo='default_uk.png')
            else:
                new_user = User(phone=phone, name=name, surname=surname, second_name=second_name, org=1, address=address,
                                inn=inn, org_name=org_name, status="active", token=token, jk=jk, points=10, is_uk=is_uk,
                                registered=int(time.time()), photo='default_org.png')
            db.session.add(new_user)
            db.session.commit()
        else:
            new_user = User(phone=phone, name=name, surname=surname, org=1, address=address,
                            status="active", token=token, jk=jk, points=10, registered=int(time.time()))
            db.session.add(new_user)
            db.session.commit()
        deviceId = request.args.get('DeviceID')
        os = request.args.get('OS')
        action(token, deviceId, os)
        new_points = Points(user_id=new_user.id, side=1, quantity=10, type=1, timestamp=time.time())
        db.session.add(new_points)
        db.session.commit()
        return current_app.response_class(
            response=json.dumps(
                {'token': token}
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


@auth_api.route('/api/referer')
def referer():
    """
    ---
    get:
      summary: Ввести код пригласившего
      parameters:
          - in: query
            name: phone
            schema:
              description: Phone number
              type: string
              example: 79151290127
            description: Номер телефона
          - in: query
            name: token
            schema:
              description: Токен
              type: string
              example: inHMylyABcnlhUR6$ecae409c0045c77e815d4399aeab0cc7f219225770145f0a6b64dc35c08627be
            description: Токен
      responses:
        '200':
          description: Результат
          content:
            application/json:
              schema:      # Request body contents
                  type: object
                  properties:
                    result:
                      type: string
                    status:
                        type: string
                  example:   # Sample object
                    result: Сообщение отправлено
                    status: ok
        '401':
          description: Неверный токен
          content:
            application/json:
              schema: ErrorSchema
        '404':
          description: Нет такого номера телефона в базе
          content:
            application/json:
              schema: ErrorSchema
        '400':
          description: Не передан обязательный параметр
          content:
            application/json:
              schema: ErrorSchema
      tags:
        - auth
    """
    try:
        phone = request.args.get('phone')
        token = request.args.get('token')
        if not User.query.filter_by(token=token).first():
            return current_app.response_class(
                response=json.dumps(
                    {'result': 'User not found',
                     'status': 'error'}
                ),
                status=401,
                mimetype='application/json'
            )
        new_points = Points(user_id=User.query.filter_by(phone=phone).first().id, side=1, quantity=5, type=2,
                            timestamp=time.time())
        if User.query.filter_by(phone=phone).first() and not User.query.filter_by(token=token).first().referer:
            points = User.query.filter_by(phone=phone).first().points
            _ = User.query.filter_by(token=token).update({'referer': User.query.filter_by(phone=phone).first().id})
            if not points:
                points = 0
            User.query.filter_by(phone=phone).update({'points': float(points) + 5})
            db.session.add(new_points)
            db.session.commit()
            sender = Gate(SMS_LOGIN, SMS_PASSWORD)
            status = sender.send_message(phone, f'Поздравляем, вам начислен бонус - 5 баллов за приглашенного друга!',
                                         'SMS DUCKOHT')
            if status.split(';')[0] == 'accepted':
                return current_app.response_class(
                    response=json.dumps(
                        {'result': status,
                         'status': 'ok'}
                    ),
                    status=200,
                    mimetype='application/json'
                )
            else:
                return current_app.response_class(
                    response=json.dumps(
                        {'result': status,
                         'status': 'error'}
                    ),
                    status=400,
                    mimetype='application/json'
                )
        else:
            return current_app.response_class(
                response=json.dumps(
                    {'result': 'Пользователь не найден',
                     'status': 'error'}
                ),
                status=404,
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


@auth_api.route('/api/logout')
def logout():
    """
---
get:
  summary: Выйти
  parameters:
      - in: query
        name: token
        schema:
          description: Токен
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
      description: Не верный токен
      content:
        application/json:
          schema: ErrorSchema
    '400':
      description: Не передан обязательный параметр
      content:
        application/json:
          schema: ErrorSchema
  tags:
    - auth
"""
    try:
        token = request.args.get('token')
        if not User.query.filter_by(token=token).first():
            return current_app.response_class(
                response=json.dumps(
                    {'error': f'USER DOES NOT EXIST'}
                ),
                status=403,
                mimetype='application/json'
            )
        if User.query.filter_by(token=token).first().status == "blocked":
            return current_app.response_class(
                response=json.dumps(
                    {'error': "USER BLOCKED"}
                ),
                status=403,
                mimetype='application/json'
            )
        else:
            deviceId = request.args.get('DeviceId')
            os = request.args.get('os')
            action(token, deviceId, os)
            user = User.query.filter_by(token=token).first()
            User.query.filter_by(token=token).update({'status': 'incative', "token": generate_password_hash(user.phone,
                                                                                                            method='sha256').replace(
                'sha256$', '')})
            db.session.commit()
            return current_app.response_class(
                response=json.dumps(
                    {
                        "status": "ok"
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


@auth_api.route('/api/profile')
def profile():
    """
    ---
    get:
      summary: Профиль
      parameters:
          - in: query
            name: token
            schema:
              description: Токен
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
      responses:
        '200':
          description: Результат
          content:
            application/json:
              schema:      # Request body contents
                  type: object
                  properties:
                    photo:
                        type: string
                    org:
                        type: integer
                    phone:
                        type: string
                    name:
                        type: string
                    surname:
                        type: string
                    second_name:
                        type: string
                    status:
                        type: string
                    address:
                        type: string
                    jk_name:
                        type: string
                    jk:
                        type: string
                    inn:
                        type: string
                    org_name:
                        type: string
                    is_uk:
                        type: integer
                  example:   # Sample object
                    photo: /static/profile_photos/1.png
                    org: 1
                    phone: 79151290127
                    name: Иван
                    surname: Иванов
                    second_name: Иванович
                    status: active
                    address: 108804, г Москва, поселение Кокошкино, Новомосковский округ, дп Кокошкино, ул Пушкина, д 5
                    jk: 1
                    jk_name: ЖК Ромашка
                    inn: 86869878978
                    org_name: ООО Ромашка
                    is_uk: 0
        '401':
          description: Не верный токен
          content:
            application/json:
              schema: ErrorSchema
        '400':
          description: Не передан обязательный параметр
          content:
            application/json:
              schema: ErrorSchema
      tags:
        - auth
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
        if user.photo:
            photo = url_for('static', filename=f"profile_photos/{user.photo}")
        else:
            photo = ''
        if JK.query.filter_by(id=user.jk).first():
            jk_name = JK.query.filter_by(id=user.jk).first().name
        else:
            jk_name = ""
        return current_app.response_class(
            response=json.dumps(
                {
                    "photo": photo,
                    "org": user.org,
                    "phone": user.phone,
                    "name": user.name,
                    "surname": user.surname,
                    "second_name": user.second_name,
                    "status": user.status,
                    "address": user.address,
                    "jk": user.jk,
                    "jk_name": jk_name,
                    "inn": user.inn,
                    "org_name": user.org_name,
                    "is_uk": user.is_uk
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


@auth_api.route('/api/edit_profile', methods=['POST'])
def edit_profile():
    """
    ---
    post:
      summary: Редактировать профиль
      parameters:
          - in: query
            name: token
            schema:
              type: string
              example: inHMylyABcnlhUR6$ecae409c0045c77e815d4399aeab0cc7f219225770145f0a6b64dc35c08627be
            description: токен
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
      requestBody:
        required: true
        content:
          application/json:
              schema:
                type: object
                properties:
                    photo:
                        type: string
                        description: Фото Base64
                    name:
                        type: string
                        description: Имя
                    surname:
                        type: string
                        description: Фамилия
                    second_name:
                        type: string
                        description: Отчество
                    address:
                        type: string
                        description: Адрес
                    jk:
                        type: string
                        description: ID ЖК
                    jk_exist:
                        type: integer
                        description: Существует ли такой ЖК в базе
                    inn:
                        type: string
                        description: ИНН
                    org_name:
                        type: string
                        description: Наименование организации
                    is_uk:
                        type: integer
                        description: Является ли УК
                example:   # Sample object
                    photo: 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
                    name: Иван
                    surname: Иванов
                    second_name: Иванович
                    status: active
                    address: 108804, г Москва, поселение Кокошкино, Новомосковский округ, дп Кокошкино, ул Пушкина, д 5
                    jk_exist: 1
                    jk: 1
                    inn: 86869878978
                    org_name: ООО Ромашка
                    is_uk: 0
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
          description: Неверный токен
          content:
            application/json:
              schema: ErrorSchema
        '400':
          description: Не передан обязательный параметр
          content:
            application/json:
              schema: ErrorSchema
      tags:
        - auth
    """
    try:
        token = request.args.get('token')
        user = User.query.filter_by(token=token).first()
        photo = request.json.get('photo')
        name = request.json.get('name')
        surname = request.json.get('surname')
        address = request.json.get('address')
        jk_exist = int(request.json.get('jk_exist'))
        jk = request.json.get('jk')
        if not user:
            return current_app.response_class(
                response=json.dumps(
                    {'error': f'Incorrect TOKEN'}
                ),
                status=401,
                mimetype='application/json'
            )
        if user.org:
            second_name = request.json.get('second_name')
            inn = request.json.get('inn')
            org_name = request.json.get('org_name')
            is_uk = request.json.get('is_uk')

        if photo:
            im = Image.open(BytesIO(base64.b64decode(photo)))
            im.save(f"{getcwd()}/app/static/profile_photos/{user.id}.png")
            _ = User.query.filter_by(token=token).update(
                {'photo': f'{user.id}.png'})
            db.session.commit()
        if User.query.filter_by(token=token).first().status == "blocked":
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
        if not jk_exist:
            new_jk = JK(name=jk)
            db.session.add(new_jk)
            db.session.commit()
            jk = new_jk.id
        if user.org:
            _ = User.query.filter_by(id=user.id).update({'name': name, 'surname': surname, 'second_name': second_name,
                                                         'address': address, 'inn': inn, 'org_name': org_name,
                                                         'jk': jk, 'is_uk': is_uk})
        else:
            _ = User.query.filter_by(id=user.id).update(
                {'name': name, 'surname': surname, 'address': address, 'jk': jk})
        db.session.commit()
        return current_app.response_class(
            response=json.dumps(
                {'status': f'ok'}
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


@auth_api.route('/api/points')
def points():
    """
    ---
    get:
      summary: Профиль
      parameters:
          - in: query
            name: token
            schema:
              description: Токен
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
      responses:
        '200':
          description: Результат
          content:
            application/json:
              schema:      # Request body contents
                  type: object
                  properties:
                    list:
                      type: array
                      items:
                          type: object
                          properties:
                            id:
                              type: integer
                            side:
                              type: integer
                            quantity:
                              type: number
                            description:
                              type: string
        '403':
          description: Пользователь заблокирован
          content:
            application/json:
              schema: ErrorSchema
        '401':
          description: Не верный токен
          content:
            application/json:
              schema: ErrorSchema
        '400':
          description: Не передан обязательный параметр
          content:
            application/json:
              schema: ErrorSchema
      tags:
        - auth
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
        else:
            deviceId = request.args.get('DeviceId')
            os = request.args.get('os')
            action(token, deviceId, os)
            points = Points.query.filter_by(user_id=user.id).all()
        return current_app.response_class(
            response=json.dumps(
                {"list": [{
                    "id": point.id,
                    "side": point.side,
                    "quantity": point.quantity,
                    "description": PointsTypes.query.filter_by(id=point.type).first().name} for point in points]
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

# api.py
import datetime
import json

import base64
from PIL import Image
from io import BytesIO
from flask import Blueprint, request, current_app, url_for
from werkzeug.security import generate_password_hash
from os import getcwd
from . import db
from .models import User, Codes, JK, Points, Promotions, PointsTypes, News, Addresses
from iqsms_rest import Gate
import random
import time
from .config import *
from dadata import Dadata

promotions_api = Blueprint('promotions_api', __name__)

'''
if User.query.filter_by(token=token).first().status == "blocked":
    return current_app.response_class(
        response=json.dumps(
            {'error': "USER BLOCKED"}
        ),
        status=403,
        mimetype='application/json'
    )
'''


def action(token, deviceId, os):
    if User.query.filter_by(token=token).first():
        print(2)
        if User.query.filter_by(token=token).first().status in ['inactive', 'active']:
            _ = User.query.filter_by(token=token).update(
                {'deviceId': deviceId, 'os': os, 'last_updated': int(time.time()), 'status': 'active'})
            db.session.commit()


@promotions_api.route('/api/promotions')
def get_promotions():
    """
    ---
    get:
      summary: Получить все объявления по ЖК(если ЖК=0 - все объявления)
      parameters:
          - in: query
            name: jk
            schema:
              type: string
              example: 1
            description: ID ЖК юзера
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
                            price:
                              type: number
                            address:
                              type: string
                            name:
                              type: string
        '400':
          description: Не передан обязательный параметр
          content:
            application/json:
              schema: ErrorSchema
      tags:
        - promotions
    """
    try:
        jk = request.args.get('jk')
        token = request.args.get('token')
        deviceId = request.args.get('DeviceId')
        os = request.args.get('os')
        action(token, deviceId, os)
        if str(jk) != '0':
            promotions = Promotions.query.filter_by(jk=jk).all()
        else:
            promotions = Promotions.query.filter_by().all()
        promotions = sorted(promotions, key=lambda x: x.timestamp)[::-1]
        output = []
        for i in promotions:
            if i.photo1:
                photo1 = url_for('static', filename=f"profile_photos/{i.photo1}")
            else:
                photo1 = ''
            if i.photo2:
                photo2 = url_for('static', filename=f"profile_photos/{i.photo2}")
            else:
                photo2 = ''
            if i.photo3:
                photo3 = url_for('static', filename=f"profile_photos/{i.photo3}")
            else:
                photo3 = ''
            output.append(
                {
                    'id': i.id,
                    'photo1': photo1,
                    'photo2': photo2,
                    'photo3': photo3,
                    'name': i.name,
                    'price': i.price,
                    'address': i.address
                }
            )
        return current_app.response_class(
            response=json.dumps(
                {'list': output}
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


@promotions_api.route('/api/news')
def get_news():
    """
    ---
    get:
      summary: Получить все новости по ЖК(если ЖК=0 - все объявления)
      parameters:
          - in: query
            name: jk
            schema:
              type: string
              example: 1
            description: ID ЖК юзера
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
                            address:
                              type: string
                            title:
                              type: string
                            description:
                              type: string
                            phone:
                              type: string
                            author:
                              type: string
                            photo:
                              type: string
        '400':
          description: Не передан обязательный параметр
          content:
            application/json:
              schema: ErrorSchema
      tags:
        - news
    """
    try:
        jk = request.args.get('jk')
        if str(jk) != '0':
            news = News.query.filter_by(jk=jk).all()
        else:
            news = News.query.filter_by().all()
        news = sorted(news, key=lambda x: x.timestamp)[::-1]
        output = []
        for i in news:
            user = User.query.filter_by(id=i.author).first()
            output.append(
                {
                    'id': i.id,
                    'title': i.name,
                    'description': i.description,
                    'phone': i.phone,
                    'author': user.name + ' ' + user.surname,
                    'photo': url_for('static', filename=f"profile_photos/{i.photo1}"),
                    'address': i.address
                }
            )
        return current_app.response_class(
            response=json.dumps(
                {'list': output}
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


@promotions_api.route('/api/my-promotions')
def my_promotions():
    """
    ---
    get:
      summary: Получить все объявления пользователя
      parameters:
          - in: query
            name: user
            schema:
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
                    list:
                        type: array
                        items:
                          type: object
                          properties:
                            id:
                              type: integer
                            price:
                              type: number
                            address:
                              type: string
                            title:
                              type: string
                            description:
                              type: string
                            phone:
                              type: string
                            author:
                              type: string
                            photo:
                              type: string
        '400':
          description: Не передан обязательный параметр
          content:
            application/json:
              schema: ErrorSchema
      tags:
        - promotions
    """
    try:
        user = request.args.get('user')
        promotions = Promotions.query.filter_by(author=user).all()
        output = []
        for i in promotions:
            user = User.query.filter_by(id=i.author).first()
            output.append(
                {
                    'id': i.id,
                    'price': i.price,
                    'title': i.name,
                    'description': i.description,
                    'phone': i.phone,
                    'author': user.name + ' ' + user.surname,
                    'photo': url_for('static', filename=f"profile_photos/{i.photo1}"),
                    'address': i.address
                }
            )
        return current_app.response_class(
            response=json.dumps(
                {'list': output}
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


@promotions_api.route('/api/my-news')
def my_news():
    """
    ---
    get:
      summary: Получить все новости пользователя
      parameters:
          - in: query
            name: user
            schema:
              type: string
              example: 1
            description: ID юзера
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
                            address:
                              type: string
                            title:
                              type: string
                            description:
                              type: string
                            phone:
                              type: string
                            author:
                              type: string
                            photo:
                              type: string
        '400':
          description: Не передан обязательный параметр
          content:
            application/json:
              schema: ErrorSchema
      tags:
        - news
    """
    try:
        user = request.args.get('user')
        news = News.query.filter_by(author=user).all()
        output = []
        for i in news:
            user = User.query.filter_by(id=i.author).first()
            output.append(
                {
                    'id': i.id,
                    'title': i.name,
                    'description': i.description,
                    'phone': i.phone,
                    'author': user.name + ' ' + user.surname,
                    'photo': url_for('static', filename=f"profile_photos/{i.photo1}"),
                    'address': i.address
                }
            )
        return current_app.response_class(
            response=json.dumps(
                {'list': output}
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


@promotions_api.route('/api/promotion')
def get_promotion():
    """
    ---
    get:
      summary: Объявление
      parameters:
          - in: query
            name: id
            schema:
              type: string
              example: 1
            description: ID объявления
      responses:
        '200':
          description: Результат
          content:
            application/json:
              schema:      # Request body contents
                  type: object
                  properties:
                    id:
                      type: integer
                    price:
                      type: number
                    address:
                      type: string
                    title:
                      type: string
                    description:
                      type: string
                    phone:
                      type: string
                    author:
                      type: string
                    photo1:
                      type: string
                    photo2:
                      type: string
                    photo3:
                      type: string
        '400':
          description: Не передан обязательный параметр
          content:
            application/json:
              schema: ErrorSchema
      tags:
        - promotions
    """
    try:
        id = request.args.get('id')
        promotion = Promotions.query.filter_by(id=id).first()
        user = User.query.filter_by(id=promotion.author).first()
        out = {
            'id': promotion.id,
            'price': promotion.price,
            'title': promotion.name,
            'description': promotion.description,
            'phone': promotion.phone,
            'author': user.name + ' ' + user.surname,
            'photo1': url_for('static', filename=f"profile_photos/{promotion.photo1}"),
            'photo2': url_for('static', filename=f"profile_photos/{promotion.photo2}"),
            'photo3': url_for('static', filename=f"profile_photos/{promotion.photo3}"),
            'address': promotion.address
        }
        return current_app.response_class(
            response=json.dumps(
                out
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


@promotions_api.route('/api/new')
def get_new():
    """
    ---
    get:
      summary: Новость
      parameters:
          - in: query
            name: id
            schema:
              type: string
              example: 1
            description: ID новости
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
      responses:
        '200':
          description: Результат
          content:
            application/json:
              schema:      # Request body contents
                  type: object
                  properties:
                    id:
                      type: integer
                    address:
                      type: string
                    title:
                      type: string
                    description:
                      type: string
                    phone:
                      type: string
                    author:
                      type: string
                    photo1:
                      type: string
                    photo2:
                      type: string
                    photo3:
                      type: string
        '400':
          description: Не передан обязательный параметр
          content:
            application/json:
              schema: ErrorSchema
      tags:
        - news
    """
    try:
        id = request.args.get('id')
        token = request.args.get('token')
        deviceId = request.args.get('DeviceId')
        os = request.args.get('os')
        action(token, deviceId, os)
        promotion = News.query.filter_by(id=id).first()
        user = User.query.filter_by(id=promotion.author).first()
        out = {
            'id': promotion.id,
            'title': promotion.name,
            'description': promotion.description,
            'phone': promotion.phone,
            'author': user.name + ' ' + user.surname,
            'photo1': url_for('static', filename=f"profile_photos/{promotion.photo1}"),
            'photo2': url_for('static', filename=f"profile_photos/{promotion.photo2}"),
            'photo3': url_for('static', filename=f"profile_photos/{promotion.photo3}"),
            'address': promotion.address
        }
        return current_app.response_class(
            response=json.dumps(
                out
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


@promotions_api.route('/api/add_new', methods=['POST'])
def add_new():
    """
    ---
    post:
      summary: Добавить новость
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
      requestBody:
        required: true
        content:
          application/json:
              schema:
                type: object
                properties:
                    photo1:
                        type: string
                    photo2:
                        type: string
                    photo3:
                        type: string
                    name:
                        type: string
                    address:
                        type: string
                    phone:
                        type: string
                    description:
                        type: string
                example:   # Sample object
                    photo1:
                    photo2:
                    photo3:
                    name: Открылась кафешка
                    address: Россия, г Москва, ул Пушкина, д 5
                    phone: 79151290127
                    description: Классная кафешка
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
          description: Не передан обязательный параметр
          content:
            application/json:
              schema: ErrorSchema
        '400':
          description: Не передан обязательный параметр
          content:
            application/json:
              schema: ErrorSchema
      tags:
        - news
    """
    try:
        # TODO: добавит списание баллов и фотки
        photo1 = request.json.get('photo1')
        photo2 = request.json.get('photo2')
        photo3 = request.json.get('photo3')
        token = request.args.get('token')
        name = request.json.get('name')
        address = request.json.get('address')
        phone = request.json.get('phone')
        description = request.json.get('description')
        user = User.query.filter_by(token=token).first()
        if user:
            deviceId = request.args.get('DeviceId')
            os = request.args.get('os')
            action(token, deviceId, os)
            new_new = News(author=user.id, name=name, address=address, phone=phone, description=description, jk=user.jk
                           , timestamp=time.time())
            db.session.add(new_new)
            db.session.commit()
            if photo1:
                im = Image.open(BytesIO(base64.b64decode(photo1)))
                im.save(f"{getcwd()}/app/static/news/{new_new.id}_1.png")
                _ = News.query.filter_by(id=new_new.id).update(
                    {'photo1': f'{new_new.id}_1.png'})
                db.session.commit()
            if photo2:
                im = Image.open(BytesIO(base64.b64decode(photo2)))
                im.save(f"{getcwd()}/app/static/news/{new_new.id}_2.png")
                _ = News.query.filter_by(id=new_new.id).update(
                    {'photo2': f'{new_new.id}_2.png'})
                db.session.commit()
            if photo3:
                im = Image.open(BytesIO(base64.b64decode(photo3)))
                im.save(f"{getcwd()}/app/static/news{new_new.id}_3.png")
                _ = News.query.filter_by(id=new_new.id).update(
                    {'photo3': f'{new_new.id}_3.png'})
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
        return current_app.response_class(
            response=json.dumps(
                {'error': f'ERROR: {e}!'}
            ),
            status=400,
            mimetype='application/json'
        )


@promotions_api.route('/api/add_promotion', methods=['POST'])
def add_promotion():
    """
    ---
    post:
      summary: Добавить объявление
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
      requestBody:
        required: true
        content:
          application/json:
              schema:
                type: object
                properties:
                    photo1:
                        type: string
                    photo2:
                        type: string
                    photo3:
                        type: string
                    name:
                        type: string
                    address:
                        type: string
                    price:
                        type: number
                    phone:
                        type: string
                    description:
                        type: string
                example:   # Sample object
                    photo1:
                    photo2:
                    photo3:
                    name: Открылась кафешка
                    address: Россия, г Москва, ул Пушкина, д 5
                    price: 1000
                    phone: 79151290127
                    description: Классная кафешка
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
          description: Не передан обязательный параметр
          content:
            application/json:
              schema: ErrorSchema
        '400':
          description: Не передан обязательный параметр
          content:
            application/json:
              schema: ErrorSchema
      tags:
        - promotions
    """
    try:
        photo1 = request.json.get('photo1')
        photo2 = request.json.get('photo2')
        photo3 = request.json.get('photo3')
        token = request.args.get('token')
        name = request.json.get('name')
        price = request.json.get('price')
        address = request.json.get('address')
        phone = request.json.get('phone')
        description = request.json.get('description')
        user = User.query.filter_by(token=token).first()
        if user:
            deviceId = request.args.get('DeviceId')
            os = request.args.get('os')
            action(token, deviceId, os)
            # TODO: добавит списание баллов и фотки
            new_new = Promotions(author=user.id, name=name, price=price, address=address, phone=phone,
                                 description=description, jk=user.jk, timestamp=time.time())
            db.session.add(new_new)
            db.session.commit()
            if photo1:
                im = Image.open(BytesIO(base64.b64decode(photo1)))
                im.save(f"{getcwd()}/app/static/promotions/{new_new.id}_1.png")
                _ = Promotions.query.filter_by(id=new_new.id).update(
                    {'photo1': f'{new_new.id}_1.png'})
                db.session.commit()
            if photo2:
                im = Image.open(BytesIO(base64.b64decode(photo2)))
                im.save(f"{getcwd()}/app/static/promotions/{new_new.id}_2.png")
                _ = Promotions.query.filter_by(id=new_new.id).update(
                    {'photo2': f'{new_new.id}_2.png'})
                db.session.commit()
            if photo3:
                im = Image.open(BytesIO(base64.b64decode(photo3)))
                im.save(f"{getcwd()}/app/static/promotions/{new_new.id}_3.png")
                _ = Promotions.query.filter_by(id=new_new.id).update(
                    {'photo3': f'{new_new.id}_3.png'})
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
        return current_app.response_class(
            response=json.dumps(
                {'error': f'ERROR: {e}!'}
            ),
            status=400,
            mimetype='application/json'
        )


@promotions_api.route('/api/edit_new', methods=['POST'])
def edit_new():
    """
    ---
    post:
      summary: Редактировать новость
      parameters:
          - in: query
            name: token
            schema:
              type: string
              example: inHMylyABcnlhUR6$ecae409c0045c77e815d4399aeab0cc7f219225770145f0a6b64dc35c08627be
            description: Токен
          - in: query
            name: id
            schema:
              type: integer
              example: 1
            description: id новости
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
                    photo1:
                        type: string
                    photo2:
                        type: string
                    photo3:
                        type: string
                    name:
                        type: string
                    address:
                        type: string
                    phone:
                        type: string
                    description:
                        type: string
                example:   # Sample object
                    photo1:
                    photo2:
                    photo3:
                    name: Открылась кафешка
                    address: Россия, г Москва, ул Пушкина, д 5
                    phone: 79151290127
                    description: Классная кафешка
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
          description: Не передан обязательный параметр
          content:
            application/json:
              schema: ErrorSchema
        '400':
          description: Не передан обязательный параметр
          content:
            application/json:
              schema: ErrorSchema
      tags:
        - news
    """
    try:
        # TODO: добавит списание баллов и фотки
        photo1 = request.json.get('photo1')
        photo2 = request.json.get('photo2')
        photo3 = request.json.get('photo3')
        token = request.args.get('token')
        id = request.args.get('id')
        name = request.json.get('name')
        address = request.json.get('address')
        phone = request.json.get('phone')
        description = request.json.get('description')
        user = User.query.filter_by(token=token).first()
        deviceId = request.args.get('DeviceId')
        os = request.args.get('os')
        action(token, deviceId, os)
        if user and News.query.filter_by(id=id).first().author == user.id:
            _ = News.query.filter_by(id=id).update(
                {'name': name, 'address': address, 'phone': phone, 'description': description})
            db.session.commit()
            if photo1:
                im = Image.open(BytesIO(base64.b64decode(photo1)))
                im.save(f"{getcwd()}/app/static/news/{id}_1.png")
                _ = News.query.filter_by(id=id).update(
                    {'photo1': f'{id}_1.png'})
                db.session.commit()
            if photo2:
                im = Image.open(BytesIO(base64.b64decode(photo2)))
                im.save(f"{getcwd()}/app/static/news/{id}_2.png")
                _ = News.query.filter_by(id=id).update(
                    {'photo2': f'{id}_2.png'})
                db.session.commit()
            if photo3:
                im = Image.open(BytesIO(base64.b64decode(photo3)))
                im.save(f"{getcwd()}/app/static/news/{id}_3.png")
                _ = News.query.filter_by(id=id).update(
                    {'photo3': f'{id}_3.png'})
                db.session.commit()
            return current_app.response_class(
                response=json.dumps(
                    {'status': 'ok'}
                ),
                status=200,
                mimetype='application/json'
            )
        elif News.query.filter_by(id=id).first.author != user.id:
            return current_app.response_class(
                response=json.dumps(
                    {'error': 'You have no premission to edit this'}
                ),
                status=401,
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
        return current_app.response_class(
            response=json.dumps(
                {'error': f'ERROR: {e}!'}
            ),
            status=400,
            mimetype='application/json'
        )


@promotions_api.route('/api/edit_promotion', methods=['POST'])
def edit_promotion():
    """
    ---
    post:
      summary: Редактировать объявление
      parameters:
          - in: query
            name: token
            schema:
              type: string
              example: inHMylyABcnlhUR6$ecae409c0045c77e815d4399aeab0cc7f219225770145f0a6b64dc35c08627be
            description: Токен
          - in: query
            name: id
            schema:
              type: integer
              example: 1
            description: id новости
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
                    name:
                        type: string
                    address:
                        type: string
                    price:
                        type: number
                    phone:
                        type: string
                    description:
                        type: string
                example:   # Sample object
                    name: Открылась кафешка
                    address: Россия, г Москва, ул Пушкина, д 5
                    price: 1000
                    phone: 79151290127
                    description: Классная кафешка
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
          description: Не передан обязательный параметр
          content:
            application/json:
              schema: ErrorSchema
        '400':
          description: Не передан обязательный параметр
          content:
            application/json:
              schema: ErrorSchema
      tags:
        - promotions
    """
    try:
        # TODO: добавит списание баллов и фотки
        photo1 = request.json.get('photo1')
        photo2 = request.json.get('photo2')
        photo3 = request.json.get('photo3')
        token = request.args.get('token')
        id = request.args.get('id')
        name = request.json.get('name')
        price = request.json.get('price')
        address = request.json.get('address')
        phone = request.json.get('phone')
        description = request.json.get('description')
        user = User.query.filter_by(token=token).first()
        deviceId = request.args.get('DeviceId')
        os = request.args.get('os')
        action(token, deviceId, os)
        if user and Promotions.query.filter_by(id=id).first().author == user.id:
            _ = Promotions.query.filter_by(id=id).update(
                {'name': name, 'address': address, 'phone': phone, 'description': description, 'price': price})
            db.session.commit()
            if photo1:
                im = Image.open(BytesIO(base64.b64decode(photo1)))
                im.save(f"{getcwd()}/app/static/promotions/{id}_1.png")
                _ = Promotions.query.filter_by(id=id).update(
                    {'photo1': f'{id}_1.png'})
                db.session.commit()
            if photo2:
                im = Image.open(BytesIO(base64.b64decode(photo2)))
                im.save(f"{getcwd()}/app/static/promotions/{id}_2.png")
                _ = Promotions.query.filter_by(id=id).update(
                    {'photo2': f'{id}_2.png'})
                db.session.commit()
            if photo3:
                im = Image.open(BytesIO(base64.b64decode(photo3)))
                im.save(f"{getcwd()}/app/static/promotions/{id}_3.png")
                _ = Promotions.query.filter_by(id=id).update(
                    {'photo3': f'{id}_3.png'})
                db.session.commit()
            return current_app.response_class(
                response=json.dumps(
                    {'status': 'ok'}
                ),
                status=200,
                mimetype='application/json'
            )
        elif News.query.filter_by(id=id).first.author != user.id:
            return current_app.response_class(
                response=json.dumps(
                    {'error': 'You have no premission to edit this'}
                ),
                status=401,
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
        return current_app.response_class(
            response=json.dumps(
                {'error': f'ERROR: {e}!'}
            ),
            status=400,
            mimetype='application/json'
        )


@promotions_api.route('/api/update_new', methods=['POST'])
def update_new():
    """
    ---
    post:
      summary: Поднять новость
      parameters:
          - in: query
            name: token
            schema:
              type: string
              example: inHMylyABcnlhUR6$ecae409c0045c77e815d4399aeab0cc7f219225770145f0a6b64dc35c08627be
            description: Токен
          - in: query
            name: id
            schema:
              type: integer
              example: 1
            description: id новости
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
          description: Не передан обязательный параметр
          content:
            application/json:
              schema: ErrorSchema
        '400':
          description: Не передан обязательный параметр
          content:
            application/json:
              schema: ErrorSchema
      tags:
        - news
    """
    try:
        # TODO: добавит списание баллов
        token = request.args.get('token')
        id = request.args.get('id')
        user = User.query.filter_by(token=token).first()
        deviceId = request.args.get('DeviceId')
        os = request.args.get('os')
        action(token, deviceId, os)
        if user and News.query.filter_by(id=id).first().author == user.id:
            _ = News.query.filter_by(id=id).update(
                {'timestamp': time.time()})
            db.session.commit()
            return current_app.response_class(
                response=json.dumps(
                    {'status': 'ok'}
                ),
                status=200,
                mimetype='application/json'
            )
        elif News.query.filter_by(id=id).first.author != user.id:
            return current_app.response_class(
                response=json.dumps(
                    {'error': 'You have no premission to edit this'}
                ),
                status=401,
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
        return current_app.response_class(
            response=json.dumps(
                {'error': f'ERROR: {e}!'}
            ),
            status=400,
            mimetype='application/json'
        )


@promotions_api.route('/api/update_promotion', methods=['POST'])
def update_promotion():
    """
    ---
    post:
      summary: Поднять объявление
      parameters:
          - in: query
            name: token
            schema:
              type: string
              example: inHMylyABcnlhUR6$ecae409c0045c77e815d4399aeab0cc7f219225770145f0a6b64dc35c08627be
            description: Токен
          - in: query
            name: id
            schema:
              type: integer
              example: 1
            description: id новости
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
          description: Не передан обязательный параметр
          content:
            application/json:
              schema: ErrorSchema
        '400':
          description: Не передан обязательный параметр
          content:
            application/json:
              schema: ErrorSchema
      tags:
        - promotions
    """
    try:
        # TODO: добавит списание баллов
        token = request.args.get('token')
        id = request.args.get('id')
        user = User.query.filter_by(token=token).first()
        deviceId = request.args.get('DeviceId')
        os = request.args.get('os')
        action(token, deviceId, os)
        if user and Promotions.query.filter_by(id=id).first().author == user.id:
            _ = Promotions.query.filter_by(id=id).update(
                {'timestamp': time.time()})
            db.session.commit()
            return current_app.response_class(
                response=json.dumps(
                    {'status': 'ok'}
                ),
                status=200,
                mimetype='application/json'
            )
        elif News.query.filter_by(id=id).first.author != user.id:
            return current_app.response_class(
                response=json.dumps(
                    {'error': 'You have no premission to edit this'}
                ),
                status=401,
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
        return current_app.response_class(
            response=json.dumps(
                {'error': f'ERROR: {e}!'}
            ),
            status=400,
            mimetype='application/json'
        )

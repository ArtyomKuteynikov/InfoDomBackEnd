# api.py
import datetime
import json
from flask import Blueprint, request, current_app, url_for
from werkzeug.security import generate_password_hash
import base64
from PIL import Image
from io import BytesIO
from . import db
from .models import User, Codes, JK, Points, Promotions, PointsTypes, News, Addresses, Complaints, AdditionalUK
from iqsms_rest import Gate
import random
import time
from .config import *
from dadata import Dadata
from os import getcwd
from .api import action

api = Blueprint('main_api', __name__)


@api.route('/api/all_jk', methods=['GET'])
def all_jk():
    """
    ---
    get:
      summary: Все ЖК
      parameters:
          - in: query
            name: token
            schema:
              type: string
              example: 5zqxZa16b0vEE1sx$9a74b2452862f8b0061a5356079f69c3b83af9aec7430d070901f745b984a3f9
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
                            name:
                              type: string
                            users:
                              type: integer
                            photo:
                              type: string
                            addresses:
                              type: array
                              items:
                                type: object
                                properties:
                                  address:
                                    type: string
                                  lat:
                                    type: number
                                  lon:
                                    type: number

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
        - map
    """
    try:
        token = request.args.get('token')
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
            jks = JK.query.filter_by(moderated=1).all()
            output = []
            for i in jks:
                count = len(User.query.filter_by(org=0, jk=i.id).all())
                output.append(
                    {
                        'id': i.id,
                        'name': i.name,
                        'users': count,
                        'photo': url_for('static', filename=f"jk/{i.photo}") if i.photo else 'jk/default_org.png',
                        'addresses': [
                            {
                                'address': j.name,
                                'lat': j.lat,
                                'lon': j.lon
                            } for j in Addresses.query.filter_by(jk_id=i.id)
                        ]
                    }
                )
            return current_app.response_class(
                response=json.dumps(
                    {'list': output}
                ),
                status=200,
                mimetype='application/json'
            )
        return current_app.response_class(
            response=json.dumps(
                {'error': f'USER NOT EXIST'}
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


@api.route('/api/all_orgs', methods=['GET'])
def all_orgs():
    """
    ---
    get:
      summary: Все организации
      parameters:
          - in: query
            name: token
            schema:
              type: string
              example: 5zqxZa16b0vEE1sx$9a74b2452862f8b0061a5356079f69c3b83af9aec7430d070901f745b984a3f9
            description: Токен
          - in: query
            name: jk
            schema:
              type: integer
              example: 0
            description: ЖК(0 - если все)
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
                            is_uk:
                              type: integer
                            jk:
                              type: integer
                            jk_name:
                              type: string
                            org_name:
                              type: string
                            phone:
                              type: string
                            photo:
                              type: string
                            address:
                              type: string
                            lat:
                              type: number
                            lon:
                              type: number
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
        - map
    """
    try:
        jk = request.args.get('jk')
        token = request.args.get('token')
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
            if int(jk) == 0:
                orgs = User.query.filter_by(org=1).all()
            else:
                orgs = User.query.filter_by(org=1, jk=jk).all()
            output = []
            for i in orgs:
                jk_name = JK.query.filter_by(id=i.jk).first().name
                output.append(
                    {
                        'id': i.id,
                        'jk': i.jk,
                        'is_uk': 1 if i.is_uk else 0,
                        'jk_name': jk_name,
                        'org_name': i.org_name,
                        'phone': i.phone,
                        'photo': url_for('static', filename=f"profile_photos/{i.photo}") if i.photo else 'profile_photos/default_uk.png' if i.is_uk else 'profile_photos/default_org.png',
                        'address': i.address,
                        'lon': i.lon,
                        'lat': i.lat
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


@api.route('/api/search_jk', methods=['GET'])
def search_jk():
    """
    ---
    get:
      summary: Поиск по ЖК
      parameters:
          - in: query
            name: q
            schema:
              type: string
              example: Вялые паруса
            description: Поиск
          - in: query
            name: token
            schema:
              type: string
              example: 5zqxZa16b0vEE1sx$9a74b2452862f8b0061a5356079f69c3b83af9aec7430d070901f745b984a3f9
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
                            name:
                              type: string
                            users:
                              type: integer
                            photo:
                              type: string
                            addresses:
                              type: array
                              items:
                                type: object
                                properties:
                                  address:
                                    type: string
                                  lat:
                                    type: number
                                  lon:
                                    type: number

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
        - map
    """
    try:
        token = request.args.get('token')
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
            jks = JK.query.filter_by(moderated=1).all()
            output = []
            for i in jks:
                if request.args.get('q').lower() in i.name.lower():
                    count = len(User.query.filter_by(org=0, jk=i.id).all())
                    output.append(
                        {
                            'id': i.id,
                            'name': i.name,
                            'users': count,
                            'photo': url_for('static', filename=f"jk/{i.photo}") if i.photo else 'jk/default_org.png',
                            'addresses': [
                                {
                                    'address': j.name,
                                    'lat': j.lat,
                                    'lon': j.lon
                                } for j in Addresses.query.filter_by(jk_id=i.id)
                            ]
                        }
                    )
            return current_app.response_class(
                response=json.dumps(
                    {'list': output}
                ),
                status=200,
                mimetype='application/json'
            )
        return current_app.response_class(
            response=json.dumps(
                {'error': f'USER NOT EXIST'}
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


@api.route('/api/search_orgs', methods=['GET'])
def search_orgs():
    """
    ---
    get:
      summary: Поиск по организациям
      parameters:
          - in: query
            name: q
            schema:
              type: string
              example: Ромашка 1
            description: Поиск
          - in: query
            name: token
            schema:
              type: string
              example: 5zqxZa16b0vEE1sx$9a74b2452862f8b0061a5356079f69c3b83af9aec7430d070901f745b984a3f9
            description: Токен
          - in: query
            name: jk
            schema:
              type: integer
              example: 0
            description: ЖК(0 - если все)
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
                            is_uk:
                              type: integer
                            jk:
                              type: integer
                            jk_name:
                              type: string
                            org_name:
                              type: string
                            phone:
                              type: string
                            photo:
                              type: string
                            address:
                              type: string
                            lat:
                              type: number
                            lon:
                              type: number
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
        - map
    """
    try:
        jk = request.args.get('jk')
        token = request.args.get('token')
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
            if int(jk) == 0:
                orgs = User.query.filter_by(org=1).all()
            else:
                orgs = User.query.filter_by(org=1, jk=jk).all()
            output = []
            for i in orgs:
                if request.args.get('q').lower() in i.org_name.lower():
                    jk_name = JK.query.filter_by(id=i.jk).first().name
                    output.append(
                        {
                            'id': i.id,
                            'jk': i.jk,
                            'is_uk': 1 if i.is_uk else 0,
                            'jk_name': jk_name,
                            'org_name': i.org_name,
                            'phone': i.phone,
                            'photo': url_for('static', filename=f"profile_photos/{i.photo}") if i.photo else 'profile_photos/default_uk.png' if i.is_uk else 'profile_photos/default_org.png',
                            'address': i.address,
                            'lon': i.lon,
                            'lat': i.lat
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


@api.route('/api/get_org', methods=['POST', 'GET'])
def get_org():
    """
    ---
    get:
      summary: Данные организации
      parameters:
          - in: query
            name: token
            schema:
              type: string
              example: 5zqxZa16b0vEE1sx$9a74b2452862f8b0061a5356079f69c3b83af9aec7430d070901f745b984a3f9
            description: Токен
          - in: query
            name: org
            schema:
              type: integer
              example: 1
            description: id организации
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
                    photo:
                      type: string
                    jk:
                      type: integer
                    jk_name:
                      type: string
                    org_name:
                      type: string
                    phone:
                      type: string
                    address:
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
        - map
    """
    try:
        org = request.args.get('org')
        token = request.args.get('token')
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
            org = User.query.filter_by(id=org).first()
            jk_name = JK.query.filter_by(id=org.jk).first().name
            output = {
                    'id': org.id,
                    'photo': url_for('static', filename=f"profile_photos/{org.photo}") if org.photo else 'profile_photos/default_org.png',
                    'jk': org.jk,
                    'jk_name': jk_name,
                    'org_name': org.org_name,
                    'phone': org.phone,
                    'address': org.address
                }
            print(output)
            return current_app.response_class(
                response=json.dumps({
                    output
                }),
                status=200,
                mimetype='application/json'
            )
        return current_app.response_class(
            response=json.dumps(
                {'error': f'USER DOES NOT EXIST'}
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


@api.route('/api/get_jk', methods=['GET'])
def get_jk():
    """
   ---
   get:
     summary: Данные об УК
     parameters:
         - in: query
           name: token
           schema:
             type: string
             example: 5zqxZa16b0vEE1sx$9a74b2452862f8b0061a5356079f69c3b83af9aec7430d070901f745b984a3f9
           description: token
         - in: query
           name: jk
           schema:
             type: integer
             example: 1
           description: jk
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
                   id:
                     type: integer
                   jk_name:
                     type: string
                   neighbours:
                     type: integer
                   photo:
                     type: string
                   uk:
                     type: array
                     items:
                       type: object
                       properties:
                         id:
                           type: integer
                         name:
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
       - map
   """
    try:
        jk_id = request.args.get('jk')
        token = request.args.get('token')
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
            jk = JK.query.filter_by(id=jk_id).first()
            output = {
                'id': jk.id,
                'jk_name': jk.name,
                'neighbours': len(User.query.filter_by(org=0, jk=jk.id).all()),
                'photo': url_for('static', filename=f"jk/{jk.photo}") if jk.photo else 'jk/default_org.png',
                'uk':[
                    {
                        'id': j,
                        'name': User.query.filter_by(id=j).first().org_name,
                    } for j in set([i.uk_id for i in Addresses.query.filter_by(jk_id=jk.id).all()])
                ]
            }
            return current_app.response_class(
                response=json.dumps(
                    output
                ),
                status=200,
                mimetype='application/json'
            )
        return current_app.response_class(
            response=json.dumps(
                {'error': f'USER DOES NOT EXIST'}
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


@api.route('/api/get_uk', methods=['POST', 'GET'])
def get_uk():
    """
      ---
   get:
     summary: Данные об УК
     parameters:
         - in: query
           name: uk
           schema:
             type: integer
             example: 3
           description: uk
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
                   id:
                     type: integer
                   jk_name:
                     type: string
                   address:
                     type: string
                   photo:
                     type: string
                   work_days:
                     type: array
                     items:
                       type: object
                       properties:
                           time:
                             type: string
                           days:
                             type: string
                   day_off:
                     type: string
                   pause:
                     type: string
                   contact_phones:
                     type: array
                     items:
                       type: object
                       properties:
                           name:
                             type: string
                           phone:
                             type: string
                   useful_phones:
                     type: array
                     items:
                       type: object
                       properties:
                           name:
                             type: string
                           phone:
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
       - map
   """
    try:
        uk_id = request.args.get('uk')
        token = request.args.get('token')
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
            uk = User.query.filter_by(id=uk_id).first()
            uk_data = AdditionalUK.query.filter_by(uk_id=uk_id).first()
            if not uk_data:
                if user.status == "blocked":
                    return current_app.response_class(
                        response=json.dumps(
                            {'error': "UK NOT FOUND"}
                        ),
                        status=404,
                        mimetype='application/json'
                    )
            work_days = dict()
            days_off = []
            if uk_data.mon:
                if uk_data.mon in work_days:
                    work_days[uk_data.mon].append('ПН')
                else:
                    work_days.update({uk_data.mon: ['ПН']})
            else:
                days_off.append('ВТ')
            if uk_data.tue:
                if uk_data.tue in work_days:
                    work_days[uk_data.tue].append('ВТ')
                else:
                    work_days.update({uk_data.tue: ['ВТ']})
            else:
                days_off.append('ВТ')
            if uk_data.wed:
                if uk_data.wed in work_days:
                    work_days[uk_data.wed].append('СР')
                else:
                    work_days.update({uk_data.wed: ['СР']})
            else:
                days_off.append('СР')
            if uk_data.thu:
                if uk_data.thu in work_days:
                    work_days[uk_data.thu].append('ЧТ')
                else:
                    work_days.update({uk_data.thu: ['ЧТ']})
            else:
                days_off.append('ЧТ')
            if uk_data.fri:
                if uk_data.fri in work_days:
                    work_days[uk_data.fri].append('ПТ')
                else:
                    work_days.update({uk_data.fri: ['ПТ']})
            else:
                days_off.append('ПТ')
            if uk_data.sat:
                if uk_data.sat in work_days:
                    work_days[uk_data.sat].append('СБ')
                else:
                    work_days.update({uk_data.sat: ['СБ']})
            else:
                days_off.append('СБ')
            if uk_data.san:
                if uk_data.san in work_days:
                    work_days[uk_data.san].append('ВС')
                else:
                    work_days.update({uk_data.san: ['ВС']})
            else:
                days_off.append('ВС')
            output = {
                'id': uk.id,
                'jk_name': uk.org_name,
                'address': uk.address,
                'photo': url_for('static', filename=f"profile_photos/{uk.photo}") if uk.photo else 'profile_photos/default_uk.png',
                'work_days': [
                    {
                        'time': i,
                        'days': '/'.join(work_days[i]),
                    } for i in work_days
                ],
                'day_off': '/'.join(days_off),
                'pause': uk_data.delay if uk_data.delay else 'Без перерывов',
                'contact_phones':[
                    {
                        'name': i,
                        'phone': json.loads(uk_data.contact_phones)[i],
                    } for i in json.loads(uk_data.contact_phones)
                ],
                'useful_phones':[
                    {
                        'name': i,
                        'phone': json.loads(uk_data.useful_phones)[i],
                    } for i in json.loads(uk_data.useful_phones)
                ]
            }
            return current_app.response_class(
                response=json.dumps(
                    output
                ),
                status=200,
                mimetype='application/json'
            )
        return current_app.response_class(
            response=json.dumps(
                {'error': f'USER DOES NOT EXIST'}
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

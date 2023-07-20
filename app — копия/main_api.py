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

api = Blueprint('main_api', __name__)


@api.route('/api/all_addresses', methods=['GET'])
def all_addresses():
    """
        ---
        get:
          summary: Все адреса ЖК
          parameters:
              - in: query
                name: token
                schema:
                  type: string
                  example: inHMylyABcnlhUR6$ecae409c0045c77e815d4399aeab0cc7f219225770145f0a6b64dc35c08627be
                description: Токен
              - in: query
                name: city
                schema:
                  type: string
                  example: Москва
                description: Город
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
                                city:
                                  type: string
                                jk_id:
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
        city = request.args.get('city')
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
            if city:
                addrs = Addresses.query.filter_by(city=city).all()
            else:
                addrs = Addresses.query.filter_by().all()
            output = []
            for i in addrs:
                output.append(
                    {
                        'id': i.id,
                        'name': i.name,
                        'city': i.city,
                        'jk_id': i.jk_id
                    }
                )
            return current_app.response_class(
                response=json.dumps(
                    {'list': output}
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
                            uk:
                              type: integer
                            uk_name:
                              type: string
                            name:
                              type: string
                            users:
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
            orgs = JK.query.filter_by(moderated=1).all()
            output = []
            for i in orgs:
                uk_name = User.query.filter_by(id=i.uk).first()
                if uk_name:
                    uk_name = uk_name.org_name
                else:
                    uk_name = ''
                count = len(User.query.filter_by(org=0, jk=i.id).all())
                output.append(
                    {
                        'id': i.id,
                        'uk': i.uk,
                        'uk_name': uk_name,
                        'name': i.name,
                        'users': count
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


@api.route('/api/all_orgs', methods=['GET'])
def all_orgs():
    """
    ---
    get:
      summary: Все ЖК
      parameters:
          - in: query
            name: token
            schema:
              type: string
              example: inHMylyABcnlhUR6$ecae409c0045c77e815d4399aeab0cc7f219225770145f0a6b64dc35c08627be
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
        - chats
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
                orgs = User.query.filter_by(org=1, is_uk=0).all()
                print(orgs)
            else:
                orgs = User.query.filter_by(org=1, is_uk=0, jk=jk).all()
            output = []
            for i in orgs:
                jk_name = JK.query.filter_by(id=i.jk).first().name
                output.append(
                    {
                        'id': i.id,
                        'jk': i.jk,
                        'jk_name': jk_name,
                        'org_name': i.org_name,
                        'phone': i.phone,
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


@api.route('/api/get_org', methods=['POST'])
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
              example: inHMylyABcnlhUR6$ecae409c0045c77e815d4399aeab0cc7f219225770145f0a6b64dc35c08627be
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
        - chats
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
            output =  {
                    'id': org.id,
                    'jk': org.jk,
                    'jk_name': jk_name,
                    'org_name': org.org_name,
                    'phone': org.phone,
                    'address': org.address
                }
            return current_app.response_class(
                response=json.dumps(
                    output
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


@api.route('/api/get_jk', methods=['POST'])
def get_jk():
    pass


@api.route('/api/get_uk', methods=['POST'])
def get_uk():
    pass

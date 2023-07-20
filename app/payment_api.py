import json
import requests
from flask import Blueprint, request, current_app
import time
from . import db
from .models import User
from yookassa import Payment
import uuid
from yookassa import Configuration

Configuration.configure('313873', 'test_5I0c--TCS4yO6FhMuNCqp9Bhh4gl9EEshttAQNOIqlY')
idempotence_key = str(uuid.uuid4())

payment_api = Blueprint('payment_api', __name__)


def action(token, deviceId, os):
    if User.query.filter_by(token=token).first():
        print(2)
        if User.query.filter_by(token=token).first().status in ['inactive', 'active']:
            _ = User.query.filter_by(token=token).update(
                {'deviceId': deviceId, 'os': os, 'last_updated': int(time.time()), 'status': 'active'})
            db.session.commit()


@payment_api.route('/api/payment', methods=['GET'])
def create_payment():
    """
    ---
   get:
     summary: Ссылк на оплату
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
         - in: query
           name: amount
           schema:
             type: integer
             example: 1
           description: amount
     responses:
       '200':
         description: Результат
         content:
           application/json:
             schema:      # Request body contents
               type: object
               properties:
                   confirmation_url:
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
       - payment
    """
    try:
        # Получаем параметры из запроса
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
        amount = request.args.get('amount')

        # Формируем параметры для запроса к API Юкассы
        payment = Payment.create({
            "amount": {
                "value": str(amount),
                "currency": "RUB"
            },
            "payment_method_data": {
                "type": "bank_card"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": "http://127.0.0.1:5000/payment_success"
            },
            "description": "Заказ №72"
        }, idempotence_key)

        # get confirmation url
        confirmation_url = payment.confirmation.confirmation_url

        # Возвращаем ссылку в формате JSON
        return current_app.response_class(
            response=json.dumps({
                'confirmation_url': confirmation_url
            }),
            status=200,
            mimetype='application/json'
        )

    except Exception as e:
        # В случае ошибки возвращаем сообщение об ошибке в формате JSON
        return current_app.response_class(
            response=json.dumps({
                'error': f'Error: {e}'
            }),
            status=400,
            mimetype='application/json'
        )


@payment_api.route('/payment_success', methods=['get'])
def payment_success():
    payment_id = request.args
    print(payment_id)
    payment = Payment.find_one(payment_id)

    if payment.status == 'succeeded':
        print('Платеж прошел успешно')

    return '', 200

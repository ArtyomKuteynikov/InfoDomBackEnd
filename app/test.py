from yookassa import Payment
import uuid
from yookassa import Configuration

Configuration.configure('313873', 'test_5I0c--TCS4yO6FhMuNCqp9Bhh4gl9EEshttAQNOIqlY')
idempotence_key = str(uuid.uuid4())
payment = Payment.create({
    "amount": {
        "value": "2.00",
        "currency": "RUB"
    },
    "payment_method_data": {
        "type": "bank_card"
    },
    "confirmation": {
        "type": "redirect",
        "return_url": "https://www.example.com/return_url"
    },
    "description": "Заказ №72"
}, idempotence_key)

# get confirmation url
confirmation_url = payment.confirmation.confirmation_url
print(dir(payment), payment.id)

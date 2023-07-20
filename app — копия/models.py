# models.py

from flask_login import UserMixin
from . import db
from sqlalchemy.sql import func


class ChatRooms(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(10))
    jk = db.Column(db.Integer)
    user1 = db.Column(db.Integer)
    user2 = db.Column(db.Integer)


class Messages(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer)
    author = db.Column(db.Integer)
    attachment = db.Column(db.Integer, default=0)
    text = db.Column(db.String(10000))
    image = db.Column(db.String(100))
    timestamp = db.Column(db.DateTime(timezone=True), server_default=func.now())
    read = db.Column(db.Integer, default=0)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)  # primary keys are required by SQLAlchemy
    photo = db.Column(db.String(1000))
    phone = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100))
    surname = db.Column(db.String(100))
    second_name = db.Column(db.String(100))
    status = db.Column(db.String(100), default="inactive")
    org = db.Column(db.Integer, default=0)
    inn = db.Column(db.String(100))
    org_name = db.Column(db.String(100))
    address = db.Column(db.String(100))
    jk = db.Column(db.Integer)
    points = db.Column(db.Integer)
    is_uk = db.Column(db.Integer)
    token = db.Column(db.String(256))
    registered = db.Column(db.Integer)
    last_updated = db.Column(db.Integer)
    os = db.Column(db.String(10))
    deviceId = db.Column(db.String(100))
    referer = db.Column(db.Integer)


class Codes(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)  # primary keys are required by SQLAlchemy
    phone = db.Column(db.String(100))
    code = db.Column(db.String(10))


class JK(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)  # primary keys are required by SQLAlchemy
    name = db.Column(db.String(100))
    city = db.Column(db.String(100))
    moderated = db.Column(db.Integer)
    uk = db.Column(db.Integer)


class Points(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)  # primary keys are required by SQLAlchemy
    user_id = db.Column(db.Integer)
    quantity = db.Column(db.Integer)
    side = db.Column(db.Integer)
    type = db.Column(db.Integer)
    timestamp = db.Column(db.REAL)


class PointsTypes(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)  # primary keys are required by SQLAlchemy
    name = db.Column(db.String(1000))
    description = db.Column(db.String(1000))


class Promotions(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)  # primary keys are required by SQLAlchemy
    author = db.Column(db.Integer)
    jk = db.Column(db.Integer)
    photo1 = db.Column(db.String(100))
    photo2 = db.Column(db.String(100))
    photo3 = db.Column(db.String(100))
    name = db.Column(db.String(100))
    price = db.Column(db.REAL)
    address = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    description = db.Column(db.String(10000))
    timestamp = db.Column(db.REAL)
    blocked = db.Column(db.Integer, default=0)


class News(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)  # primary keys are required by SQLAlchemy
    author = db.Column(db.Integer)
    jk = db.Column(db.Integer)
    photo1 = db.Column(db.String(100))
    photo2 = db.Column(db.String(100))
    photo3 = db.Column(db.String(100))
    name = db.Column(db.String(100))
    address = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    description = db.Column(db.String(10000))
    timestamp = db.Column(db.REAL)
    blocked = db.Column(db.Integer, default=0)


class Addresses(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)  # primary keys are required by SQLAlchemy
    name = db.Column(db.String(100), unique=True)
    jk_id = db.Column(db.Integer)
    city = db.Column(db.String(100), unique=True)
    street = db.Column(db.String(100), unique=True)
    # lat = db.Column(db.REAL)
    # lon = db.Column(db.REAL)


class Notifications(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)  # primary keys are required by SQLAlchemy
    type = db.Column(db.Integer)
    text = db.Column(db.String(1000))
    read = db.Column(db.Integer)


class Complaints(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)  # primary keys are required by SQLAlchemy
    timestamp = db.Column(db.DateTime(timezone=True), server_default=func.now())
    from_user = db.Column(db.Integer)
    type = db.Column(db.String(10))
    text = db.Column(db.String(1000))
    message_id = db.Column(db.Integer)
    promotion_id = db.Column(db.Integer)
    new_id = db.Column(db.Integer)
    profile_id = db.Column(db.Integer)
    status = db.Column(db.Integer, default=0)


class Transactions(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    userId = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime(timezone=True), server_default=func.now())
    transactId = db.Column(db.String(1000))
    amount = db.Column(db.REAL, default=0)

from chat_app import db
from flask_login import UserMixin
from sqlalchemy.sql import func


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

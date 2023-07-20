# chats.py
from datetime import datetime

from flask import Blueprint, render_template, request, send_from_directory, make_response, session
from flask_login import login_required, current_user
import os
from . import db
from dadata import Dadata
from .config import *
from app.models import JK, Addresses, User, News, Promotions, Transactions, Complaints
from app.models import Messages, ChatRooms
from flask_socketio import emit, join_room, leave_room

main = Blueprint('main', __name__)


@main.route('/', methods=['POST', 'GET'])
@main.route('/stats', methods=['POST', 'GET'])
@login_required
def stats():
    user = request.args.get('user')
    user_data = dict()
    user_transactions = []
    if user:
        user_data = User.query.filter_by(id=user).first()
        user_transactions = Transactions.query.filter_by(userId=user).all()
    caption = "Все пользователи"
    active = request.args.get('active')
    print()
    org = request.args.get('org')
    uk = request.args.get('uk')
    if org and org != "None":
        org = int(request.args.get('org')) if request.args.get('org') else None
    if str(uk) == "1":
        print(uk)
        data = User.query.filter_by(is_uk=1).all()
    elif not active and (org not in [0, 1]):
        data = User.query.filter_by().all()
    elif active and org == 1:
        caption = "Все организации"
        data = User.query.filter_by(status="active", org=1).all() + User.query.filter_by(status="admin", org=1).all()
    elif active and org == 0:
        caption = "Все жильцы"
        data = User.query.filter_by(status="active", org=0).all() + User.query.filter_by(status="admin", org=0).all()
    elif active:
        data = User.query.filter_by(status="active").all() + User.query.filter_by(status="admin").all()
    elif org == 1:
        caption = "Все организации"
        data = User.query.filter_by(org=1).all()
    else:
        caption = "Все жильцы"
        data = User.query.filter_by(org=0).all()
    couters = {
        'all_users': User.query.filter_by().count(),
        'active_users': User.query.filter_by(status='active').count() + User.query.filter_by(status='admin').count(),
        'all_people': User.query.filter_by(org=0).count(),
        'active_people': User.query.filter_by(org=0, status='active').count() + User.query.filter_by(org=0,
                                                                                                     status='admin').count(),
        'all_orgs': User.query.filter_by(org=1).count(),
        'active_orgs': User.query.filter_by(org=1, status='active').count() + User.query.filter_by(org=1,
                                                                                                   status='admin').count(),
        'all_uk': User.query.filter_by(is_uk=1).count()
    }
    if request.method == 'POST':
        start_raw = request.form['start']
        finish_raw = request.form['finish']
        if start_raw:
            start = int(datetime.strptime(start_raw, '%Y-%m-%d').timestamp())
        else:
            start = datetime.strptime('2020-01-01', '%Y-%m-%d').timestamp()
        if finish_raw:
            finish = int(datetime.strptime(finish_raw, '%Y-%m-%d').timestamp())
        else:
            finish = datetime.strptime('2030-01-01', '%Y-%m-%d').timestamp()
        if not start:
            start = datetime.strptime('2020-01-01', '%Y-%m-%d').timestamp()
        if not finish:
            finish = datetime.strptime('2030-01-01', '%Y-%m-%d').timestamp()
        data = list(filter(lambda x: start < x.registered < finish, data))
        return render_template('stats/stats.html', start=datetime.fromtimestamp(start).strftime('%Y-%m-%d'),
                               finish=datetime.fromtimestamp(finish).strftime('%Y-%m-%d'),
                               data=data, datetime=datetime, active=active, org=org, JK=JK, user=user,
                               user_data=user_data, uk=uk)
    else:
        start = datetime.strptime('2020-01-01', '%Y-%m-%d').timestamp()
        finish = datetime.strptime('2030-01-01', '%Y-%m-%d').timestamp()
    data = list(filter(lambda x: start < x.registered < finish, data))
    data = sorted(data, key=lambda x: x.id)
    return render_template('stats/stats.html', data=data, datetime=datetime, counters=couters, JK=JK, str=str,
                           caption=caption, user=user, user_data=user_data, active=active, org=org,
                           user_transactions=user_transactions, uk=uk)


@main.route('/sales/org', methods=['POST', 'GET'])
def sales_org():
    data = Transactions.query.filter_by().all()
    summary = sum([i.amount for i in data])
    if request.method == 'POST':
        start_raw = request.form['start']
        finish_raw = request.form['finish']
        print(start_raw)
        if start_raw:
            start = int(datetime.strptime(start_raw, '%Y-%m-%d').timestamp())
        else:
            start = datetime.strptime('2020-01-01', '%Y-%m-%d').timestamp()
        if finish_raw:
            finish = int(datetime.strptime(finish_raw, '%Y-%m-%d').timestamp())
        else:
            finish = datetime.strptime('2030-01-01', '%Y-%m-%d').timestamp()
        if not start:
            start = datetime.strptime('2020-01-01', '%Y-%m-%d').timestamp()
        if not finish:
            finish = datetime.strptime('2030-01-01', '%Y-%m-%d').timestamp()
        data = list(
            filter(lambda x: datetime.fromtimestamp(start) < x.timestamp < datetime.fromtimestamp(finish), data))
        amount = sum([i.amount for i in data])
        return render_template('sales/sales.html', start=datetime.fromtimestamp(start).strftime('%Y-%m-%d'),
                               finish=datetime.fromtimestamp(finish).strftime('%Y-%m-%d'),
                               data=data, datetime=datetime, summary=summary, amount=amount, User=User, JK=JK, org=1)
    else:
        start = datetime.strptime('2020-01-01', '%Y-%m-%d').timestamp()
        finish = datetime.strptime('2030-01-01', '%Y-%m-%d').timestamp()
    amount = sum([i.amount for i in data])
    return render_template('sales/sales.html', data=data, datetime=datetime, summary=summary, amount=amount, User=User,
                           org=1, JK=JK)


@main.route('/sales/users', methods=['POST', 'GET'])
def sales_users():
    users = User.query.filter_by(org=1).all()
    if request.method == 'POST':
        start_raw = request.form['start']
        finish_raw = request.form['finish']
        print(start_raw)
        if start_raw:
            start = int(datetime.strptime(start_raw, '%Y-%m-%d').timestamp())
        else:
            start = datetime.strptime('2020-01-01', '%Y-%m-%d').timestamp()
        if finish_raw:
            finish = int(datetime.strptime(finish_raw, '%Y-%m-%d').timestamp())
        else:
            finish = datetime.strptime('2030-01-01', '%Y-%m-%d').timestamp()
        if not start:
            start = datetime.strptime('2020-01-01', '%Y-%m-%d').timestamp()
        if not finish:
            finish = datetime.strptime('2030-01-01', '%Y-%m-%d').timestamp()
        users = list(filter(lambda x: start < x.registered < finish, users))
        return render_template('sales/sales.html', data=users, JK=JK, org=0, datetime=datetime)
    else:
        start = datetime.strptime('2020-01-01', '%Y-%m-%d').timestamp()
        finish = datetime.strptime('2030-01-01', '%Y-%m-%d').timestamp()
    return render_template('sales/sales.html', data=users, JK=JK, org=0, datetime=datetime)


@main.route('/jk/all', methods=['POST', 'GET'])
def jk_all():
    jks = JK.query.filter_by().all()
    cities = db.session.query(JK.city).distinct().all()
    if request.method == 'POST':
        city = request.form['city']
        if city != 'ВСЕ':
            jks = JK.query.filter_by(city=city).all()
    jk = request.args.get('jk')
    if jk:
        jk_info = JK.query.filter_by(id=jk).first()
        addresses = Addresses.query.filter_by(jk_id=jk).all()
        num_people = len(User.query.filter_by(jk=jk, org=0).all())
        num_orgs = len(User.query.filter_by(jk=jk, org=1).all())
        num_news = len(News.query.filter_by(jk=jk).all())
        num_proms = len(Promotions.query.filter_by(jk=jk).all())
        return render_template('jk/jk_all.html', jks=jks, cities=cities, jk=jk_info, addresses=addresses,
                               num_people=num_people, num_orgs=num_orgs,
                               num_news=num_news, num_proms=num_proms)
    return render_template('jk/jk_all.html', jks=jks, cities=cities)


@main.route('/jk/<id>', methods=['GET'])
def jk(id):
    jk = JK.query.filter_by(id=id).first()
    addresses = Addresses.query.filter_by(jk_id=id).all()
    num_people = len(User.query.filter_by(jk=id, org=0).all())
    num_orgs = len(User.query.filter_by(jk=id, org=1).all())
    num_news = len(News.query.filter_by(jk=id).all())
    num_proms = len(Promotions.query.filter_by(jk=id).all())
    return render_template('jk/jk.html', jk=jk, addresses=addresses, num_people=num_people, num_orgs=num_orgs,
                           num_news=num_news, num_proms=num_proms)


@main.route('/jk/add', methods=['GET'])
def jk_add():
    jks = JK.query.filter_by().all()
    cities = db.session.query(JK.city).distinct().all()
    if request.method == 'POST':
        city = request.form['city']
        if city != 'ВСЕ':
            jks = JK.query.filter_by(city=city).all()
    return render_template('jk/add_jk.html', jks=jks, cities=cities)


@main.route('/jk/moderate', methods=['GET'])
def jk_moderate():
    jks = JK.query.filter_by(moderated=0).all()
    addrs = dict()
    streets = dict()
    for i in jks:
        addrs.update({i.id: []})
        streets.update({i.id: []})
    for i in jks:
        addresses = Addresses.query.filter_by(jk_id=i.id).all()
        for j in addresses:
            addrs[i.id].append(j.name)
        address = j.name
        dadata = Dadata(DADATA)
        street = dadata.suggest("address", address, 10)[0]['data']['street']
        if street:
            for k in Addresses.query.filter_by(street=street).all():
                if k.jk_id != i.id and JK.query.filter_by(id=k.jk_id).first() not in streets[i.id]:
                    streets[i.id].append(JK.query.filter_by(id=k.jk_id).first())
    return render_template('jk/moderate_jk.html', jks=jks, addrs=addrs, streets=streets)


@main.route('/orgs', methods=['POST', 'GET'])
@login_required
def orgs():
    data = [
        {
            'id': 1,
            'date': 1677940112,
            'DeviceID': 'Gnx786nzdg758',
            'OS': 'Android',
            'org': 0,
            'status': 'active'
        },
        {
            'id': 2,
            'date': 1677767312,
            'DeviceID': 'Gnx786nzdg758',
            'OS': 'Android',
            'org': 1,
            'status': 'inactive'
        },
        {
            'id': 3,
            'date': 1677680912,
            'DeviceID': 'Gnx786nzdg758',
            'OS': 'iOS',
            'org': 1,
            'status': 'blocked'
        },
        {
            'id': 4,
            'date': 1675261712,
            'DeviceID': 'Gnx786nzdg758',
            'OS': 'Android',
            'org': 1,
            'status': 'admin'
        }
    ]
    cities = db.session.query(JK.city).distinct().all()
    jks = db.session.query(JK.name).distinct().all()
    addresses = db.session.query(Addresses.name).distinct().all()
    return render_template('orgs/orgs.html', data=data, datetime=datetime, cities=cities, jks=jks, addresses=addresses)


@main.route('/people', methods=['POST', 'GET'])
@login_required
def people():
    data = []
    cities = db.session.query(JK.city).distinct().all()
    jks = db.session.query(JK.name).distinct().all()
    addresses = db.session.query(Addresses.name).distinct().all()
    return render_template('people/people.html', data=data, datetime=datetime, cities=cities, jks=jks,
                           addresses=addresses)


@main.route('/org/<id>')
@main.route('/user/<id>')
@login_required
def user(id):
    user = User.query.filter_by(id=id).first()
    jk = JK.query.filter_by(id=user.jk).first()
    if user.org:
        news = News.query.filter_by().all()
    else:
        news = Promotions.query.filter_by().all()
    return render_template('people/user.html', user=user, jk=jk, news=news)


@main.route('/news')
@login_required
def news():
    news = News.query.filter_by().all()
    news = sorted(news, key=lambda x: x.timestamp)[::-1]
    cities = db.session.query(JK.city).distinct().all()
    jks = db.session.query(JK.name).distinct().all()
    addresses = db.session.query(News.address).distinct().all()
    return render_template('news/news.html', news=news, User=User, cities=cities, jks=jks, addresses=addresses, str=str,
                           datetime=datetime, JK=JK)


@main.route('/promotions')
@login_required
def promotions():
    news = Promotions.query.filter_by().all()
    news = sorted(news, key=lambda x: x.timestamp)[::-1]
    cities = db.session.query(JK.city).distinct().all()
    jks = db.session.query(JK.name).distinct().all()
    addresses = db.session.query(News.address).distinct().all()
    return render_template('news/news.html', news=news, User=User, cities=cities, jks=jks, addresses=addresses, str=str,
                           datetime=datetime, JK=JK)


@main.route('/new/<id>')
@login_required
def new(id):
    new = News.query.filter_by(id=id).first()
    return render_template('news/new.html', jk=new, User=User, JK=JK)


@main.route('/promotion/<id>')
@login_required
def promotion(id):
    new = Promotions.query.filter_by(id=id).first()
    return render_template('news/promotion.html', jk=new, User=User, JK=JK)


@main.route("/privacy")
def privacy():
    workingdir = os.path.abspath(os.getcwd())
    filepath = workingdir + '/app/static/files/'
    return send_from_directory(filepath, 'privacy.pdf')


@main.route("/terms")
def terms():
    workingdir = os.path.abspath(os.getcwd())
    filepath = workingdir + '/app/static/files/'
    return send_from_directory(filepath, 'terms.pdf')


@main.route('/profile')
@login_required
def profile():
    return render_template('auth/profile.html', name=current_user.name)


@main.route('/test')
@login_required
def test():
    return render_template('test.html')


@main.route('/chats/personal')
@login_required
def personal_chats():
    chat_rooms = []
    chats = ChatRooms.query.filter_by(type="personal", user1=current_user.id).all() + ChatRooms.query.filter_by(
        type="personal", user2=current_user.id).all()
    for i in chats:
        if Messages.query.filter_by(chat_id=i.id).all():
            last_message = Messages.query.filter_by(chat_id=i.id).all()[-1]
        else:
            last_message = 0
        user = i.user1 if i.user1 != current_user.id else i.user2
        user = User.query.filter_by(id=user).first()
        unread = len(Messages.query.filter_by(chat_id=i.id, read=0).all()) - len(
            Messages.query.filter_by(author=current_user.id, chat_id=i.id, read=0).all())
        if last_message:
            chat_rooms.append({
                'id': i.id,
                'user': f'{user.name} {user.surname}' if not user.org else f'{user.org_name}',
                'profile_photo': user.photo,
                'last_message': last_message.text,
                'last_message_time': last_message.timestamp.strftime('%H:%M'),
                'last_message_timestamp': last_message.timestamp,
                'unread': unread
            })
        else:
            chat_rooms.append({
                'id': i.id,
                'user': f'{user.name} {user.surname}' if not user.org else f'{user.org_name}',
                'profile_photo': user.photo,
                'last_message': '',
                'last_message_time': '',
                'last_message_timestamp': datetime.now(),
                'unread': unread
            })
    chat_rooms = sorted(chat_rooms, key=lambda x: x['last_message_time'])[::-1]
    return render_template('chats/personal_chats.html', chat_rooms=chat_rooms)


@main.route('/chats/jk')
@login_required
def jk_chats():
    jks = JK.query.filter_by(moderated=1).all()
    chats = ChatRooms.query.filter_by(type="jk").all()
    chat_jks = [i.jk for i in chats]
    for i in jks:
        if i.id not in chat_jks:
            new_chat = ChatRooms(type="jk", jk=i.id)
            db.session.add(new_chat)
            db.session.commit()
    chats = ChatRooms.query.filter_by(type="jk").all()
    chat_rooms = []
    for i in chats:
        if Messages.query.filter_by(chat_id=i.id).all():
            last_message = Messages.query.filter_by(chat_id=i.id).all()[-1]
        else:
            last_message = 0
        if last_message:
            chat_rooms.append({
                'id': i.id,
                'user': JK.query.filter_by(id=i.jk).first().name,
                'last_message': last_message.text,
                'last_message_time': last_message.timestamp.strftime('%H:%M'),
                'last_message_timestamp': last_message.timestamp,
            })
        else:
            chat_rooms.append({
                'id': i.id,
                'user': JK.query.filter_by(id=i.jk).first().name,
                'last_message': '',
                'last_message_time': '',
                'last_message_timestamp': datetime.now(),
            })
    chat_rooms = sorted(chat_rooms, key=lambda x: x['last_message_time'])[::-1]
    return render_template('chats/jk_chats.html', chats=chat_rooms, JK=JK)


@main.route('/chats/personal/<id>')
@login_required
def personal_chat(id):
    session['room'] = id
    chat_rooms = []
    chats = ChatRooms.query.filter_by(type="personal", user1=current_user.id).all() + ChatRooms.query.filter_by(
        type="personal", user2=current_user.id).all()
    for i in chats:
        if Messages.query.filter_by(chat_id=i.id).all():
            last_message = Messages.query.filter_by(chat_id=i.id).all()[-1]
        else:
            last_message = 0
        user = i.user1 if i.user1 != current_user.id else i.user2
        user = User.query.filter_by(id=user).first()
        unread = len(Messages.query.filter_by(chat_id=i.id, read=0).all()) - len(
            Messages.query.filter_by(author=current_user.id, chat_id=i.id, read=0).all())
        if last_message:
            chat_rooms.append({
                'id': i.id,
                'user': f'{user.name} {user.surname}' if not user.org else f'{user.org_name}',
                'profile_photo': user.photo,
                'last_message': last_message.text,
                'last_message_time': last_message.timestamp.strftime('%H:%M'),
                'last_message_timestamp': last_message.timestamp,
                'unread': unread
            })
        else:
            chat_rooms.append({
                'id': i.id,
                'user': f'{user.name} {user.surname}' if not user.org else f'{user.org_name}',
                'profile_photo': user.photo,
                'last_message': '',
                'last_message_time': '',
                'last_message_timestamp': datetime.now(),
                'unread': unread
            })
    chat_rooms = sorted(chat_rooms, key=lambda x: x['last_message_time'])[::-1]
    chat = ChatRooms.query.filter_by(id=id).first()
    user = chat.user1 if chat.user1 != current_user.id else chat.user2
    user = User.query.filter_by(id=user).first()
    msgs = []
    messages = Messages.query.filter_by(chat_id=id).all()
    for i in messages:
        msgs.append({
            'profile_photo': user.photo,
            'text': i.text,
            'time': i.timestamp.strftime('%H:%M'),
            'author': i.author
        })
    _ = Messages.query.filter_by(chat_id=id, read=0, author=user.id).update({'read': 1})
    db.session.commit()
    return render_template('chats/personal_chat.html', chat_rooms=chat_rooms, msgs=msgs, chat_id=id, user=user)


@main.route('/chats/jk/<id>')
@login_required
def jk_chat(id):
    session['room'] = id
    chat_rooms = []
    chats = ChatRooms.query.filter_by(type="personal", user1=current_user.id).all() + ChatRooms.query.filter_by(
        type="personal", user2=current_user.id).all()
    for i in chats:
        if Messages.query.filter_by(chat_id=i.id).all():
            last_message = Messages.query.filter_by(chat_id=i.id).all()[-1]
        else:
            last_message = 0
        user = i.user1 if i.user1 != current_user.id else i.user2
        user = User.query.filter_by(id=user).first()
        unread = len(Messages.query.filter_by(chat_id=i.id, read=0).all()) - len(
            Messages.query.filter_by(author=current_user.id, chat_id=i.id, read=0).all())
        if last_message:
            chat_rooms.append({
                'id': i.id,
                'user': f'{user.name} {user.surname}' if not user.org else f'{user.org_name}',
                'profile_photo': user.photo,
                'last_message': last_message.text,
                'last_message_time': last_message.timestamp.strftime('%H:%M'),
                'last_message_timestamp': last_message.timestamp,
                'unread': unread
            })
        else:
            chat_rooms.append({
                'id': i.id,
                'user': f'{user.name} {user.surname}' if not user.org else f'{user.org_name}',
                'profile_photo': user.photo,
                'last_message': '',
                'last_message_time': '',
                'last_message_timestamp': datetime.now(),
                'unread': unread
            })
    chat_rooms = sorted(chat_rooms, key=lambda x: x['last_message_time'])[::-1]
    msgs = []
    messages = Messages.query.filter_by(chat_id=id).all()
    for i in messages:
        user = User.query.filter_by(id=i.author).first()
        msgs.append({
            'profile_photo': user.photo,
            'text': i.text,
            'time': i.timestamp.strftime('%H:%M'),
            'author': user
        })
    jk = JK.query.filter_by(id=ChatRooms.query.filter_by(id=id).first().jk).first()
    return render_template('chats/jk_chat.html', chat_rooms=chat_rooms, msgs=msgs, chat_id=id, jk=jk)


@main.route('/members/<id>', methods=['POST', 'GET'])
@login_required
def members(id):
    chat_room = ChatRooms.query.filter_by(id=id).first()
    jk = JK.query.filter_by(id=chat_room.jk).first()
    members = User.query.filter_by(jk=jk.id).all()
    return render_template('chats/members.html', id=id, members=members)


@main.route('/support', methods=['POST', 'GET'])
@login_required
def support():
    complaints = []
    complaints_raw = Complaints.query.filter_by().all()
    if request.method == 'POST':
        start_raw = request.form['start']
        finish_raw = request.form['finish']
        if start_raw:
            start = datetime.strptime(start_raw, '%Y-%m-%d')
        else:
            start = datetime.strptime('2020-01-01', '%Y-%m-%d')
        if finish_raw:
            finish = datetime.strptime(finish_raw, '%Y-%m-%d')
        else:
            finish = datetime.strptime('2030-01-01', '%Y-%m-%d')
        complaints_raw = list(filter(lambda x: start < x.timestamp < finish, complaints_raw))
    for i in complaints_raw:
        user = User.query.filter_by(id=i.from_user).first()
        jk = JK.query.filter_by(id=user.jk).first()
        complaints.append(
            {
                'id': i.id,
                'date': i.timestamp.strftime('%Y-%m-%d'),
                'name': user.name + ' ' + user.surname,
                'phone': user.phone,
                'jk': jk.name,
                'type': i.type,
                'status': i.status,
                'text': i.text,
                'page': i.promotion_id if i.type == 'promotion' else i.new_id if i.type == 'new' else i.profile_id if i.type == 'profile' else '',
                'message': Messages.query.filter_by(id=i.message_id).first() if i.type == 'message' else '',
            }
        )
    return render_template('complaints/complaints.html', complaints=complaints)


@main.route('/uk/all', methods=['POST', 'GET'])
@login_required
def all_uk():
    data = User.query.filter_by(is_uk=1).all()
    if request.method == 'POST':
        start_raw = request.form['start']
        finish_raw = request.form['finish']
        if start_raw:
            start = int(datetime.strptime(start_raw, '%Y-%m-%d').timestamp())
        else:
            start = datetime.strptime('2020-01-01', '%Y-%m-%d').timestamp()
        if finish_raw:
            finish = int(datetime.strptime(finish_raw, '%Y-%m-%d').timestamp())
        else:
            finish = datetime.strptime('2030-01-01', '%Y-%m-%d').timestamp()
        if not start:
            start = datetime.strptime('2020-01-01', '%Y-%m-%d').timestamp()
        if not finish:
            finish = datetime.strptime('2030-01-01', '%Y-%m-%d').timestamp()
        data = list(filter(lambda x: start < x.registered < finish, data))
        return render_template('stats/stats.html', start=datetime.fromtimestamp(start).strftime('%Y-%m-%d'),
                               finish=datetime.fromtimestamp(finish).strftime('%Y-%m-%d'),
                               data=data, datetime=datetime, JK=JK, user=user, uk=uk)
    else:
        start = datetime.strptime('2020-01-01', '%Y-%m-%d').timestamp()
        finish = datetime.strptime('2030-01-01', '%Y-%m-%d').timestamp()
    data = list(filter(lambda x: start < x.registered < finish, data))
    data = sorted(data, key=lambda x: x.id)
    return render_template('uk/all_uk.html', data=data, datetime=datetime, JK=JK, str=str, user=user, uk=uk)


@main.route('/uk/<id>', methods=['POST', 'GET'])
@login_required
def uk(id):
    user = User.query.filter_by(id=id).first()
    jk = JK.query.filter_by(id=user.jk).first()
    return render_template('uk/uk.html', user=user, jk=jk)


@main.route('/uk/moderate', methods=['POST', 'GET'])
@login_required
def moderate_uk():
    data = User.query.filter_by(is_uk=1).all()
    if request.method == 'POST':
        start_raw = request.form['start']
        finish_raw = request.form['finish']
        if start_raw:
            start = int(datetime.strptime(start_raw, '%Y-%m-%d').timestamp())
        else:
            start = datetime.strptime('2020-01-01', '%Y-%m-%d').timestamp()
        if finish_raw:
            finish = int(datetime.strptime(finish_raw, '%Y-%m-%d').timestamp())
        else:
            finish = datetime.strptime('2030-01-01', '%Y-%m-%d').timestamp()
        if not start:
            start = datetime.strptime('2020-01-01', '%Y-%m-%d').timestamp()
        if not finish:
            finish = datetime.strptime('2030-01-01', '%Y-%m-%d').timestamp()
        data = list(filter(lambda x: start < x.registered < finish, data))
        return render_template('stats/stats.html', start=datetime.fromtimestamp(start).strftime('%Y-%m-%d'),
                               finish=datetime.fromtimestamp(finish).strftime('%Y-%m-%d'),
                               data=data, datetime=datetime, JK=JK, user=user, uk=uk)
    else:
        start = datetime.strptime('2020-01-01', '%Y-%m-%d').timestamp()
        finish = datetime.strptime('2030-01-01', '%Y-%m-%d').timestamp()
    data = list(filter(lambda x: start < x.registered < finish, data))
    data = sorted(data, key=lambda x: x.id)
    return render_template('uk/moderate_uk.html', data=data, datetime=datetime, JK=JK, str=str, user=user, uk=uk)

# _XiuCNs7:@xu
import json
from datetime import datetime
from os import getcwd
from flask import Blueprint, render_template, request, send_from_directory, make_response, session, redirect, url_for
from flask_login import login_required, current_user
import os
from . import db
from app.models import JK, Addresses, User, News, Promotions, Transactions, Complaints
from app.models import Messages, ChatRooms, AdditionalUK

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
        print(uk)
        return render_template('stats/stats.html', start=datetime.fromtimestamp(start).strftime('%Y-%m-%d'),
                               finish=datetime.fromtimestamp(finish).strftime('%Y-%m-%d'),
                               data=data, datetime=datetime, active=active, org=org, JK=JK, user=user,
                               user_data=user_data, uk=uk, str=str, counters=couters)
    else:
        start = datetime.strptime('2020-01-01', '%Y-%m-%d').timestamp()
        finish = datetime.strptime('2030-01-01', '%Y-%m-%d').timestamp()
    data = list(filter(lambda x: start < x.registered < finish, data))
    data = sorted(data, key=lambda x: x.id)
    print(uk)
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
    users = User.query.filter_by(org=0).all()
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
    jks_ = JK.query.filter_by(moderated=1).all()
    jks = []
    for i in jks_:
        jks.append({
            'id': i.id,
            'name': i.name,
            'city': i.city,
            'num_people': len(User.query.filter_by(jk=i.id, org=0).all()),
            'num_orgs': len(User.query.filter_by(jk=i.id, org=1).all()),
            'num_news': len(News.query.filter_by(jk=i.id).all()),
            'num_proms': len(Promotions.query.filter_by(jk=i.id).all()),
        })
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
    jks_ = JK.query.filter_by(moderated=0).all()
    jks = []
    for i in jks_:
        jks.append({
            'id': i.id,
            'name': i.name,
            'city': i.city,
            'num_people': len(User.query.filter_by(jk=i.id, org=0).all()),
            'num_orgs': len(User.query.filter_by(jk=i.id, org=1).all()),
            'num_news': len(News.query.filter_by(jk=i.id).all()),
            'num_proms': len(Promotions.query.filter_by(jk=i.id).all()),
        })
    addrs = dict()
    streets = dict()
    for i in jks_:
        addrs.update({i.id: []})
    for i in jks_:
        addresses = Addresses.query.filter_by(jk_id=i.id).all()
        for j in addresses:
            addrs[i.id].append(j.name)
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


@main.route('/org/<id>', methods=['GET'])
@main.route('/user/<id>', methods=['GET'])
@login_required
def user(id):
    user = User.query.filter_by(id=id).first()
    jk = JK.query.filter_by(id=user.jk).first()
    if user.org:
        news = News.query.filter_by().all()
    else:
        news = Promotions.query.filter_by().all()
    jks = JK.query.filter_by(moderated=1).all()
    user_transactions = Transactions.query.filter_by(userId=id)
    return render_template('people/user.html', user=user, jk=jk, news=news, jks=jks, user_transactions=user_transactions)


@main.route('/block/<id>', methods=['GET'])
@login_required
def block(id):
    _ = User.query.filter_by(id=id).update({'status': 'blocked'})
    db.session.commit()
    user = User.query.filter_by(id=id).first()
    if user.is_uk:
        return redirect(url_for('main.uk', id=id))
    return redirect(url_for('main.user', id=id))


@main.route('/connect/<id>', methods=['GET'])
@login_required
def connect(id):
    if int(id) != current_user.id:
        chats = ChatRooms.query.filter_by(user1=id, user2=current_user.id).all() + \
                ChatRooms.query.filter_by(user2=id, user1=current_user.id).all()
        if chats:
            chat = chats[0]
        else:
            new_chat = ChatRooms(type='personal', user2=id, user1=current_user.id)
            db.session.add(new_chat)
            db.session.commit()
            chat = new_chat
        return redirect(url_for('main.personal_chat', id=chat.id))
    else:
        user = User.query.filter_by(id=id).first()
        if user.is_uk:
            return redirect(url_for('main.uk', id=id))
        return redirect(url_for('main.user', id=id))


@main.route('/unblock/<id>', methods=['GET'])
@login_required
def unblock(id):
    _ = User.query.filter_by(id=id).update({'status': 'inactive'})
    db.session.commit()
    user = User.query.filter_by(id=id).first()
    if user.is_uk:
        return redirect(url_for('main.uk', id=id))
    return redirect(url_for('main.user', id=id))


@main.route('/org/<id>', methods=['POST'])
@main.route('/user/<id>', methods=['POST'])
@login_required
def user_post(id):
    org_name = request.form.get('org_name')
    inn = request.form.get('inn')
    phone = request.form.get('phone').replace('+', '').replace(' ', '').replace('-', '').replace('(', '').replace(')',
                                                                                                                  '')
    name = request.form.get('name')
    surname = request.form.get('surname')
    second_name = request.form.get('second_name')
    jk = request.form.get('jk')
    address = request.form.get('address')
    user = User.query.filter_by(id=id).first()
    if user.org:
        _ = User.query.filter_by(id=user.id).update({'name': name, 'surname': surname, 'second_name': second_name,
                                                     'address': address, 'inn': inn, 'org_name': org_name,
                                                     'jk': jk, 'phone': phone})
    else:
        _ = User.query.filter_by(id=user.id).update(
            {'name': name, 'surname': surname, 'address': address, 'jk': jk, 'phone': phone})
    db.session.commit()
    if user.is_uk:
        return redirect(url_for('main.uk', id=id))
    return redirect(url_for('main.user', id=id))


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
    jks = JK.query.filter_by(moderated=1).all()
    return render_template('news/new.html', jk=new, User=User, jks=jks)


@main.route('/block_new/<id>')
@login_required
def block_new(id):
    _ = News.query.filter_by(id=id).update({'blocked': 1})
    db.session.commit()
    return redirect(url_for('main.new', id=id))


@main.route('/unblock_new/<id>')
@login_required
def unblock_new(id):
    _ = News.query.filter_by(id=id).update({'blocked': 0})
    db.session.commit()
    return redirect(url_for('main.new', id=id))


@main.route('/update_new/<id>', methods=["POST"])
@login_required
def update_new(id):
    db.session.commit()
    name = request.form.get('name')
    description = request.form.get('description')
    phone = request.form.get('phone').replace('+', '').replace(' ', '').replace('-', '').replace('(', '').replace(')',
                                                                                                                  '')
    jk = request.form.get('jk')
    address = request.form.get('address')
    _ = News.query.filter_by(id=id).update(
        {'name': name, 'description': description, 'address': address, 'jk': jk, 'phone': phone})
    db.session.commit()
    return redirect(url_for('main.new', id=id))


@main.route('/promotion/<id>')
@login_required
def promotion(id):
    new = Promotions.query.filter_by(id=id).first()
    jks = JK.query.filter_by(moderated=1).all()
    return render_template('news/promotion.html', jk=new, User=User, jks=jks)


@main.route('/block_promotion/<id>')
@login_required
def block_promotion(id):
    _ = Promotions.query.filter_by(id=id).update({'blocked': 1})
    db.session.commit()
    return redirect(url_for('main.promotion', id=id))


@main.route('/unblock_promotion/<id>')
@login_required
def unblock_promotion(id):
    _ = Promotions.query.filter_by(id=id).update({'blocked': 0})
    db.session.commit()
    return redirect(url_for('main.promotion', id=id))


@main.route('/update_promotion/<id>', methods=["POST"])
@login_required
def update_promotion(id):
    db.session.commit()
    name = request.form.get('name')
    description = request.form.get('description')
    phone = request.form.get('phone').replace('+', '').replace(' ', '').replace('-', '').replace('(', '').replace(')',
                                                                                                                  '')
    jk = request.form.get('jk')
    price = request.form.get('price')
    address = request.form.get('address')
    _ = Promotions.query.filter_by(id=id).update(
        {'name': name, 'description': description, 'address': address, 'jk': jk, 'phone': phone, 'price': price})
    db.session.commit()
    return redirect(url_for('main.promotion', id=id))


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
    jks = JK.query.filter_by().all()
    return render_template('auth/profile.html', name=current_user.name, user=current_user, jks=jks)


@main.route('/edit_profile', methods=['POST'])
@login_required
def edit_profile():
    org_name = request.form.get('org_name')
    inn = request.form.get('inn')
    phone = request.form.get('phone').replace('+', '').replace(' ', '').replace('-', '').replace('(', '').replace(')',
                                                                                                                  '')
    name = request.form.get('name')
    surname = request.form.get('surname')
    second_name = request.form.get('second_name')
    jk = request.form.get('jk')
    address = request.form.get('address')
    if current_user.org:
        _ = User.query.filter_by(id=current_user.id).update(
            {'name': name, 'surname': surname, 'second_name': second_name,
             'address': address, 'inn': inn, 'org_name': org_name,
             'jk': jk, 'phone': phone})
    else:
        _ = User.query.filter_by(id=current_user.id).update(
            {'name': name, 'surname': surname, 'address': address, 'jk': jk, 'phone': phone})
    db.session.commit()
    return redirect(url_for('main.profile'))


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
    chat_rooms = sorted(chat_rooms, key=lambda x: x['last_message_timestamp'])
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
                'photo': JK.query.filter_by(id=i.jk).first().photo,
                'user': JK.query.filter_by(id=i.jk).first().name,
                'last_message': last_message.text,
                'last_message_time': last_message.timestamp.strftime('%H:%M'),
                'last_message_timestamp': last_message.timestamp,
            })
        else:
            chat_rooms.append({
                'id': i.id,
                'photo': JK.query.filter_by(id=i.jk).first().photo,
                'user': JK.query.filter_by(id=i.jk).first().name,
                'last_message': '',
                'last_message_time': '',
                'last_message_timestamp': datetime.now(),
            })
    chat_rooms = sorted(chat_rooms, key=lambda x: x['last_message_timestamp'])
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
            'id': i.id,
            'profile_photo': user.photo,
            'text': i.text,
            'time': i.timestamp.strftime('%H:%M'),
            'author': i.author,
            'image': i.image
        })
    _ = Messages.query.filter_by(chat_id=id, read=0, author=user.id).update({'read': 1})
    db.session.commit()
    return render_template('chats/personal_chat.html', chat_rooms=chat_rooms, msgs=msgs, chat_id=id, user=user)


@main.route('/delete_msg/<id>')
@login_required
def delete_msg(id):
    msg = Messages.query.filter_by(id=id).first()
    chat = ChatRooms.query.filter_by(id=msg.chat_id).first()
    _ = Messages.query.filter_by(id=id).delete()
    db.session.commit()
    if not chat:
        return {'status': 'ok'}  # redirect(url_for('main.jk_chat', id=chat.id))
    else:
        if chat.type == 'jk':
            return {'status': 'ok'}  # redirect(url_for('main.jk_chat', id=chat.id))
        else:
            return {'status': 'ok'}  # redirect(url_for('main.personal_chat', id=chat.id))


@main.route('/chats/jk/<id>')
@login_required
def jk_chat(id):
    session['room'] = id
    chat_rooms = []
    chat_rooms = sorted(chat_rooms, key=lambda x: x['last_message_time'])[::-1]
    msgs = []
    messages = Messages.query.filter_by(chat_id=id).all()
    for i in messages:
        user = User.query.filter_by(id=i.author).first()
        msgs.append({
            'id': i.id,
            'profile_photo': user.photo,
            'text': i.text,
            'time': i.timestamp.strftime('%H:%M'),
            'author': user,
            'image': i.image
        })
    jk = JK.query.filter_by(id=ChatRooms.query.filter_by(id=id).first().jk).first()
    return render_template('chats/jk_chat.html', chat_rooms=chat_rooms, msgs=msgs, chat_id=id, jk=jk)


@main.route('/members/<id>', methods=['POST', 'GET'])
@login_required
def members(id):
    chat_room = ChatRooms.query.filter_by(id=id).first()
    jk = JK.query.filter_by(id=chat_room.jk).first()
    members = User.query.filter_by(jk=jk.id).all()
    return render_template('chats/members.html', id=int(id), members=members, participants=len(members), jk=jk)


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
                'user': user.id,
                'date': i.timestamp.strftime('%Y-%m-%d'),
                'name': user.name + ' ' + user.surname + ' ' + user.second_name if user.org else user.name + ' ' + user.surname,
                'phone': user.phone,
                'jk': jk.name,
                'type': i.type,
                'status': i.status,
                'text': i.text,
                'page': i.promotion_id if i.type == 'promotion' else i.new_id if i.type == 'new' else i.profile_id if i.type == 'profile' else '',
                'message': Messages.query.filter_by(id=i.message_id).first() if i.type == 'message' else '',
                'reply': i.reply
            }
        )
    return render_template('complaints/complaints.html', complaints=complaints)


@main.route('/reply_complaint/<id>', methods=['POST'])
@login_required
def reply_complaint(id):
    text = request.form.get('text')
    complaint = Complaints.query.filter_by(id=id).first()
    _ = Complaints.query.filter_by(id=id).update({'status': 1, 'reply': text})
    db.session.commit()
    if int(id) != current_user.id:
        chats = ChatRooms.query.filter_by(user1=complaint.from_user, user2=current_user.id).all() + \
                ChatRooms.query.filter_by(user2=complaint.from_user, user1=current_user.id).all()
        if chats:
            chat = chats[0]
        else:
            new_chat = ChatRooms(type='personal', user2=complaint.from_user, user1=current_user.id)
            db.session.add(new_chat)
            db.session.commit()
            chat = new_chat
        new_message = Messages(author=complaint.from_user, chat_id=chat.id,
                               text=f'Жалоба №{complaint.id}\n{complaint.text}')
        db.session.add(new_message)
        new_message = Messages(author=current_user.id, chat_id=chat.id, text=text)
        db.session.add(new_message)
        db.session.commit()
        return redirect(url_for('main.personal_chat', id=chat.id))
    return redirect(url_for('main.support'))


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
        return render_template('uk/all_uk.html', start=datetime.fromtimestamp(start).strftime('%Y-%m-%d'),
                               finish=datetime.fromtimestamp(finish).strftime('%Y-%m-%d'),
                               data=data, datetime=datetime, JK=JK, user=user, uk=uk, str=str)
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
    jks = JK.query.filter_by().all()
    uk_data = AdditionalUK.query.filter_by(uk_id=id).first()
    if uk_data:
        return render_template('uk/uk.html', user=user, jk=jk, jks=jks, uk_data=uk_data,
                               contact_phones=json.loads(uk_data.contact_phones),
                               useful_phones=json.loads(uk_data.useful_phones), x=len(json.loads(uk_data.contact_phones)),
                               y=len(json.loads(uk_data.useful_phones)), enumerate=enumerate)
    else:
        return render_template('uk/uk.html', user=user, jk=jk, jks=jks, uk_data=uk_data, x=0, y=0, enumerate=enumerate)


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
        return render_template('uk/moderate_uk.html', start=datetime.fromtimestamp(start).strftime('%Y-%m-%d'),
                               finish=datetime.fromtimestamp(finish).strftime('%Y-%m-%d'),
                               data=data, datetime=datetime, JK=JK, user=user, uk=uk, str=str)
    else:
        start = datetime.strptime('2020-01-01', '%Y-%m-%d').timestamp()
        finish = datetime.strptime('2030-01-01', '%Y-%m-%d').timestamp()
    data = list(filter(lambda x: start < x.registered < finish, data))
    data = sorted(data, key=lambda x: x.id)
    return render_template('uk/moderate_uk.html', data=data, datetime=datetime, JK=JK, str=str, user=user, uk=uk)


@main.route('/delete_picture/<id>', methods=['POST', 'GET'])
@login_required
def delete_picture(id):
    user = User.query.filter_by(id=id).first()
    if user.org == 1:
        if user.is_uk == 1:
            _ = User.query.filter_by(id=id).update({'photo': 'default_uk.png'})
            db.session.commit()
            return redirect(url_for('main.uk', id=id))
        _ = User.query.filter_by(id=id).update({'photo': 'default_org.png'})
        db.session.commit()
        return redirect(url_for('main.user', id=id))
    else:
        _ = User.query.filter_by(id=id).update({'photo': 'default_user.jpg'})
        db.session.commit()
        return redirect(url_for('main.user', id=id))


@main.route('/delete_picture_new/<id>/<picture>', methods=['POST', 'GET'])
@login_required
def delete_picture_new(id, picture):
    new = News.query.filter_by(id=id).update({f'photo{picture}': None})
    db.session.commit()
    return redirect(url_for('main.new', id=id))


@main.route('/delete_picture_promotion/<id>/<picture>', methods=['POST', 'GET'])
@login_required
def delete_picture_promotion(id, picture):
    new = Promotions.query.filter_by(id=id).update({f'photo{picture}': None})
    db.session.commit()
    return redirect(url_for('main.new', id=id))


@main.route('/delete_picture_jk/<id>', methods=['POST', 'GET'])
@login_required
def delete_picture_jk(id):
    new = JK.query.filter_by(id=id).update({f'photo': 'default_org.png'})
    db.session.commit()
    return redirect(url_for('main.jk', id=id))


@main.route('/add_jk', methods=['POST', 'GET'])
@login_required
def add_jk():
    name = request.form.get('name')
    city = request.form.get('city')
    new_jk = JK(name=name, city=city, moderated=1)
    db.session.add(new_jk)
    db.session.commit()
    for i in range(1, 11):
        addr = request.form.get(f'fullName{i}')
        print(addr)
        if addr:
            new_addr = Addresses(name=addr, city=city, jk_id=new_jk.id)
            db.session.add(new_addr)
            db.session.commit()
    f = request.files['image']
    if f:
        f.save(f"{getcwd()}/app/static/jk/{new_jk.id}.png")
        _ = JK.query.filter_by(id=new_jk.id).update({f'photo': f'{new_jk.id}.png'})
    else:
        _ = JK.query.filter_by(id=new_jk.id).update({f'photo': 'default_org.png'})
    db.session.commit()
    return redirect(url_for('main.jk', id=new_jk.id))


@main.route('/edit_jk/<id>', methods=['POST', 'GET'])
@login_required
def edit_jk(id):
    name = request.form.get('name')
    city = request.form.get('city')
    _ = JK.query.filter_by(id=id).update({'name': name, 'city': city, 'moderated': 1})
    _ = Addresses.query.filter_by(jk_id=id).delete()
    db.session.commit()
    for i in range(1, 11):
        addr = request.form.get(f'fullName{i}')
        print(addr)
        if addr:
            new_addr = Addresses(name=addr, city=city, jk_id=id)
            db.session.add(new_addr)
            db.session.commit()
    f = request.files['image']
    if f:
        f.save(f"{getcwd()}/app/static/jk/{id}.png")
        _ = JK.query.filter_by(id=id).update({f'photo': f'{id}.png'})
    db.session.commit()
    return redirect(url_for('main.jk', id=id))


@main.route('/moderate_jk/<id>', methods=['POST', 'GET'])
@login_required
def moderate_jk(id):
    name = request.form.get('name')
    city = request.form.get('city')
    _ = JK.query.filter_by(id=id).update({'name': name, 'city': city, 'moderated': 1})
    _ = Addresses.query.filter_by(jk_id=id).delete()
    db.session.commit()
    for i in range(1, 11):
        addr = request.form.get(f'fullName{i}')
        print(addr)
        if addr:
            new_addr = Addresses(name=addr, city=city, jk_id=id)
            db.session.add(new_addr)
            db.session.commit()
    return redirect(url_for('main.jk', id=id))


@main.route('/additional_uk/<id>', methods=['POST', 'GET'])
@login_required
def additional_uk(id):
    mon = request.form.get('mon')
    tue = request.form.get('tue')
    wed = request.form.get('wed')
    thu = request.form.get('thu')
    fri = request.form.get('fri')
    sat = request.form.get('sat')
    san = request.form.get('san')
    contacts = dict()
    usefuls = dict()
    for i in range(11):
        contact_name = request.form.get(f'contact_name_{i}')
        contact_phone = request.form.get(f'contact_phone_{i}')
        if contact_name and contact_phone:
            contacts.update({contact_name: contact_phone})
        useful_name = request.form.get(f'useful_name_{i}')
        useful_phone = request.form.get(f'useful_phone_{i}')
        if useful_name and useful_phone:
            usefuls.update({useful_name: useful_phone})
    print(usefuls, contacts)
    if AdditionalUK.query.filter_by(uk_id=id).first():
        _ = AdditionalUK.query.filter_by(uk_id=id).update({'mon': mon, 'tue': tue, 'wed': wed, 'thu': thu, 'fri': fri,
                                                        'sat': sat, 'san': san, 'contact_phones': json.dumps(contacts),
                                                        'useful_phones': json.dumps(usefuls)})
    else:
        new_uk = AdditionalUK(mon=mon, tue=tue, wed=wed, thu=thu, fri=fri,
                               sat=sat, san=san, contact_phones=json.dumps(contacts),
                               useful_phones=json.dumps(usefuls), uk_id=id)
        db.session.add(new_uk)
    db.session.commit()
    return redirect(url_for('main.uk', id=id))

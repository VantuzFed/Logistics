# Задание на учебную практику: разработать веб-приложение для
# автоматизации безнес-процессов логистической компании
# Среда разработки: PyCharm
# Дипломный проект
# Название: Разработка веб-приложения
# Разработал: Федюнин Иван Владиславович ТБД-82
# Дата: 05.06.2026
# Язык: Python

import os
import string
import subprocess
from datetime import datetime

from flask import Flask, request, jsonify, make_response, redirect, url_for, render_template, send_file, abort, after_this_request
import secrets
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import create_engine, func, or_, and_
from sqlalchemy.orm import sessionmaker
from models import Base, Users, Sessions, Clients, Drivers, Vehicles, Warehouses, Orders, Routes, t_warehouses_orders

app = Flask(__name__)

engine = create_engine('postgresql://admin:1234@192.168.56.103:5432/logistics', echo=False)
DB_Session = sessionmaker(bind=engine)

class UserSession:
    def __init__(self):
        self.session_token = request.cookies.get('session_token')
        self.user_id = False
        self.login = False
        self.acc_type = False
        with DB_Session() as db:
            user = db.query(Users.login, Users.id, Users.account_type, Sessions.token, Sessions.ip_address).filter(
                and_(Sessions.token == self.session_token, Sessions.ip_address == request.remote_addr, Sessions.expiration_date > func.current_timestamp())).join(
                Sessions).first()
        if user:
            self.user_id = user.id
            self.login = user.login
            self.acc_type = user.account_type
        else:
            self.delete_expired_sessions()

    def delete_expired_sessions(self):
        with DB_Session() as db:
            exp_session = db.query(Sessions).filter(
                and_(Sessions.expiration_date < func.current_timestamp(), Sessions.ip_address == request.remote_addr)).all()
            if exp_session:
                for rec in exp_session:
                    db.delete(rec)
                db.commit()

class LoginUsr:
    def __init__(self, e_mail, passwd):
        self.email_str = e_mail
        self.password_str = passwd

    def login_fun(self):
        with DB_Session() as db:
            user = db.query(Users).filter(Users.e_mail == self.email_str).first()
        if user:
            if user.e_mail == self.email_str and check_password_hash(user.password, self.password_str):
                with DB_Session() as db:
                    token_var = secrets.token_hex(24)
                    new_user_session = Sessions(token=token_var, ip_address=request.remote_addr, user_id=user.id)
                    db.add(new_user_session)
                    db.commit()
                response = make_response(jsonify({'message': 'Вы успешно зашли в аккаунт', 'login': user.login, 'account_type': user.account_type, 'success': True}))
                response.set_cookie('session_token', token_var, max_age=60 * 45)
                return response
        return jsonify({'message': 'Неверное имя пользователя или пароль', 'success': False})

class RegisterUsr:
    def __init__(self, login_st, email, passwd):
        self.login_str = login_st
        self.e_mail_str = email
        self.password_str = passwd
        self.hashed_password = generate_password_hash(self.password_str, method="pbkdf2:sha256", salt_length=16)

    def reg_fun(self):
        with DB_Session() as db:
            user = db.query(Users).filter(or_(Users.login == self.login_str, Users.e_mail == self.e_mail_str)).first()
        if user:
            if user.login == self.login_str or user.e_mail == self.e_mail_str:
                return jsonify({'message': 'Такой пользователь уже существует', 'success': False})
        else:
            with DB_Session() as db:
                new_user = Users(login=self.login_str, e_mail=self.e_mail_str, password=self.hashed_password)
                db.add(new_user)
                db.commit()
            return jsonify({'message': 'Пользователь успешно создан', 'success': True})


# Routes
@app.route('/')
def index():
    session_user = UserSession()
    return render_template('index.html', page_name='Главная страница', user=session_user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    session_user = UserSession()
    if request.method == 'POST':
        data = request.json
        email_str = data.get('e_mail')
        password_str = data.get('password')
        login_obj = LoginUsr(email_str, password_str)
        return login_obj.login_fun()
    return render_template('login.html', page_name='Вход', user=session_user)

@app.route('/register', methods=['GET', 'POST'])
def register():
    session_user = UserSession()
    if request.method == 'POST':
        data = request.json
        login_str = data.get('login')
        e_mail_str = data.get('e_mail')
        password_str = data.get('password')
        reg_obj = RegisterUsr(login_str, e_mail_str, password_str)
        return reg_obj.reg_fun()
    return render_template('regist.html', page_name='Регистрация', user=session_user)

@app.route('/logout')
def logout():
    response = make_response(redirect(url_for('index')))
    response.set_cookie('session_token', '', expires=0)
    return response

@app.route('/admin_panel')
def admin_panel():
    session_user = UserSession()
    if session_user.login and session_user.acc_type == 'Admin':
        return render_template('admin.html', user=session_user, page_name='Админ-панель')
    else:
        return render_template('error.html', user=session_user, page_name='Админ-панель', message='Требуется вход')

@app.route('/dashboard', methods=['GET'])
def dashboard():
    session_user = UserSession()
    if session_user.login:
        return render_template('dashboard.html', page_name='Главный интерфейс', user=session_user)
    else:
        return render_template('error.html', user=session_user, page_name='Админ-панель', message='Требуется вход')

@app.route('/api/admin', methods=['GET'])
def admin_api():
    session_user = UserSession()
    if session_user.login and session_user.acc_type == 'Admin':
        with DB_Session() as db:
            users_count = db.query(Users).count()
            orders_count = db.query(Orders).count()
            valid_session = db.query(Sessions).filter(Sessions.expiration_date > func.current_timestamp()).count()
            users_sessions = db.query(Users.login, func.count(Sessions.id)).group_by(Users.login).join(Sessions).all()
            users_sessions_tup = [{'user_login': user_login, 'sessions_count': count} for user_login, count in users_sessions]
            return jsonify({'users_count': users_count,'orders_count': orders_count, 'valid_session': valid_session, 'sessions_per_user': users_sessions_tup})
    else:
        return jsonify({'error': 'Требуется вход или права администратора'})


# API Endpoints
@app.route('/api/clients', methods=['GET', 'POST', 'DELETE'])
def clients_api():
    session_user = UserSession()
    if not session_user.user_id:
        return jsonify({'error': 'Требуется вход'})

    with DB_Session() as db:
        match request.method:
            case 'GET':
                clients = db.query(Clients).all()
                return jsonify([{'id': c.id, 'first_name': c.first_name, 'last_name': c.last_name, 'e_mail': c.e_mail, 'phone_number': c.phone_number} for c in clients])
            case 'POST':
                data = request.json
                new_client = Clients(first_name=data['first_name'], last_name=data['last_name'], e_mail=data['e_mail'], phone_number=data['phone_number'])
                db.add(new_client)
                db.commit()
                return jsonify({'message': 'Client added', 'id': new_client.id})
            case 'DELETE':
                client_id = request.args.get('id')
                client = db.query(Clients).filter(Clients.id == client_id).first()
                if client:
                    db.delete(client)
                    db.commit()
                    return jsonify({'message': 'Client deleted'})
                return jsonify({'error': 'Client not found'}), 404

@app.route('/api/clients/<int:client_id>', methods=['GET','PUT'])
def clients_api_id(client_id):
    session_user = UserSession()
    if not session_user.user_id:
        return jsonify({'error': 'Требуется вход'})

    with DB_Session() as db:
        match request.method:
            case 'GET':
                client = db.query(Clients).filter(Clients.id == client_id).first()
                if client:
                    return jsonify({'id': client.id, 'first_name': client.first_name, 'last_name': client.last_name, 'e_mail': client.e_mail, 'phone_number': client.phone_number})
            case 'PUT':
                client = db.query(Clients).filter(Clients.id == client_id).first()
                if client:
                    data = request.json
                    client.first_name = data.get('first_name', client.first_name)
                    client.last_name = data.get('last_name', client.last_name)
                    client.e_mail = data.get('e_mail', client.e_mail)
                    client.phone_number = data.get('phone_number', client.phone_number)
                    db.commit()
                    return jsonify({'message': 'Client updated'})

        return jsonify({'error': 'Client not found'}), 404

@app.route('/api/drivers', methods=['GET', 'POST'])
def drivers_api():
    session_user = UserSession()
    if not session_user.user_id:
        return jsonify({'error': 'Требуется вход'})

    with DB_Session() as db:
        match request.method:
            case 'GET':
                drivers = db.query(Drivers).all()
                return jsonify([{'id': d.id, 'first_name': d.first_name, 'last_name': d.last_name, 'phone': d.phone} for d in drivers])
            case 'POST':
                data = request.json
                new_driver = Drivers(first_name=data['first_name'], last_name=data['last_name'], phone=data.get('phone'))
                db.add(new_driver)
                db.commit()
                return jsonify({'message': 'Driver added', 'id': new_driver.id})
        return jsonify({'error': 'Driver not found'}), 404

@app.route('/api/drivers/<int:driver_id>', methods=['GET', 'PUT', 'DELETE'])
def drivers_api_id(driver_id):
    session_user = UserSession()
    if not session_user.user_id:
        return jsonify({'error': 'Требуется вход'})

    with DB_Session() as db:
        match request.method:
            case 'GET':
                driver = db.query(Drivers).filter(Drivers.id == driver_id).first()
                if driver:
                    return jsonify({'id': driver.id, 'first_name': driver.first_name, 'last_name': driver.last_name, 'phone': driver.phone})
            case 'PUT':
                driver = db.query(Drivers).filter(Drivers.id == driver_id).first()
                if driver:
                    data = request.json
                    driver.first_name = data.get('first_name', driver.first_name)
                    driver.last_name = data.get('last_name', driver.last_name)
                    driver.phone = data.get('phone', driver.phone)
                    db.commit()
                    return jsonify({'message': 'Driver updated'})
            case 'DELETE':
                driver = db.query(Drivers).filter(Drivers.id == driver_id).first()
                if driver:
                    db.delete(driver)
                    db.commit()
                    return jsonify({'message': 'Driver deleted'})
        return jsonify({'error': 'Driver not found'}), 404

@app.route('/api/vehicles', methods=['GET', 'POST'])
def vehicles_api():
    session_user = UserSession()
    if not session_user.user_id:
        return jsonify({'error': 'Требуется вход'})

    with DB_Session() as db:
        match request.method:
            case 'GET':
                vehicles = db.query(Vehicles).all()
                return jsonify([{'id': v.id, 'plate_number': v.plate_number,'model': v.model, 'type': v.type, 'capacity': v.capacity} for v in vehicles])
            case 'POST':
                data = request.json
                new_vehicle = Vehicles(plate_number=data['plate_number'],model=data.get('model') ,type=data.get('type'), capacity=data.get('capacity'))
                db.add(new_vehicle)
                db.commit()
                return jsonify({'message': 'Vehicle added', 'id': new_vehicle.id})
        return jsonify({'error': 'Vehicle not found'}), 404

@app.route('/api/vehicles/<int:vehicle_id>', methods=['GET', 'PUT', 'DELETE'])
def vehicles_api_id(vehicle_id):
    session_user = UserSession()
    if not session_user.user_id:
        return jsonify({'error': 'Требуется вход'})

    with DB_Session() as db:
        match request.method:
            case 'GET':
                vehicle = db.query(Vehicles).filter(Vehicles.id == vehicle_id).first()
                if vehicle:
                    return jsonify({'id': vehicle.id, 'plate_number': vehicle.plate_number,'model': vehicle.model, 'type': vehicle.type, 'capacity': vehicle.capacity})
            case 'PUT':
                vehicle = db.query(Vehicles).filter(Vehicles.id == vehicle_id).first()
                if vehicle:
                    data = request.json
                    vehicle.plate_number = data.get('plate_number', vehicle.plate_number)
                    vehicle.model = data.get('model', vehicle.model)
                    vehicle.type = data.get('type', vehicle.type)
                    vehicle.capacity = data.get('capacity', vehicle.capacity)
                    db.commit()
                    return jsonify({'message': 'Vehicle updated'})
            case 'DELETE':
                vehicle = db.query(Vehicles).filter(Vehicles.id == vehicle_id).first()
                if vehicle:
                    db.delete(vehicle)
                    db.commit()
                    return jsonify({'message': 'Vehicle deleted'})
        return jsonify({'error': 'Vehicle not found'}), 404

@app.route('/api/warehouses', methods=['GET', 'POST'])
def warehouses_api():
    session_user = UserSession()
    if not session_user.user_id:
        return jsonify({'error': 'Требуется вход'})

    with DB_Session() as db:
        match request.method:
            case 'GET':
                warehouses = db.query(Warehouses).all()
                return jsonify([{'id': w.id, 'name': w.name, 'address': w.address, 'capacity': w.capacity} for w in warehouses])
            case 'POST':
                data = request.json
                new_warehouse = Warehouses(name=data['name'], address=data['address'], capacity=data['capacity'])
                db.add(new_warehouse)
                db.commit()
                return jsonify({'message': 'Warehouse added', 'id': new_warehouse.id})
        return jsonify({'error': 'Warehouse not found'}), 404

@app.route('/api/warehouses/<int:warehouse_id>', methods=['GET', 'PUT', 'DELETE'])
def warehouses_api_id(warehouse_id):
    session_user = UserSession()
    if not session_user.user_id:
        return jsonify({'error': 'Требуется вход'})

    with DB_Session() as db:
        match request.method:
            case 'GET':
                warehouse = db.query(Warehouses).filter(Warehouses.id == warehouse_id).first()
                if warehouse:
                    return jsonify({'id': warehouse.id, 'name': warehouse.name, 'address': warehouse.address, 'capacity': warehouse.capacity})
            case 'PUT':
                warehouse = db.query(Warehouses).filter(Warehouses.id == warehouse_id).first()
                if warehouse:
                    data = request.json
                    warehouse.name = data.get('name', warehouse.name)
                    warehouse.address = data.get('address', warehouse.address)
                    warehouse.capacity = data.get('capacity', warehouse.capacity)
                    db.commit()
                    return jsonify({'message': 'Warehouse updated'})
            case 'DELETE':
                warehouse = db.query(Warehouses).filter(Warehouses.id == warehouse_id).first()
                if warehouse:
                    db.delete(warehouse)
                    db.commit()
                    return jsonify({'message': 'Warehouse deleted'})
        return jsonify({'error': 'Warehouse not found'}), 404

@app.route('/api/orders', methods=['GET', 'POST'])
def orders_api():
    session_user = UserSession()
    if not session_user.user_id:
        return jsonify({'error': 'Требуется вход'})

    with DB_Session() as db:
        match request.method:
            case 'GET':
                orders = db.query(Orders).all()
                return jsonify([{'id': o.id, 'client_id': o.client_id, 'order_date': o.order_date.isoformat(), 'status': o.status, 'user': o.user_id} for o in orders])
            case 'POST':
                data = request.json
                new_order = Orders(client_id=data['client_id'], order_date=data['order_date'], status=data.get('status'), user_id=session_user.user_id)
                db.add(new_order)
                db.commit()
                return jsonify({'message': 'Order added', 'id': new_order.id})
        return jsonify({'error': 'Order not found'}), 404

@app.route('/api/orders/<int:order_id>', methods=['GET', 'PUT', 'DELETE'])
def orders_api_id(order_id):
    session_user = UserSession()
    if not session_user.user_id:
        return jsonify({'error': 'Требуется вход'})

    with DB_Session() as db:
        match request.method:
            case 'GET':
                order = db.query(Orders).filter(Orders.id == order_id).first()
                if order:
                    return jsonify({'id': order.id, 'client_id': order.client_id, 'order_date': order.order_date.isoformat(), 'status': order.status, 'user': order.user_id})
            case 'PUT':
                order = db.query(Orders).filter(Orders.id == order_id).first()
                if order:
                    data = request.json
                    order.client_id = data.get('client_id', order.client_id)
                    order.order_date = data.get('order_date', order.order_date)
                    order.status = data.get('status', order.status)
                    db.commit()
                    return jsonify({'message': 'Order updated'})
            case 'DELETE':
                order_id = request.args.get('id')
                order = db.query(Orders).filter(Orders.id == order_id).first()
                if order:
                    db.delete(order)
                    db.commit()
                    return jsonify({'message': 'Order deleted'})
        return jsonify({'error': 'Order not found'}), 404


@app.route('/api/warehouses_orders/<int:order_id>', methods=['GET', 'POST', 'DELETE'])
def warehouses_orders_api_id(order_id):
    session_user = UserSession()
    if not session_user.user_id:
        return jsonify({'error': 'Требуется авторизация'}), 401

    with DB_Session() as db:
        match request.method:
            case 'GET':
                order = db.query(Orders).filter(Orders.id == order_id).first()
                if not order:
                    return jsonify({'error': 'Заказ не найден'}), 404

                warehouses = (
                    db.query(Warehouses)
                    .join(t_warehouses_orders, t_warehouses_orders.c.warehouses_id == Warehouses.id)
                    .filter(t_warehouses_orders.c.orders_id == order_id)
                    .all()
                )

                return jsonify([
                    {
                        'id': w.id,
                        'name': w.name,
                        'address': w.address,
                        'capacity': w.capacity
                    } for w in warehouses
                ]), 200
            case 'POST':
                data = request.get_json(silent=True) or {}
                warehouse_id = data.get('warehouse_id')
                if not warehouse_id:
                    return jsonify({'error': 'Требуется ID склада'}), 400

                order = db.query(Orders).filter(Orders.id == order_id).first()
                warehouse = db.query(Warehouses).filter(Warehouses.id == warehouse_id).first()

                if not order:
                    return jsonify({'error': 'Заказ не найден'}), 404
                if not warehouse:
                    return jsonify({'error': 'Склад не найден'}), 404

                existing_relation = db.execute(
                    t_warehouses_orders.select().where(
                        t_warehouses_orders.c.orders_id == order_id,
                        t_warehouses_orders.c.warehouses_id == warehouse_id
                    )
                ).first()

                if existing_relation:
                    return jsonify({'error': 'Связь уже существует'}), 400

                try:
                    db.execute(
                        t_warehouses_orders.insert().values(
                            orders_id=order_id,
                            warehouses_id=warehouse_id
                        )
                    )
                    db.commit()
                except Exception as e:
                    db.rollback()

                    if 'переполнен' in str(e):
                        return jsonify({'error': f'Невозможно добавить заказ. Склад №{warehouse_id} переполнен.'}), 400

                    return jsonify({'error': 'Внутренняя ошибка базы данных'}), 500

                return jsonify({'message': 'Склад добавлен к заказу'}), 201
            case 'DELETE':
                data = request.get_json(silent=True) or {}
                warehouse_id = data.get('warehouse_id')
                if not warehouse_id:
                    return jsonify({'error': 'Требуется ID склада'}), 400
                relation = db.execute(
                    t_warehouses_orders.select().where(
                        t_warehouses_orders.c.orders_id == order_id,
                        t_warehouses_orders.c.warehouses_id == warehouse_id
                    )
                ).first()

                if not relation:
                    return jsonify({'error': 'Связь не найдена'}), 404
                db.execute(
                    t_warehouses_orders.delete().where(
                        t_warehouses_orders.c.orders_id == order_id,
                        t_warehouses_orders.c.warehouses_id == warehouse_id
                    )
                )
                db.commit()
                return jsonify({'message': 'Склад удалён из заказа'}), 200

        return jsonify({'error': 'Метод не разрешен'}), 405

@app.route('/api/routes', methods=['GET', 'POST'])
def routes_api():
    session_user = UserSession()
    if not session_user.user_id:
        return jsonify({'error': 'Требуется вход'})

    with DB_Session() as db:
        match request.method:
            case 'GET':
                routes = db.query(Routes).all()
                return jsonify([{'id': r.id, 'order_id': r.order_id, 'vehicle_id': r.vehicle_id, 'driver_id': r.driver_id, 'departure_date': r.departure_date, 'arrival_date': r.arrival_date} for r in routes])
            case 'POST':
                data = request.json
                new_route = Routes(order_id=data['order_id'], vehicle_id=data['vehicle_id'], driver_id=data['driver_id'], departure_date=data.get('departure_date'), arrival_date=data.get('arrival_date'))
                db.add(new_route)
                db.commit()
                return jsonify({'message': 'Route added', 'id': new_route.id})
        return jsonify({'error': 'Route not found'}), 404

@app.route('/api/routes/<int:route_id>', methods=['GET', 'PUT', 'DELETE'])
def routes_api_id(route_id):
    session_user = UserSession()
    if not session_user.user_id:
        return jsonify({'error': 'Требуется вход'})

    with DB_Session() as db:
        match request.method:
            case 'GET':
                route = db.query(Routes).filter(Routes.id == route_id).first()
                if route:
                    return jsonify({'id': route.id, 'order_id': route.order_id, 'vehicle_id': route.vehicle_id, 'driver_id': route.driver_id, 'departure_date': route.departure_date, 'arrival_date': route.arrival_date})
            case 'PUT':
                route = db.query(Routes).filter(Routes.id == route_id).first()
                if route:
                    data = request.json
                    route.order_id = data.get('order_id', route.order_id)
                    route.vehicle_id = data.get('vehicle_id', route.vehicle_id)
                    route.driver_id = data.get('driver_id', route.driver_id)
                    route.departure_date = data.get('departure_date', route.departure_date)
                    route.arrival_date = data.get('arrival_date', route.arrival_date)
                    db.commit()
                    return jsonify({'message': 'Route updated'})
            case 'DELETE':
                route = db.query(Routes).filter(Routes.id == route_id).first()
                if route:
                    db.delete(route)
                    db.commit()
                    return jsonify({'message': 'Route deleted'})
        return jsonify({'error': 'Route not found'}), 404

@app.route('/api/admin/users', methods=['GET'])
def admin_users_api():
    session_user = UserSession()
    if session_user.login and session_user.acc_type == 'Admin':
        with DB_Session() as db:
            users = db.query(Users).filter(Users.id != session_user.user_id).all()
            users_tup = [{'id': row.id, 'login': row.login, 'e_mail': row.e_mail, 'account_type': row.account_type} for row in users]
        return jsonify(users_tup)
    else:
        return jsonify({'error': 'Требуется вход или права администратора'})

@app.route('/api/admin/users/<int:users_id>', methods=['DELETE', 'PUT'])
def admin_users_api_id(users_id):
    session_user = UserSession()
    if session_user.login and session_user.acc_type == 'Admin':
        match request.method:
            case 'PUT':
                data = request.json
                account_type = data.get('account_type')
                reset_password = data.get('reset_password')
                with DB_Session() as db:
                    user = db.query(Users).filter(Users.id == users_id).first()
                    if user:
                        if reset_password:
                            alphabet = string.ascii_letters + string.digits
                            new_password = ''.join(secrets.choice(alphabet) for i in range(8))
                            hashed_password = generate_password_hash(new_password, method="pbkdf2:sha256", salt_length=16)
                            user.password = hashed_password
                            db.commit()
                            return jsonify({'success': True, 'message': 'Пароль успешно сброшен, новый пароль', 'new_password': new_password})
                        elif not reset_password:
                            user = db.query(Users).filter(Users.id == users_id).first()
                            if user:
                                user.account_type = account_type
                                db.commit()
                                return jsonify({'success': True, 'message': 'Тип аккаунта успешно изменен'})
            case 'DELETE':
                with DB_Session() as db:
                    record = db.query(Users).filter(Users.id == users_id).first()
                    if record and record.id != session_user.user_id:
                        db.delete(record)
                        db.commit()
                        return jsonify({'success': True, 'message': 'Пользователь успешно удален'})
                    else:
                        return jsonify({'success': False, 'message': 'Пользователь не найден или попытка удалить текущего пользователя'})
    else:
        return jsonify({'error': 'Требуется вход или права администратора'})


@app.route('/api/admin/backup')
def download_backup():
    session_user = UserSession()
    if session_user.login and session_user.acc_type == 'Admin':
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        temp_backup_path = f"/tmp/db_backup_{timestamp}.sql"

        try:
            env = os.environ.copy()
            env["PGPASSWORD"] = "1234"
            subprocess.run(
                ["pg_dump", "-U", "admin", "-h", "192.168.56.103", "logistics", "-f", temp_backup_path],
                env=env,
                check=True
            )

            @after_this_request
            def remove_file(response):
                try:
                    if os.path.exists(temp_backup_path):
                        os.remove(temp_backup_path)
                except Exception as error:
                    app.logger.error(f"Error deleting temporary backup file: {error}")
                return response

            return send_file(
                temp_backup_path,
                as_attachment=True,
                download_name=f"db_backup_{timestamp}.sql"
            )

        except subprocess.CalledProcessError:
            abort(500, description="Database backup generation failed.")
    return None


if __name__ == '__main__':
    Base.metadata.create_all(engine)
    app.run(debug=True)

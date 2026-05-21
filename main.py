# Задание на производственную практику: разработать веб-приложение для
# автоматизации бизнес-процессов логистической компании
# Среда разработки: PyCharm
# Производственная практика
# Название: Разработка веб-приложения
# Разработал: Федюнин Иван Владиславович ТБД-72
# Язык: Python

import string
import secrets
from functools import wraps
from flask import Flask, request, jsonify, make_response, redirect, url_for, render_template
from sqlalchemy import create_engine, func, or_, and_, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import InternalError
from models import Base, Users, Sessions, Clients, Drivers, Vehicles, Warehouses, Orders, Routes, t_warehouses_orders

app = Flask(__name__)

# Настройки подключения к PostgreSQL
engine = create_engine('postgresql://admin:1234@192.168.57.7:5432/logistics', echo=False)
DB_Session = sessionmaker(bind=engine)


class UserSession:
    """Управление контекстом сессии пользователя на основе данных из СУБД."""
    def __init__(self):
        self.session_token = request.cookies.get('session_token')
        self.user_id = False
        self.login = False
        self.acc_type = False

        if self.session_token:
            with DB_Session() as db:
                result = db.execute(
                    text("SELECT user_id, user_login, account_type FROM logistics.validate_session(:token)"),
                    {"token": self.session_token}
                ).first()

                if result:
                    self.user_id = result.user_id
                    self.login = result.user_login
                    self.acc_type = result.account_type  # Хранит одну из ролей: Admin, Manager, Dispatcher, Driver_Warehouse
                else:
                    self.session_token = None


def roles_required(*allowed_roles):
    """Декоратор для декларативного разграничения прав доступа на веб-ресурсах."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            session_user = UserSession()
            if not session_user.login:
                if request.is_json or request.path.startswith('/api/'):
                    return jsonify({'error': 'Требуется аутентификация в системе'}), 401
                return render_template('error.html', user=session_user, page_name='Ошибка доступа', message='Требуется вход в систему')

            if session_user.acc_type not in allowed_roles:
                if request.is_json or request.path.startswith('/api/'):
                    return jsonify({'error': 'Отказ в доступе: недостаточно прав'}), 403
                return render_template('error.html', user=session_user, page_name='Ошибка доступа', message='Недостаточно прав для просмотра данной секции')

            return f(*args, **kwargs)
        return decorated_function
    return decorator


class LoginUsr:
    def __init__(self, e_mail, passwd):
        self.email_str = e_mail
        self.password_str = passwd

    def login_fun(self):
        with DB_Session() as db:
            user = db.execute(
                text("SELECT user_id, user_login, account_type FROM logistics.login_user(:email, :password)"),
                {"email": self.email_str, "password": self.password_str}
            ).first()

            if user:
                token_var = secrets.token_hex(24)
                db.execute(
                    text("CALL logistics.create_session(:user_id, :token, :ip)"),
                    {"user_id": user.user_id, "token": token_var, "ip": request.remote_addr}
                )
                db.commit()

                response = make_response(jsonify({
                    'message': 'Вы успешно зашли в аккаунт',
                    'login': user.user_login,
                    'account_type': user.account_type,
                    'success': True
                }))
                response.set_cookie('session_token', token_var, max_age=60 * 45)
                return response

        return jsonify({'message': 'Неверное имя пользователя или пароль', 'success': False})


class RegisterUsr:
    def __init__(self, login_st, email, passwd, account_type='Manager'):
        self.login_str = login_st
        self.e_mail_str = email
        self.password_str = passwd
        self.account_type = account_type

    def reg_fun(self):
        try:
            with DB_Session() as db:
                db.execute(
                    text("CALL logistics.register_user(:login, :email, :password, :role)"),
                    {
                        "login": self.login_str,
                        "email": self.e_mail_str,
                        "password": self.password_str,
                        "role": self.account_type
                    }
                )
                db.commit()
            return jsonify({'message': 'Пользователь успешно создан', 'success': True})

        except InternalError as e:
            error_msg = str(e.orig)
            if 'PASSWORD_TOO_SHORT' in error_msg:
                msg = 'Пароль слишком короткий (минимум 8 символов)'
            elif 'LOGIN_TAKEN' in error_msg:
                msg = 'Пользователь с таким логином уже существует'
            elif 'EMAIL_TAKEN' in error_msg:
                msg = 'Пользователь с таким E-mail уже существует'
            else:
                msg = 'Ошибка валидации роли или структуры данных'
            return jsonify({'message': msg, 'success': False})


# --- Маршруты авторизации и общих страниц ---

@app.route('/')
def index():
    session_user = UserSession()
    return render_template('index.html', page_name='Главная страница', user=session_user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    session_user = UserSession()
    if request.method == 'POST':
        data = request.json
        login_obj = LoginUsr(data.get('e_mail'), data.get('password'))
        return login_obj.login_fun()
    return render_template('login.html', page_name='Вход', user=session_user)

@app.route('/register', methods=['GET', 'POST'])
def register():
    session_user = UserSession()
    if request.method == 'POST':
        data = request.json
        reg_obj = RegisterUsr(data.get('login'), data.get('e_mail'), data.get('password'), data.get('account_type', 'Manager'))
        return reg_obj.reg_fun()
    return render_template('regist.html', page_name='Регистрация', user=session_user)

@app.route('/logout')
def logout():
    token_var = request.cookies.get('session_token')
    if token_var:
        with DB_Session() as db:
            db.execute(text("CALL logistics.logout_user(:token)"), {"token": token_var})
            db.commit()
    response = make_response(redirect(url_for('index')))
    response.set_cookie('session_token', '', expires=0)
    return response

# Панели интерфейсов, разграниченные по ролям согласно матрице
@app.route('/admin_panel')
@roles_required('Admin')
def admin_panel():
    session_user = UserSession()
    return render_template('admin.html', user=session_user, page_name='Админ-панель')

@app.route('/dashboard', methods=['GET'])
@roles_required('Admin', 'Manager', 'Dispatcher', 'Driver_Warehouse')
def dashboard():
    session_user = UserSession()
    return render_template('dashboard.html', page_name='Главный интерфейс', user=session_user)


# --- REST API: Разграничение прав доступа согласно предоставленной таблице ---

@app.route('/api/admin', methods=['GET'])
@roles_required('Admin')
def admin_api():
    with DB_Session() as db:
        users_count = db.query(Users).count()
        orders_count = db.query(Orders).count()
        valid_session = db.query(Sessions).filter(Sessions.expiration_date > func.current_timestamp()).count()
        users_sessions = db.query(Users.login, func.count(Sessions.id)).group_by(Users.login).join(Sessions).all()
        users_sessions_tup = [{'user_login': ul, 'sessions_count': sc} for ul, sc in users_sessions]
        return jsonify({'users_count': users_count, 'orders_count': orders_count, 'valid_session': valid_session, 'sessions_per_user': users_sessions_tup})


# Справочники (Транспорт, Водители): Доступ имеют Администратор и Диспетчер
@app.route('/api/drivers', methods=['GET', 'POST'])
@roles_required('Admin', 'Dispatcher')
def drivers_api():
    with DB_Session() as db:
        if request.method == 'GET':
            drivers = db.query(Drivers).all()
            return jsonify([{'id': d.id, 'first_name': d.first_name, 'last_name': d.last_name, 'phone': d.phone} for d in drivers])

        data = request.json
        new_driver = Drivers(first_name=data['first_name'], last_name=data['last_name'], phone=data.get('phone'))
        db.add(new_driver)
        db.commit()
        return jsonify({'message': 'Водитель успешно добавлен', 'id': new_driver.id}), 201

@app.route('/api/drivers/<int:driver_id>', methods=['GET', 'PUT', 'DELETE'])
@roles_required('Admin', 'Dispatcher')
def drivers_api_id(driver_id):
    with DB_Session() as db:
        driver = db.query(Drivers).filter(Drivers.id == driver_id).first()
        if not driver:
            return jsonify({'error': 'Водитель не найден'}), 404

        if request.method == 'GET':
            return jsonify({'id': driver.id, 'first_name': driver.first_name, 'last_name': driver.last_name, 'phone': driver.phone})
        elif request.method == 'PUT':
            data = request.json
            driver.first_name = data.get('first_name', driver.first_name)
            driver.last_name = data.get('last_name', driver.last_name)
            driver.phone = data.get('phone', driver.phone)
            db.commit()
            return jsonify({'message': 'Данные водителя обновлены'})
        elif request.method == 'DELETE':
            db.delete(driver)
            db.commit()
            return jsonify({'message': 'Запись водителя удалена'})


@app.route('/api/vehicles', methods=['GET', 'POST'])
@roles_required('Admin', 'Dispatcher')
def vehicles_api():
    with DB_Session() as db:
        if request.method == 'GET':
            vehicles = db.query(Vehicles).all()
            return jsonify([{'id': v.id, 'plate_number': v.plate_number, 'model': v.model, 'type': v.type, 'capacity': float(v.capacity) if v.capacity else 0.0} for v in vehicles])

        data = request.json
        new_vehicle = Vehicles(plate_number=data['plate_number'], model=data.get('model'), type=data.get('type'), capacity=data.get('capacity'))
        db.add(new_vehicle)
        db.commit()
        return jsonify({'message': 'Транспортное средство добавлено', 'id': new_vehicle.id}), 201

@app.route('/api/vehicles/<int:vehicle_id>', methods=['GET', 'PUT', 'DELETE'])
@roles_required('Admin', 'Dispatcher')
def vehicles_api_id(vehicle_id):
    with DB_Session() as db:
        vehicle = db.query(Vehicles).filter(Vehicles.id == vehicle_id).first()
        if not vehicle:
            return jsonify({'error': 'Транспортное средство не найдено'}), 404

        if request.method == 'GET':
            return jsonify({'id': vehicle.id, 'plate_number': vehicle.plate_number, 'model': vehicle.model, 'type': vehicle.type, 'capacity': float(vehicle.capacity) if vehicle.capacity else 0.0})
        elif request.method == 'PUT':
            data = request.json
            vehicle.plate_number = data.get('plate_number', vehicle.plate_number)
            vehicle.model = data.get('model', vehicle.model)
            vehicle.type = data.get('type', vehicle.type)
            vehicle.capacity = data.get('capacity', vehicle.capacity)
            db.commit()
            return jsonify({'message': 'Данные ТС обновлены'})
        elif request.method == 'DELETE':
            db.delete(vehicle)
            db.commit()
            return jsonify({'message': 'Транспортное средство удалено'})


# Заказы (Создание и редактирование): Доступ имеют Администратор, Менеджер, Диспетчер
@app.route('/api/orders', methods=['GET', 'POST'])
@roles_required('Admin', 'Manager', 'Dispatcher')
def orders_api():
    session_user = UserSession()
    with DB_Session() as db:
        if request.method == 'GET':
            orders = db.query(Orders).all()
            return jsonify([{'id': o.id, 'client_id': o.client_id, 'order_date': o.order_date.isoformat(), 'status': o.status, 'user': o.user_id} for o in orders])

        data = request.json
        new_order = Orders(client_id=data['client_id'], order_date=data['order_date'], status=data.get('status'), user_id=session_user.user_id)
        db.add(new_order)
        db.commit()
        return jsonify({'message': 'Заказ успешно сформирован', 'id': new_order.id}), 201

@app.route('/api/orders/<int:order_id>', methods=['GET', 'PUT', 'DELETE'])
@roles_required('Admin', 'Manager', 'Dispatcher')
def orders_api_id(order_id):
    with DB_Session() as db:
        order = db.query(Orders).filter(Orders.id == order_id).first()
        if not order:
            return jsonify({'error': 'Заказ не найден'}), 404

        if request.method == 'GET':
            return jsonify({'id': order.id, 'client_id': order.client_id, 'order_date': order.order_date.isoformat(), 'status': order.status, 'user': order.user_id})
        elif request.method == 'PUT':
            data = request.json
            order.client_id = data.get('client_id', order.client_id)
            order.order_date = data.get('order_date', order.order_date)
            order.status = data.get('status', order.status)
            db.commit()
            return jsonify({'message': 'Данные заказа обновлены'})
        elif request.method == 'DELETE':
            # Удаление разрешено только Администратору
            session_user = UserSession()
            if session_user.acc_type != 'Admin':
                return jsonify({'error': 'Полное удаление данных доступно только Администратору'}), 403
            db.delete(order)
            db.commit()
            return jsonify({'message': 'Заказ полностью удален из СУБД'})


# Клиенты и склады (Просмотр доступен всем ролям, изменения — согласно иерархии)
@app.route('/api/clients', methods=['GET', 'POST', 'DELETE'])
@roles_required('Admin', 'Manager', 'Dispatcher', 'Driver_Warehouse')
def clients_api():
    session_user = UserSession()
    with DB_Session() as db:
        if request.method == 'GET':
            clients = db.query(Clients).all()
            return jsonify([{'id': c.id, 'first_name': c.first_name, 'last_name': c.last_name, 'e_mail': c.e_mail, 'phone_number': c.phone_number} for c in clients])

        if session_user.acc_type not in ['Admin', 'Manager', 'Dispatcher']:
            return jsonify({'error': 'Недостаточно прав для модификации справочника клиентов'}), 403

        if request.method == 'POST':
            data = request.json
            new_client = Clients(first_name=data['first_name'], last_name=data['last_name'], e_mail=data['e_mail'], phone_number=data['phone_number'])
            db.add(new_client)
            db.commit()
            return jsonify({'message': 'Клиент добавлен', 'id': new_client.id}), 201

        if request.method == 'DELETE':
            if session_user.acc_type != 'Admin':
                return jsonify({'error': 'Удаление клиентов разрешено только Администратору'}), 403
            client_id = request.args.get('id')
            client = db.query(Clients).filter(Clients.id == client_id).first()
            if client:
                db.delete(client)
                db.commit()
                return jsonify({'message': 'Запись клиента удалена'})
            return jsonify({'error': 'Клиент не найден'}), 404


@app.route('/api/warehouses', methods=['GET', 'POST'])
@roles_required('Admin', 'Manager', 'Dispatcher', 'Driver_Warehouse')
def warehouses_api():
    session_user = UserSession()
    with DB_Session() as db:
        if request.method == 'GET':
            warehouses = db.query(Warehouses).all()
            return jsonify([{'id': w.id, 'name': w.name, 'address': w.address, 'capacity': w.capacity} for w in warehouses])

        if session_user.acc_type not in ['Admin', 'Dispatcher']:
            return jsonify({'error': 'Управление справочником складов доступно Администраторам и Диспетчерам'}), 403

        data = request.json
        new_warehouse = Warehouses(name=data['name'], address=data['address'], capacity=data['capacity'])
        db.add(new_warehouse)
        db.commit()
        return jsonify({'message': 'Склад успешно зарегистрирован', 'id': new_warehouse.id}), 201


# Маршруты доставки
@app.route('/api/routes', methods=['GET', 'POST'])
@roles_required('Admin', 'Manager', 'Dispatcher', 'Driver_Warehouse')
def routes_api():
    session_user = UserSession()
    with DB_Session() as db:
        if request.method == 'GET':
            routes = db.query(Routes).all()
            return jsonify([{'id': r.id, 'order_id': r.order_id, 'vehicle_id': r.vehicle_id, 'driver_id': r.driver_id, 'departure_date': r.departure_date.isoformat() if r.departure_date else None, 'arrival_date': r.arrival_date.isoformat() if r.arrival_date else None} for r in routes])

        if session_user.acc_type not in ['Admin', 'Dispatcher']:
            return jsonify({'error': 'Назначать маршруты могут только Диспетчеры и Администраторы'}), 403

        data = request.json
        new_route = Routes(order_id=data['order_id'], vehicle_id=data['vehicle_id'], driver_id=data['driver_id'], departure_date=data.get('departure_date'), arrival_date=data.get('arrival_date'))
        db.add(new_route)
        db.commit()
        return jsonify({'message': 'Маршрут успешно назначен', 'id': new_route.id}), 201


# Системное администрирование пользователей (Только для роли Admin)
@app.route('/api/admin/users', methods=['GET'])
@roles_required('Admin')
def admin_users_api():
    with DB_Session() as db:
        users = db.query(Users).all()
        return jsonify([{'id': r.id, 'login': r.login, 'e_mail': r.e_mail, 'account_type': r.account_type} for r in users])

@app.route('/api/admin/users/<int:users_id>', methods=['DELETE', 'PUT'])
@roles_required('Admin')
def admin_users_api_id(users_id):
    session_user = UserSession()
    with DB_Session() as db:
        user = db.query(Users).filter(Users.id == users_id).first()
        if not user:
            return jsonify({'success': False, 'message': 'Пользователь не найден'}), 404

        if request.method == 'PUT':
            data = request.json
            account_type = data.get('account_type')
            reset_password = data.get('reset_password')

            if reset_password:
                alphabet = string.ascii_letters + string.digits
                new_password = ''.join(secrets.choice(alphabet) for _ in range(8))
                db.execute(
                    text("UPDATE logistics.Users SET password_hash = crypt(:passwd, gen_salt('bf', 12)) WHERE id = :id"),
                    {"passwd": new_password, "id": users_id}
                )
                db.commit()
                return jsonify({'success': True, 'message': 'Пароль успешно сброшен', 'new_password': new_password})

            if account_type in ['Admin', 'Manager', 'Dispatcher', 'Driver_Warehouse']:
                user.account_type = account_type
                db.commit()
                return jsonify({'success': True, 'message': 'Роль пользователя изменена'})
            return jsonify({'success': False, 'message': 'Неверный тип роли'}), 400

        if request.method == 'DELETE':
            if user.id == session_user.user_id:
                return jsonify({'success': False, 'message': 'Нельзя удалить собственный системный аккаунт'}), 400
            db.delete(user)
            db.commit()
            return jsonify({'success': True, 'message': 'Аккаунт пользователя полностью удален'})


if __name__ == '__main__':
    Base.metadata.create_all(engine)
    app.run(debug=True)

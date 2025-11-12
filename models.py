from typing import List

from sqlalchemy import CheckConstraint, Column, Date, DateTime, ForeignKeyConstraint, Integer, Numeric, PrimaryKeyConstraint, String, Table, Text, UniqueConstraint, text
from sqlalchemy.orm import Mapped, declarative_base, mapped_column, relationship
from sqlalchemy.orm.base import Mapped

Base = declarative_base()
metadata = Base.metadata


class Clients(Base):
    __tablename__ = 'clients'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='clients_pkey'),
    )

    id = mapped_column(Integer)
    first_name = mapped_column(String(100), nullable=False)
    last_name = mapped_column(String(100), nullable=False)
    e_mail = mapped_column(String(100), nullable=False)
    phone_number = mapped_column(String(100), nullable=False)

    orders: Mapped[List['Orders']] = relationship('Orders', uselist=True, back_populates='client')


class Drivers(Base):
    __tablename__ = 'drivers'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='drivers_pkey'),
    )

    id = mapped_column(Integer)
    first_name = mapped_column(String(100), nullable=False)
    last_name = mapped_column(String(100), nullable=False)
    phone = mapped_column(String(20))

    routes: Mapped[List['Routes']] = relationship('Routes', uselist=True, back_populates='driver')


class Users(Base):
    __tablename__ = 'users'
    __table_args__ = (
        CheckConstraint("account_type::text = ANY (ARRAY['User'::character varying, 'Admin'::character varying]::text[])", name='users_account_type_check'),
        PrimaryKeyConstraint('id', name='users_pkey'),
        UniqueConstraint('e_mail', name='users_e_mail_key'),
        UniqueConstraint('login', name='users_login_key')
    )

    id = mapped_column(Integer)
    login = mapped_column(String(20), nullable=False)
    e_mail = mapped_column(String(30), nullable=False)
    password = mapped_column(String(255), nullable=False)
    account_type = mapped_column(String(10), server_default=text("'User'::character varying"))

    orders: Mapped[List['Orders']] = relationship('Orders', uselist=True, back_populates='user')
    sessions: Mapped[List['Sessions']] = relationship('Sessions', uselist=True, back_populates='user')


class Vehicles(Base):
    __tablename__ = 'vehicles'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='vehicles_pkey'),
        UniqueConstraint('plate_number', name='vehicles_plate_number_key')
    )

    id = mapped_column(Integer)
    plate_number = mapped_column(String(20), nullable=False)
    type = mapped_column(String(50))
    model = mapped_column(String(50))
    capacity = mapped_column(Numeric(10, 2))

    routes: Mapped[List['Routes']] = relationship('Routes', uselist=True, back_populates='vehicle')


class Warehouses(Base):
    __tablename__ = 'warehouses'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='warehouses_pkey'),
    )

    id = mapped_column(Integer)
    name = mapped_column(String(100), nullable=False)
    address = mapped_column(Text, nullable=False)
    capacity = mapped_column(Integer, nullable=False)

    orders: Mapped['Orders'] = relationship('Orders', secondary='warehouses_orders', back_populates='warehouses')


class Orders(Base):
    __tablename__ = 'orders'
    __table_args__ = (
        ForeignKeyConstraint(['client_id'], ['clients.id'], name='orders_client_id_fkey'),
        ForeignKeyConstraint(['user_id'], ['users.id'], name='orders_user_id_fkey'),
        PrimaryKeyConstraint('id', name='orders_pkey')
    )

    id = mapped_column(Integer)
    client_id = mapped_column(Integer, nullable=False)
    user_id = mapped_column(Integer, nullable=False)
    order_date = mapped_column(Date, nullable=False)
    status = mapped_column(String(50))

    client: Mapped['Clients'] = relationship('Clients', back_populates='orders')
    user: Mapped['Users'] = relationship('Users', back_populates='orders')
    warehouses: Mapped['Warehouses'] = relationship('Warehouses', secondary='warehouses_orders', back_populates='orders')
    routes: Mapped[List['Routes']] = relationship('Routes', uselist=True, back_populates='order')


class Sessions(Base):
    __tablename__ = 'sessions'
    __table_args__ = (
        ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE', name='sessions_user_id_fkey'),
        PrimaryKeyConstraint('id', name='sessions_pkey'),
        UniqueConstraint('token', name='sessions_token_key')
    )

    id = mapped_column(Integer)
    user_id = mapped_column(Integer, nullable=False)
    token = mapped_column(String(255), nullable=False)
    ip_address = mapped_column(String(15), nullable=False)
    creation_time = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    expiration_date = mapped_column(DateTime, server_default=text("(CURRENT_TIMESTAMP + '00:45:00'::interval)"))

    user: Mapped['Users'] = relationship('Users', back_populates='sessions')


class Routes(Base):
    __tablename__ = 'routes'
    __table_args__ = (
        ForeignKeyConstraint(['driver_id'], ['drivers.id'], name='routes_driver_id_fkey'),
        ForeignKeyConstraint(['order_id'], ['orders.id'], name='routes_order_id_fkey'),
        ForeignKeyConstraint(['vehicle_id'], ['vehicles.id'], name='routes_vehicle_id_fkey'),
        PrimaryKeyConstraint('id', name='routes_pkey')
    )

    id = mapped_column(Integer)
    order_id = mapped_column(Integer, nullable=False)
    vehicle_id = mapped_column(Integer, nullable=False)
    driver_id = mapped_column(Integer, nullable=False)
    departure_date = mapped_column(Date)
    arrival_date = mapped_column(Date)

    driver: Mapped['Drivers'] = relationship('Drivers', back_populates='routes')
    order: Mapped['Orders'] = relationship('Orders', back_populates='routes')
    vehicle: Mapped['Vehicles'] = relationship('Vehicles', back_populates='routes')


t_warehouses_orders = Table(
    'warehouses_orders', metadata,
    Column('warehouses_id', Integer, nullable=False),
    Column('orders_id', Integer, nullable=False),
    ForeignKeyConstraint(['orders_id'], ['orders.id'], name='warehouses_orders_orders_id_fkey'),
    ForeignKeyConstraint(['warehouses_id'], ['warehouses.id'], name='warehouses_orders_warehouses_id_fkey'),
    PrimaryKeyConstraint('warehouses_id', 'orders_id', name='warehouses_orders_pkey')
)

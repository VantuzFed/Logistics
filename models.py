from typing import List

from sqlalchemy import CheckConstraint, Column, DECIMAL, Date, ForeignKeyConstraint, Index, Integer, String, TIMESTAMP, Table, Text, text
from sqlalchemy.orm import Mapped, declarative_base, mapped_column, relationship
from sqlalchemy.orm.base import Mapped

Base = declarative_base()
metadata = Base.metadata


class Clients(Base):
    __tablename__ = 'Clients'

    id = mapped_column(Integer, primary_key=True)
    first_name = mapped_column(String(100), nullable=False)
    last_name = mapped_column(String(100), nullable=False)
    e_mail = mapped_column(String(100), nullable=False)
    phone_number = mapped_column(String(100), nullable=False)

    Orders: Mapped[List['Orders']] = relationship('Orders', uselist=True, back_populates='client')


class Drivers(Base):
    __tablename__ = 'Drivers'

    id = mapped_column(Integer, primary_key=True)
    first_name = mapped_column(String(100), nullable=False)
    last_name = mapped_column(String(100), nullable=False)
    phone = mapped_column(String(20))

    Routes: Mapped[List['Routes']] = relationship('Routes', uselist=True, back_populates='driver')


class Users(Base):
    __tablename__ = 'Users'
    __table_args__ = (
        CheckConstraint("(`account_type` in (_utf8mb4'User',_utf8mb4'Admin'))", name='Users_chk_1'),
        Index('e_mail', 'e_mail', unique=True),
        Index('login', 'login', unique=True)
    )

    id = mapped_column(Integer, primary_key=True)
    login = mapped_column(String(20), nullable=False)
    e_mail = mapped_column(String(30), nullable=False)
    password = mapped_column(String(255), nullable=False)
    account_type = mapped_column(String(10), server_default=text("'User'"))

    Orders: Mapped[List['Orders']] = relationship('Orders', uselist=True, back_populates='user')
    Sessions: Mapped[List['Sessions']] = relationship('Sessions', uselist=True, back_populates='user')


class Vehicles(Base):
    __tablename__ = 'Vehicles'
    __table_args__ = (
        Index('plate_number', 'plate_number', unique=True),
    )

    id = mapped_column(Integer, primary_key=True)
    plate_number = mapped_column(String(20), nullable=False)
    type = mapped_column(String(50))
    model = mapped_column(String(50))
    capacity = mapped_column(DECIMAL(10, 2))

    Routes: Mapped[List['Routes']] = relationship('Routes', uselist=True, back_populates='vehicle')


class Warehouses(Base):
    __tablename__ = 'Warehouses'

    id = mapped_column(Integer, primary_key=True)
    name = mapped_column(String(100), nullable=False)
    address = mapped_column(Text, nullable=False)
    capacity = mapped_column(Integer, nullable=False)

    Orders: Mapped['Orders'] = relationship('Orders', secondary='Warehouses_Orders', back_populates='Warehouses_')


class Orders(Base):
    __tablename__ = 'Orders'
    __table_args__ = (
        ForeignKeyConstraint(['client_id'], ['Clients.id'], name='Orders_ibfk_1'),
        ForeignKeyConstraint(['user_id'], ['Users.id'], name='Orders_ibfk_2'),
        Index('client_id', 'client_id'),
        Index('user_id', 'user_id')
    )

    id = mapped_column(Integer, primary_key=True)
    client_id = mapped_column(Integer, nullable=False)
    user_id = mapped_column(Integer, nullable=False)
    order_date = mapped_column(Date, nullable=False)
    status = mapped_column(String(50))

    client: Mapped['Clients'] = relationship('Clients', back_populates='Orders')
    user: Mapped['Users'] = relationship('Users', back_populates='Orders')
    Warehouses_: Mapped['Warehouses'] = relationship('Warehouses', secondary='Warehouses_Orders', back_populates='Orders')
    Routes: Mapped[List['Routes']] = relationship('Routes', uselist=True, back_populates='order')


class Sessions(Base):
    __tablename__ = 'Sessions'
    __table_args__ = (
        ForeignKeyConstraint(['user_id'], ['Users.id'], ondelete='CASCADE', name='Sessions_ibfk_1'),
        Index('token', 'token', unique=True),
        Index('user_id', 'user_id')
    )

    id = mapped_column(Integer, primary_key=True)
    user_id = mapped_column(Integer, nullable=False)
    token = mapped_column(String(255), nullable=False)
    ip_address = mapped_column(String(15), nullable=False)
    creation_time = mapped_column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    expiration_date = mapped_column(TIMESTAMP, server_default=text('((now()'))

    user: Mapped['Users'] = relationship('Users', back_populates='Sessions')


class Routes(Base):
    __tablename__ = 'Routes'
    __table_args__ = (
        ForeignKeyConstraint(['driver_id'], ['Drivers.id'], name='Routes_ibfk_3'),
        ForeignKeyConstraint(['order_id'], ['Orders.id'], name='Routes_ibfk_1'),
        ForeignKeyConstraint(['vehicle_id'], ['Vehicles.id'], name='Routes_ibfk_2'),
        Index('driver_id', 'driver_id'),
        Index('order_id', 'order_id'),
        Index('vehicle_id', 'vehicle_id')
    )

    id = mapped_column(Integer, primary_key=True)
    order_id = mapped_column(Integer, nullable=False)
    vehicle_id = mapped_column(Integer, nullable=False)
    driver_id = mapped_column(Integer, nullable=False)
    departure_date = mapped_column(Date)
    arrival_date = mapped_column(Date)

    driver: Mapped['Drivers'] = relationship('Drivers', back_populates='Routes')
    order: Mapped['Orders'] = relationship('Orders', back_populates='Routes')
    vehicle: Mapped['Vehicles'] = relationship('Vehicles', back_populates='Routes')


t_Warehouses_Orders = Table(
    'Warehouses_Orders', metadata,
    Column('Warehouses_id', Integer, primary_key=True, nullable=False),
    Column('Orders_id', Integer, primary_key=True, nullable=False),
    ForeignKeyConstraint(['Orders_id'], ['Orders.id'], name='Warehouses_Orders_ibfk_2'),
    ForeignKeyConstraint(['Warehouses_id'], ['Warehouses.id'], name='Warehouses_Orders_ibfk_1'),
    Index('Orders_id', 'Orders_id')
)

DROP SCHEMA IF EXISTS logistics CASCADE;
CREATE SCHEMA IF NOT EXISTS logistics;
SET search_path TO logistics;

CREATE TABLE Clients (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    e_mail VARCHAR(100) NOT NULL,
    phone_number VARCHAR(100) NOT NULL
);

CREATE TABLE Orders (
    id SERIAL PRIMARY KEY,
    client_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    order_date DATE NOT NULL,
    status VARCHAR(50)
);

CREATE TABLE Warehouses (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    address TEXT NOT NULL,
    capacity INTEGER NOT NULL
);

CREATE TABLE Vehicles (
    id SERIAL PRIMARY KEY,
    plate_number VARCHAR(20) UNIQUE NOT NULL,
    type VARCHAR(50),
    model VARCHAR(50),
    capacity NUMERIC(10,2)
);

CREATE TABLE Drivers (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20)
);

CREATE TABLE Routes (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL,
    vehicle_id INTEGER NOT NULL,
    driver_id INTEGER NOT NULL,
    departure_date DATE,
    arrival_date DATE
);

CREATE TABLE Users (
    id SERIAL PRIMARY KEY,
    login VARCHAR(20) UNIQUE NOT NULL,
    e_mail VARCHAR(30) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    account_type VARCHAR(10) DEFAULT 'User' CHECK (account_type IN ('User', 'Admin'))
);

CREATE TABLE Sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    token VARCHAR(255) UNIQUE NOT NULL,
    ip_address VARCHAR(15) NOT NULL,
    creation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expiration_date TIMESTAMP DEFAULT (CURRENT_TIMESTAMP + INTERVAL '45 minute'),
    FOREIGN KEY (user_id) REFERENCES Users(id) ON DELETE CASCADE
);

ALTER TABLE Orders ADD FOREIGN KEY (client_id) REFERENCES Clients(id);
ALTER TABLE Orders ADD FOREIGN KEY (user_id) REFERENCES Users(id);

CREATE TABLE Warehouses_Orders (
    Warehouses_id INTEGER,
    Orders_id INTEGER,
    PRIMARY KEY (Warehouses_id, Orders_id),
    FOREIGN KEY (Warehouses_id) REFERENCES Warehouses(id),
    FOREIGN KEY (Orders_id) REFERENCES Orders(id)
);

ALTER TABLE Routes ADD FOREIGN KEY (order_id) REFERENCES Orders(id);
ALTER TABLE Routes ADD FOREIGN KEY (vehicle_id) REFERENCES Vehicles(id);
ALTER TABLE Routes ADD FOREIGN KEY (driver_id) REFERENCES Drivers(id);

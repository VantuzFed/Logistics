DROP SCHEMA IF EXISTS public CASCADE;
CREATE SCHEMA IF NOT EXISTS public;
SET search_path TO public;

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

CREATE OR REPLACE PROCEDURE create_order_with_warehouse(
    p_client_id INT,
    p_user_id INT,
    p_warehouse_id INT,
    p_status VARCHAR(50) DEFAULT 'Новый'
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_order_id INT;
BEGIN

    INSERT INTO Orders (client_id, user_id, order_date, status)
    VALUES (p_client_id, p_user_id, CURRENT_DATE, p_status)
    RETURNING id INTO v_order_id;


    INSERT INTO Warehouses_Orders (Warehouses_id, Orders_id)
    VALUES (p_warehouse_id, v_order_id);

    RAISE NOTICE 'Заказ №% успешно создан и привязан к складу №%', v_order_id, p_warehouse_id;
EXCEPTION
    WHEN OTHERS THEN
        RAISE EXCEPTION 'Ошибка при создании заказа: %', SQLERRM;
END;
$$;

CREATE OR REPLACE PROCEDURE clear_expired_sessions()
LANGUAGE plpgsql
AS $$
DECLARE
    deleted_rows INT;
BEGIN
    DELETE FROM Sessions
    WHERE expiration_date < CURRENT_TIMESTAMP;
    
    GET DIAGNOSTICS deleted_rows = ROW_COUNT;
    RAISE NOTICE 'Удалено устаревших сессий: %', deleted_rows;
END;
$$;


CREATE OR REPLACE FUNCTION check_warehouse_capacity()
RETURNS TRIGGER AS $$
DECLARE
    v_capacity INT;
    v_current_orders INT;
BEGIN

    SELECT capacity INTO v_capacity 
    FROM Warehouses 
    WHERE id = NEW.Warehouses_id;

    SELECT COUNT(*) INTO v_current_orders 
    FROM Warehouses_Orders 
    WHERE Warehouses_id = NEW.Warehouses_id;


    IF v_current_orders >= v_capacity THEN
        RAISE EXCEPTION 'Невозможно добавить заказ! Склад №% переполнен (Макс. вместимость: %)', 
                        NEW.Warehouses_id, v_capacity;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER trg_check_warehouse_capacity
BEFORE INSERT ON Warehouses_Orders
FOR EACH ROW
EXECUTE FUNCTION check_warehouse_capacity();


CREATE OR REPLACE FUNCTION update_order_status_on_route()
RETURNS TRIGGER AS $$
BEGIN

    UPDATE Orders
    SET status = 'В пути'
    WHERE id = NEW.order_id;

    RAISE NOTICE 'Статус заказа №% автоматически изменен на "В пути"', NEW.order_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER trg_update_order_status_on_route
AFTER INSERT ON Routes
FOR EACH ROW
EXECUTE FUNCTION update_order_status_on_route();



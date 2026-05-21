DROP SCHEMA IF EXISTS logistics CASCADE;
CREATE SCHEMA IF NOT EXISTS logistics;
SET search_path TO logistics;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE Clients (
    id         SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name  VARCHAR(100) NOT NULL,
    e_mail     VARCHAR(100) NOT NULL,
    phone_number VARCHAR(100) NOT NULL
);

-- Таблица пользователей с расширенным списком ролей из матрицы доступа
CREATE TABLE Users (
    id            SERIAL PRIMARY KEY,
    login         VARCHAR(20)  UNIQUE NOT NULL,
    e_mail        VARCHAR(100) UNIQUE NOT NULL,
    password_hash TEXT         NOT NULL,  -- bcrypt через pgcrypto
    account_type  VARCHAR(20)  DEFAULT 'Manager' CHECK (account_type IN ('Admin', 'Manager', 'Dispatcher', 'Driver_Warehouse')),
    created_at    TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Sessions (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER      NOT NULL,
    token           VARCHAR(255) UNIQUE NOT NULL,
    ip_address      VARCHAR(45)  NOT NULL,
    creation_time   TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    expiration_date TIMESTAMP    DEFAULT (CURRENT_TIMESTAMP + INTERVAL '45 minutes'),
    FOREIGN KEY (user_id) REFERENCES Users(id) ON DELETE CASCADE
);

CREATE TABLE Orders (
    id         SERIAL PRIMARY KEY,
    client_id  INTEGER     NOT NULL,
    user_id    INTEGER     NOT NULL,
    order_date DATE        NOT NULL,
    status     VARCHAR(50),
    FOREIGN KEY (client_id) REFERENCES Clients(id),
    FOREIGN KEY (user_id)   REFERENCES Users(id)
);

CREATE TABLE Warehouses (
    id       SERIAL PRIMARY KEY,
    name     VARCHAR(100) NOT NULL,
    address  TEXT         NOT NULL,
    capacity INTEGER      NOT NULL
);

CREATE TABLE Vehicles (
    id           SERIAL PRIMARY KEY,
    plate_number VARCHAR(20)    UNIQUE NOT NULL,
    type         VARCHAR(50),
    model        VARCHAR(50),
    capacity     NUMERIC(10, 2)
);

CREATE TABLE Drivers (
    id         SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name  VARCHAR(100) NOT NULL,
    phone      VARCHAR(20)
);

CREATE TABLE Routes (
    id             SERIAL PRIMARY KEY,
    order_id       INTEGER NOT NULL,
    vehicle_id     INTEGER NOT NULL,
    driver_id      INTEGER NOT NULL,
    departure_date DATE,
    arrival_date   DATE,
    FOREIGN KEY (order_id)   REFERENCES Orders(id),
    FOREIGN KEY (vehicle_id) REFERENCES Vehicles(id),
    FOREIGN KEY (driver_id)  REFERENCES Drivers(id)
);

CREATE TABLE Warehouses_Orders (
    warehouses_id INTEGER NOT NULL,
    orders_id     INTEGER NOT NULL,
    PRIMARY KEY (warehouses_id, orders_id),
    FOREIGN KEY (warehouses_id) REFERENCES Warehouses(id),
    FOREIGN KEY (orders_id)     REFERENCES Orders(id)
);

-- Процедура регистрации (с учетом новых ролей)
CREATE OR REPLACE PROCEDURE register_user(
    p_login    TEXT,
    p_email    TEXT,
    p_password TEXT,
    p_account_type TEXT DEFAULT 'Manager'
)
LANGUAGE plpgsql AS $$
BEGIN
    IF LENGTH(TRIM(p_password)) < 8 THEN
        RAISE EXCEPTION 'PASSWORD_TOO_SHORT';
    END IF;

    IF EXISTS (SELECT 1 FROM Users WHERE login = p_login) THEN
        RAISE EXCEPTION 'LOGIN_TAKEN';
    END IF;

    IF EXISTS (SELECT 1 FROM Users WHERE e_mail = LOWER(TRIM(p_email))) THEN
        RAISE EXCEPTION 'EMAIL_TAKEN';
    END IF;

    -- Валидация передаваемой роли на уровне СУБД
    IF p_account_type NOT IN ('Admin', 'Manager', 'Dispatcher', 'Driver_Warehouse') THEN
        RAISE EXCEPTION 'INVALID_ROLE';
    END IF;

    INSERT INTO Users (login, e_mail, password_hash, account_type)
    VALUES (
        TRIM(p_login),
        LOWER(TRIM(p_email)),
        crypt(p_password, gen_salt('bf', 12)),
        p_account_type
    );
END;
$$;

-- Функция авторизации
CREATE OR REPLACE FUNCTION login_user(
    p_email    TEXT,
    p_password TEXT
)
RETURNS TABLE (
    user_id      INTEGER,
    user_login   VARCHAR,
    account_type VARCHAR
)
LANGUAGE plpgsql
SECURITY DEFINER AS $$
BEGIN
    RETURN QUERY
    SELECT id, login, account_type
    FROM Users
    WHERE e_mail = LOWER(TRIM(p_email))
      AND password_hash = crypt(p_password, password_hash);
END;
$$;

-- Управление сессиями
CREATE OR REPLACE PROCEDURE create_session(
    p_user_id   INTEGER,
    p_token     TEXT,
    p_ip        TEXT
)
LANGUAGE plpgsql AS $$
BEGIN
    DELETE FROM Sessions
    WHERE user_id = p_user_id
      AND expiration_date < NOW();

    INSERT INTO Sessions (user_id, token, ip_address)
    VALUES (p_user_id, p_token, p_ip);
END;
$$;

-- Валидация сессии
CREATE OR REPLACE FUNCTION validate_session(
    p_token TEXT
)
RETURNS TABLE (
    user_id      INTEGER,
    user_login   VARCHAR,
    account_type VARCHAR
)
LANGUAGE plpgsql
SECURITY DEFINER AS $$
BEGIN
    RETURN QUERY
    SELECT u.id, u.login, u.account_type
    FROM Sessions s
    JOIN Users u ON u.id = s.user_id
    WHERE s.token = p_token
      AND s.expiration_date > NOW();
END;
$$;

-- Удаление сессии (разлогин)
CREATE OR REPLACE PROCEDURE logout_user(p_token TEXT)
LANGUAGE plpgsql AS $$
BEGIN
    DELETE FROM Sessions WHERE token = p_token;
END;
$$;

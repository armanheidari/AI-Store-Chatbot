DROP SCHEMA IF EXISTS kharid_yar;

CREATE SCHEMA kharid_yar;

USE kharid_yar;

CREATE TABLE users (
    customer_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(11)
);

CREATE TABLE orders (
    order_id    BIGINT PRIMARY KEY AUTO_INCREMENT,
    customer_id BIGINT,
    total_price       DECIMAL(10, 2),
    status      ENUM ('progress', 'delivered', 'completed', 'returned'),
    FOREIGN KEY (customer_id) REFERENCES users (customer_id)
);

# ALTER TABLE orders
# ADD COLUMN status ENUM('p', 'd', 'c');

CREATE TABLE products (
    product_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255),
    price DECIMAL(10, 2)
);

CREATE TABLE order_products (
    order_id BIGINT,
    product_id BIGINT,
    amount FLOAT,
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    PRIMARY KEY (order_id, product_id)
);

CREATE TABLE inventory (
    product_id BIGINT,
    count INT,
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);


INSERT INTO users (name, email, phone)
VALUES ('ali', 'ali@gmail.com', '09123456789'),
       ('sara', 'sara@gmail.com', '09129876543'),
       ('maryam', 'maryam@gmail.com', '09369026286');

INSERT INTO products (name, price)
VALUES  ('موز', 50000.00),
        ('گیلاس', 200000.00),
        ('گلابی', 40000.00),
        ('پودر ماشین لباسشویی', 20000.00),
        ('پودر بچه', 23000.00),
        ('چیپس', 15000.00),
        ('کیک وانیلی', 8000.00),
        ('آبمیوه هلو', 18000.00),
        ('دلستر', 12000.00),
        ('تن ماهی', 80000.00);


INSERT INTO inventory (product_id, count)
VALUES  (1, 10),
        (2, 20),
        (3, 5),
        (4, 7),
        (5, 2),
        (6, 1),
        (7, 9),
        (8, 5),
        (9, 4),
        (10, 6);

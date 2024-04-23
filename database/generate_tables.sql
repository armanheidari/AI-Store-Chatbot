DROP SCHEMA IF EXISTS kharid_yar;

CREATE SCHEMA kharid_yar;

USE kharid_yar;

CREATE TABLE users (
    customer_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(11),
    password VARCHAR(255)
);

# ALTER TABLE users
# ADD COLUMN password VARCHAR(255);

CREATE TABLE orders (
    order_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    customer_id BIGINT,
    total_price DECIMAL(10, 2),
    status ENUM ('progress', 'delivered', 'completed', 'returned'),
    updated_time TIMESTAMP DEFAULT current_timestamp,
    FOREIGN KEY (customer_id) REFERENCES users (customer_id)
);

# ALTER TABLE orders
# RENAME COLUMN created_at TO updated_time;

# ALTER TABLE orders
# ADD COLUMN created_at TIMESTAMP DEFAULT current_timestamp;

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
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

CREATE TABLE inventory (
    product_id BIGINT,
    count FLOAT,
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

# ALTER TABLE inventory
# MODIFY COLUMN count FLOAT;

INSERT INTO users (name, email, phone)
VALUES ('ali', 'ali@gmail.com', '09123456789'),
       ('sara', 'sara@gmail.com', '09129876543'),
       ('maryam', 'maryam@gmail.com', '09369026286');

INSERT INTO users (customer_id, name, email, phone)
VALUES (2001, 'Mahsa', 'mhs@gmail.com', '09129876544');

INSERT INTO users (name, email, phone)
VALUES ('zahra', 'zahra@gmail.com', '09362789015');

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

DROP TRIGGER IF EXISTS inventory_check;

CREATE TRIGGER inventory_check
BEFORE UPDATE ON inventory
FOR EACH ROW
BEGIN
    IF NEW.count < 0
        THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Quantity is not enough';
    END IF;
END;


SELECT name
FROM inventory i
JOIN products p ON p.product_id = i.product_id
WHERE name = 'گیلاس' AND
      count >= 20;

SELECT price
FROM products
WHERE name = 'گیلاس';

UPDATE inventory
JOIN products p ON p.id = inventory.id
SET count = count - 4
WHERE name = 'تن ماهی';

SELECT *
FROM order_products
WHERE order_id = 2;

UPDATE inventory
SET count = count + 4
WHERE id = 2;


USE mysql;

SELECT *
FROM mysql.user u;


SELECT *
FROM global_grants gg;

SHOW TABLES;

INSERT INTO orders (customer_id, total_price, status)
VALUES (2001, 200000, 'progress');

INSERT INTO order_products (order_id, product_id, amount)
VALUES ();


WITH order_detail AS (
    SELECT *
    FROM orders o
    WHERE order_id = 5
),
    order_products_detail AS (
        SELECT *
        FROM order_products op
        WHERE order_id = 5
    )
SELECT order_detail.order_id, customer_id, product_id, amount, total_price, status
FROM order_detail
JOIN order_products_detail ON order_detail.order_id = order_products_detail.order_id;

SELECT order_id, customer_id, total_price, status
FROM orders o
WHERE order_id = 7 AND
      current_timestamp - created_at <= 28800; # 8 hours

SELECT current_timestamp() + 300000 ;


SELECT order_id, customer_id, total_price, status, created_at
FROM orders o
WHERE order_id = 5;

SELECT *
FROM order_products op
WHERE order_id = 5;

DELETE FROM order_products op
WHERE order_id = 7;


SELECT *
FROM order_products op;

DROP PROCEDURE IF EXISTS delete_products_for_order;

DELIMITER $$

CREATE PROCEDURE delete_products_for_order(IN order_id BIGINT)
BEGIN
    DECLARE product BIGINT;
    DECLARE amount FLOAT;
    DECLARE done BOOL DEFAULT FALSE;

    DECLARE my_cursor CURSOR FOR (
        SELECT op.product_id, op.amount
        FROM order_products op
        WHERE op.order_id = order_id
    );

    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

    START TRANSACTION ;

    OPEN my_cursor;
    my_loop: LOOP
        FETCH my_cursor INTO product, amount;

        IF done THEN
            LEAVE my_loop;
        END IF;

        UPDATE inventory i
        SET i.count = i.count + amount
        WHERE i.product_id = product;

    END LOOP;

    CLOSE my_cursor;

    DELETE FROM order_products o
    WHERE o.order_id = order_id;

    COMMIT ;
END $$

DELIMITER ;

CALL delete_products_for_order(8);

INSERT INTO order_products
VALUES (8, 1, 10),
       (8, 1, 10);

DROP TEMPORARY TABLE temp;

CREATE TEMPORARY TABLE temp (
    t_product INT,
    t_amount FLOAT
);

SELECT *
FROM temp t;

UPDATE inventory i
SET i.count = i.count + 10
WHERE i.product_id = 1;

SELECT customer_id, status
FROM orders o
WHERE order_id = 6;

UPDATE orders o
SET updated_time = '2000-01-01 12:12:12',
    status = 'returned'
WHERE order_id = 6;

INSERT INTO orders
VALUES (9, 1, 1, 'progress', '2024-02-02 16:14:18');

CREATE TABLE product_unit (
    product_id BIGINT PRIMARY KEY,
    unit VARCHAR(255),
    FOREIGN KEY (product_id)
        REFERENCES products(product_id)
);

INSERT INTO product_unit
VALUES (1, 'کیلو'),
       (2, 'کیلو'),
       (3, 'کیلو'),
       (4, 'عدد'),
       (5, 'عدد'),
       (6, 'عدد|بسته'),
       (7, 'بسته|عدد'),
       (8, 'عدد'),
       (9, 'عدد'),
       (10, 'عدد');

import mysql.connector
from pathlib import Path
import json
import os
import re
from datetime import datetime

path = Path(__file__).parent

cursor = None
connection = None


def connect_to_database(fail=False):
    global connection
    global cursor
    global password_path
    if fail:
        if connection is not None:
            connection.reconnect()
    else:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="654321",
            database="kharid_yar",
            port="3306"
        )
        cursor = connection.cursor()


connect_to_database()


def check_inventory_product(product_name, amount):
    global cursor
    query = f'''
        SELECT name
        FROM inventory i
        JOIN products p ON p.product_id = i.product_id
        WHERE name = '{product_name}' AND
        count >= {amount};
    '''
    cursor.execute(query)
    res = cursor.fetchone()
    if res == None:
        raise ValueError("به تعداد کافی محصول مورد نظر موجود نمی باشد!")


def get_total_price(customer_id, discount=0):
    global path
    global cursor
    total_price = 0

    with open(path / 'tmp' / f'{customer_id}.json', 'r', encoding='utf-8') as f:
        try:
            order_list = json.load(f)
        except:
            return 0

    data = {
        'total_price': None,
        'cart': []
    }

    for order in order_list:
        query = f'''
            SELECT price, product_id
            FROM products
            WHERE name = '{order[1]}';
        '''
        cursor.execute(query)
        res = cursor.fetchone()
        cursor.reset()
        price = float(re.search(r'\d+\.\d{2}', str(res[0]))[0])
        total_price += order[0] * price
        data['cart'].append([res[1], order[0]])

    data['total_price'] = total_price
    with open(path / 'tmp' / f'{customer_id}.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    return total_price * (1 - discount)


def add_cart_to_database(customer_id):
    global connection
    global cursor
    with open(path / 'tmp' / f'{customer_id}.json', 'r', encoding='utf-8') as f:
        try:
            cart = json.load(f)
        except:
            return 0

    query = f'''
        INSERT INTO orders (customer_id, total_price, status)
        VALUES ('{customer_id}', {cart["total_price"]}, 'progress');
    '''

    cursor.execute(query)
    o_id = cursor._last_insert_id

    for product in cart['cart']:
        query = f'''
            INSERT INTO order_products (order_id, product_id, amount)
            VALUES ({o_id}, {product[0]}, {product[1]});
        '''
        cursor.execute(query)
        cursor.reset()
        query = f'''
            UPDATE inventory i
            SET count = count - {product[1]}
            WHERE product_id = {product[0]};
        '''
        cursor.execute(query)

    os.remove(path / 'tmp' / f'{customer_id}.json')

    connection.commit()
    cursor.reset()

    return o_id


def check_order_id(customer_id, order_id):
    global cursor

    query = f'''
        SELECT *
        FROM orders
        WHERE order_id = '{order_id}' and customer_id = '{customer_id}';
        '''
    cursor.execute(query)
    res = cursor.fetchone()
    cursor.reset()
    if res == None:
        raise ValueError("شما همچین سفارشی ثبت نکرده اید!")

def delete_order(order_id, customer_id):
    global connection
    global cursor
    
    check_order_id(customer_id, order_id)
    
    query = f'''
        SELECT order_id, customer_id, total_price, status, updated_time
        FROM orders
        WHERE order_id = {order_id};
        
    '''
    cursor.execute(query)
    res = cursor.fetchone()
    
    if (datetime.now() - res[-1]).seconds >= 28800:
        cursor.reset()
        raise Exception(
            '8 ساعت از زمان ثبت سفارش شما گذشته است و نمی توانید آن را مرجوع کنید.')
    
    elif res[3] == 'delivered':
        cursor.reset()
        raise Exception('سفارش شما از مرکز ارسال خارج شده است و نمی توانید آن را کنسل کنید. چنانچه هنوز هم تمایل به حذف سفارش خود دارید می توانید بعد از دریافت سفارش، طبق قوانین مرجوعی سفارشات، آن را برگردانید. با تشکر.')
    elif res[3] == 'completed':
        cursor.reset()
        raise Exception(
            'این سفارش تحویل مشتری داده شده است و نمی توانید آن را کنسل کنید.')
    else:
        cursor.reset()
        query = f'''
            CALL delete_products_for_order({order_id});
        '''
        cursor.execute(query)
        cursor.reset()
        
        query = f'''
            DELETE FROM orders
            where order_id = {order_id} and customer_id = {customer_id}
        '''
        cursor.execute(query)
        connection.commit()
        cursor.reset()
        return 'سفارش شما با موفقیت کنسل شد.'


def refund_order_database(order_id, customer_id):
    global connection
    global cursor
    
    check_order_id(customer_id, order_id)
    
    query = f'''
        SELECT customer_id, status
        FROM orders o
        WHERE order_id = {order_id};
    '''
    cursor.execute(query)
    res = cursor.fetchone()

    if res[1] != 'completed':
        raise Exception(
            'سفارش به دست مشتری نرسیده است و نمی توان آن را مرجوع کرد.')
    else:
        cursor.reset()
        query = f'''
            UPDATE orders o
            SET updated_time = '{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}',
                status = 'returned'
            WHERE order_id = {order_id};
        '''
        cursor.execute(query)
        connection.commit()
        cursor.reset()
        return 'درخواست مرجوعی شما با موفقیت انجام شد.'


def order_tracking(customer_id, order_id):
    global cursor

    check_order_id(customer_id, order_id)

    query = f'''
        SELECT status
        FROM orders
        WHERE order_id = '{order_id}';
        '''
    cursor.execute(query)
    result = cursor.fetchone()[0]
    cursor.reset()

    res = "مشخص نشده"
    if result == "progress":
        res = "در حال بررسی"
    elif result == "delivered":
        res = "ارسال شده"
    elif result == "completed":
        res = "تکمیل شده"
    elif result == "returned":
        res = "مرجوع شده"

    return res


def cancel_refund(customer_id, order_id):
    global cursor
    global connection

    check_order_id(customer_id, order_id)

    query = f'''
        SELECT updated_time
        FROM orders
        WHERE status = 'returned';
        '''
    cursor.execute(query)
    res = cursor.fetchone()
    cursor.reset()

    if res == None:
        raise ValueError("سفارش شما در وضعیت مرجوعی نیست.")

    time_left = (datetime.now() - res[0]).seconds
    if time_left <= 4 * 3600:
        query = f'''
        UPDATE orders
        SET `status` = "progress"
        WHERE order_id = '{order_id}'
        '''
    cursor.execute(query)
    connection.commit()
    cursor.reset()

    return "درخواست مرجوعی شما لغو شد."

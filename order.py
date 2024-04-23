import re
from hazm import InformalNormalizer
from database.database import connect_to_database, connection, cursor

normalizer = InformalNormalizer()

def get_num(amount: str) -> float | int:
    try:
        return float(amount)
    except:
        str_to_int = {
            "صفر": 0,
            "یک": 1,
            "دو": 2,
            "سه": 3,
            "چهار": 4,
            "پنج": 5,
            "شش": 6,
            "هفت": 7,
            "هشت": 8,
            "نه": 9
        }

        try:
            return str_to_int[amount]
        except:
            raise ValueError("عدد وارد شده صحیح نمی‌باشد")

connect_to_database()

def loadunits():
    query = f'''
        SELECT name, unit
        FROM product_unit pu
        JOIN products p ON p.product_id = pu.product_id;
    '''
    cursor.execute(query)
    res = cursor.fetchall()
    unit_dict = {}
    for product_name, unit in res:
        for i in unit.split('|'):
            try:
                unit_dict[i].add(product_name)
            except:
                unit_dict[i] = {product_name}
    return unit_dict


unit_dict = loadunits()


def check_compatibility(product: str, unit: str) -> None:
    if list(filter(lambda x: product in x, unit_dict.values())) == []:
        raise ValueError("کالای مورد نظر موجود نمی‌باشد")

    try:
        compatible_products = unit_dict[unit]
    except:
        raise ValueError("واحد داده شده معتبر نمی‌باشد")

    if product not in compatible_products:
        raise ValueError("عدم مطابقت واحد و کالا")


def check_order(order):

    pattern = re.compile(r"^(?P<amount>[\u0621-\u0628\u062A-\u063A\u0641-\u0642\u0644-\u0648\u064E-\u0651\u0655\u067E\u0686\u0698\u06A9\u06AF\u06BE\u06CC\u06F0-\u06F9\u0660-\u0669\d\.]+)( \u062A\u0627)? (?P<unit>[\u0621-\u0628\u062A-\u063A\u0641-\u0642\u0644-\u0648\u064E-\u0651\u0655\u067E\u0686\u0698\u06A9\u06AF\u06BE\u06CC]+) (?P<product>[\u0621-\u0628\u062A-\u063A\u0641-\u0642\u0644-\u0648\u064E-\u0651\u0655\u067E\u0686\u0698\u06A9\u06AF\u06BE\u06CC\u0020\u2000-\u200F\u2028-\u202F]+)$")

    if ptr := pattern.match(order):
        amount = ptr.group("amount")
        unit = ptr.group("unit")
        product = ptr.group("product")

        # - تخم     مرغ ----> تخم مرغ
        word_list = [normalizer.normalized_word(x)[0]
                    for x in product.split() if x != ""]
        product = " ".join(word_list).replace("\u200c", "")

        amount = get_num(amount)
        check_compatibility(product, unit)

        return amount, unit, product

    else:
        raise SyntaxError("سفارش قابل قبول نیست")


connection = None
cursor = None


def sold(amount: int, unit: str, product: str):
    global connection
    global cursor
    query = f'''
        UPDATE inventory
        JOIN products p ON p.id = inventory.id
        SET count = count - {amount}
        WHERE name = '{product}';
    '''
    try:
        cursor.execute(query)
        connection.commit()
        cursor.reset()
    except Exception as e:
        raise


def order(orders):

    orders_va = [x for x in orders.strip().split(" و ") if x != ""]
    orders_dash = [x for x in orders.strip().split(" - ") if x != ""]

    order_list = []
    try:
        for order in orders_dash:
            order_list.append(check_order(order))

    except:
        for order in orders_va:
            order_list.append(check_order(order))

    return order_list

# '''
# یک عدد کیک - یک عدد صابون - یک کیلو سیب
# یک عدد کیک و یک عدد صابون و یک کیلو سیب
# '''

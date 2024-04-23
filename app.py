from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import tensorflow as tf
import pickle
import json
from sklearn.preprocessing import LabelEncoder
import random
from order import order
from pathlib import Path
import os
from database.database import *
from hazm import *
import glob

mode = False
path = Path(__file__).parent


technical_model = tf.keras.models.load_model(path / "models/technical_model")
cancel_model = tf.keras.models.load_model(path / "models/cancel_model")
chitchat_model = tf.keras.models.load_model(path / "models/chitchat_model")
full_model = tf.keras.models.load_model(path / "models/full_model")

with open(path / "tokenizers/full_tokenizer.pickle", 'rb') as handle:
    full_tokenizer = pickle.load(handle)

with open(path / "tokenizers/chitchat_tokenizer.pickle", 'rb') as handle:
    chitchat_tokenizer = pickle.load(handle)

with open(path / "tokenizers/technical_tokenizer.pickle", 'rb') as handle:
    technical_tokenizer = pickle.load(handle)

with open(path / "tokenizers/cancel_tokenizer.pickle", 'rb') as handle:
    cancel_tokenizer = pickle.load(handle)

full_label = ['miss_understanding', 'chitchat', 'technical']
chitchat_label = ['whats_up', 'goodbye', 'greet', 'how_are_you', 'job', 'name']
technical_label = ['buying', 'order_tracking', 'customer_service', 'refund', 'cancelling', 'edit_order']
cancel_label = ['order_cancelling', 'refund_cancelling', 'edit_order']


technical_encoder = LabelEncoder()
chitchat_encoder = LabelEncoder()
full_encoder = LabelEncoder()
cancel_encoder = LabelEncoder()


technical_encodedLabel = technical_encoder.fit_transform(technical_label)
chitchat_encodedLabel = chitchat_encoder.fit_transform(chitchat_label)
full_encodedLabel = full_encoder.fit_transform(full_label)
cancel_encodedLabel = cancel_encoder.fit_transform(cancel_label)


with open(path / 'answer_dataset.json', 'rb') as json_data:
    answers = json.load(json_data)

instructions_queue = []
order_list = []

flag = True

special_words_yes = [
    "بله",
    "اره",
    "یس",
    "اوهوم"
]

special_words_no = [
    "خیر",
    "نخیر",
    "نه",
    "نو",
    "نمیکنم"
]

special_words_end = [
    "تمومه",
    "تمام",
    "همینا",
    "همین",
]

special_words_have = [
    "ندارم",
    "نمیخوام",
    "رد کردن",
]

special_words_discount = [
    "starter25",
    "starter20",
    "special50"
]


class Preproccessing:
    def __init__(self):
        self.normalizer_formal = Normalizer(
            correct_spacing=True,
            remove_diacritics=True,
            remove_specials_chars=True,
            decrease_repeated_chars=True,
            seperate_mi=True
        )
        self.normalizer_informal = InformalNormalizer()
        self.lemmatizer = Lemmatizer()

    def train(self, text, string=True):
        strs = ""
        text = self.normalizer_formal.normalize(text)
        text = self.normalizer_informal.normalize(text)[0]
        for i in range(len(text)):
            if len(text[i]) != 1:
                text[i] = [text[i][0]]
            text[i] = self.lemmatizer.lemmatize(text[i][0]).split("#")[0]
            strs += (text[i] + " ")
        if string:
            return re.sub(r'[^\w\s]', ' ', self.normalizer_formal.normalize(strs))
        return text

preProcess = Preproccessing()

def classify(text, tokenizer, model, encoder, maxlen=30):
    text = preProcess.train(text)
    tokenized = tokenizer.texts_to_sequences([text])
    tokenized = tf.keras.preprocessing.sequence.pad_sequences(
        tokenized, maxlen)
    prediction = model.predict(tokenized)
    label = prediction.argmax()
    print(prediction)
    prediction = encoder.inverse_transform([label])
    return prediction

def get_order(customer_id, text):
    global mode
    def __delete():
        try:
            os.remove(path / 'tmp' / f'{customer_id}.json')
        except:
            return {
                "status": "message",
                "message": json.dumps(["درخواست سفارش شما لغو شد.", "چه کاری می توانم برایتان انجام دهم؟"], ensure_ascii=False),
                "content": json.dumps([], ensure_ascii=False)
            }
        return {
            "status": "delete_cart",
            "message": json.dumps(["سفارش شما با موفقیت حذف شد!"], ensure_ascii=False),
            "content": json.dumps([], ensure_ascii=False)
        }


    def __edit(item, new_item):
        removed = False
        try:
            with open(path / 'tmp' / f'{customer_id}.json', 'r', encoding='utf-8') as f:
                cart = json.load(f)
        except OSError as e:
            raise Exception("سبد خرید شما خالی است.")
        
        __add(new_item)

        index = 0
        for i in range(len(cart)):
            if item == cart[i]:
                cart.__delitem__(i)
                index = i
                removed = True
                break
        
        if removed == False:
            return {
                "status": "message",
                "message": json.dumps(["شما همچین کالایی برای تغییر دادن ندارید.", "لطفا ادامه لیست خرید خود را وارد کنید."], ensure_ascii=False),
                "content": json.dumps([], ensure_ascii=False)
            }
        
        with open(path / 'tmp' / f'{customer_id}.json', 'w', encoding='utf-8') as f:
            json.dump(cart, f, ensure_ascii=False, indent=4)
            
        return {
            "status": "edit_cart",
            "message": json.dumps(["تغییرات با موفقیت اعمال شد.", "لطفا ادامه لیست خرید خود را وارد کنید."], ensure_ascii=False),
            "content": json.dumps(new_item, ensure_ascii=False),
            "deleted": index
        }


    def __add(item):
        customized_orders = []

        # return unit of products in each product
        # check overlap cart products
        for o in item:
            customized_orders.append([o[0], o[2]])
            try:
                check_inventory_product(o[2], o[0])
            except ValueError as ve:
                return {
                    "status": "message",
                    "message": json.dumps(["کالای مورد نظر به تعداد کافی موجود نمی باشد."], ensure_ascii=False),
                    "content": json.dumps([], ensure_ascii=False)
                }

        try:
            with open(path / 'tmp' / f'{customer_id}.json', 'r', encoding='utf-8') as f:
                try:
                    cart = json.load(f)
                except:
                    cart = []
            with open(path / 'tmp' / f'{customer_id}.json', 'w', encoding='utf-8') as f:
                json.dump(cart + customized_orders, f,
                            ensure_ascii=False, indent=4)

        except OSError as e:
            with open(path / 'tmp' / f'{customer_id}.json', 'w', encoding='utf-8') as f:
                json.dump(customized_orders, f, ensure_ascii=False, indent=4)

        return {
            "status": "cart",
            "message": json.dumps(["کالای مورد نظر به سبد خرید اضافه شد."], ensure_ascii=False),
            "content": json.dumps(item, ensure_ascii=False)
        }

    if mode:
        try:
            text = text.split(" به جای")
            delete_item = [order(text[1])[0][0], order(text[1])[0][2]]
            new_item = order(text[0])
        except ValueError as ve:
            return {
                "status": "message",
                "message": json.dumps([str(ve), "نحوه درست وارد کردن سفارش به شرح زیر است:", "[مقدار محصول] [واحد محصول] [محصول مورد نظر]"], ensure_ascii=False),
                "content": json.dumps([], ensure_ascii=False)
            }

        mode = False
        return __edit(delete_item, new_item)


    tag = classify(text, technical_tokenizer, technical_model, technical_encoder)
    
    if text not in special_words_end + special_words_yes + special_words_have + special_words_no + special_words_yes + special_words_discount:
        instructions_queue.append((get_order, 2001))
        try:
            orders = order(text)
        except Exception as se:
            if tag == "cancelling" or tag == "refund":
                instructions_queue.pop()
                return __delete()
                
            elif tag == "edit_order":
                # instructions_queue.pop()
                instructions_queue.append((get_order, 2001))
                mode = True
                return {
                    "status": "message",
                    "message": json.dumps(["لطفا تغییرات خود را اعمال کنید."], ensure_ascii=False),
                    "content": json.dumps([], ensure_ascii=False)
            } 
            else:
                return {
                    "status": "message",
                    "message": json.dumps([str(se), "نحوه درست وارد کردن سفارش به شرح زیر است:", "[مقدار محصول] [واحد محصول] [محصول مورد نظر]"], ensure_ascii=False),
                    "content": json.dumps([], ensure_ascii=False)
                }

        return __add(orders)
    
    elif text in special_words_end:
        instructions_queue.append((get_order, 2001))
        return {
            "status": "message",
            "message": json.dumps(["کد تخفیف خود را وارد کنید (درصورت نداشتن کد اعلام کنید)"], ensure_ascii=False),
            "content": json.dumps([], ensure_ascii=False)
        }

    elif text in special_words_discount:
        total_price = get_total_price('2001', float(f"0.{text[-2:]}"))
        instructions_queue.append((get_order, 2001))
        return {
            "status": "total_price",
            "message": json.dumps([f"جمع هزینه کل خرید های شما: {total_price}", "آیا سفارش خود را تایید می کنید؟"], ensure_ascii=False),
            "content": json.dumps([total_price], ensure_ascii=False)
        }

    elif text in special_words_have:
        total_price = get_total_price('2001')
        instructions_queue.append((get_order, 2001))
        return {
            "status": "total_price",
            "message": json.dumps([f"جمع هزینه کل خرید های شما: {total_price}", "آیا سفارش خود را تایید می کنید؟"], ensure_ascii=False),
            "content": json.dumps([total_price], ensure_ascii=False)
        }

    elif text in special_words_yes:
        order_id = add_cart_to_database('2001')
        return {
            "status": "order_complete",
            "message": json.dumps([f"سفارش شما با موفقیت ثبت شد!", f"شماره پیگیری سفارش: {order_id}", "امیدوارم بازهم ازما خرید کنید!"], ensure_ascii=False),
            "content": json.dumps([], ensure_ascii=False)
        }

    elif text in special_words_no:
        return __delete()
        
    
def control_flow(instructor, text):
    return instructor(text)

def cancel_order(order_id):
    try:
        res = delete_order(order_id, "2001")
    except Exception as e:
        return {
            "status": "message",
            "message": json.dumps([f"سفارش شما با شماره پیگیری {order_id} جهت حذف خرید، بررسی خواهد شد.", str(e)], ensure_ascii=False),
            "content": json.dumps([], ensure_ascii=False)
        }
    return {
        "status": "message",
        "message": json.dumps([f"سفارش شما با شماره پیگیری {order_id} جهت حذف خرید، بررسی خواهد شد.", res], ensure_ascii=False),
        "content": json.dumps([], ensure_ascii=False)
    }
    
def refund_order(order_id):
    try:
        res = refund_order_database(int(order_id), "2001")
    except Exception as e:
        return {
            "status": "message",
            "message": json.dumps([f"سفارش شما با شماره پیگیری {order_id} جهت بازگشت پیگیری خواهد شد.", str(e)], ensure_ascii=False),
            "content": json.dumps([], ensure_ascii=False)
        }
    return {
        "status": "message",
        "message": json.dumps([f"سفارش شما با شماره پیگیری {order_id} جهت بازگشت پیگیری خواهد شد.", res], ensure_ascii=False),
        "content": json.dumps([], ensure_ascii=False)
    }

def tracking_order(order_id):
    result = order_tracking("2001", order_id)
    answer = f'سفارش شما در وضعیت "{result}" است.'
    return {
        "status": "message",
        "message": json.dumps([f"سفارش شما با شماره پیگیری {order_id} برای آگاهی از وضعیت حال حاضر پیگیری خواهد شد.", answer], ensure_ascii=False),
        "content": json.dumps([], ensure_ascii=False)
    }

def cancel_refund(order_id):
    try:
        result = cancel_refund("2001", order_id)
    except Exception as e:
        return {
            "status": "message",
            "message": json.dumps([f"سفارش شما با شماره پیگیری {int(order_id)} جهت حذف مرجوعی، بررسی خواهد شد.", str(e)], ensure_ascii=False),
            "content": json.dumps([], ensure_ascii=False)
        }
    return {
        "status": "message",
        "message": json.dumps([result], ensure_ascii=False),
        "content": json.dumps([], ensure_ascii=False)
    }

def get_response(msg, tag, stats):
    global instructions_queue
    if stats:
        if len(instructions_queue) != 0:
            if instructions_queue.pop() == get_order:
                try:
                    os.remove(path / 'tmp' / f'{2001}.json')
                except:
                    pass
        instructions_queue = []
        for answer in answers['intents']:
            if tag == answer["tag"]:
                return {
                    "status": "message",
                    "message": json.dumps([random.choice(answer['responses'])], ensure_ascii=False),
                    "content": json.dumps([], ensure_ascii=False)
                }

    if not instructions_queue:
        if tag == "chitchat":
            tag = classify(msg, chitchat_tokenizer,
                            chitchat_model, chitchat_encoder, 20)
        elif tag == "technical":
            tag = classify(msg, technical_tokenizer,
                            technical_model, technical_encoder)
            if tag == "cancelling":
                tag = classify(msg, cancel_tokenizer,
                                cancel_model, cancel_encoder)

        for answer in answers['intents']:
            if tag == answer["tag"]:
                if tag == "buying":
                    instructions_queue.append((get_order, 2001))
                    return {
                        "status": "message",
                        "message": json.dumps([random.choice(answer['responses'])], ensure_ascii=False),
                        "content": json.dumps([], ensure_ascii=False)
                    }

                elif tag == "refund":
                    instructions_queue.append((control_flow, refund_order))
                    return {
                        "status": "message",
                        "message": json.dumps([random.choice(answer['responses'])], ensure_ascii=False),
                        "content": json.dumps([], ensure_ascii=False)
                    }

                elif tag == "order_tracking":
                    instructions_queue.append((control_flow, tracking_order))
                    return {
                        "status": "message",
                        "message": json.dumps([random.choice(answer['responses'])], ensure_ascii=False),
                        "content": json.dumps([], ensure_ascii=False)
                    }
                    
                elif tag == "refund_cancelling":
                    instructions_queue.append((control_flow, cancel_refund))
                    return {
                        "status": "message",
                        "message": json.dumps([random.choice(answer['responses'])], ensure_ascii=False),
                        "content": json.dumps([], ensure_ascii=False)
                    }
                    
                elif tag == "order_cancelling":
                    instructions_queue.append((control_flow, cancel_order))
                    return {
                        "status": "message",
                        "message": json.dumps([random.choice(answer['responses'])], ensure_ascii=False),
                        "content": json.dumps([], ensure_ascii=False)
                    }
                    
                elif tag == "edit_order":
                    instructions_queue.append((control_flow, cancel_order))
                    return {
                        "status": "message",
                        "message": json.dumps(random.choice(answer['responses']), ensure_ascii=False),
                        "content": json.dumps([], ensure_ascii=False)
                    }

                elif tag == "customer_service":
                    instructions_queue.append((control_flow, refund_order))
                    return {
                        "status": "message",
                        "message": json.dumps([random.choice(answer['responses'])], ensure_ascii=False),
                        "content": json.dumps([], ensure_ascii=False)
                    }

                elif tag == "whats_up":
                    return {
                        "status": "message",
                        "message": json.dumps([random.choice(answer['responses'])], ensure_ascii=False),
                        "content": json.dumps([], ensure_ascii=False)
                    }

                elif tag == "goodbye":
                    return {
                        "status": "message",
                        "message": json.dumps([random.choice(answer['responses'])], ensure_ascii=False),
                        "content": json.dumps([], ensure_ascii=False)
                    }

                elif tag == "how_are_you":
                    return {
                        "status": "message",
                        "message": json.dumps([random.choice(answer['responses'])], ensure_ascii=False),
                        "content": json.dumps([], ensure_ascii=False)
                    }

                elif tag == "job":
                    return {
                        "status": "message",
                        "message": json.dumps(random.choice(answer['responses']), ensure_ascii=False),
                        "content": json.dumps([], ensure_ascii=False)
                    }
                elif tag == "name":
                    return {
                        "status": "message",
                        "message": json.dumps(random.choice(answer['responses']), ensure_ascii=False),
                        "content": json.dumps([], ensure_ascii=False)
                    }

                elif tag == "greet":
                    return {
                        "status": "message",
                        "message": json.dumps([random.choice(answer['responses'])], ensure_ascii=False),
                        "content": json.dumps([], ensure_ascii=False)
                    }

                elif tag == "miss_understanding":
                    return {
                        "status": "message",
                        "message": json.dumps([random.choice(answer['responses'])], ensure_ascii=False),
                        "content": json.dumps([], ensure_ascii=False)
                    }
    else:
        func = instructions_queue.pop()
        return func[0](func[1], msg)


app = Flask(__name__, template_folder='templates')
CORS(app)

@app.route("/", methods=["GET"])
def index_get():
    global instructions_queue
    instructions_queue = []
    return render_template('base.html')

@app.route("/predict", methods=["POST"])
def predict():
    text = request.get_json().get("message")
    tag = classify(text, full_tokenizer, full_model, full_encoder)

    if tag == "miss_understanding":
        stats = True
    else:
        stats = False

    try:
        response = get_response(text, tag, stats)
    except Exception as e:
        response = {
            "status": "message",
            "message": json.dumps([str(e)], ensure_ascii=False),
            "content": json.dumps([], ensure_ascii=False)
        }

    if response == None:
        return None

    return jsonify(response)

if __name__ == "__main__":
    files = glob.glob(str(path / 'tmp/*'))
    for f in files:
        os.remove(f)
    app.run()
class Chatbox {
    constructor() {
        this.args = {
            openButton: document.querySelector('.chatbox__button'),
            chatBox: document.querySelector('.chatbox__support'),
            sendButton: document.querySelector('.send__button'),
            cart: document.querySelector('.cart')
        }

        this.stateChatBox = false;
        this.stateCart = false;
        this.mustToggleCart = false
        this.messages = [];
    }

    display() {
        const {openButton, chatBox, sendButton, cart} = this.args;

        openButton.addEventListener('click', () => this.toggleStateChatBox(chatBox, cart))

        sendButton.addEventListener('click', () => this.onSendButton(chatBox, cart))

        const node = chatBox.querySelector('input');
        node.addEventListener("keyup", ({key}) => {
            if (key === "Enter") {
                this.onSendButton(chatBox, cart)
            }
        })
    }

    toggleStateCart(cart) {
        this.stateCart = !this.stateCart;

        // show or hides the box
        if(this.stateCart) {
            cart.classList.add('cart--active')
        } else {
            cart.classList.remove('cart--active')
        }
    }

    toggleStateChatBox(chatbox, cart) {
        this.stateChatBox = !this.stateChatBox;

        if (this.mustToggleCart) {
            this.toggleStateCart(cart)
        }

        // show or hides the box
        if(this.stateChatBox) {
            chatbox.classList.add('chatbox--active')
        } else {
            chatbox.classList.remove('chatbox--active')
        }
    }

    onSendButton(chatbox, cart) {
        var textField = chatbox.querySelector('input');
        let text1 = textField.value
        if (text1 === "") {
            return;
        }

        let msg1 = { name: "User", message: text1 }
        this.messages.push(msg1);

        fetch('http://127.0.0.1:5000/predict', {
            method: 'POST',
            body: JSON.stringify({ message: text1 }),
            'Access-Control-Allow-Origin': '*',
            mode: 'cors',
            headers: {
              'Content-Type': 'application/json'
            },
          })
          .then(r => r.json())
          .then(r => {

            if (r.status == "message") {
                this.showMessage(r)
                textField.value = '' 
            }
            else if (r.status == "total_price") {
                this.showTotalPrice(r)
                this.showMessage(r)
                textField.value = '' 
            }
            else if (r.status == "cart") {
                if (this.stateCart == false) {
                    this.toggleStateCart(cart)
                    this.mustToggleCart = true
                }
                this.updateCartList(r)
                this.showMessage(r)
                textField.value = ''
            }
            else if (r.status == "delete_cart") {
                this.deleteCart()
                this.toggleStateCart(cart)
                this.showMessage(r)
                textField.value = ''
            }
            else if (r.status == "order_complete") {
                this.deleteCart()
                this.toggleStateCart(cart)
                this.showMessage(r)
                textField.value = ''
            }
            else if (r.status == "edit_cart") {
                this.showMessage(r)
                this.deleteFromCart(r)
                this.updateCartList(r)
                textField.value = ''
            }
            else {
                console.log("UNKOWN")
            }

        }).catch((error) => {
            console.error('Error:', error);
            this.updateChatText(chatbox)
            textField.value = ''
          });
    }

    showMessage(response) {
        const elements = JSON.parse(response.message)
        for (let index = 0; index < elements.length; index++) {
            this.messages.push(
                {name: "KharidYar", message: elements[index]}
            )
        }
        this.updateChatText(chatbox)
    }

    showTotalPrice(response) {
        const price = JSON.parse(response.content)[0]
        const cartfooter = document.querySelector(".cart__footer")

        var html = ""
        html += '<p>هزار تومان</p>\n'
        html += '<p>' + price + '</p>\n'
        html += '<h4 class="cart__footer--header">:قیمت</h4>\n'

        cartfooter.innerHTML = html
    }

    updateChatText(chatbox) {
        var html = '';
        this.messages.slice().reverse().forEach(function(item, index) {
            if (item.name === "KharidYar")
            {
                html += '<div class="messages__item messages__item--visitor">' + item.message + '</div>'
            }
            else
            {
                html += '<div class="messages__item messages__item--operator">' + item.message + '</div>'
            }
          });

        const chatmessage = document.querySelector('.chatbox__messages');
        chatmessage.innerHTML = html;
    }

    updateCartList(response) {
        const elements = JSON.parse(response.content)
        const cartlist = document.querySelector(".cart__list")
        var html = ""
        for (let index = 0; index < elements.length; index++) {
            const res = elements[index]
            html += '<div class="cart__item">\n<div class="cart__item__val">' + res[2] + '</div>\n'
            html += '<div class="cart__item__val">' + res[1] + '</div>\n'
            html += '<div class="cart__item__val">' + res[0] + '</div>\n</div>\n'
        }
        cartlist.innerHTML += html
    }

    deleteCart() {
        const cartlist = document.querySelector(".cart__list")
        const cartfooter = document.querySelector(".cart__footer")

        cartlist.innerHTML = ""
        cartfooter.innerHTML = ""
        this.mustToggleCart = false
    }

    deleteFromCart(response) {
        let items = document.querySelectorAll('.cart__item')
        const index = response.deleted

        console.log(index)
        console.log(items)

        if (index >= 0 && index < items.length) {
            items[index].remove();
        }

    }

}


const chatbox = new Chatbox();
chatbox.display();
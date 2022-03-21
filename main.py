import telebot
import time
from datetime import date, datetime

from database import Database

db = Database()
current_date = date.today()
TELEGRAM_TOKEN = '5127599455:AAFSqmdXkujm_l17jKLfFVPo6nGAoodM_JY'
bot = telebot.TeleBot(TELEGRAM_TOKEN, parse_mode='HTML')
start_buttons = ['Посмотреть записи', 'Добавить запись', 'Зачисление средств', 'Статистика', 'Вклад']


def check(arg):
    if arg is None or arg[0][0] is None:
        arg = 0
    else:
        arg = arg[0][0]
    return arg


def send_message(message, text, keyboard=None):
    bot.send_message(
        message.chat.id,
        text,
        reply_markup=keyboard
    )


def check_db(message):
    global db
    global current_date
    current_date = date.today()
    id_user = message.chat.id
    if db is None:
        db = Database()
        send_message(message, '<tg-spoiler><i>Подключаю базу данных...</i></tg-spoiler>')
        time.sleep(1)
        bot.edit_message_text(
            text='<i>База успешно подключена.</i>',
            chat_id=id_user,
            message_id=message.id + 1
        )
        # text = '''<tg-spoiler>spoiler</tg-spoiler> <code>inline fixed-width code</code>''''''


def keyboards(args):
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = [telebot.types.KeyboardButton(
        f'{i}') for i in args]
    keyboard.add('В начало')
    keyboard.add(*buttons)
    return keyboard


def mouth(start, end, user_id):
    start = datetime.strptime(f'{start}.22', '%d.%m.%y').date()
    end = datetime.strptime(f'{end}.22', '%d.%m.%y').date()
    cash = db.query(f"""select sum(balance)
                        from cash
                        where user_id = '{user_id}' and date(date) between date('{start}') and date('{end}');""")
    product = db.query(f"""select sum(price)
                           from product
                           where user_id = '{user_id}' and date(date) between date('{start}') and date('{end}');""")
    bank = db.query(f"""select sum(balance)
                        from bank
                        where user_id = '{user_id}' and date(date) between date('{start}') and date('{end}');""")
    cash = check(cash)
    product = check(product)
    bank = check(bank)
    return cash, product, bank


def create_product(cat, name, count, price, user_id):
    cat_id = db.query(f"SELECT cat_id FROM category where user_id = '{user_id}' and cat_name='{cat}';")[0][0]
    prod_id = db.query(f"SELECT MAX(prod_id) FROM product;")[0][0]
    if prod_id is None:
        prod_id = 1
    else:
        prod_id += 1
    user = (prod_id, name, cat_id, price, count, current_date, user_id)
    db.create("INSERT INTO product VALUES (?,?,?,?,?,?,?);", user)


def keyboard_category(user_id):
    category = db.query(f"SELECT cat_name FROM category where user_id = '{user_id}';")
    if category:
        category = [i[0] for i in category]
        return keyboards(category)
    return keyboards(['Категории отсутствуют.'])


@bot.message_handler(commands=['start'])
def start_command(message):
    check_db(message)
    keyboard = keyboards(start_buttons)
    message_start = 'Здравствуйте, я ваш финансовый помощник.\nВыберите пункт в меню, что бы начать работу.'
    send_message(message, message_start, keyboard)


@bot.message_handler(commands=['base'])
def open_base(message):
    check_db(message)


@bot.message_handler(func=lambda m: m.text == 'В начало')
def up(message):
    check_db(message)
    keyboard = keyboards(start_buttons)
    send_message(message, 'Выберите пункт в меню, что бы начать работу.', keyboard)


@bot.message_handler(func=lambda m: m.text == 'Вклад')
def create(message):
    check_db(message)
    buttons = ['Внести', 'Снять', 'Баланс']
    keyboard = keyboards(buttons)
    send_message(message, 'Выберите действие', keyboard)


@bot.message_handler(func=lambda m: m.text == 'Внести')
def add_balance(message):
    check_db(message)
    send_message(message, 'Данные в формате\n<code>*Сумма</code>')


@bot.message_handler(func=lambda m: m.text[0] == '*')
def balance_in_db(message):
    check_db(message)
    balance = message.text[1:].split()
    if len(balance) == 1:
        bank_id = db.query(f"SELECT bank_id FROM bank;")
        if bank_id is None or bank_id[0][0] is None:
            bank = (1, balance[0], current_date, message.chat.id)

        else:
            bank_id = db.query(f"SELECT max(bank_id) FROM bank;")[0][0] + 1
            bank = (bank_id, balance[0], current_date, message.chat.id)
        db.create("INSERT INTO bank VALUES (?,?,?,?)", bank)
        send_message(message, 'Успешно зачислено!')


@bot.message_handler(func=lambda m: m.text == 'Снять')
def eject_bank(message):
    check_db(message)
    send_message(message, 'Данные в формате\n<code>-Сумма</code>')


@bot.message_handler(func=lambda m: m.text[0] == '-')
def balance_out_db(message):
    check_db(message)
    balance = message.text[1:].split()
    if len(balance) == 1:
        bank_id = db.query(f"select bank_id from bank;")
        if bank_id is None or bank_id[0][0] is None:
            message_text = 'Средства отсутствуют!'
        else:
            bank_id = db.query(f"SELECT max(bank_id) FROM bank;")[0][0] + 1
            bank = (bank_id, f'-{balance[0]}', current_date, message.chat.id)
            db.create("INSERT INTO bank VALUES (?,?,?,?);", bank)
            message_text = 'Успешно изъято!'
        send_message(message, message_text)


@bot.message_handler(func=lambda m: m.text == 'Баланс')
def show_balance(message):
    check_db(message)
    bank = db.query(f"select sum(balance) from bank where user_id = '{message.chat.id}';")[0][0]
    if bank is not None:
        message_text = f'Сумма на счету: <code>{bank}</code> руб.'
    else:
        message_text = 'В НЗ нет средств.'
    send_message(message, message_text)


@bot.message_handler(func=lambda m: m.text == 'Зачисление средств')
def add_money(message):
    check_db(message)
    buttons = ['Просмотреть движение средств за месяц']
    keyboard = keyboards(buttons)
    send_message(message,
                 'Введите данные в формате\n<code>+Сумма Описание</code>',
                 keyboard
                 )


@bot.message_handler(func=lambda m: m.text == 'Просмотреть движение средств за месяц')
def show_money(message):
    check_db(message)
    d, m, y = current_date.strftime('%d %m %y').split()
    if 1 < int(d) < 10:
        start_date = f'{10}.{int(m) - 1}'
        end_date = f'{9}.{m}'
    else:
        start_date = f'{10}.{m}'
        end_date = f'{9}.{int(m) + 1}'
    start = datetime.strptime(f'{start_date}.22', '%d.%m.%y').date()
    end = datetime.strptime(f'{end_date}.22', '%d.%m.%y').date()
    info = db.query(f"""select date, balance, desc
                        from cash
                        where user_id = '{message.chat.id}' and 
                        date(date) between date('{start}') and date('{end}');""")
    message_text = ''
    if info is not None:
        for i in info:
            dates = '.'.join(i[0].split('-')[::-1])
            message_text += f'{dates}\nЗачислено <code>{i[1]}</code> руб.\n{i[2]}\n{"_"*23}\n'
    else:
        message_text = "Нет средств."
    send_message(message, message_text)


@bot.message_handler(func=lambda m: m.text == 'Добавить запись')
def create(message):
    check_db(message)
    send_message(message,
                 'Введите данные в формате\n<code>!Категория Наименование Количество Цена</code>',
                 )


@bot.message_handler(func=lambda m: m.text == 'Статистика')
def statistic(message):
    check_db(message)
    balance = db.query(f"select sum(balance) from cash where user_id = '{message.chat.id}';")
    total_price = db.query(f"select sum(price) from product where user_id = '{message.chat.id}';")
    bank = db.query(f"select sum(balance) from bank where user_id = '{message.chat.id}';")
    balance = check(balance)
    total_price = check(total_price)
    bank = check(bank)
    money = int(balance) - int(total_price) - int(bank)
    message_text = (
        f'На сегодня:\n'
        f'Прибыль с начала учета: <code>{balance}</code> руб.\n'
        f'Потрачено: <code>{total_price}</code> руб.\n'
        f'НЗ: <code>{bank}</code> руб.\n'
        f'Доступно средств: <code>{money}</code> руб.\n'
    )
    buttons = ['За период', 'За текущий месяц', 'За сегодня']
    keyboard = keyboards(buttons)
    send_message(message, message_text, keyboard)


@bot.message_handler(func=lambda m: m.text == 'За текущий месяц')
def stat_mount(message):
    check_db(message)
    d, m, y = current_date.strftime('%d %m %y').split()
    if 1 < int(d) < 10:
        start_date = f'{10}.{int(m) - 1}'
        end_date = f'{9}.{m}'
    else:
        start_date = f'{10}.{m}'
        end_date = f'{9}.{int(m) + 1}'
    data = mouth(start_date, end_date, message.chat.id)
    money = int(data[0]) - int(data[1]) - int(data[2])
    message_text = (
        f'За месяц с {start_date} по {end_date}:\n'
        f'Прибыль: <code>{data[0]}</code> руб.\n'
        f'Потрачено: <code>{data[1]}</code> руб.\n'
        f'НЗ: <code>{data[2]}</code> руб.\n'
        f'Доступно средств: <code>{money}</code> руб.'
    )
    send_message(message, message_text)


@bot.message_handler(func=lambda m: m.text == 'За период')
def stat_now(message):
    check_db(message)
    send_message(message,
                 'Введите период в формате:\n <code>.31.01/28.02</code>\nили один день\n <code>.31.01</code>'
                 )


@bot.message_handler(func=lambda m: m.text == 'За сегодня')
def stat_period(message):
    check_db(message)
    cash = db.query(f"select sum(balance) from cash where user_id = '{message.chat.id}' and date = '{current_date}';")
    product = db.query(f"select sum(price) from product where user_id = '{message.chat.id}' and date = '{current_date}';")
    bank = db.query(f"select balance from bank where user_id = '{message.chat.id}' and date = '{current_date}';")
    cash = check(cash)
    product = check(product)
    bank = check(bank)
    start_date = current_date.strftime('%d.%m')
    message_text = (
        f'''За {start_date}:
                Прибыль: {cash} руб.
                Потрачено: {product} руб.
                Изменения в нз: {bank} руб.
                '''
    )
    send_message(message, message_text)


@bot.message_handler(func=lambda m: m.text[0] == '.')
def period(message):
    check_db(message)
    start_end = message.text[1:].split('/')
    if len(start_end) == 2:
        start_date, end_date = start_end
        data = mouth(start_date, end_date, message.chat.id)
        message_text = (
            f'За период с {start_date} по {end_date}:\n'
            f'Прибыль: <code>{data[0]}</code> руб.\n'
            f'Потрачено: <code>{data[1]}</code> руб.\n'
            f'Изменения в НЗ: <code>{data[2]}</code> руб.\n'
        )
    else:
        start = datetime.strptime(f'{start_end[0]}.22', '%d.%m.%y').date()
        print(start)
        cash = db.query(f"select sum(balance) from cash where user_id = '{message.chat.id}' and date = '{start}';")
        product = db.query(f"select sum(price) from product where user_id = '{message.chat.id}' and date = '{start}';")
        bank = db.query(f"select balance from bank where user_id = '{message.chat.id}' and date = '{start}';")
        cash = check(cash)
        product = check(product)
        bank = check(bank)
        start_date = '.'.join(start_end[0].split('-')[-1::-1][:2])
        message_text = (
            f'''За {start_date}:
            Прибыль: {cash} руб.
            Потрачено: {product} руб.
            Изменения в нз: {bank} руб.
            '''
        )
    send_message(message, message_text)


@bot.message_handler(func=lambda m: m.text[0] == '+')
def add_balance(message):
    check_db(message)
    text = message.text[1:].split()
    text = [text[0], ' '.join(text[2:])]
    if len(text) == 2:
        summa, desc = text
        cash_id = db.query(f"SELECT MAX(cash_id) FROM cash;")[0][0]
        if cash_id is None:
            cash_id = 1
        else:
            cash_id += 1
        cash = (cash_id, summa, current_date, desc, message.chat.id)
        db.create("INSERT INTO cash VALUES (?,?,?,?,?);", cash)


@bot.message_handler(func=lambda m: m.text[0] == '!')
def new(message):
    check_db(message)
    text = message.text[1:].split()
    if len(text) == 4:
        cat, name, count, price = text
        cat_id = db.query(f"SELECT MAX(cat_id) FROM category;")[0][0]
        if cat_id is None:
            cat_id = 1
            db.create("INSERT INTO category VALUES (?,?,?);", (cat_id, cat, message.chat.id))
            create_product(cat, name, count, price, message.chat.id)
        elif db.query(f"""SELECT cat_id
                          FROM category
                          where cat_name='{cat}';""") is not None:
            create_product(cat, name, count, price, message.chat.id)
        else:
            cat_id += 1
            db.create("INSERT INTO category VALUES (?,?,?);", (cat_id, cat, message.chat.id))
            create_product(cat, name, count, price, message.chat.id)


@bot.message_handler(func=lambda m: m.text == 'Посмотреть записи')
def menu_choice(message):
    check_db(message)
    send_message(message, 'Выберите категорию:', keyboard_category(message.chat.id))


@bot.message_handler(func=lambda m: db.query(f"""SELECT *
                                                FROM category
                                                where user_id = '{m.chat.id}'
                                                and cat_name = '{m.text}';""") is not None)
def worker(message):
    check_db(message)
    total_price = db.query(
        f"""SELECT SUM(price)
           FROM product
           JOIN category ON category.cat_id=product.cat_id
           WHERE category.cat_id = (SELECT cat_id
                                    FROM category
                                    where user_id = '{message.chat.id}' and cat_name = '{message.text}');"""
    )[0][0]
    all_prod_in_cat = db.query(
        f"""SELECT DISTINCT prod_name
           FROM product
           JOIN category ON category.cat_id=product.cat_id
           WHERE category.cat_id = (SELECT cat_id
                                    FROM category
                                    where user_id = '{message.chat.id}' and cat_name = '{message.text}');"""
    )
    all_prod_in_cat = [i[0] for i in all_prod_in_cat]
    keyboard = keyboards(all_prod_in_cat)
    send_message(message, f'Всего потрачено в категории:\n<code>{total_price}</code> руб.', keyboard)


@bot.message_handler(func=lambda m: db.query(f"""SELECT *
                                                 FROM product
                                                 where user_id = '{m.chat.id}'
                                                 and prod_name = '{m.text}';""") is not None)
def show_one_product(message):
    check_db(message)
    prod = db.query(
        f"""SELECT prod_name, SUM(prod_count), SUM(price)
           FROM product
           where user_id = '{message.chat.id}' and prod_name = '{message.text}';"""
    )[0]
    showing = f'<b>{prod[0]}</b>\nКоличество: {prod[1]} шт.\nОбщая сумма: <code>{prod[2]}</code> руб.'
    send_message(message, showing, keyboard_category(message.chat.id))


bot.polling(none_stop=True, skip_pending=True)

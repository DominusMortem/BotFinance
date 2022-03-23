from telebot import types, TeleBot
import time
from datetime import date, datetime

from database import Database
from config import TELEGRAM_TOKEN

db = Database()
current_date = date.today()

bot = TeleBot(TELEGRAM_TOKEN, parse_mode='HTML')
start_buttons = ['Посмотреть записи', 'Добавить запись', 'Зачисление средств', 'Статистика', 'Вклад']


def check(arg):
    if arg is None or arg[0][0] is None:
        arg = 0
    else:
        arg = arg[0][0]
    return arg


def check_db(message):
    global db
    global current_date
    current_date = date.today()
    id_user = message.chat.id
    if db is None:
        db = Database()
        bot.send_message(id_user, '<tg-spoiler><i>Подключаю базу данных...</i></tg-spoiler>')
        time.sleep(1)
        bot.edit_message_text(
            text='<i>База успешно подключена.</i>',
            chat_id=id_user,
            message_id=message.id + 1
        )


def keyboards(args):
    """Создание клавиатуры"""
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = [types.KeyboardButton(
        f'{i}') for i in args]
    keyboard.add('В начало')
    keyboard.add(*buttons)
    return keyboard


def mouth(start, end, user_id):

    start = datetime.strptime(f'{start}.{current_date.year}', '%d.%m.%Y').date()
    end = datetime.strptime(f'{end}.{current_date.year}', '%d.%m.%Y').date()
    cash = db.query(f"""select sum(balance)
                        from cash
                        where user_id = '{user_id}' and date(date) between date('{start}') and date('{end}');""")
    product = db.query(f"""select sum(price)
                           from product
                           where user_id = '{user_id}' and date(date) between date('{start}') and date('{end}');""")
    bank = db.query(f"""select sum(balance)
                        from bank
                        where user_id = '{user_id}' and date(date) between date('{start}') and date('{end}');""")
    prod_list = db.query(f"""select prod_name, price, prod_count
                                                 from product
                                                 where user_id = '{user_id}'
                                                 and date(date) between date('{start}') and date('{end}');""")
    cash = check(cash)
    product = check(product)
    bank = check(bank)
    return cash, product, bank, prod_list


def create_product(cat, name, count, price, user_id):
    cat_id = db.query(f"SELECT cat_id FROM category where user_id = '{user_id}' and cat_name='{cat}';")[0][0]
    prod_id = db.query(f"SELECT MAX(prod_id) FROM product;")
    prod_id = check(prod_id)
    if prod_id:
        prod_id += 1
    else:
        prod_id = 1
    user = (prod_id, name, cat_id, price, count, current_date, user_id)
    db.create("INSERT INTO product VALUES (?,?,?,?,?,?,?);", user)


def keyboard_category(user_id):
    category = db.query(f"SELECT cat_name FROM category where user_id = '{user_id}';")
    if category:
        category = [i[0] for i in category]
        return keyboards(category)
    return keyboards(['Категории отсутствуют.'])


def time_now(arg=False):
    d, m, y = current_date.strftime('%d %m %y').split()
    if 1 < int(d) < 10:
        start_date = f'{10}.{int(m) - 1}'
        end_date = f'{9}.{m}'
    else:
        start_date = f'{10}.{m}'
        end_date = f'{9}.{int(m) + 1}'
    start = datetime.strptime(f'{start_date}.{y}', '%d.%m.%y').date()
    end = datetime.strptime(f'{end_date}.{y}', '%d.%m.%y').date()
    if arg:
        return start_date, end_date
    else:
        return start, end


@bot.message_handler(commands=['start'])
def start_command(message):
    keyboard = keyboards(start_buttons)
    message_start = 'Здравствуйте, я ваш финансовый помощник.\nВыберите пункт в меню, что бы начать работу.'
    bot.send_message(message.chat.id, message_start, reply_markup=keyboard)


@bot.message_handler(commands=['base'])
def open_base(message):
    """Ручной запуск базы."""
    check_db(message)


def up():
    keyboard = keyboards(start_buttons)
    message_text = 'Выберите пункт в меню, что бы начать работу.'
    return message_text, keyboard


# Работа с вкладом
# ---------------------------------------------------------------------------
def deposits():
    buttons = ['Внести', 'Снять', 'Баланс']
    keyboard = keyboards(buttons)
    message_text = 'Выберите действие'
    return message_text, keyboard


def add_deposit():
    return 'Данные в формате\n<code>*Сумма</code>', None


def deposit_add_in_db(message):
    balance = message.text[1:].split()
    if len(balance) == 1:
        bank = db.query(f"SELECT bank_id FROM bank;")

        if check(bank):
            bank_id = db.query(f"SELECT max(bank_id) FROM bank;")[0][0] + 1
            bank = (bank_id, balance[0], current_date, message.chat.id)
        else:
            bank = (1, balance[0], current_date, message.chat.id)
        db.create("INSERT INTO bank VALUES (?,?,?,?)", bank)
        return 'Успешно зачислено!', None
    return 'Некорректные данные', None


def withdraw_bank():
    return 'Данные в формате\n<code>-Сумма</code>', None


def deposit_out_db(message):
    balance = message.text[1:].split()
    if len(balance) == 1:
        bank = db.query(f"select bank_id from bank;")
        if check(bank):
            money_bank = db.query(f"SELECT sum(balance) FROM bank;")[0][0]
            if int(money_bank) >= int(balance[0]):
                bank_id = db.query(f"SELECT max(bank_id) FROM bank;")[0][0] + 1
                bank = (bank_id, f'-{balance[0]}', current_date, message.chat.id)
                db.create("INSERT INTO bank VALUES (?,?,?,?);", bank)
                message_text = 'Успешно изъято!'
            else:
                message_text = 'Средств недостаточно!'
        else:
            message_text = 'Средства отсутствуют!'
        return message_text, None
    return 'Некорректные данные', None


def show_balance(message):
    check_db(message)
    bank = db.query(f"select sum(balance) from bank where user_id = '{message.chat.id}';")
    if check(bank):
        message_text = f'Сумма на счету: <code>{bank}</code> руб.'
    else:
        message_text = 'В НЗ нет средств.'
    return message_text, None
# ---------------------------------------------------------------------------


# Поступление средств и работа с ними
# ---------------------------------------------------------------------------
def add_money(message):
    buttons = ['Просмотреть движение средств за месяц']
    info = db.query(f"""select sum(balance)
                            from cash
                            where user_id = '{message.chat.id}';""")
    message_text = 'Введите данные в формате\n<code>+Сумма Описание</code>\n\n'
    info = check(info)
    if info:
        message_text += f'<i>Средств за все время: <code>{info}</code> руб.</i>'
    keyboard = keyboards(buttons)
    return message_text, keyboard


def show_money(message):
    start, end = time_now()
    info = db.query(f"""select date, balance, desc
                        from cash
                        where user_id = '{message.chat.id}' and 
                        date(date) between date('{start}') and date('{end}');""")
    message_text = ''
    if info:
        for i in info:
            dates = '.'.join(i[0].split('-')[::-1])
            message_text += f'{dates}\nЗачислено <code>{i[1]}</code> руб.\n{i[2]}\n{"_"*23}\n'
    else:
        message_text = "Нет средств."
    return message_text, None


def add_balance(message):
    text = message.text[1:].split()
    if len(text) >= 2:
        print(text)
        text = [text[0], ' '.join(text[1:])]
        summa, desc = text
        cash_id = db.query(f"SELECT MAX(cash_id) FROM cash;")
        cash_id = check(cash_id)
        if cash_id:
            cash_id += 1
        else:
            cash_id = 1
        cash = (cash_id, summa, current_date, desc, message.chat.id)
        db.create("INSERT INTO cash VALUES (?,?,?,?,?);", cash)
        return 'Успешно!', None
    return 'Некорректные данные', None
# ---------------------------------------------------------------------------


# Статистика
# ---------------------------------------------------------------------------
def statistic(message):
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
    return message_text, keyboard


def stat_mount(message):
    start, end = time_now(True)
    data = mouth(start, end, message.chat.id)
    money = int(data[0]) - int(data[1]) - int(data[2])
    message_text = (
        f'За месяц с {start} по {end}:\n'
        f'Прибыль: <code>{data[0]}</code> руб.\n'
        f'Потрачено: <code>{data[1]}</code> руб.\n'
        f'НЗ: <code>{data[2]}</code> руб.\n'
        f'Доступно средств: <code>{money}</code> руб.'
    )
    return message_text, None


def stat_period():
    return 'Введите период в формате:\n <code>.31.01/28.02</code>\nили один день\n <code>.31.01</code>', None


def stat_show_now(message):
    cash = db.query(f"select sum(balance) from cash where user_id = '{message.chat.id}' and date = '{current_date}';")
    product = db.query(
        f"select sum(price) from product where user_id = '{message.chat.id}' and date = '{current_date}';"
    )
    bank = db.query(f"select balance from bank where user_id = '{message.chat.id}' and date = '{current_date}';")
    cash = check(cash)
    product = check(product)
    bank = check(bank)
    prod_list = db.query(f"""select prod_name, price, prod_count
                             from product
                             where user_id = '{message.chat.id}' and date = '{current_date}';""")
    start_date = current_date.strftime('%d.%m')
    message_text = (
        f'''За {start_date}:
                Прибыль: <code>{cash}</code> руб.
                Потрачено: <code>{product}</code> руб.
                Изменения в нз: <code>{bank}</code> руб.\n\n
                '''
    )
    if prod_list:
        for i in prod_list:
            message_text += f'{i[0]} - {i[1]} руб., количество - {i[2]}\n'
    return message_text, None


def stat_show_period(message):
    start_end = message.text[1:].split('/')
    if len(start_end) == 2:
        start_date, end_date = start_end
        data = mouth(start_date, end_date, message.chat.id)
        message_text = (
            f'За период с {start_date} по {end_date}:\n'
            f'Прибыль: <code>{data[0]}</code> руб.\n'
            f'Потрачено: <code>{data[1]}</code> руб.\n'
            f'Изменения в НЗ: <code>{data[2]}</code> руб.\n\n'
        )
        if data[3] is not None:
            for i in data[3]:
                message_text += f'{i[0]} - {i[1]} руб., количество - {i[2]}\n'
    else:
        start = datetime.strptime(f'{start_end[0]}.{current_date.year}', '%d.%m.%Y').date()
        cash = db.query(f"select sum(balance) from cash where user_id = '{message.chat.id}' and date = '{start}';")
        product = db.query(f"select sum(price) from product where user_id = '{message.chat.id}' and date = '{start}';")
        bank = db.query(f"select balance from bank where user_id = '{message.chat.id}' and date = '{start}';")
        cash = check(cash)
        product = check(product)
        bank = check(bank)
        start_date = '.'.join(start_end[0].split('-')[-1::-1][:2])
        prod_list = db.query(f"""select prod_name, price, prod_count
                                     from product
                                     where user_id = '{message.chat.id}' and date = '{start}';""")
        message_text = (
            f'За {start_date}:\n'
            f'    Прибыль: <code>{cash}</code> руб.\n'
            f'    Потрачено: <code>{product}</code> руб.\n'
            f'    Изменения в нз: <code>{bank}</code> руб.\n\n'
        )

        if prod_list:
            for i in prod_list:
                message_text += f'{i[0]} - {i[1]} руб., количество - {i[2]}\n'
    return message_text, None
# ---------------------------------------------------------------------------


# Работа с записью информации в базу данных
# ---------------------------------------------------------------------------
def create():
    return 'Введите данные в формате\n<code>!Категория Наименование Количество Цена</code>', None


def new(message):
    text = message.text[1:].split()
    if len(text) == 4:
        cat, name, count, price = text
        cat_id = db.query(f"SELECT MAX(cat_id) FROM category;")
        cat_id = check(cat_id)
        print(db.query(f"""SELECT cat_id
                          FROM category
                          where cat_name='{cat}';"""))
        if db.query(f"""SELECT cat_id
                          FROM category
                          where cat_name='{cat}';"""):
            print('Категория есть')
            create_product(cat, name, count, price, message.chat.id)
        elif cat_id:
            cat_id += 1
            db.create("INSERT INTO category VALUES (?,?,?);", (cat_id, cat, message.chat.id))
            create_product(cat, name, count, price, message.chat.id)
        else:
            cat_id = 1
            db.create("INSERT INTO category VALUES (?,?,?);", (cat_id, cat, message.chat.id))
            create_product(cat, name, count, price, message.chat.id)
        return 'Успешно!', None
    return 'Некорректные данные', None
# ---------------------------------------------------------------------------


# Посмотреть записи
# ---------------------------------------------------------------------------
def menu_choice(message):
    return 'Выберите категорию:', keyboard_category(message.chat.id)


def select_category(message):
    start, end = time_now()
    total_price = db.query(
        f"""SELECT SUM(price)
           FROM product
           JOIN category ON category.cat_id=product.cat_id
           WHERE category.cat_id = (SELECT cat_id
                                    FROM category
                                    WHERE user_id = '{message.chat.id}'
                                    AND cat_name = '{message.text}');"""
    )
    total_price_mouth = db.query(
        f"""SELECT SUM(price)
               FROM product
               JOIN category ON category.cat_id=product.cat_id
               WHERE date(date) between date('{start}') and date('{end}')
               AND category.cat_id = (SELECT cat_id
                                        FROM category
                                        WHERE user_id = '{message.chat.id}'
                                        AND cat_name = '{message.text}');"""
    )
    all_prod_in_cat = db.query(
        f"""SELECT DISTINCT prod_name
           FROM product
           JOIN category ON category.cat_id=product.cat_id
           WHERE category.cat_id = (SELECT cat_id
                                    FROM category
                                    WHERE user_id = '{message.chat.id}'
                                    AND cat_name = '{message.text}');"""
    )
    total_price_mouth = check(total_price_mouth)
    keyboard = None
    message_text = ''
    if all(total_price):
        total_price = total_price[0][0]
        message_text += f'Всего потрачено в категории:\n<code>{total_price}</code> руб.\n'
        message_text += f'За месяц: <code>{total_price_mouth}</code> руб.'
    if all(all_prod_in_cat):
        all_prod_in_cat = [i[0] for i in all_prod_in_cat]
        keyboard = keyboards(all_prod_in_cat)
    return message_text, keyboard


def show_one_product(message):
    check_db(message)
    start, end = time_now()
    prod = db.query(
        f"""SELECT prod_name, SUM(prod_count), SUM(price)
           FROM product
           where user_id = '{message.chat.id}' and prod_name = '{message.text}';"""
    )
    prod_mouth = db.query(
        f"""SELECT prod_name, SUM(prod_count), SUM(price)
           FROM product
           where user_id = '{message.chat.id}' and prod_name = '{message.text}'
           and date(date) between date('{start}') and date('{end}');"""
    )
    message_text = ''
    if all(prod):
        message_text += (f'<b>{prod[0][0]}</b>\nКоличество: {prod[0][1]} шт.\n'
                         f'Общая сумма: <code>{prod[0][2]}</code> руб.\n')
    if all(prod_mouth):
        message_text += (f'<b>За месяц:</b>\nКоличество: {prod_mouth[0][1]} шт.\n'
                         f'Общая сумма: <code>{prod_mouth[0][2]}</code> руб.')
    return message_text, keyboard_category(message.chat.id)
# ---------------------------------------------------------------------------


dict_func = {
    'В начало': lambda _: up(),
    'Вклад': lambda _: deposits(),
    'Внести': lambda _: add_deposit(),
    '*': deposit_add_in_db,
    'Снять': lambda _: withdraw_bank(),
    '-': deposit_out_db,
    'Баланс': show_balance,
    'Зачисление средств': add_money,
    'Просмотреть движение средств за месяц': show_money,
    '+': add_balance,
    'Статистика': statistic,
    'За текущий месяц': stat_mount,
    'За период': lambda _: stat_period(),
    'За сегодня': stat_show_now,
    '.': stat_show_period,
    'Добавить запись': lambda _: create(),
    '!': new,
    'Посмотреть записи': menu_choice
}


@bot.message_handler(content_types=['text'])
def main(message):
    check_db(message)
    key = message.text
    if key[0] in '*-+.!':
        key = key[0]
    if key in dict_func:
        message_text, keyboard = dict_func.get(key)(message)
    category = db.query(f"""SELECT *
                            FROM category
                            WHERE user_id = '{message.chat.id}'
                            AND cat_name = '{message.text}';""")
    if category:
        message_text, keyboard = select_category(message)
    product = db.query(f"""SELECT *
                           FROM product
                           WHERE user_id = '{message.chat.id}'
                           AND prod_name = '{message.text}';""")
    if product:
        message_text, keyboard = show_one_product(message)
    bot.send_message(message.chat.id, message_text, reply_markup=keyboard)


bot.polling(none_stop=True, skip_pending=True)

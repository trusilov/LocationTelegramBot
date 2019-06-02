import telebot
import static
from telebot import types
from peewee import *

TOKEN = static.T
bot = telebot.TeleBot(TOKEN)

db = SqliteDatabase('telegram.db')


class User(Model):
    id = PrimaryKeyField(null=False)
    telegram_id = IntegerField(null=False, unique=True)
    name = CharField(max_length=50, null=True)
    first_name = CharField(max_length=50, null=True)
    last_name = CharField(max_length=50, null=True)
    longitude = FloatField()
    latitude = FloatField()

    class Meta:
        database = db


@bot.message_handler(commands=['start'])
def welcome(message):
    """bot welcome message and start keyboard markup """
    bot.send_message(message.chat.id, text='Hello, I am is LocationBot', )
    keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn_send = types.KeyboardButton(text='Send Location', request_location=True)
    btn_get = types.KeyboardButton(text='Get Location')
    keyboard.add(btn_send, btn_get)
    bot.send_message(message.chat.id, "Choose", reply_markup=keyboard)


@bot.message_handler(commands=['help'])
def help(message):
    help_text = 'U can see last location, if u friend exist in database'
    bot.send_message(message.chat.id, text=help_text)


def initialize():
    """create table if not exist"""
    db.connect()
    db.create_tables([User], safe=True)


@bot.message_handler(content_types=['location'])
def location(message):
    """send location and add data in database"""
    if message.location is not None:
        bot.send_message(message.chat.id, text='I put your location in the database.')
        bot.send_message(message.chat.id, text='Your TelegramID: %d' % message.from_user.id)

        try:
            User.create(telegram_id=message.from_user.id,
                        name=message.from_user.username,
                        first_name=message.from_user.first_name,
                        last_name=message.from_user.last_name,
                        longitude=message.location.longitude,
                        latitude=message.location.latitude)
        except IntegrityError:
            user_record = User.get(telegram_id=message.from_user.id)
            user_record.name = message.from_user.username
            user_record.first_name = message.from_user.first_name
            user_record.last_name = message.from_user.last_name
            user_record.longitude = message.location.longitude
            user_record.latitude = message.location.latitude

            user_record.save()


@bot.message_handler(content_types=['text'])
def get_location_btn(message):
    """get location button"""
    if 'Get Location' in message.text:
        bot.send_message(message.chat.id, text='Send TelegramID')
        bot.register_next_step_handler(message, get_location)
    else:
        bot.send_message(message.chat.id, text='Send or Get Location')


def get_location(message):
    """select location from database"""
    users_id = message.text
    try:
        query = (User
                 .select(User.telegram_id,
                         User.name,
                         User.first_name,
                         User.last_name,
                         User.latitude,
                         User.longitude)
                 .where(User.telegram_id == users_id))

        for m in query:
            bot.send_message(message.chat.id, text='Username : %s \n'
                                                   'Name: %s %s \n'
                                                   'Latitude: %F \n'
                                                   'Longitude: %F \n'
                                                   % (m.name,
                                                      m.first_name, m.last_name,
                                                      m.latitude,
                                                      m.longitude))
            bot.send_message(message.chat.id, text='LAST LOCATION: ')
            bot.send_location(message.chat.id, m.latitude, m.longitude)

    except ValueError:
        bot.send_message(message.chat.id, text='ENTER NORMAL TELEGRAMID, IDIOT')


if __name__ == '__main__':
    initialize()

bot.polling(timeout=0)

import telebot
import os
from telebot import types
from database import get_db
from sqlalchemy.exc import SQLAlchemyError
from models import Tag, Url

TOKEN = os.getenv("BOTTOKEN")
bot = telebot.TeleBot(TOKEN)

# Dictionary to save the state of each user
user_states = {}

# /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
	chat_id = message.chat.id
	# Restart data of the conversation
	user_states[chat_id] = {'step': 'ask_db'}
	bot.send_message(chat_id, "Bienvenide a la extension CatS, ¿Cuál es el token de tu comunidad?")

# token reseption
@bot.message_handler(func=lambda message: user_states.get(message.chat.id, {}).get('step') == 'ask_db')
def set_db(message):
    chat_id = message.chat.id
    db_token = message.text.strip()  # en este ejemplo usamos el token como string
    user_states[chat_id]['db'] = db_token
    # Aquí podrías, si lo deseas, validar el token o decidir qué conexión usar.
    user_states[chat_id]['step'] = 'choose_table'
    
    # keyboard with options to choose the next action
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    btn_tag = types.KeyboardButton("Agregar tag")
    btn_url = types.KeyboardButton("Agregar url")
    markup.add(btn_tag, btn_url)
    
    bot.send_message(chat_id, "¿Qué deseas hacer?", reply_markup=markup)

# election reseption
@bot.message_handler(func=lambda message: user_states.get(message.chat.id, {}).get('step') == 'choose_table')
def choose_table(message):
    chat_id = message.chat.id
    text = message.text.lower()
    if "tag" in text:
        user_states[chat_id]['table'] = 'tag'
        user_states[chat_id]['step'] = 'fill_tag'
        bot.send_message(chat_id, "Ingresa el nombre del tag:")
        ####3 PEDIR ACTION Y DESCRIPCION ##
    elif "url" in text:
        user_states[chat_id]['table'] = 'url'
        user_states[chat_id]['step'] = 'fill_url'
        bot.send_message(chat_id, "Ingresa la dirección de la URL:")
    else:
        bot.send_message(chat_id, "Opción no válida. Por favor selecciona 'Agregar tag' o 'Agregar url'.")

# fill tag
@bot.message_handler(func=lambda message: user_states.get(message.chat.id, {}).get('step') == 'fill_tag')
def fill_tag(message):
    chat_id = message.chat.id
    tag_name = message.text.strip()
    # validar -----------
    
	# save in db
    try:
        # CAMBIAR A MULTIPLES DB
        db_gen = get_db() 
        db = next(db_gen)
        
        new_tag = Tag(name=tag_name) # AGREGAR DATOS FALTANTES
        db.add(new_tag)
        db.commit()
        bot.send_message(chat_id, f"Tag '{tag_name}' agregado correctamente.")
    except SQLAlchemyError as e:
        bot.send_message(chat_id, f"Ocurrió un error al guardar el tag: {str(e)}")
    finally:
        # restart state
        user_states.pop(chat_id, None)
        
@bot.message_handler(func=lambda message: user_states.get(message.chat.id, {}).get('step') == 'fill_url')
def fill_url(message):
    chat_id = message.chat.id
    url_address = message.text.strip()
    # validar -----------
    
	# save in db
    try:
        # CAMBIAR A MULTIPLES DB
        db_gen = get_db()
        db = next(db_gen)

        new_url = Url(address=url_address)  # AGREGAR DATOS FALTANTES
        db.add(new_url)
        db.commit()
        bot.send_message(chat_id, f"URL '{url_address}' agregada correctamente.")
    except SQLAlchemyError as e:
        bot.send_message(chat_id, f"Ocurrió un error al guardar la url: {str(e)}")
    finally:
        # restart state
        user_states.pop(chat_id, None)
        	
# chat init
bot.polling()  
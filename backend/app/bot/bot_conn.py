import telebot
import os
from telebot import types
from datetime import datetime
from app.database import get_db
from sqlalchemy.exc import SQLAlchemyError
from app.models import Community, Tag, Url

# Bot setup
TOKEN = os.getenv("BOTTOKEN")
bot = telebot.TeleBot(TOKEN)
print(TOKEN)
# Default server IP (for all communities)
IPSERVER = os.getenv("SERVER_IP")
print(IPSERVER)
# Dictionary to save the state per chat
user_states = {}
# Fuction to show the action menu (create tag or add url)
def show_action_menu(chat_id, community):
    """
    Send appropriate menu: if no tags, ask to create one, else, ask create tag or add URL
    """
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    if not community.tags:  # Asumiendo que `community` tiene un atributo `tags`
        markup.add(types.KeyboardButton("Crear tag"))
        bot.send_message(chat_id, "No hay tags creados. ¿Deseas crear un tag?", reply_markup=markup)
    else:
        markup.add(types.KeyboardButton("Crear tag"), types.KeyboardButton("Agregar URL"))
        bot.send_message(chat_id, "¿Qué deseas hacer?", reply_markup=markup)
    user_states[chat_id] = {'step': 'choose_action'}

"""
@bot.message_handler(func=lambda message: bot.get_me().username in message.text)
def handle_mention(message):
    bot.reply_to(message, "Hola, escribe /start para configurar tu comunidad 😊")
"""


# /start handler
@bot.message_handler(commands=['start'])
def handle_start(message):
    chat = message.chat
    chat_id = chat.id
    print(chat_id)
    # Only operate in group chats
    if chat.type not in ['group', 'supergroup']:
        bot.send_message(chat_id, "Este bot solo funciona en chats grupales.")
        return

    # Initialize or retrieve community
    db = next(get_db())
    #community = db.query(Community).filter_by(id=chat_id).first()
    community = None
    if community is None:
        # Preguntar nombre de comunidad
        user_states[chat_id] = {'step': 'ask_name'}
        print(user_states)
        bot.send_message(chat_id, "¡Hola! Primero, ingresa el nombre de la comunidad a registrar:")
    else:
        # Mostrar menú de acciones
        show_action_menu(chat_id, community)


# Name reseption
@bot.message_handler(func=lambda m: user_states.get(m.chat.id, {}).get('step') == 'ask_name')
def handle_name(message):
    chat_id = message.chat.id
    name = message.text.strip()
    user_states[chat_id] = {'step': 'ask_description', 'name': name}
    print(f"Estado actualizado a 'ask_description' para {chat_id}. Nombre: {name}") 
    bot.send_message(chat_id, "Ahora ingresa una descripción para la comunidad:")


# Descripton reseption and community creation
@bot.message_handler(func=lambda m: user_states.get(m.chat.id, {}).get('step') == 'ask_description')
def handle_description(message):
    chat_id = message.chat.id
    description = message.text.strip()
    name = user_states.get(chat_id, {}).get('name')
    try:
        db = next(get_db())
        community = Community(
            id=chat_id,
            name=name,
            ip=IPSERVER, # eliminar -------------------------------------
            description=description,
            total_followers =0,  # reformular --------------- investigar tools para estadisticas fuera de la db
            created_date=datetime.utcnow()
        )
        db.add(community)
        db.commit()
        bot.send_message(chat_id, f"Comunidad '{name}' registrada correctamente.")
    except SQLAlchemyError as e:
        bot.send_message(chat_id, f"Error al crear la comunidad: {e}")
    finally:
        # Limpiar estado y mostrar menú
        user_states.pop(chat_id, None)
        db = next(get_db())
        community = db.query(Community).filter_by(id=chat_id).first()
        show_action_menu(chat_id, community)


# Action choise
@bot.message_handler(func=lambda m: user_states.get(m.chat.id, {}).get('step') == 'choose_action')
def handle_choice(message):
    chat_id = message.chat.id
    text = message.text.lower()
    if 'tag' in text:
        user_states[chat_id] = {'step': 'fill_tag'}
        bot.send_message(chat_id, "Ingresa el nombre del tag:")
        ## PEDIR ACCION Y DESCRIPTCION
    elif 'url' in text:
        user_states[chat_id] = {'step': 'fill_url'}
        bot.send_message(chat_id, "Ingresa la dirección de la URL:")
    else:
        bot.send_message(chat_id, "Opción no válida. Elige 'Crear tag' o 'Agregar URL'.")


# -- FILL TAG --
# -> tag name
@bot.message_handler(func=lambda m: user_states.get(m.chat.id, {}).get('step') == 'fill_tag_name')
def handle_fill_tag_name(message):
    chat_id = message.chat.id
    tag_name = message.text.strip()
    user_states[chat_id] = {'step': 'fill_tag_action', 'tag_name':tag_name}
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add('block', 'alert', 'notification')
    bot.send_message(chat_id, "Selecciona la acción del tag (block / alert / notification):", reply_markup=markup)

# -> tag action
@bot.message_handler(func=lambda m: user_states.get(m.chat.id, {}).get('step') == 'fill_tag_action')
def handle_fill_tag_action(message):
    chat_id = message.chat.id
    state = user_states.get(chat_id, {})
    action = message.text.strip().lower()
    tag_name = state.get('tag_name')    
    try:
        db = next(get_db())
        community = db.query(Community).filter_by(id=chat_id).first()
        new_tag = Tag(name=tag_name, action=action, community_id=community.id)
        db.add(new_tag)
        db.commit()
        bot.send_message(chat_id, f"Tag '{tag_name}' con acción '{action}' agregado a '{community.name}'.")
    except SQLAlchemyError as e:
        bot.send_message(chat_id, f"Error al guardar el tag: {e}")
    finally:
        user_states.pop(chat_id, None)
        show_action_menu(chat_id, community)


# -- FILL URL --
# -> url address
@bot.message_handler(func=lambda m: user_states.get(m.chat.id, {}).get('step') == 'fill_url_address')
def handle_fill_url_address(message):
    chat_id = message.chat.id
    user_states[chat_id] = {'step': 'fill_url_justification', 'url': message.text.strip()}
    bot.send_message(chat_id, "Ingresa una justificación para esta URL:")

# -> url justification
@bot.message_handler(func=lambda m: user_states.get(m.chat.id, {}).get('step') == 'fill_url_justification')
def handle_fill_url_justification(message):
    chat_id = message.chat.id
    state = user_states.get(chat_id, {})
    url_address = state.get('url')
    justification = message.text.strip()
    try:
        db = next(get_db())
        community = db.query(Community).filter_by(id=chat_id).first()
        new_url = Url(address=url_address, justification=justification, community_id=community.id)
        db.add(new_url); db.commit()
        bot.send_message(chat_id, f"URL '{url_address}' agregada con justificación.")
    except SQLAlchemyError as e:
        bot.send_message(chat_id, f"Error guardando URL: {e}")
    finally:
        user_states.pop(chat_id, None)
        show_action_menu(chat_id, community)

print(user_states)
# Inicia polling
if __name__ == '__main__':
    bot.polling(none_stop=True)
    print(user_states)
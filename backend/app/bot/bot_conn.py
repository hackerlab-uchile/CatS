import telebot
import os
from telebot import types
from datetime import datetime
from app.database import get_db
from sqlalchemy.exc import SQLAlchemyError
from app.models import Community, Tag, Url
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Bot setup
TOKEN = os.getenv("BOTTOKEN")
bot = telebot.TeleBot(TOKEN)

# Default server IP (for all communities)
IPSERVER = os.getenv("SERVER_IP")

# Dictionary to save the state per chat
user_states = {}

# Fuction to show the action menu (create tag or add url)
def show_action_menu(chat_id, db):
    """
    Send appropriate menu: if no tags, ask to create one, else, ask create tag or add URL
    """
    markup = InlineKeyboardMarkup()
    tag = db.query(Tag).filter_by(community_id=chat_id).first() 

    if tag is None:
        markup.add(InlineKeyboardButton("Crear tag", callback_data=f"action_create_tag"))
        bot.send_message(chat_id, "No hay tags creados. ¿Deseas crear un tag?", reply_markup=markup)
    else:
        markup.add(
            InlineKeyboardButton("Crear tag", callback_data="action_create_tag"),
            InlineKeyboardButton("Agregar URL", callback_data="action_add_url")
        )        
        bot.send_message(chat_id, "¿Qué deseas hacer?", reply_markup=markup)
    user_states[chat_id] = {'step': 'choose_action'}


@bot.message_handler(func=lambda message: bot.get_me().username in message.text)
def handle_mention(message):
    bot.reply_to(message, "Hola, escribe /start para configurar tu comunidad 😊")


# /start handler
@bot.message_handler(commands=['start'])
def handle_start(message):
    chat = message.chat
    chat_id = chat.id
    
    # Only operate in group chats
    if chat.type not in ['group', 'supergroup']:
        bot.send_message(chat_id, "Este bot solo funciona en chats grupales.")
        return

    # Initialize or retrieve community
    db = next(get_db())
    community = db.query(Community).filter_by(id=chat_id).first()
    if community is None:
        # Ask community name
        user_states[chat_id] = {'step': 'ask_name'}
        print(user_states)
        bot.send_message(chat_id, "¡Hola! Primero, ingresa el nombre de la comunidad a registrar:")
    else:
        # show action menu
        show_action_menu(chat_id, db)


# Name reseption and ask for community description
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
            description=description,
            created_date=datetime.utcnow()
        )
        db.add(community)
        db.commit()
        bot.send_message(chat_id, f"Comunidad '{name}' registrada correctamente.")
    except SQLAlchemyError as e:
        bot.send_message(chat_id, f"Error al crear la comunidad: {e}")
    finally:
        # Clean state and show menu action
        user_states.pop(chat_id, None)
        db = next(get_db())
        show_action_menu(chat_id, db)


# Action choise
@bot.callback_query_handler(func=lambda call: call.data.startswith("action_"))
def handle_action_menu(call):
    chat_id = call.message.chat.id
    action = call.data
    bot.delete_message(chat_id, call.message.message_id)

    if action == "action_create_tag":
        user_states[chat_id] = {'step': 'fill_tag'}
        bot.send_message(chat_id, "Ingresa el nombre del nuevo tag:")
    else:
        user_states[chat_id] = {'step': 'fill_url'}
        bot.send_message(chat_id, "Ingresa la dirección de la URL que deseas agregar:")

# -- FILL TAG --
# -> get tag name and ask tag description
@bot.message_handler(func=lambda m: user_states.get(m.chat.id, {}).get('step') == 'fill_tag')
def handle_fill_tag_name(message):
    chat_id = message.chat.id
    tag_name = message.text.strip()
    user_states[chat_id] = {'step': 'fill_tag_description', 'tag_name':tag_name}
    bot.send_message(chat_id, "Ingresa una descripción para el Tag:")

# -> get tag description and ask action of the tag
@bot.message_handler(func=lambda m: user_states.get(m.chat.id, {}).get('step') == 'fill_tag_description')
def handle_fill_tag_description(message):
    chat_id = message.chat.id
    tag_description = message.text.strip()
    state = user_states.get(chat_id, {})
    tag_name = state.get('tag_name')

    user_states[chat_id] = {'step': 'fill_tag_action', 'tag_name':tag_name, 'tag_description': tag_description}

    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("🔒 Block", callback_data="tag_action_block"),
        InlineKeyboardButton("⚠️ Alert", callback_data="tag_action_alert"),
        InlineKeyboardButton("🔔 Notification", callback_data="tag_action_notification")
    )
    bot.send_message(chat_id, "Selecciona la acción del tag:", reply_markup=markup)

# -> get tag action and add tag to database
@bot.callback_query_handler(func=lambda call: call.data.startswith("tag_action_"))
def handle_tag_action_selection(call):
    chat_id = call.message.chat.id
    state = user_states.get(chat_id, {})
    tag_name = state.get('tag_name')    
    tag_description = state.get('tag_description') 
    action = call.data.replace("tag_action_","")
    bot.delete_message(chat_id, call.message.message_id)

    try:
        db = next(get_db())
        community = db.query(Community).filter_by(id=chat_id).first()
        new_tag = Tag(name=tag_name, action=action, description=tag_description, community_id=community.id)
        db.add(new_tag)
        db.commit()
        bot.send_message(chat_id, f"Tag '{tag_name}' con acción '{action}' agregado a '{community.name}'.")
    except SQLAlchemyError as e:
        bot.send_message(chat_id, f"Error al guardar el tag: {e}")
    finally:
        user_states.pop(chat_id, None)
        show_action_menu(chat_id, db)


# Function that page existing tags
TAGS_PER_PAGE = 3

def show_tag_buttons(chat_id, page=0):
    db = next(get_db())
    tags = db.query(Tag).filter_by(community_id=chat_id).all()
    start = page * TAGS_PER_PAGE
    end = start + TAGS_PER_PAGE
    page_tags = tags[start:end]

    markup = InlineKeyboardMarkup()
    for tag in page_tags:
        markup.add(InlineKeyboardButton(tag.name, callback_data=f"select_tag:{tag.name}"))

    # Page layout
    nav_buttons = []
    if start > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Anterior", callback_data=f"page:{page-1}"))
    if end < len(tags):
        nav_buttons.append(InlineKeyboardButton("Siguiente ➡️", callback_data=f"page:{page+1}"))

    if nav_buttons:
        markup.row(*nav_buttons)

    bot.send_message(chat_id, "Selecciona un tag para esta URL:", reply_markup=markup)

# Manage the page layout
@bot.callback_query_handler(func=lambda call: call.data.startswith("page:"))
def handle_page_navigation(call):
    chat_id = call.message.chat.id
    page = int(call.data.split(":")[1])

    # Delete the previous message with buttons before sending the new message
    bot.delete_message(chat_id, call.message.message_id)

    # Muestra la siguiente página
    show_tag_buttons(chat_id, page=page)


# -- FILL URL --
# -> url address
@bot.message_handler(func=lambda m: user_states.get(m.chat.id, {}).get('step') == 'fill_url')
def handle_fill_url_address(message):
    chat_id = message.chat.id
    url = message.text.strip()
    user_states[chat_id] = {'step': 'fill_url_tag', 'url': url}
    show_tag_buttons(chat_id, page=0)


@bot.callback_query_handler(func=lambda call: call.data.startswith("select_tag:"))
def handle_tag_selection(call):
    chat_id = call.message.chat.id
    tag_name = call.data.split(":")[1]
    
    # Guarda el tag en el estado
    state = user_states.get(chat_id, {})
    url = state.get('url')
    user_states[chat_id] = {'step': 'fill_url_justification', 'url': url, 'tag': tag_name}

    # Borra el mensaje con los botones para evitar confusión
    bot.delete_message(chat_id, call.message.message_id)

    bot.send_message(chat_id, f"Seleccionaste el tag '{tag_name}'. Ahora ingresa una justificación para esta URL:")


# -> url justification
@bot.message_handler(func=lambda m: user_states.get(m.chat.id, {}).get('step') == 'fill_url_justification')
def handle_fill_url_justification(message):
    chat_id = message.chat.id
    state = user_states.get(chat_id, {})
    url_address = state.get('url')
    url_tag =  state.get('tag')
    justification = message.text.strip()
    try:
        db = next(get_db())
        tag = db.query(Tag).filter_by(name=url_tag, community_id=chat_id).first()
        community = db.query(Community).filter_by(id=chat_id).first()
        new_url = Url(url=url_address, justification=justification, community_id=community.id, tag_id=tag.id)
        db.add(new_url); db.commit()
        bot.send_message(chat_id, f"URL '{url_address}' agregada!")
    except SQLAlchemyError as e:
        bot.send_message(chat_id, f"Error guardando URL: {e}")
    finally:
        user_states.pop(chat_id, None)
        show_action_menu(chat_id, db)

print(user_states)
# Inicia polling
if __name__ == '__main__':
    bot.polling(none_stop=True)
    print(user_states)
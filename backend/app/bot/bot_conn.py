import telebot
import os
from app.database import get_db
from app.models import Community, Tag, Url
from app.bot.utils import is_valid_url, is_valid_name
from sqlalchemy.exc import SQLAlchemyError
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Bot setup
TOKEN = os.getenv("BOTTOKEN")
bot = telebot.TeleBot(TOKEN)

# Default server IP (for all communities)
IPSERVER = os.getenv("SERVER_IP")

# Length name fields
LENNAMES = int(os.getenv("LENNAMES"))
LENDESC = int(os.getenv("LENDESC"))

# Function that page existing tags
TAGS_PER_PAGE = 3

# Dictionary to save the state per chat
user_states = {}

# Fuction to show the action menu (create tag or add url)
def show_action_menu(chat_id, db):
    """
    Send a menu appropriate to the chat conditions
    """
    markup = InlineKeyboardMarkup()
    tag = db.query(Tag).filter_by(community_id=chat_id).first() 
    url = db.query(Url).filter_by(community_id=chat_id).first() 
    community = db.query(Community).filter_by(id=chat_id).first() 
    if community is None:
        user_states[chat_id] = {'step': 'ask_name'}
        bot.send_message(chat_id, "No existe una comunidad asociada a este chat, ingresa el nombre de la comunidad a registrar:")
    elif tag is None:
        markup.add(
            InlineKeyboardButton("Crear tag", callback_data=f"action_create_tag"),
            InlineKeyboardButton("No, Eliminar Comunidad", callback_data="confirm_delete_community")
            )
        bot.send_message(chat_id, "No hay tags creados. ¿Deseas crear un tag?", reply_markup=markup)
    elif url is None:
        markup.add(
            InlineKeyboardButton("Crear tag", callback_data="action_create_tag"),
            InlineKeyboardButton("Eliminar Tag", callback_data="confirm_delete_tag"),
            InlineKeyboardButton("Agregar URL", callback_data="action_add_url"),
            InlineKeyboardButton("Eliminar Comunidad", callback_data="confirm_delete_community")
        )        
        bot.send_message(chat_id, "¿Qué deseas hacer?", reply_markup=markup)
    else:
        markup.add(
            InlineKeyboardButton("Crear tag", callback_data="action_create_tag"),
            InlineKeyboardButton("Eliminar Tag", callback_data="confirm_delete_tag"),
            InlineKeyboardButton("Agregar URL", callback_data="action_add_url"),
            InlineKeyboardButton("Ver/Editar URLs", callback_data="manage_urls"),
            InlineKeyboardButton("Eliminar Comunidad", callback_data="confirm_delete_community")
        )        
        bot.send_message(chat_id, "¿Qué deseas hacer?", reply_markup=markup)


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

    if not is_valid_name(name, LENNAMES):
        bot.send_message(chat_id, f"Nombre inválido, ingresa un nombre válido y de máximo {LENNAMES} carácteres.")
        bot.send_message(chat_id, "Ingresa el nombre de la comunidad a registrar:")
        user_states[chat_id] = {'step': 'ask_name'}
    else:
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
            description=description
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

    if not is_valid_name(tag_name, LENNAMES):
        bot.send_message(chat_id, f"⚠️ Nombre inválido, ingresa un nombre válido y de máximo {LENNAMES} carácteres.")
        bot.send_message(chat_id, "Ingresa el nombre del nuevo Tag:")
        user_states[chat_id] = {'step': 'fill_tag'}
    else:
        # check if exits a tag with that name in this community
        db = next(get_db())
        existing_tag = db.query(Tag).filter_by(name=tag_name, community_id=chat_id).first()
        if existing_tag:
            bot.send_message(chat_id, f"⚠️ Ya existe un tag llamado '{tag_name}' en esta comunidad. Por favor ingresa otro nombre para el tag:")
            user_states[chat_id] = {'step': 'fill_tag'}
        else:
            user_states[chat_id] = {'step': 'fill_tag_description', 'tag_name':tag_name}
            bot.send_message(chat_id, "Ingresa una descripción para el Tag:")

# -> get tag description and ask action of the tag
@bot.message_handler(func=lambda m: user_states.get(m.chat.id, {}).get('step') == 'fill_tag_description')
def handle_fill_tag_description(message):
    chat_id = message.chat.id
    tag_description = message.text.strip()
    state = user_states.get(chat_id, {})
    tag_name = state.get('tag_name')

    if not is_valid_name(tag_description, LENDESC):
        bot.send_message(chat_id, f"⚠️ Descripción inválida, ingresa una descripción válida y de máximo {LENNAMES} carácteres.")
        bot.send_message(chat_id, "Ingresa una descripción para el Tag:")
        user_states[chat_id] = {'step': 'fill_tag_description', 'tag_name':tag_name}
    else:

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

    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url

    if not is_valid_url(url):
        bot.send_message(chat_id, "🚫 La URL ingresada no es válida o es privada. Intenta con una dirección como `https://ejemplo.com`.")
        bot.send_message(chat_id, "Ingresa la dirección de la URL que deseas agregar:")
        user_states[chat_id] = {'step': 'fill_url'}
        
    else:
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

    if not is_valid_name(justification, LENDESC):
        bot.send_message(chat_id, f"⚠️ Justificación inválida, ingresa una justificación válida y de máximo {LENNAMES} carácteres.")
        bot.send_message(chat_id, "Ingresa una justificación para la URL:")
        user_states[chat_id] = {'step': 'fill_url_justification', 'url': url_address, 'tag': url_tag}
    else:
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


# -- EDIT URL --
@bot.callback_query_handler(func=lambda call: call.data == "manage_urls")
def handle_manage_urls(call):
    chat_id = call.message.chat.id
    db = next(get_db())
    urls = db.query(Url).filter_by(community_id=chat_id).limit(10).all()

    for url in urls:
        text = f"🌐 URL: {url.url}\n Justificación: {url.justification}\n Tag ID: {url.tag_id}"
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("✏️ Editar", callback_data=f"edit_url_{url.id}"),
            InlineKeyboardButton("🗑️ Eliminar", callback_data=f"delete_url_{url.id}")
        )
        bot.send_message(chat_id, text, reply_markup=markup)

    bot.answer_callback_query(call.id)

# Action buttons for edit url
@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_url_"))
def show_url_edit_actions(call):
    url_id = int(call.data.split("_")[-1])
    chat_id = call.message.chat.id
    
    # Delete the previous message with buttons before sending the new message
    bot.delete_message(chat_id, call.message.message_id)
    
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("✏️ Editar justificación", callback_data=f"edit_just_{url_id}"),
        InlineKeyboardButton("🔁 Cambiar tag", callback_data=f"edit_tag_{url_id}")
    )
    bot.send_message(chat_id, f"¿Qué deseas hacer con la URL ID {url_id}?", reply_markup=markup)
    bot.answer_callback_query(call.id)

# Edit Justification url
@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_just_"))
def edit_url_justification(call):
    url_id = int(call.data.split("_")[-1])
    chat_id = call.message.chat.id
    user_states[chat_id] = {'step': 'editing_just', 'url_id': url_id}
    bot.send_message(chat_id, "Escribe la nueva justificación:")


@bot.message_handler(func=lambda m: user_states.get(m.chat.id, {}).get('step') == 'editing_just')
def save_new_justification(message):
    chat_id = message.chat.id
    new_just = message.text.strip()
    url_id = user_states[chat_id]['url_id']

    if not is_valid_name(new_just, LENDESC):
        bot.send_message(chat_id, f"⚠️ Justificación inválida, ingresa una justificación válida y de máximo {LENNAMES} carácteres.")
        bot.send_message(chat_id, "Ingresa una justificación para la URL:")
        user_states[chat_id] = {'step': 'editing_just', 'url_id': url_id}
    else:
        try:
            db = next(get_db())
            url_entry = db.query(Url).filter_by(id=url_id).first()
            url_entry.justification = new_just
            db.commit()
            bot.send_message(chat_id, "Justificación actualizada correctamente.")
        except SQLAlchemyError as e:
            bot.send_message(chat_id, f"Error al actualizar: {e}")
        finally:
            user_states.pop(chat_id, None)
            show_action_menu(chat_id, db)

# change url's tag
@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_tag_"))
def handle_change_tag_request(call):
    chat_id = call.message.chat.id
    url_id = int(call.data.split("_")[-1])
    db = next(get_db())
    tags = db.query(Tag).filter_by(community_id=chat_id).all()
    markup = InlineKeyboardMarkup()
    for tag in tags:
        markup.add(InlineKeyboardButton(tag.name, callback_data=f"set_new_tag_{url_id}_{tag.id}"))
    bot.edit_message_text("Selecciona el nuevo tag para la URL:", chat_id, call.message.message_id, reply_markup=markup)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("set_new_tag_"))
def set_new_tag(call):
    parts = call.data.split("_")
    url_id = int(parts[3])
    new_tag_id = int(parts[4])
    chat_id = call.message.chat.id
    db = next(get_db())
    url = db.query(Url).filter_by(id=url_id, community_id=chat_id).first()
    if url:
        url.tag_id = new_tag_id
        db.commit()
        bot.edit_message_text(f"✅ Tag actualizado para la URL ID {url_id}.", chat_id, call.message.message_id)
    else:
        bot.send_message(chat_id, "❌ No se encontró la URL.")
    bot.answer_callback_query(call.id)
    show_action_menu(chat_id, db)

# Drop url
@bot.callback_query_handler(func=lambda call: call.data.startswith("delete_url_"))
def confirm_delete_url(call):
    url_id = int(call.data.split("_")[-1])
    chat_id = call.message.chat.id

    # Delete the previous message with buttons before sending the new message
    bot.delete_message(chat_id, call.message.message_id)
    
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("✅ Sí, eliminar", callback_data=f"confirm_delete_url_{url_id}"),
        InlineKeyboardButton("❌ Cancelar", callback_data="cancel_delete")
    )
    #bot.edit_message_text("¿Estás segure que deseas eliminar esta URL?", chat_id, call.message.message_id, reply_markup=markup)
    bot.send_message(chat_id, "¿Estás segure que deseas eliminar esta URL??", reply_markup=markup)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_delete_url_"))
def delete_url(call):
    url_id = int(call.data.split("_")[-1])
    chat_id = call.message.chat.id
    db = next(get_db())
    url = db.query(Url).filter_by(id=url_id, community_id=chat_id).first()
    if url:
        db.delete(url)
        db.commit()
        bot.edit_message_text(f"🗑️ URL ID {url_id} eliminada con éxito.", chat_id, call.message.message_id)
    else:
        bot.send_message(chat_id, "No se encontró la URL.")
    bot.answer_callback_query(call.id)
    show_action_menu(chat_id, db)


# -- DROP TAG OR COMMUNITY --

#adk confirmation delete tag
@bot.callback_query_handler(func=lambda call: call.data == "confirm_delete_tag")
def show_tags_to_delete(call):
    chat_id = call.message.chat.id
    db = next(get_db())
    tags = db.query(Tag).filter_by(community_id=chat_id).all()

    if not tags:
        bot.edit_message_text("❌ No hay tags para eliminar.", chat_id, call.message.message_id)
        return

    markup = InlineKeyboardMarkup()
    for tag in tags:
        markup.add(InlineKeyboardButton(f"{tag.name}", callback_data=f"delete_tag_{tag.id}"))
    bot.edit_message_text("Selecciona un tag para eliminar:", chat_id, call.message.message_id, reply_markup=markup)
    bot.answer_callback_query(call.id)

#delete tag
@bot.callback_query_handler(func=lambda call: call.data.startswith("delete_tag_"))
def delete_tag(call):
    tag_id = int(call.data.split("_")[-1])
    chat_id = call.message.chat.id
    db = next(get_db())
    tag = db.query(Tag).filter_by(id=tag_id, community_id=chat_id).first()
    if tag:
        db.delete(tag)
        db.commit()
        bot.edit_message_text(f"✅ Tag '{tag.name}' eliminado.", chat_id, call.message.message_id)
        show_action_menu(chat_id, db)
    else:
        bot.answer_callback_query(call.id, "Tag no encontrado.", show_alert=True)

# ask confirmation delete community 
@bot.callback_query_handler(func=lambda call: call.data == "confirm_delete_community")
def ask_confirm_community_delete(call):
    chat_id = call.message.chat.id
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("⚠️ Sí, eliminar comunidad", callback_data="delete_community"),
        InlineKeyboardButton("❌ Cancelar", callback_data="cancel_delete")
    )
    bot.edit_message_text("⚠️ ¿Estás segurx de que deseas eliminar toda la comunidad? Esto eliminará todos los tags y URLs asociados.", chat_id, call.message.message_id, reply_markup=markup)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data == "delete_community")
def ask_confirm_delete_community(call):
    chat_id = call.message.chat.id
    db = next(get_db())
    community = db.query(Community).filter_by(id=chat_id).first()
    if community:
        # confirmas si es bnecesario borras las url y tags !!!!!!!!!!!!!!!!!!!!!!!!!!!
        db.query(Url).filter_by(community_id=chat_id).delete()
        db.query(Tag).filter_by(community_id=chat_id).delete()
        db.delete(community)
        db.commit()
        bot.edit_message_text("Comunidad eliminada exitosamente.", chat_id, call.message.message_id)
        show_action_menu(chat_id, db)
    else:
        bot.answer_callback_query(call.id, "No se encontró la comunidad.", show_alert=True)


# in case of cancel button
@bot.callback_query_handler(func=lambda call: call.data == "cancel_delete")
def cancel_deletion(call):
    bot.answer_callback_query(call.id, text="Operación cancelada.")
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

print(user_states)
# Inicia polling
if __name__ == '__main__':
    bot.polling(none_stop=True)
    print(user_states)
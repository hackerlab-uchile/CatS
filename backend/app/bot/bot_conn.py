import telebot
import threading
import os
from app.database import get_db
from app.models import Community, Tag, Url
from app.bot.utils import is_valid_url, is_valid_name
from collections import defaultdict
from sqlalchemy.exc import SQLAlchemyError
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ForceReply, PollAnswer

# ------------------------------------------- Global variables section ----------------------------------------------
# Bot setup
TOKEN = os.getenv("BOTTOKEN")
bot = telebot.TeleBot(TOKEN)

# Default server IP (for all communities)
IPSERVER = os.getenv("SERVER_IP")

# Length name fields
LENNAMES = int(os.getenv("LENNAMES"))
LENDESC = int(os.getenv("LENDESC"))
SURVEY_WAITIG_TIME = int(os.getenv("SURVEY_WAITIG_TIME"))

# Function that page existing tags
TAGS_PER_PAGE = 3

# Dictionary to save the state per chat
user_states = {}

# New dictionary to track anonymous votes
anonymous_votes = defaultdict(lambda: {'yes': 0, 'no': 0, 'voters': set()})

# ------------------------------------------------------------------------------------------------------------------

# --------------------------------------------- Functions section --------------------------------------------------

def instrucciones_text():
    """
    Function that returns the intructions for use of the bot
    """
    return (
        "👋 *Bienvenide a CatS bot!*\n"
        "Con este bot podrás crear y gestionar tu comunidad 😺 \n"
        "------------------------------------------------------\n\n"

        "Aquí hay algunas instrucciones para usar el bot:\n\n"

        "⭐ Envía */start* y el bot te guiará en la creación de tu comunidad!\n\n"

        "❗❗Para procesar tu respuesta, responde directamente al mensaje del bot❗❗\n"
        "👉 Para hacerlo:\n"
        "1. Mantén presionado (o haz clic derecho) en el mensaje del bot que te pidió algo.\n"
        '2. Elige la opción "Responder".\n'
        "3. Escribe tu respuesta y envíalo.\n\n"

        "❌ Si deseas cancelar la creación de un tag o url en algún paso intermedio, solo envía /start para mostrar el menú de acciones disponibles\n\n"

        "⚙️ Usa */start* para ver las acciones disponibles.\n"
        "ℹ️ Ante dudas, envía */help* para volver a ver estas instrucciones."
    )

@bot.message_handler(commands=["menu"])
def explain_menu(message):
    """
    
    """
    explanation = (
        "Descripción de las acciones existentes:\n\n"
        
        "📌 *Crear tag:* Te guiará en la creación de un tag. Para más información envía /tags.\n"
        "🔍 *Ver tags:* Selecciona 'Ver tags' para revisar los que ya existen.\n"
        "🌐 *Agregar URL:* Luego de tener al menos un tag, te guiará en la creación de una URL. Para más información envía /urls.\n"
        "🔍 *Ver/Editar URLs:* Luego de tener al menos una URL, selecciona 'Ver/Editar URLs' para revisar o editar las URL existentes.\n"
        "🧹 *Eliminar tag:* Permite eliminar un tag dentro de la lista de tags creados. ⚠️¡Esto eliminará todas las URLs asociadas exclusivamente a ese tag!⚠️\n"
        "🧹 *Eliminar Comunidad:* Permite eliminar la comunidad asociada al chat. ⚠️¡Esto eliminará todos los tags y URLs creados en este chat!⚠️\n\n"

        "ℹ️ Las acciones *Ver tags*, *Eliminar tag*, *Agregar URL* y *Ver/Editar URLs* estarán disponibles cuando crees al menos 1 tag.\n"
        "⚙️ Usa */start* para ver las acciones disponibles."
    )
    bot.send_message(message.chat.id, explanation, parse_mode="Markdown")


@bot.message_handler(commands=["comunidades"])
def explain_communities(message):
    """
    Function that returns the explanation of what is a community
    """
    explanation = (
        "🏘️ *¿Qué son las comunidades?*\n\n"
        "Una comunidad es un grupo de personas que comparten intereses similares, y que colaboran en la categorización y control de URLs en CatS.\n\n"
        "Cada comunidad puede definir sus propios *tags* (etiquetas) para organizar sitios web y asignarles acciones como bloquear, alertar o notificar.\n"
        "Además, requieren una pequeña descripción de lo que se tratará tu comunidad\n\n"
        "👉 Puedes unirte a comunidades y suscribirte a sus tags desde la extensión del navegador.\n"
        "🗳️ Las decisiones como agregar o editar tags/URLs requieren votación entre les integrantes del grupo.\n\n"
        "⚙️ Usa */start* para ver las acciones disponibles."
    )
    bot.send_message(message.chat.id, explanation, parse_mode="Markdown")


@bot.message_handler(commands=["tags"])
def explain_tags(message):
    """
    Function that returns the explanation of what is a tag
    """
    explanation = (
        "🏷️ *¿Qué son los tags?*\n\n"
        "Las *etiquetas* (o tags) permiten clasificar las URLs compartidas por cada comunidad.\n"
        "Por ejemplo, una comunidad de _Estudio_ que puede tener los tags _Idiomas_, _Matemáticas_, o _Ciencia_.\n\n"
        "Cada etiqueta define una *acción predeterminada* que tu navegador ejecutará cuando detecte una URL asociada a ella:\n"
        "- `block`: bloquear el sitio automáticamente 🚫\n"
        "- `alert`: mostrar una alerta al visitar el sitio ⚠️\n"
        "- `notify`: mostrar una notificación al visitar el sitio 🛎️\n\n"
        "Cuando te suscribes a un tag, aplicas sus acciones automáticamente en tu navegador para las URLs relacionadas.\n\n"
        "⚙️ Usa */start* para ver las acciones disponibles."
    )
    bot.send_message(message.chat.id, explanation, parse_mode="Markdown")


@bot.message_handler(commands=["urls"])
def explain_urls(message):
    """
    Function that returns the explanation of what is a url
    """
    explanation = (
        "🔗 *¿Qué son las URLs registradas?*\n\n"
        "Cada comunidad puede asociar *URLs* a sus etiquetas.\n"
        "Estas URLs representan sitios que la comunidad considera relevantes o problemáticos, según el propósito de la etiqueta.\n\n"
        "Cada URL se registra junto con una *justificación*, explicando por qué fue agregada.\n"
        "Por ejemplo: una comunidad de _Ciberseguridad_ podría agregar _badsite.com_ bajo una etiqueta _Peligrosos_ con acción _block_, justificando que _Es un sitio web falso_.\n\n"
        "Cuando te suscribes a un tag, todas las URLs asociadas a ella se aplicarán automáticamente según su acción definida.\n\n"
        "⚙️ Usa */start* para ver las acciones disponibles."
    )
    bot.send_message(message.chat.id, explanation, parse_mode="Markdown")


def show_action_menu(chat_id, db):
    """
    Options menu, sends buttons with options to execute depending on the context of the chat.
    If you have not created a community:
        - redirects to the process of creating one.
    If no tag:
        - Create tag
        - Delete community
    If there is at least 1 tag:
        - Create tag
        - view tags
        - delete tag
        - create url
        - delete community
    If there is at least 1 url:
        - Create tag
        - view tags
        - delete tag
        - create url
        - view/edit url
        - delete community
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
            InlineKeyboardButton("➕ Crear tag", callback_data=f"action_create_tag"),
            InlineKeyboardButton("🗑️ Eliminar Comunidad", callback_data="confirm_delete_community")
            )
        bot.send_message(chat_id, "No hay tags creados. ¿Qué deseas hacer?\nℹ️ Envía /menu para más información", reply_markup=markup)
    elif url is None:
        markup.add(
            InlineKeyboardButton("➕ Crear tag", callback_data="action_create_tag"),
            InlineKeyboardButton("🏷️ Ver tags", callback_data="view_tags")
        )
        markup.add(
            InlineKeyboardButton("🌐 Agregar URL", callback_data="action_add_url"),
            InlineKeyboardButton("🗑️ Eliminar tag", callback_data="confirm_delete_tag")
        )
        markup.add(
            InlineKeyboardButton("🗑️ Eliminar comunidad", callback_data="confirm_delete_community")
        )
        bot.send_message(chat_id, "¿Qué deseas hacer?\nℹ️ Envía /menu para más información", reply_markup=markup)
    else:
        markup.add(
            InlineKeyboardButton("➕ Crear tag", callback_data="action_create_tag"),
            InlineKeyboardButton("🏷️ Ver tags", callback_data="view_tags")
        )
        markup.add(
            InlineKeyboardButton("🌐 Agregar URL", callback_data="action_add_url"),
            InlineKeyboardButton("🔍 Ver/Editar URLs", callback_data="manage_urls")
        )
        markup.add(
            InlineKeyboardButton("🗑️ Eliminar tag", callback_data="confirm_delete_tag"),
        )        
        markup.add(
            InlineKeyboardButton("🗑️ Eliminar comunidad", callback_data="confirm_delete_community")
        )
        bot.send_message(chat_id, "¿Qué deseas hacer?\nℹ️ Envía /menu para más información", reply_markup=markup)


def show_tag_buttons(chat_id, page=0):
    """
    Creates catalog showing all existing tags paginated

    Inputs:
    -------
    page: int
        number of the displayed page, by default it starts at 0
    """
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

# Manage the page layout when the ➡️ (Next or previus) button is selected
@bot.callback_query_handler(func=lambda call: call.data.startswith("page:"))
def handle_page_navigation(call):
    chat_id = call.message.chat.id
    page = int(call.data.split(":")[1])

    # Delete the previous message with buttons before sending the new message
    bot.delete_message(chat_id, call.message.message_id)

    # Show the next page
    show_tag_buttons(chat_id, page=page)


# Launch anonymous vote using inline buttons
def launch_anonymous_vote(chat_id, question, object_type, data):
    """
    Launches anonymous voting with buttons and stores expected quorum.
    """
    try:
        total_members = bot.get_chat_members_count(chat_id)
    except Exception as e:
        bot.send_message(chat_id, "❌ No se pudo obtener el número de integrantes del grupo, para asegurar el funcionamiento de la encuesta, promueve al bot a administrador de chat")
        total_members = 1  # fallback to avoid division by zero

    quorum = max(1, int((total_members - 1) * 0.5) +1)  # at least 50%

    full_question = question + "\n\n ⚠️ No podrás cambiar tu selección luego de votar ⚠️"
    message = bot.send_message(
        chat_id,
        full_question,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ Sí", callback_data=f"vote_yes|{chat_id}"),
            InlineKeyboardButton("❌ No", callback_data=f"vote_no|{chat_id}")
        ]])
    )

    # Initialize votes
    anonymous_votes[chat_id] = {
        'yes': 0,
        'no': 0,
        'voters': set()
    }

    # User status
    user_states[chat_id] = {
        'step': 'wait_approval',
        'object_type': object_type,
        'data': data,
        'message_id': message.message_id,
        'quorum': quorum
    }
    # Start vote check timer
    threading.Timer(SURVEY_WAITIG_TIME, check_anonymous_vote_result, args=[chat_id]).start()
    m, s = divmod(SURVEY_WAITIG_TIME, 60)
    if m and s:
        readable = f"{m} min {s} s"
    elif m:
        readable = f"{m} min"
    else:
        readable = f"{s} s"
    bot.send_message(chat_id, f"Se esperará {readable} para recolectar la mayor cantidad de votos posibles, por favor espere antes de continuar.")

# Handle votes
@bot.callback_query_handler(func=lambda call: call.data.startswith("vote_"))
def handle_vote_buttons(call):
    action, chat_id = call.data.split("|")
    chat_id = int(chat_id)
    user_id = call.from_user.id

    # Early verification
    if chat_id not in anonymous_votes:
        bot.answer_callback_query(call.id, "⚠️ La votación ya expiró o no fue inicializada correctamente.")
        return

    # Prevent double voting
    if user_id in anonymous_votes[chat_id]['voters']:
        bot.answer_callback_query(call.id, "Ya has votado.")
        return

    anonymous_votes[chat_id]['voters'].add(user_id)
    if action == "vote_yes":
        anonymous_votes[chat_id]['yes'] += 1
    else:
        anonymous_votes[chat_id]['no'] += 1

    bot.answer_callback_query(call.id, "✅ Voto recibido.")
    total_votes = len(anonymous_votes[chat_id]['voters'])
    total_members = bot.get_chat_members_count(chat_id)
    if total_votes == (total_members -1):
        check_anonymous_vote_result(chat_id)

# Check result

def check_anonymous_vote_result(chat_id):
    state = user_states.get(chat_id, {})
    result = anonymous_votes.get(chat_id, {})

    # If there is no more data, the vote was processed earlier because 100% of the chat voted before the time expired
    if not state or not result:
        return

    total_votes = result['yes'] + result['no']
    quorum = state.get('quorum', 1)

    # Requiere mayoría absoluta: más de la mitad de los votos del quórum
    required_yes_votes = (quorum // 2) + 1

    if  total_votes >= quorum and result['yes'] >= required_yes_votes:
        type = state.get('object_type')
        data = state.get('data')
        if type == "tag":
            save_tag(chat_id, data)
        elif type == "url":
            save_url(chat_id, data)
        elif type == "edit_url":
            edit_type = data.get("type")
            url_id = data.get("url_id")
            new_value = data.get("new_value")
            db = next(get_db())
            url_entry = db.query(Url).filter_by(id=url_id).first()
            if url_entry:
                if edit_type == "justification":
                    url_entry.justification = new_value
                elif edit_type == "tag":
                    url_entry.tag_id = new_value
                db.commit()
                bot.send_message(chat_id, "✅ Edición aplicada correctamente.")
            else:
                bot.send_message(chat_id, "❌ No se encontró la URL para editar.")
        elif type == "delete_url":
            url_id = data.get("url_id")
            db = next(get_db())
            url_entry = db.query(Url).filter_by(id=url_id, community_id=chat_id).first()
            if url_entry:
                db.delete(url_entry)
                db.commit()
                bot.send_message(chat_id, f"🗑️ URL {url_entry.url} eliminada con éxito.")
            else:
                bot.send_message(chat_id, "❌ No se encontró la URL para eliminar.")
        elif type == "delete_tag":
            tag_id = data.get("tag_id")
            db = next(get_db())
            tag = db.query(Tag).filter_by(id=tag_id, community_id=chat_id).first()
            if tag:
                db.delete(tag)
                db.commit()
                bot.send_message(chat_id, f"🗑️ Tag {tag.name} eliminado correctamente.")
            else:
                bot.send_message(chat_id, "❌ El tag ya no existe.")
        elif type == "delete_community":
            db = next(get_db())
            db.query(Url).filter_by(community_id=chat_id).delete()
            db.query(Tag).filter_by(community_id=chat_id).delete()
            community = db.query(Community).filter_by(id=chat_id).first()
            if community:
                db.delete(community)
                db.commit()
                bot.send_message(chat_id, "🗑️ Comunidad eliminada exitosamente.")
            else:
                bot.send_message(chat_id, "❌ Comunidad ya no existe.")

    else:
        bot.send_message(chat_id, f"❌ La propuesta fue rechazada por la comunidad o no se cumplió quórum mínimo: {quorum}, votos recibidos: {total_votes}.")

    # Cleanup
                   
    message_id = state.get('message_id')
    bot.delete_message(chat_id, message_id)  # Delete msg with the survey
        
    anonymous_votes.pop(chat_id, None)
    user_states.pop(chat_id, None)
    db = next(get_db())
    show_action_menu(chat_id, db)


# ------------------------------------------------------------------------------------------------------------------

# --------------------------------------------- Bot flow section ---------------------------------------------------

# Welcome message, sent when the bot is added for the first time or a new member is added to the group.
@bot.message_handler(content_types=['new_chat_members'])
def welcome_new_members(message):
    for member in message.new_chat_members:
        if member.id == bot.get_me().id:
            bot.send_message(
                message.chat.id,
                "👋 ¡Hola! Soy CatS bot.\n"
                "Escribe o presiona /help para ver qué puedo hacer.",
                parse_mode="Markdown"
            )


# Show use instructions when the command /help is sended
@bot.message_handler(commands=['help'])
def handle_bot_mention(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, instrucciones_text(), parse_mode="Markdown")


# /start handler, if not community, ask for create one, else show action menu
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
        bot.send_message(chat_id, "¡Hola! Primero, ingresa el nombre de la comunidad a registrar:\n\nℹ️ Si quieres saber más sobre comunidades, envía /comunidades.", reply_markup=ForceReply(selective=True))
    else:
        # show action menu
        show_action_menu(chat_id, db)


# Community name reseption and ask for community description
@bot.message_handler(func=lambda m: user_states.get(m.chat.id, {}).get('step') == 'ask_name')
def handle_name(message):
    chat_id = message.chat.id
    name = message.text.strip()

    # sanitization of the name
    if not is_valid_name(name, LENNAMES):
        bot.send_message(chat_id, f"Nombre inválido, ingresa un nombre válido y de máximo {LENNAMES} carácteres.")
        bot.send_message(chat_id, "Ingresa el nombre de la comunidad a registrar:", reply_markup=ForceReply(selective=True))
        user_states[chat_id] = {'step': 'ask_name'}
    else:
        bot.send_message(chat_id, "Ahora ingresa una descripción para la comunidad:", reply_markup=ForceReply(selective=True))
        user_states[chat_id] = {'step': 'ask_description', 'name': name} 


# Community description reseption and community creation
@bot.message_handler(func=lambda m: user_states.get(m.chat.id, {}).get('step') == 'ask_description')
def handle_description(message):
    chat_id = message.chat.id
    description = message.text.strip()
    name = user_states.get(chat_id, {}).get('name')

    # description sanitization
    if not is_valid_name(description, LENDESC):
        bot.send_message(chat_id, f"⚠️ Descripción inválida, ingresa una descripción válida y de máximo {LENDESC} carácteres.")
        bot.send_message(chat_id, "Ingresa una descripción para la comunidad:", reply_markup=ForceReply(selective=True))
        user_states[chat_id] = {'step': 'ask_description', 'name': name}
    else:
        try:
            # add new community
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


# Action choise (fill_tag or fill_url): ask for the name of the tag or address or the URL respectively
@bot.callback_query_handler(func=lambda call: call.data.startswith("action_"))
def handle_action_menu(call):
    chat_id = call.message.chat.id
    action = call.data
    bot.delete_message(chat_id, call.message.message_id)

    if action == "action_create_tag":
        user_states[chat_id] = {'step': 'fill_tag'}
        bot.send_message(chat_id, "Ingresa el nombre del nuevo tag:\n\nℹ️ Si quieres saber más sobre tags, envía /tags.", reply_markup=ForceReply(selective=True))
    else:
        user_states[chat_id] = {'step': 'fill_url'}
        bot.send_message(chat_id, "Ingresa la dirección de la URL que deseas agregar:\n\nℹ️ Si quieres saber más sobre urls, envía /urls.", reply_markup=ForceReply(selective=True))


# ----- FILL TAG -----
# Tag name reseption and ask for tag description
@bot.message_handler(func=lambda m: user_states.get(m.chat.id, {}).get('step') == 'fill_tag')
def handle_fill_tag_name(message):
    chat_id = message.chat.id
    tag_name = message.text.strip()

    # name sanitization
    if not is_valid_name(tag_name, LENNAMES):
        bot.send_message(chat_id, f"⚠️ Nombre inválido, ingresa un nombre válido y de máximo {LENNAMES} carácteres.")
        bot.send_message(chat_id, "Ingresa el nombre del nuevo Tag:\n\nℹ️ Si quieres saber más sobre tags, envía /tags.", reply_markup=ForceReply(selective=True))
        user_states[chat_id] = {'step': 'fill_tag'}
    else:
        # check if exits a tag with that name in this community, if so, ask again for the tag name
        db = next(get_db())
        existing_tag = db.query(Tag).filter_by(name=tag_name, community_id=chat_id).first()
        if existing_tag:
            bot.send_message(chat_id, f"⚠️ Ya existe un tag llamado '{tag_name}' en esta comunidad. Por favor ingresa otro nombre para el tag:")
            user_states[chat_id] = {'step': 'fill_tag'}
        else:
            user_states[chat_id] = {'step': 'fill_tag_description', 'tag_name':tag_name}
            bot.send_message(chat_id, "Ingresa una descripción para el Tag:", reply_markup=ForceReply(selective=True))

# tag description reseption and ask for tag action
@bot.message_handler(func=lambda m: user_states.get(m.chat.id, {}).get('step') == 'fill_tag_description')
def handle_fill_tag_description(message):
    chat_id = message.chat.id
    tag_description = message.text.strip()
    state = user_states.get(chat_id, {})
    tag_name = state.get('tag_name')

    # description sanitization
    if not is_valid_name(tag_description, LENDESC):
        bot.send_message(chat_id, f"⚠️ Descripción inválida, ingresa una descripción válida y de máximo {LENDESC} carácteres.")
        bot.send_message(chat_id, "Ingresa una descripción para el Tag:")
        user_states[chat_id] = {'step': 'fill_tag_description', 'tag_name':tag_name}
    else:
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("🔒 Bloquear", callback_data="tag_action_block"),
            InlineKeyboardButton("⚠️ Alertar", callback_data="tag_action_alert"),
            InlineKeyboardButton("🔔 Notificar", callback_data="tag_action_notify")
        )
        bot.send_message(chat_id, "Selecciona la acción del tag:", reply_markup=markup)
        user_states[chat_id] = {'step': 'tag_action_', 'tag_name':tag_name, 'tag_description': tag_description}

# tag action reseption
@bot.callback_query_handler(func=lambda call: call.data.startswith("tag_action_"))
def handle_tag_action_selection(call):
    chat_id = call.message.chat.id
    state = user_states.get(chat_id, {})
    tag_name = state.get('tag_name')    
    tag_description = state.get('tag_description') 
    action = call.data.replace("tag_action_","")

    # Delete the msg with the buttons to void confusion
    bot.delete_message(chat_id, call.message.message_id)

    # Guardar info y lanzar encuesta
    question = f"¿Aprobar el nuevo tag: '{tag_name}' con acción: '{action}' y descripción: '{tag_description}'?"
    data = {
        'tag_name': tag_name,
        'tag_description': tag_description,
        'action': action
    }
    launch_anonymous_vote(chat_id, question, object_type="tag", data=data)


def save_tag(chat_id, data):
    """
    function in charge of storing the tag in the database

    Inputs:
    -------
    chat_id: int
        ID of the chat
    data: dict
        Data of the tag to save
    """
    try:
        db = next(get_db())
        community = db.query(Community).filter_by(id=chat_id).first()
        new_tag = Tag(
            name=data['tag_name'],
            description=data['tag_description'],
            action=data['action'],
            community_id=community.id
        )
        db.add(new_tag)
        db.commit()
        bot.send_message(chat_id, f"✅ Tag '{data['tag_name']}' agregado exitosamente.")
    except SQLAlchemyError as e:
        bot.send_message(chat_id, f"❌ Error al guardar el tag: {e}")


# ----- View tags -----
@bot.callback_query_handler(func=lambda call: call.data == "view_tags")
def handle_view_tags(call):
    chat_id = call.message.chat.id
    db = next(get_db())

    # Delete the msg with the buttons to void confusion
    bot.delete_message(chat_id, call.message.message_id)

    tags = db.query(Tag).filter_by(community_id=chat_id).all()

    # button with tag info per tag
    for tag in tags:
        text = (
            f"🏷️ *Tag:* {tag.name}\n"
            f"📝 *Descripción:* {tag.description}\n"
            f"⚙️ *Acción:* {tag.action}"
        )
        bot.send_message(chat_id, text, parse_mode="Markdown")

    bot.answer_callback_query(call.id)


# ----- FILL URL -----
# url address reseption and ask for tag
@bot.message_handler(func=lambda m: user_states.get(m.chat.id, {}).get('step') == 'fill_url')
def handle_fill_url_address(message):
    chat_id = message.chat.id
    url = message.text.strip()

    # if do not have http or https add it
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    # url sanitization
    if not is_valid_url(url):
        bot.send_message(chat_id, "🚫 La URL ingresada no es válida o es privada. Intenta con una dirección como `https://ejemplo.com`.")
        bot.send_message(chat_id, "Ingresa la dirección de la URL que deseas agregar:\n\nℹ️ Si quieres saber más sobre urls, envía /urls.")
        user_states[chat_id] = {'step': 'fill_url'}
        
    else:
        user_states[chat_id] = {'step': 'fill_url_tag', 'url': url}
        show_tag_buttons(chat_id, page=0)

# url tag reseption and ask for justification
@bot.callback_query_handler(func=lambda call: call.data.startswith("select_tag:"))
def handle_tag_selection(call):
    chat_id = call.message.chat.id
    tag_name = call.data.split(":")[1]
    
    # retrieve URL from status
    state = user_states.get(chat_id, {})
    url = state.get('url')
    
    db = next(get_db())
    tag = db.query(Tag).filter_by(name=tag_name, community_id=chat_id).first()

    # check if the same URL already exists for that tag and community
    existing_url = db.query(Url).filter_by(url=url, tag_id=tag.id, community_id=chat_id).first()
    if existing_url:
        bot.answer_callback_query(call.id, "⚠️ Esta URL ya fue registrada en este tag.")
        bot.send_message(chat_id, "Por favor, intenta con una URL o Tag diferente.")
        return show_action_menu(chat_id, db)

    # save the new state
    user_states[chat_id] = {'step': 'fill_url_justification', 'url': url, 'tag': tag_name}

    # Delete the msg with the buttons to void confusion
    bot.delete_message(chat_id, call.message.message_id)

    bot.send_message(chat_id, f"Seleccionaste el tag '{tag_name}'. Ahora ingresa una justificación para esta URL:")


# url justification reseption
@bot.message_handler(func=lambda m: user_states.get(m.chat.id, {}).get('step') == 'fill_url_justification')
def handle_fill_url_justification(message):
    chat_id = message.chat.id
    state = user_states.get(chat_id, {})
    url_address = state.get('url')
    url_tag =  state.get('tag')
    justification = message.text.strip()

    # justification sanitization
    if not is_valid_name(justification, LENDESC):
        bot.send_message(chat_id, f"⚠️ Justificación inválida, ingresa una justificación válida y de máximo {LENDESC} carácteres.")
        bot.send_message(chat_id, "Ingresa una justificación para la URL:")
        user_states[chat_id] = {'step': 'fill_url_justification', 'url': url_address, 'tag': url_tag}
    else:
        question = f"¿Aprobar agregar la URL: '{url_address}' al tag: '{url_tag}' con justificación: '{justification}'?"
        data = {
            'url': url_address,
            'tag': url_tag,
            'justification': justification
        }
        launch_anonymous_vote(chat_id, question, object_type="url", data=data)


def save_url(chat_id, data):
    """
    function in charge of storing the url in the database

    Inputs:
    -------
    chat_id: int
        ID of the chat
    data: dict
        Data of the tag to save
    """
    try:
        db = next(get_db())
        tag = db.query(Tag).filter_by(name=data['tag'], community_id=chat_id).first()
        community = db.query(Community).filter_by(id=chat_id).first()
        new_url = Url(
            url=data['url'],
            justification=data['justification'],
            community_id=community.id,
            tag_id=tag.id
        )
        db.add(new_url)
        db.commit()
        bot.send_message(chat_id, f"✅ URL '{data['url']}' agregada exitosamente.")
    except SQLAlchemyError as e:
        bot.send_message(chat_id, f"❌ Error al guardar la URL: {e}")

# ----- EDIT URL -----
@bot.callback_query_handler(func=lambda call: call.data == "manage_urls")
def handle_manage_urls(call):
    chat_id = call.message.chat.id
    db = next(get_db())
    urls = db.query(Url).filter_by(community_id=chat_id).all()

    # Delete the msg with the buttons to void confusion 
    bot.delete_message(chat_id, call.message.message_id)

    # show urls
    for url in urls:
        tag_id =url.tag_id
        tag = db.query(Tag).filter_by(community_id=chat_id, id=tag_id).first()
        text = f"🌐 URL: {url.url}\n 📝 Justificación: {url.justification}\n 🏷️ Tag: {tag.name}"
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
    db = next(get_db())
    url = db.query(Url).filter_by(id=url_id, community_id=chat_id).first()

    # Delete the previous message with buttons before sending the new message
    bot.delete_message(chat_id, call.message.message_id)
    
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("✏️ Editar justificación", callback_data=f"edit_just_{url_id}"),
        InlineKeyboardButton("🔁 Cambiar tag", callback_data=f"edit_tag_{url_id}")
    )
    bot.send_message(chat_id, f"¿Qué deseas hacer con la URL {url.url}?", reply_markup=markup)
    bot.answer_callback_query(call.id)

# Edit Justification url
@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_just_"))
def edit_url_justification(call):
    url_id = int(call.data.split("_")[-1])
    chat_id = call.message.chat.id

    # Delete the previous message with buttons before sending the new message
    bot.delete_message(chat_id, call.message.message_id)

    user_states[chat_id] = {'step': 'editing_just', 'url_id': url_id}
    bot.send_message(chat_id, "Escribe la nueva justificación:")

# new url justificacion reseption  and update url
@bot.message_handler(func=lambda m: user_states.get(m.chat.id, {}).get('step') == 'editing_just')
def save_new_justification(message):
    chat_id = message.chat.id
    new_just = message.text.strip()
    url_id = user_states[chat_id]['url_id']

    # new justification sanitization
    if not is_valid_name(new_just, LENDESC):
        bot.send_message(chat_id, f"⚠️ Justificación inválida, ingresa una justificación válida y de máximo {LENDESC} carácteres.")
        bot.send_message(chat_id, "Ingresa una justificación para la URL:")
        user_states[chat_id] = {'step': 'editing_just', 'url_id': url_id}
    else:
        # Launch approval survey before saving the new justification
        db = next(get_db())
        url_entry = db.query(Url).filter_by(id=url_id).first()
        question = f"¿Aprobar la nueva justificación: '{new_just}' para la URL: '{url_entry.url}'?"
        data = {
            'type': 'justification',
            'url_id': url_id,
            'new_value': new_just
        }
        launch_anonymous_vote(chat_id, question, object_type="edit_url", data=data)

# change url's tag
@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_tag_"))
def handle_change_tag_request(call):
    chat_id = call.message.chat.id
    url_id = int(call.data.split("_")[-1])
    db = next(get_db())
    tags = db.query(Tag).filter_by(community_id=chat_id).all()

    # show buttons with tags
    markup = InlineKeyboardMarkup()
    for tag in tags:
        markup.add(InlineKeyboardButton(tag.name, callback_data=f"set_new_tag_{url_id}_{tag.id}"))
    bot.edit_message_text("Selecciona el nuevo tag para la URL:", chat_id, call.message.message_id, reply_markup=markup)
    bot.answer_callback_query(call.id)

# new url tag reseption and update url
@bot.callback_query_handler(func=lambda call: call.data.startswith("set_new_tag_"))
def set_new_tag(call):
    parts = call.data.split("_")
    url_id = int(parts[3])
    new_tag_id = int(parts[4])
    chat_id = call.message.chat.id

    db = next(get_db())
    url = db.query(Url).filter_by(id=url_id, community_id=chat_id).first()
    new_tag = db.query(Tag).filter_by(id=new_tag_id).first()

    if url and new_tag:
        question = f"¿Aprobar el cambio de tag de la URL '{url.url}' a '{new_tag.name}'?"
        data = {
            'type': 'tag',
            'url_id': url_id,
            'new_value': new_tag_id
        }
        launch_anonymous_vote(chat_id, question, object_type="edit_url", data=data)
    else:
        bot.send_message(chat_id, "❌ No se encontró la URL o el nuevo tag.")
        db = next(get_db())
        show_action_menu(chat_id, db)
    bot.answer_callback_query(call.id)

# ask confirmation for delete url
@bot.callback_query_handler(func=lambda call: call.data.startswith("delete_url_"))
def confirm_delete_url(call):
    url_id = int(call.data.split("_")[-1])
    chat_id = call.message.chat.id
    db = next(get_db())
    url = db.query(Url).filter_by(id=url_id, community_id=chat_id).first()

    if not url:
        bot.answer_callback_query(call.id, "❌ No se encontró la URL.")
        return
    
    # shows confirmation of deletion buttons
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("✅ Sí, proponer eliminación", callback_data=f"propose_delete_url_{url_id}"),
        InlineKeyboardButton("❌ Cancelar", callback_data="cancel_delete")
    )
    bot.edit_message_text(
        f"¿Estás segurx que deseas proponer la eliminación de la URL {url.url}?", 
        chat_id, 
        call.message.message_id, 
        reply_markup=markup)
    bot.answer_callback_query(call.id)

# delete url
@bot.callback_query_handler(func=lambda call: call.data.startswith("propose_delete_url_"))
def propose_delete_url_vote(call):
    url_id = int(call.data.split("_")[-1])
    chat_id = call.message.chat.id
    db = next(get_db())
    url = db.query(Url).filter_by(id=url_id, community_id=chat_id).first()
    message_id = call.message.message_id

    # delete propose delete button
    bot.delete_message(chat_id, message_id)

    if not url:
        bot.send_message(chat_id, "❌ No se encontró la URL.")
        return
    
    question = f"¿Apruebas eliminar la URL: {url.url}?"
    launch_anonymous_vote(chat_id, question, "delete_url", {"url_id": url_id})
    bot.answer_callback_query(call.id)


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
def propose_delete_tag_vote(call):
    tag_id = int(call.data.split("_")[-1])
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    bot.delete_message(chat_id, message_id)

    db = next(get_db())
    tag = db.query(Tag).filter_by(id=tag_id, community_id=chat_id).first()
    if not tag:
        bot.send_message(chat_id, "❌ No se encontró el tag.")
        return

    question = f"¿Apruebas eliminar el tag: *{tag.name}*?"
    launch_anonymous_vote(chat_id, question, "delete_tag", {"tag_id": tag_id})

    bot.answer_callback_query(call.id)


# ask confirmation delete community 
@bot.callback_query_handler(func=lambda call: call.data == "confirm_delete_community")
def ask_confirm_community_delete(call):
    chat_id = call.message.chat.id

    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("⚠️ Sí, eliminar comunidad", callback_data="delete_community"),
        InlineKeyboardButton("❌ Cancelar", callback_data="cancel_delete")
    )
    bot.edit_message_text("⚠️ ¿Estás segurx de que deseas proponer la eliminación de toda la comunidad? Esto eliminará todos los tags y URLs asociados.", chat_id, call.message.message_id, reply_markup=markup)
    bot.answer_callback_query(call.id)

# delete community
@bot.callback_query_handler(func=lambda call: call.data == "delete_community")
def propose_delete_community_vote(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    bot.delete_message(chat_id, message_id)

    db = next(get_db())
    community = db.query(Community).filter_by(id=chat_id).first()
    if not community:
        bot.send_message(chat_id, "❌ Comunidad no encontrada.")
        return

    question = f"¿Apruebas eliminar *toda la comunidad* y sus contenidos asociados?"
    launch_anonymous_vote(chat_id, question, "delete_community", {"community_id": chat_id})

    bot.answer_callback_query(call.id)



# in case of cancel button
@bot.callback_query_handler(func=lambda call: call.data == "cancel_delete")
def cancel_deletion(call):
    bot.answer_callback_query(call.id, text="Operación cancelada.")
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

print(user_states)
# Inicia polling
if __name__ == '__main__':
    bot.polling(none_stop=True)
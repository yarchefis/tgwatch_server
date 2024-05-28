from flask import Flask, request, render_template, session, redirect, url_for, flash, jsonify
from telethon import TelegramClient, errors
import os
import asyncio
import json
import configparser
import time
from telethon.tl.types import User, Channel
from urllib.parse import unquote

app = Flask(__name__)
app.secret_key = 'your_secret_key'
config = configparser.ConfigParser()
config.read('config.ini')
api_id = config.get('settings', 'api_id')
api_hash = config.get('settings', 'api_hash')

# Create a global event loop
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

def create_telegram_client():
    client = TelegramClient('session', api_id, api_hash, loop=loop)
    return client

@app.route('/', methods=['GET', 'POST'])
async def index():
    session_file = 'session.session'
    if os.path.exists(session_file) and 'user_id' in session:
        return redirect(url_for('home'))

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'send_code':
            phone_number = request.form['phone']
            session['phone'] = phone_number
            client = create_telegram_client()

            await client.connect()
            result = await client.send_code_request(phone_number)
            session['phone_code_hash'] = result.phone_code_hash

            await client.disconnect()
            return render_template('verify.html')

        elif action == 'verify_code':
            phone_number = session.get('phone')
            phone_code_hash = session.get('phone_code_hash')
            code = request.form['code']
            client = create_telegram_client()

            await client.connect()
            try:
                await client.sign_in(phone=phone_number, code=code, phone_code_hash=phone_code_hash)
                user = await client.get_me()
                session['user_id'] = user.id
                await client.disconnect()
                return redirect(url_for('home'))
            except errors.SessionPasswordNeededError:
                session['code'] = code
                await client.disconnect()
                return render_template('twofa.html')
            except errors.PhoneCodeInvalidError:
                flash('Введённый код неверен.')
                await client.disconnect()
                return render_template('index.html')
            except Exception as e:
                flash(f'Произошла ошибка: {str(e)}')
                await client.disconnect()
                return render_template('index.html')

        elif action == 'verify_2fa':
            phone_number = session.get('phone')
            password = request.form['password']
            client = create_telegram_client()

            await client.connect()
            try:
                await client.sign_in(password=password)
                user = await client.get_me()
                session['user_id'] = user.id
                await client.disconnect()
                return redirect(url_for('home'))
            except errors.PasswordHashInvalidError:
                flash('Введённый пароль неверен.')
                await client.disconnect()
                return render_template('twofa.html')
            except Exception as e:
                flash(f'Произошла ошибка: {str(e)}')
                await client.disconnect()
                return render_template('twofa.html')

    return render_template('index.html')

@app.route('/home')
def home():
    session_file = 'session.session'
    if not os.path.exists(session_file):
        return redirect(url_for('index'))

    if 'user_id' not in session:
        return redirect(url_for('index'))

    user_id = session['user_id']
    return render_template('home.html', user_id=user_id)

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    session_file = 'session.session'
    if os.path.exists(session_file):
        os.remove(session_file)
    return redirect(url_for('index'))

@app.route('/api/chats', methods=['GET', 'POST'])
async def get_chats():
    session_file = 'session.session'
    if not os.path.exists(session_file):
        return jsonify({'error': 'Session file not found'})

    client = create_telegram_client()

    retries = 5
    for i in range(retries):
        try:
            await client.connect()
            await client.start()
            
            config = configparser.ConfigParser()
            config.read('config.ini')
            chats_per_page = config.getint('settings', 'chats_per_page')
            
            page = request.args.get('page', 1, type=int)
            start_index = (page - 1) * chats_per_page
            end_index = start_index + chats_per_page

            dialogs = client.iter_dialogs()
            chats = []
            async for dialog in dialogs:
                entity = dialog.entity
                if isinstance(entity, User) or isinstance(entity, Channel):
                    title = None
                    if isinstance(entity, User):
                        title = entity.first_name
                        if entity.last_name:
                            title += ' ' + entity.last_name
                    elif isinstance(entity, Channel):
                        title = entity.title
                    chat = {
                        'id': entity.id,
                        'title': title,
                        'username': entity.username if entity.username else None
                    }
                    chats.append(chat)
            
            response_data = json.dumps(chats[start_index:end_index], ensure_ascii=False, indent=4).encode('utf-8')
            await client.disconnect()
            return app.response_class(response=response_data, mimetype='application/json')
        except Exception as e:
            await client.disconnect()
            if "database is locked" in str(e) and i < retries - 1:
                time.sleep(1)
                continue
            return jsonify({'error': str(e)})



@app.route('/api/chat/<int:chat_id>', methods=['GET'])
async def get_chat(chat_id):
    session_file = 'session.session'
    if not os.path.exists(session_file):
        return jsonify({'error': 'Session file not found'})

    client = create_telegram_client()

    retries = 5
    for i in range(retries):
        try:
            await client.connect()
            config = configparser.ConfigParser()
            config.read('config.ini')
            max_msg = config.getint('settings', 'max_msg')
            messages = await client.get_messages(chat_id, limit=max_msg)  # Change limit as needed
            me = await client.get_me()
            messages_list = []

            for message in messages:
                sender_name = None
                if message.sender:
                    if isinstance(message.sender, User):
                        sender_name = message.sender.first_name
                        if not sender_name:
                            sender_name = message.sender.username
                    elif isinstance(message.sender, Channel):
                        sender_name = message.sender.title

                you = True if message.sender_id == me.id else False
                message_text = message.text if message.text else ''

                message_data = {
                    'id': message.id,
                    'text': message_text,
                    'sender_id': message.sender_id,
                    'sender_name': sender_name,
                    'date': message.date.timestamp(),
                    'you': you
                }

                if message.media is not None:
                    if hasattr(message.media, 'photo'):
                        message_data['text'] += "\n(ФОТО)"
                    elif hasattr(message.media, 'document'):
                        if message.media.document.mime_type.startswith('audio'):
                            message_data['text'] += "\n(ГОЛОСОВОЕ СООБЩЕНИЕ)"
                        elif message.media.document.mime_type.startswith('video'):
                            message_data['text'] += "\n(ВИДЕО)"
                        elif message.media.document.mime_type.startswith('image'):
                            message_data['text'] += "\n(ИЗОБРАЖЕНИЕ или СТИКЕР)"
                        elif message.media.document.mime_type.startswith('application') or message.media.document.mime_type.startswith('text'):
                            message_data['text'] += "\n(ФАЙЛ)"
                    elif hasattr(message.media, 'sticker'):
                        message_data['text'] += "\n(СТИКЕР)"

                messages_list.append(message_data)

            await client.disconnect()
            return jsonify(messages_list)
        except Exception as e:
            await client.disconnect()
            if "database is locked" in str(e) and i < retries - 1:
                time.sleep(1)
                continue
            return jsonify({'error': str(e)})
 

@app.route('/api/chatformsg/<int:chat_id>/<path:message_text_encoded>', methods=['GET', 'POST'])
async def send_message(chat_id, message_text_encoded):
    session_file = 'session.session'
    if not os.path.exists(session_file):
        return jsonify({'error': 'Session file not found'})

    client = create_telegram_client()

    retries = 5
    for i in range(retries):
        try:
            await client.connect()

            # Decode message text
            message_text = unquote(message_text_encoded.replace('_', ' '))

            # Send message
            await client.send_message(chat_id, message_text)

            await client.disconnect()
            return jsonify({'status': 'Message sent successfully'})
        except Exception as e:
            await client.disconnect()
            if "database is locked" in str(e) and i < retries - 1:
                time.sleep(1)
                continue
            return jsonify({'error': str(e)})


@app.route('/api/getme', methods=['GET', 'POST'])
async def get_me():
    session_file = 'session.session'
    if not os.path.exists(session_file):
        return jsonify({'error': 'Session file not found'})

    client = create_telegram_client()
    try:
        await client.connect()
        user = await client.get_me()
        user_data = {
            'id': user.id,
            'first_name': user.first_name,
            'last_name': user.last_name
        }
        await client.disconnect()
        return jsonify(user_data)
    except Exception as e:
        await client.disconnect()
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8007)

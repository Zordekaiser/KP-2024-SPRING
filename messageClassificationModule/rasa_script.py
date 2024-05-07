import time
from .normalize import normalize_nouns

import socketio

# Create a Socket.IO client instance
sio = socketio.Client()

normalized_response = None

@sio.on('user_uttered')
def send_message(message):
    sio.emit('user_uttered', {'message': message})  # Отправка сообщения на вебсокет с расой


@sio.on('bot_uttered')
def on_bot_uttered(data):
    global normalized_response
    if data.get('text'):
        response = data['text']
        normalized_response = normalize_nouns(response)
        return normalized_response


@sio.event
def connect():
    sio.emit('session_request', {})
    print("Connected to Rasa")


def connect_to_rasa(input_string):
    sio.connect('http://localhost:5005')  # 'http://localhost:5005'
    send_message(input_string)
    while not normalized_response:
        time.sleep(1)
        print(normalized_response)
    return normalized_response


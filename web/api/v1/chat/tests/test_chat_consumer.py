import pytest
from unittest.mock import patch
from channels.testing import WebsocketCommunicator
from chat.consumers import ChatConsumer


pytestmark = [pytest.mark.django_db, pytest.mark.asyncio]

# Как получать все response с один раз
async def test_chat_connection(mocked_user_1, mocked_user_2, chat, userchat, consumer):
    expected_data_after_connect = {
        'type': 'user_online_event',
        'data': {
            'user_name': mocked_user_1['full_name'],
            'online': True,
            'chat_id': chat.id
            }
        }
    response_after_connect = await consumer.receive_json_from()

    assert response_after_connect == expected_data_after_connect
    data = {
        'command': 'new_message',
        'data': {
            'chat_id': chat.id,
            'body': 'Hi',
            }
        }
    await consumer.send_json_to(data)

    response_after_send_message = await consumer.receive_json_from()

    assert response_after_send_message['type'] == 'new_message_event'
    assert response_after_send_message['data']['chat_id'] == data['data']['chat_id']
    assert response_after_send_message['data']['body'] == data['data']['body']
    assert response_after_send_message['data']['user']['id'] == mocked_user_1['id']
    assert response_after_send_message['data']['user']['full_name'] == mocked_user_1['full_name']
    assert response_after_send_message['data']['user']['avatar'] == mocked_user_1['avatar']

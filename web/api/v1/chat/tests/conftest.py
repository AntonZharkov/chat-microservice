import pytest
from channels.testing import WebsocketCommunicator
from chat.consumers import ChatConsumer
import pytest_asyncio
from unittest.mock import patch
from chat.models import Chat, UserChat

@pytest_asyncio.fixture
async def consumer(mocked_user_1):
    comm = WebsocketCommunicator(ChatConsumer.as_asgi(), path='ws/chat/')
    with patch.dict(comm.scope, {'user': mocked_user_1}):
        connected, _ = await comm.connect()
        assert connected
        yield comm
        await comm.disconnect()


@pytest.fixture
def mocked_user_1() -> dict:
    return {
        'id': 1,
        'full_name': 'Anton Zharkov',
        'avatar': '',
    }

@pytest.fixture
def mocked_user_2() -> dict:
    return {
        'id': 2,
        'full_name': 'Ivan Ivanov',
        'avatar': '',
    }


@pytest_asyncio.fixture
async def chat(mocked_user_1, mocked_user_2):
    return await Chat.objects.acreate(
        name={
            f'id_{mocked_user_1["id"]}': mocked_user_2["full_name"],
            f'id_{mocked_user_2["id"]}': mocked_user_1["full_name"],
        }
    )

@pytest_asyncio.fixture
async def userchat(mocked_user_1, mocked_user_2, chat):
    userchats = [UserChat(user=mocked_user_1["id"], chat=chat), UserChat(user=mocked_user_2["id"], chat=chat)]
    return await UserChat.objects.abulk_create(userchats)

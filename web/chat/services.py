import httpx


class ChatService:
    async def get_user_by_jwt(self, token: str):
        async with httpx.AsyncClient() as client:
            response = await client.get('/api/...').json()
            return response.get('user_id', '')

import pytest


class TestChat:

    @pytest.mark.llm
    async def test_chat_reply(self, auth_client):
        response = await auth_client.post(
            "/chat",
            json={"message": "What is 2+2?", "conversation_id": None},
        )
        assert response.status_code == 200
        data = response.json()
        assert "reply" in data
        assert len(data["reply"]) > 0
        assert "conversation_id" in data
        assert "message_id" in data

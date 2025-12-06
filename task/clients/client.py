from aidial_client import Dial, AsyncDial

from task.clients.base import BaseClient
from task.constants import DIAL_ENDPOINT
from task.models.message import Message
from task.models.role import Role


class DialClient(BaseClient):

    def __init__(self, deployment_name: str):
        super().__init__(deployment_name)
        # 1. Create Dial client (synchronous)
        self._client = Dial(
            base_url=DIAL_ENDPOINT,
            api_key=self._api_key
        )
        # 2. Create AsyncDial client (asynchronous)
        self._async_client = AsyncDial(
            base_url=DIAL_ENDPOINT,
            api_key=self._api_key
        )

    def get_completion(self, messages: list[Message]) -> Message:
        # 1. Create chat completions with client
        # Convert messages to dict format using to_dict() method
        messages_dicts = [msg.to_dict() for msg in messages]

        response = self._client.chat.completions.create(
            deployment_name=self._deployment_name,
            messages=messages_dicts,
            stream=False
        )

        # 3. If choices are not present then raise Exception
        if not response.choices:
            raise Exception("No choices in response found")

        # 2. Get content from response, print it and return message with assistant role and content
        content = response.choices[0].message.content or ""
        print(content)

        return Message(role=Role.AI, content=content)

    async def stream_completion(self, messages: list[Message]) -> Message:
        # 1. Create chat completions with async client (stream=True)
        messages_dicts = [msg.to_dict() for msg in messages]

        chunks = await self._async_client.chat.completions.create(
            deployment_name=self._deployment_name,
            messages=messages_dicts,
            stream=True
        )

        # 2. Create array with 'contents' name to collect all content chunks
        contents = []

        # 3. Make async loop from chunks
        async for chunk in chunks:
            if chunk.choices and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                if delta and delta.content:
                    # 4. Print content chunk and collect it in contents array
                    print(delta.content, end='')
                    contents.append(delta.content)

        # 5. Print empty row (end of streaming)
        print()

        # 6. Return Message with assistant role and collected content
        full_content = "".join(contents)
        return Message(role=Role.AI, content=full_content)

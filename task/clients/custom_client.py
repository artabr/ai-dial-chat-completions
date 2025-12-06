import json
import aiohttp
import requests

from task.clients.base import BaseClient
from task.constants import DIAL_ENDPOINT
from task.models.message import Message
from task.models.role import Role


class CustomDialClient(BaseClient):

    def __init__(self, deployment_name: str):
        super().__init__(deployment_name)
        self._endpoint = DIAL_ENDPOINT + f"/openai/deployments/{deployment_name}/chat/completions"

    def get_completion(self, messages: list[Message]) -> Message:
        # 1. Create headers dict with api-key and Content-Type
        headers = {
            "api-key": self._api_key,
            "Content-Type": "application/json"
        }

        # 2. Create request_data dictionary with messages
        request_data = {
            "messages": [msg.to_dict() for msg in messages]
        }

        # Print request for debugging (as per task requirement #10)
        print(f"\n[DEBUG] Request URL: {self._endpoint}")
        print(f"[DEBUG] Request Body: {json.dumps(request_data, indent=2)}")

        # 3. Make POST request using requests.post()
        response = requests.post(
            url=self._endpoint,
            headers=headers,
            json=request_data
        )

        # 5. If status code != 200 then raise Exception
        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}: {response.text}")

        # Print response for debugging (as per task requirement #10)
        print(f"[DEBUG] Response: {json.dumps(response.json(), indent=2)}")

        # 4. Get content from response, print it and return message with assistant role and content
        response_json = response.json()
        if not response_json.get("choices"):
            raise Exception("No choices in response found")

        choices = response_json.get("choices", [])
        content = choices[0].get("message", {}).get("content")
        print(content)

        return Message(Role.AI, content)

    async def stream_completion(self, messages: list[Message]) -> Message:
        # 1. Create headers dict with api-key and Content-Type
        headers = {
            "api-key": self._api_key,
            "Content-Type": "application/json"
        }

        # 2. Create request_data dictionary with stream=True and messages
        request_data = {
            "stream": True,
            "messages": [msg.to_dict() for msg in messages]
        }

        # Print request for debugging (as per task requirement #10)
        print(f"\n[DEBUG] Request URL: {self._endpoint}")
        print(f"[DEBUG] Request Body: {json.dumps(request_data, indent=2)}")

        # 3. Create empty list called 'contents' to store content snippets
        contents = []

        # 4. Create aiohttp.ClientSession() using 'async with' context manager
        async with aiohttp.ClientSession() as session:
            # 5. Inside session, make POST request using session.post()
            async with session.post(
                url=self._endpoint,
                json=request_data,
                headers=headers
            ) as response:
                # 6. Get content from chunks
                if response.status == 200:
                    async for line in response.content:
                        decoded_line = line.decode("utf-8").strip()

                        # Skip empty lines
                        if not decoded_line:
                            continue

                        if decoded_line.startswith("data: "):
                            data = decoded_line[6:].strip()
                            if data != "[DONE]":

                                # Print raw chunk for debugging
                                print(f"[DEBUG] Chunk: {decoded_line}")

                                # Get content snippet from the chunk
                                content_snippet = self._get_content_snippet(decoded_line)
                                if content_snippet:
                                    print(content_snippet, end='')
                                    contents.append(content_snippet)
                else:
                    error_text = await response.text()
                    print(f"{response.status} {error_text}")

                # Print empty row (end of streaming)
                print()

                # Return as assistant message
                full_content = "".join(contents)
                return Message(role=Role.AI, content=full_content)

    def _get_content_snippet(self, data_chunk: str) -> str:
        """Parse streaming data chunks to extract content.

        Chunks start with 'data: ' prefix (6 chars).
        Final chunk is 'data: [DONE]'.
        """
        try:
            # Parse the JSON
            data = json.loads(data_chunk)

            # Extract content from delta
            choices = data.get("choices", [])
            if choices:
                delta = choices[0].get("delta", {})
                content = delta.get("content", '')
                return content
            return ''
        except json.JSONDecodeError:
            return ''

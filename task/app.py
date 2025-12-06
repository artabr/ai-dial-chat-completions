import asyncio

from task.clients.client import DialClient
from task.constants import DEFAULT_SYSTEM_PROMPT
from task.models.conversation import Conversation
from task.models.message import Message
from task.models.role import Role


async def start(stream: bool) -> None:
    # 1.1. Create DialClient (using aidial-client library)
    # You can get available deployment_name via https://ai-proxy.lab.epam.com/openai/models
    client = DialClient(deployment_name="gpt-4o")

    # 1.2. Alternatively, create CustomDialClient (using raw HTTP requests)
    # Uncomment the line below to use CustomDialClient instead:
    # client = CustomDialClient(deployment_name="gpt-4o")

    # 2. Create Conversation object
    conversation = Conversation()

    # 3. Get System prompt from console or use default
    print("Provide System prompt or press 'enter' to continue.")
    system_prompt = input("> ").strip()
    if not system_prompt:
        system_prompt = DEFAULT_SYSTEM_PROMPT

    # Add system message to conversation history
    conversation.add_message(Message(role=Role.SYSTEM, content=system_prompt))

    print("\nType your question or 'exit' to quit.")

    # 4. Use infinite cycle (while True)
    while True:
        # Get user message from console
        user_input = input("> ").strip()

        # 5. If user message is 'exit' then stop the loop
        if user_input.lower() == "exit":
            print("Exiting the chat. Goodbye!")
            break

        # 6. Add user message to conversation history (role 'user')
        conversation.add_message(Message(role=Role.USER, content=user_input))

        # 7. If 'stream' param is true -> call stream_completion()
        #    else -> call get_completion()
        if stream:
            print("AI: ", end="", flush=True)
            response_message = await client.stream_completion(conversation.get_messages())
        else:
            response_message = client.get_completion(conversation.get_messages())
            print(f"AI: {response_message.content}")

        # 8. Add generated message to history
        conversation.add_message(response_message)
        print()


asyncio.run(
    start(True)
)

import os
import asyncio
import json
from dotenv import load_dotenv
from contextlib import AsyncExitStack

from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition
from openai.types.responses.response_input_param import ResponseInputParam

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


# ---------------------------------------------------------
# ENV SETUP
# ---------------------------------------------------------

os.system("cls" if os.name == "nt" else "clear")

load_dotenv()

project_endpoint = os.getenv("PROJECT_ENDPOINT")
model_deployment = os.getenv("MODEL_DEPLOYMENT_NAME")


# ---------------------------------------------------------
# MCP SERVER CONNECTION
# ---------------------------------------------------------

async def connect_to_server(exit_stack: AsyncExitStack) -> ClientSession:
    server_params = StdioServerParameters(
        command="python",
        args=["server.py"],
        env=None,
    )

    stdio_transport = await exit_stack.enter_async_context(
        stdio_client(server_params)
    )

    stdio, write = stdio_transport

    session = await exit_stack.enter_async_context(
        ClientSession(stdio, write)
    )

    await session.initialize()

    response = await session.list_tools()

    print(
        "MCP tools available:",
        [tool.name for tool in response.tools],
    )

    return session


# ---------------------------------------------------------
# CHAT LOOP
# ---------------------------------------------------------

async def chat_loop(session: ClientSession):

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(
            endpoint=project_endpoint,
            credential=credential,
        ) as project_client,
        project_client.get_openai_client() as openai_client,
    ):

        response = await session.list_tools()
        tools = response.tools

        functions_dict = {}

        def make_tool_func(tool_name):
            async def tool_func(**kwargs):
                result = await session.call_tool(
                    tool_name,
                    kwargs,
                )
                return result
            return tool_func

        for tool in tools:
            functions_dict[tool.name] = make_tool_func(
                tool.name
            )

        agent = project_client.agents.create_version(
            agent_name="inventory-agent",
            definition=PromptAgentDefinition(
                model=model_deployment,
                instructions="""
You are an inventory assistant.

Rules:
- Recommend restock if inventory < 10 and weekly sales > 15
- Recommend clearance if inventory > 20 and weekly sales < 5
""",
                tools=[],
            ),
        )

        print("Agent created:", agent.name)

        conversation = openai_client.conversations.create()

        input_list: ResponseInputParam = []

        while True:

            user_input = input(
                "\nUSER (type 'quit' to exit): "
            ).strip()

            if user_input.lower() == "quit":
                break

            openai_client.conversations.items.create(
                conversation_id=conversation.id,
                items=[
                    {
                        "type": "message",
                        "role": "user",
                        "content": user_input,
                    }
                ],
            )

            response = openai_client.responses.create(
                conversation=conversation.id,
                input=input_list,
                extra_body={
                    "agent": {
                        "name": agent.name,
                        "type": "agent_reference",
                    }
                },
            )

            if response.status == "failed":
                print("Agent failed:", response.error)
                continue

            input_list = []

            for item in response.output:

                if item.type == "function_call":

                    function_name = item.name
                    args = json.loads(item.arguments)

                    tool_func = functions_dict.get(
                        function_name
                    )

                    if not tool_func:
                        continue

                    result = await tool_func(**args)

                    input_list.append(
                        {
                            "type": "function_call_output",
                            "call_id": item.call_id,
                            "output": result.content[0].text,
                        }
                    )

            if input_list:

                response = openai_client.responses.create(
                    input=input_list,
                    previous_response_id=response.id,
                    extra_body={
                        "agent": {
                            "name": agent.name,
                            "type": "agent_reference",
                        }
                    },
                )

            print("\nAGENT RESPONSE:")
            print(response.output_text)

        project_client.agents.delete_version(
            agent_name=agent.name,
            agent_version=agent.version,
        )

        print("Inventory agent deleted.")


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

async def main():

    async with AsyncExitStack() as exit_stack:

        session = await connect_to_server(
            exit_stack
        )

        await chat_loop(session)


if __name__ == "__main__":
    asyncio.run(main())
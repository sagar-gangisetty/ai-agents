import os
import asyncio
import json
from dotenv import load_dotenv
from contextlib import AsyncExitStack

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition, FunctionTool
from azure.identity import DefaultAzureCredential
from openai.types.responses.response_input_param import (
    FunctionCallOutput,
    ResponseInputParam,
)

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


# Clear console
os.system("cls" if os.name == "nt" else "clear")

# Load env
load_dotenv()
project_endpoint = os.getenv("PROJECT_ENDPOINT")
model_deployment = os.getenv("MODEL_DEPLOYMENT_NAME")


async def connect_to_server(exit_stack: AsyncExitStack):
    server_params = StdioServerParameters(
        command="python",
        args=["server.py"],
        env=None,
    )

    stdio, write = await exit_stack.enter_async_context(
        stdio_client(server_params)
    )

    session = await exit_stack.enter_async_context(
        ClientSession(stdio, write)
    )
    await session.initialize()

    response = await session.list_tools()
    tools = response.tools
    print("Connected to MCP tools:", [t.name for t in tools])

    return session


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

        def make_tool_func(tool_name):
            async def tool_func(**kwargs):
                result = await session.call_tool(tool_name, kwargs)
                return result

            tool_func.__name__ = tool_name
            return tool_func

        functions_dict = {
            tool.name: make_tool_func(tool.name)
            for tool in tools
        }

        mcp_function_tools: list[FunctionTool] = []
        for tool in tools:
            mcp_function_tools.append(
                FunctionTool(
                    name=tool.name,
                    description=tool.description,
                    parameters={
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False,
                    },
                    strict=True,
                )
            )

        agent = project_client.agents.create_version(
            agent_name="inventory-agent",
            definition=PromptAgentDefinition(
                model=model_deployment,
                instructions="""
You are an inventory assistant.

Rules:
- Restock if inventory < 10 and weekly sales > 15
- Clearance if inventory > 20 and weekly sales < 5
""",
                tools=mcp_function_tools,
            ),
        )

        conversation = openai_client.conversations.create()
        input_list: ResponseInputParam = []

        while True:
            user_input = input("USER > ").strip()
            if user_input.lower() == "quit":
                break

            openai_client.conversations.items.create(
                conversation_id=conversation.id,
                items=[{
                    "type": "message",
                    "role": "user",
                    "content": user_input,
                }],
            )

            response = openai_client.responses.create(
                conversation=conversation.id,
                input=input_list,
                extra_body={
                    "agent": {"name": agent.name, "type": "agent_reference"}
                },
            )

            for item in response.output:
                if item.type == "function_call":
                    fn = functions_dict[item.name]
                    args = json.loads(item.arguments)
                    result = await fn(**args)

                    input_list.append(
                        FunctionCallOutput(
                            type="function_call_output",
                            call_id=item.call_id,
                            output=result.content[0].text,
                        )
                    )

            if input_list:
                response = openai_client.responses.create(
                    input=input_list,
                    previous_response_id=response.id,
                    extra_body={
                        "agent": {"name": agent.name, "type": "agent_reference"}
                    },
                )

            print("AGENT >", response.output_text)

        project_client.agents.delete_version(
            agent_name=agent.name,
            agent_version=agent.version,
        )


async def main():
    async with AsyncExitStack() as stack:
        session = await connect_to_server(stack)
        await chat_loop(session)


if __name__ == "__main__":
    asyncio.run(main())

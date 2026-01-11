import asyncio
from backboard import BackboardClient

from config import BACKBOARD_API_KEY
from tools.create_project import create_project_tool, create_project
from tools.create_task import create_task_tool, create_task

async def main():
    # Initialize the Backboard client
    client = BackboardClient(api_key=BACKBOARD_API_KEY)

    # Create an assistant with the tool
    assistant = await client.create_assistant(
        name="Project Assistant",
        description="An assistant that can help with project management tasks.",
        tools=[
            create_project_tool,
            create_task_tool
        ]
    )

    # Create a message thread
    thread = await client.create_thread(assistant.assistant_id)

    while True:
        print("Hello there! How can I help?")
        message = input("> ").strip()

        if message == "":
            continue

        message += " For this project, define a name, description, a status explanation for a NOT STARTED status, and a whether the project should be public."
        message += " If asked to at the beginning of this message, create important tasks for the project with a subject, description, start date, due date, and priority level (low, medium, high, immediate). Tasks should be tied to the developement of the project. (like setup authentication, choose database, etc.) Do not define tasks tied to business objectives like planning, launch or maintenance. Also define a timeline for the project by choosing accordingly the start and due dates of each task."

        # Send a message 
        response = await client.add_message(
            thread_id=thread.thread_id,
            content=message,
            stream=False
        )

        # Check if the assistant requires action (tool call)
        if response.status == "REQUIRES_ACTION" and response.tool_calls:
            tool_outputs = []
            print("Assistant requested tool calls.")
            # Process each tool call
            for tc in response.tool_calls:
                match tc.function.name:
                    case "create_project":
                        print("Project creation tool called.")
                        tool_outputs.append(create_project(tc))
                    case "create_task":
                        print("Task creation tool called.")
                        tool_outputs.append(create_task(tc))

            # Submit the tool outputs back to continue the conversation
            final_response = await client.submit_tool_outputs(
                thread_id=thread.thread_id,
                run_id=response.run_id,
                tool_outputs=tool_outputs
            )
            print(final_response.content)


if __name__ == "__main__":
    asyncio.run(main())
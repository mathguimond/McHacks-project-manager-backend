import asyncio
from backboard import BackboardClient

from flask import Flask, request, jsonify
from flask_cors import CORS

from config import BACKBOARD_API_KEY
from tools.create_project import create_project_tool, create_project
from tools.create_task import create_task_tool, create_task
from tools.update_project import update_project_tool, update_project
from tools.update_task import update_task_tool, update_task

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["https://openproject.chiem.me"]}})


@app.route("/sendMessage", methods=["POST"])
def receive_message():
    data = request.get_json()

    if not data or "message" not in data:
        return jsonify({"error": "Missing 'message' field"}), 400

    message = data["message"]
    asyncio.run(sendMessage(message))

    return jsonify({"status": "ok", "received": message}), 200


async def sendMessage(message: str):
    # Initialize the Backboard client
    client = BackboardClient(api_key=BACKBOARD_API_KEY)

    # Create an assistant with the tool
    assistant = await client.create_assistant(
        name="Project Assistant",
        description="An assistant that can help with project management tasks.",
        tools=[
            create_project_tool,
            create_task_tool,
            update_project_tool,
            update_task_tool
        ]
    )

    # Create a message thread
    thread = await client.create_thread(assistant.assistant_id)


    data = request.get_json(force=True)
    
    if message == "":
        return

    message += " This is the end of the beginning message. Now, based on this message beginning, consider the following instructions (only consider one set of instructions based on what is present at the beginning of the message):"
    
    # Create project and tasks instructions
    message += " If asked to create a new project at the beginning of this message, consider the following instructions in brakets: [For this project, define a name, description, a status explanation for a NOT STARTED status, and a whether the project should be public."
    message += " If asked to at the beginning of this message, create important tasks for the project with a subject, description, start date, due date, and priority level (low, medium, high, immediate). Tasks should be tied to the developement of the project. (Tasks that require actual code implementation like setup authentication) Do not define tasks tied to business objectives like planning, launch or maintenance. Give at least 10 tasks that give a good overview of what should be done to implement this particular project. Also define a timeline for the project by choosing accordingly the start and due dates of each task.]"

    # Create a single task instruction
    message += " Otherwise, if asked to create a single task at the message beginning, consider the following instructions in brakets: [Create a new task. For this task, define a subject, description, start date, due date, and priority level (low, medium, high, immediate) based on what is present at the beginning of this message. Expand the description of the task to give more details about what needs to be done.]"

    # Update a project instruction
    message += " Otherwise, if asked to update a project at the beginning of this message, consider the following instructions in brakets: [Update the specified project with any new details provided at the beginning of this message. Make sure to only update the fields that have been changed or added.]"

    # Update a task instruction
    message += " Otherwise, if asked to update a task at the beginning of this message, consider the following instructions in brakets: [Update the specified task with any new details provided at the beginning of this message. Make sure to only update the fields that have been changed or added.]"

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
                case "update_project":
                    print("Project update tool called.")
                    tool_outputs.append(update_project(tc))
                case "update_task":
                    print("Task update tool called.")
                    tool_outputs.append(update_task(tc))

        # Submit the tool outputs back to continue the conversation
        final_response = await client.submit_tool_outputs(
            thread_id=thread.thread_id,
            run_id=response.run_id,
            tool_outputs=tool_outputs
        )
        print(final_response.content)




    
    
    return jsonify(id=1, **data)

            



if __name__ == "__main__":
    app.run(debug=False, port=8000)
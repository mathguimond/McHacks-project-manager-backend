import asyncio
import threading
import datetime
from backboard import BackboardClient

from flask import Flask, json, request, jsonify
from flask_cors import CORS

from config import BACKBOARD_API_KEY
from tools.create_project import create_project_tool, create_project
from tools.create_task import create_task_tool, create_task
from tools.update_project import update_project_tool, update_project
from tools.update_task import update_task_tool, update_task

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["https://openproject.chiem.me"]}})

# --- Option B: one persistent event loop ---
loop = asyncio.new_event_loop()

def loop_runner():
    asyncio.set_event_loop(loop)
    loop.run_forever()

threading.Thread(target=loop_runner, daemon=True).start()
# ------------------------------------------


@app.route("/sendMessage", methods=["POST"])
def receive_message():
    data = request.get_json()

    if not data or "message" not in data:
        return jsonify({"error": "Missing 'message' field"}), 400

    message = data["message"]

    # --- changed: schedule coroutine on persistent loop instead of asyncio.run ---
    future = asyncio.run_coroutine_threadsafe(sendMessage(message), loop)
    response = future.result(timeout=120)  # increase if needed
    # --------------------------------------------------------------------------

    print(response)
    return jsonify({"status": "ok", "message": response}), 200


async def sendMessage(message: str):
    if message == "":
        return

    message += f" This is the end of the beginning message. Today's date is {datetime.datetime.now()}. Now, based on this message beginning, consider the following instructions (only consider one set of instructions based on what is present at the beginning of the message):"
    
    message += " If asked to create a new project at the beginning of this message, consider the following instructions in brakets: [For this project, define a name, description, a status explanation for a NOT STARTED status, and a whether the project should be public."
    message += " If asked to at the beginning of this message, create important tasks for the project with a subject, description, start date, due date, and priority level (low, medium, high, immediate). Tasks should be tied to the developement of the project. (Tasks that require actual code implementation like setup authentication) Do not define tasks tied to business objectives like planning, launch or maintenance. Give at least 10 tasks that give a good overview of what should be done to implement this particular project. Also define a timeline for the project by choosing accordingly the start and due dates of each task.]"

    message += " Otherwise, if asked to create a single task at the message beginning, consider the following instructions in brakets: [Create a new task. For this task, define a subject, description, start date, due date, and priority level (low, medium, high, immediate) based on what is present at the beginning of this message. Expand the description of the task to give more details about what needs to be done.]"

    message += " Otherwise, if asked to update a project at the beginning of this message, consider the following instructions in brakets: [Update the specified project with any new details provided at the beginning of this message. Make sure to only update the fields that have been changed or added.]"

    message += " Otherwise, if asked to update a task at the beginning of this message, consider the following instructions in brakets: [Update the specified task with any new details provided at the beginning of this message. Make sure to only update the fields that have been changed or added.]"

    message += " Don't give a long answer with explanations on what you did (like describing tasks created). Simply respond with the result like for example 'I created the project X and generated relevent tasks'. If no set of instructions apply, do not create or update a project or task. Instead, simply respond to the message as a helpful assistant would."

    response = await client.add_message(
        thread_id=thread.thread_id,
        content=message,
        stream=False
    )

    if response.status == "REQUIRES_ACTION" and response.tool_calls:
        tool_outputs = []
        print("Assistant requested tool calls.")

        for tc in response.tool_calls:
            try:
                match tc.function.name:
                    case "create_project":
                        print("Creating project...")
                        result = create_project(tc)
                    case "create_task":
                        print("Creating task...")
                        result = create_task(tc)
                    case "update_project":
                        print("Updating project...")
                        result = update_project(tc)
                    case "update_task":
                        print("Updating task...")
                        result = update_task(tc)
                    case _:
                        result = {"error": f"Unknown tool {tc.function.name}"}
            except Exception as e:
                result = {"error": str(e)}

            tool_outputs.append({
                "tool_call_id": tc.id,
                "output": json.dumps(result)
            })

        final_response = await client.submit_tool_outputs(
            thread_id=thread.thread_id,
            run_id=response.run_id,
            tool_outputs=tool_outputs
        )

        return final_response.content
    
    return response.content


async def main():
    global client
    client = BackboardClient(api_key=BACKBOARD_API_KEY)

    global assistant
    assistant = await client.create_assistant(
        name="Project Assistant",
        description="An assistant that can help with project management tasks.",
        memory="Auto",
        tools=[
            create_project_tool,
            create_task_tool,
            update_project_tool,
            update_task_tool
        ]
    )

    global thread
    thread = await client.create_thread(assistant.assistant_id)


if __name__ == "__main__":
    # --- changed: init on persistent loop, not asyncio.run ---
    asyncio.run_coroutine_threadsafe(main(), loop).result()
    # -------------------------------------------------------
    app.run(debug=False, port=8000)

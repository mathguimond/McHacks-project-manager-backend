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

# GitHub tools
from tools.github_repo import (
    github_search_code_tool,
    github_get_file_tool,
    github_search_code,
    github_get_file
)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["https://openproject.chiem.me"]}})

# --- one persistent event loop ---
loop = asyncio.new_event_loop()

def loop_runner():
    asyncio.set_event_loop(loop)
    loop.run_forever()

threading.Thread(target=loop_runner, daemon=True).start()
# --------------------------------


# --- helpers to support tool_calls as objects OR dicts ---
class _FnShim:
    def __init__(self, name, parsed_arguments):
        self.name = name
        self.parsed_arguments = parsed_arguments

class _ToolCallShim:
    def __init__(self, tc_dict):
        self.id = tc_dict.get("id")
        fn = tc_dict.get("function", {}) or {}
        name = fn.get("name")

        parsed = fn.get("parsed_arguments", None)
        if parsed is None or parsed == {}:
            args_raw = fn.get("arguments", None)
            if isinstance(args_raw, str) and args_raw.strip():
                try:
                    parsed = json.loads(args_raw)
                except Exception:
                    parsed = {}
            elif isinstance(args_raw, dict):
                parsed = args_raw
            else:
                parsed = {}

        self.function = _FnShim(name, parsed)

def _normalize_tool_call(tc):
    if hasattr(tc, "function") and hasattr(tc, "id"):
        return tc
    if isinstance(tc, dict):
        return _ToolCallShim(tc)
    raise TypeError(f"Unsupported tool call type: {type(tc)}")
# --------------------------------------------------------


@app.route("/sendMessage", methods=["POST"])
def receive_message():
    data = request.get_json()

    if not data or "message" not in data:
        return jsonify({"error": "Missing 'message' field"}), 400

    message = data["message"]

    future = asyncio.run_coroutine_threadsafe(sendMessage(message), loop)
    response = future.result(timeout=120)

    if response is None:
        response = ""

    print("Response:", response)
    return jsonify({"status": "ok", "message": response}), 200


async def sendMessage(message: str):
    if message == "":
        return ""

    # --- NEW: per-run limiter state ---
    github_search_calls = 0
    # -------------------------------

    message += f" This is the end of the beginning message. Today's date is {datetime.datetime.now()}. Now, based on this message beginning, consider the following instructions (only consider one set of instructions based on what is present at the beginning of the message):"
    
    message += " If asked to create a new project at the beginning of this message, consider the following instructions in brakets: [For this project, define a name, description, a status explanation for a NOT STARTED status, and a whether the project should be public."
    message += " If asked to at the beginning of this message, create important tasks for the project with a subject, description, start date, due date, and priority level (low, medium, high, immediate). Tasks should be tied to the developement of the project. (Tasks that require actual code implementation like setup authentication) Do not define tasks tied to business objectives like planning, launch or maintenance. Give at least 10 tasks that give a good overview of what should be done to implement this particular project. Also define a timeline for the project by choosing accordingly the start and due dates of each task.]"

    message += " Otherwise, if asked to create a single task at the message beginning, consider the following instructions in brakets: [Create a new task. For this task, define a subject, description, start date, due date, and priority level (low, medium, high, immediate) based on what is present at the beginning of this message. Expand the description of the task to give more details about what needs to be done.]"

    message += " Otherwise, if asked to update a project at the beginning of this message, consider the following instructions in brakets: [Update the specified project with any new details provided at the beginning of this message. Make sure to only update the fields that have been changed or added.]"

    message += " Otherwise, if asked to update a task at the beginning of this message, consider the following instructions in brakets: [Update the specified task with any new details provided at the beginning of this message. Make sure to only update the fields that have been changed or added.]"

    # Encourage fewer search calls
    message += " If the request involves GitHub context, avoid calling github_search_code repeatedly (rate-limited). Prefer github_get_file for known files like README.md or key entrypoints."
    message += " If you need GitHub context and the repository is not specified at the beginning of the message, ask the user to provide the repo in the form owner/repo before calling GitHub tools."
    message += " Never output secrets (tokens, .env contents, private keys). If you detect secrets, do not print them."

    message += " Don't give a long answer with explanations on what you did (like describing tasks created). Simply respond with the result like for example 'I created the project X and generated relevent tasks'. If no set of instructions apply, do not create or update a project or task. Instead, simply respond to the message as a helpful assistant would."

    response = await client.add_message(
        thread_id=thread.thread_id,
        memory="Auto",
        content=message,
        stream=False
    )

    while getattr(response, "status", None) == "REQUIRES_ACTION" and getattr(response, "tool_calls", None):
        tool_outputs = []
        print("Assistant requested tool calls.")

        normalized_tool_calls = [_normalize_tool_call(tc) for tc in response.tool_calls]

        for tc in normalized_tool_calls:
            try:
                tool_name = tc.function.name

                # --- NEW: hard cap github_search_code to 1 call per /sendMessage run ---
                if tool_name == "github_search_code":
                    github_search_calls += 1
                    if github_search_calls > 1:
                        result = {
                            "tool_call_id": tc.id,
                            "output": json.dumps({
                                "error": "github_search_code call blocked to prevent rate limits. Use github_get_file for README.md or list files first."
                            })
                        }
                        tool_outputs.append(result)
                        continue
                # ---------------------------------------------------------------------

                match tool_name:
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
                    case "github_search_code":
                        print("Searching GitHub code...")
                        result = github_search_code(tc)
                    case "github_get_file":
                        print("Fetching GitHub file...")
                        result = github_get_file(tc)
                    case _:
                        result = {"tool_call_id": tc.id, "output": json.dumps({"error": f"Unknown tool {tool_name}"})}

            except Exception as e:
                result = {"tool_call_id": tc.id, "output": json.dumps({"error": str(e)})}

            tool_outputs.append(result)

            # --- NEW: tiny delay after each GitHub call to reduce burstiness ---
            if tool_name in ("github_search_code", "github_get_file"):
                await asyncio.sleep(0.2)
            # ------------------------------------------------------------------

        print("Tool outputs:", tool_outputs)

        response = await client.submit_tool_outputs(
            thread_id=thread.thread_id,
            run_id=response.run_id,
            tool_outputs=tool_outputs
        )

    return getattr(response, "content", None) or ""


async def main():
    global client
    client = BackboardClient(api_key=BACKBOARD_API_KEY)

    global assistant
    assistant = await client.create_assistant(
        name="Project Assistant",
        description="An assistant that can help with project management tasks.",
        tools=[
            create_project_tool,
            create_task_tool,
            update_project_tool,
            update_task_tool,
            github_search_code_tool,
            github_get_file_tool
        ]
    )

    global thread
    thread = await client.create_thread(assistant.assistant_id)


if __name__ == "__main__":
    asyncio.run_coroutine_threadsafe(main(), loop).result()
    app.run(debug=False, port=8000)

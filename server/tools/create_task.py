from test import createTask
import json

create_task_tool = {
        "type": "function",
        "function": {
            "name": "create_task",
            "description": "Create tasks for a new project with a subject, description, start date, due date, and priority level",
            "parameters": {
                "type": "object",
                "properties": {
                    "projectName": {"type": "string", "description": "Project name to which the task belongs"},
                    "subject": {"type": "string", "description": "Task subject/title"},
                    "description": {"type": "string", "description": "Task description"},
                    "startDate": {"type": "string", "description": "Task start date in YYYY-MM-DD format"},
                    "dueDate": {"type": "string", "description": "Task due date in YYYY-MM-DD format"},
                    "priority": {"type": "string", "description": "Task priority level (low, medium, high, immediate)"}
                },
                "required": ["projectName", "subject", "startDate", "dueDate"]
            }
        }
    }

def create_task(tc) -> dict[str, int]:
    # Get parsed arguments (required parameters are guaranteed by API)
    args = tc.function.parsed_arguments
    projectName = args["projectName"]
    subject = args["subject"]
    startDate = args["startDate"]
    dueDate = args["dueDate"]
    description = args.get("description", "")
    priority = args.get("priority", "medium")

    # Call the actual function to create the project
    status_code = createTask(projectName, subject, startDate, dueDate, description, priority)

    taskData = {
        "projectName": projectName,
        "subject": subject,
        "startDate": startDate,
        "dueDate": dueDate,
        "description": description,
        "priority": priority,
        "status_code": status_code
    }
    
    return {
        "tool_call_id": tc.id,
        "output": json.dumps(taskData)
    }
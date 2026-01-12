from test import updateTask
import json

update_task_tool = {
        "type": "function",
        "function": {
            "name": "update_task",
            "description": "Update a task using the associated project name and task subject, and by providing an optional new subject, description, start date, due date, and/or priority level",
            "parameters": {
                "type": "object",
                "properties": {
                    "projectName": {"type": "string", "description": "Project name to which the task belongs"},
                    "subject": {"type": "string", "description": "Current task subject/title"},
                    "newSubject": {"type": "string", "description": "New task subject/title"},
                    "newDescription": {"type": "string", "description": "New task description"},
                    "newStartDate": {"type": "string", "description": "New task start date in YYYY-MM-DD format"},
                    "newDueDate": {"type": "string", "description": "New task due date in YYYY-MM-DD format"},
                    "newPriority": {"type": "string", "description": "New task priority level (low, medium, high, immediate)"}
                },
                "required": ["projectName", "subject"]
            }
        }
    }

def update_task(tc) -> dict[str, int]:
    # Get parsed arguments (required parameters are guaranteed by API)
    args = tc.function.parsed_arguments
    projectName = args["projectName"]
    subject = args["subject"]
    newSubject = args.get("newSubject", None)
    newDescription = args.get("newDescription", None)
    newStartDate = args.get("newStartDate", None)
    newDueDate = args.get("newDueDate", None)
    newPriority = args.get("newPriority", None)

    # Call the actual function to update the task
    status_code = updateTask(projectName, subject, newSubject, newDescription, newStartDate, newDueDate, newPriority)

    updateTaskData = {
        "projectName": projectName,
        "subject": subject,
        "newSubject": newSubject,
        "newDescription": newDescription,
        "newStartDate": newStartDate,
        "newDueDate": newDueDate,
        "newPriority": newPriority,
        "status_code": status_code
    }
    
    return {
        "tool_call_id": tc.id,
        "output": json.dumps(updateTaskData)
    }
from test import updateProject
import json

update_project_tool = {
        "type": "function",
        "function": {
            "name": "update_project",
            "description": "Update an existing project using the project name and by providing an optional new name, description, public status and/or status explanation",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Current project name"},
                    "newName": {"type": "string", "description": "New project name"},
                    "newPublic": {"type": "boolean", "description": "New public status (whether the project is public or not)"},
                    "newDescription": {"type": "string", "description": "New Project description"},
                    "newStatusExplanation": {"type": "string", "description": "New explanation of the project status"}
                },
                "required": ["name"]
            }
        }
    }



def update_project(tc) -> dict[str, int]:
    # Get parsed arguments (required parameters are guaranteed by API)
    args = tc.function.parsed_arguments
    name = args["name"]
    newName = args.get("newName", None)
    newPublic = args.get("newPublic", None)
    newDescription = args.get("newDescription", None)
    newStatusExplanation = args.get("newStatusExplanation", None)

    # Call the actual function to update the project
    status_code = updateProject(name, newName, newPublic, newDescription, newStatusExplanation)

    updateProjectData = {
        "name": name,
        "newName": newName,
        "newPublic": newPublic,
        "newDescription": newDescription,
        "newStatusExplanation": newStatusExplanation,
        "status_code": status_code
    }
    
    return {
        "tool_call_id": tc.id,
        "output": json.dumps(updateProjectData)
    }


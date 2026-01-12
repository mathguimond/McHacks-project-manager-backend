from test import createProject
import json

create_project_tool = {
        "type": "function",
        "function": {
            "name": "create_project",
            "description": "Create a new project with a name and optional description, public status and status explanation",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Project name"},
                    "public": {"type": "boolean", "description": "Whether the project is public"},
                    "description": {"type": "string", "description": "Project description"},
                    "status_explanation": {"type": "string", "description": "Explanation of the project completion status (status is: NOT STARTED)"}
                },
                "required": ["name"]
            }
        }
    }

def create_project(tc) -> dict[str, int]:
    # Get parsed arguments (required parameters are guaranteed by API)
    args = tc.function.parsed_arguments
    name = args["name"]
    public = args.get("public", True)
    description = args.get("description", "")
    status_explanation = args.get("status_explanation", "")

    # Call the actual function to create the project
    status_code = createProject(name, public, description, status_explanation)

    projectData = {
        "name": name,
        "public": public,
        "description": description,
        "status_explanation": status_explanation,
        "status_code": status_code
    }
    
    return {
        "tool_call_id": tc.id,
        "output": json.dumps(projectData)
    }


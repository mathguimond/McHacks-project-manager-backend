import requests
import json

from config import OPENPROJECT_API_KEY


# Setup a session
session = requests.Session()
session.auth = ("apikey", OPENPROJECT_API_KEY)

baseUrl = "https://openproject.chiem.me"

PRIORITIES = {
    "low": 7,
    "medium": 8,
    "high": 9,
    "immediate": 10
}

def getProjectId(name: str) -> int:
    url = f"{baseUrl}/api/v3/projects"
    
    filters = [
        {
            "name_and_identifier": {
                "operator": "~",
                "values": [name]
            }
        }
    ]

    headers = {
        "Content-Type": "application/json"
    }

    response = session.get(url, params={"filters": json.dumps(filters)}, headers=headers)
    if response.status_code != 200:
        print("Error getting project ID:", response.status_code, response.text)

    return response.json()["_embedded"]["elements"][0]["id"]

def createProject(name: str, public: bool = True, description: str = "", statusExplanation: str = "") -> int:
    url = f"{baseUrl}/api/v3/projects"
    
    payload = {
        "_type": "Project",
        "name": name,
        "identifier": name.lower().replace(" ", "-"),
        "active": True,
        "public": public,
        "description": {
            "format": "markdown",
            "raw": description
        },
        "statusExplanation": {
            "format": "markdown",
            "raw": statusExplanation
        },
        "_links": {
            "status": {
                "href": "/api/v3/project_statuses/not_started"
            }
        }
    }

    headers = {
        "Content-Type": "application/json"
    }

    response = session.post(url, json=payload, headers=headers)
    if response.status_code != 201:
        print("Error creating project:", response.status_code, response.text)
    
    return response.status_code

def updateProject(name: str, newName: str = None, newPublic: bool = None, newDescription: str = None, newStatusExplanation: str = None) -> int:
    url = f"{baseUrl}/api/v3/projects/{getProjectId(name)}"
    
    payload = {
        "_type": "Project",
    }
    
    if newName is not None:
        payload["name"] = newName
        payload["identifier"] = newName.lower().replace(" ", "-")
    if newPublic is not None:
        payload["public"] = newPublic
    if newDescription is not None:
        payload["description"] = {
            "format": "markdown",
            "raw": newDescription
        }
    if newStatusExplanation is not None:
        payload["statusExplanation"] = {
            "format": "markdown",
            "raw": newStatusExplanation
        }

    headers = {
        "Content-Type": "application/json"
    }

    response = session.patch(url, json=payload, headers=headers)
    if response.status_code != 200:
        print("Error updating project:", response.status_code, response.text)
    
    return response.status_code

def getTaskId(projectName: str, subject: str) -> (int, int):
    url = f"{baseUrl}/api/v3/projects/{getProjectId(projectName)}/work_packages"
    
    filters = [
        {
            "subject": {
                "operator": "~",
                "values": [subject]
            }
        }
    ]

    headers = {
        "Content-Type": "application/json"
    }

    response = session.get(url, params={"filters": json.dumps(filters)}, headers=headers)
    if response.status_code != 200:
        print("Error getting task ID:", response.status_code, response.text)

    return (response.json()["_embedded"]["elements"][0]["id"], response.json()["_embedded"]["elements"][0]["lockVersion"])

def createTask(projectName: str, subject: str, startDate: str, dueDate: str, description: str = "", priority: str = "medium") -> int:
    url = f"{baseUrl}/api/v3/projects/{getProjectId(projectName)}/work_packages"

    payload = {
        "subject": subject,
        "description": {
            "format": "markdown",
            "raw": description
        },
        "startDate": startDate,
        "dueDate": dueDate,
        "percentageDone": 0,
        "_links": {
            "priority": { "href": f"/api/v3/priorities/{PRIORITIES[priority]}" }
        }
    }

    headers = {
        "Content-Type": "application/json"
    }

    response = session.post(url, json=payload, headers=headers)
    if response.status_code != 201:
        print("Error creating task:", response.status_code, response.text)
    
    return response.status_code

def updateTask(projectName: str, subject: str, newSubject: str = None, newDescription: str = None, newStartDate: str = None, newDueDate: str = None, newPriority: str = None) -> int:
    url = f"{baseUrl}/api/v3/work_packages/{getTaskId(projectName, subject)[0]}"
    
    payload = {
        "lockVersion": getTaskId(projectName, subject)[1]
    }
    
    if newSubject is not None:
        payload["subject"] = newSubject
    if newDescription is not None:
        payload["description"] = {
            "format": "markdown",
            "raw": newDescription
        }
    if newStartDate is not None:
        payload["startDate"] = newStartDate
    if newDueDate is not None:
        payload["dueDate"] = newDueDate
    if newPriority is not None:
        payload["_links"] = {
            "priority": { "href": f"/api/v3/priorities/{PRIORITIES[newPriority]}" }
        }

    headers = {
        "Content-Type": "application/json"
    }

    response = session.patch(url, json=payload, headers=headers)
    if response.status_code != 200:
        print("Error updating project:", response.status_code, response.text)
    
    return response.status_code


if __name__ == "__main__":
    #print(createProject("Great project", True))
    #print(updateProject("Super duper project", newName="Wow great name", newDescription="This is an updated description."))
    #print(createTask("Wow great name", "New task", "Set up user authentication using OAuth2.", "2024-07-01", "2024-07-07", "high"))
    #print(getTaskId("Wow great name", "Another task"))
    #print(updateTask("Wow great name", "Another task", newSubject="New Task Name"))
    pass

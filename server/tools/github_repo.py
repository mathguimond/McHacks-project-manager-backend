from config import GITHUB_TOKEN
import json
import base64
import requests



GITHUB_API_BASE = "https://api.github.com"


def _headers():
    h = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "backboard-openproject-assistant",
    }
    print("GitHub token loaded:", bool(GITHUB_TOKEN))

    if GITHUB_TOKEN:
        h["Authorization"] = f"token {GITHUB_TOKEN}"
    return h


github_search_code_tool = {
    "type": "function",
    "function": {
        "name": "github_search_code",
        "description": "Search for code files in a GitHub repository matching a query. Returns matching file paths and URLs.",
        "parameters": {
            "type": "object",
            "properties": {
                "repo": {
                    "type": "string",
                    "description": "GitHub repo in the form owner/repo (e.g., octocat/Hello-World)."
                },
                "query": {
                    "type": "string",
                    "description": "Search query, e.g., 'auth middleware' or 'routes openproject'."
                },
                "limit": {
                    "type": "integer",
                    "description": "Max number of results to return (default 5)."
                }
            },
            "required": ["repo", "query"]
        }
    }
}


github_get_file_tool = {
    "type": "function",
    "function": {
        "name": "github_get_file",
        "description": "Fetch a file's content from a GitHub repository (truncated).",
        "parameters": {
            "type": "object",
            "properties": {
                "repo": {
                    "type": "string",
                    "description": "GitHub repo in the form owner/repo (e.g., octocat/Hello-World)."
                },
                "path": {
                    "type": "string",
                    "description": "File path within the repo (e.g., src/app.py)."
                },
                "ref": {
                    "type": "string",
                    "description": "Branch, tag, or commit SHA. Default 'main'."
                },
                "max_chars": {
                    "type": "integer",
                    "description": "Maximum characters to return (default 12000)."
                }
            },
            "required": ["repo", "path"]
        }
    }
}


def github_search_code(tc) -> dict[str, int]:
    args = tc.function.parsed_arguments
    repo = args["repo"]
    query = args["query"]
    limit = int(args.get("limit", 5))

    # GitHub code search query
    q = f"{query} repo:{repo}"
    print(q)

    url = f"{GITHUB_API_BASE}/search/code"
    r = requests.get(url, headers=_headers(), params={"q": q, "per_page": limit}, timeout=20)

    if r.status_code != 200:
        data = {
            "error": "GitHub search failed",
            "status_code": r.status_code,
            "details": r.text,
            "repo": repo,
            "query": query
        }
        return {
            "tool_call_id": tc.id,
            "output": json.dumps(data)
        }

    payload = r.json()
    items = payload.get("items", [])[:limit]

    results = []
    for it in items:
        results.append({
            "path": it.get("path"),
            "name": it.get("name"),
            "html_url": it.get("html_url"),
            "repository": it.get("repository", {}).get("full_name"),
        })

    data = {
        "repo": repo,
        "query": query,
        "count": len(results),
        "results": results
    }

    return {
        "tool_call_id": tc.id,
        "output": json.dumps(data)
    }


def github_get_file(tc) -> dict[str, int]:
    args = tc.function.parsed_arguments
    repo = args["repo"]
    path = args["path"]
    ref = args.get("ref", "main")
    max_chars = int(args.get("max_chars", 12000))

    url = f"{GITHUB_API_BASE}/repos/{repo}/contents/{path}"
    r = requests.get(url, headers=_headers(), params={"ref": ref}, timeout=20)

    if r.status_code != 200:
        data = {
            "error": "GitHub get file failed",
            "status_code": r.status_code,
            "details": r.text,
            "repo": repo,
            "path": path,
            "ref": ref
        }
        return {
            "tool_call_id": tc.id,
            "output": json.dumps(data)
        }

    payload = r.json()
    print(payload)

    content_b64 = payload.get("content", "")
    encoding = payload.get("encoding", "")

    if encoding != "base64" or not content_b64:
        data = {
            "repo": repo,
            "path": path,
            "ref": ref,
            "note": "File content not directly available (maybe too large or not a normal file).",
            "download_url": payload.get("download_url"),
            "html_url": payload.get("html_url"),
        }
        return {
            "tool_call_id": tc.id,
            "output": json.dumps(data)
        }

    raw = base64.b64decode(content_b64).decode("utf-8", errors="replace")
    truncated = raw[:max_chars]

    data = {
        "repo": repo,
        "path": path,
        "ref": ref,
        "returned_chars": len(truncated),
        "content": truncated,
        "html_url": payload.get("html_url")
    }

    return {
        "tool_call_id": tc.id,
        "output": json.dumps(data)
    }

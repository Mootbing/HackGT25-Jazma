from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, BackgroundTasks
from git_utils import *
from repo_utils import *
from pathlib import Path
from llm_util import generate_store_payload
import subprocess, json


app = FastAPI()
watchers = {}

@app.post("/process")
async def process_data(payload, path):
    curr_branch = get_current_branch(path)
    pre_commit_hash = commit_pre_fix_state(path, curr_branch)
    tmp_branch = create_temp_branch(path, pre_commit_hash)

    files_to_watch = payload.get("files", [])

    watchers[path] = {
        "files": files_to_watch,
        "pre_hashes": {f: file_hash(Path(path) / f) for f in files_to_watch},
        "tmp_branch": tmp_branch,
        "pre_commit_hash": pre_commit_hash,
        "curr_branch": curr_branch,
        "payload": payload,
        "changed": False
    }

    return {"message": "Snapshot taken, temp branch created, watching for changes in background."}

@app.get("/watch_status")
async def watch_status(path: str):
    info = watchers.get(path)
    if not info:
        return {"error": "No watcher for this path"}
    
    changed = False
    for f in info["files"]:
        current_hash = file_hash(Path(path) / f)
        if current_hash != info["pre_hashes"][f]:
            changed = True
            break

    info["changed"] = changed
    return {"changed": changed}

@app.post("/apply_changes")
async def apply_changes(path: str, accepted: bool):
    info = watchers.get(path)
    if not info:
        return {"error": "No watcher for this path"}

    payload = info["payload"]
    curr_branch = info["curr_branch"]
    pre_commit_hash = info["pre_commit_hash"]
    tmp_branch = info["tmp_branch"]
    files_to_watch = info["files"]

    new_commit_hash = commit_applied_fix(path, tmp_branch)

    if accepted:
        diff_text = git_diff(path, pre_commit_hash, new_commit_hash, files_to_watch)
        output = generate_store_payload(
            "bug",
            payload.get("stack_trace", ""),
            diff_text,
            payload.get("repo", ""),
            curr_branch,
            payload.get("language", "")
        )
        merge_temp_branch(path, tmp_branch, curr_branch)

        subprocess.run(
            ["node", "store_runner.js", json.dumps(output)],
            capture_output=True,
            text=True
        )

        return {"message": "Changes accepted, merged and stored."}
    else:
        rollback_to_commit(path, curr_branch, pre_commit_hash)
        return {"message": "Changes rejected, rolled back to pre-fix state."}




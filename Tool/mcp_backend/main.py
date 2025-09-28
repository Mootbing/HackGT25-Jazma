from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Body
from git_utils import *
from repo_utils import *
from pathlib import Path
from llm_util import generate_store_payload
import subprocess, json
from pydantic import BaseModel
import os


app = FastAPI()
watchers = {}

class ApplyChangesPayload(BaseModel):
    accepted: bool

@app.post("/process")
async def process_data(payload: dict = Body(...)):
    path = str(Path.home()) + "/Desktop" + "/Projects" + "/testProject"

    curr_branch = get_current_branch(path)
    pre_commit_hash = commit_pre_fix_state(path, curr_branch)
    tmp_branch = create_temp_branch(path, pre_commit_hash)

    files_to_watch = get_all_repo_files(path)

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

first_iter = True

@app.get("/watch_status")
async def watch_status():
    global first_iter
    path = str(Path.home()) + "/Desktop" + "/Projects" + "/testProject"
    info = watchers.get(path)
    if not info:
        return {"error": "No watcher for this path"}
    
    if info:
        if first_iter:
            first_iter = False
            return {"message":"Snapshot taken, temp branch created, watching for file changes"}
    
    changed = False
    for f in info["files"]:
        current_hash = file_hash(Path(path) / f)
        if current_hash != info["pre_hashes"][f]:
            changed = True
            break

    info["changed"] = changed
    return {"changed": changed}

@app.post("/apply_changes")
async def apply_changes(payload: ApplyChangesPayload):
    accepted = payload.accepted

    global first_iter
    path = str(Path.home()) + "/Desktop" + "/Projects" + "/testProject"
    info = watchers.get(path)
    if not info:
        return {"error": "No watcher for this path"}
    
    payload = info["payload"]
    if isinstance(payload, str):
        payload = json.loads(payload)
    curr_branch = info["curr_branch"]
    pre_commit_hash = info["pre_commit_hash"]
    tmp_branch = info["tmp_branch"]
    files_to_watch = info["files"]

    new_commit_hash = commit_applied_fix(path, tmp_branch)

    if accepted:
        diff_text = git_diff(path, pre_commit_hash, new_commit_hash, files_to_watch)
        output = generate_store_payload(
            "bug",
            diff_text,
            path.split("/")[-1],
            curr_branch
        )
        merge_temp_branch(path, tmp_branch, curr_branch)
        

        result = subprocess.run(
            ["node", "../src/util/store_runner.ts", json.dumps(output)],
            capture_output=True,
            text=True
        )

        first_iter = True

        return {"message": "Changes accepted, merged and stored."}
    else:
        rollback_to_commit(path, curr_branch, tmp_branch, pre_commit_hash)

        first_iter = True

        return {"message": "Changes rejected, rolled back to pre-fix state."}




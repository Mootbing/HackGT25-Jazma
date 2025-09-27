from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, BackgroundTasks
from git_utils import *
from repo_utils import *
from pathlib import Path
from llm_util import generate_store_payload


app = FastAPI()

def run_validation_pipeline(payload, path, curr_branch, pre_commit_hash, tmp_branch, files_to_watch):
    pre_hashes = {f: file_hash(Path(path) / f) for f in files_to_watch}

    for f in files_to_watch:
        try:
            wait_for_file_change(Path(path) / f, pre_hashes[f], timeout=300)
        except TimeoutError:
            print(f"[Watcher] File {f} did not change within timeout.")
            return

    new_commit_hash = commit_applied_fix(path, tmp_branch)

    response = input("Did the proposed fix properly fix your bug? (y/n) ")

    diff_text = git_diff(path, pre_commit_hash, new_commit_hash, files_to_watch)

    if response.lower() == 'y':
        output = generate_store_payload(
            "bug",
            payload.get("stack_trace", ""),
            diff_text,
            payload.get("repo", ""),
            curr_branch,
            payload.get("language", "")
        )
        merge_temp_branch(path, tmp_branch, curr_branch)
        print("[Watcher] Fix accepted, merged to branch, stored payload:")
        print(output)
    else:
        rollback_to_commit(path, curr_branch, pre_commit_hash)
        print("[Watcher] Rolled back to pre-fix state")

@app.post("/process")
async def process_data(payload, path, background_tasks):
    curr_branch = get_current_branch(path)
    pre_commit_hash = commit_pre_fix_state(path, curr_branch)
    tmp_branch = create_temp_branch(path, pre_commit_hash)

    files_to_watch = payload.get("files", [])

    # Start background watcher
    background_tasks.add_task(
        run_validation_pipeline,
        payload,
        path,
        curr_branch,
        pre_commit_hash,
        tmp_branch,
        files_to_watch
    )

    return {"message": "Snapshot taken, temp branch created, watching for changes in background."}



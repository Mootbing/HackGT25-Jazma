from fastapi import FastAPI
from git_utils import *
from repo_utils import *
from pathlib import Path
from llm_util import generate_store_payload

app = FastAPI()

@app.post("/process")
async def process_data(payload, path):
    curr_branch = get_current_branch(path)
    pre_commit_hash = commit_pre_fix_state(path, curr_branch)
    tmp_branch = create_temp_branch(path, pre_commit_hash)

    #do changes
    files_to_watch = payload.get("files", [])
    pre_hashes = {f: file_hash(Path(path) / f) for f in files_to_watch}

    for f in files_to_watch:
        try:
            wait_for_file_change(Path(path) / f, pre_hashes[f], timeout=120)  # 2 min max
        except TimeoutError:
            return {"error": f"File {f} did not change within timeout"}
    
    new_commit_hash = commit_applied_fix(path, tmp_branch)

    response = input("Did the proposed fix properly fix your bug? (y/n)")

    diff_text = git_diff(path, pre_commit_hash, new_commit_hash, files_to_watch)

    if response.lower() == 'y':
        generate_store_payload("bug", payload.get("stack_trace", ""), diff_text, payload.get("repo", ""), curr_branch, payload.get("language", ""))
        merge_temp_branch(path, tmp_branch, curr_branch)
    else:
        rollback_to_commit(path, curr_branch, pre_commit_hash)

    return {
        "pre_commit": pre_commit_hash,
        "post_commit": new_commit_hash,
        "branch": curr_branch,
        "tmp_branch": tmp_branch
    }



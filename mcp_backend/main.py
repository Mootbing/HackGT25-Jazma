from fastapi import FastAPI
from git_utils import *

app = FastAPI()

@app.post("/process")
async def process_data(payload, path):
    curr_branch = get_current_branch(path)
    commit_hash = commit_pre_fix_state(path, curr_branch)
    tmp_branch = create_temp_branch(path, commit_hash)

    #do changes

    new_commit_hash = commit_applied_fix(path, tmp_branch)

    response = input("Did the proposed fix properly fix your bug? (y/n)")

    if response.lower() == 'y':
        merge_temp_branch(path, tmp_branch, curr_branch)
    else:
        rollback_to_commit(path, curr_branch, commit_hash)



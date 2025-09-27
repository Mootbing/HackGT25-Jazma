import subprocess
import datetime

def get_current_branch(repo_path: str) -> str:
    result = subprocess.run(
        ["git", "-C", repo_path, "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
        text=True,
        check=True
    )
    return result.stdout.strip()

def commit_pre_fix_state(repo_path, branch):
    subprocess.run(["git", "-C", repo_path, "checkout", branch], check=True)
    subprocess.run(["git", "-C", repo_path, "add", "."], check=True)
    subprocess.run(["git", "-C", repo_path, "commit", "-m", "MCP Pre-fix snapshot"], check=True)

    commit_hash = subprocess.run(["git", "-C", repo_path, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    return commit_hash

def create_temp_branch(repo_path, base_commit):
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    temp_branch = f"mcp-fix-{timestamp}"
    subprocess.run(["git", "-C", repo_path, "checkout", "-b", temp_branch, base_commit], check=True)

    return temp_branch

def commit_applied_fix(repo_path, branch):
    subprocess.run(["git", "-C", repo_path, "add", "."], check=True)
    subprocess.run(["git", "-C", repo_path, "commit", "-m", "MCP Applied fix"], check=True)

    commit_hash = subprocess.run(
        ["git", "-C", repo_path, "rev-parse", "HEAD"],
        capture_output=True, text=True, check=True
    ).stdout.strip()
    
    return commit_hash

def merge_temp_branch(repo_path, temp_branch, target_branch):
    subprocess.run(["git", "-C", repo_path, "checkout", target_branch], check=True)
    subprocess.run(["git", "-C", repo_path, "merge", "--no-ff", temp_branch], check=True)
    subprocess.run(["git", "-C", repo_path, "branch", "-d", temp_branch], check=True)

def rollback_to_commit(repo_path, target_branch, commit_hash):
    subprocess.run(["git", "-C", repo_path, "checkout", target_branch], check=True)
    subprocess.run(["git", "-C", repo_path, "reset", "--hard", commit_hash], check=True)

def git_diff(repo_path: str, from_commit: str, to_commit: str, files: list[str] = None):
    cmd = ["git", "-C", repo_path, "diff", from_commit, to_commit]
    if files:
        cmd += files
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Git diff failed: {result.stderr}")
    return result.stdout


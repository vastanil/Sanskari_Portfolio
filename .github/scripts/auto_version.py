import os
import subprocess
from datetime import datetime
import git  # GitPython

repo = git.Repo(".")

branch = repo.active_branch.name
print(f"🧠 Current branch: {branch}")

# Get latest semantic version tag
tags = sorted(repo.tags, key=lambda t: t.commit.committed_datetime)
latest_tag = next((str(t) for t in reversed(tags) if str(t).startswith("v")), "v0.0.0")
print(f"🔖 Latest tag: {latest_tag}")

# Parse version
version = latest_tag.lstrip("v").split("-")[0]  # remove timestamp if any
major, minor, patch = map(int, version.split("."))

new_tag = None

if branch == "develop":
    print("📦 Rule: develop → MINOR bump")
    minor += 1
    patch = 0
    new_tag = f"v{major}.{minor}.{patch}"

elif branch == "main":
    last_msg = repo.head.commit.message
    print(f"🔍 Merge commit message: {last_msg}")
    if "from release_" in last_msg:
        print("🚀 Rule: release_* → MAJOR bump")
        major += 1
        minor = patch = 0
        new_tag = f"v{major}.{minor}.{patch}"
    elif "from hotfix_" in last_msg:
        print("🩹 Rule: hotfix_* → PATCH bump")
        patch += 1
        new_tag = f"v{major}.{minor}.{patch}"
    else:
        print("⚠️ No rule matched. Skipping.")
        exit(0)
else:
    print(f"⚠️ No versioning rule for branch: {branch}")
    exit(0)

# Check if tag already exists
if any(str(t) == new_tag for t in repo.tags):
    print(f"⚠️ Tag {new_tag} already exists. Skipping.")
    exit(0)

print(f"🏷️ Creating new tag: {new_tag}")

# Tag and push
subprocess.run(["git", "config", "--global", "user.name", "github-actions[bot]"])
subprocess.run(["git", "config", "--global", "user.email", "github-actions[bot]@users.noreply.github.com"])
subprocess.run([
    "git", "remote", "set-url", "origin",
    f"https://x-access-token:{os.environ['GITHUB_TOKEN']}@github.com/{os.environ['GITHUB_REPOSITORY']}.git"
])
subprocess.run(["git", "tag", new_tag], check=True)
subprocess.run(["git", "push", "origin", new_tag], check=True)

print(f"✅ Tag {new_tag} created and pushed successfully!")

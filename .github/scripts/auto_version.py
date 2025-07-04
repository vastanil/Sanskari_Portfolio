import os
import subprocess
from datetime import datetime
import re
import git  # GitPython

# Constants for files
VERSION_FILE = "VERSION"
HISTORY_FILE = "VERSION_HISTORY.md"

repo = git.Repo(".")
branch = repo.active_branch.name
print(f"🧠 Current branch: {branch}")

# Get latest semantic version tag
tags = sorted(repo.tags, key=lambda t: t.commit.committed_datetime)
latest_tag = next((str(t) for t in reversed(tags) if str(t).startswith("v")), "v0.0.0")
print(f"🔖 Latest tag: {latest_tag}")

# Parse version (strip date suffix if any)
version = latest_tag.lstrip("v").split("-")[0]
major, minor, patch = map(int, version.split("."))

new_tag_base = None
source_branch = None

if branch == "develop":
    print("📦 Rule: develop → MINOR bump")
    minor += 1
    patch = 0
    new_tag_base = f"v{major}.{minor}.{patch}"
    source_branch = "develop"

elif branch == "master":
    last_msg = repo.head.commit.message
    print(f"🔍 Merge commit message: {last_msg}")

    # Extract source branch from merge message
    match = re.search(r'from\s+[\w\-]+/([\w\-]+)', last_msg)
    merged_branch = match.group(1) if match else ''
    source_branch = merged_branch
    print(f"🔍 Merged branch: {merged_branch}")

    if merged_branch.startswith("release_"):
        print("🚀 Rule: release_* → MAJOR bump")
        major += 1
        minor = patch = 0
        new_tag_base = f"v{major}.{minor}.{patch}"
    elif merged_branch.startswith("hotfix_"):
        print("🩹 Rule: hotfix_* → PATCH bump")
        patch += 1
        new_tag_base = f"v{major}.{minor}.{patch}"
    else:
        print("⚠️ No rule matched for merged branch. Skipping.")
        exit(0)
else:
    print(f"⚠️ No versioning rule for branch: {branch}")
    exit(0)

# Add date suffix to tag
date_suffix = datetime.now().strftime("%Y%m%d")
new_tag = f"{new_tag_base}-{date_suffix}"

# Check if tag already exists
if any(str(t) == new_tag for t in repo.tags):
    print(f"⚠️ Tag {new_tag} already exists. Skipping.")
    exit(0)

print(f"🏷️ Creating new tag: {new_tag}")

# Git user setup
subprocess.run(["git", "config", "--global", "user.name", "github-actions[bot]"])
subprocess.run(["git", "config", "--global", "user.email", "github-actions[bot]@users.noreply.github.com"])
subprocess.run([
    "git", "remote", "set-url", "origin",
    f"https://x-access-token:{os.environ['GITHUB_TOKEN']}@github.com/{os.environ['GITHUB_REPOSITORY']}.git"
])

# Create and push tag
subprocess.run(["git", "tag", new_tag], check=True)
subprocess.run(["git", "push", "origin", new_tag], check=True)
print(f"✅ Tag {new_tag} created and pushed successfully!")

# Write to VERSION file
with open(VERSION_FILE, "w") as vf:
    vf.write(new_tag + "\n")
print(f"📝 VERSION file updated with {new_tag}")

# Append to VERSION_HISTORY.md
history_entry = f"- {new_tag} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Source: {source_branch or branch}\n"
if not os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "w") as hf:
        hf.write("# Version History\n\n")
with open(HISTORY_FILE, "a") as hf:
    hf.write(history_entry)
print(f"🗂️ VERSION_HISTORY.md updated.")

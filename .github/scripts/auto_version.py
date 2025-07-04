import os
import subprocess
import re
from datetime import datetime
import git  # GitPython

# Constants
VERSION_FILE = "VERSION"
HISTORY_FILE = "VERSION_HISTORY.md"

# Initialize repo
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

# Handle develop branch (MINOR bump)
if branch == "develop":
    print("📦 Rule: develop → MINOR bump")
    minor += 1
    patch = 0
    new_tag_base = f"v{major}.{minor}.{patch}"
    source_branch = "develop"

# Handle master branch merges
elif branch == "master":
    merge_commit = repo.head.commit
    parents = merge_commit.parents

    if len(parents) < 2:
        print("⚠️ Not a merge commit. Skipping.")
        exit(0)

    # Parent 2 is the merged commit
    merged_commit = parents[1]

    # Try to identify the branch merged
    merged_branch = None
    for ref in repo.remotes.origin.refs:
        if ref.commit == merged_commit:
            merged_branch = ref.name.replace("origin/", "")
            break

    if not merged_branch:
        print("⚠️ Could not determine merged branch name. Skipping.")
        exit(0)

    source_branch = merged_branch
    print(f"🔍 Merged branch: {merged_branch}")

    # Decide bump level
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
        print("⚠️ No versioning rule matched for merged branch. Skipping.")
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

# Git setup
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
print(f"📝 VERSION file updated.")

# Append to VERSION_HISTORY.md
history_line = f"- {new_tag} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Source: {source_branch or branch}\n"
if not os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "w") as hf:
        hf.write("# Version History\n\n")
with open(HISTORY_FILE, "a") as hf:
    hf.write(history_entry)
print(f"🗂️ VERSION_HISTORY.md updated..")


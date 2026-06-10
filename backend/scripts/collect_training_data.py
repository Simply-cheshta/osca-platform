"""
Collect weak-labeled issue data from GitHub for difficulty classifier training.
Usage: python scripts/collect_training_data.py --token YOUR_GITHUB_TOKEN
"""
import argparse
import json
import sys
from pathlib import Path

import httpx

BEGINNER = {"good first issue", "good-first-issue", "beginner", "easy", "starter"}
HARD = {"hard", "complex", "architecture", "refactor", "breaking-change"}


def infer_difficulty(labels: list[str]) -> str:
    lower = {l.lower() for l in labels}
    if lower & BEGINNER:
        return "easy"
    if lower & HARD:
        return "hard"
    return "medium"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", required=True, help="GitHub personal access token")
    parser.add_argument("--output", default="data/issues_training.jsonl")
    args = parser.parse_args()

    headers = {"Authorization": f"Bearer {args.token}", "Accept": "application/vnd.github.v3+json"}
    repos = [
        "firstcontributions/first-contributions",
        "public-apis/public-apis",
        "tiangolo/fastapi",
        "facebook/react",
    ]

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    count = 0

    with httpx.Client(headers=headers, timeout=30.0) as client:
        with output.open("w") as f:
            for repo in repos:
                resp = client.get(
                    f"https://api.github.com/repos/{repo}/issues",
                    params={"state": "closed", "per_page": 50},
                )
                if resp.status_code != 200:
                    continue
                for issue in resp.json():
                    if "pull_request" in issue:
                        continue
                    labels = [l["name"] for l in issue.get("labels", [])]
                    row = {
                        "title": issue.get("title"),
                        "body_length": len(issue.get("body") or ""),
                        "comments": issue.get("comments", 0),
                        "labels": labels,
                        "difficulty": infer_difficulty(labels),
                        "repo": repo,
                    }
                    f.write(json.dumps(row) + "\n")
                    count += 1

    print(f"Wrote {count} samples to {output}")


if __name__ == "__main__":
    main()

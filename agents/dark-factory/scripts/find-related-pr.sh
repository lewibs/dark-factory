#!/bin/bash
# find-related-pr.sh - Fuzzy-match taskDescription against open PR titles/branch names
# Usage: find-related-pr.sh <taskDescription>
# Output: BRANCH=<branch> URL=<url> TITLE=<title>  OR  empty on no match

taskDescription="$1"

# Normalize to lowercase keywords, strip punctuation
keywords=$(echo "$taskDescription" | tr '[:upper:]' '[:lower:]' | tr -cs 'a-z0-9 ' ' ' | tr -s ' ')

# Fetch all open PRs with title, headRefName, url
prs=$(gh pr list --state open --limit 50 --json title,headRefName,url 2>/dev/null) || exit 0

# For each PR: score = count of keyword hits in (title + branchName)
# Select best match if score >= 2 keywords match
best=$(echo "$prs" | python3 -c "
import sys, json, re
data = json.load(sys.stdin)
keywords = set(\"\"\"$keywords\"\"\".split())
best = None
best_score = 0
for pr in data:
    candidate = (pr['title'] + ' ' + pr['headRefName']).lower()
    score = sum(1 for kw in keywords if kw in candidate and len(kw) > 2)
    if score >= 2 and score > best_score:
        best_score = score
        best = pr
if best:
    print(f\"BRANCH={best['headRefName']}\")
    print(f\"URL={best['url']}\")
    print(f\"TITLE={best['title']}\")
")

echo "$best"

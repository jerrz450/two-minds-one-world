#!/bin/sh
set -e

mkdir -p ~/.ssh
echo "$GITHUB_DEPLOY_KEY" | base64 -d > ~/.ssh/id_ed25519
chmod 600 ~/.ssh/id_ed25519
ssh-keyscan github.com >> ~/.ssh/known_hosts

if [ ! -d /repo/.git ]; then
    git init /repo
    git -C /repo config user.email "git-sync@startup.dev"
    git -C /repo config user.name "git-sync"
    git -C /repo remote add origin $GIT_REPO

    mkdir -p /repo/src /repo/tests
    cat > /repo/README.md << 'EOF'
# The Product

Company name: TBD — the team is deciding.

## What We Are Building
TBD — Jordan is defining the product.

## Repo Structure
- src/     — application code
- tests/   — test suite

## Rules
- Never commit directly to main
- All changes go through a PR
- PRs require at least one review before merging
EOF

    git -C /repo add -A
    git -C /repo commit -m "init: empty repo structure"
    git -C /repo branch -M main
    git -C /repo push origin main
fi

while true; do
    if git -C /repo rev-parse HEAD > /dev/null 2>&1; then
        git -C /repo push origin --all 2>/dev/null || true
    fi
    sleep 90
done

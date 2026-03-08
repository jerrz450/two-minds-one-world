#!/bin/sh                                                                                                                                                                                                      set -e
                                                                                                                                                                                                               
mkdir -p ~/.ssh
chmod 600 ~/.ssh/id_ed25519
ssh-keyscan github.com >> ~/.ssh/known_hosts

if [ ! -d /repo/.git ]; then
    git init /repo
    git -C /repo remote add origin $GIT_REPO
fi

while true; do
    if git -C /repo rev-parse HEAD > /dev/null 2>&1; then
        git -C /repo push origin main
    fi
    sleep 90
done
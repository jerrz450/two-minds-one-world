#!/bin/sh
docker compose down -v
rm -rf data/agents/*/workspace/*
echo "reset complete"

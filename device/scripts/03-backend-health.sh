#!/usr/bin/env bash
set -euo pipefail

echo "== Backend health =="
curl -fsS http://127.0.0.1:8080/health
echo

echo "== Contacts =="
curl -fsS http://127.0.0.1:8080/contacts
echo

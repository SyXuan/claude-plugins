#!/usr/bin/env bash
# Fetch Claude rate limit usage and update local cache
exec python "$(dirname "$0")/fetch-usage.py"

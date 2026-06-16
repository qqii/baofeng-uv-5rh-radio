#!/usr/bin/env bash

set -uo pipefail
trap 'status=$?; echo "$0: Error on line $LINENO: $BASH_COMMAND"; exit "$status"' ERR
IFS=$'\n\t' # nosemgrep: bash.lang.security.ifs-tampering.ifs-tampering

# Validate the commit message follows Conventional Commits.
# https://www.conventionalcommits.org/

read -r line < "$1" || true
[[ $line =~ ^(feat|fix|refactor|perf|style|test|docs|build|ops|chore)(\(.+\))?!?:\ .+ ]] \
  || [[ $line =~ ^(fixup|squash|amend|wip)\! ]]

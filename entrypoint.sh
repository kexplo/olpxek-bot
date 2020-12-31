#!/usr/bin/env bash

set -euo pipefail

if [ "${BOT_TOKEN:-x}" == "x" ]; then
  echo 'Error: $BOT_TOKEN environemnt variable is unset or null' 1>&2
  exit 1
fi

poetry run olpxek_bot "$BOT_TOKEN"

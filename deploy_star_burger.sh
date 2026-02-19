#!/bin/bash

set -e
cd /opt/star-burger-new/

printf "\nPulling changes\n"
git pull

printf "\nReloading services\n"
docker compose up -d

printf "\nTracking deploy in rollbar\n"
REVISION=$(git rev-parse --short HEAD)
curl -H "X-Rollbar-Access-Token: 35fb6a14d0d64b399b39a98e99da4c09" -H "Content-Type: application/json" -X POST 'https://api.rollbar.com/api/1/deploy' -d "{\"environment\":\"production\",\"revision\":\"$REVISION\",\"local_username\":\"deploy\"}"

printf "\nDeploy completed\n"
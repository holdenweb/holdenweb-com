#!/bin/bash
# Runs exactly once: the image's entrypoint only executes this directory while
# the data directory is still empty, which -- because the data directory lives
# on the host -- means "the first time you bring this lab up on this machine".
#
# Its job is to create the least-privileged user the application connects with,
# so the root credentials never leave .env and the bootstrap.
set -euo pipefail

echo "creating application user '${MONGO_APP_USER}' in database '${MONGO_DB}'"

mongosh --quiet \
    --host 127.0.0.1 \
    --username "${MONGO_INITDB_ROOT_USERNAME}" \
    --password "${MONGO_INITDB_ROOT_PASSWORD}" \
    --authenticationDatabase admin \
    "${MONGO_DB}" \
    --eval "db.createUser({
        user: '${MONGO_APP_USER}',
        pwd: '${MONGO_APP_PASSWORD}',
        roles: [{role: 'readWrite', db: '${MONGO_DB}'}]
    })"

# Create the collection up front so index definitions have somewhere to live.
mongosh --quiet \
    --host 127.0.0.1 \
    --username "${MONGO_INITDB_ROOT_USERNAME}" \
    --password "${MONGO_INITDB_ROOT_PASSWORD}" \
    --authenticationDatabase admin \
    "${MONGO_DB}" \
    --eval "db.notes.createIndex({created: -1})"

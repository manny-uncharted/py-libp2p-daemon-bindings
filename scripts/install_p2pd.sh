#!/bin/bash

set -euo pipefail

# LIBP2P_DAEMON_VERSION=v0.2.0 # has a lot of issues
LIBP2P_DAEMON_VERSION=v0.9.1
PROJECT_NAME=go-libp2p-daemon
LIBP2P_DAEMON_REPO=github.com/libp2p/$PROJECT_NAME

go version
go env
git clone https://$LIBP2P_DAEMON_REPO
cd $PROJECT_NAME
git checkout $LIBP2P_DAEMON_VERSION

# Patch go.mod for Go 1.12 compatibility
# Handle different sed syntax for macOS and Linux
if [[ "$OSTYPE" == "darwin"* ]]; then
    sed -i '' 's/go 1.22/go 1.12/' go.mod
    sed -i '' '/toolchain/d' go.mod
else
    sed -i 's/go 1.22/go 1.12/' go.mod
    sed -i '/toolchain/d' go.mod
fi

go get ./...
go install ./...
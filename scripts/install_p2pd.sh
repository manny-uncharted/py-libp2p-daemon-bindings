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

# Set GO111MODULE and use specific Go proxy settings for better compatibility
export GO111MODULE=on
export GOPROXY=https://proxy.golang.org,direct
export GOSUMDB=sum.golang.org

# Try to build with less strict dependency resolution
go mod download || echo "Some dependencies failed to download, continuing..."
go build -o p2pd-bin ./p2pd/
go build -o p2p-keygen-bin ./p2p-keygen/

# Install to GOPATH/bin
GOPATH=${GOPATH:-$(go env GOPATH)}
mkdir -p "$GOPATH/bin"
cp p2pd-bin "$GOPATH/bin/p2pd"
cp p2p-keygen-bin "$GOPATH/bin/p2p-keygen"

echo "Successfully installed p2pd and p2p-keygen"
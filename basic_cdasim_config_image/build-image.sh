#!/bin/bash

#  Copyright (C) 2018-2024 LEIDOS.
#
#  Licensed under the Apache License, Version 2.0 (the "License"); you may not
#  use this file except in compliance with the License. You may obtain a copy of
#  the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations under
#  the License.

#
# Build the basic CDASim configuration image.

USERNAME=usdotfhwastol
IMAGE=cdasim-config
cd "$(dirname "$0")" || exit 1
DIR_NAME=${PWD##*/}
CONFIG_NAME=$(echo "$DIR_NAME" | sed 's/_/-/g')

while [[ $# -gt 0 ]]; do
    arg="$1"
    case $arg in
        -d|--develop)
            USERNAME=usdotfhwastoldev
            TAG=develop
            shift
            ;;
    esac
done

echo ""
echo "##### CARMA $CONFIG_NAME Configuration Docker Image Build Script #####"
echo ""


if [[ -z "$TAG" ]]; then
    TAG="$("../docker/get-system-version.sh")-$CONFIG_NAME"
else
    TAG="$TAG-$CONFIG_NAME"
fi

echo "Building docker image for CDASim Configuration version: $TAG"
echo "Final image name: $USERNAME/$IMAGE:$TAG"

docker build --no-cache -t "$USERNAME/$IMAGE:$TAG" \
    --build-arg VERSION="$TAG" \
    --build-arg VCS_REF="$(git rev-parse --short HEAD)" \
    --build-arg CONFIG_NAME="cdasim-config:$CONFIG_NAME" \
    --build-arg BUILD_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" .

echo ""
echo "##### CARMA $CONFIG_NAME Docker Image Build Done! #####"

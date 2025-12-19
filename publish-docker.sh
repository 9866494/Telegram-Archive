#!/bin/bash

# Telegram Archive Docker Hub Publication Script
# This script builds and publishes Docker images to Docker Hub

set -e

# Configuration
DOCKERHUB_USERNAME="awful"
IMAGE_NAME="telegram-archive"
VERSION=${1:-latest}

echo "🚀 Publishing Telegram Archive Docker images to Docker Hub"
echo "Username: $DOCKERHUB_USERNAME"
echo "Image: $IMAGE_NAME"
echo "Version: $VERSION"
echo

# Function to build and publish an image
build_and_publish() {
    local service_name=$1
    local dockerfile=$2
    local tag="${DOCKERHUB_USERNAME}/${IMAGE_NAME}-${service_name}:${VERSION}"

    echo "📦 Building $service_name image..."
    docker build -f "$dockerfile" -t "$tag" .

    echo "📤 Publishing $tag to Docker Hub..."
    docker push "$tag"

    echo "✅ Successfully published $tag"
    echo
}

# Check if user is logged in to Docker Hub
echo "🔐 Checking Docker Hub authentication..."
if ! docker info | grep -q "Username.*$DOCKERHUB_USERNAME"; then
    echo "❌ Please login to Docker Hub first:"
    echo "   docker login"
    exit 1
fi

# Build and publish backup service
build_and_publish "backup" "Dockerfile.backup"

# Build and publish viewer service
build_and_publish "viewer" "Dockerfile.viewer"

echo "🎉 All images published successfully!"
echo
echo "📋 Published images:"
echo "   $DOCKERHUB_USERNAME/$IMAGE_NAME-backup:$VERSION"
echo "   $DOCKERHUB_USERNAME/$IMAGE_NAME-viewer:$VERSION"
echo
echo "💡 To use these images, update your docker-compose.yml:"
echo "   telegram-backup:"
echo "     image: $DOCKERHUB_USERNAME/$IMAGE_NAME-backup:$VERSION"
echo "     build: .  # Remove this line"
echo
echo "   telegram-viewer:"
echo "     image: $DOCKERHUB_USERNAME/$IMAGE_NAME-viewer:$VERSION"
echo "     build: .  # Remove this line"
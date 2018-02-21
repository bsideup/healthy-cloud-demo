#!/bin/bash

export PS4='\[\e[35m\] >>> \[\e[m\]'

set -x
set -e

ENV_NAME=meetup-demo

SERVICE=$1

pushd services/$SERVICE

# CI stage :)
./gradlew build

# Docker stage
ECR_REPOSITORY_NAME=$SERVICE-service
DOCKER_IMAGE=145231954520.dkr.ecr.$(aws configure get region).amazonaws.com/$ECR_REPOSITORY_NAME:$(date +%s)

docker build -t $DOCKER_IMAGE .

aws ecr create-repository --repository-name=$ECR_REPOSITORY_NAME &2>/dev/null || true

set +o xtrace
`aws ecr get-login --no-include-email` && docker push $DOCKER_IMAGE
set -o xtrace

INFRASTRUCTURE_FILE=/tmp/infrastructure-$(date +%s).yaml

# Deployment stage
python2 infrastructure.py > $INFRASTRUCTURE_FILE

aws cloudformation deploy \
    --capabilities CAPABILITY_IAM \
    --stack-name $SERVICE-service-demo \
    --template-file $INFRASTRUCTURE_FILE \
    --no-execute-changeset \
    --parameter-overrides \
    Env=$ENV_NAME \
    DockerImage=$DOCKER_IMAGE

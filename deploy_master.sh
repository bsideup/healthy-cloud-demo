#!/bin/bash

export PS4='\[\e[35m\] >>> \[\e[m\]'

set -x
set -e

ENV_NAME=meetup-demo

# Use your own values (or create it with CloudFormation :) )
CF_BUCKET=cf-templates-q9njjvo0tv1j-eu-central-1
ACM_CERTIFICATE_ARN=arn:aws:acm:eu-west-1:145231954520:certificate/398ad101-9c33-4402-9aaa-f0c822666fbc
INTERNAL_DOMAIN=vivy.services

INFRASTRUCTURE_FILE=/tmp/infrastructure-$(date +%s).yaml

aws cloudformation package \
    --template-file platform/_master.yaml \
    --s3-bucket=$CF_BUCKET \
    --output-template-file $INFRASTRUCTURE_FILE

aws cloudformation deploy \
    --template-file $INFRASTRUCTURE_FILE \
    --stack-name $ENV_NAME \
    --no-execute-changeset \
    --capabilities CAPABILITY_IAM \
    --parameter-overrides \
    CertificateArn=$ACM_CERTIFICATE_ARN \
    InternalDomain=$INTERNAL_DOMAIN

#!/usr/bin/env bash

set -o nounset
set -e

DEFAULT_REGION=eu-west-1
PROFILE=${1:-rob}

aws cloudformation package --template-file root-stack.yml  --s3-bucket arthur2016cloudformationtemplates --output-template-file sentiment-pipeline-output.yaml --profile ${PROFILE} --region ${DEFAULT_REGION} && \
aws cloudformation deploy --template-file ./sentiment-pipeline-output.yaml --stack-name sentiment-analysis-pipeline --capabilities CAPABILITY_IAM --profile ${PROFILE} --region ${DEFAULT_REGION}
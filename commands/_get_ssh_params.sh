#/bin/bash -xeu

ENV=$1

BASTION_HOST=$(aws ec2 describe-instances --filters "Name=tag:Name,Values=bastion" "Name=tag:environment,Values=$ENV" --query 'Reservations[0].Instances[0].PublicDnsName' --output=text)

CURRENT_USER=$(aws sts get-caller-identity --query='UserId' --output=text | cut -d ':' -f2)
CURRENT_USER=${CURRENT_USER/"+"/".plus."}
CURRENT_USER=${CURRENT_USER/"="/".equal."}
CURRENT_USER=${CURRENT_USER/","/".comma."}
CURRENT_USER=${CURRENT_USER/"@"/".at."}

printf "$CURRENT_USER@$BASTION_HOST"

# Healthy Cloud demo
https://speakerdeck.com/bsideup/healthy-cloud-for-a-healthtech-company-aws-berlin-meetup

# How to run the demo

## Before we start
1. Adjust `deploy_master.sh` and put your own values for `ENV_NAME`, `CF_BUCKET`, `ACM_CERTIFICATE_ARN` and `INTERNAL_DOMAIN` variables
1. Adjust `ENV_NAME` in `cicd.sh`

## Deploy the platform

1. Create a single ACM certificate for your internal domain (e.g. `mycompany.services`) and your public domain (e.g. `example.com`)
1. Execute it (Alternatively, pack a template and use your favorite CloudFormation tool to deploy it)
1. Go to AWS Console and execute the changeset after reviewing it
1. Once it is created, add `*.example.com` wildcard Route53 record pointing to your public ALB

Now you have:
- VPC with 10.0.0.0/16 CIDR and 3 AZs
- ECS Cluster with EC2 ASG draining
- Internal ALB with `*.mycompany.services` private DNS zone
- Public ALB
- SSH bastion instance with IAM-based auth.  
Check https://github.com/widdix/aws-ec2-ssh how to configure it

## Deploy your first (internal) micro-service

1. use `./cicd.sh foo` to deploy service `foo` (you can find it in `services/foo/` folder)
1. Go to AWS console and execute the changeset (`--no-execute-changeset` is set, you can remove it to immediately run the deployment)

`services/foo/infrastructure.py` describes `foo` service's infrastructure.

## Verify that it works
Since `foo` is an internal service, we can only query it from the inside of our VPC.

**Important:** this step assumes you have aws-ec2-ssh configured (see `Deploy the platform`)

Run
```shell
$ ./commands/shell.sh $ENV_NAME 'curl -sSL https://foo.mycompany.services/hello'

Hello, I am 6cae38f4-5dee-4344-8c0d-10a430dfbd98
```
Where `ENV_NAME` is your environment name (see `Before we start`)

## Deploy your public micro-service

1. Go to AWS Parameter Store UI and add an encrypted parameter "/some/secret"
1. use `./cicd.sh bar` to deploy service `bar` (you can find it in `services/bar/` folder)
1. Go to AWS console and execute the changeset
1. Test it:
```shell
$ curl -sSL https://bar.example.com/

Foo answered:
Hello, I am 6cae38f4-5dee-4344-8c0d-10a430dfbd98

$ curl -sSL https://bar.example.com/env/something
**the value of "/some/secret" secret parameter**
```

## Make changes
1. Adjust `services/foo/infrastructure.py`, add `desired_count=2` after `priority`
1. use `./cicd.sh foo` to update service `foo`
1. Go to AWS console, review and execute the changeset
1. Test it:
```shell
$ curl -sSL https://bar.example.com/

Foo answered:
Hello, I am 79586eb1-2488-4039-a16f-fbab4d06d215

$ curl -sSL https://bar.example.com/

Foo answered:
Hello, I am 91d0bf3e-5157-493f-b031-faf86ba7d6df

$ curl -sSL https://bar.example.com/

Foo answered:
Hello, I am 79586eb1-2488-4039-a16f-fbab4d06d215

$ curl -sSL https://bar.example.com/

Foo answered:
Hello, I am 91d0bf3e-5157-493f-b031-faf86ba7d6df
```

# Future steps
Use Jenkins or some other CD platform to deploy your platform & services

# Links
- https://github.com/widdix/aws-ec2-ssh
- https://github.com/remind101/ssm-env
- https://github.com/bsideup/ecs-drainer
- https://github.com/cevoaustralia/aws-google-auth

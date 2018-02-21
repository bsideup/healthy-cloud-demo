#!/usr/bin/env python2
import sys
# You probably will want to use PIP :)
sys.path.append("../..")

from infralib import ECSMicroService, SSMParameter
from troposphere import Template, Parameter
from troposphere import iam

t = Template()

t.add_parameter(Parameter('Env', Type="String"))
t.add_parameter(Parameter('DockerImage', Type="String"))

service = ECSMicroService(
    "bar",
    priority=200,
    public=True,
    imports_format='${Env}-%s',
    envs = {
        "foo_ribbon_listOfServers": "https://foo.vivy.services:443",
        "something": SSMParameter("/some/secret"),
    }
)
service.inject_to(t)

t.resources["TaskDefinition"].TaskRoleArn = t.add_resource(iam.Role(
    'ECSTaskRole',
    Path="/",
    AssumeRolePolicyDocument={
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": { "Service": [ "ecs-tasks.amazonaws.com" ] },
            "Action": [ "sts:AssumeRole" ]
        }]
    },
    Policies=[iam.PolicyProperty(
        PolicyName='inline',
        PolicyDocument={
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Action": [
                    "kms:*",
                    "ssm:*",
                ],
                # ALWAYS limit the access in your real environments, mkay?
                "Resource": "*"
            }]
        }
    )]
)).ref()

print(t.to_yaml())

#!/usr/bin/env python2
import sys
# You probably will want to use PIP :)
sys.path.append("../..")

from infralib import ECSMicroService
from troposphere import Template, Parameter

t = Template()

t.add_parameter(Parameter('Env', Type="String"))
t.add_parameter(Parameter('DockerImage', Type="String"))

service = ECSMicroService(
    "foo",
    priority=100,
    imports_format='${Env}-%s'
)
service.inject_to(t)

print(t.to_yaml())

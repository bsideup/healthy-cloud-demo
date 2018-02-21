from troposphere import Parameter, Ref, Sub, ImportValue, Region
from troposphere import ecs, logs, elasticloadbalancingv2
from SSMParameter import SSMParameter

class ECSMicroService(object):

    def __init__(
        self,
        name,
        priority, # ALB target group's priority
        imports_format, # format of your exports, like "mycorp-prod-%s"
        domains = None,
        public=False,
        memory=512,
        port=8080,
        desired_count=1,
        deployment_configuration = ecs.DeploymentConfiguration(MinimumHealthyPercent=100, MaximumPercent=200),
        healthcheck_path = "/health",
        healthcheck_interval = 10,
        container_name = None,
        envs = {},
        resource_name_format='%s', # Useful if you want to have multiple services in a single infrastructure file
        docker_image=Ref('DockerImage'),
        logs_datetime_format='%Y-%m-%d %H:%M:%S',
    ):
        self.name = name
        self.priority = priority
        self.domains = domains if domains is not None else ["%s.*" %(name)]
        self.public = public
        self.memory = memory
        self.port = port
        self.desired_count = desired_count
        self.deployment_configuration = deployment_configuration
        self.healthcheck_path = healthcheck_path
        self.healthcheck_interval = healthcheck_interval
        self.container_name = container_name if container_name is not None else name
        self.envs = envs
        self.resource_name_format = resource_name_format
        self.imports_format = imports_format
        self.docker_image = docker_image
        self.logs_datetime_format = logs_datetime_format

    def get_envs(self, t):
        result = self.envs.copy()
        result.update({
            "AWS_REGION": Region,
        })
        return result

    def target_group_attributes(self):
        return {
            "deregistration_delay.timeout_seconds": "5"
        }

    def create_task_definition(self, t):
        return t.add_resource(ecs.TaskDefinition(
            self.resource_name_format % ('TaskDefinition'),
            Family=Sub('${AWS::StackName}-app'),
            ContainerDefinitions=[ecs.ContainerDefinition(
                Name=self.container_name,
                Image=self.docker_image,
                Memory=self.memory,
                PortMappings=[ecs.PortMapping(ContainerPort=self.port)],
                Environment=[
                    ecs.Environment(Name=key, Value=value)
                    for (key, value) in sorted(self.get_envs(t).items())
                ]
            )]
        ))

    def create_service(self, t, task_definition):
        return t.add_resource(ecs.Service(
            self.resource_name_format % ('Service'),
            Cluster=ImportValue(Sub(self.imports_format % ('ECSCluster'))),
            DesiredCount=self.desired_count,
            DeploymentConfiguration=self.deployment_configuration,
            Role=Sub('arn:aws:iam::${AWS::AccountId}:role/ecsServiceRole'),
            TaskDefinition=Ref(task_definition),
            DependsOn=[]
        ))

    def inject_to(self, t):
        task_definition = self.create_task_definition(t)
        service = self.create_service(t, task_definition)

        self.configure_alb(t, service)
        self.configure_awslogs(t, task_definition.ContainerDefinitions[0])

        return t

    def configure_alb(self, t, service):
        service_target_group = t.add_resource(elasticloadbalancingv2.TargetGroup(
            self.resource_name_format % ('ServiceTargetGroup'),
            Port=80,
            Protocol="HTTP",
            HealthCheckPath=self.healthcheck_path,
            HealthCheckIntervalSeconds=self.healthcheck_interval,
            HealthCheckTimeoutSeconds=self.healthcheck_interval - 1,
            HealthyThresholdCount=2,
            UnhealthyThresholdCount=5,
            VpcId=ImportValue(Sub(self.imports_format % ('VpcId'))),
            TargetGroupAttributes=[
                elasticloadbalancingv2.TargetGroupAttribute(Key=key, Value=value)
                for (key, value) in sorted(self.target_group_attributes().items())
            ]
        ))

        listener_rule = t.add_resource(elasticloadbalancingv2.ListenerRule(
            self.resource_name_format % ('SecureListenerRule'),
            ListenerArn=ImportValue(Sub(self.imports_format % ('PublicListener' if self.public else 'InternalListener'))),
            Priority=self.priority,
            Actions=[elasticloadbalancingv2.Action(Type="forward", TargetGroupArn=Ref(service_target_group))],
            Conditions=[elasticloadbalancingv2.Condition(Field="host-header", Values=self.domains)]
        ))

        service.DependsOn.append(listener_rule.title)
        service.LoadBalancers = [
            ecs.LoadBalancer(
                ContainerName=self.container_name,
                ContainerPort=self.port,
                TargetGroupArn=Ref(service_target_group)
            )
        ]

    def configure_awslogs(self, t, container_definition):
        logs_group = t.add_resource(logs.LogGroup(self.resource_name_format % ('CloudWatchLogsGroup'), RetentionInDays=90))

        container_definition.LogConfiguration = ecs.LogConfiguration(
            LogDriver="awslogs",
            Options={
                "awslogs-group": Ref(logs_group),
                "awslogs-region": Region,
                "awslogs-datetime-format": self.logs_datetime_format
            }
        )

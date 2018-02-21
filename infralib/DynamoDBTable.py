import datetime
from troposphere import Ref, Sub
from troposphere import dynamodb, applicationautoscaling


class DynamoDBTable(object):
    def __init__(self, label, hash_key, range_key=None, min_read_capacity=5, min_write_capacity=5):
        self.label = label
        self.hash_key = hash_key
        self.range_key = range_key
        self.min_read_capacity = min_read_capacity
        self.min_write_capacity = min_write_capacity

    def table_ref(self):
        return Ref(self.label)

    def get_provisioned_throughput(self, t):
        return dynamodb.ProvisionedThroughput(ReadCapacityUnits=self.min_read_capacity, WriteCapacityUnits=self.min_write_capacity)

    def inject_to(self, t):
        attribute_definitions = [
            dynamodb.AttributeDefinition(AttributeName=self.hash_key[0], AttributeType=self.hash_key[1])
        ]

        key_schema = [
            dynamodb.KeySchema(AttributeName=self.hash_key[0], KeyType="HASH")
        ]

        if self.range_key is not None:
            attribute_definitions.append(
                dynamodb.AttributeDefinition(AttributeName=self.range_key[0], AttributeType=self.range_key[1])
            )
            key_schema.append(
                dynamodb.KeySchema(AttributeName=self.range_key[0], KeyType="RANGE")
            )

        table = t.add_resource(dynamodb.Table(
            self.label,
            AttributeDefinitions = attribute_definitions,
            KeySchema = key_schema,
            ProvisionedThroughput=self.get_provisioned_throughput(t)
        ))

        self.configure_autoscaling(t, table)

        return t

    def configure_autoscaling(self, t, table):
        dimensions = [
            ("Read", self.min_read_capacity),
            ("Write", self.min_write_capacity)
        ]

        for (capacity_type, min_capacity) in dimensions:
            scalable_target = t.add_resource(applicationautoscaling.ScalableTarget(
                '%s%sCapacityScalableTarget' % (capacity_type, self.label),
                MinCapacity=min_capacity,
                MaxCapacity=1000,
                ResourceId=Sub("table/${%s}" % (table.title)),
                RoleARN=Sub("arn:aws:iam::${AWS::AccountId}:role/service-role/DynamoDBAutoscaleRole"),
                ScalableDimension="dynamodb:table:%sCapacityUnits" % (capacity_type),
                ServiceNamespace="dynamodb"
            ))

            t.add_resource(applicationautoscaling.ScalingPolicy(
                '%s%sScalingPolicy' % (capacity_type, self.label),
                PolicyName='%sAutoScalingPolicy' % (capacity_type),
                PolicyType='TargetTrackingScaling',
                ScalingTargetId=scalable_target.ref(),
                TargetTrackingScalingPolicyConfiguration=applicationautoscaling.TargetTrackingScalingPolicyConfiguration(
                    TargetValue=70.0,
                    ScaleInCooldown=int(datetime.timedelta(hours=10).total_seconds()),
                    ScaleOutCooldown=60,
                    PredefinedMetricSpecification=applicationautoscaling.PredefinedMetricSpecification(
                        PredefinedMetricType='DynamoDB%sCapacityUtilization' % (capacity_type)
                    )
                )
            ))

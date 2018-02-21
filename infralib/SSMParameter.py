from troposphere import Sub

def SSMParameter(path):
    return Sub('ssm://%s' % (path))

from aws_cdk import (
    core,
    aws_iam,
    aws_s3 as s3,
    aws_s3_notifications,
    aws_sns as sns,
    aws_lambda,
    aws_dynamodb as ddb,
    aws_sns_subscriptions as subscriptions,
    aws_lambda_event_sources
    )


class ScanVideoS3RekognitionStack(core.Stack):

    def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        REGION_NAME = 'us-east-1'
        email="elizabethfuentes12@gmail.com"

        #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        #++++++++++Creamos el data bucket +++++++++++++++++++++++++++++++
        #El cual sera el encargado de almacenar los videos a escanear.+++
        #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

        bucket1 = s3.Bucket(self,"data-bucket" ,  versioned=False, removal_policy=core.RemovalPolicy.DESTROY)

        #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        #++++++++++     Creamos el work bucket +++++++++++++++++++++++++++
        #++El cual sera el encargado de almacenar report y logs.++++++++++
        #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

        #bucket2 = s3.Bucket(self,"work-bucket" ,  versioned=False, removal_policy=core.RemovalPolicy.DESTROY)

        #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        #+++++++++++++++++++++++++++++++++++ Crear el topic SNS +++++++++++++++++++++++++++++++++++++++++++++++++
        #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        #https://docs.aws.amazon.com/cdk/api/latest/python/aws_cdk.aws_sns/Topic.html
        #https://pypi.org/project/aws-cdk.aws-sns-subscriptions/

        my_topic_email = sns.Topic(self, "my_topic_email",
                        display_name="Customer subscription topic")
        my_topic_email.add_subscription(subscriptions.EmailSubscription(email))
        SNS_ARN_email = my_topic_email.topic_arn


        my_topic_rekognition = sns.Topic(self, "my_topic_rekognition",
                        display_name="Rekognition subscription topic")
        SNS_ARN_rekognition=my_topic_rekognition.topic_arn

        #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        #+++++++++++++++++++++++++++++++++++ Role Rekognition para poder publicar en SNS ++++++++++++++++++++++++
        #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

        rekognitionServiceRole = aws_iam.Role( self, "RekognitionServiceRole", assumed_by=aws_iam.ServicePrincipal('rekognition.amazonaws.com'))
        rekognitionServiceRole.add_to_policy(
            aws_iam.PolicyStatement(
                actions=["sns:Publish"], 
                resources=[my_topic_rekognition.topic_arn])
                )

        SNS_ROLE_ARN_REKO = rekognitionServiceRole.role_arn

        #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        #+++++++++++++++++++++++++++++++++++ Creamos la tabla DynamoDB ++++++++++++++++++++++++++++++++++++++++++
        #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        table_name="rekognition-demo-table"

        ddb_table = ddb.Table(
            self, table_name,
            partition_key=ddb.Attribute(name="Id", type=ddb.AttributeType.STRING),
            sort_key=ddb.Attribute(name="Timestamp", type=ddb.AttributeType.NUMBER),
            removal_policy=core.RemovalPolicy.DESTROY)


        #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        #++++++++++The Lambda function invokes Amazon Rekognition for content moderation on videos ++++++++++++++++
        #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

        lambda_invokes_Rekognition= aws_lambda.Function(self, "lambda_invokes_Rekognition",
                                    handler = "lambda_function.lambda_handler",
                                    timeout = core.Duration.seconds(300),
                                    runtime = aws_lambda.Runtime.PYTHON_3_8,
                                    memory_size = 256, description = "Lambda que invoca Amazon Rekognition ",
                                    code = aws_lambda.Code.asset("./lambda_invokes_rekognition"),
                                    environment = {
                                        'ENV_REGION_NAME': REGION_NAME,
                                        'ENV_TABLE_NAME':ddb_table.table_name, 
                                        'ENV_SNS_ARN': SNS_ARN_email,
                                        'ENV_SNS_REKOGNITION': SNS_ARN_rekognition,
                                        "ENV_SNS_ROLE_ARN_REK":SNS_ROLE_ARN_REKO}
                                    )

        lambda_invokes_Rekognition.add_to_role_policy(
            aws_iam.PolicyStatement(
                actions=["rekognition:*"], 
                resources=['*'])
              )
        
        lambda_invokes_Rekognition.add_to_role_policy(
            aws_iam.PolicyStatement(
                actions=["sns:*"], 
                resources=['*']))

        lambda_invokes_Rekognition.add_to_role_policy(
            aws_iam.PolicyStatement(
                actions =['iam:PassRole'],
                resources =[rekognitionServiceRole.role_arn]  
            )
        )

        #Permiso para leer y escribir en S3 y se agrega el evento que la activara 
        bucket1.grant_read(lambda_invokes_Rekognition) 
        notification = aws_s3_notifications.LambdaDestination(lambda_invokes_Rekognition)
        bucket1.add_event_notification(s3.EventType.OBJECT_CREATED, notification) 

        #Permiso para enviar email con SNS
        my_topic_email.grant_publish(lambda_invokes_Rekognition)


        #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        #++++++++++The Lambda function invokes Amazon Rekognition for content moderation on videos ++++++++++++++++
        #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

        lambda_process_Rekognition= aws_lambda.Function(self, "lambda_process_Rekognition",
                                    handler = "lambda_function.lambda_handler",
                                    timeout = core.Duration.seconds(300),
                                    runtime = aws_lambda.Runtime.PYTHON_3_8,
                                    memory_size = 256, description = "Lambda que procesa Amazon Rekognition ",
                                    code = aws_lambda.Code.asset("./lambda_process_Rekognition"),
                                    environment = {
                                        'ENV_REGION_NAME': REGION_NAME,
                                        'ENV_TABLE_NAME':ddb_table.table_name, 
                                        'ENV_SNS_ARN': SNS_ARN_email}
                                    )
        

        lambda_process_Rekognition.add_to_role_policy(
            aws_iam.PolicyStatement(
                actions=["rekognition:*"], 
                resources=['*']))

        lambda_process_Rekognition.add_to_role_policy(
            aws_iam.PolicyStatement(
                actions=["sns:*"], 
                resources=['*']))
        
        #Permiso para escribir en la tabla
        ddb_table.grant_write_data(lambda_process_Rekognition)   
        lambda_process_Rekognition.add_environment("TABLE_NAME", ddb_table.table_name)
        my_topic_rekognition.add_subscription(subscriptions.LambdaSubscription(lambda_process_Rekognition))



    
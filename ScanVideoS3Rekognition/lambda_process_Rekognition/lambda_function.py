import boto3
import time
import uuid
import datetime
import os
import time
import json


def procesa_sns (record):

    body = record["Sns"]
    print ("body: {}".format(body))

    message = json.loads(body['Message'])
    print ("Message: {}".format(message))

    request = {}

    request["jobId"] = message['JobId']
    request["Timestamp"] = message['Timestamp']
    request["jobStatus"] = message['Status']
    request["jobAPI"] = message['API']
    request["bucketName"] = message['Video']['S3Bucket']
    request["objectName"] = message['Video']['S3ObjectName']

    print ("Message de SNS: {}".format(request))

    return request

def lambda_handler(event, context):
    print (event)

    region_name = os.environ.get('ENV_REGION_NAME')
    table_name = os.environ.get('ENV_TABLE_NAME')
    SNS_ARN = os.environ.get('ENV_SNS_ARN')

    rekognition = boto3.client('rekognition')
    client = boto3.client('sns')

    dynamodb = boto3.resource('dynamodb', region_name=region_name)
    table = dynamodb.Table(table_name)

    for record in event['Records']:

        request= procesa_sns (record) 
        moderationJobId = request["jobId"]
        filename = request["objectName"]

        print ("moderationJobId: {}".format(moderationJobId))
        print ("filename: {}".format(filename))

        #get content moderation
        #https://docs.aws.amazon.com/cli/latest/reference/rekognition/get-content-moderation.html

        getContentModeration = rekognition.get_content_moderation(
            JobId=moderationJobId,
            SortBy='TIMESTAMP')

        while (getContentModeration['JobStatus'] == 'IN_PROGRESS'):
            time.sleep(5)
            print('.', end='')

            getContentModeration = rekognition.get_content_moderation(
                JobId=moderationJobId,
                SortBy='TIMESTAMP')

        print(getContentModeration['JobStatus'])
        print(getContentModeration)

        theObjects = {}

        strDetail = "Moderation labels in video\n"
        strOverall = "Moderation labels in the overall video:\n"

        # Potentially unsafe content detected in each frame
        for obj in getContentModeration['ModerationLabels']:
            ts = obj["Timestamp"]
            cconfidence = obj['ModerationLabel']["Confidence"]
            oname = obj['ModerationLabel']["Name"]
            strDetail = strDetail + "At {} ms: {} (Confidence: {})\n".format(ts, oname, round(cconfidence, 2))
            if oname in theObjects:
                cojb = theObjects[oname]
                theObjects[oname] = {"Name": oname, "Count": 1 + cojb["Count"]}
            else:
                theObjects[oname] = {"Name": oname, "Count": 1}

        # Unique objects detected in video
        for theObject in theObjects:
            strOverall = strOverall + "Name: {}, Count: {}\n".format(theObject, theObjects[theObject]["Count"])

        # Display results
        print(strOverall)

        mailer = ''
        timestamps = []
        for i in getContentModeration['ModerationLabels']:
            conf_level = i['ModerationLabel']['Confidence']
            name = i['ModerationLabel']["Name"]
            parent = i['ModerationLabel']["ParentName"]
            timestamp = i['Timestamp']
            if timestamp not in timestamps:
                if conf_level > 80:
                    string = f'Amazon Rekognition detected "{parent}" at {timestamp}ms "{name}" on video "{filename} with a confidence of {round(conf_level, 1)}%";\n'
                    mailer += string
                    timestamps.append(timestamp)

                table.put_item(
                    Item={
                        "Id": str(uuid.uuid4()),
                        'Timestamp': timestamp,
                        'Confidence': str(round(conf_level, 1)),
                        'Name': name,
                        'ParentName': parent,
                        'Video': filename,
                        'Date': str(datetime.datetime.now())
                    })
        print("Guardado en dynamodb")
        mailer += "\n"
        mailer += strOverall
    

        if mailer != '':
            message = client.publish(TargetArn= SNS_ARN, Message=mailer,
                                    Subject='Amazon Rekognition Video Detection '+filename)
            print("Correo enviado")
            

        results = [{
            'taskId': moderationJobId,
            'resultCode': 'Succeeded',
            'resultString': 'Succeeded'
        }]

    return {
        #'invocationSchemaVersion': invocationSchemaVersion,
        'treatMissingKeysAs': 'PermanentFailure',
        #'invocationId': invocationId,
        'results': results
    }
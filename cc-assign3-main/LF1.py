import io 
import boto3        
import json
import email
import re
import os
from botocore.exceptions import ClientError
# grab environment variables
from sms_spam_classifier_utilities import one_hot_encode
from sms_spam_classifier_utilities import vectorize_sequences
    
ENDPOINT_NAME = os.environ['ENDPOINT_NAME']
# "sms-spam-classifier-mxnet-2022-04-06-17-57-49-391"
runtime = boto3.Session().client('sagemaker-runtime')

s3 = boto3.client('s3')   

def lambda_handler(event, context):
    
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    # bucket = "cc-assign3-ses-emails"
    # key = "0jkg72qhmpkii16min6mkhlroki9g79cmefgqco1"
    
    
    response = s3.get_object(Bucket=bucket, Key=key)
    print('response')
    print(response)

    emailRawString = response['Body'].read()
    receiveDate = response["LastModified"].strftime('%m/%d/%Y')
    parser = email.parser.Parser()
    emailString = parser.parsestr(emailRawString.decode('utf-8'))
    fromaddress = re.findall('\S+@\S+', emailString.get('From'))[0]
    fromaddress = fromaddress[1:len(fromaddress)-1]
    
    subject = emailString['subject']
    if emailString.is_multipart():
        for part in emailString.walk():
            if part.get_content_type() == 'text/plain':
                body = part.get_payload()
    else:
        body = emailString.get_payload()
    print('body')
    print(body)
    print('check')
    print(fromaddress)
    print(subject)
    print(receiveDate)
    print("end")
    
    
    # prediction of spam or not
    vocabulary_length = 9013
    test_messages = [body.replace('\r\n',' ').strip()]
    one_hot_test_messages = one_hot_encode(test_messages, vocabulary_length)
    encoded_test_messages = vectorize_sequences(one_hot_test_messages, vocabulary_length)
    payload = json.dumps(encoded_test_messages.tolist())
    response = runtime.invoke_endpoint(EndpointName=ENDPOINT_NAME,ContentType='application/json',Body=payload)
    print("check response")
    print(response)
    res = json.loads(response['Body'].read())
    print(res)
    
    if res['predicted_label'][0][0] == 0.0:
        classification = "HAM"
    else:
        classification = 'SPAM'
    confidence = res['predicted_probability'][0][0] * 100
    
    # send prediction results back to sender in an email
    print("send email!")
    SENDER = "cc-assign3 <holeking2016@ccassign3.xyz>"
    RECIPIENT = fromaddress
    
    AWS_REGION = "us-east-1"
    SUBJECT = "Prediction Result: Spam or not?"
    CHARSET = "UTF-8"
    BODY_TEXT = ("""We received your email sent at {} with the subject {}.
            Here is a 240 character sample of the email body: {}
            The email was categorized as {} with a {}% confidence.""".format(receiveDate, 
            subject, body, classification, confidence))
            
    # The HTML body of the email.
    BODY_HTML = """<html>
    <head></head>
    <body>
      <h1>Prediction Result: Spam or not?</h1>
      <p>We received your email sent at {} with the subject {}.<p>
        <p>Here is a 240 character sample of the email body: </p>
        <p>{}</p>
        <p>The email was categorized as {} with a {}% confidence.</p>
    </body>
    </html>
                """.format(receiveDate, subject, body, classification, confidence)
    
    sesclient = boto3.client('ses',region_name=AWS_REGION)
    
    try:
        #Provide the contents of the email.
        response = sesclient.send_email(
            Destination={
                'ToAddresses': [
                    RECIPIENT
                ],
            },
            Message={
                'Body': {
                    'Html': {
                        'Charset': CHARSET,
                        'Data': BODY_HTML,
                    },
                    'Text': {
                        'Charset': CHARSET,
                        'Data': BODY_TEXT,
                    },
                },
                'Subject': {
                    'Charset': CHARSET,
                    'Data': SUBJECT,
                },
            },
            Source=SENDER,
        )
    # Display an error if something goes wrong.	
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent! Message ID:"),
        print(response['MessageId'])
    # the end of sending email section. feel free to comment it out when working on others
    
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }

import json
from typing import final
import boto3
from boto3.dynamodb.conditions import Key, Attr
import requests
from requests_aws4auth import AWS4Auth
import random



# 1. pulls a message from the SQS queue 
# 2. gets a random restaurant recommendation according to cuisine 
#       Elastic: find the ID of the restraunt in this cuisine
#       DB: find the resturant information according random selected IDs
# 3. formats them and form message to send
# 4. sends message to the phone number using SNS


def connect():
    #connect sqs
    #pull sqs message
    query = {}
    sqs_client = boto3.client('sqs')
    sqs_url =  'https://sqs.us-east-1.amazonaws.com/033562404598/DiningConcierge' #这里需要一个建好后的url
    resp = sqs_client.receive_message(
        QueueUrl=sqs_url, 
        AttributeNames=['SentTimestamp'],
        MessageAttributeNames=['All'],
        VisibilityTimeout=0,
        MaxNumberOfMessages=1,
        WaitTimeSeconds=0
    )
      
         
    #link https://boto3.amazonaws.com/v1/documentation/api/latest/guide/sqs-example-sending-receiving-msgs.html
    print("check point 1: resp for sqs")
    print(resp)
        
    try:
        if 'Messages' in resp:        
            message_attribute = resp['Messages'][0]
            query = json.loads(message_attribute['Body']) # get cuisine from message later
            print("check point 2: query")
            print(query)
            receipt_handle = message_attribute['ReceiptHandle']
            print("check point 3: receipt_handle")
            print(receipt_handle)
            sqs_client.delete_message(
                QueueUrl=sqs_url,
                ReceiptHandle=receipt_handle
            )
    except: 
        print("Pull sqs message failed")
        

    # query = {'Cusine': 'chinese', 'Phone': '+16463345118', 'NumberOfPeople': '2', 'Time': '19:00', 'Date': '2022-02-21', 'Location': 'manhattan'}
    # print("check point 4: final query")
    # print(query)
    
    return query
    

    # try:
    #     mess = resp['Messages']
    # except KeyError:
    #     print('No messages in the queue!')

    # message = resp['Messages'][0]
    # receipt_handle = message['ReceiptHandle']


    # sqs.delete_message(
    #     QueueUrl=sqs_url,
    #     ReceiptHandle=receipt_handle
    # )


    
    


def loadsInit(recieved):
    # msg_detail = json.loads(recieved)
    msg_detail = recieved
    cuisine_type = msg_detail['Cusine']
   

    date = msg_detail['Date']
    rev_time = msg_detail['Time']
    num_people = msg_detail['NumberOfPeople']
    phone_num = msg_detail['Phone']
    print("check point 5: information sqs ")
    print(cuisine_type)
    print(date)
    print(rev_time)
    print(num_people)
    print(phone_num)

    #这个地方  paramater 已经和 DiningConcierge lex 和 LF 1 匹配

    send_message = "Hello! Here are my {} restaurant suggestions in Manhattan for {} people for {} at {}".format(cuisine_type, num_people, date, rev_time)

    print("check point 5: initial message ")
    print(send_message)
    
    return phone_num, send_message, cuisine_type



def recommend(cuisine):
    
    # elastic search
    # crediential: 
    host = 'https://search-restaurants-gwjv7fubrzkpj6vzjkaiqez6nq.us-east-1.es.amazonaws.com' # The OpenSearch domain endpoint with https://
    index = 'restaurants'
    url = host + '/' + index + '/_search'
    headers = { "Content-Type": "application/json" }
    
    auth = ('hando', '0912Namjoon!') # For testing only. Don't store credentials in code.
    
    print("cuisine in recommend")
    print(cuisine)
    rand = random.randrange(9999999999999999999)
    query = {
            "size": 3,
            "query": {
                "function_score" : {
                "query" : { "query_string": { "query": str(cuisine) } },
                "random_score" : { "seed" : rand }
                }
            }
    }

    esResp = requests.get(url, auth=auth, headers=headers, data=json.dumps(query))
    print(esResp)

    data = json.loads(esResp.text)
    print("check point 8")
    print(data['hits']['hits'])

    try:
         esData =data["hits"]["hits"]
    except KeyError:
         print('No data find by elastic search!')

    idlist = []
    for cur in esData:
        idlist.append(cur["_source"]["RestaurantID"])
    
    print("check point 10")
    print(idlist)
    
    return idlist
    #link https://www.elastic.co/guide/en/elasticsearch/reference/current/search-search.html （reponse 的结构）


    
def searchDB(recommendsID, send_message):
    #connect dynamdb 
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('yelp-restaurants')
    print("initial db")

    track = 1
    for id in recommendsID:
        if track == 4:
            break
        curMsg = ''  
        response = table.scan(FilterExpression=Attr('id').eq(id))
        print("check point response db")
        print(response)
        #link https://stackoverflow.com/questions/44704443/dynamodb-scan-using-filterexpression
        #link https://stackoverflow.com/questions/49179036/how-can-i-scan-a-dynamodb-table-with-python-for-a-specific-key
        # 这个结构上应该有一个item 的index，但是item后边还有没有结构，我不太确定。

        try: 

            item = response['Items'][0]
            print("check item in try")
            print(item)
            name = item["name"]
            address = ' '.join(item["address"])
            
            print("check address in try")
            print(address)
            
            curMsg = ' {0}. {1}, located at {2}.'.format(track, name, address)
            track = track + 1
        
        except:
            print("dynamdb Response Failed")

        
        send_message += curMsg
    
    send_message += "Enjoy your meal!!" 
    
    print("check point send_message in db")
    print(send_message)
    
    return send_message


def sendSNS(phone_num, message):
    #send message to sms
    print('initi sns send')
    print(phone_num)
    print(message)
    
    if phone_num[0] == '+' and phone_num[1] == '1':
        final_num = phone_num
    elif phone_num[0] == '1' and len(phone_num) == 11:
        final_num = '1' + phone_num
    else:
        print("without +1")
        final_num = '+1' + phone_num

    print("check final number")
    print(final_num)
    try:
        client = boto3.client('sns')
        print("check before public")
        response = client.publish(
            PhoneNumber = final_num,
            Message = message
            # messageStructure='string'
        )
    
    except KeyError:
        print("SNS send failed")
    

    #https://stackoverflow.com/questions/34029251/aws-publish-sns-message-for-lambda-function-via-boto3-python2

    
def lambda_handler(event, context):
    # TODO implement
    recieved = connect()

    # phone_num, send_message, cuisine_type = loadsInit(recieved[0]['Body'])
    phone_num, send_message, cuisine_type = loadsInit(recieved) 
    recommendsID = recommend(cuisine_type)
    
    print("check point 11 idlist in main")
    print(recommendsID)
    
    final_message = searchDB(recommendsID, send_message)
    print("check point 12 final message in main")
    print(final_message)
    
    sendSNS(phone_num, final_message)

    return {
        'statusCode': 200,
        'body': json.dumps("LF2 running succesfully")
    }

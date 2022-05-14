import boto3
import json
import requests
# Define the client to interact with Lex
client = boto3.client('lex-runtime')

host = 'https://search-photo-zb3hxahbrrsbcfgx2lryffue6i.us-east-1.es.amazonaws.com' # The OpenSearch domain endpoint with https://
index = 'photo'
url = host + '/' + index + '/_search'
headers = { "Content-Type": "application/json" }
auth = ('hando', '0912Namjoon!')


def lambda_handler(event, context):
    print("event: ")
    print(event)
    # last_user_message = event['q']
    last_user_message = "show me car and leaf"
    
    # change this to the message that user submits on 
    # your website using the 'event' variable
    print(f"Message from frontend: {last_user_message}")
    response = client.post_text(botName='Search',
                                botAlias='searchtest',
                                userId='testuser',
                                inputText=last_user_message)
    
    msg_from_lex = response['message']
    keywords = msg_from_lex.split(" ")
    
    # find result from opensearch
    bucket_url = "https://assign2-b2.s3.amazonaws.com/"
    
    query = {
      "query": {
        "terms_set": {
          "labels": {
            "terms": keywords,
            "minimum_should_match_script": {
              "source": "1"
            },
          }
        }
      }
    }
    # query = {
    #         "size": 1,
    #         "query": {
    #             "function_score" : {
    #             "query" : { "query_string": { "query": 'test5.jpg' } }
    #             }
    #         }
    # }

    esResp = requests.get(url, auth=auth, headers=headers, data=json.dumps(query))
    data = json.loads(esResp.text)
    print("opensearch return:")
    print(data)
    
    photos = []
    
    esData = data["hits"]["hits"]
    for photo in esData:
        photo_detail = {
            'url': bucket_url+photo['_source']['objectKey'],
            'labels': photo['_source']['labels']
        }
        photos.append(photo_detail)
    print(photos)
    
    if len(photos) > 0:
        print(f"Message from Chatbot: {keywords}")
        print(response)
        resp = {
            'statusCode': 200,
            'body': {
                "results": photos
            }
        }
        # modify resp to send back the next question Lex would ask from the user
        
        # format resp in a way that is understood by the frontend
        # HINT: refer to function insertMessage() in chat.js that you uploaded
        # to the S3 bucket
        return resp
    else:
        resp = {
            'statusCode': 400,
            'body': "Nothing from LF2!"
        }
        return resp
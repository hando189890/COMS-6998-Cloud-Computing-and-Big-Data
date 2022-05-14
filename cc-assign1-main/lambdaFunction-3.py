import json

import boto3
import datetime
from itertools import product
#from botocore.vendored import requests
import requests
from decimal import *

from time import sleep



# yelp documentation https://www.yelp.com/developers/documentation/v3/business_search

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('yelp-restaurants')
restaurants = set()

#credential
url = 'https://api.yelp.com/v3/businesses/search'
key = '1Ysr079bw76G_lZowBm1P9BXJN3kgurh0tmN09zgUOENMYOxAJmTTZPsFUyG85OyYtIzGWNB8H_KurGJXYrqJkkcE7m3FmvMTavNnKRF72VkQp3XOVl-17oTmwwNYnYx'
cliendID = 'IqcbO0ZTLnPQypnlXqz0vw'
headers = {
    'Authorization' : 'Bearer %s' % key
}


#scrape

def scrape():
    types = ['chinese', 'italian', 'indian', 'american', 'mexican', 'korean', 'japanese']
    #'korean', 'mediterranean', 'japanese', 'latin'


    for type in types:
     offset = 0
     while offset < 20:
        params = {
          'location': 'Manhattan',
          'offset': offset*50,
          'limit': 50,
          'term': type + " restaurants",
          'sort_by': 'best_match'
        }
        response = requests.request("GET", url, headers=headers, params=params)
        data = response.json()
        addItems(data["businesses"], type)
        offset += 1
        #print(data)
    
        

#add Items in list
def addItems(data, cuisine):
     global restaurants

     with table.batch_writer() as batch:
         for cur in data:
             if cur["alias"] not in restaurants:
                 restaurants.add(cur["alias"])
                 response = table.put_item(Item={
                     'insertedAtTimestamp': str(datetime.datetime.now()),
                     'name': cur["name"],
                     'id': cur["id"],
                     'type': cuisine,
                     'rating': Decimal(str(cur["rating"])),
                     'latitude': Decimal(str(cur["coordinates"]["latitude"])),
                     'longitude': Decimal(str(cur["coordinates"]["longitude"])),
                     'address': cur["location"]["display_address"],
                     'zipcode': cur["location"]["zip_code"],
                     'review': cur["review_count"],
                 })
            # print(response)
             
             

def lambda_handler(event, context):
    # TODO implement
    scrape()
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }

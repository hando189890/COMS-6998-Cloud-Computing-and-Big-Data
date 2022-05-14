import json
import boto3  

def lambda_handler(event, context):
    # TODO implement
    # print(event)
    sqs = boto3.resource('sqs')
    queue = sqs.Queue('https://sqs.us-east-1.amazonaws.com/033562404598/DiningConcierge')
    
    slots = event['currentIntent']['slots']
    cuisines = ['chinese', 'italian', 'indian', 'american', 'mexican']
    if slots["Cusine"] == None:
        return {
            "dialogAction": {
                "type": "ElicitSlot",
                "slotToElicit": "Cusine",
                "intentName": "DiningSuggestionsIntent",
                "slots": slots
            }
        }
    elif slots['Cusine'].lower() not in cuisines:
        slots['Cusine'] = None
        return {
            "dialogAction": {
                "type": "ElicitSlot",
                "slotToElicit": "Cusine",
                "intentName": "DiningSuggestionsIntent",
                "slots": slots
            }
        }
    else:
        slots['Cusine'] = slots['Cusine'].lower()
    
    if slots["Location"] == None:
        return {
            "dialogAction": {
                "type": "ElicitSlot",
                "slotToElicit": "Location",
                "intentName": "DiningSuggestionsIntent",
                "slots": slots
            }
        }
    elif slots['Location'].lower() != 'manhattan':
        slots['Location'] = None
        return {
            "dialogAction": {
                "type": "ElicitSlot",
                "slotToElicit": "Location",
                "intentName": "DiningSuggestionsIntent",
                "slots": slots
            }
        }
        
    if slots["NumberOfPeople"] == None:
        return {
            "dialogAction": {
                "type": "ElicitSlot",
                "slotToElicit": "NumberOfPeople",
                "intentName": "DiningSuggestionsIntent",
                "slots": slots
            }
        }
    if slots["Date"] == None:
        return {
            "dialogAction": {
                "type": "ElicitSlot",
                "slotToElicit": "Date",
                "intentName": "DiningSuggestionsIntent",
                "slots": slots
            }
        }
    if slots["Time"] == None:
        return {
            "dialogAction": {
                "type": "ElicitSlot",
                "slotToElicit": "Time",
                "intentName": "DiningSuggestionsIntent",
                "slots": slots
            }
        }
    if slots["Phone"] == None:
        return {
            "dialogAction": {
                "type": "ElicitSlot",
                "slotToElicit": "Phone",
                "intentName": "DiningSuggestionsIntent",
                "slots": slots
            }
        }
    response = queue.send_message(MessageBody=json.dumps(slots))
    print(response)
    return {
        "dialogAction": {
            "type": "Close",
            "fulfillmentState": "Fulfilled",
            # "intentName": "DiningSuggestionsIntent",
            # "slots": slots,
            "message": {
              "contentType": "PlainText",
              "content": "You’re all set. Expect my suggestions shortly! Have a good day."
            }
        }
    }


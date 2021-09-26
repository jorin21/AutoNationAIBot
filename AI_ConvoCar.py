import json
import random
import decimal
import os
import logging
import traceback

debug=True


# on error, return nice message to bot
def fail(intent_request,error):
    #don't share the full eerror in production code, it's not good to give full traceback data to users
    error = error if debug else ''
    intent_name = intent_request['sessionState']['intent']['name']
    message = {
                'contentType': 'PlainText',
                'content': f"Oops... I guess I ran into an error I wasn't expecting... Sorry about that. My dev should probably look in the logs.\n {error}"
                }
    fulfillment_state = "Fulfilled"
    return close(intent_request, get_session_attributes(intent_request), fulfillment_state, message) 
       
#mock data query against storeinfo.json instead of a database or using an api call
def query_data(sales_hrs, day):
    store_path = os.environ['LAMBDA_TASK_ROOT'] + "/storeinfo.json"
    content=open(store_path).read()
    store_json=json.loads(content)
    filtered= [v for v in store_json if sales_hrs==v['salesHours'] and day==v['day']]
    return filtered

def query_data2(name,address):
    store_path = os.environ['LAMBDA_TASK_ROOT'] + "/storeinfo.json"
    content=open(store_path).read()
    store_json=json.loads(content)
    filtered= [v for v in store_json if name==v['name'] and address==v['address']]
    return filtered

'''''
=== UTIL METHODS ===========================
'''''

#util method to get the slots fromt he request
def get_slots(intent_request):
    return intent_request['sessionState']['intent']['slots']

#util method to get a slot's value
def get_slot(intent_request, slotName):
    slots = get_slots(intent_request)
    if slots is not None and slotName in slots and slots[slotName] is not None and 'interpretedValue' in slots[slotName]['value']:
        return slots[slotName]['value']['interpretedValue']
    else:
        return None
#gets a map of the session attributes
def get_session_attributes(intent_request):
    sessionState = intent_request['sessionState']
    if 'sessionAttributes' in sessionState:
        return sessionState['sessionAttributes']

    return {}
# builds response to tell the bot you want to trigger another intent (use to switch the context)
def elicit_intent(intent_request, session_attributes, message):
    return {
        'sessionState': {
            'dialogAction': {
                'type': 'ElicitIntent'
            },
            'sessionAttributes': session_attributes
        },
        'messages': [ message ] if message != None else None,
        'requestAttributes': intent_request['requestAttributes'] if 'requestAttributes' in intent_request else None
    }
# builds response to tell the bot you need to get the value of a particular slot
def elicit_slot(intent_request, session_attributes,slot_to_elicit, message):
    intent_request['sessionState']['intent']['state'] = 'InProgress'
    return {
        'sessionState': {
            'sessionAttributes': session_attributes,
            'dialogAction': {
                'type': 'ElicitSlot',
                'slotToElicit': slot_to_elicit
            },
            'intent': intent_request['sessionState']['intent']
        },
        'messages': [message],
        'sessionId': intent_request['sessionId'],
        'requestAttributes': intent_request['requestAttributes'] if 'requestAttributes' in intent_request else None
    }
# builds response to end the dialog
def close(intent_request, session_attributes, fulfillment_state, message):
    intent_request['sessionState']['intent']['state'] = fulfillment_state
    return {
        'sessionState': {
            'sessionAttributes': session_attributes,
            'dialogAction': {
                'type': 'Close'
            },
            'intent': intent_request['sessionState']['intent']
        },
        'messages': [message],
        'sessionId': intent_request['sessionId'],
        'requestAttributes': intent_request['requestAttributes'] if 'requestAttributes' in intent_request else None
    }



'''
==== intent handlers =====
'''

# Handle the day and hours for different operations intent
def find_hours(intent_request):
    session_attributes = get_session_attributes(intent_request)
    slots = get_slots(intent_request)
    
    #get slot values 
    sales_hrs=get_slot(intent_request,'sales_hrs')
    day=get_slot(intent_request,'day')
    
    
    #look up data
    results=query_data(sales_hrs, day)
    
    # process results
    if(len(results)==1): 
        print(results)
        found=results[0]
        text = f" Sale hours for {found['day']} are {found['openTime']} to {found['closeTime']}."
    elif(len(results)>1): #Multiple results case; Checking service hours 
        service_hrs=[v for v in results if v['serviceHours']]
        found=service_hrs[0] 
        text = f" Service hours for {found['day']} are {found['openTime']} to {found['closeTime']}. You may reach the department at {found['servicePhoneNumber']}."
    else: #nothing found
        text= f" Sorry, could not find the information you are looking for."

    message =  {
                'contentType': 'PlainText',
                'content': text
                }

    fulfillment_state = "Fulfilled"
    return close(intent_request, session_attributes, fulfillment_state, message)


#this shows an example of using session_attributes to save information over multiple interactions
def store_location(intent_request):
    session_attributes = get_session_attributes(intent_request)
    slots = get_slots(intent_request)
    
    #get slot values 
    name=get_slot(intent_request,'name')
    address=get_slot(intent_request,'address')
    #color=slots['color']['value']['interpretedValue'] if slots['color'] else ''
    
    #look up data
    results=query_data2(name, address)
    
    # process results
    if(len(results)==1): 
        print(results)
        found=results[0]
        text = f" Nearest store is {found['name']}.\n Located at {found['address']}. "
    elif(len(results)>1): #Multiple results case; Checking service hours 
        phoneNum=[v for v in results if v['phoneNumber']] 
        found=phoneNum[0] 
        text = f" Store phone number is {found['phoneNumber']}."
    else: #nothing found
        text= f" Sorry, could not find the information you are looking for."

    message =  {
                'contentType': 'PlainText',
                'content': text
                }

    fulfillment_state = "Fulfilled"
    return close(intent_request, session_attributes, fulfillment_state, message)
            
            
    
# handles the hello intent
def process_hello(intent_request):
    session_attributes = get_session_attributes(intent_request)
    slots = get_slots(intent_request)
    message = {
        'contentType': 'PlainText',
        'content': 'hello from the lambda'
    }
    fulfillment_state = "Fulfilled"
    return close(intent_request, session_attributes, fulfillment_state, message)

#handler for when there is no matching intent handler
def default_response(intent_request):
    session_attributes = get_session_attributes(intent_request)
    intent_name = intent_request['sessionState']['intent']['name']
    message = {
        'contentType': 'PlainText',
        'content': f"This lambda doesn't know how to process intent_name={intent_name}"
    }
    fulfillment_state = "Fulfilled"
    return close(intent_request, session_attributes, fulfillment_state, message)
    

#looks at the intent_name and routes to the handler method    
def dispatch(intent_request):
    try:
        intent_name = intent_request['sessionState']['intent']['name']
        response = None
        # Dispatch to your bot's intent handlers
        if intent_name == 'Hello':
            return process_hello(intent_request)
        elif intent_name == 'DayandHours':
            return find_hours(intent_request)
        elif intent_name == 'StoreLocation':
            return store_location(intent_request)
        else:
            return default_response(intent_request)
    except Exception as ex:
        error = traceback.format_exc()
        print(error)
        return fail(intent_request,error)


    
#entry point of lambda
def lambda_handler(event, context):
    print(json.dumps(event))
    response = dispatch(event)
    return response


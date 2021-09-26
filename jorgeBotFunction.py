import json
import random
import decimal
import os
import logging
import traceback

debug=True



def fail(intent_request,error):
    error = error if debug else ''
    intent_name = intent_request['sessionState']['intent']['name']
    message = {
                'contentType': 'PlainText',
                'content': f"Oops... I guess I ran into an error I wasn't expecting... Sorry about that. My dev should probably look in the logs.\n \n {error}"
                }
    fulfillment_state = "Fulfilled"
    return close(intent_request, get_session_attributes(intent_request), fulfillment_state, message)


def query_data(make,model,reasons):
    inventory_path = os.environ['LAMBDA_TASK_ROOT'] + "/customerinfo.json"
    content=open(inventory_path).read()
    customerinfo_json=json.loads(content)
    filtered= [v for v in customerinfo_json if make==v['make'] and model==v['model']]
    return filtered
    


def get_slots(intent_request):
    return intent_request['sessionState']['intent']['slots']

def get_slot(intent_request, slotName):
    slots = get_slots(intent_request)
    if slots is not None and slotName in slots and slots[slotName] is not None and 'interpretedValue' in slots[slotName]['value']:
        return slots[slotName]['value']['interpretedValue']
    else:
        return None

def get_session_attributes(intent_request):
    sessionState = intent_request['sessionState']
    if 'sessionAttributes' in sessionState:
        return sessionState['sessionAttributes']

    return {}

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






def bookAppointment(intent_request):
    session_attributes = get_session_attributes(intent_request)
    slots = get_slots(intent_request)
    






    



        
    reasons=get_slot(intent_request,'reasons')
    make=get_slot(intent_request,'make')
    date=get_slot(intent_request,'date')
    time=get_slot(intent_request,'time')
    if date and time and reasons and make in session_attributes:
        
        message= {'contentType': 'PlainText','content': f"Your appointment for your {make} vehicle for {reasons} is set and is scheduled for {date} at {time}."}
        fulfillment_state = "Fulfilled"
        return close(intent_request, session_attributes, fulfillment_state, message)
    elif reasons is None:
        message= {'contentType': 'PlainText','content': f'What reason would you like to schedule your appointment for?'}
        return elicit_slot(intent_request,session_attributes,'reasons',message)
    elif date in session_attributes:
        message= {'contentType': '{date}?'}
    else:

        if date is None:
            message= {'contentType': 'PlainText','content': f'What day would you like to schedule the appoint for the {reasons}?'}
            return elicit_slot(intent_request,session_attributes,'date',message)
        elif time is None:
            message= {'contentType': 'PlainText','content': f'What time would you like to schedule the appoint for the {reasons} on {date}?'}
            return elicit_slot(intent_request,session_attributes,'time',message)
        elif make is None:
            message= {'contentType': 'PlainText','content': f'What is the make of your car?'}
            return elicit_slot(intent_request,session_attributes,'make',message)
        else:
            message= {'contentType': 'PlainText','content': "Code has a bug"}
            fulfillment_state = "Fulfilled"
            return close(intent_request, session_attributes, fulfillment_state, message)





def default_response(intent_request):
    session_attributes = get_session_attributes(intent_request)
    intent_name = intent_request['sessionState']['intent']['name']
    message = {
        'contentType': 'PlainText',
        'content': f"This lambda doesn't know how to process intent_name={intent_name}"
    }
    fulfillment_state = "Fulfilled"
    return close(intent_request, session_attributes, fulfillment_state, message)
    

  
def dispatch(intent_request):
    try:
        intent_name = intent_request['sessionState']['intent']['name']
        response = None

        if intent_name == 'bookAppointment':
            return bookAppointment(intent_request)

        else:
            return default_response(intent_request)
    except Exception as ex:
        error = traceback.format_exc()
        print(error)
        return fail(intent_request,error)


    

def lambda_handler(event, context):
    print(json.dumps(event))
    response = dispatch(event)
    return response
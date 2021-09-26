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
                'content': f"Oops... I guess I ran into an error I wasn't expecting... Sorry about that. My dev should probably look in the logs.\n \n {error}"
                }
    fulfillment_state = "Fulfilled"
    return close(intent_request, get_session_attributes(intent_request), fulfillment_state, message)

# querying the data to input into slot
def query_data(make,model,reasons):
    inventory_path = os.environ['LAMBDA_TASK_ROOT'] + "/customerinfo.json"
    content=open(inventory_path).read()
    customerinfo_json=json.loads(content)
    filtered= [v for v in customerinfo_json if make==v['make'] and model==v['model'] and reasons==v['reasons']]
    return filtered




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



#handle the bookAppointment intent.
#this shows an example of using session_attributes to save information over multiple interactions
def bookAppointment(intent_request):
    session_attributes = get_session_attributes(intent_request)
    slots = get_slots(intent_request)
    

#trying to place appointments




    
    # check if we already set the session data
    if 'selectedReason' not in session_attributes:
        reasons=get_slot(intent_request,'reasons')
        if reasons: #if reason is set in the slots query the data
            resultsReason = query_data(reasons)
            if len(resultsReason)>0:
                v=resultsReason[0] #pick the first reason to match
                # set the display value of the selected reason
                session_attributes['selectedReason']=f"{v['reasons']}"
            else: #no match no reason
                message= {'contentType': 'PlainText','content': f"Sorry, we don't offer appointments for {reasons} right now"}
                fulfillment_state = "Fulfilled"
                return close(intent_request, session_attributes, fulfillment_state, message)
        
    
    make=get_slot(intent_request,'make')
    date=get_slot(intent_request,'date')
    time=get_slot(intent_request,'time')
    if date and time and make and 'selectedReason' in session_attributes:
        reason_str = session_attributes['reasons']
        # all data available fulfill
        message= {'contentType': 'PlainText','content': f"Your appointment for {reason_str} is set and is scheduled for {date} at {time}."}
        fulfillment_state = "Fulfilled"
        return close(intent_request, session_attributes, fulfillment_state, message)
    elif 'selectedReasons' in session_attributes:
        reason=session_attributes['selectedReasons']
        # still need data delegate to the bot
        if date is None:
            message= {'contentType': 'PlainText','content': f'What day would you like to schedule the appoint for the {reasons}?'}
            return elicit_slot(intent_request,session_attributes,'date',message,make)
        elif time is None:
            message= {'contentType': 'PlainText','content': f'What time would you like to schedule the appoint for the {reason}?'}
            return elicit_slot(intent_request,session_attributes,'time',message,make)
        elif make is None:
            message= {'contentType': 'PlainText','content': f'What is the make of your car?'}
            return elicit_slot(intent_request,session_attributes,time,message,'make')
        else:
            message= {'contentType': 'PlainText','content': "Bruhmoment...Check your code idiot"}
            fulfillment_state = "Fulfilled"
            return close(intent_request, session_attributes, fulfillment_state, message,make)




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
        if intent_name == 'bookAppointment':
            return bookAppointment(intent_request)

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
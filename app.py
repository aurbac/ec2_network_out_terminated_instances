import boto3
from datetime import datetime, timedelta
import time
import botocore
import ssl
import os
import json
#import pandas as pd
import os.path
from os import path

from botocore.exceptions import ClientError
from boto3 import Session

def describeServiceItems( client , describe_function, key_items, filters="", next_step=""):
	try:
		if (next_step!=""):
			#print("Filters - " + filters)
			filters_to_add = ""
			if filters != "":
				filters_to_add = ", "+filters
			if describe_function=="list_resource_record_sets":
				strfunction = "client."+describe_function+"(StartRecordName='"+next_step+"'"+filters_to_add+")"
			else:
				strfunction = "client."+describe_function+"(NextToken='"+next_step+"'"+filters_to_add+")"
			#print("1 - " + strfunction)
			response = eval(strfunction)
		else:
			strfunction = "client."+describe_function+"("+filters+")"
			#print("2 - " + strfunction)
			response = eval(strfunction)
		listItems = []
		if not key_items in response or len(response[key_items])<=0:
			return False
		else:
			listItems = response[key_items]
		##print("");
		if 'NextToken' in response:
			#print("go 1")
			listItems += describeServiceItems(client, describe_function, key_items, filters, response['NextToken'])
		if 'NextRecordName' in response:
			#print("go 2")
			listItems += describeServiceItems(client, describe_function, key_items, filters, response['NextRecordName'])
		return listItems
	except botocore.exceptions.EndpointConnectionError as e:
		print(e)
		return False
	except ClientError as e:
		print(e)
		return False
		
def isTrueOrFalse( bool_vale ):
	if bool_vale:
		return "True"
	else:
		return "False"


def getExistsValueKey( item, keyname ):
	if keyname in item:
		return item[keyname]
	else:
		return ""


def existsKey( item, keyname ):
	if keyname in item:
		return True
	else:
		return False

def getValueTag( items, keyname ):
	for item in items:
		if item['Key'] == keyname:
			return item['Value']
	return ""
		
def getValueFromArray(items):
	strVO = ""
	for index, item in enumerate(items):
		if index < len(items) and index > 0:
			strVO += ", "
		strVO += item
	return strVO
	
def getRoleFromProfile (item):
	strRole = ""
	if item!="":
		values = item['Arn'].split(":")
		return values[5].split("/")[1]
	else:
		return strRole

def isValueInArray(value, items, key):
	for item in items:
		if key in item:
			if item[key]==value:
				return True
	return False
	
def getItemFromArray(key, value, items):
	for item in items:
		if key in item and item[key]==value:
			return item
	return False

	
client_cw = boto3.client('cloudwatch')
client = boto3.client('cloudtrail')

instances_data = []

start_time =  datetime.today() - timedelta(days=30)
response = client.lookup_events(LookupAttributes=[{ 'AttributeKey': "EventName", "AttributeValue": "TerminateInstances" }],StartTime=start_time, EndTime=datetime.today() )
for item in response['Events']:
    #print(item['Resources'])
    for resource in item['Resources']:
        #print(resource['ResourceName'])
        item_service = { "InstanceId": resource['ResourceName'] } 
        responseDatapoints = describeServiceItems(client_cw, "get_metric_statistics", "Datapoints", " Namespace='AWS/EC2', MetricName='NetworkOut', Dimensions=[ { 'Name' : 'InstanceId', 'Value': '"+resource['ResourceName']+"'  } ], Period=86400, Statistics=['Sum'], StartTime=datetime.today() - timedelta(days=30), EndTime=datetime.today(), Unit='Bytes'")
        if responseDatapoints:
        	total = 0
        	for data_point in responseDatapoints:
        		total += data_point['Sum']
        	item_service['NetOut-Total-Gigabytes-30days'] = round(total/1000000000,2)
        instances_data.append(item_service)

print(json.dumps(instances_data))

'''
responseVpcs = describeServiceItems(client, "lookup_events", "Events")
if responseVpcs:
	dataVpcs = []
	for item in responseVpcs:
		item_service = {}
		item_service['AccountId'] = account_id
		item_service['Region'] = AWS_DEFAULT_REGION
		item_service['Name'] = getValueTag( getExistsValueKey(item, 'Tags'), "Name")
		item_service['VpcId'] = item['VpcId']
		item_service['State'] = item['State']
		item_service['CidrBlock'] = item['CidrBlock']
		item_service['DhcpOptionsId'] = item['DhcpOptionsId']
		item_service['InstanceTenancy'] = item['InstanceTenancy']
		item_service['IsDefault'] = isTrueOrFalse(item['IsDefault'])
		dataVpcs.append(item_service)
	df = pd.DataFrame(dataVpcs)
	df.to_csv(path_folder+'/vpc_vpcs.csv', index=False)
'''
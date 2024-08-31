import json
import requests
import boto3
from botocore.exceptions import ClientError
from datetime import datetime




def get_secret():

    secret_name = "EnphaseDetails"
    region_name = "us-east-2"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        return client.get_secret_value(
            SecretId=secret_name
        )['SecretString']
         
    except ClientError as e:
        print("Secret error:",e)
    

def lambda_handler(event, context):
    
    
    dynamodb = boto3.resource('dynamodb') 
    #table name 
    table = dynamodb.Table('Enphase_User_System_Devices')
    
    if event['httpMethod']=='POST':
        
        postData =  event['body']
        postDataDict = json.loads(postData)
        
        conData = json.loads(get_secret())
        print("Secret Data", conData)
        
        if event['path'] == "/resource_systems_site":
            responseData = {}
            try:
                if not postDataDict.get('siteID'):
                    raise Exception("Provide the siteID")
                systemID = postDataDict.get('siteID')
                # accessTokenGeneration = requests.post('https://api.enphaseenergy.com/oauth/token?grant_type=authorization_code&redirect_uri=https://api.enphaseenergy.com/oauth/redirect_uri&code=UjjrAR', auth =('1b0dc4ecc662773617b93d290bd00033', '9ac449cb7fa58759eaa154f6595b7267') )
                # print(accessTokenGeneration.json())
                print("systemID", systemID)
                params = {'key' :conData["enphaseKey"]} #'6e699734664cd6ed1eebc2f7b527224f'
                headers = {'Authorization': f'Bearer {conData["AToken"]}'}
                print("params", params)
                print("headers",headers)
                #  Gets the system details
                systemURL = 'https://api.enphaseenergy.com/api/v4/systems'
                systemDetails =  requests.get(systemURL,params= params, headers=headers)
                print("system details API response", systemDetails.status_code )
                if systemDetails.status_code != 200 :
                    raise Exception("Access Token Expired")
                systemDetails = systemDetails.json()
                responseData['systemDetails'] = systemDetails
                
                # Gets the Device Details by using the System ID
                
                devicesURL = f'https://api.enphaseenergy.com/api/v4/systems/{systemID}/devices'
                deviceDetails = requests.get(devicesURL,params= params, headers=headers).json()
                print("Device details API response", deviceDetails)
                responseData['deviceDetails'] = deviceDetails
                
                # Gets the inverters summary by siteid(system ID)
                
                invertersSummaryURL = 'https://api.enphaseenergy.com/api/v4/systems/inverters_summary_by_envoy_or_site'
                params['site_id'] = systemID #5347528
                invertersSummary = requests.get(invertersSummaryURL,params= params, headers=headers).json()
                print("invertersSummary API response", invertersSummary)
                responseData['invertersSummary'] = invertersSummary
                
                finalResult = {}
                print("finalResult",finalResult)
                finalResult['partner']={
                    "name":"",
                    "siteID":systemID
                }
                finalResult['customers']=[
                    {
                        "name": system["name"],
                        "timezone": system["timezone"],
                        "email":None,
                        "phone":None,
                        "lastName":None,
                        "firstName": None,
                        "address": system["address"],
                    }
                    for system in systemDetails['systems']
                ]
                finalResult['systemDetails']={
                    "systemType":systemDetails['systems'][0]['public_name'],
                    "systemSize":systemDetails['systems'][0]['system_size'],
                    "ptoDate": datetime.fromtimestamp(systemDetails['systems'][0]['operational_at']).strftime('%Y-%m-%d'),
                    "interconnectionDate":systemDetails['systems'][0]['interconnect_date'],
                }
                finalResult['installationPartner'] = {
                    "email":None,
                    "name":None,
                    "phone":None,
                    "address":None
                }
                finalResult['utiltyProvider'] = {
                    "utilityName":None,
                    "utilityMeterId":None
                }
                finalResult['devices'] = deviceDetails['devices']
                print("finalResult",finalResult)
                #inserting values into table 
                # site-20240831-6digit(L/N)
                response = table.put_item( 
                   Item={ 
                        'userID': "887899", 
                        'userEnphaseDetails': finalResult
                    } 
                ) 
                print("response of put_item",response )
                return{
                    'statusCode': 200,
                    'body': json.dumps(finalResult)
                }
            
            except Exception as e:
                print("error", e)
                return{
                    'statusCode': 200,
                    'body': json.dumps({"error": str(e)})
                }
        
        
    
    
    # TODO implement
    # return {
    #     'statusCode': 200,
    #     'body': json.dumps('Hello from Lambda!')
    # }

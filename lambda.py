import pg8000.native as psycopg2
import boto3
import json
import os

def get_db_credentials():
    """
    Retrieve database credentials from AWS Secrets Manager.

    Parameters:
    secret_name (str): The name of the secret in AWS Secrets Manager.
    region_name (str): The AWS region where the secret is stored.

    Returns:
    dict: A dictionary containing the username and password.
    """

    secret_name = os.environ.get('SECRET_NAME')
    print(secret_name)
    try:
        return {
            'user': 'postgres',
            'password': f"{secret_name}",
            'host': 'genai-workshop.cluster-c9micoqmu13m.us-west-2.rds.amazonaws.com',
            'database': 'postgres'
        }

    except Exception as e:
        print(f"Error retrieving secret: {str(e)}")
        return None



# Connect to the database
def connect_database(conn_params, dictionary=False):
    #print(conn_params)
    return psycopg2.Connection(**conn_params)
    return None

def get_tables():
    credentials = get_db_credentials()
    conn = connect_database(credentials)
    print("getting tables")
    data = []
    results = conn.run("""SELECT table_name
  FROM information_schema.tables
 WHERE table_schema='public'
   AND table_type='BASE TABLE';;
""")
    data.extend(results)
    return data
    
def get_column_names(tableName):
    credentials = get_db_credentials()
    conn = connect_database(credentials)
    table_name = tableName[0]["value"]
    data = []
    results = conn.run(f"SELECT column_name FROM information_schema.columns where table_name = '{table_name}'")
    data.extend(results)
    return data

def lambda_handler(event, context):
    action = event['actionGroup']
    api_path = event['apiPath']
    if api_path == '/tables':
        body = get_tables()
    elif api_path == '/table/{tableName}/columns':
        parameters = event['parameters']
        body = get_column_names(parameters)
    else:
        body = {"{}::{} is not a valid api, try another one.".format(action, api_path)}

    response_body = {
        'application/json': {
            'body': str(body)
        }
    }

    action_response = {
        'actionGroup': event['actionGroup'],
        'apiPath': event['apiPath'],
        'httpMethod': event['httpMethod'],
        'httpStatusCode': 200,
        'responseBody': response_body
    }

    response = {'response': action_response}
    return response
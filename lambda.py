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

    # Create a Secrets Manager client
    client = boto3.client(service_name='secretsmanager')
    
    try:
        # Retrieve the secret
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
        
        # Error handling for missing secrets
        if 'SecretString' in get_secret_value_response:
            secret = get_secret_value_response['SecretString']
            secret_dict = json.loads(secret)
            return {
                'user': secret_dict['username'],
                'password': secret_dict['password'],
                'host': secret_dict['host'],
                'database': secret_dict['db']
            }
        else:
            raise Exception("Secret binary not supported.")

    except Exception as e:
        print(f"Error retrieving secret: {str(e)}")
        return None

# Initialize the AWS Bedrock client (replace 'service-name' with the actual AWS service used by Bedrock)
def initialize_bedrock_client():
    return boto3.client('bedrock-runtime')

# Connect to the database
def connect_database(conn_params, dictionary=False):
    return psycopg2.Connection(**conn_params)

def get_tables():
    credentials = get_db_credentials()
    conn = connect_database(credentials)

    data = []
    with conn.cursor() as cur:
        cur.run("""SELECT table_schema x|| '.' || table_name
FROM information_schema.tables
WHERE table_type = 'BASE TABLE'
AND table_schema NOT IN ('pg_catalog', 'information_schema');
""")
        data.extend(cur.fetchall())
    return data
    
def get_column_names(tableName):
    credentials = get_db_credentials()
    conn = connect_database(credentials)
    table_name = tableName[0]["value"]
    data = []
    with conn.cursor() as cur:
        cur.run(f"SHOW COLUMNS FROM {table_name}")
        data.extend(cur.fetchall())
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
import json
import boto3
import psycopg2
import os
import time
from botocore.exceptions import ClientError

# Initialize AWS clients
print("Initializing Lambda function...")

# Global connection pool (reuse across invocations)
db_connection = None
db_credentials_cache = None

def get_db_credentials():
    """Retrieve database credentials from Secrets Manager with caching."""
    global db_credentials_cache
    
    # Return cached credentials if available
    if db_credentials_cache:
        print("Using cached database credentials")
        return db_credentials_cache
    
    secret_arn = os.environ.get('SECRET_ARN')
    if not secret_arn:
        raise ValueError("SECRET_ARN environment variable not set")
    
    print(f"Fetching credentials from Secrets Manager: {secret_arn}")
    
    try:
        # Initialize client (this needs internet/VPC endpoint access)
        secretsmanager_client = boto3.client('secretsmanager', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
        
        start_time = time.time()
        response = secretsmanager_client.get_secret_value(SecretId=secret_arn)
        elapsed = time.time() - start_time
        
        print(f"Retrieved secret in {elapsed:.2f}s")
        
        secret = json.loads(response['SecretString'])
        db_credentials_cache = secret  # Cache for future invocations
        return secret
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        print(f"ClientError retrieving secret: {error_code} - {e}")
        
        if error_code == 'ResourceNotFoundException':
            raise ValueError(f"Secret not found: {secret_arn}")
        elif error_code == 'InvalidRequestException':
            raise ValueError(f"Invalid request for secret: {secret_arn}")
        else:
            raise e
    except Exception as e:
        print(f"Unexpected error retrieving secret: {type(e).__name__} - {e}")
        raise e

def get_db_connection():
    """Establish connection to PostgreSQL database with connection pooling."""
    global db_connection
    
    # Reuse existing connection if available and valid
    if db_connection:
        try:
            # Test if connection is still alive
            cursor = db_connection.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            print("Reusing existing database connection")
            return db_connection
        except Exception as e:
            print(f"Existing connection invalid, creating new one: {e}")
            db_connection = None
    
    print("Creating new database connection...")
    credentials = get_db_credentials()
    
    # Extract host without port if present
    host = credentials['host'].split(':')[0]
    
    print(f"Connecting to PostgreSQL at {host}:{credentials['port']}")
    
    try:
        start_time = time.time()
        connection = psycopg2.connect(
            host=host,
            port=credentials['port'],
            database=credentials['database'],
            user=credentials['username'],
            password=credentials['password'],
            connect_timeout=10  # 10 second timeout
        )
        elapsed = time.time() - start_time
        print(f"Connected to database in {elapsed:.2f}s")
        
        db_connection = connection
        return connection
        
    except psycopg2.OperationalError as e:
        print(f"Database connection failed: {e}")
        raise ValueError(f"Cannot connect to database at {host}:{credentials['port']} - Check VPC/Security Groups")
    except Exception as e:
        print(f"Unexpected database error: {type(e).__name__} - {e}")
        raise e

def lambda_handler(event, context):
    """
    Lambda handler to fetch maze level data.
    
    Expects:
        GET /level/{stage_number}
    
    Returns:
        JSON with level data or error message
    """
    
    print(f"Lambda invoked. Event: {json.dumps(event)}")
    print(f"Remaining time: {context.get_remaining_time_in_millis()}ms")
    
    # Enable CORS
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'GET, OPTIONS',
        'Content-Type': 'application/json'
    }
    
    try:
        # Extract stage number from path parameters
        stage_number = event.get('pathParameters', {}).get('stage_number')
        print(f"Requested stage_number: {stage_number}")
        
        if not stage_number:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({
                    'error': 'Missing stage_number parameter'
                })
            }
        
        # Validate stage number
        try:
            stage_number = int(stage_number)
            if stage_number < 1 or stage_number > 10:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({
                        'error': 'Stage number must be between 1 and 10'
                    })
                }
        except ValueError:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({
                    'error': 'Invalid stage_number format'
                })
            }
        
        print(f"Fetching stage {stage_number} from database...")
        
        # Connect to database
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Query for the specific stage
        query = """
            SELECT stage_id, stage_number, layout, width, height, 
                   start_x, start_y, end_x, end_y
            FROM maze_stages
            WHERE stage_number = %s
        """
        
        print(f"Executing query for stage {stage_number}")
        start_time = time.time()
        cursor.execute(query, (stage_number,))
        result = cursor.fetchone()
        elapsed = time.time() - start_time
        print(f"Query completed in {elapsed:.2f}s")
        
        if not result:
            cursor.close()
            print(f"Stage {stage_number} not found in database")
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({
                    'error': f'Stage {stage_number} not found'
                })
            }
        
        # Build response
        stage_data = {
            'stage_id': result[0],
            'stage_number': result[1],
            'layout': result[2],
            'width': result[3],
            'height': result[4],
            'start_x': result[5],
            'start_y': result[6],
            'end_x': result[7],
            'end_y': result[8]
        }
        
        cursor.close()
        # Don't close connection - reuse it (global connection pool)
        
        print(f"Successfully retrieved stage {stage_number}")
        print(f"Remaining time: {context.get_remaining_time_in_millis()}ms")
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'success': True,
                'data': stage_data
            })
        }
        
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e),
                'type': type(e).__name__
            })
        }

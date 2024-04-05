import boto3
import time
import json
import logging
import os

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# temporary file path to store previous prefix count value
file_path = '/tmp/previous_prefix_count.txt'

# Function to get the previous prefix count from the temporary file created by Lambda
def get_previous_prefix_count():
    try:
        with open(file_path, 'r') as file:
            return int(file.read().strip())
    except Exception as e:
        logger.error(f"Error getting previous prefix count: {str(e)}")
        return 0

# Function to update and store the previous prefix count in a file for comparison 
def update_previous_prefix_count(count):
    try:
        logger.info(f"Updating previous prefix count. New count: {count}")
        with open(file_path, 'w') as file:
            file.write(str(count))
        logger.info("Update successful.")
    except Exception as e:
        logger.error(f"Error updating previous prefix count: {str(e)}")

# Function to send an alert using AWS SNS
def send_alert(message, subject, sns_topic_arn, region):
    sns_client = boto3.client('sns', region_name=region)
    sns_client.publish(TopicArn=sns_topic_arn, Message=message, Subject=subject)

# Function to send a log message to AWS CloudWatch Logs
def send_log_to_cloudwatch(log_message, log_group_name, log_stream_name, region):
    try:
        logs_client = boto3.client('logs', region_name=region)
        timestamp = int(time.time() * 1000)
        log_event = {'timestamp': timestamp, 'message': log_message}
        logs_client.put_log_events(logGroupName=log_group_name, logStreamName=log_stream_name, logEvents=[log_event])
    except Exception as e:
        logger.error(f"Error sending log to CloudWatch Logs: {str(e)}")
        return None


# AWS Lambda function handler
def lambda_handler(event, context):

# Replace the values in this section with your own values
    region = '<Your_AWS_region>'
# You can add multiple AWS regions if the services are present in different regions.
    transit_gateway_id = '<Your_TGW_ID>'
    sns_topic_arn = '<SNS_topic_ARN>'
    log_group_name = '<Log_Group_name>'
    log_stream_name = '<Log_Stream_name>'
    threshold = <threshold>


    # Creating an EC2 client and getting the previous count value from the file
    ec2_client = boto3.client('ec2', region_name=region)
    previous_count = get_previous_prefix_count()

# Setting filters for querying transit gateway route tables
    filters = [{'Name': 'transit-gateway-id', 'Values': [transit_gateway_id]}]

# Make the describe-transit-gateway-route-tables API call with the specified filters
    try:
        response = ec2_client.describe_transit_gateway_route_tables(Filters=filters)

    # store the route counts for each Direct Connect Gateway attachment
        attachment_route_count = {'IPv4': 0, 'IPv6': 0}
        attachments_info = []  # List to store attachment information

        # Iterating through route tables and counting the number of IPv4 and IPv6 routes
        for route_table in response.get('TransitGatewayRouteTables', []):
            route_table_id = route_table['TransitGatewayRouteTableId']
            routes_response = ec2_client.search_transit_gateway_routes(
                TransitGatewayRouteTableId=route_table_id,
                Filters=[
                    {'Name': 'attachment.resource-type', 'Values': ['direct-connect-gateway']},
                    {'Name': 'type', 'Values': ['propagated']}
                ]
            )

            for route in routes_response.get('Routes', []):
                route_type = 'IPv6' if ':' in route['DestinationCidrBlock'] or '::' in route['DestinationCidrBlock'] else 'IPv4'
                attachment_route_count[route_type] += 1

            for attachment in route.get('TransitGatewayAttachments', []):
                    if attachment['ResourceType'] == 'direct-connect-gateway':
                        attachment_info = {'attachment_id': attachment['ResourceId']}
                        attachments_info.append(attachment_info)


        # Send cumulative log to CloudWatch Logs
        log_message = {
            'attachment_route_count': attachment_route_count,
            'attachments_info': attachments_info
        }
        send_log_to_cloudwatch(json.dumps(log_message), log_group_name, log_stream_name, region)


        # Check if either the IPv4 or IPv6 route count exceeds the threshold value.
        if attachment_route_count['IPv4'] >= threshold or attachment_route_count['IPv6'] >= threshold:
            current_max = max(attachment_route_count['IPv4'], attachment_route_count['IPv6'])
            logger.info(f"Current Max Count: {current_max}, Previous Count: {previous_count}")
            if current_max > previous_count:
                # Send an alert if the route count exceeds the threshold

                unique_attachment_ids = set(attachment_info['attachment_id'] for attachment_info in attachments_info)
                message = f"Learned prefixes over DXGW has reached a maximum threshold - IPv4: {attachment_route_count['IPv4']}, IPv6: {attachment_route_count['IPv6']}. Configured threshold is {threshold}. Unique Attachment IDs: {', '.join(unique_attachment_ids)}"
                send_alert(message, "Number of Direct Connect Learned Prefixes exceeding threshold", sns_topic_arn, region)

        else:
            # If the condition is not met, update current_max anyway
            current_max = max(attachment_route_count['IPv4'], attachment_route_count['IPv6'])

#Update the current prefix count in the temporary file for comparision
        update_previous_prefix_count(current_max)

        return {'statusCode': 200, 'body': 'Success'}

    except Exception as e:
        error_message = f"Error: {str(e)}"
        logger.error(error_message, exc_info=True)
        return {'statusCode': 500, 'body': 'Error'}

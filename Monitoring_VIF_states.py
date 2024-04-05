import boto3
import json
import time

# Replace section: Replace with your own values
log_group_name = '<Log_Group_name>'
log_stream_name = '<Log_Stream_name>'
sns_topic_arn = '<SNS_topic_ARN>'
aws_region = '<aws_region>' 
# You can add multiple AWS regions if the services are present in different regions by specifying another aws_region as mentioned below and use it while initializing the boto3 clients.
#aws_cross_region = '<aws_region_2>'

# Initialize the Boto3 clients
cloudwatch = boto3.client('cloudwatch', region_name=aws_region)
sns = boto3.client('sns', region_name=aws_region)
directconnect = boto3.client('directconnect', region_name=aws_region)
#The regions can be different than the aws_region where the Lambda function is created. 
#You can use the “region_name” value as “aws_cross_region” for cross region service which is defined above in the replace section.

logs = boto3.client('logs', region_name=aws_region)
 


# Maintaining a set to track VIFs that have triggered an alert. Lambda persists global variables between invocations.
alerted_vifs = set()

def lambda_handler(event, context):
    try:
        # Get BGP information for all Direct Connect VIFs
        response = directconnect.describe_virtual_interfaces()

        # If no VIFs found, log the message and return
        if len(response['virtualInterfaces']) == 0:
            no_vifs_found = "No VIFs found"
            print(no_vifs_found)
            logs.put_log_events(
                logGroupName=log_group_name,
                logStreamName=log_stream_name,
                logEvents=[
                    {
                        'timestamp': int(round(time.time() * 1000)),
                        'message': no_vifs_found
                    }
                ]
            )
            return {
                'statusCode': 200,
                'body': json.dumps('No VIFs found')
            }

        # Create lists to store information about VIFs with down neighborship
        down_vifs = []
        up_vifs = []

        # Iterate through the VIFs and check the BGP neighborship status
        for vif in response['virtualInterfaces']:
            vif_id = vif['virtualInterfaceId']
            bgp_peers = vif['bgpPeers']
            neighborship_status = "UP" if all(peer['bgpStatus'] == 'up' for peer in bgp_peers) else "DOWN"

            # Log the status to CloudWatch Logs
            log_message = f"BGP neighborship status for VIF {vif_id} is {neighborship_status}"
            print(log_message)

            # Use the logs client to put log events
            logs.put_log_events(
                logGroupName=log_group_name,
                logStreamName=log_stream_name,
                logEvents=[
                    {
                        'timestamp': int(round(time.time() * 1000)),
                        'message': log_message
                    }
                ]
            )

            # Check if the VIF is down and hasn't triggered an alert yet
            if neighborship_status == "DOWN" and vif_id not in alerted_vifs:
                down_vifs.append(vif_id)
                alerted_vifs.add(vif_id)
            elif neighborship_status == "UP" and vif_id in alerted_vifs:
                # If the VIF is now up, remove it from the alerted list
                alerted_vifs.remove(vif_id)
                up_vifs.append(vif_id)

        # Send a separate SNS alert for all VIFs that are down
        if down_vifs:
            for vif_id in down_vifs:
                sns.publish(
                    TopicArn=sns_topic_arn,
                    Subject=f'VIF: {vif_id} BGP Neighborship Down',
                    Message=f"The BGP neighborship is DOWN for VIF {vif_id}"
                )

	# Send a separate SNS alert for all VIFs that are now up
        if up_vifs:
            for vif_id in up_vifs:
                sns.publish(
                    TopicArn=sns_topic_arn,
                    Subject=f'VIF: {vif_id} BGP Neighborship Restored',
                    Message=f"The BGP neighborship has been restored for VIF {vif_id}."
                )

        return {
            'statusCode': 200,
            'body': json.dumps('Success')
        }

    except Exception as e:
        # Log any errors to CloudWatch Logs
        error_message = f"Error: {str(e)}"
        print(error_message)

        # Use the logs client to put log events for errors as well
        logs.put_log_events(
            logGroupName=log_group_name,
            logStreamName='<Log_Stream_name>',
            logEvents=[
                {
                    'timestamp': int(round(time.time() * 1000)),
                    'message': error_message
                }
            ]
        )
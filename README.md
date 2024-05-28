# AWS Direct Connect Monitoring Solution

## Introduction
As businesses transition to cloud-based infrastructure, establishing reliable connectivity between on-premises and cloud environments becomes a critical requirement. AWS Direct Connect provides a dedicated network link that extends a corporate data center network into the Amazon Web Services (AWS) Cloud. At the core of this connection is the Border Gateway Protocol (BGP), a dynamic routing protocol that initiates and maintains connections between these networks. This project explores mechanisms for monitoring these connections and sending alerts when their state changes.

## Features
This project provides a comprehensive solution for monitoring and alerting on the following aspects of your AWS Direct Connect setup:
VIF State Monitoring: Establish a notification mechanism to receive alerts when there are changes in the state of virtual interfaces (VIFs) within your AWS account, whether they are transit, private, or public VIFs.
Prefix Count Monitoring: Monitor the number of prefixes propagated from the AWS Direct Connect Gateway (DXGW) attachment to an AWS Transit Gateway route table, and receive notifications when the number of prefixes exceeds a defined threshold.

## Prerequisites
To use this solution, you will need:
- An AWS account
- A Direct Connect connection (dedicated or hosted) with an operational VIF
- Permissions to create an AWS Lambda function, Amazon CloudWatch, Amazon Simple Notification Service (Amazon SNS), and Amazon EventBridge
  
## Installation and Configuration
### VIF State Monitoring:
- Create an IAM role for the Lambda functions with the necessary permissions.
- Create an Amazon SNS topic and subscription to receive alert notifications.
- Set up a CloudWatch log group and log stream to store VIF information.
- Create a Lambda function to monitor VIF states and send alerts.
- Configure an EventBridge trigger to run the Lambda function every minute.
  
### Prefix Count Monitoring:
- Create an IAM role for the Lambda functions with the necessary permissions.
- Establish an Amazon SNS topic and subscription to receive alert notifications.
- Create a CloudWatch log group and log stream to store prefix count information.
- Develop a Lambda function to monitor the number of prefixes propagated from the DXGW attachment to the Transit Gateway route table.
- Configure an EventBridge trigger to run the Lambda function every minute.
  
Detailed step-by-step instructions can be found in the Walk-through section of this [BLOG](https://aws.amazon.com/blogs/networking-and-content-delivery/monitor-bgp-status-on-aws-direct-connect-vifs-and-track-prefix-count-advertised-over-transit-vif/)

## Usage
The provided solution will automatically monitor your VIF states and the number of prefixes propagated over the transit VIF. When changes occur, such as a VIF going down or the prefix count exceeding a defined threshold, you will receive email notifications to the specified address.
You can customize the threshold values and other parameters within the Lambda functions to suit your specific requirements.
Contributing
If you encounter any issues or have suggestions for improvements, please feel free to open a new issue or submit a pull request. Contributions are welcome!

## License
This project is licensed under the [MIT License](https://console.harmony.a2z.com/internal-ai-assistant/LICENSE).

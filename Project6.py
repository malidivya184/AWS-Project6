# =========================================================
# AWS Automated Cost Optimizer using Boto3
# =========================================================
# Features:
# ✅ Detects low CPU EC2 instances
# ✅ Stops idle instances automatically
# ✅ Prints detailed logs
# ✅ Handles AWS errors properly
# ✅ Can run locally OR in AWS Lambda
#
# AWS Services Used:
# - EC2
# - CloudWatch
# - Lambda
# =========================================================

import boto3
from botocore.exceptions import NoCredentialsError, ClientError
from datetime import datetime, timedelta

# ---------------------------------------------------------
# AWS Clients
# ---------------------------------------------------------
ec2 = boto3.client('ec2', region_name='ap-south-1')
cloudwatch = boto3.client('cloudwatch', region_name='ap-south-1')

# ---------------------------------------------------------
# Get CPU Utilization Function
# ---------------------------------------------------------
def get_cpu_utilization(instance_id):

    end_time = datetime.utcnow()
    start_time = end_time - timedelta(minutes=30)

    try:
        response = cloudwatch.get_metric_statistics(
            Namespace='AWS/EC2',
            MetricName='CPUUtilization',
            Dimensions=[
                {
                    'Name': 'InstanceId',
                    'Value': instance_id
                }
            ],
            StartTime=start_time,
            EndTime=end_time,
            Period=300,
            Statistics=['Average']
        )

        datapoints = response['Datapoints']

        # No data available
        if not datapoints:
            return 0

        # Calculate average CPU usage
        avg_cpu = sum(
            point['Average'] for point in datapoints
        ) / len(datapoints)

        return round(avg_cpu, 2)

    except ClientError as e:
        print(f"CloudWatch Error: {e}")
        return 0


# ---------------------------------------------------------
# Main Lambda Handler
# ---------------------------------------------------------
def lambda_handler(event=None, context=None):

    print("\n===================================")
    print(" AWS Automated Cost Optimizer ")
    print("===================================\n")

    stopped_instances = []

    try:
        # Get running EC2 instances
        response = ec2.describe_instances(
            Filters=[
                {
                    'Name': 'instance-state-name',
                    'Values': ['running']
                }
            ]
        )

        reservations = response['Reservations']

        if not reservations:
            print("No running EC2 instances found.")
            return {
                'statusCode': 200,
                'message': 'No running instances'
            }

        # Loop through instances
        for reservation in reservations:

            for instance in reservation['Instances']:

                instance_id = instance['InstanceId']

                print(f"\nChecking Instance: {instance_id}")

                # Get CPU Utilization
                cpu_usage = get_cpu_utilization(instance_id)

                print(f"Average CPU Usage: {cpu_usage}%")

                # Stop instance if CPU usage is below threshold
                if cpu_usage < 10:

                    print(f"Stopping Idle Instance: {instance_id}")

                    ec2.stop_instances(
                        InstanceIds=[instance_id]
                    )

                    stopped_instances.append(instance_id)

                else:
                    print("Instance is active. No action taken.")

        print("\n===================================")
        print(" Cost Optimization Completed ")
        print("===================================\n")

        return {
            'statusCode': 200,
            'stopped_instances': stopped_instances
        }

    except NoCredentialsError:
        print("AWS credentials not found.")

    except ClientError as e:
        print(f"AWS Client Error: {e}")

    except Exception as e:
        print(f"Unexpected Error: {e}")


# ---------------------------------------------------------
# Run Locally
# ---------------------------------------------------------
if __name__ == "__main__":

    result = lambda_handler()

    print("\nFinal Result:")
    print(result)
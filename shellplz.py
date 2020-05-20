import boto3
import collections
import datetime
import json
from instances import instances_map
import time
import subprocess
import sys

price_filter = "0.01" # 1c defaul
OPTIONS = sys.argv[1:]

session = boto3.session.Session()
client = boto3.client('ec2')


keys = client.describe_key_pairs()['KeyPairs']
s = "Which key pair would you like to use. Press enter for [0]"
for i in range(len(keys)):
    s += "\n\t [" + str(i) + "]\t" + keys[i]['KeyName']

key = keys[int(input(s + "\n:") or '0')]

resp = client.describe_spot_price_history(
    MaxResults=1000,
    InstanceTypes=list(instances_map.keys()),
    StartTime=(datetime.datetime.now() - datetime.timedelta(hours=2)).isoformat(),
    ProductDescriptions=['Linux/UNIX (Amazon VPC)'])

prices = resp["SpotPriceHistory"]
prices = list(filter(lambda k: k['SpotPrice'] < price_filter, prices))
for p in prices:
    p['factor'] = instances_map[p['InstanceType']]

prices = sorted(prices, key=lambda k: k['factor'])

last_common_types = list(filter(lambda k: k['InstanceType'] == prices[-1]['InstanceType'], prices))
chosen_instance = last_common_types[0]

print(chosen_instance['SpotPrice'] + " \t " + chosen_instance['InstanceType'] + "\t" + chosen_instance['AvailabilityZone'] + "\t" + str(chosen_instance['factor']))


images = client.describe_images(Owners=["amazon"], Filters=[
                                                                {
                                                                    "Name": "root-device-type",
                                                                    "Values" : ["ebs"]
                                                                },
                                                                {
                                                                    "Name": "architecture",
                                                                    "Values" : ["x86_64"]
                                                                },
                                                                {
                                                                    "Name": "state",
                                                                    "Values" : ["available"]
                                                                },
                                                                {
                                                                    "Name": "name",
                                                                    "Values" : ["amzn2-ami-hvm-2.0.2020*"]
                                                                },
                                                            ])

images = images['Images']
images = sorted(images, key=lambda k: k['CreationDate'])
chosen_image = images[-1]

try:
    response = client.request_spot_instances(
        DryRun=False,
        SpotPrice=price_filter,
        # BlockDurationMinutes= 60, # This would work i think, but set duration instances are more expensive but guaranteed 
        # ClientToken='string',
        InstanceCount=1,
        Type='one-time',
        LaunchSpecification={
            'ImageId': chosen_image['ImageId'],
            'KeyName': key['KeyName'],
            'InstanceType': chosen_instance['InstanceType'],
            'Placement': {
                'AvailabilityZone': chosen_instance['AvailabilityZone'],
            },
            # 'SecurityGroups': [''], # Going to use default - maybe change to an option?
            # 'EbsOptimized': True, # Default?
            # 'Monitoring': { 'Enabled': True  }, # Default?
            # 'SecurityGroupIds': ['default', 'ssh','others?']
        }
    )
except:
    pass

counter = 0
print("Spot request successfully created. Finding Spot instance")
while counter < 60:
    spots = client.describe_spot_instance_requests()['SpotInstanceRequests']

    # Filter out the instances that were not created by this spot request
    # Strickly speaking you could have others here - but a) unlikely, b) same key so we can still connect and use it
    spots = list(filter(lambda k: k['State'] == 'active'
                            and k['LaunchSpecification']['InstanceType'] == chosen_instance['InstanceType']
                            and chosen_image['ImageId'] == k['LaunchSpecification']['ImageId']
                            and key['KeyName'] == k['LaunchSpecification']['KeyName'], spots))
    if len(spots) < 1:
        print("Waiting up to 60 seconds")
        time.sleep(1)
        counter += 1
    else:
        break

if len(spots) == 0:
    raise Exception("Couldnt find your spot instance. here is it described:\n\n" + str(client.describe_spot_instance_requests()))
if len(spots) > 1:
    print("Found multiple spot instances - have you run this multiple times? Guess i'll just try and grab one?")
    spots = sorted(spots, key=lambda i: i['CreateTime'], reverse=True)  # Sort spots so newest is first
    
spot = spots[0]
instance_created_id = spot['InstanceId']

instance_created = client.describe_instances(InstanceIds=[instance_created_id])['Reservations'][0]['Instances'][0]
public_ip = instance_created['PublicIpAddress']

cmd = ["ssh", "ec2-user@" + public_ip] + OPTIONS
print("Command running is:")
print(cmd)

subprocess.call(cmd)

print()
print("FINISHED WITH INSTANCE. Terminating now")
print("FINISHED WITH INSTANCE. Terminating now")
print("FINISHED WITH INSTANCE. Terminating now")
print("FINISHED WITH INSTANCE. Terminating now")
print()

client.terminate_instances(InstanceIds=[instance_created_id])

print("Goodbye")

import json
import boto3

def get_current_instances():
    instance_types = {}
    ec2_client = boto3.client('ec2', region_name='us-east-1')
    ec2_pager = ec2_client.get_paginator('describe_instance_types')
    instance_type_iterator = ec2_pager.paginate()
    for result in instance_type_iterator:
        for instance_type in result['InstanceTypes']:
            instance_types[instance_type['InstanceType']] = instance_type
    instances = {}
    pricing_client = boto3.client('pricing', region_name='us-east-1')
    product_pager = pricing_client.get_paginator('get_products')
    product_iterator = product_pager.paginate(
         ServiceCode='AmazonEC2',
         Filters=[
            # We're gonna assume N. Virginia has all the available types
            {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': 'US East (N. Virginia)'},
        ]
    )
    for product_item in product_iterator:
        for offer_string in product_item.get('PriceList'):
            offer = json.loads(offer_string)
            product = offer.get('product')
            # Check if it's an instance
            if product.get('productFamily') not in ['Compute Instance', 'Compute Instance (bare metal)', 'Dedicated Host']:
                continue
            product_attributes = product.get('attributes')
            instance_type = product_attributes.get('instanceType')
            if instance_type in ['u-6tb1', 'u-9tb1', 'u-12tb1']:
                # API returns the name without the .metal suffix
                instance_type = instance_type + '.metal'
            if instance_type in instances:
                continue
            new_inst = (instance_type, product_attributes, instance_types.get(instance_type))
            # Some instanced may be dedicated hosts instead
            if new_inst is not None:
                instances[instance_type] = new_inst
    print("Found data for instance types: " + ', '.join(sorted(instances.keys())))
    instances_map = {}

    instance_filter = "t1.micro | t2.nano | t2.micro | t2.small | t2.medium | t2.large | t2.xlarge | t2.2xlarge | t3.nano | t3.micro | t3.small | t3.medium | t3.large | t3.xlarge | t3.2xlarge | t3a.nano | t3a.micro | t3a.small | t3a.medium | t3a.large | t3a.xlarge | t3a.2xlarge | m1.small | m1.medium | m1.large | m1.xlarge | m3.medium | m3.large | m3.xlarge | m3.2xlarge | m4.large | m4.xlarge | m4.2xlarge | m4.4xlarge | m4.10xlarge | m4.16xlarge | m2.xlarge | m2.2xlarge | m2.4xlarge".split(" | ") # List of instance types - stolen from documentation

    for ins in instance_filter:
        cpus = int(instances[ins][1]['vcpu'])
        ramMb = instances[ins][2]['MemoryInfo']['SizeInMiB']
        factor = cpus * ramMb # FACTOR - to change the weight of RAM vs CPU - look here. To weigh CPU more, try something like this 2 * cpus + (ramMb / 1000)
        instances_map[ins] = factor

    return instances_map


# This map is calculated from the code above. Not sure if this will ever need to be updated.
# I could create this programmatically but it takes some time. Most the code was stolen from:
# https://github.com/powdahound/ec2instances.info/blob/master/ec2.py
instances_map = {
    # Ms 
    'm1.medium': 3788, 'm1.small': 1740, 'm1.xlarge': 61440,  'm1.large': 15360,
    'm2.4xlarge': 560328, 'm2.xlarge': 35020, 'm2.2xlarge': 140080,
    'm3.2xlarge': 245760, 'm3.xlarge': 61440, 'm3.large': 15360, 'm3.medium': 3840,
    'm4.large': 16384, 'm4.4xlarge': 1048576, 'm4.2xlarge': 262144, 'm4.16xlarge': 16777216, 'm4.10xlarge': 6553600, 'm4.xlarge': 65536,

    # Ts 
    't1.micro': 627,
    't2.medium': 8192, 't2.micro': 1024, 't2.large': 16384, 't2.xlarge': 65536,   't2.small': 2048, 't2.nano': 512,   't2.2xlarge': 262144,
    't3.micro': 2048, 't3.xlarge': 65536,  't3.small': 4096, 't3.2xlarge': 262144, 't3.nano': 1024, 't3.medium': 8192, 't3.large': 16384,
    't3a.large': 16384, 't3a.medium': 8192, 't3a.nano': 1024, 't3a.small': 4096, 't3a.2xlarge': 262144, 't3a.micro': 2048
}

# shellplz

## Setup
Python3. Boto3. aws credentials already setup.

## Usage
```
python shellplz.py [ssh options]
```

## Settings
Currently in shellplz.py, you can change the maximum price from 1c to something else. In case 1c is too much or not enough.
(default 1c)

## What instance do i get
I try to get the best instance you can get for 1c. It assumes RAM and CPU is equivalent in importance. The calculation code is in instances.py, but as its pretty slow to run I just dumped the output once, it just creates a map of instance name to a weight that is CPU * RAM, specifying only the normal EC2 instance types

## TODO
More options? 

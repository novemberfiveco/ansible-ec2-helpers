#!/usr/bin/env python

from __future__ import print_function
import sys
import os
from boto.kms import connect_to_region
from base64 import b64decode

def main():

    if 'KMS_ENCRYPTED_PASSWORD' not in os.environ:
        print("ERROR: The KMS_ENCRYPTED_PASSWORD environment variable is required.", file=sys.stderr)
        return
    else:
        encrypted_password = os.environ['KMS_ENCRYPTED_PASSWORD']

    if 'KMS_EC2_REGION' in os.environ:
        region = os.environ['KMS_EC2_REGION']
    elif 'EC2_REGION' in os.environ:
        region = os.environ['EC2_REGION']
    else:
        region = 'us-east-1'

    try:
        kms = connect_to_region(region)
        password = kms.decrypt(b64decode(encrypted_password))
        print(password['Plaintext'])

    except Exception, e:
        print("ERROR: Decryption failed. Do you have permission to decrypt?", file=sys.stderr)

if __name__ == '__main__':
    main()

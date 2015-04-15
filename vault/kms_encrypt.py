#!/usr/bin/env python

from __future__ import print_function
import sys
import os
import random
import string
from boto.kms.exceptions import NotFoundException
from boto.kms import connect_to_region
from base64 import b64encode


PASSWORD_LENGTH = 128


def main():

    if 'KMS_KEY_ID' not in os.environ:
        print("ERROR: The KMS_KEY_ID environment variable is required. It \
            is a unique identifier of the customer master. This can be an \
            ARN, an alias, or the Key ID.", file=sys.stderr)
        return
    else:
        key_id = os.environ['KMS_KEY_ID']

    if 'KMS_EC2_REGION' in os.environ:
        region = os.environ['KMS_EC2_REGION']
    elif 'EC2_REGION' in os.environ:
        region = os.environ['EC2_REGION']
    else:
        region = 'us-east-1'

    try:
        kms = connect_to_region(region)

        plaintext_password = ''.join(random.SystemRandom().choice(string.digits
            + string.letters + string.punctuation) for _ in xrange(PASSWORD_LENGTH))
        encryption_dict = kms.encrypt(key_id, plaintext_password)
        encrypted_password = b64encode(encryption_dict['CiphertextBlob'])

        print(plaintext_password)
        print("Encrypted password:\n" + encrypted_password, file=sys.stderr)

    except NotFoundException, e:
        print("ERROR: Key not found. Is it in {0}?".format(region), file=sys.stderr)
    except Exception, e:
       print("ERROR: Encryption failed. Do you have permission to encrypt?", file=sys.stderr)

if __name__ == '__main__':
    main()

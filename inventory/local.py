#!/usr/bin/env python

'''
EC2 localhost inventory script, to be used for ansible-pull on EC2.

Build an inventory file based only on the instance data
that is locally available in the instance.
The format is similar to the format of the official ec2.py
inventory script, but only contains the following EC2 properties:
- ec2_ami_launch_index
- ec2_architecture
- ec2_dns_name
- ec2_id
- ec2_image_id
- ec2_instance_type
- ec2_ip_address
- ec2_kernel
- ec2_private_dns_name
- ec2_private_ip_address
- ec2_public_dns_name
- ec2_ramdisk
- ec2_region
- ec2_security_group_ids
- ec2_security_group_names
- ec2_subnet_id
- ec2_vpc_id
- ec2_availability_zone

In addition, the following ansible facts are set:
- ansible_ssh_host: 127.0.0.1
- ansible_connection: local

When the instance has DescribeInstances access to the EC2 APIs for
its own instance ID, the above data is enriched with the tags.
'''

from __future__ import print_function
import sys
import re
from boto.utils import get_instance_metadata, get_instance_identity
from boto.ec2 import connect_to_region
from boto.exception import EC2ResponseError

try:
    import json
except ImportError:
    import simplejson as json


class Ec2LocalInventory:

    def __init__(self):

        self.metadata, self.identity = self._get_instance_info()
        self.tags = self._get_instance_tags()


        self.hostname = None
        self.host_vars = {}
        self.groups = []

        self._populate_hostvars()
        self._populate_groups()
        self._generate_inventory()


    def _populate_hostvars(self):
        ''' Populate self.host_vars with properties from self.metadata and
        self.identity '''

        self.hostname = "localhost" #self.metadata['public-ipv4']

        first_network_device = self.metadata['network']['interfaces']['macs'].values()[0]

        self.host_vars['ec2_ami_launch_index'] = self.metadata['ami-launch-index']
        self.host_vars['ec2_architecture'] = self.identity['document']['architecture']
        self.host_vars['ec2_dns_name'] = self.metadata['public-hostname']
        self.host_vars['ec2_id'] = self.metadata['instance-id']
        self.host_vars['ec2_image_id'] = self.identity['document']['imageId']
        self.host_vars['ec2_instance_type'] = self.metadata['instance-type']
        self.host_vars['ec2_ip_address'] = self.metadata['public-ipv4']
        self.host_vars['ec2_kernel'] = self.identity['document']['kernelId']
        self.host_vars['ec2_private_dns_name'] = self.metadata['local-hostname']
        self.host_vars['ec2_private_ip_address'] = self.metadata['local-ipv4']
        self.host_vars['ec2_public_dns_name'] = self.metadata['public-hostname']
        self.host_vars['ec2_ramdisk'] = self.identity['document']['ramdiskId']
        self.host_vars['ec2_region'] = self.identity['document']['region']
        self.host_vars['ec2_security_group_ids'] = first_network_device['security-group-ids']
        self.host_vars['ec2_security_group_names'] = self.metadata['security-groups']
        self.host_vars['ec2_subnet_id'] = first_network_device['subnet-id']
        self.host_vars['ec2_vpc_id'] = first_network_device['vpc-id']
        self.host_vars['ec2_availability_zone'] = self.identity['document']['availabilityZone']

        self.host_vars['ansible_ssh_host'] = '127.0.0.1'
        self.host_vars['ansible_connection'] = 'local'

        if self.tags is not None:
            for key, value in self.tags.iteritems():
                self.host_vars['ec2_tag_' + self._to_safe(key)] = value


    def _get_instance_tags(self):
        ''' if we have permission to query boto for more info, add tags as well '''
        try:
            c = connect_to_region(self.identity['document']['region'])
            instance = c.get_only_instances(instance_ids=[self.metadata['instance-id']])[0]
            return instance.tags

        except EC2ResponseError, e:
            if e.status == 403 or e.status == 401:
                # no permission to access instance properties, skip these vars
                return None


    def _populate_groups(self):
        ''' Populate groups from self.hostvars and self.tags '''

        self.groups.append('ec2')
        self.groups.append(self.host_vars['ec2_region'])
        self.groups.append(self.host_vars['ec2_availability_zone'])
        self.groups.append(self.host_vars['ec2_id'])
        self.groups.append('type_' + self._to_safe(self.host_vars['ec2_instance_type']))
        self.groups.append('vpc_id_' + self._to_safe(self.host_vars['ec2_vpc_id']))

        for sg in self.host_vars['ec2_security_group_names']:
            self.groups.append("security_group_" + self._to_safe(sg))

        if self.tags is not None:
            for key, value in self.tags.iteritems():
                self.groups.append('tag_' + self._to_safe(key) + "_" + self._to_safe(value))


    def _generate_inventory(self):
        ''' Generate inventory and print to stdout '''

        # initialize dict
        data = {'_meta': {'hostvars' : {}}}

        # set hostvars
        data['_meta']['hostvars'][self.hostname] = self.host_vars

        # set groups
        for group in self.groups:
            data[group] = [self.hostname]

        print (json.dumps(data, sort_keys=True, indent=2))


    def _get_instance_info(self):
        ''' Get instance metadata and identity data'''

        metadata = get_instance_metadata(timeout=1, num_retries=2)

        if metadata == {}:
            raise Exception("Should be on an EC2 instance for this inventory script to work.")

        identity = get_instance_identity(timeout=1, num_retries=2)

        return metadata, identity


    def _to_safe(self, word):
        ''' Converts 'bad' characters in a string to underscores so they can be
        used as Ansible groups '''

        return re.sub("[^A-Za-z0-9\-]", "_", word)


if __name__ == '__main__':
    try:
        Ec2LocalInventory()
    except Exception, e:
        print("ERROR: " + str(e), file=sys.stderr)

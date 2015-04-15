#!/bin/bash -x

# Script to be executed from userdata. Installs ansible, boto
# awscli.

echo "*** Install Ansible, git, boto"

# install apt-get packages for git and python-pip
sudo apt-get -y install git python-dev python-pip

# install pip packages for ansible, awscli and boto
sudo pip install ansible
sudo pip install awscli
sudo pip install boto

echo "*** Install ansible EC2 local inventory"
sudo mkdir -p /etc/ansible
sudo wget https://github.com/Appstrakt/ansible-ec2-helpers/archive/master.zip -O /tmp/ansible-ec2-helpers.zip
sudo unzip /tmp/ansible-ec2-helpers.zip -d /tmp
sudo mv /tmp/ansible-ec2-helpers-master /etc/ansible/ec2

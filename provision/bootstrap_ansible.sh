#!/bin/bash

set -e

if [ $(dpkg-query -W -f='${Status}' ansible 2>/dev/null | grep -c "ok installed") -eq 0 ];
then
    echo "Ansible is not installed. Installing..."
    apt-get update
    apt-get install -y software-properties-common
    apt-add-repository ppa:ansible/ansible
    apt-get update
    apt-get install -y --force-yes ansible
    cp /vagrant/provision/ansible.cfg /etc/ansible/ansible.cfg
else
    echo "Ansible already installed, we gucci"
fi

# Only update apt cache if it's stale (older than 1 day)
if [[ $(find "/var/lib/apt/periodic/update-success-stamp" -mtime +2 -print) ]]; then
    echo "Updating apt caches..."
    apt-get update

    echo "Upgrading packages..."
    apt-get upgrade -y --force-yes
fi


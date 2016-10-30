#! /usr/bin/env bash

set -e

echo "Installing Git..."
sudo apt-get install -y git

echo "Whitelist the GitHub sshd key so we can clone.."
if [ ! -n "$(grep "^github.com " ~/.ssh/known_hosts)" ]; then
    ssh-keyscan github.com >> ~/.ssh/known_hosts 2>/dev/null;
fi

echo "Installing Playbooks..."
if [ ! -d ~/hautomation-playbooks ]; then
    echo "No existing playbook dir found, making fresh clone..."
    cd ~/ && git clone https://github.com/geudrik/hautomation-playbooks.git;
else
    echo "Updating exisitng playbooks repo..."
    cd ~/hautomation-playbooks && git pull;
fi
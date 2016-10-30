# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure(2) do |config|
  config.vm.box = "ubuntu/trusty64"
  config.vm.box_check_update = false
  config.ssh.insert_key = false

  config.vm.provider "virtualbox" do |v|
    v.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]
    v.customize ["modifyvm", :id, "--natdnsproxy1", "on"]
    v.customize ["modifyvm", :id, "--natnet1", "192.168.223.0/24"]
  end

  config.vm.define "web" do |web|

    # Make sure you set this hostname in /etc/hosts so DNS "works"
    web.vm.hostname = "web.ha.local"

    # Set up networking
    web.vm.network "forwarded_port", guest: 443, host: 443
    web.vm.network "forwarded_port", guest: 3306, host: 3306
    web.vm.network :private_network, ip: "192.168.28.2"

    # Ensure we map our working dir 
    web.vm.synced_folder "./", "/vagrant"

    web.vm.provider "virtualbox" do |v|
      v.memory = 4096
      v.cpus = 2
    end

    web.vm.provision :shell, path: "provision/bootstrap_ansible.sh"
#    web.vm.provision :shell, path: "provision/bootstrap_playbooks.sh", privileged: false
#    web.vm.provision :shell, inline: "PYTHONUNBUFFERED=1 ansible-playbook ~/hautomation-playbooks/pb_hautomation.yml -i ~/hautomation-playbooks/inventory/hautomation_vagrant -c local", privileged: false
  end
end

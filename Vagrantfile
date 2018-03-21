# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
    config.vm.box = "ubuntu/trusty64"

    config.vm.network :forwarded_port, guest: 80, host: 8080

    # If RAM is set at 256mb, salt performance is basically none
    config.vm.provider :virtualbox do |vb|
        vb.customize ["modifyvm", :id, "--memory", "1024",
                      "--natdnshostresolver1", "on"]
    end

end

VMware fusion
=============

*This is an experimental feature, use vagrant when in doubt*

Bootstrapping
-------------

Import the VM and make sure the `publet/` directory is a shared folder.

In bash:

    $ PUBLET_USE_FUSION=true
    $ PUBLET_FUSION_IP=192.xxx.xxx.xxx
    $ fab bootstrap

In fishshell:

    $ set -x PUBLET_USE_FUSION true
    $ set -x PUBLET_FUSION_IP 192.xxx.xxx.xxx
    $ fab bootstrap

Using a pre-built fusion VM
---------------------------

Download the VM:

### precise64 - 2014-01-07

* [precise64-20140107.tar.gz][1]
* SHA: 6759040f74451791632972735d8532061371a46d
* [GPG signature][2]

[1]: https://s3.amazonaws.com/publet-vms/ubuntu-precise64-20140107.tar.gz
[2]: https://s3.amazonaws.com/publet-vms/ubuntu-precise64-20140107.tar.gz.asc

Then, import it to VMware and you're done.  Once the VM is booted, the login
screen will show you the VM's IP address.

Building a precise64 VM
-----------------------

The idea here is to build a base VM that can be used to base the Publet VM on.
We're going to try and make it as similar to the vagrant VM as possible so we
don't have to modify our application code.

Do the following as root:

* Install 12.04 from mini.iso
* Set hostname to `fusion-precise64`
* Install OpenSSH
* Set user to `vagrant` and password to `vagrant`
* `mkdir /mnt/cdrom`
* `mkdir /mnt/hgfs`
* `apt-get update`
* Install

```
    apt-get install build-essential linux-headers-`uname -r`
```

* Install vmware tools
* `mount /dev/cdrom /mnt/cdrom`
* `tar xzvf /mnt/cdrom/vmware.... -C /tmp/`
* `/tmp/vmware-tools-contrib/vmware-install.pl -d`
* `reboot`
* Add `publet` as a shared folder
* `reboot`
* Verify that `/mnt/hgfs/publet` exists
* `ln -s /mnt/hgfs/publet /vagrant`

Add the following to `/etc/network/if-up.d/show-ip`:

```
#!/bin/sh
#
# goes to /etc/network/if-up.d/show-ip

if [ "$METHOD" = loopback ]; then
    exit 0
fi

# Only run from ifup.
if [ "$MODE" != start ]; then
    exit 0
fi

IP=`hostname -I`
cat << EOF > /etc/issue
Ubuntu 14.04 \n \l
  IP Address: $IP
EOF
```

* `chmod +x /etc/network/if-up.d/show-ip`
* Remove bash history

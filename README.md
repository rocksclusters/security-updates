security-updates
================

Create a roll with security updates.  Has been tested with Rocks 6.2 

Introduction
--------------
This roll fundamentally determines which packages in a rocks-dist created 
ditribution require security updates. It then creates a roll with those
packages.

The roll was inspired by the updateinfo.xml generation process described in
http://blog.vmfarms.com/2013/12/inject-little-security-in-to-your.html.
The 3rd party components used in the roll:
 

+ This roll uses ``errata.latest.xml`` file that is maintained and updated 
  by CEFS project http://cefs.steve-meier.de/errata.latest.xml

+ a previous version used``generate_info.py`` from https://github.com/hany55/generate_updateinfo

The roll works as follows

+ The security information is downloaded into ``errata.latest.xml`` 

+ The roll creates a local rocks-dist distro

+ the information from ``errata.latest.xml`` is used to determine which RPMS in the rocks-dist distro require update

+ It then downloads the required RPMs (and their dependencies) as RPMs
for this roll. This utilizes yumdownloader

+ The roll can be added to the cluster, a new distro created and then 
``yum update`` can used to upgrade the frontend.  

During the **make roll** run a directory ``current/``  and script ``bin/downloadRPMS.sh`` are generated.
The directory contains the latest ``errata.latest.xml``.
The script lists commands used for downloading RPMs. 


Prerequisites
--------------

Binary yumdownloader must be present. If not, install with :

     # yum --enablerepo=base install yum-utils

Building the roll
-----------------

Checkout roll distribution from git repo :

     # git clone https://github.com/rocksclusters/security-updates.git  
     # cd security-updates/  
     # make roll

The roll iso image name is of the form: ``os-<rocks version>-security-updates-<date>-0.<arch>.disk1.iso``. 

Installing the roll
---------------------

To install the roll :  

     # rocks add roll os-6.2-security-updates-08_01_2015-0.x86_64.disk1.iso
     # rocks enable roll os-6.2-security-updates 
     # (cd /export/rocks/install; rocks create distro)  
     # yum clean all  
     # yum check-update  

The output of the last command should list all the RPMs that are now available from the Rocks repo.
For example:   

    # yum check-update
    Rocks-6.2                                                | 2.9 kB     00:00 ...
    Rocks-6.2/primary_db                                     | 2.1 MB     00:00 ...
    
    cairo.x86_64                         1.8.8-6.el6_6                     Rocks-6.2
    cairo-devel.x86_64                   1.8.8-6.el6_6                     Rocks-6.2
    cups.x86_64                          1:1.4.2-67.el6_6.1                Rocks-6.2
    cups-libs.x86_64                     1:1.4.2-67.el6_6.1                Rocks-6.2
    kernel.x86_64                        2.6.32-504.23.4.el6               Rocks-6.2
    kernel-devel.x86_64                  2.6.32-504.23.4.el6               Rocks-6.2
    kernel-doc.noarch                    2.6.32-504.23.4.el6               Rocks-6.2
    kernel-firmware.noarch               2.6.32-504.30.3.el6               Rocks-6.2
    kernel-headers.x86_64                2.6.32-504.23.4.el6               Rocks-6.2
    nss.x86_64                           3.19.1-3.el6_6                    Rocks-6.2
    nss-sysinit.x86_64                   3.19.1-3.el6_6                    Rocks-6.2
    nss-tools.x86_64                     3.19.1-3.el6_6                    Rocks-6.2
    nss-util.x86_64                      3.19.1-1.el6_6                    Rocks-6.2
     
To install RPMS :

     # yum update  

Or install specific updates one by one per your security requirements.

The process of building and installing a roll  can be set as a cron job on a weekly/monthly
or other basis. 

Multiple architecture packages resolution
------------------------------------------

It may happen that there is an update for multiple architectures of RPM and both
need to be installed. The roll downloads both architecutes if both are listed as security updates
and makes them available but yum will still produce a dependency resolution error and suggest a work around. 
Here is an example of how to deal with firefox dependency nss-softokn-freebl for i686 and x86_64: ::

      yum update --exclude nss-softokn-freebl.i686

The command above will install rpms for x86_64 architecture and skip i686. Verify if you really need to install 
the i686 rpm. If you do, install it with 

      yum --enablerepo=base,updates install  nss-softokn-freebl.i686

Using ``yum update --setopt=protected_multilib=false`` to intsall updates for both architectures may have an undesired
effect of installing i686 and removing x86_64 fro the same verison of RPM. 

 


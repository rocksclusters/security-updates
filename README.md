security-updates
================

Create a roll with security updates.
Has been tested on rocks 6.1 and 6.1.1

Introduction
--------------
The roll leverages updateinfo.xml generation process described in
http://blog.vmfarms.com/2013/12/inject-little-security-in-to-your.html
The 3rd party components used in the roll:
 
+ ``generate_info.py`` from https://github.com/hany55/generate_updateinfo

+ the ``generate_info.py`` uses ``errata.latest.xml`` file that is maintained and updated 
  by CEFS project http://cefs.steve-meier.de/errata.latest.xml

When the **make roll** is run for the first time, the **yum-plugin-security** RPM is installed
and the plugins are enabled in **/etc/yum.conf**.

The security information from downloaded ``errata.latest.xml`` is parsed and injected into
the repomd.xml file.  

The **yum check-update** command is run with ``--security`` flag that is now understood by yum
and listed security updates rpms (and their dependencies) are downloaded and added to the roll iso.

The subsequent roll builds will add any new security-related rpm updates to the **security-updates/RPMS/*/** 
and the latest iso will have all the rpms accummulated since the first **make roll**.

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

The roll iso image name is of the form: hostname-security-updates-date-0.arch.disk1.iso. 
For example, on the x86_64-based frontend with the FQDN of rocks-45.sdsc.edu, the roll i
build on Aug 14, 2014 will be named ``rocks-45.sdsc.edu-security-updates-2014.08.14-0.x86_64.disk1.iso``.

Installing the roll
---------------------

To install the above example roll :  

     # rocks add roll rocks-45.sdsc.edu-security-updates-2014.08.14-0.x86_64.disk1.iso  
     # rocks enable roll rocks-45.sdsc.edu-security-updates   
     # (cd /export/rocks/install; rocks create distro)  
     # yum clean all  
     # yum check-update  

The output of the last command should list all the RPMs that are now available from the Rocks repo.
To install RPMS :

     # yum update  

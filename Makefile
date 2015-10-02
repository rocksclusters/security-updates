#
# $Id$
#
# @Copyright@
# 
# 				Rocks(r)
# 		         www.rocksclusters.org
# 		         version 5.6 (Emerald Boa)
# 		         version 6.1 (Emerald Boa)
# 
# Copyright (c) 2000 - 2013 The Regents of the University of California.
# All rights reserved.	
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
# 1. Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright
# notice unmodified and in its entirety, this list of conditions and the
# following disclaimer in the documentation and/or other materials provided 
# with the distribution.
# 
# 3. All advertising and press materials, printed or electronic, mentioning
# features or use of this software must display the following acknowledgement: 
# 
# 	"This product includes software developed by the Rocks(r)
# 	Cluster Group at the San Diego Supercomputer Center at the
# 	University of California, San Diego and its contributors."
# 
# 4. Except as permitted for the purposes of acknowledgment in paragraph 3,
# neither the name or logo of this software nor the names of its
# authors may be used to endorse or promote products derived from this
# software without specific prior written permission.  The name of the
# software includes the following terms, and any derivatives thereof:
# "Rocks", "Rocks Clusters", and "Avalanche Installer".  For licensing of 
# the associated name, interested parties should contact Technology 
# Transfer & Intellectual Property Services, University of California, 
# San Diego, 9500 Gilman Drive, Mail Code 0910, La Jolla, CA 92093-0910, 
# Ph: (858) 534-5815, FAX: (858) 534-7345, E-MAIL:invent@ucsd.edu
# 
# THIS SOFTWARE IS PROVIDED BY THE REGENTS AND CONTRIBUTORS ``AS IS''
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE REGENTS OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN
# IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# 
# @Copyright@
#

-include $(ROLLSROOT)/etc/Rolls.mk
include Rolls.mk

## Packages that are forced to latest update
ENABLED-REPOS = base,updates
FORCE-PKGS = 	glibc \
		glibc-common \
		glibc-devel \
		glibc-headers \
		glibc-static 

FILELIST = force-pkgs-list

.PHONY: $(FORCE-PKGS) force-pkgs


default: roll

## Rules to create a local rocks distro and yum repository so
## that the main repo is unchanged

yum.dirs:
	- mkdir -p $(CACHEDIR) $(LOGDIR) $(REPOSDIR)

yum.repos: yum.dirs
	(cd /etc/$(REPOSDIR); tar cf - *repo) | ( cd $(REPOSDIR); tar xvfBp -)	

yum.conf: yum.conf.in
	sed -e "s#%PWD%#`pwd`#" yum.conf.in > yum.conf

local.repo: yum.repos
	sed -i 's#baseurl.*#baseurl=file://$(PWD)/rocks-dist/x86_64#' yum.repos.d/rocks-local.repo

rocks-dist:
	rocks create distro
 
pretar:: yum.conf local.repo rocks-dist 
	./bin/security-updates.py 
	/bin/bash ./bin/downloadRPMS.sh
	make force-pkgs

##  Get packages that are forced to the latest version, irrespective of security. Usually this is 
# just glibc as other software updates sometimes depend on latest glibc, not just the latest security update

$(FORCE-PKGS):
	yumdownloader --resolve --urls --disablerepo='*' --enablerepo=$(ENABLED-REPOS) --destdir=RPMS $(FORCE-PKGS)  | grep ^http >  $(FILELIST)
	(cd RPMS/$(ARCH); wget -nc -i ../../$(FILELIST))

force-pkgs: $(FORCE-PKGS)

roll::

clean-dist: 
	-rm -rf rocks-dist
clean::
	rm -f $(ROLLNAME)*.iso
	rm -f timestamp
	rm -f *spec.mk
	rm -f nodes/security-updates.xml
	rm -f _os _arch
	rm -f bin/downloadRPMS.sh
	rm -rf current/
	rm -f yum.conf 
	rm -rf $(CACHEDIR) $(LOGDIR) $(REPOSDIR) var
	rm -f $(FILELIST)

veryclean: clean-dist clean

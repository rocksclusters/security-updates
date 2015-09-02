#!/opt/rocks/bin/python 
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

import os
import platform
import sys
import stat
import string
import subprocess
import errno
import rocks.app
import parseit2
import re

class App(rocks.app.Application):
	def __init__(self, argv):
		rocks.app.Application.__init__(self, argv)
		self.getopt.l.extend([ ('list=', ''), ])
		
		self.setDefaults()

	def setDefaults(self):
		""" set default variables. Most are related to roll dir structure"""
		self.rpms = []
		self.downloads = []

		self.thisdir 	     = os.getcwd()
		self.repodata        = os.path.join(self.thisdir,"rocks-dist/x86_64/repodata")
		self.repopkgs        = os.path.join(self.thisdir,"rocks-dist/x86_64/RedHat/RPMS")
		self.yumrepos        = os.path.join(self.thisdir,"/var/lib/yum/repos/")

		self.rolldir         = os.getcwd() 
		self.updatesdir      = os.path.join(self.thisdir,"current")
		self.download_script = os.path.join(self.thisdir,"bin/downloadRPMS.sh") 
		self.nodexml         = os.path.join(self.thisdir,"nodes/security-updates.xml")

		self.errata_src      = "http://cefs.steve-meier.de/errata.latest.xml"
		self.errata_wget     = "/usr/bin/wget -q -N -P%s %s" % (self.updatesdir, self.errata_src)
		self.errata          = "%s/errata.latest.xml" % self.updatesdir

		self.arch = platform.machine()
		self.setRolldirs()



	def writeFile(self, fname, content):
		"""write content into a file  fname"""
		try: 
			fout = open(fname , 'w')
			fout.write(content)
		except IOError:
			print "Error writing %s file" % fname
		else:
			fout.close()
			print "Wrote %s" % fname

	def writeScript2(self,pkgs):
		""" write script for rpms download"""
		#if os.path.isfile(self.download_script):
		#	os.remove(self.download_script)
		ydl = "/usr/bin/yumdownloader"
		ydconf = "--config=yum.conf --destdir %s/RPMS/x86_64 " + \
			"--enablerepo=base,updates %s"  
		ydresolv ="--resolve" 
		
		content = "#!/bin/bash\n\n"
		# remove .rpm from the end of each package name
		yumdl = map(lambda x: x.replace(".rpm",""), pkgs)
                
		# download with resolution non-kernel packages
		resolvePkgs = filter(lambda x: re.match("^kernel-.*",x) is None, yumdl)
		ycmd = " ".join((ydl,ydresolv,ydconf))
		resolvePkgs = map(lambda x: ycmd % \
			(self.rolldir,x), resolvePkgs)
		content += "\n".join(resolvePkgs)

		# download without resolution kernel- packages
		noResolvePkgs = filter(lambda x: re.match("^kernel-.*",x) is not None, yumdl)
		ycmd = " ".join((ydl, ydconf))
		noResolvePkgs = map(lambda x: ycmd % \
                        (self.rolldir,x), noResolvePkgs)
		content += "\n".join(noResolvePkgs)

		# if noResolvePkgs has non-zero length download dracut-kernel
		if len(noResolvePkgs) > 0:
			dracutPkgs = ["dracut","dracut-kernel"]
			ycmd = " ".join((ydl,ydresolv,ydconf))
			dracutPkgs = map(lambda x: ycmd % \
                                (self.rolldir,x), dracutPkgs)
			content += "\n".join(dracutPkgs)
			
		self.writeFile(self.download_script, content)

	def getErrata(self):
		""" download security errata xml file """
		self.createDir(self.updatesdir)
		print "Fetching errata.latest.xml"
		info, err = subprocess.Popen(self.errata_wget, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
		if err:
			print "Error in getErrata(): %s" % err

	def setRolldirs(self):
		""" create dir structure under roll's RPMS/"""
		for name in [self.arch, "noarch"]:	
			archdir = "%s/RPMS/%s" % (self.rolldir, name)	
			self.createDir(archdir)
		self.createDir("%s/nodes" % self.rolldir)
						
	def createDir(self, path):
		""" create directory """
		if  not os.path.exists(path):
			try:
				os.makedirs(path)
			except OSError as exception:
				if exception.errno != errno.EEXIST:
					raise
	def run(self):
		self.getErrata()
		# process the errata updates
		pkgs = parseit2.pkglist(self.repopkgs)
		upd = parseit2.pkgsecurity(self.errata)
		updlist=parseit2.updlist(pkgs,upd)
		self.writeScript2(updlist)

app = App(sys.argv)             
app.run()
#app.runTest()


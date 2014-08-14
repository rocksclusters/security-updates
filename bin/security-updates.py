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

import xml.sax.saxutils
import os
import sys
import stat
import string
import subprocess
import glob
import platform
import errno
import rocks.app

class App(rocks.app.Application):
	def __init__(self, argv):
		rocks.app.Application.__init__(self, argv)

		self.getopt.l.extend([
			('list=', ''),
                        ])
		
		self.setDefaults()

	def setDefaults(self):
		self.rpms = []
		self.downloads = []

		self.plugin          = "yum-plugin-security"
		self.plugin_enabled  = "plugins=1"
		self.repodata        = "/state/partition1/rocks/install/rocks-dist/x86_64/repodata"
		self.yumrepos        = "/var/lib/yum/repos/"

		self.rolldir         = "/state/partition1/site-roll/rocks/src/roll/security-updates"
		self.updatesdir      = "%s/current" % self.rolldir
		self.update_script   = "%s/bin/generate_updateinfo.py" % self.rolldir
		self.download_script = "%s/bin/downloadRPMS.sh" % self.rolldir
		self.nodexml         = "%s/nodes/security-updates.xml" % self.rolldir

		self.errata_src      = "http://cefs.steve-meier.de/errata.latest.xml"
		self.errata_wget     = "/usr/bin/wget -q -N -P%s %s" % (self.updatesdir, self.errata_src)
		self.errata          = "%s/errata.latest.xml" % self.updatesdir

		self.releases        = ["updateinfo-6", "updateinfo-other"]

		self.getLocalRepos()
		self.setRolldirs()

	def writeHeader(self):
		txt = '<?xml version="1.0" standalone="no"?>\n'
		txt += '<kickstart>\n'
		txt += '<description>\n'
		txt += '</description>\n'
		txt += '<changelog>\n'
		txt += '</changelog>\n'
		return txt

	def writeFooter(self):
		txt =  '</kickstart>\n'
		return txt

	def writeXML(self):
		content = self.writeHeader()
		for rpm in self.rpms:
			content += '<package>%s</package>\n' % rpm
		content += self.writeFooter()

		fout = open(self.nodexml , 'w')
		fout.write(content)
		fout.close()

	def writeScript(self):
		#if os.path.isfile(self.download_script):
		#	os.remove(self.download_script)
		
		content = "#!/bin/bash\n\n"
		content += "\n".join(self.downloads)

		fout = open(self.download_script, 'w')
		fout.write(content)
		fout.close()

	def checkSecPlugin(self):
		# check if yum security plugin is installed
		cmd = "/bin/rpm -qa | /bin/grep %s" % self.plugin
		info, err = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
		lines = info.split("\n")
		lines = lines[:-1]
		if len(lines) == 1:
			if string.find(lines[0], self.plugin) != 0:
				self.installYumPlugin()
		else:
			self.installYumPlugin()
			
		# check if yum security plugin is enabled
		cmd = "/bin/grep %s /etc/yum.conf" % self.plugin_enabled
		info, err = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
		lines = info.split("\n")
		lines = lines[:-1]
		if len(lines) == 1:
			if string.find(lines[0], self.plugin_enabled) != 0:
				self.enableYumPlugin()
		else:
			self.enableYumPlugin()

	def installYumPlugin(self):
		# install yum security plugin
		print "Installing %s" %self.plugin
		cmd = "/usr/bin/yum --enablerepo=base install %s" % self.plugin
		info, err = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
		if err:
			print "Error in installYumPlugin(): %s" % err

	def enableYumPlugin(self):
		# enable yum security plugin
		print "Enabling %s" %self.plugin
		cmd = "/bin/echo %s >> /etc/yum.conf" % self.plugin_enabled
		info, err = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
		if err:
			print "Error in enableYumPlugin(): %s" % err
			
	def getErrata(self):
		self.createDir(self.updatesdir)
		print "Fetching errata.latest.xml"
		info, err = subprocess.Popen(self.errata_wget, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
		if err:
			print "Error in getErrata(): %s" % err

	def generateUpdateInfo(self):
		cmd = "%s %s" % (self.update_script, self.errata)
		info, err = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()

	def getLocalRepos(self):
		# create list of repos to look for updates 
		self.arch = platform.machine()
		reposDir = glob.glob("%s/%s/*/" % (self.yumrepos, self.arch) )[0]
		self.reposlist = os.listdir(reposDir)
		self.reposlist = [ x for x in self.reposlist if x.find("Rocks") < 0 ] 

	def setRolldirs(self):
		for name in [self.arch, "noarch"]:	
			archdir = "%s/RPMS/%s" % (self.rolldir, name)	
			self.createDir(archdir)
		self.createDir("%s/nodes" % self.rolldir)
						
	def createDir(self, path):
		if  not os.path.exists(path):
			try:
				os.makedirs(path)
			except OSError as exception:
				if exception.errno != errno.EEXIST:
					raise

	def getSecurityUpdates(self):
		reposString = ",".join(self.reposlist)
		for release in self.releases:
			self.modifyRepodata(release)
			content = self.listUpdates(reposString)
			fname = "%s/%s.out" % (self.updatesdir, release)
			try:
				fout = open(fname , 'w')
				fout.write(content)
				fout.close()
			except IOError :
				continue
			self.parsePackageNames(content)


	def parsePackageNames(self, content):
		lines = content.split("\n")
		
		count = 0
		startline = 0
		endline = len(lines)
		for l in lines:
			if l.find("needed for security") > 0:
				startline = count + 1
			if l.find("Obsoleting") > -1 :
				endline = count
			count += 1

		lines = lines[startline:endline]
		for l in lines:
			if len(l) < 1: continue
			rpmarch,version,repo = l.split()
			rpm,arch = rpmarch.split(".")
			if rpm in self.rpms: 
				continue
			self.rpms.append(rpm)
			self.downloads.append("/usr/bin/yumdownloader --resolve --destdir %s/RPMS/%s --enablerepo %s %s" 
						% (self.rolldir, arch, repo, rpmarch))
		
	def testFunc(self):
		reposString = ",".join(self.reposlist)
		for release in self.releases:
			fname = "%s/%s.out" % (self.updatesdir, release)
			try:
				fin = open(fname , 'r')
				content = fin.read()
				fin.close()
			except IOError :
				continue 
			self.parsePackageNames(content)

	def modifyRepodata(self, release):
		cmd = "/usr/bin/modifyrepo %s/%s/updateinfo.xml %s" % (self.updatesdir, release, self.repodata)
		info, err = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
		cmd = "/usr/bin/yum  clean all"
		info, err = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()

	def listUpdates(self, repolist):
		cmd = "/usr/bin/yum --security --enablerepo=%s check-update" % repolist
		info, err = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
		return info

	def getSuffix(self,filename):
		suffix_dict = {'py':'/opt/rocks/bin/python','csh':'/bin/tcsh','pl':'/usr/bin/perl'}
		suffix = filename.split('.')[-1]
		try:
			interpreter = suffix_dict[suffix]
		except KeyError:
			interpreter = ""

		return interpreter
		
	def run(self):
		self.checkSecPlugin()
		self.getErrata()
		self.generateUpdateInfo()
		self.getSecurityUpdates()
		self.writeXML()
		self.writeScript()

	def runTest(self):
		self.testFunc()

app = App(sys.argv)             
app.run()
#app.runTest()


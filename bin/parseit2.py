#! /usr/bin/env python
## find packages that are security updates.  This works on a distribution, not installed 
## updates
import xml.etree.ElementTree as ET
import os
import rpm


### From: <https://git.fedorahosted.org/cgit/rpmdevtools.git/tree/rpmdev-vercmp>
# from yum and rpmlint, with less internal assumptions, and returning
# empty strings instead of None for missing bits
def stringToEVR(verstring):
    if verstring in (None, ''):
        return ('', '', '')
    i = verstring.find(':')
    if i == -1:
        epoch = ''
    else:
        epoch = verstring[:i]
    i += 1
    j = verstring.find('-', i)
    if j == -1:
        version = verstring[i:]
        release = ''
    else:
        version = verstring[i:j]
        release = verstring[j+1:]
    return (epoch, version, release)
### END FROM ########################

def pkgrep(pkg):
	"""Package representation. Take an RPM filename and split it name, version, suffix """
	try:
		name,version,suffix=pkg.rsplit("-",2)
	except:
		return(pkg,"","")
	rel=suffix.rsplit(".",2)[0]
	suffix=".".join(suffix.rsplit(".",2)[-2:])
	version="-".join((version,rel))
	return (name,stringToEVR(version),suffix)	

def pkgname(rep):
	"""return package name given a representation built by pkgrep"""
	name,ver,suf = rep
	if len(ver[0]) == 0:
		ver = ver[1:]
	ver="-".join(ver)
	name="-".join((name,ver))
	return ".".join((name,suf))

def pkgsecurity(filename):
	"""Given an xml doc of security related updates, packages that are security updates"""
	try:
		tree = ET.parse(filename)
	except:
		None
	root = tree.getroot()
	pkgs=[]
	for advisory in root:
		if advisory.attrib.has_key('type') and advisory.attrib['type'] == 'Security Advisory' and advisory.attrib.has_key('severity') and advisory.attrib['severity'] in ['Critical', 'Important'] :
			doBreak = False
			for st in advisory.findall('os_release'):
				if st.text == '6':	
					doBreak=True
			if (doBreak):
				# print advisory.tag, advisory.attrib['product']
				for st in advisory.findall('packages'):
					ptype=pkgrep(st.text) 
					pkgs.append(ptype)		
	return pkgs

def pkglist(dirname):
	"""Given a directory of RPMS, return packages in comparable form to pkgsecurity"""
	pkgs=[]
	for (dirpath,dirnames,filenames) in os.walk(dirname):
		pkgs.extend(map(lambda x: pkgrep(x),filenames))
	return(pkgs)

def updlist(pkgs,updates,filterlist=("alt","el7","el5")):
	"""Find updates that are newer than pkgs. Filter out unwanteds"""
	# create a list of package name and suffixes (no version-release) for filtering
	purepkgs = map(lambda x: (x[0],x[2]),pkgs)
	cand = filter(lambda x: len(x[1]) == 3, updates)
	for mstr in filterlist: 
		cand = filter(lambda x: x[1][2].find(mstr) < 0, cand)

	# now look only for candidates that would update downloaded packages
	cand = filter(lambda x: (x[0],x[2]) in purepkgs, cand)
	dlpkgs = []

	# find the packages that are newer
	for upd in cand:
		indistro = filter( lambda x: x[0] == upd[0] and x[2] == upd[2],pkgs)
		for pk in indistro:
			print pk,upd
			if rpm.labelCompare(upd[1],pk[1]) > 0:
				dlpkgs.append(upd)
	return map(lambda x: pkgname(x),dlpkgs)

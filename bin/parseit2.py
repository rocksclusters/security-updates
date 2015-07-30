#! /usr/bin/env python
import xml.etree.ElementTree as ET
import os


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
	try:
		name,version,suffix=pkg.rsplit("-",2)
	except:
		return(pkg,"","")
	rel=suffix.rsplit(".",2)[0]
	suffix=".".join(suffix.rsplit(".",2)[-2:])
	print rel,suffix
	version="-".join((version,rel))
	return (name,stringToEVR(version),suffix)	



def pkgsecurity(filename):
	try:
		tree = ET.parse(filename)
	except:
		None
	root = tree.getroot()
	pkgs=[]
	for advisory in root:
		if advisory.attrib.has_key('type') and advisory.attrib['type'] == 'Security Advisory':
			doBreak = False
			for st in advisory.findall('os_release'):
				if st.text == '6':	
					doBreak=True
			if (doBreak):
				print advisory.tag, advisory.attrib['product']
				for st in advisory.findall('packages'):
					ptype=pkgrep(st.text) 
					pkgs.append(ptype)		
	return pkgs

def pkglist(dirname):
	pkgs=[]
	for (dirpath,dirnames,filenames) in os.walk(dirname):
		pkgs.extend(map(lambda x: pkgrep(x),filenames))
	return(pkgs)


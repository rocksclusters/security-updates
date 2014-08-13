#!/usr/bin/env python
#    Copyright (C) 2013  Kristian K. [http://vmfarms.com] [kris@vmfarms.com]
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see [http://www.gnu.org/licenses/].

import re
import xml.sax.handler
import sys
import os
import errno
import logging

##### START CONFIGURATION HEADER #####
# Set to true if you want to use Sentry
SENTRY = False
# Sentry logging
if SENTRY:
    from raven.handlers.logging import SentryHandler
    from raven import Client
    from raven.conf import setup_logging
    sentry_client = Client('INSERT_SENTRY_DSN_HERE')
    handler = SentryHandler(sentry_client)
    setup_logging(handler)

# What releases would you like to track. 'other' is mandatory
RELEASES = ['6','other']

# What severity levels do we want to include
SEVERITY = ['Critical', 'Important']

# Who is this from?
UPDATE_FROM = "you@your_domain.com"

# Directory prefix to build the files under.
BUILD_PREFIX = "/state/partition1/site-roll/rocks/src/roll/security-updates/current"

##### END CONFIGURATION HEADER #####

def xml2obj(src):
    """
    A simple function to converts XML data into native Python object.
    """

    non_id_char = re.compile('[^_0-9a-zA-Z]')
    def _name_mangle(name):
        return non_id_char.sub('_', name)

    class DataNode(object):
        def __init__(self):
            self._attrs = {}    # XML attributes and child elements
            self.data = None    # child text data
        def __len__(self):
            # treat single element as a list of 1
            return 1
        def __getitem__(self, key):
            if isinstance(key, basestring):
                return self._attrs.get(key,None)
            else:
                return [self][key]
        def __contains__(self, name):
            return self._attrs.has_key(name)
        def __nonzero__(self):
            return bool(self._attrs or self.data)
        def __getattr__(self, name):
            if name.startswith('__'):
                # need to do this for Python special methods???
                raise AttributeError(name)
            return self._attrs.get(name,None)
        def _add_xml_attr(self, name, value):
            if name in self._attrs:
                # multiple attribute of the same name are represented by a list
                children = self._attrs[name]
                if not isinstance(children, list):
                    children = [children]
                    self._attrs[name] = children
                children.append(value)
            else:
                self._attrs[name] = value
        def __str__(self):
            return self.data or ''
        def __repr__(self):
            items = sorted(self._attrs.items())
            if self.data:
                items.append(('data', self.data))
            return u'{%s}' % ', '.join([u'%s:%s' % (k,repr(v)) for k,v in items])

    class TreeBuilder(xml.sax.handler.ContentHandler):
        def __init__(self):
            self.stack = []
            self.root = DataNode()
            self.current = self.root
            self.text_parts = []
        def startElement(self, name, attrs):
            self.stack.append((self.current, self.text_parts))
            self.current = DataNode()
            self.text_parts = []
            # xml attributes --> python attributes
            for k, v in attrs.items():
                self.current._add_xml_attr(_name_mangle(k), v)
        def endElement(self, name):
            text = ''.join(self.text_parts).strip()
            if text:
                self.current.data = text
            if self.current._attrs:
                obj = self.current
            else:
                # a text only node is simply represented by the string
                obj = text or ''
            self.current, self.text_parts = self.stack.pop()
            self.current._add_xml_attr(_name_mangle(name), obj)
        def characters(self, content):
            self.text_parts.append(content)

    builder = TreeBuilder()
    if isinstance(src,basestring):
        xml.sax.parseString(src, builder)
    else:
        xml.sax.parse(src, builder)
    return builder.root._attrs.values()[0]

def build_updateinfo(src):
    rel_fd = {}
    for rel_num in RELEASES:
        try:
            os.mkdir("%s/updateinfo-%s" % (BUILD_PREFIX, rel_num))
        except OSError, e:
            # Directories that exist are fine
            if e.errno != errno.EEXIST:
                logging.debug("Directory %s/updateinfo-%s already exists." % (BUILD_PREFIX, rel_num))
        try:
            rel_fd[rel_num] = open("%s/updateinfo-%s/updateinfo.xml" % (BUILD_PREFIX, rel_num), 'w')
        except Exception, e:
            logging.error("Error opening file: %s" % e)

        rel_fd[rel_num].write('<updates>\n')
            
    pkg_parts = re.compile("(?P<name>.*)-(?P<version>.*)-(?P<release>.*)\.(?P<arch>.*).rpm")
    pkg_os_rel = re.compile(".*\.el(?P<os_rel>[0-9]*).*")
    for i in src._attrs.keys():
        # Sometimes it's a dict, sometimes it's a list, where we just take the first element.
        if type(src._attrs[i]) is list:
            sec_dict = src._attrs[i][0]
        else:
            sec_dict = src._attrs[i]

        # Ignore this entry
        if "meta" == i:
            continue

        # Is this a properly formatted CEBA/CESA entry?
        if 'type' not in sec_dict:
            logging.warning("Improperly formatted CEBA/CESA entry: %s" % (i))
            continue

        # Is this a security advisory?
        if sec_dict._attrs['type'] != 'Security Advisory':
            continue

        # What severity levels are we including? 
        if 'severity' not in sec_dict._attrs:
            continue
        if sec_dict._attrs['severity'] not in SEVERITY:
            continue

        # More than one OS release? Generate multiple entries
        if sec_dict.os_release == None:
            sec_dict.os_release = ""
        if isinstance(sec_dict.os_release, basestring):
            releases = [sec_dict.os_release]
        else:
            releases = sec_dict.os_release
            
        for release in releases:
            # If we can't pull the release, then we infer it from the package names
            p_release = release
            packages = []
            for pkg in sec_dict.packages:
                package = None
                # Parse the package name
                try:
                    pkg_match = pkg_parts.match(pkg)
                    package = pkg_match.groupdict()
                    packages.append(package)
                except Exception, err:
                    logging.warning("Package name '%s' couldn't be matched against regex" % (pkg))
                    continue
                # Extract the el release from here, otherwise it has no discernable release
                if not p_release:
                    if ".el" in package['release']:
                        try:
                            p_rel_match = pkg_os_rel.match(package['release'])
                            p_release = p_rel_match.groupdict()['os_rel']
                        except Exception, err:
                            logging.warning("Package release '%s' couldn't be matched against regex" % (package['release']))
                            continue
        
            # Place unidentifiable or uninteresting releases in an alternate updateinfo.xml
            if p_release not in RELEASES:
                p_release = "other"

            rel_fd[p_release].write('  <update from="%s" status="stable" type="security" version="1.4">\n' % UPDATE_FROM)
            rel_fd[p_release].write("    <id>%s</id>\n" % i)
            rel_fd[p_release].write("    <title>%s</title>\n" % sec_dict._attrs['synopsis'])
            rel_fd[p_release].write("    <release>CentOS %s</release>\n" % p_release)
            rel_fd[p_release].write("    <issued date=\"%s\" />\n" % sec_dict._attrs['issue_date'])
            rel_fd[p_release].write("    <references>\n")
            for ref in sec_dict._attrs['references'].split():
                rel_fd[p_release].write("      <reference href=\"%s\"/>\n" % ref)
            rel_fd[p_release].write("    </references>\n")
            rel_fd[p_release].write("    <description>%s</description>\n" % sec_dict._attrs['synopsis'])
            rel_fd[p_release].write("    <pkglist>\n")
            rel_fd[p_release].write("      <collection short=\"EL-%s\">\n" % p_release)
            rel_fd[p_release].write("        <name>CentOS %s</name>\n" % p_release)
            for pkg in packages:
                rel_fd[p_release].write("        <package arch=\"%s\" epoch=\"%s\" name=\"%s\" release=\"%s\" src=\"%s\" version=\"%s\">\n" % (pkg['arch'], "0", pkg['name'], pkg['release'], "", pkg['version']))
                rel_fd[p_release].write("          <filename>%s</filename>\n" % (pkg))
                rel_fd[p_release].write("        </package>\n")
            rel_fd[p_release].write("      </collection>\n")
            rel_fd[p_release].write("    </pkglist>\n")
            rel_fd[p_release].write("  </update>\n")
    for rel_num in RELEASES:
        rel_fd[rel_num].write("</updates>\n")
        rel_fd[rel_num].close()

if __name__ == "__main__":
    try:
        if len(sys.argv) < 2:
            sys.exit("Usage: %s <path to errata.xml>\n")
        errata_file = open(sys.argv[1], 'r')
        errata_xml = errata_file.read()
        errata = xml2obj(errata_xml)
        build_updateinfo(errata)
    except Exception, e:
        logging.critical("Caught exception: %s" % e, exc_info=True)

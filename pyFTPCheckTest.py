#!/usr/bin/env python

# 
# Copyright (C) 2003-2007  Robey Pointer <robeypointer@gmail.com>
#
# This file is part of paramiko.
#
# Paramiko is free software; you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation; either version 2.1 of the License, or (at your option)
# any later version.
#
# Paramiko is distrubuted in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Paramiko; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA.

# based on code provided by raymond mosteller (thanks!)

import base64
import getpass
import os
import socket
import sys
import traceback
import filecmp
from filecmp import dircmp

import paramiko

def traverse(sftp):
    list = sftp.listdir('.')
    #print list
    for file in list:
        try:
			sftp.chdir(file)
			dlist = sftp.listdir('.')
			print dlist
			try:
				traverse(sftp)
			except:
				print file+" is not a dir"	
        except:
			print "error"
					

def print_diff_files(dcmp):
    for name in dcmp.diff_files:
        print "diff_file %s found in %s and %s" % (name, dcmp.left, dcmp.right)
    for sub_dcmp in dcmp.subdirs.values():
        print_diff_files(sub_dcmp)
        
	
			

# setup logging
paramiko.util.log_to_file('demo_sftp.log')

# get hostname
username = ''
if len(sys.argv) > 1:
	hostname = sys.argv[1]
	if hostname.find('@') >= 0:
		username, hostname = hostname.split('@')
else:
	hostname = raw_input('Hostname: ')
if len(hostname) == 0:
	print '*** Hostname required.'
	sys.exit(1)
port = 22
if hostname.find(':') >= 0:
	hostname, portstr = hostname.split(':')
	port = int(portstr)


# get username
if username == '':
	default_username = getpass.getuser()
	username = raw_input('Username [%s]: ' % default_username)
	if len(username) == 0:
		username = default_username
password = getpass.getpass('Password for %s@%s: ' % (username, hostname))


# get host key, if we know one
hostkeytype = None
hostkey = None
try:
	host_keys = paramiko.util.load_host_keys(os.path.expanduser('~/.ssh/known_hosts'))
except IOError:
	try:
		# try ~/ssh/ too, because windows can't have a folder named ~/.ssh/
		host_keys = paramiko.util.load_host_keys(os.path.expanduser('~/ssh/known_hosts'))
	except IOError:
		print '*** Unable to open host keys file'
		host_keys = {}

if host_keys.has_key(hostname):
	hostkeytype = host_keys[hostname].keys()[0]
	hostkey = host_keys[hostname][hostkeytype]
	print 'Using host key of type %s' % hostkeytype
#LastDirList = null

# now, connect and use paramiko Transport to negotiate SSH2 across the connection
try:
    t = paramiko.Transport((hostname, port))
    t.connect(username=username, password=password, hostkey=hostkey)
    sftp = paramiko.SFTPClient.from_transport(t)

	# dirlist on remote host
#	dirlist = sftp.listdir('.')
#	print "Dirlist:", dirlist
#	sftp.chdir(dirlist[0])
#	dirlist = sftp.listdir('.')
#	print "Dirlist:", dirlist
#	sftp.chdir(dirlist[0])
#	dirlist = sftp.listdir('.')
#	print "Dirlist:", dirlist#
#	for dir in Dirlist:
#'''
    dlist = sftp.listdir('.')
    dcmp = dircmp(dlist[0], dlist[0]) 
    print_diff_files(dcmp)     
	#print traverse(sftp)	

	#t.close()


except Exception, e:
	print '*** Caught exception: %s: %s' % (e.__class__, e)
	traceback.print_exc()
	try:
		t.close()
	except:
		pass
	sys.exit(1)

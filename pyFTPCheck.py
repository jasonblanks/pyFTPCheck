#!/usr/bin/python

# Copyright (C) 2013  Jason Blanks <jason.blanks@gmail.com>
#
#This is a a simple script to check for new files on a sftp, can be set to a cron job for times reports.
# based on code provided by raymond mosteller and Robey Pointer (thanks!)

import base64
import getpass
import os
import socket
import sys
import traceback
import paramiko
import smtplib

files = []
username = 'username'
hostname = "ftp.site.com"
port = 22
password = "password"

gmail_user = "user@gmail.com"
gmail_pwd = "password"
FROM = 'user@gmail.com'
TO = ['user@gmail.com'] #must be a list
SUBJECT = "SFTP Hourly update"

def traverseSFTP(sftp, cwd, files):
    list = sftp.listdir(cwd)
    sftp.chdir(cwd)
    c = sftp.getcwd()
    #print "c is "+c
    for f in list:
        try:
            sftp.chdir(f)
            lwd = cwd
            cwd = sftp.getcwd()
            #files.append(f)
            #print "f is "+f
            ##print "cwd is "+sftp.getcwd()
            dlist = sftp.listdir(cwd)
            for d in dlist:
                x = cwd+"\/"+d
                files.append(x)
            ##print dlist
            try:
                #print f
                traverseSFTP(sftp, cwd, files)
                sftp.chdir('..')
            except:
                continue
                #print f+" is not a dir"	
                #sftp.chdir('lwd')
        except:
            #sftp.chdir('..')
            #count = count + 1
            #print count
            #print "error"
            pass
    return cwd
    

def send_email(files,gmail_user,gmail_pwd,FROM,TO,SUBJECT):
            def printl(files):
                f = "New Files in the past Hour:\n\n"
                for l in files:
                        f = f+"\n"+l+"\n"
                return f
            
            TEXT = printl(files)

            # Prepare actual message
            message = """\From: %s\nTo: %s\nSubject: %s\n\n%s
            """ % (FROM, ", ".join(TO), SUBJECT, TEXT)
            try:
                #server = smtplib.SMTP(SERVER) 
                server = smtplib.SMTP("smtp.gmail.com", 587) #or port 465 doesn't seem to work!
                server.ehlo()
                server.starttls()
                server.login(gmail_user, gmail_pwd)
                server.sendmail(FROM, TO, message)
                #server.quit()
                server.close()
                print 'successfully sent the mail'
            except:
                print "failed to send mail"
# setup logging
#paramiko.util.log_to_file('demo_sftp.log')


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

# now, connect and use paramiko Transport to negotiate SSH2 across the connection
try:
    t = paramiko.Transport((hostname, port))
    t.connect(username=username, password=password, hostkey=hostkey)
    sftp = paramiko.SFTPClient.from_transport(t)
#t.close()


except Exception, e:
    print '*** Caught exception: %s: %s' % (e.__class__, e)
    traceback.print_exc()
    try:
        t.close()
    except:
        pass
    sys.exit(1)


#Read in last hourly snapshot list
try:
    with open('hourly.txt') as HourlySnapshotFile:
        snapshot = HourlySnapshotFile.read().splitlines()
except:
    pass

cwd = '.'
#cwd = sftp.chdir('.')
traverseSFTP(sftp, cwd, files)
HourlySnapshotFile = open('hourly.txt', 'w')
for l in files:
    HourlySnapshotFile.write(l+"\n")


new_files = []
for element in files:
    if element not in snapshot:
        new_files.append(element)
print new_files

send_email(new_files,gmail_user,gmail_pwd,FROM,TO,SUBJECT)

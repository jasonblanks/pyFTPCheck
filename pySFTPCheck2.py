#!/usr/bin/python

# Copyright (C) 2013 Jason Blanks <jason.blanks@gmail.com>
#
#This is a a simple script to check for new files on a sftp, can be set to a cron job for times reports.
# based on code provided by raymond mosteller and Robey Pointer (thanks!)
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import base64, argparse, getpass, os, socket, sys, traceback, paramiko, smtplib, sqlite3


#DB vars
db_filename = 'new_sftp.db'
schema_filename = 'new_sftp.sql'
db_is_new = not os.path.exists(db_filename)

current_SFTP_files = []
snapshot = []
new_files = []

##SFTP VARS
cwd = '.'
username = 'Jason'
hostnames = [("sftp.address.com", "Project1"), ("sftp2.address.com", "Project2")]

port = 22
password = "password"
sftp = None

#Email Vars
gmail_user = "email@email.com"
gmail_pwd = "password"
FROM = 'email@email.com'
TO = []
SUBJECT = None
#TO = ['email@email.com'] #must be a list



def GET_CURRENT_SFTP_FILES(sftp, cwd, current_SFTP_files):
	list = sftp.listdir(cwd)
	sftp.chdir(cwd)
	c = sftp.getcwd()

	for f in list:
		try:
			sftp.chdir(f)
			lwd = cwd
			cwd = sftp.getcwd()
			dlist = sftp.listdir(cwd)
			for d in dlist:
				x = cwd+"/"+d
				mtime = datetime.fromtimestamp(sftp.stat(x).st_atime)
				size = sftp.stat(x).st_size
				sftpfile = (x,mtime,size)
				current_SFTP_files.append(sftpfile)

			try:
				GET_CURRENT_SFTP_FILES(sftp, cwd, current_SFTP_files)
				sftp.chdir('..')
			except:
				continue
		except:
			pass
	#return cwd
	

def send_email(gmail_user,gmail_pwd,FROM,TO,SUBJECT,hostnames,args):


			from_date = datetime.now() - timedelta(hours=int(args.time))
			#from_date = datetime.now() - timedelta(hours=24)
			#from_date = from_date.fromtimestamp(from_date)
			from_date.isoformat()
			db_filename = 'new_sftp.db'
			filelist = []
			matter_list = []
			new_files = []
			#for hostname in hostnames:
			def printl(db_filename):
				with sqlite3.connect(db_filename) as conn:
					cursor = conn.cursor()
					#for hostname in hostnames:
					cursor.execute("select distinct project from "+hostname[1])
					
					for row in cursor.fetchall():
						#print row[0]
						matter_list.append(row[0])
					
					cursor.execute("select id, filename, project, fullpath, upload_date, filesize from "+hostname[1])

				for row in cursor.fetchall():
					id, filename, project, fullpath, upload_date, filesize = row
					filelist.append(fullpath)
					#print '%2s {%s} %-20s [%-8s] (%s)' % (id, filename, project, fullpath, upload_date)
					
					#print str(upload_date)
					#print from_date.isoformat()
					#print str(upload_date) - from_date.isoformat()				
					#if str(upload_date) > from_date.isoformat():
					dateObj = datetime.strptime(str(upload_date),"%Y-%m-%d %X")
					if dateObj > from_date:
						print dateObj
						print row
						new_files.append(row)
				if len(new_files) >= 1:
					f = """<img src=\"http://www.abbl.lu/sites/abbl.lu/files/wysiwyg/logo_KPMG.gif\"><br>
							<table>
							"""
				else:
					f = """<img src=\"http://www.abbl.lu/sites/abbl.lu/files/wysiwyg/logo_KPMG.gif\"><br>
							<table><tr>No new files in the past 24 hours</tr>
							"""
					sys.exit()
						#<table height=\"20\">
				
				for u in matter_list:
					temp = []
					for k in new_files:
						if k[2] == u:
							temp.append([k[1],k[5],k[4]])
					if temp:
						f = f + """	<tr style=\"\"><td valign=center style=\"background-color:#FFFFFF;text-align:left;line-height:125%;font-size:25px;\"><b>"""+str(u)+"""</b></td></tr>
									<tr style=\"max-height:5px\"><td valign=top style=\"max-height:5px;background-color:#CCCCCC;text-align:left;text-decoration:underline;\">Filename</td><td valign=top style=\"background-color:#CCCCCC;text-align:left;text-decoration:underline;\">FileSize</td><td valign=top style=\"background-color:#CCCCCC;text-align:left;text-decoration:underline;\">Upload Date</td></tr>
								"""
						b = 0
						for i in temp:
							if b % 2:
								b = b + 1
								f = f +"<tr style=\"max-height:5px\"><td valign=top style=\"max-height:5px;background-color:#CCCCFF;text-align:left;\">"+str(i[0])+"</td><td valign=top style=\"background-color:#CCCCFF;text-align:left;\">"+str(i[1])+"</td><td valign=top style=\"background-color:#CCCCFF;text-align:left;\">"+str(i[2])+"</td></tr>"
							else:
								b = b + 1
								f = f +"<tr style=\"max-height:5px\"><td valign=top style=\"max-height:5px;background-color:#9999ff;text-align:left;\">"+str(i[0])+"</td><td valign=top style=\"background-color:#9999ff;text-align:left;\">"+str(i[1])+"</td><td valign=top style=\"background-color:#9999ff;text-align:left;\">"+str(i[2])+"</td></tr>"
				return f
			
			TEXT = printl(db_filename)
			part1 = MIMEText(TEXT, 'html')
			
			#print files

			# Prepare actual message
			
			if args.time == "24":
				SUBJECT = "Project1 & Project2 SFTP Daily update"
				#TO = ['jblanks@kpmg.com'] #must be a list
				TO = ['email@email.com','email@email.com'] #must be a list
			elif args.time == "1":
				SUBJECT = "Project1 & Project2 SFTP Hourly update"
				TO = ['jblanks@kpmg.com'] #must be a list
				#TO = ['email@email.com','email@email.com'] #must be a list
			else:
				SUBJECT = "Project1 & Project2 SFTP update"
				TO = ['email@email.com'] #must be a list
				print args.time
				
			message = """"\From: %s\nTo: %s\nSubject: %s\n\n%s""" % (FROM, ", ".join(TO), SUBJECT, TEXT)
			
			msg = MIMEMultipart('alternative')
			msg['Subject'] = SUBJECT
			msg['From'] = FROM
			msg['To'] = ', '.join(TO)
			msg.attach(part1)
			#msg['To'] = TO
			if TEXT != None:
				try:
					#server = smtplib.SMTP(SERVER)
					server = smtplib.SMTP("smtp.address.com", 25) #or port 465 doesn't seem to work!
					server.ehlo()
					#server.starttls()
					#server.login(gmail_user)
					#server.login(gmail_user, gmail_pwd)
					#server.sendmail(FROM, TO, message)
					server.sendmail(FROM, TO, msg.as_string())
					#server.quit()
					server.close()
					print 'successfully sent the mail'
				except (RuntimeError, TypeError, NameError):
					#print "failed to send mail"
					pass

# get host key, if we know one

def create_sftp_connection(sftp,hostname,password,port,cwd):
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
	return sftp

parser = argparse.ArgumentParser(description='Check FTPs and report updates')
parser.add_argument('--time', default=24, help='sum the integers (default: 24 hours)')
args = parser.parse_args()
if args.time:
    print args.time

for hostname in hostnames:	
	sftp = create_sftp_connection(sftp,hostname[0],password,port,cwd)
	#Read in all past files from db
	GET_CURRENT_SFTP_FILES(sftp, cwd, current_SFTP_files)

#Connect to db, create db if does not exist

	with sqlite3.connect(db_filename) as conn:
		if db_is_new:
			print 'Creating schema'
			with open(schema_filename, 'rt') as f:
				schema = f.read()
			conn.executescript(schema)
		else:
			print 'Database exists, assume schema does, too.'
			cursor = conn.cursor()
			sql = "select fullpath from "+hostname[1]+""
			cursor.execute(sql)
			
			#Create file history snapshot from db using fullpath names
			for row in cursor.fetchall():
				snapshot.append(row[0])


	for element in current_SFTP_files:
		if element[0] not in snapshot:
			element_split = element[0].split("/")
			if len(element_split) <= 3:
				continue
			else:
				project = element_split[3]
				
				if len(element_split) == 5:
					filename = element_split[(len(element_split) - 1)]
				else:
					filename = "null"
				flag = "current"
				fullpath = element[0]
				upload_date = element[1]
				filesize = element[2]
				
				db_is_new = not os.path.exists(db_filename)
				with sqlite3.connect(db_filename) as conn:
					if db_is_new:
						print 'Creating schema'
						with open(schema_filename, 'rt') as f:
							schema = f.read()
						conn.executescript(schema)

						print 'Inserting initial data'
					if not db_is_new:
						#sql = "insert into "+hostname[1]+" ('filename','project','fullpath','upload_date','flag','filesize') values ("+str(filename)+","+str(project)+","+str(fullpath)+","+str(upload_date)+","+str(flag)+","+str(filesize)+")"
						conn.execute("insert into "+hostname[1]+" ('filename','project','fullpath','upload_date','flag','filesize') values (?,?,?,?,?,?)",(filename,project,fullpath,upload_date,flag,filesize))
						#onn.execute(sql)
						
				#new_files.append(element)

send_email(gmail_user,gmail_pwd,FROM,TO,SUBJECT,hostnames,args)

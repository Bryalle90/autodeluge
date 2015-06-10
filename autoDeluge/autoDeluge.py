import os, sys, time, textwrap
import errno
import shutil
import binascii
import subprocess
import ConfigParser

from Lib.deluge_client.client import DelugeRPCClient
from Lib.notifications.pushbullet import PushBullet
from Lib.notifications.email import Email
from Lib.unrar2 import RarFile

HEADER = textwrap.dedent(
'''
              _        _    _ _______ _____   _____ 
             | |      | |  | |__   __|  __ \ / ____|
   __ _ _   _| |_ ___ | |__| |  | |  | |__) | |     
  / _` | | | | __/ _ \|  __  |  | |  |  ___/| |     
 | (_| | |_| | || (_) | |  | |  | |  | |    | |____ 
  \__,_|\__,_|\__\___/|_|  |_|  |_|  |_|     \_____|
'''
)
NAME = 'Bryan Allen'
VERSION = '1.2'

class Torrent():
	def __init__(self, id=None, name=None, path=None):
		self.id = id
		self.name = name
		self.path = path
		self.files = []
		self.label = None
		
class Client():
	def __init__(self, host, port, username, password):
		self.host = host
		self.port = port
		self.username = username
		self.password = password
		self.client = DelugeRPCClient(host, port, username, password)
		self.client.connect()
		self.connected = self.client.connected
		
	def get_all_info(self, torrent=None):
		if torrent:
			return self.client.call('core.get_torrent_status', torrent.id, [])
		return self.client.call('core.get_torrents_status')
		
	def get_files(self, torrent):
		files = self.client.call('core.get_torrent_status', torrent.id, ['files'])['files']
		for file in files:
			f = os.path.normpath(os.path.join(torrent.path, file['path']))
			torrent.files.append(f)
	
	def get_label(self, torrent):
		torrent.label = self.client.call('core.get_torrent_status', torrent.id, ['label'])['label']
		
	def get_enabled_plugins(self):
		return self.client.call('core.get_enabled_plugins')
		
	def get_method_list(self):
		return self.client.call('daemon.get_method_list')
		
	def pause(self, torrent=None):
		if torrent:
			self.client.call('core.pause_torrent', [torrent.id])
		else:
			self.client.call('core.pause_all_torrents')
			
	def unpause(self, torrent=None):
		if torrent:
			self.client.call('core.resume_torrent', [torrent.id])
		else:
			self.client.call('core.resume_all_torrents')
		
class Processor():
		
	def readConfig(self, path, fname):
		file = os.path.normpath(os.path.join(path, fname) + '.cfg')
		config = ConfigParser.ConfigParser()
		config.read(file)
		return config
		
	def getExtensions(self, keep_ext, extensions):
		ext_list = []
		if keep_ext['video']:
			ext_list.extend(extensions['video'])
		if keep_ext['subs']:
			ext_list.extend(extensions['subs'])
		if keep_ext['readme']:
			ext_list.extend(extensions['readme'])
		return tuple(ext_list)
		
	def isSubstring(self, list, searchstring):
		for item in list:
			if item in searchstring:
				return True
		return False

	def isMainRar(self, f):
		with open(f, "rb") as this_file:
			byte = this_file.read(12)

		spanned = binascii.hexlify(byte[10])
		main = binascii.hexlify(byte[11])

		if (spanned == "01" or spanned == "11") and main == "01":	# main rar archive in a set of archives
			return True
		elif spanned == "00" and main == "00":	# single rar
			return True
		return False
		
	def filterFiles(self, files, extensions, ignore):
		keep = []
		for file in files:
			if file.endswith(extensions):
				if not (self.isSubstring(ignore, os.path.split(file)[1])):
					keep.append(file)
		return keep
		
	def filterArchives(self, files, extensions, ignore):
		keep = []
		for file in files:
			if file.endswith(extensions):
				if not (self.isSubstring(ignore, os.path.split(file)[1])):
					if file.endswith('.rar'):
						try:
							if self.isMainRar(file):
								keep.append(file)
						except Exception, e:
							print 'File does not exist:', file, '\n'
					else:
						keep.append(file)
		return keep
		
	def extract(self, file, destination):
		file_name = os.path.split(file)[1]
		print 'attempting to extract:', file_name
		try:
			rar_handle = RarFile(file)
			for rar_file in rar_handle.infolist():
				sub_path = os.path.join(destination, rar_file.filename)
				if rar_file.isdir and not os.path.exists(sub_path):
					os.makedirs(sub_path)
				else:
					rar_handle.extract(condition=[rar_file.index], path=destination, withSubpath=True, overwrite=False)
			del rar_handle
			print '\tSuccess!'
		except Exception, e:
			print '\tFailed:', str(e)
			
	def createDir(self, directory):
		if not os.path.isdir(directory):
			try:
				os.makedirs(directory)
			except OSError as e:
				if e.errno != errno.EEXIST:
					raise
				pass
				
	def copyFile(self, source_file, destination):
		if os.path.isfile(source_file):
			file_name = os.path.split(source_file)[1]
			destination_file = os.path.normpath(os.path.join(destination, file_name))
			print 'attempting to copy:', file_name
			if not os.path.isfile(destination_file):
				try:
					shutil.copy2(source_file, destination_file)
					print '\tSuccess!'
				except Exception, e:
					print '\tFailed:',str(e)
			else:
				print '\t', file_name, 'already exists in destination - skipping'
			return destination_file
			
	def cleanDir(self, path, desiredExtensions, ignore):
		# remove any file that doesn't have a desired extension or has an ignore word in the file name
		for dirName, subdirList, fileList in os.walk(path):
			for file in fileList:
				if not file.endswith(desiredExtensions) or self.isSubstring(ignore, file):
					try:
						print 'removing file:', file
						os.remove(os.path.normpath(os.path.join(dirName, file)))
					except Exception, e:
						print 'could not delete ' + file + ': ' + str(e)
						
		# remove any folder that is completely empty
		for dirName, subdirList, fileList in os.walk(path, topdown=False):
			if len(fileList) == 0 and len(subdirList) == 0:
				print 'removing directory:', dirName
				os.rmdir(dirName)
		
class Notifier():
	def __init__(self, pushbullet, email):
		self.pushbullet = pushbullet
		self.email = email
		self.pb_info = None
		self.email_info = None
		self.notification = None
		
	def send(self):
		if self.pushbullet:
			self.sendPush()
		if self.email:
			self.sendEmail()
		
	def sendPush(self):
		pushbullet = PushBullet(self.pb_info['token'])
		subject = self.notification['subject']
		body = 'title: ' + self.notification['title'] + '\n' +\
				'label: ' + self.notification['label'] + '\n' +\
				'date: ' + self.notification['date'] + '\n' +\
				'time: ' + self.notification['time']
		
		print 'pushing notification via pushbullet'
		if not self.pb_info['devices'] == ['']:
			devices = pushbullet.getDevices()
			for device in devices:
				if device['pushable'] and device['nickname'] in devices:
					pushbullet.pushNote(device['iden'], subject, body)
		else:
			pushbullet.pushNote('', subject, body)
	
	def sendEmail(self):
		em = Email()
		
		header = 'Content-type: text/html\n' + 'Subject:' + self.notification['subject'] + '\n'
		body = """
		<html xmlns="http://www.w3.org/1999/xhtml">
			<head>
				<style type="text/css">
				table.gridtable {
					font-family: verdana,arial,sans-serif;
					font-size:11px;
					color:#333333;
					border-width: 0px;
					border-color: green;
					border-collapse: collapse;
				}
				table.gridtable th {
					border-width: 0x;
					padding: 8px;
					border-style: solid;
					border-color: green;
					background-color: green;
					align: left;
				}
				table.gridtable td {
					border-width: 0px;
					padding: 8px;
					border-style: solid;
					border-color: white;
					background-color: #ffffff;
				}
				</style>
			</head>
			<body bgcolor="black">
				<table class="gridtable">
					<colgroup>
						<col/>
						<col/>
					</colgroup>
					<tr><td>Title:</td><td>%s</td></tr>
					<tr><td>Label:</td><td>%s</td></tr>
					<tr><td>Date:</td><td>%s</td></tr>
					<tr><td>Time:</td><td>%s</td></tr>
				</table>
			</body>
		</html>
		""" % (self.notification['title'], self.notification['label'], self.notification['date'], self.notification['time'])
		msg = header + body
		
		print 'sending email notification'
		em.send_email(self.email_info, msg)
	
class FileBot():
	def __init__(self, fb, ow):
		self.fb = fb
		self.conflict = 'override' if ow else 'skip'
		
	def rename_move(self, info):
		fb_args = [
			self.fb,
			'-rename', info['from'],
			'--output', info['to'],
			'--db', info['database'],
			'--format', info['format'],
			'--lang', info['language'],
			'--conflict', self.conflict,
			'-non-strict', '-r'
		]
		
		if info['query']:
			fb_args.append('--q')
			fb_args.append(info['query'])
			
		try:
			subprocess.call(fb_args)
		except Exception, e:
			print 'could not rename file:', str(e)
			
	def extract(self, source, dest):
		fb_args = [
			self.fb,
			'-extract', source,
			'--output', dest,
			'--conflict', self.conflict
		]
		
		try:
			subprocess.call(fb_args)
		except Exception, e:
			print 'could not extract files:', str(e)
	
if __name__ == "__main__":
	print HEADER
	print 'by:', NAME
	print 'version:', VERSION
	print '-----------------------------------------------------'
	
	root = os.path.dirname(os.path.realpath(sys.argv[0]))
	if len(sys.argv) > 1:
		torrent = Torrent(sys.argv[1], sys.argv[2], sys.argv[3])
	
	labels_folder = os.path.normpath(os.path.join(root, 'labels'))
	processor = Processor()
	
	config = processor.readConfig(root, 'config')
	
	filebot = Filebot(os.path.normpath(os.path.join(root, 'Lib', 'FileBot_4.6', 'filebot')), config.getboolean('General', 'overwrite'))
	notifier = Notifier(config.getboolean('PushBullet', 'enable'), config.getboolean('Email', 'enable'))
	notifier.email_info = {
		'server': config.get("Email", "SMTPServer"),
		'port': config.get("Email", "SMTPPort"),
		'user': config.get("Email", "username"),
		'pass': config.get("Email", "password"),
		'to': config.get("Email", "emailTo").split('|')
	}
	notifier.pb_info = {
		'token': config.get("PushBullet", "token"),
		'devices': config.get("PushBullet", "devices").split('|')
	}
	
	host = str(config.get('Client','host'))
	port = config.getint('Client','port')
	username = config.get('Client','username')
	password = config.get('Client','password')
	deluge = Client(host, port, username, password)
	
	if deluge.connected:
	
		deluge.get_files(torrent)
		deluge.get_label(torrent)
	
		if torrent.label == '':
			print 'label is blank - skipping'
		elif os.path.isfile(os.path.join(labels_folder, torrent.label) + '.cfg'):
			# get what extensions we want
			extensions = {
				'video': config.get('Extensions','video').split('|'),
				'subs': config.get('Extensions','subtitle').split('|'),
				'readme': config.get('Extensions','readme').split('|'),
			}
			label_config = processor.readConfig(labels_folder, torrent.label)
			keep_ext = {
				'video': label_config.getboolean('Type', 'video'),
				'subs': label_config.getboolean('Type', 'subtitle'),
				'readme': label_config.getboolean('Type', 'readme')
			}
			desiredExtensions = processor.getExtensions(keep_ext, extensions)
			print 'looking for files with these extensions:', desiredExtensions, '\n'
			
			# get words we don't want
			wordsToIgnore = config.get("Extensions","ignore").split('|')
			print 'ignoring files with these words in the file name:', wordsToIgnore, '\n'
			
			# get what files to keep from torrent folder
			filesToCopy = processor.filterFiles(torrent.files, desiredExtensions, wordsToIgnore)
			
			# get archives to extract from
			archiveExtensions = tuple(config.get("Extensions","archive").split('|'))
			filesToExtract = processor.filterArchives(torrent.files, archiveExtensions, wordsToIgnore)
			
			# copy/extract files to processing directory
			processingDir = os.path.normpath(os.path.join(config.get("General","path"), torrent.name))
			processor.createDir(processingDir)
			print 'copying and extracting files to:\n\t', processingDir
			print '--'
			filebot.extract(torrent, processingDir)
			for file in filesToCopy:
				processor.copyFile(file, processingDir)
			print '--\n'
			
			# clean out unwanted files from processing dir
			print 'cleaning unwanted files in:\n\t', processingDir
			print '--'
			processor.cleanDir(processingDir, desiredExtensions, wordsToIgnore)
			print '--\n'
			
			# use filebot to rename files and move to final directory
			print 'sending file info to filebot\n'
			rename_info = {
				'from': processingDir,
				'to': label_config.get('Filebot','path'),
				'database': label_config.get('Filebot','database'),
				'format': label_config.get('Filebot','format'),
				'query': label_config.get('Filebot', 'query'),
				'language': label_config.get('Filebot','language'),
			}
			filebot.rename_move(rename_info)
			
			# send notifications
			notifier.notification = {
				'subject': 'autoDeluge Notification',
				'title': torrent.name,
				'label': torrent.label,
				'date': time.strftime("%m/%d/%Y"),
				'time': time.strftime("%I:%M:%S%p")
			}
			notifier.send()
		else:
			print 'could not find label config file'
			

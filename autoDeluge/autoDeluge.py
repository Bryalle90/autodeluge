import ConfigParser
import pprint
import textwrap
import sys, os
import logging
import shutil
import errno
import binascii
import math
import time

from Lib.mylib.filebot import AutoDelugeFilebot as Filebot
from Lib.mylib.notify import AutoDelugeNotify as Notify
from Lib.mylib.deluge_client_wrapper import AutoDelugeWrapper as Client

from Lib.mylib.s_zip import Archive

HEADER = textwrap.dedent(
'''
             _       ______     _                  
            | |      |  _  \   | |                 
  __ _ _   _| |_ ___ | | | |___| |_   _  __ _  ___ 
 / _` | | | | __/ _ \| | | / _ \ | | | |/ _` |/ _ \\
| (_| | |_| | || (_) | |/ /  __/ | |_| | (_| |  __/
 \__,_|\__,_|\__\___/|___/ \___|_|\__,_|\__, |\___|
                                         __/ |     
                                        |____/      
'''
)
NAME = 'Bryan Allen'
VERSION = '2.0'
		
class AutoDeluge:
	def read_config(self, f):
		config = ConfigParser.ConfigParser()
		config.read(f)
		return config
		
	def get_extensions(self, keep_ext, extensions):
		ext_list = []
		if keep_ext['video']:
			ext_list.extend(extensions['video'])
		if keep_ext['subs']:
			ext_list.extend(extensions['subs'])
		if keep_ext['readme']:
			ext_list.extend(extensions['readme'])
		return ext_list
		
	def is_substring(self, keys, searchstring):
		for key in keys:
			if key in searchstring:
				return True
		return False

	def is_mainRar(self, f):
		with open(f, "rb") as rar_file:
			byte = rar_file.read(12)

		spanned = binascii.hexlify(byte[10])
		main = binascii.hexlify(byte[11])

		if (spanned == "01" or spanned == "11") and main == "01":	# main rar archive in a set of archives
			return True
		elif spanned == "00" and main == "00":	# single rar
			return True
		return False
		
	def filter_files(self, files, extensions, ignore_list):
		keep = []
		for f in files:
			if f.endswith(tuple(extensions)) and not self.is_substring(ignore_list, os.path.split(f)[1]):
				keep.append(f)
		return keep
		
	def filter_archives(self, files, extensions, ignore_list):
		keep = []
		for f in files:
			if f.endswith(tuple(extensions)) and not self.is_substring(ignore_list, os.path.split(f)[1]):
				if f.endswith('.rar'):
					try:
						if self.is_mainRar(f):
							keep.append(f)
					except Exception, e:
						logger.warning('File does not exist: '+str(e))
				else:
					keep.append(f)
		return keep

	def unpack(self, program, f, dest):
		file_name = os.path.split(f)[1]
		logger.debug('attempting to extract: '+file_name)
		try:
			archive = Archive(program, f)
			return archive.extract_all(dest)
		except Exception, e:
			logger.warn(str(e))
		return None # unknown error


			
	def create_dir(self, directory):
		if not os.path.isdir(directory):
			logger.debug('Attempting to create directory: '+directory)
			try:
				os.makedirs(directory)
				logger.debug('Success!')
			except OSError as e:
				if e.errno != errno.EEXIST:
					raise
				pass
		else:
			logger.debug('Directory already exists')
				
	def copy_file(self, source_file, destination):
		if os.path.isfile(source_file):
			file_name = os.path.split(source_file)[1]
			destination_file = os.path.normpath(os.path.join(destination, file_name))
			logger.debug('attempting to copy: '+file_name)
			if not os.path.isfile(destination_file):
				try:
					shutil.copy2(source_file, destination_file)
					logger.debug('Success!')
				except Exception, e:
					logger.warning('Failed: '+str(e))
					return None
			else:
				logger.debug(file_name+' already exists in destination - skipping')
			return destination_file
		return None
			
	def clean_dir(self, path, desiredExtensions, ignore_list):
		# remove any file that doesn't have a desired extension or has an ignore word in the file name
		for dirName, subdirList, fileList in os.walk(path):
			for f in fileList:
				if not f.endswith(tuple(desiredExtensions)) or self.is_substring(ignore_list, f):
					logger.debug('Removing file: '+f)
					try:
						os.remove(os.path.normpath(os.path.join(dirName, f)))
					except Exception, e:
						logger.warning('Error: could not delete file: '+f)
						logger.warning('MSG: '+str(e))
						
		# remove any folder that is completely empty
		for dirName, subdirList, fileList in os.walk(path, topdown=False):
			if len(fileList) == 0 and len(subdirList) == 0:
				logger.debug('removing directory: '+dirName)
				os.rmdir(dirName)
		
	def convert_size(self, amt, start, end, kilo=1024.0):
		bits_per_byte = 8.0
		pre = {'B':0, 'K':1, 'M':2, 'G':3, 'T':4, 'P':5}

		# convert amt to bytes
		if start[-1] == 'b':
			amt = amt / bits_per_byte

		amt_bytes = amt * math.pow(kilo, pre[start[0]]) if start[0] in pre else amt

		# convert to end
		amt_end = amt_bytes / math.pow(kilo, pre[end[0]]) if end[0] in pre else amt_bytes

		if end[-1] == 'b':
			amt_end = amt_end * bits_per_byte

		return amt_end

	def round_dec(self, val, places):
		return int((val * math.pow(10.0, places)) + 0.5) / 100.0

if __name__ == "__main__":
	print '-----------------------------------------------------'
	print HEADER
	print 'version:', VERSION
	print 'by:', NAME
	print '-----------------------------------------------------'

	# allow time for deluge to place files
	time.sleep(5)

	# get arguments
	if len(sys.argv) < 2:
		sys.exit('Error: invalid argument amount')
	root = os.path.dirname(os.path.realpath(sys.argv[0]))
	tor_hash = sys.argv[1]

	# set up logger
	logger = logging.getLogger('autoDeluge')
	logger.setLevel(logging.DEBUG)
	# console handler
	ch = logging.StreamHandler()
	ch.setLevel(logging.INFO)
	# file handler
	log = os.path.normpath(os.path.join(root, 'log') + '.txt')
	fh = logging.FileHandler(log)
	fh.setLevel(logging.DEBUG)
	# add formatter
	formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
	ch.setFormatter(formatter)
	fh.setFormatter(formatter)
	# add handlers
	logger.addHandler(ch)
	logger.addHandler(fh)

	logger.info('Start log')

	# create torrent dict
	torrent = {}
	torrent['hash'] = tor_hash
	logger.debug('Torrent hash: '+torrent['hash'])

	# create processor
	processor = AutoDeluge()

	# read main config
	logger.info('Reading config')
	config_file = os.path.normpath(os.path.join(root, 'config') + '.cfg')
	config = processor.read_config(config_file)
	logger.info('Config successfully read')
	logger.debug(config_file)

	# set up deluge
	logger.info('Connecting to Deluge')
	host = str(config.get('Client','host'))
	port = config.getint('Client','port')
	username = config.get('Client','username')
	password = config.get('Client','password')
	try:
		deluge = Client(host, port, username, password)
	except Exception, e:
		logger.critical('Error: could not connect to Deluge')
		logger.critical(str(e))
		sys.exit(-1)
	logger.info('Connected to Deluge')

	# set up filebot
	logger.info('Setting up FileBot')
	filebot_path = os.path.normpath(config.get("FileBot","path"))
	overwrite = config.getboolean('General', 'overwrite')
	filebot = Filebot(filebot_path, overwrite)
	logger.info('Filebot set up')
	logger.debug(str(filebot))

	# set up notifier
	logger.info('Setting up notifiers')
	notifiers = []
	notifications = config.items('Notifications')
	for n in notifications:
		notifiers.append(config.getboolean('Notifications', n[0]))
	notifier = Notify(notifiers)
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
	logger.info('Notifiers set up')
	logger.debug(str(notifier))

	# get torrent info from deluge
	logger.info('Getting torrent info from Deluge')
	info = ['active_time', 'all_time_download', 'files', 'label', 'name', 'save_path', 'seeding_time']
	try:
		torrent_info = deluge.get_info(torrent['hash'], info)[torrent['hash']]
	except Exception, e:
		logger.critical('Error: could not get info from deluge')
		logger.critical(str(e))
		sys.exit(-1)
	torrent.update(torrent_info)
	logger.info('Received torrent info from deluge')

	# check torrent label
	logger.info('Checking torrent label')
	if torrent['label'] == '':
		logger.critical('Error: no label returned for torrent')
		sys.exit(-1)
	logger.debug(torrent['label'])
	logger.info('Torrent label found')

	# check for label file
	logger.info('Reading label config')
	labels_folder = os.path.normpath(os.path.join(root, 'labels'))
	label_file = os.path.normpath(os.path.join(labels_folder, torrent['label']+'.cfg'))
	if not os.path.isfile(label_file):
		logger.critical('Error: no label file found for \"'+torrent['label']+'\" in '+labels_folder)
		sys.exit(-1)
	label_config = processor.read_config(label_file)
	logger.info('Label config successfully read')
	logger.debug(label_file)

	# combine save path with file paths to get full paths
	logger.info('Creating full torrent file paths')
	files = []
	for f in torrent['files']:
		full_path = os.path.normpath(os.path.join(torrent['save_path'], f['path']))
		files.append(full_path)
	torrent['files'] = files
	logger.info('Full torrent file paths created')
	for f in torrent['files']:
		logger.debug(f)

	# get known file extensions
	extensions = {
					'video': config.get('Extensions','video').split('|'),
					'subs': config.get('Extensions','subtitle').split('|'),
					'readme': config.get('Extensions','readme').split('|'),
				}

	# get wanted file extensions
	keep_ext = {
					'video': label_config.getboolean('Type', 'video'),
					'subs': label_config.getboolean('Type', 'subtitle'),
					'readme': label_config.getboolean('Type', 'readme')
				}
	copy_extensions = processor.get_extensions(keep_ext, extensions)
	archive_extensions = config.get("Extensions","archive").split('|')
	logger.debug('Extensions to copy: '+str(copy_extensions))
	logger.debug('Extensions to extract: '+str(archive_extensions))

	# get words not wanted
	ignore_list = config.get("Extensions","ignore").split('|')
	logger.debug('Ignored words: '+str(ignore_list))

	# get files to copy
	logger.info('Looking for files to copy')
	copy_files = processor.filter_files(torrent['files'], copy_extensions, ignore_list)
	for f in copy_files:
		logger.debug(f)

	# get archives to extract from
	logger.info('Looking for files to extract')
	archive_files = processor.filter_archives(torrent['files'], archive_extensions, ignore_list)
	for f in archive_files:
		logger.debug(f)

	# create processing directory
	logger.info('Creating processing directory')
	processing_dir = os.path.normpath(os.path.join(config.get("General","path"), torrent['name']))
	try:
		processor.create_dir(processing_dir)
	except Exception, e:
		logger.critical('Error: could not create processing directory ('+processing_dir+')')
		logger.critical(str(e))
		sys.exit(-1)
	logger.info('Processing directory created')
	logger.debug(processing_dir)

	# extract files to processing directory
	unpacker = os.path.normpath(config.get("7zip", "path"))
	unpack_code = {
					0:'No Error',
					1:'Warning (Non fatal error(s)). For example, one or more files were locked by some other application, so they were not compressed.',
					2:'Fatal Error',
					7:'Command line error',
					8:'Not enough memory for operation',
					255:'User stopped the process'
					}
	logger.info('Extracting files')
	for f in archive_files:
		u = processor.unpack(unpacker, f, processing_dir)
		if u == 0:
			logger.debug('Success!')
		elif u in unpack_code:
			logger.debug('Failed: '+unpack_code[u])
		else:
			logger.debug('Failed :(')

	# copy files to processing directory
	logger.info('Copying files')
	for f in copy_files:
		processor.copy_file(f, processing_dir)

	# clean out unwanted files from processing dir
	logger.info('Cleaning processing dir')
	processor.clean_dir(processing_dir, copy_extensions, ignore_list)

	# use filebot to rename files and move to final directory
	logger.info('Sending file info to filebot')
	rename_info = {
		'from': processing_dir,
		'to': label_config.get('Filebot','path'),
		'database': label_config.get('Filebot','database'),
		'format': label_config.get('Filebot','format'),
		'query': label_config.get('Filebot', 'query'),
		'language': label_config.get('Filebot','language'),
	}
	try:
		filebot.rename_move(rename_info)
	except Exception, e:
		logger.error('Could not rename files')
		logger.exception(str(e))
		sys.exit(-1)

	# calculate size and speed of torrent
	size = processor.convert_size(float(torrent['all_time_download']), 'B', config.get('Display', 'filesize'))
	size = processor.round_dec(size, 2)
	dl_time = int(torrent['active_time']) - int(torrent['seeding_time'])
	speed = processor.convert_size(float(torrent['all_time_download']), 'B', config.get('Display', 'speed')) / dl_time
	speed = processor.round_dec(speed, 2)
	size = str(size) + ' ' + config.get('Display', 'filesize')
	speed = str(speed) + ' ' + config.get('Display', 'speed') + 'ps'
	logger.info('Notificaiton data gathered')
	
	logger.info('Sending notifications')
	# send notifications
	notifier.notification = {
		'subject': 'autoDeluge Notification',
		'title': torrent['name'],
		'label': torrent['label'],
		'size': size,
		'speed': speed,
		'date': time.strftime("%m/%d/%Y"),
		'time': time.strftime("%I:%M:%S%p")
	}
	notifier.send()
	
	for n in notifier.notification:
		logger.debug(n+': '+notifier.notification[n])

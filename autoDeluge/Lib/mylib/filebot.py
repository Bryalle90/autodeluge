import os
import subprocess
import logging

logger = logging.getLogger(__name__)
class AutoDelugeFilebot:
	def __init__(self, path, ow=False):
		self.fb = os.path.normpath(os.path.join(path, 'filebot'))
		self.conflict = 'override' if ow else 'skip'

	def __str__(self):
		return self.fb

	def launchWithoutConsole(self, command, args):
		"""Launches 'command' windowless"""
		startupinfo = subprocess.STARTUPINFO()
		startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

		return subprocess.Popen([command] + args, startupinfo=startupinfo,
						stderr=subprocess.PIPE, stdout=subprocess.PIPE)
		
	def rename_move(self, info):
		fb_args = [
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
			subprocess.call([self.fb] + fb_args)
			#self.launchWithoutConsole(self.fb, fb_args)
		except Exception, e:
			logger.warning('Error: could not rename file')
			logger.warning('MSG: '+str(e))
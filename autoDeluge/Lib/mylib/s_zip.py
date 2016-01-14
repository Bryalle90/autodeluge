import subprocess
import os

class Archive:
	def __init__(self, program_path, full_file_name, overwrite=False):
		self.path = program_path
		self.program = os.path.normpath(os.path.join(self.path, '7z.exe'))
		self.file_name = full_file_name
		self.overwrite = overwrite

	def launchWithoutConsole(self, command, args):
		"""Launches 'command' windowless"""
		startupinfo = subprocess.STARTUPINFO()
		startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

	def extract_all(self, dest):
		args = [
			'x', self.file_name,
			'-o'+dest
		]
		
		if self.overwrite:
			args.append('-aoa')
		else:
			args.append('-aos')
			
		try:
			ret = subprocess.call([self.program] + args)
			#self.launchWithoutConsole(self.program, args)
		except Exception, e:
			raise e

		return ret

	def look(self):
		subprocess.call([self.program, 'l', self.file_name])
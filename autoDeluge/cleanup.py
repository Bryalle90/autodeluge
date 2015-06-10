import os, sys
import ConfigParser

class Processor():
	def readConfig(self, path, fname):
		file = os.path.normpath(os.path.join(path, fname) + '.cfg')
		config = ConfigParser.ConfigParser()
		config.read(file)
		return config
		
	def cleanDir(self, path):
		# remove any file
		for dirName, subdirList, fileList in os.walk(path):
			for file in fileList:
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
			
if __name__ == "__main__":
	root = os.path.dirname(os.path.realpath(sys.argv[0]))
	if len(sys.argv) > 1:
		name = sys.argv[2]
	else:
		name = None
	
	if name:
		proc = Processor()
	
		config = proc.readConfig(root, 'config')
		
		processingDir = os.path.realpath(os.path.join(config.get('General','path'), name))
		print processingDir
	
		if os.path.isdir(processingDir):
			proc.cleanDir(processingDir)
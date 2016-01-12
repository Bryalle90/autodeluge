from ..deluge_client.client import DelugeRPCClient

class AutoDelugeWrapper:
	def __init__(self, host, port, username, password):
		self.deluge_client = DelugeRPCClient(host, port, username, password)
		try:
			self.deluge_client.connect()
			self.connected = self.deluge_client.connected
		except Exception, e:
			raise e

	def get_info(self, torrent_hashes=[], args=[]):
		if not isinstance(torrent_hashes, list):
			torrent_hashes = [torrent_hashes]
		if not isinstance(args, list):
			args = [args]
		if torrent_hashes:
			data = {}
			for torrent_hash in torrent_hashes:
				try:
					data[torrent_hash] = self.deluge_client.call('core.get_torrent_status', torrent_hash, args)
				except Exception, e:
					pass
			return data
		return self.deluge_client.call('core.get_torrents_status', [], [])

	def get_hashes(self):
		return self.deluge_client.call('core.get_session_state')

	def pause(self, torrent_hashes):
		if not isinstance(torrent_hashes, list):
			torrent_hashes = [torrent_hashes]
		self.deluge_client.call('core.pause_torrent', torrent_hashes)

	def resume(self, torrent_hashes):
		if not isinstance(torrent_hashes, list):
			torrent_hashes = [torrent_hashes]
		self.deluge_client.call('core.resume_torrent', torrent_hashes)

if __name__ == "__main__":
	import pprint
	import time

	deluge = wrapper('127.0.0.1', 58846, 'localclient', '')

	if deluge.connected:
		print 'connected'
		print ''
		print 'torrent hashes:'
		hashes = list(deluge.get_hashes())
		for hash in hashes:
			print hash
		print ''
		print 'first torrent info:'
		info = deluge.get_info(hashes[0])
		pprint.pprint( info )

		'''
		print ''
		print 'pausing torrent 0:'
		if len(hashes) > 0:
			print info[hashes[0]]['state']
			deluge.pause(hashes[0])
			time.sleep(0.5)
			print deluge.get_info(hashes[0])[hashes[0]]['state']
		print ''
		print 'resuming torrent 0:'
		if not info[hashes[0]]['paused']:
			deluge.resume(hashes[0])
			time.sleep(0.5)
		print deluge.get_info(hashes[0])[hashes[0]]['state']
		'''

		'''
		print ''
		print 'pausing all:'
		deluge.pause(hashes)
		print ''
		print 'resuming all:'
		time.sleep(0.5)
		deluge.resume(hashes)
		'''

		print ''
		pprint.pprint(deluge.get_info(hashes[-1]))
		keys = ['all_time_download', 'active_time', 'seeding_time']
		i = deluge.get_info(hashes[-1], keys)[hashes[-1]]
		print 'avg speed:',
		print ( i['all_time_download'] / ( i['active_time'] - i['seeding_time']) ) / 1000.0,
		print 'KBps'

		print 'all tests passed'
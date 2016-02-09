from .pushbullet import PushBullet
from .email import Email
import logging

logger = logging.getLogger(__name__)

class AutoDelugeNotify:
	def __init__(self, notifications):
		self.pushbullet = notifications[0]
		self.email = notifications[1]
		self.pb_info = None
		self.email_info = None
		self.notification = None

	def __str__(self):
		string = 'Notifying:'
		if self.pushbullet:
			string += ' PushBullet'
		if self.email:
			string += ' Email'
		return string
		
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
				'size: ' + self.notification['size'] + '\n' +\
				'avg speed: ' + self.notification['speed'] + '\n' +\
				'date: ' + self.notification['date'] + '\n' +\
				'time: ' + self.notification['time'] + '\n' +\
				'status: ' + self.notification['status']
		
		logger.info('pushing notification via pushbullet')
		if not self.pb_info['devices'] == ['']:
			devices = pushbullet.getDevices()
			for device in devices:
				if device['pushable'] and device['nickname'] in self.pb_info['devices']:
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
					<tr><td>Size:</td><td>%s</td></tr>
					<tr><td>Avg Speed:</td><td>%s</td></tr>
					<tr><td>Date:</td><td>%s</td></tr>
					<tr><td>Time:</td><td>%s</td></tr>
					<tr><td>Status:</td><td>%s</td></tr>
				</table>
			</body>
		</html>
		""" % (self.notification['title'], self.notification['label'], self.notification['size'], self.notification['speed'], self.notification['date'], self.notification['time'], self.notification['status'])
		msg = header + body
		
		logger.info('sending notification via email')
		em.send_email(self.email_info, msg)
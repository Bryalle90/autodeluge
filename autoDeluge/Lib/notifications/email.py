import smtplib

class Email():
	def __init__(self):
		pass

	def send_email(self, email_info, msg):
		try:
			smtpserver = smtplib.SMTP(email_info['server'],int(email_info['port']))
			smtpserver.ehlo()
			smtpserver.starttls()
			smtpserver.ehlo
			smtpserver.login(email_info['user'], email_info['pass'])
		except Exception, e:
			print e
			return False

		smtpserver.sendmail(email_info['server'], email_info['to'], msg)

		smtpserver.close()

		return True
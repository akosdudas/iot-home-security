import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from raspberry_sec.interface.action import Action


class EmailAction(Action):
	"""
	Action class for sending emails (with HTML content)
	"""
	LOGGER = logging.getLogger('EmailAction')

	def __init__(self, parameters: dict):
		"""
		Constructor
		:param parameters: see Action constructor
		"""
		super().__init__(parameters)

	def get_name(self):
		return 'EmailAction'

	def fire(self, msg: list, **kwargs):
		"""
		This method sends an email with the content set to the msg.
		:param msg: ActionMessage-s
		"""
		EmailAction.LOGGER.info('Action fired')
		try:
			mail = MIMEMultipart('alternative')
			mail['From'] = self.parameters['from_addr']
			mail['To'] = self.parameters['to_addr']
			mail['Subject'] = self.parameters['subject']

			content = ''.join(['<p>' + str(m.data) + '</p>' for m in msg])
			mail.attach(MIMEText('<html>' + content + '</html>', 'html'))

			with smtplib.SMTP(host=self.parameters['smtp_addr']) as server:
				server.ehlo()
				server.starttls()
				server.login(self.parameters['user'], self.parameters['password'])
				server.sendmail(self.parameters['from_addr'], self.parameters['to_addr'], mail.as_string())

			EmailAction.LOGGER.info('Email has been successfully sent')
		except Exception as e:
			EmailAction.LOGGER.error('Email could not be sent: ' + e.__str__())

import logging
import os, sys, json
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

class ZoneManager:

	LOGGER = logging.getLogger('ZoneManager') 		

	@staticmethod
	def get_abs_path(file: str):
		"""
		:return: the absolute path to file
		"""
		return os.path.abspath(os.path.join(os.path.dirname(__file__), file))

	CONFIG_PATH = get_abs_path.__func__('../../config/prod/pca_system.json')

	def initialize(self):
		"""
		Function, that initialize the zone manager module
		:param _zones: the zones coming from the html code
		"""
		ZoneManager.LOGGER.info('Initializing ZoneManager...')
		with open(ZoneManager.CONFIG_PATH, 'r') as file:
			config = file.read()

		data = json.loads(config)
		stream_controller = data['stream_controller']
		zones = stream_controller['zones'] 

		if zones:
			ZoneManager.LOGGER.info('ZoneManager inizialized')
		else:
			ZoneManager.LOGGER.info('Error initializing ZoneManager')

	def set_zones(self,zones: str):
		"""
		Save the JSON config with the new zones
		:param zones: the new version of zones
		"""
		ZoneManager.LOGGER.info('Setting up new zones')
		with open(ZoneManager.CONFIG_PATH, 'r') as file:
			config = file.read()

		data = json.loads(config)
		data['stream_controller']['zones'] = zones

		with open(ZoneManager.CONFIG_PATH, 'w+') as file:
			json.dump(fp=file, obj=data, indent=4, sort_keys=True)

	def get_zones(self):
		"""
		Function returns avaiable zones in the system
		return: dictionary of zones
		"""
		ZoneManager.LOGGER.info('Getting zone informations')
		with open(ZoneManager.CONFIG_PATH, 'r') as file:
			config = file.read()

		data = json.loads(config)
		stream_controller = data['stream_controller']
		zones = stream_controller['zones']
		return zones

	def add_zone(self,zone: str):
		"""
		Add new zone
		Save into the JSON config
		"""
		with open(ZoneManager.CONFIG_PATH, 'r') as file:
			config = file.read()

		data = json.loads(config)
		data['stream_controller']['zones'][zone] = False

		with open(ZoneManager.CONFIG_PATH, 'w+') as file:
			json.dump(fp=file, obj=data, indent=4, sort_keys=True)

	def delete_zone(self,zone: str):
		"""
		Deleting zone
		Save into the JSON config
		"""
		with open(ZoneManager.CONFIG_PATH, 'r') as file:
			config = file.read()

		data = json.loads(config)
		del data['stream_controller']['zones'][zone]

		with open(ZoneManager.CONFIG_PATH, 'w+') as file:
			json.dump(fp=file, obj=data, indent=4, sort_keys=True)	

	def is_zone_active(self,zone: str):
		"""
		Function for deciding whether the zone is active or not
		:param zone: zone, from which we want to know whether active or not
		"""
		with open(ZoneManager.CONFIG_PATH, 'r') as file:
			config = file.read()

		data = json.loads(config)
		zones = data['stream_controller']['zones'] 

		for key, value in zones.items():
			if key == zone and zones[key] == True:
				ZoneManager.LOGGER.info(zone + ' is active')
				return True
		ZoneManager.LOGGER.info(zone + ' is inactive, not alert')
		return False


	def toggle_zone(self,zone: str):
		"""
		Function for toggle zone activity
		:param zone: the actual zone what we want to activate or deactivate
		"""
		with open(ZoneManager.CONFIG_PATH, 'r') as file:
			config = file.read()

		data = json.loads(config)
		zones = data['stream_controller']['zones']

		for key, value in zones.items():
				if key == zone:
					zones[key] = not value
					ZoneManager.LOGGER.info('Toggle ' + key + ' activity')
					self.set_zones(zones)
	


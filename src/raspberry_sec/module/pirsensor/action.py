from raspberry_sec.interface.action import Action

import logging

class PirsensorAction(Action):
    
    LOGGER = logging.getLogger('PirsensorAction')
    NAME = 'PirsensorAction'

    def __init__(self, parameters: dict):
        super().__init__(parameters)

    def get_name(self):
        return PirsensorAction.NAME

    def fire(self, msg: list):
        PirsensorAction.LOGGER.info('ALERT')
        PirsensorAction.LOGGER.info('; '.join([str(m.data) for m in msg]))
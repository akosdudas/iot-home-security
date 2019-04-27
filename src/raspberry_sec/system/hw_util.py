from uuid import getnode

def check_platform() -> bool:
	"""
	Check if the HW platform the SW is running on is a Raspberry Pi
	:return: True if the HW plaform is issued by the Raspberry Pi Foundation, False otherwise
	"""
	MAC_OUI_RASPBERRY_FOUNDATION = ['b827eb', 'dca632']
	
	mac_addr = getnode()
	mac_addr_oui = format(mac_addr, '02x')[0:6]

	return mac_addr_oui in MAC_OUI_RASPBERRY_FOUNDATION

def is_gpio_floating(pin: int) -> bool:
    """
    Check if a GPIO pin is floating on a raspberry pi
    :param pin: the number of the pin to be checked
    :return: True if the pin is floating, False otherwise
    """
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
    
    GPIO.setup(pin,GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    state1 = GPIO.input(pin)

    GPIO.setup(pin,GPIO.IN, pull_up_down=GPIO.PUD_UP)
    state2 = GPIO.input(pin)

    GPIO.setup(pin,GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    state3 = GPIO.input(pin)

    if state1 == GPIO.LOW and state2 == GPIO.HIGH and state3 == GPIO.LOW:
        return True
    else:
        return False


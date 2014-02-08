import sys
import os
import time

import pymumble
import pymumble.pycelt.celt_0_11 as celt
import pymumble.pyopus.copus as opus
from pymumble.constants import *

Mumble = pymumble.Mumble('localhost', 64738, 'python', 'test', reconnect=True)
Mumble.set_application_string(sys.argv[0])
Mumble.start()
Mumble.is_ready()
Mumble.set_receive_sound(True)

def msg_received(message):
	"""
	This function gets called for each text message received.
	It should cause the registered SIP phone to ring.
	"""
	print message

def sound_received(user, soundchunk):
	"""
	This function gets called for every 20ms of audio received from each user.
	It should transmit the audio received from Mumble to the registered SIP phone if it is currently in a call.
	"""
	user.sound.get_sound() # remove the sound chunk from the buffer
	print user['name'], soundchunk.sequence
	
	# send back the received sound
	global Mumble
	Mumble.sound_output.add_sound(soundchunk.pcm)

def sound_send():
	"""
	This function
	It should transmit the audio received from the SIP phone to Mumble.
	"""
	pass

Mumble.callbacks.set_callback(PYMUMBLE_CLBK_TEXTMESSAGERECEIVED, msg_received)
Mumble.callbacks.set_callback(PYMUMBLE_CLBK_SOUNDRECEIVED, sound_received)

while True:
	time.sleep(10)
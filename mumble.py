import sys
import os
import time

import wave

import pymumble
import pymumble.pycelt.celt_0_11 as celt
import pymumble.pyopus.copus as opus
from pymumble.constants import *

Mumble = pymumble.Mumble('localhost', 64738, 'python', 'test', reconnect=True)
Mumble.set_application_string(sys.argv[0])
Mumble.start()
Mumble.is_ready()
Mumble.set_receive_sound(True)

pcm_fifos = {}

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
	
	try:
		print "Trying to write PCM"
		pcm_fifos[user['name']].writeframes(soundchunk.pcm)
	except:
		fifo_path = 'mumble-%s.wav' % user['name']
		# if not os.path.exists(fifo_path):
		# 	print "Creating FIFO"
		# 	#os.mkfifo(fifo_path)
		# 	os.remove(fifo_path)
		# print "Opening FIFO"
		# fifo = os.open(fifo_path, os.O_NONBLOCK | os.O_WRONLY, 700)
		# print "Opening Wave"
		# wav = wave.open(os.fdopen(fifo,'w'),'w')
		wav = wave.open(fifo_path, 'w')
		print "Setting Wave settings"
		wav.setnchannels(1)
		wav.setsampwidth(16/8)
		wav.setframerate(48000)
		pcm_fifos[user['name']] = wav
		
		# at this point, the client will need to have opened the fifo read-only. Otherwise we get "Device not configured"
		
		print "Writing PCM again"
		pcm_fifos[user['name']].writeframes(soundchunk.pcm)
		
		# problem: wav.writeframes tries to seek the file...
	
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
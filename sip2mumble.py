import sys
import os
import glob
import time
from collections import defaultdict
import audioop

# the host name of the Mumble server
hostname = 'localhost'

# an array of which phones to ring
phones = ['sip:02493571@127.0.0.1:52389']

modpath = glob.glob(os.path.join(os.path.dirname(__file__), 'shtoom*'))
sys.path.append(sorted(modpath)[-1])

# Shtoom imports
from shtoom.doug.source import Source
from shtoom.doug import VoiceApp
from shtoom.app.doug import DougApplication
from shtoom.doug.events import *

# Mumble imports
import pymumble
import pymumble.pycelt.celt_0_11 as celt
import pymumble.pyopus.copus as opus
from pymumble.constants import *

class MumbleSource(Source):
	Mumble = None
	_buffer_from_mumble = defaultdict(str)
	_buffer_to_mumble = ''
	downsampling_ratio = 6
	sample_depth = 2
	chunksize = 320
	
	# TODO: DTMF tones cause disconnect
	
	def __init__(self, mumble):
		self.Mumble = mumble

	def isPlaying(self):
		return True

	def isRecording(self):
		return True

	def close(self):
		self._buffer_from_mumble = defaultdict(str)
		return

	def read(self):
		"""
		Which audio to send to SIP. 2 bytes per sample, 8000 samples per second.
		Sent in 20ms chunks.
		"""
		total = ''
		for user in self._buffer_from_mumble.keys():
			if len(self._buffer_from_mumble[user]) >= self.chunksize:
				#print '%d bytes in buffer from %s' % (len(self._buffer_from_mumble[user]), user)
				r, self._buffer_from_mumble[user] = self._buffer_from_mumble[user][:self.chunksize], self._buffer_from_mumble[user][self.chunksize:]
				if len(total) == 0:
					total = r
				else:
					# Mix sound from multiple Mumble users together
					total = audioop.add(total, r, self.sample_depth)
		return total
	
	_stateUp = None
	def write(self, bytes):
		"""
		Received audio from SIP. 2 bytes per sample, 8000 samples per second.
		The Opus codec needs chunks sized in multiples of 20 ms.
		"""
		self._buffer_to_mumble += bytes
		#print '%d bytes in buffer from %s' % (len(self._buffer_to_mumble), 'SIP')
		if len(self._buffer_to_mumble) <= self.chunksize:
			# we do less-than-or-equal because we need one sample from the next chunk to do proper interpolation
			return
		r, self._buffer_to_mumble = self._buffer_to_mumble[:self.chunksize+self.sample_depth], self._buffer_to_mumble[self.chunksize:] # include one sample from the next chunk, but don't pop it off the buffer
		
		# Silence detection
		rmin,rmax = audioop.minmax(r, self.sample_depth)
		if rmax-rmin < 32:
			return
		
		# upsample the bitrate 1:6 (i.e. 8000:48000) at 16 bit sampling depth
		sound, self._stateUp = audioop.ratecv(r, self.sample_depth, 1, 48000/self.downsampling_ratio, 48000, self._stateUp)
		sound = sound[:-1*self.sample_depth*self.downsampling_ratio] # remove the last six samples, corresponding to the one additional sample we included above
		if len(sound) != self.chunksize*self.downsampling_ratio:
			raise Exception('Upsampling %d samples 6:1 yielded %d samples.' % (self.chunksize, len(sound)))
		self.Mumble.sound_output.add_sound(sound)
	
	_stateDown = None
	def mumble_sound_received(self, user, soundchunk):
		"""
		Received audio from Mumble. 2 bytes per sample, 48000 samples per second.
		Usually received in 20ms or 40ms chunks.
		"""
		user.sound.get_sound() # remove the sound chunk from the buffer
		#print user['name'], soundchunk.sequence, len(soundchunk.pcm)
		
		# downsample the bitrate 6:1 (i.e. 48000:8000) at 16 bit sampling depth
		sound, self._stateDown = audioop.ratecv(soundchunk.pcm, self.sample_depth, 1, 48000, 48000/self.downsampling_ratio, self._stateDown)
		if len(sound) % self.chunksize != 0:
			raise Exception('Downsampling %d samples 6:1 yielded %d samples.' % (len(soundchunk.pcm), len(sound)))
		self._buffer_from_mumble[user['name']] += sound

class MumbleApp(VoiceApp):
	
	Mumble = None

	def __start__(self):
		print "voiceapp.__start__"
		return ( (CallStartedEvent, self.answerCall), )

	def unknownEvent(self, event):
		print "Got unhandled event %s"%event
		return ()

	def answerCall(self, event):
		leg = event.getLeg()
		username = leg.getDialog().getCallee().getURI().username
		caller = leg.getDialog().getCaller().getURI().username
		print "voiceapp.__start__ to user %s from user %s"%(username, caller)
		
		# Connect to Mumble server
		self.Mumble = pymumble.Mumble(hostname, 64738, caller, '', reconnect=True)
		self.Mumble.set_application_string('sip2mumble')
		self.Mumble.start()
		self.Mumble.is_ready()
		self.Mumble.set_receive_sound(True)
		
		leg.answerCall(self)
		return ( (CallAnsweredEvent, self.beginAudio), )

	def beginAudio(self, event):
		e = MumbleSource(self.Mumble)
		self.Mumble.callbacks.set_callback(PYMUMBLE_CLBK_SOUNDRECEIVED, e.mumble_sound_received)
		self.mediaPlay([e,])
		self.mediaRecord(e)
		return ( (CallEndedEvent, self.allDone), )

	def allDone(self, event):
		# Disconnect from Mumble server
		self.Mumble.set_receive_sound(False)
		self.Mumble.reconnect = False
		self.Mumble.connected = PYMUMBLE_CONN_STATE_NOT_CONNECTED
		time.sleep(0.01)
		self.Mumble.control_socket.close()
		
		self.returnResult('other end closed')

class MumbleApplication(DougApplication):
	configFileName = None

def msg_received(message):
	print message
	# TODO: how do we make an outgoing call?
	# scripts/testcall.py makes outgoing calls

def main():
	# register with Mumble server so we can get text messages
	masterMumble = pymumble.Mumble(hostname, 64738, 'sip2mumble', '', reconnect=True)
	masterMumble.set_application_string('sip2mumble registrar')
	masterMumble.start()
	masterMumble.is_ready()
	masterMumble.callbacks.set_callback(PYMUMBLE_CLBK_TEXTMESSAGERECEIVED, msg_received)
	
	global app
	from twisted.internet import reactor

	app = MumbleApplication(MumbleApp)
	app._NATMapping = False
	app.boot()
	app.start()

if __name__ == "__main__":
	main()
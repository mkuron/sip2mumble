import sys
import os
import glob
import time

modpath = glob.glob(os.path.join(os.path.dirname(__file__), 'shtoom*'))
sys.path.append(sorted(modpath)[-1])
#modpath = glob.glob(os.path.join(os.path.dirname(__file__), 'shtoom*/scripts'))
#sys.path.append(sorted(modpath)[-1])

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
	_buffer = ''
	_delay = 0.0
	
	def __init__(self, mumble):
		self.Mumble = mumble

	def isPlaying(self):
		return True

	def isRecording(self):
		return True

	def close(self):
		self._buffer = ''
		return

	def read(self):
		"""
		Which audio to send to SIP
		"""
		# 2 bytes per sample, 8000 samples per second
		if len(self._buffer) >= 320+(self._delay * 16000.0):
			r, self._buffer = self._buffer[:320], self._buffer[320:]
			return r
		else:
			return ''

	def write(self, bytes):
		"""
		Received audio from SIP
		"""
		return
		self._buffer += bytes
	
	def mumble_sound_received(self, user, soundchunk):
		user.sound.get_sound() # remove the sound chunk from the buffer
		print user['name'], soundchunk.sequence # TODO: we need to mix the sound from multiple users together
		self._buffer += soundchunk.pcm[::3] # TODO: we need to get bytes XX____ instead of bytes X__X__!

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
		self.Mumble = pymumble.Mumble('localhost', 64738, caller, '', reconnect=True)
		self.Mumble.set_application_string(sys.argv[0])
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

def main():
	global app
	from twisted.internet import reactor

	app = MumbleApplication(MumbleApp)
	app._NATMapping = False
	app.boot()
	app.start()

if __name__ == "__main__":
	main()
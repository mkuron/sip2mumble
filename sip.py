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

class EchoSource(Source):
	def __init__(self, delay=0.0):
		self._buffer = ''
		self._delay = delay

	def isPlaying(self):
		return True

	def isRecording(self):
		return True

	def close(self):
		self._buffer = ''
		return

	def read(self):
		# 2 bytes per sample, 8000 samples per second
		if len(self._buffer) >= 320+(self._delay * 16000.0):
			r, self._buffer = self._buffer[:320], self._buffer[320:]
			return r
		else:
			return ''

	def write(self, bytes):
		self._buffer += bytes

class EchoApp(VoiceApp):
	
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
		return ( (CallAnsweredEvent, self.beginEcho), )

	def beginEcho(self, event):
		from shtoom.doug.source import EchoSource
		e = EchoSource(delay=0.0)
		self.mediaPlay([e,])
		self.mediaRecord(e)
		return ( (CallEndedEvent, self.allDone), )

	def allDone(self, event):
		# Disconnect from Mumble server
		self.Mumble.reconnect = False
		self.Mumble.connected = PYMUMBLE_CONN_STATE_NOT_CONNECTED
		time.sleep(0.01)
		self.Mumble.control_socket.close()
		
		self.returnResult('other end closed')

class EchoApplication(DougApplication):
	configFileName = None

def main():
	global app
	from twisted.internet import reactor

	app = EchoApplication(EchoApp)
	app._NATMapping = False
	app.boot()
	app.start()

if __name__ == "__main__":
	main()
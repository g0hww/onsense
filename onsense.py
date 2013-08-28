#!/usr/bin/env python

'''
This file is part of OnSense.

OnSense is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

OnSense is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with OnSense.  If not, see <http://www.gnu.org/licenses/>.

Copyright 2013 Darren Long, G0HWW. darren.long@mac.com
'''

import pexpect
from threading import Thread
from optparse import OptionParser
import time
import sys

try:
    #import pynotify
    import notify2
    print "you seem to have pynotify installed"

except:
    print "you don't seem to have pynotify installed"

from gnuradio.eng_option import eng_option


class sense_report:
	def __init__(self, report):
		fields = report.split()
		if(fields[2] != 'center_freq'):
			print "\r\n*** BAD REPORT " #+ report
			self.ok = False
		else:
			self.ok = True		
			self.date = fields[0]
			self.timetag = fields[1]
			#skip centre tag [2]
			self.dwell = float(fields[3])
			# skip freq tag [4]
			self.freq = float(fields[5])
			# skip power tag [6]
			self.power = float(fields[7])
			# skip noise tag [8]
			self.noise = float(fields[9])
			self.comments = ''

	def display(self, squelch):
		if self.ok == False:
			return
		output = self.date
		output +=' '+self.timetag
		#output +=' '+str(self.dwell)
		output +='\t'+"{0:.3f}".format((self.freq)/(1e6))+' Mhz'
		output += '\t+'+str("{0:.2f}".format(self.power))+' dB'
		#output +=' '+str(self.noise)
		output +=' ' + self.comments
		return '\r' + output



class sense_squelch:
	def __init__(self, level, centre_margin):
		self.level = level
		self.margin = centre_margin
		
	def process(self, report):
		if(report.dwell == report.freq):
			report.comments += '\tCENTRE'
			if(report.power >= (self.level + self.margin)):
				return True
		else:
			if(report.power >= self.level):
				return True
			else:
				return False	
		

class sense_rx:

        def __init__(self):
                usage = "usage: %prog [options] min_freq max_freq"
		parser = OptionParser(option_class=eng_option, usage=usage)
		parser.add_option("-a", "--args", type="string", default="",
		                  help="Device args [default=%default]")
		#parser.add_option("-A", "--antenna", type="string", default=None,
		#                  help="Select antenna where appropriate")
		parser.add_option("-s", "--samp-rate", type="eng_float", default=None,
		                  help="Set sample rate (bandwidth), minimum by default")
		parser.add_option("-g", "--gain", type="eng_float", default=None,
		                  help="Set gain in dB (default is midpoint)")
		parser.add_option("", "--tune-delay", type="eng_float",
		                  default=0.025, metavar="SECS",
		                  help="Time to delay (in seconds) after changing frequency [default=%default]")
		parser.add_option("", "--dwell-delay", type="eng_float",
		                  default=0.025, metavar="SECS",
		                  help="Time to dwell (in seconds) at a given frequency [default=%default]")
		parser.add_option("-b", "--channel-bandwidth", type="eng_float",
		                  default=25e3, metavar="Hz",
		                  help="Channel bandwidth of fft bins in Hz [default=%default]")
		parser.add_option("-q", "--squelch-threshold", type="eng_float",
		                  default=10, metavar="dB",
		                  help="Squelch threshold in dB [default=%default]")
		parser.add_option("-c", "--centre-margin", type="eng_float",
		                  default=26, metavar="dB",
		                  help="Additional margin applied to squelch threshold in dB to compensate for DC [default=%default]")		                  
		#parser.add_option("-F", "--fft-size", type="int", default=None,
		#                  help="Specify number of FFT bins [default=samp_rate/channel_bw]")
		parser.add_option("", "--real-time", action="store_true", default=False,
		                  help="Attempt to enable real-time scheduling")
		parser.add_option("-m", "--rig-model", type="string", default="",
		                  help="Hamlib rig model (--rig-device is mandatory) [default=%default]")
		parser.add_option("-d", "--rig-device", type="string", default="",
		                  help="Device for Hamlib rig, perhaps \"/dev/ttyUSB0\" (with --rig_baud) or \"localhost\" for rigctld  [default=%default]")
		parser.add_option("-o", "--rig-baud", type="string", default=None,
		                  help="Baud for Hamlib rig device (not required for rigctld) [default=%default]")
		                  
		(options, args) = parser.parse_args()
		if len(args) != 2:
		    parser.print_help()
		    sys.exit(1)

		if((options.rig_model != "") and (options.rig_device != "")):
			self.rig_model = options.rig_model
			self.rig_device = options.rig_device
			self.rig_baud = options.rig_baud
			self.aux_rx = slave_rx(options.rig_model, options.rig_device, self.rig_baud)
		else:
			print "*** No Hamlib model or device specific.  No remote slave receiver will be used. OnSense will only"
			print "*** provide reports and notifications of activity."
			
            
		self.util = 'osmocom_spectrum_sense'
		self.device = options.args
		self.srate = options.samp_rate
		self.gain = options.gain
		self.low_edge =  args[0]
		self.high_edge = args[1]		
		
		self.chan_space = options.channel_bandwidth
		self.tune_delay = options.tune_delay
		self.dwell_delay = options.dwell_delay
		self.squelch = options.squelch_threshold
		self.centre_margin = options.centre_margin
		self.cmd = self.util+' -a '+self.device+' -s '+str(self.srate)+' -g '+str(self.gain)+' -b '+str(self.chan_space)
		self.cmd += ' --tune-delay='+str(self.tune_delay)+' --dwell-delay='+str(self.dwell_delay)
		if(options.real_time == True):
			self.cmd += ' --real-time '
		self.cmd += ' -q '+str(self.squelch)+' '
		self.cmd += str(self.low_edge)+' '+str(self.high_edge)
		self.filter = sense_filter()
		self.squelcher = sense_squelch(self.squelch, self.centre_margin)

	def respawn(self):
		return pexpect.spawn(self.cmd)
		

	def run(self):
		print self.cmd
		sensor = pexpect.spawn(self.cmd)
		sensor.timeout = 3.0
		sensor.expect(["gain = ", pexpect.EOF,  pexpect.TIMEOUT])
		sensor.expect(["\r\n",pexpect.EOF, pexpect.TIMEOUT])
		strongest = self.squelch
		sensor.timeout = 1.0
		timeout_count = 0
		fadeout_count = 0
		if notify2.init("OnSense"):
			notify = notify2.Notification("OnSense")
			notify.set_timeout(30)
		last = 0.0	
		while(True):
			try:
				index = sensor.expect(["\r\n", "OO", pexpect.EOF,  pexpect.TIMEOUT])
				if index == 0:
					report = sense_report(sensor.before)
					if((report.ok == True) and (self.squelcher.process(report))):
						if((last == report.freq)and((report.power+9.0) > strongest)) or (report.power > strongest):
							if(self.filter.process(report)):
									fadeout_count = 0							
									if(self.aux_rx != None):
										self.aux_rx.tune(report.freq)
									text = report.display(self.squelch)
									if((text != None) and (notify != None)):
										sys.stdout.write('\r\n')
										notification =  report.date+'\t\t'+report.timetag+'\r'
										notification += "{0:.3f}".format((report.freq)/(1e6))+' Mhz'
										notification += '\t+'+str("{0:.2f}".format(report.power))+' dB'
										if(last == report.freq):
											notification += "\tMONITORING"
											text += "\tMONITORING"
											strongest = report.power + 9.0
											sys.stdout.write('+')
										else:
											notification += "\tDETECT"
											text += "\tDETECT"
											strongest = report.power + 3.0											
										last = report.freq
										notification += report.comments
										notify.update("OnSense", notification)
										notify.show()
										sys.stdout.write(text+'\r\n')
							else:
								sys.stdout.write("x")
						else:
							fadeout_count += 1
							if((strongest>self.squelch) and (fadeout_count%10)==0) and (last != report.freq):
								strongest -= 1.0
								sys.stdout.write('-')
							if(fadeout_count > 50):
								fadeout_count = 0
								sys.stdout.write('0')
								strongest = self.squelch													
					else:
						if(report.ok == True):
							sys.stdout.write("c")
							strongest -= 1.0
					if(strongest <= self.squelch):
						sys.stdout.write('=')
					sys.stdout.flush()
				elif index == 1:
					print "\rSensor overflowed!"
					raise(Exception("Sensor overflowed!"))
				elif index == 2:
					print "\rSensor died!"
					print sensor.before
					raise(Exception("Sensor died!"))
				elif index == 3:
					if(timeout_count >= 1):
						raise Exception("Timeout reties exceeded!")
					else:
						timeout_count += 1
					strongest = self.squelch
					fadeout_count = 0
					sys.stdout.write('.')
					sys.stdout.flush()
			except Exception as e:
				timeout_count = 0
				print type(e)
				print "\r***" + str(e.args)
				sensor.kill(9)
				time.sleep(1.3)				
				sensor.close()
				time.sleep(1.3)
				print "*** Respawning"
				sensor = self.respawn()
				sensor.timeout = 3.0
				sensor.expect(["gain = ", pexpect.EOF,  pexpect.TIMEOUT])
				sensor.expect(["\r\n",pexpect.EOF, pexpect.TIMEOUT])	
				sensor.timeout = 1.0
				strongest = self.squelch		

class sense_filter:
	def __init__(self):
		self.blacklist = []
		'''
		self.blacklist += [120000000.0]
		self.blacklist += [126600000.0]
		self.blacklist += [131525000.0]
		self.blacklist += [131725000.0]
		self.blacklist += [131825000.0]
		self.blacklist += [133950000.0]
		self.blacklist += [135375000.0]
		self.blacklist += [136500000.0]
		self.blacklist += [137500000.0]		
		self.blacklist += [137800000.0]	
		self.blacklist += [137925000.0]					
		self.blacklist += [137925000.0]			
		self.blacklist += [137950000.0]			
		self.blacklist += [137975000.0]		
		self.blacklist += [138000000.0]	
		
		self.blacklist += [230000000.0]
		self.blacklist += [240000000.0]
		self.blacklist += [249950000.0]		
		self.blacklist += [250000000.0]
		self.blacklist += [250025000.0]
		self.blacklist += [250050000.0]
		self.blacklist += [252000000.0]		
		self.blacklist += [260000000.0]		
		self.blacklist += [280000000.0]
		self.blacklist += [281375000.0]	
		self.blacklist += [281400000.0]
		self.blacklist += [281425000.0]
		self.blacklist += [282000000.0]		
		self.blacklist += [288000000.0]		
		self.blacklist += [288025000.0]
		self.blacklist += [294000000.0]
		self.blacklist += [295100000.0]				

		self.blacklist += [300000000.0]														
		self.blacklist += [312000000.0]		
		self.blacklist += [313400000.0]
		self.blacklist += [313375000.0]
		self.blacklist += [320000000.0]
		self.blacklist += [323600000.0]
		self.blacklist += [337675000.0]
		self.blacklist += [336000000.0]
		self.blacklist += [340000000.0]
		self.blacklist += [350000000.0]		
		self.blacklist += [360000000.0]	
		self.blacklist += [372000000.0]		
		self.blacklist += [379875000.0]
		self.blacklist += [392850000.0]
		self.blacklist += [392875000.0]
		'''
		
	def add(self, freq):
		self.blacklist += freq
		
	def list(self):
		for item in self.blacklist:
			print "*** "+str(item)+" blacklisted!"
		
	def process(self, report):
		if(report.freq not in self.blacklist):
			return True
		else:
			return False

class slave_rx:
	def __init__(self, model, device, baud=None):
		self.model = model
		self.device  = device
		self.baud = baud
		self.cmd = "rigctl -m "+str(model)+" -r "+device
		if(baud != None):
			self.cmd +=" -s "+str(baud)
		print self.cmd
		self.rigctl = pexpect.spawn(self.cmd)
		
	def tune(self, freq):
		cmd = "F " + str(int(freq))+"\r"
		self.rigctl.sendline(cmd)
		self.rigctl.close()
		self.rigctl = pexpect.spawn(self.cmd)		
		

if __name__ == '__main__':
	sdr_rx = sense_rx()
	sdr_rx.run()
	


from tkinter import simpledialog
import tkinter as tk

from threading import Thread
from random import gauss
#import RPi.GPIO as GPIO
import time

# The sound comes from PC, primarly use simpleaudio with a PowerShell (windows)
#  fallback.
try:
	import simpleaudio as sa
except:
	import os
	if os.name == 'nt':
		# this has a significant delay, but a no-dependency way to achieve this
		import powershellaudio as sa 
	# TODO: support aplay for *nix.
	else:
		sys.stderr.write("WARNING: No simpleaudio module, cannot play sounds.")
		sa = None

if sa:    
	lap_sound = sa.WaveObject.from_wave_file("sound/lap.wav")
	bleep_sound = sa.WaveObject.from_wave_file("sound/bleep.wav")
	blip_sound = sa.WaveObject.from_wave_file("sound/blip.wav")
	end_sound = sa.WaveObject.from_wave_file("sound/end.wav")

#GPIO_PINS = [21,23,18] # lane1, lane2, buzzer
SERIAL_SENSOR_PORT = "COM7"
LANE_COUNT = 4
DEFAULT_RACE_LAPS = 10

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 800

FONT_SCALE = 0.5
colBg1 = '#04080c'
colBg2 = '#101e28'
colFg1 = '#a1aeb4'
colFg2 = '#c8d0d4'
colGreen = '#6ca32c'
colRed = '#f34820'
colPurple = '#e051d4'
colScroll = '#273a46'

PAD = 10
SMALL_PAD = 5

HUGE_B_FONT = "Roboto %d bold"%int(82*FONT_SCALE)
MID_B_FONT = "Roboto %d bold"%int(32*FONT_SCALE)

MID_FONT = "Roboto %d"%int(32*FONT_SCALE)
SMALL_FONT = "Roboto %d"%int(28*FONT_SCALE)
TINY_FONT = "Roboto %d"%int(24*FONT_SCALE)
LAP_FONT = "Courier %d"%int(32*FONT_SCALE)

class StopWatch(tk.Frame):
	""" Implements a stop watch frame widget. """                                                                
	def __init__(self, parent=None, **kw):        
		tk.Frame.__init__(self, parent, kw)
		global LapRace
		self.config(bg=colBg2)
		self._start = 0.0
		self._elapsedtime = 0.0
		self._running = 0
		self.timestr = tk.StringVar()
		self.lapstr = tk.StringVar()
		self.lapSplit = tk.StringVar()
		self.bestLap = tk.StringVar()
		self.bestTime = 0
		self.e = 0
		self.m = 0
		self.makeWidgets()
		self.laps = []
		self.lapmod2 = 0
		self.today = time.strftime("%d %b %Y %H-%M-%S", time.localtime())
	
	def lapTrigger(self):
		if (len(self.laps)+1 == int(LapRace.get())): # Finish Race if last lap
			self.Finish()
		else:
			self.Lap()
		if sa:
			lap_sound.play()
		
	def makeWidgets(self):        
		l2 = tk.Label(self, textvariable=self.lapstr)
		self.lapstr.set('Lap: 0 / 0')
		l2.config(fg=colFg2, bg=colBg2, font=(MID_B_FONT))
		l2.pack(fill=tk.X, expand=tk.NO, pady=(2*PAD,0), padx=0)
		
		self.l = tk.Label(self, textvariable=self.timestr)
		self.l.config(fg=colFg2, bg=colBg2, font=(HUGE_B_FONT))
		self._setTime(self._elapsedtime)
		self.l.pack(fill=tk.X, expand=tk.NO, pady=(0,2*PAD), padx=0)
		
		frm = tk.Frame(self)
		frm.config(bg=colBg2)
		frm.pack(fill=tk.X, expand=1, pady=(0,2*PAD))
		
		frm2 = tk.Frame(self)
		frm2.config(bg=colBg2)
		frm2.pack(fill=tk.X, expand=1, pady=(0,3*PAD))
		
		self.spt = tk.Label(frm, textvariable=self.lapSplit, anchor=tk.W)
		self.lapSplit.set('Split: ')
		self.spt.config(fg=colFg1, bg=colBg2, font=(MID_B_FONT))
		self.spt.pack(pady=0, padx=0, fill=tk.X, expand=1, side=tk.LEFT)
				
		self.best = tk.Label(frm, textvariable=self.bestLap, anchor=tk.E)
		self.bestLap.set('Best: ')
		self.best.config(fg=colFg1, bg=colBg2, font=(MID_B_FONT))
		self.best.pack(pady=0, padx=0, fill=tk.X, expand=1, side=tk.RIGHT)

		l3 = tk.Label(frm2, text='- Times -')
		l3.config(fg=colFg1, bg=colBg1, font=(TINY_FONT))
		l3.pack(fill=tk.X, expand=tk.NO, pady=(PAD,0), padx=0)
		
		tk.Button(frm2, text='Finish Line', command=self.Finish, font=(SMALL_FONT), bg=colBg1, fg=colFg1, highlightthickness=1, highlightbackground=colFg1, relief=tk.FLAT).pack(side=tk.BOTTOM, fill=tk.X, expand=1, padx=0, pady=0)
		tk.Button(frm2, text='Lap', command=self.Lap, font=(SMALL_FONT), bg=colBg1, fg=colFg1, highlightthickness=1, highlightbackground=colFg1, relief=tk.FLAT).pack(side=tk.BOTTOM, fill=tk.X, expand=1, padx=0, pady=10)
		
		scrollbar = tk.Scrollbar(frm2, orient=tk.VERTICAL, bg=colScroll, highlightthickness=0, relief=tk.FLAT, troughcolor=colBg1, bd=0 )
		self.m = tk.Listbox(frm2,selectmode=tk.EXTENDED, height = 10, yscrollcommand=scrollbar.set)
		self.m.config(bd='0', fg=colFg1, bg=colBg1, highlightthickness=0, font=(LAP_FONT))
		self.m.pack(side=tk.LEFT, fill=tk.BOTH, expand=1, pady=0, padx=0)
		scrollbar.config(command=self.m.yview)
		scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

	def _update(self): 
		""" Update the label with elapsed time. """
		self._elapsedtime = time.time() - self._start
		self._setTime(self._elapsedtime)
		self._timer = self.after(25, self._update)

	def _setTime(self, elap):
		""" Set the time string to Minutes:Seconds:Thousandths """
		minutes = int(elap/60)
		seconds = int(elap - minutes*60.0)
		hseconds = int(((elap - minutes*60.0 - seconds)*10000)/10)                
		self.timestr.set('%02d:%02d:%03d' % (minutes, seconds, hseconds))

	def _setLapTime(self, elap):
		""" Set the time string to Minutes:Seconds:Thousandths """
		minutes = int(elap/60)
		seconds = int(elap - minutes*60.0)
		hseconds = int((elap - minutes*60.0 - seconds)*1000)           
		return '%02d:%02d:%02d' % (minutes, seconds, hseconds)
		
	def _bestLap(self, elap):
		if ((elap < self.bestTime) or (self.bestTime == 0)):
			self.bestTime = elap
			self.bestLap.set('Best: '+str(float("{0:.3f}".format(elap))))
			self.best.config(fg=colPurple)
			for i in range(3):
				time.sleep(0.3)
				self.best.config(fg=colBg2)
				time.sleep(0.3)
				self.best.config(fg=colPurple)
			

	def Start(self):                                                     
		""" Start the stopwatch, ignore if running. """
		if not self._running:            
			self._start = time.time() - self._elapsedtime
			self.lapstr.set('Lap: {} / {}'.format(len(self.laps), int(LapRace.get())))
			self._update()
			self._running = 1        
	
	def Stop(self):
		""" Stop the stopwatch, ignore if stopped. """
		if self._running:
			self.after_cancel(self._timer)            
			self._elapsedtime = time.time() - self._start    
			self._setTime(self._elapsedtime)
			self._running = 0

	def Reset(self):
		""" Reset the stopwatch. """
		self._start = time.time()
		self._elapsedtime = 0.0
		self.laps = []
		self.m.delete(0,tk.END)
		self.lapmod2 = self._elapsedtime
		self._setTime(self._elapsedtime)
		self.lapSplit.set('Split: ')
		self.bestLap.set('Best: ')
		self.l.config(fg=colFg1)
		self.spt.config(fg=colFg1)
		self.best.config(fg=colFg1)
		self.bestTime = 0
		
	def Finish(self):
		""" Finish race for this lane """
		self.Lap()
		self.Stop()
		if sa:
			end_sound.play()

	def Lap(self):
		'''Makes a lap, only if started'''
		tempo = self._elapsedtime - self.lapmod2
		if (self._running):
			self.laps.append([self._setLapTime(tempo),float("{0:.3f}".format(tempo))])
			self.m.insert(tk.END, self.laps[-1][0])
			self.m.yview_moveto(1)
			self.lapmod2 = self._elapsedtime
			# Update lap counter
			self.lapstr.set('Lap: {} / {}'.format(len(self.laps), int(LapRace.get())))
			# Update these in the background
			split = Thread(target=splitTimes, args=())
			split.start()
			bestCheck = Thread(target=self._bestLap, args=(float("{0:.3f}".format(tempo)),))
			bestCheck.start()
	
		
class Fullscreen_Window:
	def __init__(self):
		self.tk = tk.Tk()
		try:
			# X11
			self.tk.attributes('-zoomed', False) # set this to True to zoom the window to fill the available screen
		except:
			# Win / OSX
			#self.tk.state('zoomed') # set this to True to zoom the window to fill the available screen
			pass 
		self.frame = tk.Frame(self.tk)
		self.frame.pack()
		self.state = True
		#self.tk.attributes("-fullscreen", self.state)
		self.tk.bind("<F>", self.toggle_fullscreen)
		self.tk.bind("<Escape>", self.end_fullscreen)
		
	def toggle_fullscreen(self, event=None):
		self.state = not self.state
		self.tk.attributes("-fullscreen", self.state)
		return "break"
		
	def end_fullscreen(self, event=None):
		self.state = False
		self.tk.attributes("-fullscreen", False)
	
def StartRace():
	for sw in sws: sw.Start()
	
def StopRace():
	for sw in sws: sw.Stop()
	
def ResetRace():
	for sw in sws: sw.Reset()
	
def ShowRaceLights():
	hs_HDish = SCREEN_WIDTH>1280
	if hs_HDish:
		img_off = tk.PhotoImage(file="imgs/light_off_hd.png")
		img_red = tk.PhotoImage(file="imgs/light_red_hd.png")
		img_green = tk.PhotoImage(file="imgs/light_green_hd.png")
	else:
		img_off = tk.PhotoImage(file="imgs/light_off.png")
		img_red = tk.PhotoImage(file="imgs/light_red.png")
		img_green = tk.PhotoImage(file="imgs/light_green.png")
		
	lights = []
	
	coords = [(SCREEN_WIDTH/7*i,SCREEN_HEIGHT/6) for i in range(1,6)]

	cv = tk.Canvas(root.tk, width=SCREEN_WIDTH, height=SCREEN_HEIGHT, bg=colBg1, highlightthickness=0)
	cv.place(x=0, y=0)

	for i in range(5):
		lights.append(tk.Label(root.tk, image=img_off, bg=colBg1))
		lights[i].place(x=coords[i][0], y=coords[i][1])
	
	lights.append(cv)
	root.tk.update()
	time.sleep(1)

	for i in range(5):
		lights[i].config(image = img_red)
		lights[i].image = img_red
		root.tk.update()
		if sa:
			blip_sound.play()
		time.sleep(1)
							
	for i in range(5):
		lights[i].config(image = img_green)
		lights[i].image = img_green
	
	# the lights are turned green after a random wait
	time.sleep(gauss(1.0, 0.2))
	root.tk.update()
	if sa:
		bleep_sound.play()

	def LightsOut(lights):
		time.sleep(1)
		for i in range(5):
			lights[i].destroy()
		lights[5].destroy()
		root.tk.update()

	lo = Thread(target=LightsOut, args=([lights]))
	lo.start()
	
	StartRace()
	
def splitTimes():
	if len(sws)<=1: return # no sense to show split times for one timer
	
	# sorts so that winner is first (using custom __sortkey__)
	positions = list(sws); positions.sort(key=lambda sw: (-len(sw.laps), sw.lapmod2))

	for sw_i in range(len(positions)-1):
		leading_lane_sw = positions[sw_i]
		trailing_lane_sw = positions[sw_i+1]
		
		diff = 0;
		shared_laps = len(trailing_lane_sw.laps)
		lapped_laps = len(leading_lane_sw.laps)-shared_laps
		for lap_i in range(shared_laps):
			diff += trailing_lane_sw.laps[lap_i][1]-leading_lane_sw.laps[lap_i][1]
		for lap_i in range(lapped_laps):
			if shared_laps+lap_i>=len(leading_lane_sw.laps): continue
			diff += leading_lane_sw.laps[shared_laps+lap_i][1]
	  
		if (sw_i==0):
			leading_lane_sw.lapSplit.set('Split: -'+"{0:.3f}".format(diff))
			leading_lane_sw.spt.config(fg=colGreen)
			leading_lane_sw.l.config(fg=colGreen)
		
		trailing_lane_sw.lapSplit.set('Split: +'+"{0:.3f}".format(diff))
		trailing_lane_sw.spt.config(fg=colRed)
		trailing_lane_sw.l.config(fg=colRed)

def serialTriggering(has_to_stop):
	global root, sws
	import serial

	with serial.Serial(port=SERIAL_SENSOR_PORT,baudrate=115200, timeout=0.1) as ser:
		while True:
			# asked to close the thread?
			if has_to_stop(): break
			chr = ser.read(1)
			# timeout, continue trying
			if len(chr) == 0: continue

			# got trigger
			tigger_lane = int(chr.decode("utf-8"))
			if (tigger_lane>0 and tigger_lane<=len(sws)):
				sws[tigger_lane-1].lapTrigger()

def main():
	global root, sws, inputID, LapRace 

	#GPIO.setmode(GPIO.BCM)
	
	root = Fullscreen_Window()
	root.tk.geometry(str(SCREEN_WIDTH)+"x"+str(SCREEN_HEIGHT))
	root.tk.configure(bg='#04080c')
	root.tk.title('Tyco Race Control')
	
	bkgc = tk.Canvas(root.tk, width=SCREEN_WIDTH, height=SCREEN_HEIGHT/2, bg=colBg2, highlightthickness=0)
	bkgc.place(x=0, y=0)
	
	sws = []
	halfway = int(LANE_COUNT/2)
	for i in range(LANE_COUNT):
		sw = StopWatch(root.tk)
		sw_side = tk.RIGHT if i>=halfway else tk.LEFT
		sw.pack(side=sw_side, padx=(PAD,PAD))
		sws.append(sw)
	sws = sws[:halfway]+list(reversed(sws[halfway:]))

	btnFrm = tk.Frame(root.tk)
	btnFrm.config(bg=colBg1)
	btnFrm.place(relx=0.5, rely=0.6, anchor=tk.CENTER)

	tk.Button(btnFrm, text='Quit', command=root.tk.quit, font=(MID_FONT), bg=colFg1, fg=colBg1, highlightthickness=0, relief=tk.FLAT).pack(side=tk.BOTTOM, anchor=tk.N, fill=tk.X, pady=PAD)
	tk.Button(btnFrm, text='Reset', command=ResetRace, font=(MID_FONT), bg=colFg1, fg=colBg1, highlightthickness=0, relief=tk.FLAT).pack(side=tk.BOTTOM, anchor=tk.N, fill=tk.X, pady=PAD)
	tk.Button(btnFrm, text='Stop', command=StopRace, font=(MID_FONT), bg=colFg1, fg=colBg1, highlightthickness=0, relief=tk.FLAT).pack(side=tk.BOTTOM, anchor=tk.N, fill=tk.X, pady=PAD)
	tk.Button(btnFrm, text='Start', command=StartRace, font=(MID_FONT), bg=colGreen, fg='white', highlightthickness=0, relief=tk.FLAT).pack(side=tk.BOTTOM, anchor=tk.N, fill=tk.X, pady=PAD)
	tk.Button(btnFrm, text='Lights', command=ShowRaceLights, font=(MID_FONT), bg=colGreen, fg='white', highlightthickness=0, relief=tk.FLAT).pack(side=tk.BOTTOM, anchor=tk.N, fill=tk.X, pady=PAD)

	LapRace = tk.StringVar(root.tk, value="10")
	def ask_lap_count(event):
		new_laps = simpledialog.askinteger(title="Laps", prompt="Set Number of Laps", parent=root.tk, minvalue=1)
		LapRace.set(new_laps)

	root.tk.bind("f", root.toggle_fullscreen)
	root.tk.bind("l", ask_lap_count)
			
	# Bind keyboard keys 1,2,... to lap triggers (to allow manual counting or correction)
	#  Note: closures in Python are weird. Initial attempt did not work as 
	#   I expected due to late binding.
	def create_lap_hander(sw_to_call):
		return lambda e: sw_to_call.lapTrigger()
	kbd_lap_handlers = [create_lap_hander(sw) for sw in sws]
	for numkey in range(1, len(sws)+1):
		root.tk.bind(str(numkey), kbd_lap_handlers[numkey-1])

	# TODO: Feature: allow correction (remove previous lap with SHIFT+1,2,3...
		 
	#raceSetup = raceWidgets(root.tk)
	#raceSetup.pack(side=tk.RIGHT, anchor=tk.S, fill=tk.X, pady=PAD)
	
	#GPIO.setup(pins[0], GPIO.IN)
	#GPIO.add_event_detect(pins[0], GPIO.RISING, callback=triggerLap, bouncetime=1000)
	#GPIO.setup(pins[1], GPIO.IN)
	#GPIO.add_event_detect(pins[1], GPIO.RISING, callback=triggerLap, bouncetime=1000) 
	#if ((GPIO.input(channel)) and (channel == pins[0])):
	#	sw.triggerLap()
	#elif ((GPIO.input(channel)) and (channel == pins[1])):
	#	sw2.triggerLap()


	signal_stop_reading_from_serial = False
	try:
		serialtriggerer = Thread(target=serialTriggering,
			args=(lambda : signal_stop_reading_from_serial, ))
		serialtriggerer.start()
	except:
		tk.messagebox.showerror(title="No Arduino", message="Could not connect to the Arduino through serial,\nuse number keys to keep lap time record.")
	try:
		root.tk.mainloop()
	finally:
		# Ask the serial reader thread to stop
		signal_stop_reading_from_serial = True
	

if __name__ == '__main__':
	main()

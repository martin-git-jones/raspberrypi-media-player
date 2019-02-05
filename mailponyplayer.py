#!/usr/bin/env python3
import sched
import signal
import os
import sys
import time
from time import sleep
from file_read_backwards import FileReadBackwards
try:
   import buttonshim
except:
   print("No buttonshim")
from configparser import ConfigParser

try:
   from omxplayer.player import OMXPlayer
except:
   print("No omxplayer")

print("""
Mailpony Player
Control the mailponyplayer with
A = Volume Up / Change to Playlist A when held
B = Volume Down / Change to Playlist B when held
C = Fast Forward / Create Playlists when held
D = Rewind / Reset 
E = Play / Shutdown when held
Press Ctrl+C to exit.
""")

# Increase volume
#   @buttonshim.on_press(buttonshim.BUTTON_A)
def button_a(button, pressed):
    global player
    print("Status: Increase volume")
    player.action(18)
    try:
        buttonshim.set_pixel(0x94, 0x00, 0xd3)
    except:
        print("No buttons!")

@buttonshim.on_hold(buttonshim.BUTTON_A, hold_time=2)
def button_a(button):
    print("A Held - switch to playList A")
    global playList
    global player
    playList  = 'A'
    setplayList()
    player.action(15)

@buttonshim.on_press(buttonshim.BUTTON_B)
def button_b(button, pressed):
    global player
    print("Status: Decrease volume")
    player.action(17)

@buttonshim.on_hold(buttonshim.BUTTON_B, hold_time=2)
def button_b(button):
    print("B Held - switch to playList B")
    global playList
    global player
    playList = 'B'
    setplayList()
    #kill
    player.action(15)
    #restart_player()

# next track
@buttonshim.on_press(buttonshim.BUTTON_C)
def button_c(button, pressed):
    global player
    global playList
    nextTrack = getNextTrack('next')
    try:
       player.load(nextTrack)
       global starttime
       starttime=abs(time.time())
    except:
       print("Player already dead")
       player = OMXPlayer(nextTrack)
    try:
        buttonshim.set_pixel(0x00, 0xff, 0x00)
    except:
        print("No buttons!")

@buttonshim.on_hold(buttonshim.BUTTON_C, hold_time=2)
def button_c(button):
    global homedir
    global musicdirA
    global musicdirB
    print("C Held - recreating playLists")
    player.action(15)
    createPlayList(musicdirA)
    createPlayList(musicdirB)

#  Rewind
@buttonshim.on_press(buttonshim.BUTTON_D)
def button_d(button, pressed):
    print("D pressed - previous")
    global player
    global playList
    nextTrack = getNextTrack('previous')
    print("rewind  "+nextTrack)
    try:
       player.load(nextTrack)
       global starttime
       starttime=abs(time.time())
    except:
       print("Player already dead")
       player = OMXPlayer(nextTrack)
    try:
       buttonshim.set_pixel(0xff, 0xff, 0x00)
    except:
       print("No buttons!")
    #player.action(16)

@buttonshim.on_hold(buttonshim.BUTTON_D, hold_time=2)
def button_d(button):
    print("D Held - reset")
    global homedir
    global musicdirA
    global musicdirB
    global player
    player.action(15)
    if os.path.exists(homedir+'playList'+'playListA'+'.txt'):
       os.remove(homedir+'playList'+'playListA'+'.txt')
    if os.path.exists(homedir+'playList'+'playListB'+'.txt'):
       os.remove(homedir+'playList'+'playListB'+'.txt')
    createPlayList(homedir+'playList'+'playListA'+'.txt',musicdirA)
    createPlayList(homedir+'playList'+'playListB'+'.txt',musicdirB)
    global inifile
    if os.path.exists(inifile):
       os.remove(inifile)
    createinifile()
    #kill the player
    player.action(15)
    os.system("/usr/bin/sudo shutdown -h restart")

# Soft Power Off?
@buttonshim.on_press(buttonshim.BUTTON_E)
def button_e_press(button, pressed):
    print("E pressed")
    global player
    global playList
    try:
       status=player.playback_status()
       print("Player " + status)
       if status == 'Playing':
          buttonshim.set_pixel(0xff, 0x00, 0x00)
       else:
          buttonshim.set_pixel(0xff,0xff, 0x00)
       player.action(16)
    except:
       nextTrack = getNextTrack('next')
       print("nextTrack "+nextTrack)
       global starttime
       starttime=time.time()
       player = OMXPlayer(nextTrack)

@buttonshim.on_hold(buttonshim.BUTTON_E, hold_time=2)
def button_e(button):
    print("E Held for 2sec!")
    time.sleep(0.1)
    for x in range(3):
        buttonshim.set_pixel(0xff, 0x00, 0x00)
        time.sleep(0.1)
        buttonshim.set_pixel(0x00, 0x00, 0x00)
        time.sleep(0.1)
  
    player.action(15)
    os.system("/usr/bin/sudo shutdown -h now")

def createPlayList(musicdir):
    global playList
    global homedir
    with open(homedir+'playList'+playList+'.txt','w+') as f:
      for cur, _dirs, files in os.walk(musicdir,topdown=True):
        files.sort()
        for t in files:
          print( t)
          f.write(cur+'/'+t+"\n")
    f.close()

def readPlayList(direction):
    retnext=0
    global currTrack
    global homedir
    global playList
    nextTrack=''
    if direction == 'previous':
       hplayList=FileReadBackwards(homedir+'playList'+playList+'.txt', encoding="utf-8")
    else:
       hplayList=open(homedir+'playList'+playList+'.txt','r')
    for f in hplayList: 
           f = f.rstrip('\n')
           if retnext==1:
              nextTrack=f
              break
           if currTrack == "":
              nextTrack=f
              break
           if currTrack == f:
              retnext=1
    return(nextTrack)

def getNextTrack(direction):
   global currTrack
   global startup
   global playList
   if startup == True:
      startup = False
      return currTrack
   else:
     global playList
     config = ConfigParser(allow_no_value=True)
     global inifile
     config.read(inifile)
     currTrack = config.get('Playing', 'currTrack'+playList, fallback = '')
     nextTrack = readPlayList(direction)
     print("setting currTrack to "+currTrack)
     config.set('Playing','currTrack'+playList, nextTrack)
     with open(inifile, 'w') as configfile:
        config.write(configfile)
     return(nextTrack)

def play_track():
     global player
     global playList
     getplayList()
     global starttime
     try:
       status=player.playback_status()
       filename=player.get_filename()
       duration=player.duration()
       currtime=abs(time.time())
       remaining=abs(duration-(currtime-starttime))
       print("Status is " + status +' this ' + filename +' for ' + str(remaining))
     except:
       nextTrack = getNextTrack('next')
       print("restarting "+nextTrack)
       import psutil
       for proc in psutil.process_iter():
    # check whether the process name matches
         if proc.name() == 'omxplayer':
            proc.kill()
       starttime=abs(time.time())
       player = OMXPlayer(nextTrack)
       buttonshim.set_pixel(0xff,0xff, 0x00)

def  restart_player():
     global s
     play_track()
     s.enter(5, 1, restart_player)
     s.run()

     #print(s.queue)

def getplayList():
 global inifile
 global playList
 if os.path.isfile(inifile) == True:
   config = ConfigParser(allow_no_value=True)
   config.read(inifile)
   playList = config.get('Playing', 'playList', fallback = 'A')
 else:
  playList='A'
 return

def setplayList():
   global inifile
   global playList
   if os.path.isfile(inifile) == True:
      config = ConfigParser(allow_no_value=True)
      config.read(inifile)
      config.set('Playing', 'playList', playList)
      with open(inifile, 'w') as configfile:
        config.write(configfile)
   else:
      print("Error setting playlist to "+playList)
   return

def createinifile():
    global inifile
    global playList
    global homedir
    global currTrack
    if os.path.isfile(inifile) == False:
       f=open(inifile,'a')
       print("Creating  "+ inifile) 
       f.close()
    config = ConfigParser(allow_no_value=True)
    config.read(inifile)
    if config.has_section('Playing') == False:
      config.add_section('Playing')
      playListfileA =  homedir +'playListA.txt'
      config.set('Playing','playListA', playListfileA)
      playListfileB =  homedir+'playListB.txt'
      config.set('Playing','playListB', playListfileB)
      currTrack = ''
      playList='B'
      nextTrack = readPlayList( 'next')
      print("next B is "+nextTrack)
      config.set('Playing', 'currTrackB', nextTrack)
      playList='A'
      currTrack = ''
      nextTrack = readPlayList( 'next')
      print("next is "+nextTrack)
      config.set('Playing', 'currTrackA', nextTrack)
      config.set('Playing', 'playlist', playList)
      with open(inifile, 'w') as configfile:
        config.write(configfile)
    return

def getcurrTrack():
    global playList
    global currTrack
    global inifile
    global playList
    global homedir
    if os.path.isfile(inifile) == True:
       config = ConfigParser(allow_no_value=True)
       config.read(inifile)
       currTrack = config.get('Playing', 'currTrack'+playList, fallback = '')
    else :
       currTrack=readPlayList('next')
    return()

startup = True
currTrack =''
homedir = '/home/pi/'
inifile = homedir+"mailponyplayer.ini"
musicdirA = homedir+'Music'
musicdirB = homedir+'courses'
# Change this as below to handle more playlists TODO
musicdirs = {'A':homedir+'Music','B':homedir+'courses'}
for musicdir in musicdirs:
  print( musicdir,musicdirs[musicdir])
playLists = {'A':homedir+'playListA.txt','B':homedir+'playListsB.txt'}
#####
playList='B'
if os.path.isfile(homedir+'playList'+playList+'.txt') == False:
    createPlayList(musicdirB)
playList='A'
if os.path.isfile(homedir+'playList'+playList+'.txt') == False:
    createPlayList(musicdirA)
createinifile()
getplayList()
createinifile()
getcurrTrack()
s = sched.scheduler(time.time, time.sleep)
restart_player()
signal.pause()
#sys.exit(0)

#!/usr/bin/env python3
import sched
import termios
import tty
import psutil
import signal
import os
import sys
import time
from time import sleep
from file_read_backwards import FileReadBackwards
from configparser import ConfigParser
from optparse import OptionParser
# Read options from the command line
parser = OptionParser()
parser.add_option("-A", "--musicdirA", dest="musicdirA", help="First media directory containing files to be played", metavar="FILE")
parser.add_option("-B", "--musicdirB", dest="musicdirB", help="Second media directory containing files to be played", metavar="FILE")
parser.add_option("-k", "--keyboard", action="store_true", dest="usekeyboard", default=False,help="Use keyboard to enter control keys")
parser.add_option("-b", "--buttonshim", action="store_true", dest="usebuttons", default=True,help="Use buttonshim buttons")
(options, args) = parser.parse_args()
# Set initial music directory
dir_path = os.path.dirname(os.path.realpath(__file__))
homedir = dir_path + '/'
if options.musicdirA == '' :
    musicdirA = homedir + 'Music'
if options.musicdirB == '' :
    musicdirB = musicdirA
# See if the buttonshim is installed
try:
    import buttonshim
    buttonshim.set_pixel(0x94, 0x00, 0xd3)
    buttons = True
except:
    print("No buttonshim")
    if options.usebuttons:
       print("Please try again without the -b option")
       sys.exit(0)
    buttons = False
if options.usekeyboard:
   buttons = False
# Check the omxplayer is installed
try:
    from omxplayer.player import OMXPlayer
except:
    print("No omxplayer found ")
    sys.exit(0)


if buttons:
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
else:
    print("""
  Mailpony Player
  Control the mailponyplayer with
  a = Volume Up / Change to Playlist A when held
  A = Change to Playlist A 
  b = Volume Down
  B = Change to Playlist B 
  c = Next Track
  C = Create Playlists 
  d = Previous Track 
  D = Reset 
  e = Play / Pause 
  E = Shutdown 
Press Ctrl+C to exit.
""")


# Increase volume
def inc_volume():
    global player
    print("Status: Increase volume")
    player.action(18)


if buttons:
    @buttonshim.on_press(buttonshim.BUTTON_A)
    def button_a(button, pressed):
        inc_volume()
        buttonshim.set_pixel(0x94, 0x00, 0xd3)


def switchtoplayList(letter):
    print("switch to playList " + letter)
    global playList
    global player
    global direction
    playList = letter
    direction = 'resume'
    setplayList()
    try:
        player.quit()
    except:
        for proc in psutil.process_iter():
            # check whether the process name matches
            if 'omxplayer' in proc.name():
                proc.kill()


if buttons:
    @buttonshim.on_hold(buttonshim.BUTTON_A, hold_time=2)
    def button_a(button):
        switchtoplayList('A')


def dec_volume():
    global player
    print("Status: Decrease volume")
    player.action(17)


if buttons:
    @buttonshim.on_press(buttonshim.BUTTON_B)
    def button_b(button, pressed):
        dec_volume()

if buttons:
    @buttonshim.on_hold(buttonshim.BUTTON_B, hold_time=2)
    def button_b(button):
        switchtoplayList('B')

# next track
def playnextTrack():
    global player
    global playList
    global direction
    direction = 'next'
    print("Next track")
    try:
        player.quit()
    except:
        print("Player already dead")


if buttons:
    @buttonshim.on_press(buttonshim.BUTTON_C)
    def button_c(button, pressed):
        print("c pressed")
        buttonshim.set_pixel(0x00, 0xff, 0x00)
        playnextTrack()


def createPlayLists():
    global homedir
    global musicdirA
    global musicdirB
    print("C Held - recreating playLists")
    try:
        player.quit()
    except:
        for proc in psutil.process_iter():
            # check whether the process name matches
            if 'omxplayer' in proc.name():
                proc.kill()
    createPlayList(musicdirA, 'A')
    createPlayList(musicdirB, 'B')


if buttons:
    @buttonshim.on_hold(buttonshim.BUTTON_C, hold_time=2)
    def button_c(button):
        createPlayLists()


#  Rewind
def playprevTrack():
    print("Previous track")
    global player
    global playList
    global direction
    direction = 'previous'
    try:
        player.quit()
    except:
        print("Player already dead")


if buttons:
    @buttonshim.on_press(buttonshim.BUTTON_D)
    def button_d(button, pressed):
        playprevTrack()
        buttonshim.set_pixel(0xff, 0xff, 0x00)


def resetAll():
    print("D - reset")
    global homedir
    global musicdirA
    global musicdirB
    global player
    try:
        player.action(15)
    except:
        for proc in psutil.process_iter():
            # check whether the process name matches
            if 'omxplayer' in proc.name():
                proc.kill()
    if os.path.exists(homedir + 'playList' + 'playListA' + '.txt'):
        os.remove(homedir + 'playList' + 'playListA' + '.txt')
    if os.path.exists(homedir + 'playList' + 'playListB' + '.txt'):
        os.remove(homedir + 'playList' + 'playListB' + '.txt')
    createPlayList(musicdirA, 'A')
    createPlayList(musicdirB, 'B')
    global inifile
    if os.path.exists(inifile):
        os.remove(inifile)
    createinifile()
    os.system("/usr/bin/sudo shutdown -h restart")


if buttons:
    @buttonshim.on_hold(buttonshim.BUTTON_D, hold_time=2)
    def button_d(button):
        resetAll()


def playorpause():
    global player
    global playList
    global pausetime
    try:
        status = player.playback_status()
        player.action(16)
    except:
        nextTrack = getNextTrack()
        global starttime
        starttime = time.time()
        player = OMXPlayer(nextTrack)


if buttons:
    @buttonshim.on_press(buttonshim.BUTTON_E)
    def button_e_press(button, pressed):
        global player
        status = player.playback_status()
        if status == 'Playing':
            buttonshim.set_pixel(0xff, 0x00, 0x00)
        else:
            buttonshim.set_pixel(0xff, 0xff, 0x00)
        playorpause()


def softpoweroff():
    player.action(15)
    os.system("/usr/bin/sudo shutdown -h now")


if buttons:
    @buttonshim.on_hold(buttonshim.BUTTON_E, hold_time=2)
    def button_e(button):
        print("E Held for 2sec!")
        time.sleep(0.1)
        for x in range(3):
            buttonshim.set_pixel(0xff, 0x00, 0x00)
            time.sleep(0.1)
            buttonshim.set_pixel(0x00, 0x00, 0x00)
            time.sleep(0.1)
        softpoweroff()


def getch():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)

    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch


def createPlayList(musicdir, letter):
    global homedir
    with open(homedir + 'playList' + letter + '.txt', 'w+') as f:
        for cur, _dirs, files in os.walk(musicdir, topdown=True):
            files.sort()
            for t in files:
                print(t)
                f.write(cur + '/' + t + "\n")
    f.close()


def readPlayList():
    retnext = 0
    global currTrack
    global homedir
    global playList
    global direction
    nextTrack = ''
    if direction == 'resume' and currTrack != '':
        nextTrack = currTrack
        return (nextTrack)
    if direction == 'previous':
        hplayList = FileReadBackwards(homedir + 'playList' + playList + '.txt', encoding="utf-8")
    else:
        hplayList = open(homedir + 'playList' + playList + '.txt', 'r')
    for f in hplayList:
        f = f.rstrip('\n')
        if retnext == 1:
            nextTrack = f
            break
        if currTrack == "":
            nextTrack = f
            break
        if currTrack == f:
            retnext = 1
    return (nextTrack)


def getNextTrack():
    global currTrack
    global playList
    config = ConfigParser(allow_no_value=True)
    global inifile
    config.read(inifile)
    currTrack = config.get('Playing', 'currTrack' + playList, fallback='')
    nextTrack = readPlayList()
    config.set('Playing', 'currTrack' + playList, nextTrack)
    with open(inifile, 'w') as configfile:
        config.write(configfile)
    return (nextTrack)


def play_track():
    global player
    global playList
    global starttime
    global direction
    global pausetime
    if direction == '':
        direction = 'next'
    try:
        status = player.playback_status()
        filename = player.get_filename()
        duration = player.duration()
        currtime = int(time.time())
        remaining = int(duration - (currtime - starttime + pausetime))
        print(filename + ' for ' + str(remaining))
    except:
        nextTrack = getNextTrack()
        if direction == 'resume':
            direction = 'next'
        starttime = int(time.time())
        try:
            for proc in psutil.process_iter():
                if 'omxplayer' in proc.name():
                    proc.kill()
            player = OMXPlayer(nextTrack)
        except:
            direction = 'next'
            nextTrack = getNextTrack()
        if buttons:
            buttonshim.set_pixel(0xff, 0xff, 0x00)


def restart_player():
    global s
    global buttons
    play_track()
    if not buttons:
        button_delay = 0.002
        char = getch()
        if (char == "a"):
            time.sleep(button_delay)
            inc_volume()

        elif (char == "A"):
            switchtoplayList('A')

        elif (char == "b"):
            time.sleep(button_delay)
            dec_volume()

        elif (char == "B"):
            time.sleep(button_delay)
            switchtoplayList('B')

        elif (char == "c"):
            time.sleep(button_delay)
            playnextTrack()

        elif (char == "C"):
            time.sleep(button_delay)
            createPlayLists()

        elif (char == "d"):
            time.sleep(button_delay)
            playprevTrack()

        elif (char == "D"):
            time.sleep(button_delay)
            resetAll()


        elif (char == "e"):
            time.sleep(button_delay)
            playorpause()

        elif (char == "E"):
            time.sleep(button_delay)
            softpoweroff()
    s.enter(2, 1, restart_player)


def getplayList():
    global inifile
    global playList
    if os.path.isfile(inifile) == True:
        config = ConfigParser(allow_no_value=True)
        config.read(inifile)
        playList = config.get('Playing', 'playList', fallback='A')
    else:
        playList = 'A'
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
        print("Error setting playlist to " + playList)
    return


def createinifile():
    global inifile
    global playList
    global homedir
    global currTrack
    if os.path.isfile(inifile) == False:
        f = open(inifile, 'a')
        print("Creating  " + inifile)
        f.close()
    config = ConfigParser(allow_no_value=True)
    config.read(inifile)
    if config.has_section('Playing') == False:
        config.add_section('Playing')
        playListfileA = homedir + 'playListA.txt'
        config.set('Playing', 'playListA', playListfileA)
        playListfileB = homedir + 'playListB.txt'
        config.set('Playing', 'playListB', playListfileB)
        currTrack = ''
        playList = 'B'
        nextTrack = readPlayList()
        config.set('Playing', 'currTrackB', nextTrack)
        playList = 'A'
        currTrack = ''
        nextTrack = readPlayList()
        config.set('Playing', 'currTrackA', nextTrack)
        config.set('Playing', 'playlist', playList)
        with open(inifile, 'w') as configfile:
            config.write(configfile)
    return


def getcurrTrack():
    global playList
    global currTrack
    global inifile
    global homedir
    if os.path.isfile(inifile) == True:
        config = ConfigParser(allow_no_value=True)
        config.read(inifile)
        currTrack = config.get('Playing', 'currTrack' + playList, fallback='')
    if os.path.isfile(inifile) == False or currTrack == '':
        currTrack = readPlayList()
    return ()


pausetime = 0
direction = 'resume'
currTrack = ''
inifile = homedir + "mailponyplayer.ini"

# Change this as below to handle more playlists TODO
musicdirs = {'A': homedir + 'Music', 'B': homedir + 'courses'}
for musicdir in musicdirs:
    print(musicdir, musicdirs[musicdir])
playLists = {'A': homedir + 'playListA.txt', 'B': homedir + 'playListsB.txt'}
#####
if os.path.isfile(homedir + 'playList' + 'B' + '.txt') == False:
    createPlayList(musicdirB, 'B')
if os.path.isfile(homedir + 'playList' + 'A' + '.txt') == False:
    createPlayList(musicdirA, 'A')
createinifile()
getplayList()
print("playlist is " + playList)
getcurrTrack()
s = sched.scheduler(time.time, time.sleep)
restart_player()
s.run()
##signal.pause()

# sys.exit(0)

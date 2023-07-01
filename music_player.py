from flask import Flask, redirect, render_template, request
from pygame import mixer
import os
import threading
from threading import Lock
import time
import signal
import sys
import RPi.GPIO as GPIO  

music_dir = "./music"
track_list = []
playing_state = True
now_playing = 0
volume_value = 50

app = Flask(__name__)

running = True
runningLock = Lock()

queue_thread = None
server_thread = None

def turn_off_lights():
    GPIO.output(24,GPIO.LOW)
    GPIO.output(22,GPIO.LOW)
    GPIO.output(23,GPIO.LOW)
    GPIO.output(27,GPIO.LOW)

def set_lights():
    turn_off_lights()
    if volume_value < 25:
        GPIO.output(24,GPIO.HIGH)
    elif volume_value >=25 and volume_value < 50:
        GPIO.output(24,GPIO.HIGH)
        GPIO.output(22,GPIO.HIGH)
    elif volume_value >=50 and volume_value < 75:
        GPIO.output(24,GPIO.HIGH)
        GPIO.output(22,GPIO.HIGH)
        GPIO.output(23,GPIO.HIGH)
    else:
        GPIO.output(24,GPIO.HIGH)
        GPIO.output(22,GPIO.HIGH)
        GPIO.output(23,GPIO.HIGH)
        GPIO.output(27,GPIO.HIGH)

# exit app in an elegant way
def exit_app():
    global queue_thread
    global server_thread
    global running
    with runningLock:
        running = False
    print('Exiting...')
    if queue_thread is not None:
        queue_thread.join()
    sys.exit(0)

def signal_handler(sig, frame):
    exit_app()

def update_track_list():
    for file in sorted(os.listdir(music_dir)):
        # check only text files
        if file.endswith('.wav') or file.endswith('.mp3'):
            track_list.append(file)
    print("Track list: ")
    print(track_list)

### flask endpoints

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('player.html', filename=track_list[now_playing], volume_value=volume_value)


@app.route('/volume', methods=['GET', 'POST'])
def volume():
    global volume_value
    if request.method == "POST":
        volume_value=int(request.form['data'])
        mixer.music.set_volume(volume_value/100)
    set_lights()
    return redirect("/")
    

### mixer control functions


def next(e = None):
    global now_playing
    with runningLock:
        mixer.music.stop()
        now_playing = now_playing + 1 if now_playing < len(track_list) - 1 else 0
        mixer.music.load(music_dir + '/' + track_list[now_playing])
        mixer.music.play()

def previous(e = None):
    global now_playing
    with runningLock:
        mixer.music.stop()
        now_playing = now_playing - 1 if now_playing > 0 else len(track_list) - 1
        mixer.music.load(music_dir + '/' + track_list[now_playing])
        mixer.music.play()

def pause(e = None):
    global playing_state
    with runningLock:
        if playing_state:
            mixer.music.pause()
            playing_state = False
        else:
            mixer.music.unpause()
            playing_state = True

def replay(e = None):
    with runningLock:
        mixer.music.stop()
        mixer.music.load(music_dir + '/' + track_list[now_playing])
        mixer.music.play()

# console control
def input_loop():
    global playing_state
    set_lights()
    filename = music_dir + '/' + track_list[now_playing]
    mixer.music.load(filename)
    mixer.music.set_volume(volume_value/100)
    mixer.music.play()
    while True:
        print("Press 'p' to pause")
        print("Press 'a' to play previous song")
        print("Press 'd' to play next song")
        print("Press 'r' to rewind")
        print("Press 'e' to exit")
        try:
            query = input("  ")
            if query == 'p':
                pause()
            elif query == 'a':
                previous()
            elif query == 'd':
                next()
            elif query == 'r':
                replay()
            elif query == 'e':
                # Stop the mixer
                with runningLock:
                    mixer.music.stop()                                        
                exit_app()
        except:
            break

# busy waiting for the song to end
def queue_loop():
    global running
    while True:
        runningLock.acquire()

        if playing_state and not mixer.music.get_busy():
            runningLock.release()
            next(0)
        else:
            runningLock.release()

        runningLock.acquire()

        if (not running):
            runningLock.release()
            break
        else:
            runningLock.release()
        
        time.sleep(0.5)

# flask thread
def run_server():
    print("Running server")
    try:
        app.run(debug=False, host="0.0.0.0")
    except:
        print("Shutting down")
        pass

def main():

    # set up a signal handler
    signal.signal(signal.SIGINT, signal_handler)

    update_track_list()

    mixer.init()

    GPIO.setmode(GPIO.BCM)

    # setup buttons

    GPIO.setup(25, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(10, GPIO.IN, pull_up_down=GPIO.PUD_UP)  
    GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)  
    GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_UP)  

    GPIO.add_event_detect(25, GPIO.FALLING, callback=previous, bouncetime=200)
    GPIO.add_event_detect(10, GPIO.FALLING, callback=next, bouncetime=200)
    GPIO.add_event_detect(17, GPIO.FALLING, callback=pause, bouncetime=200)
    GPIO.add_event_detect(18, GPIO.FALLING, callback=replay, bouncetime=200)
    
    # setup leds

    GPIO.setup(24,GPIO.OUT)
    GPIO.setup(22,GPIO.OUT)
    GPIO.setup(23,GPIO.OUT)
    GPIO.setup(27,GPIO.OUT)

    # start threads
    
    global queue_thread
    global server_thread

    queue_thread = threading.Thread(target=queue_loop)
    server_thread = threading.Thread(target=run_server, daemon=True)

    queue_thread.start()
    server_thread.start()
    
    input_loop()


if __name__ == '__main__':
    main()
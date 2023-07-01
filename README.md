# rpi4-music-player
A simple python music player for Raspberry Pi 4 using Pygame, Flask and RPi.GPIO.

Place your music (.mp3 or .wav) in ./music.

Visit localhost:5000 for a volume control slider. GPIO leds e turned on/off according to the current volume level.

Use the console to gain access to the following commands:
 * 'p' - pause
 * 'a' - play previous song-
 * 'd' - play next song
 * 'r' - rewind
 * 'e' - exit (Ctrl+C also works)

Alternatively, you can use GPIO buttons SW4 to SW1 to access the first four commands respectively.

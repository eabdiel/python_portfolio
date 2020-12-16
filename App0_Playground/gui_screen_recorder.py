

import pynput
import sys
from pynput.mouse import Button, Listener as MouseListener
from pynput.keyboard import Key, Listener as KeyboardListener

count = 0
inputs = []
gexit = 'False'

def on_press(key):
    if gexit == 'True':
        sys.exit()
    else:
        key_value = ("Key pressed: {0}\n".format(key))
        print(key_value)
        global inputs, count
        inputs.append(key_value)
        count += 1
        if count >= 10:
            count = 0
            save(inputs)
            inputs = []


def on_release(key):
    global gexit
    if key == Key.esc:
        gexit = 'True'


def on_move(x, y):
    if gexit == 'True':
        sys.exit()
    else:
        mouse_val = ('Pointer moved to {0}\n'.format((x, y)))
        print(mouse_val)
        global inputs, count
        inputs.append(mouse_val)
        count += 1
        if count >= 10:
            count = 0
            save(inputs)
            inputs = []


def on_click(x, y, button, pressed):
    if gexit == 'True':
        sys.exit()
    else:
        mouse_click = ('{0} at {1}\n'.format('Mouse Held' if pressed else 'Mouse Released', (x, y)))
        print(mouse_click)
        global inputs, count
        inputs.append(mouse_click)
        count += 1
        if count >= 10:
            count = 0
            save(inputs)
            inputs = []


def on_scroll(x, y, dx, dy):
    if gexit == 'True':
        sys.exit()
    else:
        mouse_scroll = ('Mouse scrolled at ({0}, {1})({2}, {3})\n'.format(x, y, dx, dy))
        print(mouse_scroll)
        global inputs, count
        inputs.append(mouse_scroll)
        count += 1
        if count >= 10:
            count = 0
            save(inputs)
            inputs = []

def save(keys):
    with open("screen_recording.txt", "a") as file:
        for key in keys:
            _key = str(key).replace("'", "")
            if _key.find("space") > 0:
                file.write("\n")
            elif _key.find("key") == -1:
                file.write(_key)

# Setup the listener threads
keyboard_listener = KeyboardListener(on_press=on_press, on_release=on_release)
mouse_listener = MouseListener(on_move=on_move, on_click=on_click, on_scroll=on_scroll)

# Start the threads and join them so the script doesn't end early
keyboard_listener.start()
mouse_listener.start()
keyboard_listener.join()
mouse_listener.join()


# see https://pythonhosted.org/pynput/ for details of the library
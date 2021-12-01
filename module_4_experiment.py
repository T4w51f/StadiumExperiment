import numpy as np
import os
import turtle
import time
import random
import pyaudio
import sys
import struct
from datetime import datetime

# Config

#make sure exactly one of these is true
IS_CONTROL_EXPERIMENT = True
IS_CHANT_EXP = False
IS_LVL_EXP = False # voice level exp

INITIAL_TAP_THRESHOLD = 0.010
FORMAT = pyaudio.paInt16 
SHORT_NORMALIZE = (1.0/32768.0)
CHANNELS = 2
RATE = 44100  
INPUT_BLOCK_TIME = 0.05
INPUT_FRAMES_PER_BLOCK = int(RATE*INPUT_BLOCK_TIME)
OVERSENSITIVE = 15.0/INPUT_BLOCK_TIME                    
UNDERSENSITIVE = 120.0/INPUT_BLOCK_TIME 
MAX_TAP_BLOCKS = 0.15/INPUT_BLOCK_TIME
pa = pyaudio.PyAudio()

# Background
screen = turtle.Screen()
screen.title("CPEN 441 Experiment")
screen.setup(width = 1.0, height = 1.0, startx=None, starty=None)
screen.bgcolor("black")
screen.tracer(0)
screen.bgpic('bgd.png')

f = open("distraction_data.txt", "a")
f.write(f'\nExperiment at {datetime.now()}\n')

def makeTurtle(shape, color, shapesizeX, shapesizeY, posX, posY):
    t = turtle.Turtle()
    t.speed(0)
    t.penup()
    t.shape(shape)
    t.pencolor("black")
    t.color(color)
    t.shapesize(shapesizeX, shapesizeY)
    t.setpos(posX, posY)
    return t
    
# Status
status = 0
status = turtle.Turtle()
status.speed(0)
status.penup()
status.hideturtle()
status.color("white")
status.goto(0, 330)
status.write("Press Enter to start", align="center", font=("Arial", 24, "normal"))

# grass = makeTurtle('square', 'green', 31, 50, -200, 50)
# track = makeTurtle('square', 'grey', 10, 50, -200, 50)
# start = makeTurtle('square', 'black', 10, 1, -640, 50)
# end = makeTurtle('square', 'black', 10, 1, 230, 50)

# Player Sprites
snail_red = 'snail_red.gif'
snail_blue = 'snail_blue.gif'

#heat map (50 in y moves 18 in image, bottom at -80)
heatmap = 'heatmap.gif'


screen.addshape(snail_red)
screen.addshape(snail_blue)
screen.addshape(heatmap)


p1 = makeTurtle(snail_red, 'red', 1, 1, -570, -20)
p2 = makeTurtle(snail_blue, 'blue', 1, 1, -530, 50)


if IS_LVL_EXP:
    # Audio bar player 1 and 2
    label1 = turtle.Turtle()
    label1.speed(0)
    label1.penup()
    label1.hideturtle()
    label1.color("white")
    label1.goto(-900, 280)
    label1.write("Team Red hype levels", font=("Arial", 18, "normal"))

    label2 = turtle.Turtle()
    label2.speed(0)
    label2.penup()
    label2.hideturtle()
    label2.color("white")
    label2.goto(300, 280)
    label2.write("Team Blue hype levels", font=("Arial", 18, "normal"))


    
    bar1 = makeTurtle(heatmap, 'white', 30, 9, -700, 50)
    bar2 = makeTurtle(heatmap, 'white', 30, 9, 350, 50)
    level1 = makeTurtle('square', 'red', 0.5, 1.7, -703, -70)
    level2 = makeTurtle('square', 'blue', 0.5, 1.7, 347, -70)
    level3 = makeTurtle('square', 'blue', 0.5, 1.7, 600, 230)

else:
    level1 = makeTurtle('square', 'red', 0.5, 1, 450, -145)
    level2 = makeTurtle('square', 'blue', 0.5, 1, 550, 0)
    level1.hideturtle()
    level2.hideturtle()


# RNG distractor
coor = [(-744, -354), (-744, 373), (729, -354), (729, 373)]
beep = makeTurtle('square', 'white', 1, 1, coor[0][0], coor[0][1])
beep.hideturtle()

screen.update()

def get_mouse_click_coor(x, y):
    print(x, y)
turtle.onscreenclick(get_mouse_click_coor)

p = pyaudio.PyAudio()

def get_rms( block ):
    count = len(block)/2
    format = "%dh"%(count)
    shorts = struct.unpack( format, block )

    np_arr = np.array([shorts])
    np_arr = np_arr * SHORT_NORMALIZE
    np_arr = np.square(np_arr)

    return 100 * np.sqrt(np.sum(np_arr) / count) / 0.4

def find_input_device():
    device_index = 19 # Hardcoded #NEED TO HARDOCDE
    return device_index

def open_mic_stream():
    device_index = find_input_device()

    stream = pa.open(format = FORMAT,
                    channels = CHANNELS,
                    rate = RATE,
                    input = True,
                    input_device_index = device_index,
                    frames_per_buffer = INPUT_FRAMES_PER_BLOCK)

    return stream

def updateBeep(coor, t, old):
    idx = random.randint(0, 3)
    
    while(old == idx):
        idx = random.randint(0, 3)

    x, y = coor[idx]
    t.setpos(x, y)
    return idx

user_timer_start = -1
def store_user_timer():
    global user_timer_start
    if(user_timer_start != -1):
        f.write(f'{(datetime.now() - user_timer_start).total_seconds()}\n')

started = False
def start_game():
    global started
    status.clear()
    started = True

screen.listen()
screen.onkey(store_user_timer, "space")
screen.onkey(start_game, "Return")

stream = open_mic_stream()
amplitude = 0
x1, y1 = p1.pos()
x2, y2 = p2.pos()
xl1, yl1 = level1.pos()
xl2, yl2 = level2.pos()

old = datetime.now()
new = datetime.now()
idx = 0
iteration = 0
num_shown = 0

while(x1 < 90 and x2 < 130):
    if(started):
        new = datetime.now()
        diff = (new - old).total_seconds()

        if(amplitude < 10):
            delX1 = 3
        elif(amplitude < 20):
            delX1 = 5
        elif(amplitude < 50):
            delX1 = 10
        elif(amplitude < 100):
            delX1 = 15
        else:
            delX1 = 20

        if IS_LVL_EXP:
            lvl_increase_1 = min(450,amplitude * 5)
            lvl_increase_2 = np.random.normal(230, max(0,50))
        else:
            lvl_increase_1 = 0
            lvl_increase_2 = 0


        level1.setpos(xl1, yl1 + lvl_increase_1)
        level2.setpos(xl2, yl2 + lvl_increase_2)

        p1.setpos(x1 + delX1, y1)
        p2.setpos(x2 + 10, y2)

        if(diff//3 == 1):
            old = new
            idx = updateBeep(coor, beep, idx)
            user_timer_start = datetime.now()
            beep.showturtle()
            num_shown+=1
            iteration = 0

        if(iteration == 3):
            beep.hideturtle()

        iteration += 1
        time.sleep(0.2)

        block = stream.read(INPUT_FRAMES_PER_BLOCK, exception_on_overflow = False)

        if IS_CONTROL_EXPERIMENT:
            amplitude = 0
        else:
            amplitude = get_rms(block)

        x1, y1 = p1.pos()
        x2, y2 = p2.pos()

        screen.update()
    
    else:
        screen.update()

p1.setpos(x1, y1)
p2.setpos(x2, y2)

if(x1 >= 90 and x2 >= 130):
    score_string = "It's a tie!"
elif(x1 >= 90):
    score_string = "Team 1 won!"
else:
    score_string = "Team 2 won!"

status.clear()
status.write(score_string, align="center", font=("Arial", 24, "normal"))
f.write(f"number of times shown : {num_shown}\n")
# screen.mainloop()

time.sleep(3)
f.write(f'Status: {score_string}\n')
f.close()

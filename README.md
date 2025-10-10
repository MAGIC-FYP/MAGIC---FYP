# MAGIC---FYP
Magnetic Automated Gantry for Intelligent Chess

This repository is used to share files pertaining to the Final Year Projects of Thomas Wildoer, Alex Whitfield, Finn Pickering, and Nathan Fiddes.
Nemai Karmakar oversees the project.

In a more general sense, the MAGIC project uses the chess example to show that a 2D gantry with an electromagnetic manipulator may be used in conjunction 
with sensors underneath a multi-purpose board to the effect of manipulating the pieces that sit on top.

The project requires expertise from the electrical, mechanical and software disciplines of engineering and thus will prove engaging, novel and fruitful
in showing the skills of the participants. Moreover, the project will be a first in the specific example space of self-playing board games - whilst similar
experiments have been done that incorporate elements of the proposed design, this will be the first of its kind to implement all the necessary design elements
into one unified product ('necessary' elements discussed at length further on). 

Should be noted that the inspiration for this project came from 'Harry Potter and the Philosopher's Stone', so note the references to it throughout the
project ;)


here is how to run this on th epi and see pygame

1. download real vnc to your local machine and make an acount

2. run this in terminal:
```
    sudo apt update
    sudo apt install xvfb x11vnc
```

3. then run this in terminal on the epi from inside the chess_sim file:
```
    # Start virtual framebuffer
    Xvfb :1 -screen 0 1024x768x24 &

    # Set display
    export DISPLAY=:1

    # Run your pygame app
    /usr/bin/python /home/magicpi/Desktop/MAGIC---FYP/src/chess_sim/main.py &

    # Start VNC server
    x11vnc -display :1 -nopw -listen localhost -xkb
    
```

4. on your computer run this in terminal, and enter the pwd raspberry:
    `ssh -L 5900:localhost:5900 magicpi@192.168.10.48`
    
5. open real VNC and connect to localhost:5900 

6. to close script mid run manualy run this on pi's terminal
    `pkill -f main.py`
#!/usr/bin/python3
#
# gui.py 
#
# Andrew Bishop
# 2022/08/03
#

import tkinter as tk
import time

# creates window object
root = tk.Tk()

# create a frame object
frame_1 = tk.Frame()
# add frame object to window
frame_1.pack()

frame_2 = tk.Frame()
frame_2.pack()

# creates label object
greeting = tk.Label(master=frame_1, text="Hello")
# adds label to window
greeting.pack()

greeting_2 = tk.Label(master=frame_2, text="World")
greeting_2.pack()



# main window loop
root.mainloop()

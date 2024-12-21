import Jetson.GPIO as GPIO
from PIL import Image, ImageSequence, ImageTk
import numpy as np
import time
import tkinter as tk

# Initialize GPIO
GPIO.setmode(GPIO.BOARD)
led_pins = [3, 5, 7, 8, 10, 11, 12, 13, 15, 16]  # Example GPIO pins
for pin in led_pins:
    GPIO.setup(pin, GPIO.OUT)

# Function to control LEDs
def set_leds(direction):
    if direction == "right":
        for pin in led_pins:
            GPIO.output(pin, GPIO.HIGH)
            time.sleep(0.1)
            GPIO.output(pin, GPIO.LOW)
    elif direction == "left":
        for pin in reversed(led_pins):
            GPIO.output(pin, GPIO.HIGH)
            time.sleep(0.1)
            GPIO.output(pin, GPIO.LOW)

# Function to apply vertical shear
def vertical_shear(image, shear_factor):
    width, height = image.size
    M = np.array([[1, shear_factor], [0, 1]])
    return image.transform((width, height), Image.AFFINE, data=M.flatten(), resample=Image.BICUBIC)

# Load GIF and apply shear transformation
def process_gif(gif_path, shear_factor):
    img = Image.open(gif_path)
    frames = []
    for frame in ImageSequence.Iterator(img):
        sheared = vertical_shear(frame, shear_factor)
        frames.append(sheared)
    return frames

# Initialize Tkinter
root = tk.Tk()
canvas = tk.Canvas(root, width=800, height=480)
canvas.pack()

# Load and process GIF
gif_path = "./cat-space.gif"
shear_right = process_gif(gif_path, 0.5)
shear_left = process_gif(gif_path, -0.5)

# Main loop
running = True
direction = "right"
frame_index = 0

def update_frame():
    global frame_index, direction
    if direction == "right":
        frame = shear_right[frame_index]
    else:
        frame = shear_left[frame_index]

    frame_index = (frame_index + 1) % len(shear_right)
    set_leds(direction)

    # Convert PIL image to Tkinter PhotoImage
    tk_image = ImageTk.PhotoImage(frame)
    
    # Update image on canvas
    canvas.create_image(0, 0, anchor=tk.NW, image=tk_image)
    canvas.image = tk_image  # Keep a reference to avoid garbage collection

    # Change direction every few seconds
    if frame_index == 0:
        direction = "left" if direction == "right" else "right"

    root.after(100, update_frame)  # Update frame every 100ms

# Start the main loop
root.after(0, update_frame)
root.mainloop()

# Cleanup
GPIO.cleanup()

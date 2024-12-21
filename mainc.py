import Jetson.GPIO as GPIO
from PIL import Image, ImageSequence, ImageTk
import numpy as np
import time
import tkinter as tk
import cupy as cp

# Initialize GPIO
GPIO.setmode(GPIO.BCM)
led_pins = [4, 17, 22, 10, 9, 11, 5, 6, 13, 19]  # Example GPIO pins
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
    try:
         M = cp.array([[1, shear_factor, 0], [0, 1, 0]], dtype=cp.float32)
        img_array = cp.array(image, dtype=cp.float32)
        sheared_img = cp.zeros_like(img_array)
        
        # CUDA kernel for affine transformation
        shear_kernel = cp.ElementwiseKernel(
            'float32 x, float32 y, float32 z',
            'float32 result',
            '''
            result = x * M[0, 0] + y * M[0, 1] + z * M[0, 2];
            result += x * M[1, 0] + y * M[1, 1] + z * M[1, 2];
            ''',
            'shear_kernel'
        )
        
        sheared_img = shear_kernel(img_array, M)
        return Image.fromarray(cp.asnumpy(sheared_img))
    except Exception as e:
        print(f"Error applying vertical shear: {e}")
        return image  # Return the original image if transformation fails
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
root.attributes('-fullscreen', True)  # Set window to fullscreen
canvas = tk.Canvas(root, width=root.winfo_screenwidth(), height=root.winfo_screenheight())
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

    # Resize the frame to fit the canvas
    frame = frame.resize((root.winfo_screenwidth(), root.winfo_screenheight()), Image.ANTIALIAS)

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

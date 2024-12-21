# signiot
Embedded control of an animated sign synchronized with an LED array

Install Necessary Libraries

You will need the following Python libraries:

Pillow for image processing.
pygame for displaying the GIF on the touchscreen.
Jetson.GPIO for controlling the LED array (This setup uses Jetson Nano, but code can be easily adapted to Raspberry Pi with "RPi.GPIO").
![setup](https://github.com/argus1/signiot/blob/main/SigniotSetup.png)
Install these using pip:

    pip install pillow pygame Jetson.GPIO TIME-python

signiot accomplishes the following tasks:

   1.  GPIO Initialization: Sets up the GPIO pins for the LED array.
   2.  LED Control Function: Lights up LEDs in sequence based on the direction.
   3.  Vertical Shear Function: Applies an affine transformation to shear the image vertically.
   4.  GIF Processing: Loads the GIF and applies the shear transformation to each frame.
   5.  Pygame Initialization: Sets up Pygame for displaying the GIF on the touchscreen.
   6.  Main Loop: Alternates the shear direction and displays the GIF frames, updating the LED array accordingly.

This script will continuously shear the GIF in both directions and update the LED array to indicate the current transformation direction.

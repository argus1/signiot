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
# def vertical_shear(image, shear_factor):
#     width, height = image.size
#     try:
#          M = cp.array([[1, shear_factor, 0], [0, 1, 0]], dtype=cp.float32)
#         img_array = cp.array(image, dtype=cp.float32)
#         sheared_img = cp.zeros_like(img_array)
        
#         # CUDA kernel for affine transformation
#         shear_kernel = cp.ElementwiseKernel(
#             'float32 x, float32 y, float32 z',
#             'float32 result',
#             '''
#             result = x * M[0, 0] + y * M[0, 1] + z * M[0, 2];
#             result += x * M[1, 0] + y * M[1, 1] + z * M[1, 2];
#             ''',
#             'shear_kernel'
#         )
        
#         sheared_img = shear_kernel(img_array, M)
#         return Image.fromarray(cp.asnumpy(sheared_img))
#     except Exception as e:
#         print(f"Error applying vertical shear: {e}")
#         return image  # Return the original image if transformation fails
def _get_npp_warp_affine():
    """
    Try to locate a usable NPP affine warp in cupyx.
    Returns (func, api_style) or (None, None).
    """
    try:
        import cupyx
    except Exception:
        return None, None

    # Newer CuPy: cupyx.npp.nppi.warp_affine / warpAffine
    try:
        nppi = cupyx.npp.nppi
        if hasattr(nppi, "warp_affine"):
            return nppi.warp_affine, "warp_affine"
        if hasattr(nppi, "warpAffine"):
            return nppi.warpAffine, "warpAffine"
    except Exception:
        pass

    # Older CuPy sometimes exposes npp module differently
    try:
        npp = cupyx.npp
        if hasattr(npp, "warp_affine"):
            return npp.warp_affine, "warp_affine"
    except Exception:
        pass

    return None, None


def vertical_shear_npp(image, shear_factor, interp="cubic"):
    """
    Apply vertical shear using CuPy + NPP.
    Returns a PIL Image.
    """
    width, height = image.size

    # PIL -> NumPy -> CuPy
    img_np = np.array(image)  # HxWxC
    img_cp = cp.asarray(img_np)

    # Build affine matrix (2x3) for shear
    # PIL used [[1, s, 0], [0, 1, 0]] (x' = x + s*y)
    M = cp.array([[1.0, shear_factor, 0.0],
                  [0.0, 1.0,       0.0]], dtype=cp.float32)

    # Locate NPP warp affine
    warp_fn, api_style = _get_npp_warp_affine()
    if warp_fn is None:
        raise RuntimeError("CuPy NPP warp_affine not found. Check CuPy build with NPP support.")

    # Interpolation selection (naming varies by CuPy)
    interp_mode = None
    try:
        import cupyx
        # Try common enum holders
        if hasattr(cupyx.npp, "NPP_INTERP_LINEAR"):
            interp_mode = cupyx.npp.NPP_INTERP_CUBIC if interp == "cubic" else cupyx.npp.NPP_INTERP_LINEAR
        elif hasattr(cupyx.npp, "InterpolationMode"):
            interp_mode = (cupyx.npp.InterpolationMode.CUBIC
                           if interp == "cubic" else cupyx.npp.InterpolationMode.LINEAR)
    except Exception:
        pass

    # Destination buffer
    dst_cp = cp.empty_like(img_cp)

    # Call NPP (API differs slightly across versions)
    if api_style in ("warp_affine", "warpAffine"):
        # Common signature patterns:
        # warp_affine(src, dst, matrix, interpolation=..., output_size=...)
        try:
            dst_cp = warp_fn(img_cp, dst_cp, M,
                             interpolation=interp_mode,
                             output_size=(height, width))
        except TypeError:
            # Alternate signature: warp_fn(src, matrix, output_size=..., interpolation=...)
            dst_cp = warp_fn(img_cp, M,
                             output_size=(height, width),
                             interpolation=interp_mode)
    else:
        raise RuntimeError("Unsupported NPP API style.")

    # CuPy -> NumPy -> PIL
    out_np = cp.asnumpy(dst_cp)
    return Image.fromarray(out_np)

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

# def update_frame():
#     global frame_index, direction
#     if direction == "right":
#         frame = shear_right[frame_index]
#     else:
#         frame = shear_left[frame_index]

#     frame_index = (frame_index + 1) % len(shear_right)
#     set_leds(direction)

#     # Resize the frame to fit the canvas
#     frame = frame.resize((root.winfo_screenwidth(), root.winfo_screenheight()), Image.ANTIALIAS)

#     # Convert PIL image to Tkinter PhotoImage
#     tk_image = ImageTk.PhotoImage(frame)
    
#     # Update image on canvas
#     canvas.create_image(0, 0, anchor=tk.NW, image=tk_image)
#     canvas.image = tk_image  # Keep a reference to avoid garbage collection

#     # Change direction every few seconds
#     if frame_index == 0:
#         direction = "left" if direction == "right" else "right"

#     root.after(100, update_frame)  # Update frame every 100ms

def resize_npp(image, out_w, out_h, interp="linear"):
    img_np = np.array(image)
    img_cp = cp.asarray(img_np)

    try:
        import cupyx
        resize_fn = None
        if hasattr(cupyx.npp.nppi, "resize"):
            resize_fn = cupyx.npp.nppi.resize
        elif hasattr(cupyx.npp, "resize"):
            resize_fn = cupyx.npp.resize
        if resize_fn is None:
            raise RuntimeError("NPP resize not found.")
    except Exception as e:
        raise RuntimeError(f"NPP resize unavailable: {e}")

    # Pick interpolation enum if available
    interp_mode = None
    try:
        if hasattr(cupyx.npp, "NPP_INTERP_LINEAR"):
            interp_mode = cupyx.npp.NPP_INTERP_LINEAR
        elif hasattr(cupyx.npp, "InterpolationMode"):
            interp_mode = cupyx.npp.InterpolationMode.LINEAR
    except Exception:
        pass

    # Destination buffer
    dst_cp = cp.empty((out_h, out_w, img_cp.shape[2]), dtype=img_cp.dtype)
    try:
        dst_cp = resize_fn(img_cp, dst_cp, interpolation=interp_mode)
    except TypeError:
        dst_cp = resize_fn(img_cp, out_size=(out_h, out_w), interpolation=interp_mode)

    return Image.fromarray(cp.asnumpy(dst_cp))

# Start the main loop
root.after(0, update_frame)
root.mainloop()

# Cleanup
GPIO.cleanup()

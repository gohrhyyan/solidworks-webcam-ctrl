import argparse
import math
import win32com.client as win32
import time

def connect_to_solidworks():
    while True:
        try:
            swApp = win32.Dispatch("SldWorks.Application")
            model = swApp.ActiveDoc
            if model is None:
                raise Exception("No active document in SolidWorks. Please open a model.")
            view = model.ActiveView
            if view is None:
                raise Exception("No active view found.")
            return swApp, model, view
        except Exception as e:
            print(f"Error connecting to SolidWorks: {e} \nRetrying in 5 seconds...")
            time.sleep(5)


def rotate_view(model, view, x_deg, y_deg):
    x_rad = math.radians(x_deg)
    y_rad = math.radians(y_deg)
    # Use RotateAboutCenter on the view directly (IModelView method)
    view.RotateAboutCenter(y_rad, x_rad)
    model.GraphicsRedraw2()

def zoom_view(model, view, factor):
    if not 0.0 < factor < 2.0:
        print("Zoom factor should be between 0.0 and 2.0")
        return
    # Note: SolidWorks API uses Scale2 for zoom; multiply current scale
    current_scale = view.Scale2
    view.Scale2 = current_scale * factor
    model.GraphicsRedraw2()

def pan_view(model, view, dx_pix, dy_pix):
    # Simple version: Assume dx_pix, dy_pix are in model units for X (horizontal), Y (vertical) screen directions
    # For pixel-based, compute model delta: e.g., model_per_pixel = (visible_max_x - visible_min_x) / window_width_pixels
    # But requires getting visible box and window size (via HWND)
    view.TranslateBy(dx_pix, dy_pix)  # Translates along screen X by dx, screen Y by dy in model units
    model.GraphicsRedraw2()
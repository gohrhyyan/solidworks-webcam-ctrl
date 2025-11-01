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

def pan_view(model, view, dx, dy):
    # Simplified pan using Translate (if available) or adjust translation
    swApp = win32.Dispatch("SldWorks.Application")
    swMath = swApp.GetMathUtility()
    
    # Create delta vector in screen space (pixels)
    delta_data = [dx, dy, 0]
    delta = swMath.CreateVector(delta_data)
    
    # Get current transform and translation
    transform = view.Transform
    inv_transform = transform.Inverse()
    
    # Transform delta to model space
    model_delta = delta.MultiplyTransform(inv_transform)
    
    # Scale by current view scale
    scale_factor = 1.0 / view.Scale2
    model_delta = model_delta.Scale(scale_factor)
    
    # Get current translation and add delta
    current_trans = view.Translation2
    current_data = current_trans.ArrayData
    delta_data = model_delta.ArrayData
    
    new_trans_data = [
        current_data[0] + delta_data[0],
        current_data[1] + delta_data[1],
        current_data[2] + delta_data[2]
    ]
    
    new_trans = swMath.CreateVector(new_trans_data)
    view.Translation2 = new_trans
    
    model.GraphicsRedraw2()
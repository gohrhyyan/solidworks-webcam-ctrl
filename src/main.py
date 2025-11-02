import cv2
import mediapipe as mp
import time
from pinch_detector import *
from sw_API import *
import time

ROTATION_SENSITIVITY = 200
PAN_SENSITIVITY = -0.25 

def detect_movement(detected_pinches, last_frame_detected_pinches):
    # Compare current detected pinches with last frame's to determine movement
    # Match by hand_id and calculate deltas
    movements = {}
    for hand_id, (x, y) in detected_pinches.items():
        if hand_id in last_frame_detected_pinches:
            last_x, last_y = last_frame_detected_pinches[hand_id]
            dx = x - last_x
            dy = y - last_y
            movements[hand_id] = (dx, dy)
    #print(f"movements detected: {movements}")
    return movements

def main():
    # connect to SolidWorks and get the application, model, and active view objects.
    swApp, model, view = connect_to_solidworks()
    # initialize the video capture object from the default camera (index 0).
    # this captures live video feed from the webcam.
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 426)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

    # initialize MediaPipe hands solution for hand landmark detection.
    hands_detector = mp.solutions.hands.Hands()

    # main processing loop: continuously capture and process video frames until interrupted.
    # this loop runs indefinitely, processing each frame for hand detection and visualization.
    last_pinches = []
    last_pinches_clear_counter = 0
    while True:
        # read a frame from the video capture.
        # success is a boolean indicating if the frame was read successfully, img is the BGR image frame.
        success, img = cap.read()

        # convert the BGR image to RGB format, as required by MediaPipe for processing.
        # cv2.cvtColor handles the color space conversion.
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # process the RGB image through the hands detection pipeline.
        # detection_result contains detected hand landmarks if any are found.
        detection_result = hands_detector.process(imgRGB)

        # multi_hand_landmarks is a collection of detected/tracked hands, where each hand is represented
        # as a list of 21 hand landmarks and each landmark is composed of x, y, and z coordinates.
        # x and y are normalized to [0.0, 1.0] by the image width and height respectively.
        # z represents the landmark depth with the depth at the wrist being the origin, and the smaller
        # the value the closer the landmark is to the camera. The magnitude of z uses roughly the same
        # scale as x.
        # (Up to 21 landmarks per hand, for multi_hand_landmarks[hand_id][landmark_id].x/y/z)

        # check if multiple hand landmarks are detected in the frame.
        # if true, iterate over each detected hand.
        if detection_result.multi_hand_landmarks:
            # loop over the hand landmarks for each hand in the detection_result.

            #detected pinches is a dictionary where keys are hand_ids and values are tuples (x, y) of normalized coordinates of the index finger tip
            pinches = detect_pinch(detection_result.multi_hand_landmarks)
            movements = detect_movement(pinches, last_pinches)

            if len(movements) == 1:  # Single hand for orbit
                hand_id, (dx, dy) = next(iter(movements.items()))  # Get the only movement
                # Simplified: Direct normalized-to-degrees scaling
                x_deg = dx * ROTATION_SENSITIVITY
                y_deg = dy * ROTATION_SENSITIVITY
                # Flip X for intuitive yaw
                x_deg = -x_deg
                #print(f"Rotating: x_deg={x_deg:.2f}, y_deg={y_deg:.2f}")
                rotate_view(model, view, x_deg, y_deg)

            elif len(movements) == 2:  # Dual hands for pan
                movements_list = list(movements.values())
                dx1, dy1 = movements_list[0]
                dx2, dy2 = movements_list[1]
                avg_dx = (dx1 + dx2) / 2
                avg_dy = (dy1 + dy2) / 2
                dx_pix = avg_dx * PAN_SENSITIVITY
                dy_pix = avg_dy * PAN_SENSITIVITY
                pan_view(model, view, dx_pix, dy_pix)

            for hand_landmarks in detection_result.multi_hand_landmarks:
                # draw the hand landmarks and connections on the original BGR image.
                # mpHands.HAND_CONNECTIONS defines the lines between landmarks (e.g., finger joints).
                mp.solutions.drawing_utils.draw_landmarks(img, hand_landmarks, mp.solutions.hands.HAND_CONNECTIONS)
            
            if pinches:
                last_pinches = pinches
                last_pinches_clear_counter = 0
            
            #clear after 5 frames of no pinches detected
            if not pinches and last_pinches_clear_counter > 5:
                last_pinches = {}
                last_pinches_clear_counter = 0
            
        # display the processed image in a window titled "Image".
        cv2.imshow("Image", img)
        # wait for 1ms
        cv2.waitKey(16)  # ~60 FPS

        last_pinches_clear_counter += 1


if __name__ == "__main__":
    main()
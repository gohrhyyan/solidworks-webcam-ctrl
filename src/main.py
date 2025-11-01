import cv2
import mediapipe as mp
import time
from pinch_detector import *
import time

# initialize the video capture object from the default camera (index 0).
# this captures live video feed from the webcam.
cap = cv2.VideoCapture(0)

# initialize MediaPipe hands solution for hand landmark detection.
hands_detector = mp.solutions.hands.Hands()

# main processing loop: continuously capture and process video frames until interrupted.
# this loop runs indefinitely, processing each frame for hand detection and visualization.
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

        # detected pinches is a list of tuples (hand_id, x, y) where x,y are normalized coordinates of the index finger tip
        detected_pinches = detect_pinch(detection_result.multi_hand_landmarks)

        for hand_landmarks in detection_result.multi_hand_landmarks:
            # draw the hand landmarks and connections on the original BGR image.
            # mpHands.HAND_CONNECTIONS defines the lines between landmarks (e.g., finger joints).
            mp.solutions.drawing_utils.draw_landmarks(img, hand_landmarks, mp.solutions.hands.HAND_CONNECTIONS)
            
    # display the processed image in a window titled "Image".
    cv2.imshow("Image", img)
    # wait for 1ms
    cv2.waitKey(1)
# Threshold multiplier for pinch detection: Determines the maximum allowed distance between thumb tip and index tip,
# normalized relative to the squared length of the thumb's distal phalanx (tip to PIP joint). 
# A value of 1.0 means the tips must be no farther apart than the thumb segment length itself for a pinch to be detected.
# Values <1.0 decreases sensitivity (requires closer pinches); >1.0 increases it (allows looser pinches).
PINCH_THRESHOLD = 1  # Adjust this value as needed

#multi_hand_landmarks: list of hand landmarks detected by MediaPipe Hands. Structure: multi_hand_landmarks[hand_id][landmark_id].x/y/z
def detect_pinch(multi_hand_landmarks):
    num_pinches = 0
    pinches = {}

    # iterate over each detected hand 
    for hand_id, hand_landmarks in enumerate(multi_hand_landmarks):
    # Pinch detection: Get thumb tip (4), thumb PIP (3), and index tip (8)
        thumb_tip = hand_landmarks.landmark[4]      # Thumb tip
        thumb_pip = hand_landmarks.landmark[3]      # Thumb proximal interphalangeal joint
        index_tip = hand_landmarks.landmark[8]      # Index finger tip

        # Calculate squared thumb segment length (normalized)
        thumb_tip_pip_dx = thumb_tip.x - thumb_pip.x
        thumb_tip_pip_dy = thumb_tip.y - thumb_pip.y
        thumb_tip_pip_length_squared = thumb_tip_pip_dx * thumb_tip_pip_dx + thumb_tip_pip_dy * thumb_tip_pip_dy

        # Calculate squared Euclidean distance between thumb and index tips (normalized)
        thumb_index_tip_dx = index_tip.x - thumb_tip.x
        thumb_index_tip_dy = index_tip.y - thumb_tip.y
        thumb_index_tip_squared_dist = thumb_index_tip_dx * thumb_index_tip_dx + thumb_index_tip_dy * thumb_index_tip_dy

        # Check for pinch (sets bool state)
        if thumb_index_tip_squared_dist < thumb_tip_pip_length_squared * PINCH_THRESHOLD:
            pinches[hand_id] = (index_tip.x, index_tip.y)

    #print (f"pinches detected {pinches})")
    return pinches

#detected pinches is a dictionary where keys are hand_ids and values are tuples (x, y) of normalized coordinates of the index finger tip

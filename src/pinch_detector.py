# Pinch detection threshold (relative to thumb distal phalanx length) - tune based on anatomy
PINCH_THRESHOLD = 1  # length of thumb segment; start here, adjust 0.2-0.5 for pinch sensitivity
PINCH_THRESHOLD_SQUARED = PINCH_THRESHOLD ** 2  # Pre-compute once

def detect_pinch(multi_hand_landmarks):
    num_pinches = 0
    for hand_landmarks in multi_hand_landmarks:
    # Pinch detection: Get thumb tip (4), thumb PIP (3), and index tip (8)
        thumb_tip = hand_landmarks.landmark[4]      # Thumb tip
        thumb_pip = hand_landmarks.landmark[3]      # Thumb proximal interphalangeal joint
        index_tip = hand_landmarks.landmark[8]      # Index finger tip

        # Calculate squared thumb segment length (normalized)
        thumb_dx = thumb_tip.x - thumb_pip.x
        thumb_dy = thumb_tip.y - thumb_pip.y
        thumb_length_squared = thumb_dx*thumb_dx + thumb_dy*thumb_dy

        # Calculate squared Euclidean distance between thumb and index tips (normalized)
        tip_dx = index_tip.x - thumb_tip.x
        tip_dy = index_tip.y - thumb_tip.y
        tip_squared_dist = tip_dx*tip_dx + tip_dy*tip_dy

        # Normalize: relative squared distance
        if thumb_length_squared > 0:  # Avoid div-by-zero (rare, if hand flat)
            normalized_squared_dist = tip_squared_dist / thumb_length_squared
        else:
            normalized_squared_dist = float('inf')  # No pinch if degenerate

        # Check for pinch (sets bool state)
        if normalized_squared_dist < PINCH_THRESHOLD_SQUARED:
            num_pinches += 1
    print (f"pinches detected {num_pinches}")
    return(num_pinches)
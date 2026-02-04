import cv2
import mediapipe as mp
import numpy as np
import time
from sw_API import connect_to_solidworks, rotate_view, zoom_view, pan_view

# ──────────────────────────────────────────────
# Config / constants (tuned for speed + your logic)
# ──────────────────────────────────────────────
ROTATION_SENSITIVITY = 300.0
PAN_SENSITIVITY      = -0.5
ZOOM_THRESHOLD       = 0.025

# Legacy Hands options – big wins for speed
MODEL_COMPLEXITY     = 0          # 0 = lite model → much faster
MAX_NUM_HANDS        = 2
MIN_DETECTION_CONF   = 0.45
MIN_TRACKING_CONF    = 0.45

PREVIEW_ENABLED      = True

# Threshold multiplier for pinch detection: Determines the maximum allowed distance between thumb tip and index tip,
# normalized relative to the squared length of the thumb's distal phalanx (tip to PIP joint). 
# A value of 1.0 means the tips must be no farther apart than the thumb segment length itself for a pinch to be detected.
# Values <1.0 decreases sensitivity (requires closer pinches); >1.0 increases it (allows looser pinches).
PINCH_THRESHOLD = 1.5  # Adjust this value as needed

# ──────────────────────────────────────────────
# Landmark indices we care about
IDX_THUMB_TIP  = 4
IDX_THUMB_PIP  = 3
IDX_INDEX_TIP  = 8

NEEDED_INDICES = [IDX_THUMB_TIP, IDX_THUMB_PIP, IDX_INDEX_TIP]


def extract_key_landmarks(multi_hand_landmarks):
    """Return (n_hands × 3 × 2) array: [hand, point, xy] normalized"""
    if not multi_hand_landmarks:
        return np.empty((0, 3, 2), dtype=np.float32)

    arr = np.array([
        np.array([[lm.x, lm.y] for lm in hand_landmarks.landmark])[NEEDED_INDICES]
        for hand_landmarks in multi_hand_landmarks
    ])  # shape → (n_hands, 3, 2)

    return arr


def detect_pinches_vectorized(key_points):
    """
    key_points : (n_hands, 3, 2)  [thumb_tip, thumb_pip, index_tip]
    Returns dict {hand_id: (x,y)} of index tip when pinch detected
    """
    if key_points.shape[0] == 0:
        return {}

    thumb_tip   = key_points[:, 0]     # (n,2)
    thumb_pip   = key_points[:, 1]
    index_tip   = key_points[:, 2]

    # squared length thumb segment
    thumb_len_sq = np.sum((thumb_tip - thumb_pip)**2, axis=1)   # (n,)

    # squared dist thumb_tip ↔ index_tip
    dist_sq = np.sum((index_tip - thumb_tip)**2, axis=1)        # (n,)

    is_pinch = dist_sq < thumb_len_sq * PINCH_THRESHOLD

    pinches = {}
    for i in np.flatnonzero(is_pinch):
        x, y = index_tip[i]
        pinches[i] = (x, y)   # hand_id = index in this frame's list

    return pinches


# ──────────────────────────────────────────────
def main():
    swApp, model, view = connect_to_solidworks()

    cap = cv2.VideoCapture(0)
    #cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)

    # ── Legacy Hands solution ──
    mp_hands = mp.solutions.hands

    hands_detector = mp_hands.Hands(
        static_image_mode=False,                # video stream → use tracking
        max_num_hands=MAX_NUM_HANDS,
        #model_complexity=MODEL_COMPLEXITY,      # 0 = lite → fastest
        min_detection_confidence=MIN_DETECTION_CONF,
        min_tracking_confidence=MIN_TRACKING_CONF
    )

    drawing_utils = mp.solutions.drawing_utils   # only used if preview on

    last_pinches = {}
    last_pinches_clear_counter = 0

    zoom_active  = False
    zoom_counter = 0

    while True:
        success, img = cap.read()
        if not success:
            break

        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # ── Process with legacy API ──
        results = hands_detector.process(imgRGB)

        # ── Early exit if no hands ──
        if not results.multi_hand_landmarks:
            last_pinches_clear_counter += 1
            if last_pinches_clear_counter > 5:
                last_pinches = {}
                last_pinches_clear_counter = 0

            zoom_active = False
            zoom_counter = 0

            if PREVIEW_ENABLED:
                cv2.imshow("Image", img)
            cv2.waitKey(1)
            continue

        # ── Extract only needed landmarks ──
        key_points = extract_key_landmarks(results.multi_hand_landmarks)

        pinches = detect_pinches_vectorized(key_points)

        # ── Compute movements (only for pinched hands that existed last frame) ──
        movements = {}
        for hid, (x, y) in pinches.items():
            if hid in last_pinches:
                lx, ly = last_pinches[hid]
                movements[hid] = (x - lx, y - ly)

        n_mov = len(movements)

        if n_mov == 1:
            # ── Single hand orbit ──
            dx, dy = next(iter(movements.values()))
            x_deg = dx * ROTATION_SENSITIVITY * -1
            y_deg = dy * ROTATION_SENSITIVITY
            rotate_view(view, x_deg, y_deg)
            model.GraphicsRedraw2()

        elif n_mov >= 2:
            # ── Dual-hand pan/zoom ──
            hand_ids = list(pinches.keys())[:2]  # take first two
            p1 = np.array(pinches[hand_ids[0]])
            p2 = np.array(pinches[hand_ids[1]])

            p1_last = np.array(last_pinches[hand_ids[0]])
            p2_last = np.array(last_pinches[hand_ids[1]])

            curr_dist = np.linalg.norm(p2 - p1)
            last_dist = np.linalg.norm(p2_last - p1_last)
            delta_dist = abs(curr_dist - last_dist)

            if zoom_active:
                zoom_factor = curr_dist/last_dist
                zoom_view(view, zoom_factor)
                model.GraphicsRedraw2()
                zoom_counter += 1
                if zoom_counter >= 10:
                    zoom_active = False
            else:
                if delta_dist > ZOOM_THRESHOLD:
                    zoom_active = True
                    zoom_counter = 0
                    zoom_factor = curr_dist/last_dist
                    zoom_view(view, zoom_factor)
                    model.GraphicsRedraw2()
                else:
                    # Pan: average delta
                    m1 = np.array(movements[hand_ids[0]])
                    m2 = np.array(movements[hand_ids[1]])
                    avg_m = (m1 + m2) / 2
                    dx_pix = avg_m[0] * PAN_SENSITIVITY
                    dy_pix = avg_m[1] * PAN_SENSITIVITY
                    pan_view(view, dx_pix, dy_pix)
                    model.GraphicsRedraw2()

        # ── State updates ──
        if len(pinches) < 2:
            zoom_active = False
            zoom_counter = 0

        if pinches:
            last_pinches = pinches.copy()
            last_pinches_clear_counter = 0
        else:
            last_pinches_clear_counter += 1
            if last_pinches_clear_counter > 5:
                last_pinches = {}
                last_pinches_clear_counter = 0

        # ── Optional minimal preview ──
        if PREVIEW_ENABLED:
            for hand_lm in results.multi_hand_landmarks:
                drawing_utils.draw_landmarks(
                    img, hand_lm, mp_hands.HAND_CONNECTIONS,
                    landmark_drawing_spec=None  # skip dots for speed
                )
            cv2.imshow("Image", img)

        cv2.waitKey(1)  # non-blocking

    cap.release()
    if PREVIEW_ENABLED:
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
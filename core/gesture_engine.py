import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import time

# Safety setting
pyautogui.FAILSAFE = False

# Initialize MediaPipe
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.85,
    min_tracking_confidence=0.85
)
mp_draw = mp.solutions.drawing_utils

# Screen dimensions
screen_w, screen_h = pyautogui.size()

# Camera dimensions
cam_w, cam_h = 640, 480

# Smoothing variables
prev_x, prev_y = 0, 0
smoothing = 7

# Click variables
click_threshold = 40
last_click_time = 0
click_cooldown = 0.8

# Scroll variables
last_scroll_time = 0
scroll_cooldown = 0.3

# Open webcam
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, cam_w)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cam_h)

print("VOXIS Gesture Engine - ACTIVE")
print("Point finger  → Move cursor")
print("Pinch         → Click")
print("Two fingers   → Scroll")
print("Press ESC     → Quit")

while True:
    success, frame = cap.read()
    if not success:
        continue

    # Flip frame - mirror effect
    frame = cv2.flip(frame, 1)

    # Convert to RGB for MediaPipe
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:

            # Draw hand skeleton
            mp_draw.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS
            )

            landmarks = hand_landmarks.landmark
            h, w, _ = frame.shape

            # Key landmark positions
            # 8  = Index fingertip
            # 4  = Thumb tip
            # 12 = Middle fingertip
            # 5  = Index base
            # 9  = Middle base
            index_tip_x = int(landmarks[8].x * w)
            index_tip_y = int(landmarks[8].y * h)
            thumb_tip_x = int(landmarks[4].x * w)
            thumb_tip_y = int(landmarks[4].y * h)
            middle_tip_y = int(landmarks[12].y * h)
            index_base_y = int(landmarks[5].y * h)
            middle_base_y = int(landmarks[9].y * h)

            # Finger extended checks
            # If tip is above base = finger extended
            index_extended = index_tip_y < index_base_y
            middle_extended = middle_tip_y < middle_base_y

            # Map camera to screen coordinates
            screen_x = np.interp(
                index_tip_x, [0, w], [0, screen_w]
            )
            screen_y = np.interp(
                index_tip_y, [0, h], [0, screen_h]
            )

            # Smooth cursor
            smooth_x = prev_x + (screen_x - prev_x) / smoothing
            smooth_y = prev_y + (screen_y - prev_y) / smoothing
            prev_x, prev_y = smooth_x, smooth_y

            # Calculate pinch distance
            pinch_distance = np.sqrt(
                (index_tip_x - thumb_tip_x) ** 2 +
                (index_tip_y - thumb_tip_y) ** 2
            )

            current_time = time.time()

            # GESTURE 1 — PINCH = CLICK
            # Only index extended + pinch detected
            if pinch_distance < click_threshold:
                if current_time - last_click_time > click_cooldown:
                    pyautogui.click()
                    last_click_time = current_time
                    cv2.putText(
                        frame, "CLICK!",
                        (10, 90),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1, (0, 0, 255), 2
                    )

            # GESTURE 2 — TWO FINGERS = SCROLL
            # Index AND middle both extended
            elif index_extended and middle_extended:
                if current_time - last_scroll_time > scroll_cooldown:
                    # Hand in upper half = scroll up
                    if index_tip_y < h // 2:
                        pyautogui.scroll(3)
                        cv2.putText(
                            frame, "SCROLL UP",
                            (10, 90),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            1, (255, 255, 0), 2
                        )
                    # Hand in lower half = scroll down
                    else:
                        pyautogui.scroll(-3)
                        cv2.putText(
                            frame, "SCROLL DOWN",
                            (10, 90),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            1, (255, 255, 0), 2
                        )
                    last_scroll_time = current_time

            # GESTURE 3 — ONE FINGER = MOVE CURSOR
            elif index_extended and not middle_extended:
                pyautogui.moveTo(int(smooth_x), int(smooth_y))
                cv2.putText(
                    frame, "CURSOR MOVE",
                    (10, 90),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1, (0, 255, 0), 2
                )

            # Always show VOXIS status
            cv2.putText(
                frame, "VOXIS ACTIVE",
                (10, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1, (0, 255, 0), 2
            )

    # Show camera window
    cv2.imshow("VOXIS - Gesture Engine", frame)


    key = cv2.waitKey(1) & 0xFF
    if key == 27 or key == ord('q'):
        print("VOXIS Gesture Engine - STOPPED")
        break

    

cap.release()
cv2.destroyAllWindows()
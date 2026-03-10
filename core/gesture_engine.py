import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import time

pyautogui.FAILSAFE = False

class GestureEngine:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.85,
            min_tracking_confidence=0.85
        )
        self.mp_draw = mp.solutions.drawing_utils
        self.screen_w, self.screen_h = pyautogui.size()
        self.cam_w, self.cam_h = 640, 480
        self.prev_x, self.prev_y = 0, 0
        self.smoothing = 7
        self.click_threshold = 40
        self.last_click_time = 0
        self.click_cooldown = 0.8
        self.last_scroll_time = 0
        self.scroll_cooldown = 0.3
        print("VOXIS Gesture Engine - Initialized")

    def run(self):
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.cam_w)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.cam_h)

        print("VOXIS Gesture Engine - ACTIVE")
        print("Point finger  → Move cursor")
        print("Pinch         → Click")
        print("Two fingers   → Scroll")
        print("Press ESC     → Quit")

        while True:
            success, frame = cap.read()
            if not success:
                continue

            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(rgb_frame)

            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    self.mp_draw.draw_landmarks(
                        frame,
                        hand_landmarks,
                        self.mp_hands.HAND_CONNECTIONS
                    )

                    landmarks = hand_landmarks.landmark
                    h, w, _ = frame.shape

                    index_tip_x = int(landmarks[8].x * w)
                    index_tip_y = int(landmarks[8].y * h)
                    thumb_tip_x = int(landmarks[4].x * w)
                    thumb_tip_y = int(landmarks[4].y * h)
                    middle_tip_y = int(landmarks[12].y * h)
                    index_base_y = int(landmarks[5].y * h)
                    middle_base_y = int(landmarks[9].y * h)

                    index_extended = index_tip_y < index_base_y
                    middle_extended = middle_tip_y < middle_base_y

                    screen_x = np.interp(
                        index_tip_x, [0, w], [0, self.screen_w]
                    )
                    screen_y = np.interp(
                        index_tip_y, [0, h], [0, self.screen_h]
                    )

                    smooth_x = self.prev_x + (screen_x - self.prev_x) / self.smoothing
                    smooth_y = self.prev_y + (screen_y - self.prev_y) / self.smoothing
                    self.prev_x, self.prev_y = smooth_x, smooth_y

                    pinch_distance = np.sqrt(
                        (index_tip_x - thumb_tip_x) ** 2 +
                        (index_tip_y - thumb_tip_y) ** 2
                    )

                    current_time = time.time()

                    if pinch_distance < self.click_threshold:
                        if current_time - self.last_click_time > self.click_cooldown:
                            pyautogui.click()
                            self.last_click_time = current_time
                            cv2.putText(frame, "CLICK!", (10, 90),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

                    elif index_extended and middle_extended:
                        if current_time - self.last_scroll_time > self.scroll_cooldown:
                            if index_tip_y < h // 2:
                                pyautogui.scroll(3)
                                cv2.putText(frame, "SCROLL UP", (10, 90),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
                            else:
                                pyautogui.scroll(-3)
                                cv2.putText(frame, "SCROLL DOWN", (10, 90),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
                            self.last_scroll_time = current_time

                    elif index_extended and not middle_extended:
                        pyautogui.moveTo(int(smooth_x), int(smooth_y))
                        cv2.putText(frame, "CURSOR MOVE", (10, 90),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                    cv2.putText(frame, "VOXIS ACTIVE", (10, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            cv2.imshow("VOXIS - Gesture Engine", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == 27 or key == ord('q'):
                print("VOXIS Gesture Engine - STOPPED")
                break

        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    engine = GestureEngine()
    engine.run()
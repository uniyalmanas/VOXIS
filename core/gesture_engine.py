import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import time

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0

class GestureEngine:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7,
            model_complexity=0  # fastest model
        )
        self.mp_draw = mp.solutions.drawing_utils
        self.screen_w, self.screen_h = pyautogui.size()
        self.cam_w, self.cam_h = 640, 480

        # Cursor smoothing
        self.prev_x, self.prev_y = 0, 0
        self.smoothing = 4  # lower = faster response

        # Gesture margins — active zone inside camera
        self.margin = 0.1  # 10% margin on each side

        # Cooldowns
        self.last_click_time = 0
        self.click_cooldown = 0.5
        self.last_scroll_time = 0
        self.scroll_cooldown = 0.15
        self.last_gesture_time = 0
        self.gesture_cooldown = 0.8

        # Thresholds
        self.click_threshold = 35
        self.pinch_threshold = 35

        # State tracking
        self.prev_gesture = None
        self.gesture_hold_start = 0
        self.fist_start_time = 0
        self.is_dragging = False

        print("VOXIS Gesture Engine - Initialized")

    def get_landmarks(self, hand_landmarks, w, h):
        """Extract all key landmark positions"""
        lm = hand_landmarks.landmark
        def pt(idx):
            return int(lm[idx].x * w), int(lm[idx].y * h)

        return {
            'wrist':        pt(0),
            'thumb_tip':    pt(4),
            'thumb_ip':     pt(3),
            'index_tip':    pt(8),
            'index_mid':    pt(7),
            'index_base':   pt(5),
            'middle_tip':   pt(12),
            'middle_base':  pt(9),
            'ring_tip':     pt(16),
            'ring_base':    pt(13),
            'pinky_tip':    pt(20),
            'pinky_base':   pt(17),
        }

    def finger_extended(self, tip, base):
        """Check if finger is extended"""
        return tip[1] < base[1] - 15

    def distance(self, p1, p2):
        """Distance between two points"""
        return np.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)

    def detect_gesture(self, lm):
        """Detect which gesture is being made"""
        index_up  = self.finger_extended(lm['index_tip'], lm['index_base'])
        middle_up = self.finger_extended(lm['middle_tip'], lm['middle_base'])
        ring_up   = self.finger_extended(lm['ring_tip'], lm['ring_base'])
        pinky_up  = self.finger_extended(lm['pinky_tip'], lm['pinky_base'])

        pinch_dist   = self.distance(lm['index_tip'], lm['thumb_tip'])
        middle_pinch = self.distance(lm['middle_tip'], lm['thumb_tip'])

        fingers_up = sum([index_up, middle_up, ring_up, pinky_up])

        # PINCH → Left Click
        if pinch_dist < self.click_threshold:
            return "PINCH"

        # MIDDLE PINCH → Right Click
        if middle_pinch < self.click_threshold and not index_up:
            return "RIGHT_CLICK"

        # ONE FINGER → Move cursor
        if index_up and not middle_up and not ring_up and not pinky_up:
            return "CURSOR"

        # TWO FINGERS → Scroll
        if index_up and middle_up and not ring_up and not pinky_up:
            return "SCROLL"

        # THREE FINGERS → Screenshot
        if index_up and middle_up and ring_up and not pinky_up:
            return "SCREENSHOT"

        # FOUR FINGERS → Switch tab
        if index_up and middle_up and ring_up and pinky_up:
            return "SWITCH_TAB"

        # FIST → Stop/pause media
        if fingers_up == 0:
            return "FIST"

        return "NONE"

    def run(self):
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.cam_w)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.cam_h)
        cap.set(cv2.CAP_PROP_FPS, 30)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # reduces lag

        print("VOXIS Gesture Engine - ACTIVE")
        print("☝️  One finger    → Move cursor")
        print("🤏 Pinch          → Left click")
        print("✌️  Two fingers   → Scroll")
        print("🤟 Three fingers  → Screenshot")
        print("🖖 Four fingers   → Switch tab")
        print("✊ Fist           → Pause/Play")
        print("Press ESC        → Quit")

        while True:
            success, frame = cap.read()
            if not success:
                continue

            # Flip and process
            frame = cv2.flip(frame, 1)
            h, w, _ = frame.shape

            # Convert to RGB for MediaPipe
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            rgb_frame.flags.writeable = False
            results = self.hands.process(rgb_frame)
            rgb_frame.flags.writeable = True

            current_time = time.time()

            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    # Draw landmarks
                    self.mp_draw.draw_landmarks(
                        frame,
                        hand_landmarks,
                        self.mp_hands.HAND_CONNECTIONS,
                        self.mp_draw.DrawingSpec(
                            color=(0, 255, 0),
                            thickness=2,
                            circle_radius=3
                        ),
                        self.mp_draw.DrawingSpec(
                            color=(0, 200, 255),
                            thickness=2
                        )
                    )

                    lm = self.get_landmarks(hand_landmarks, w, h)
                    gesture = self.detect_gesture(lm)

                    # Cursor mapping with margins
                    index_x = lm['index_tip'][0]
                    index_y = lm['index_tip'][1]

                    screen_x = np.interp(
                        index_x,
                        [w * self.margin, w * (1 - self.margin)],
                        [0, self.screen_w]
                    )
                    screen_y = np.interp(
                        index_y,
                        [h * self.margin, h * (1 - self.margin)],
                        [0, self.screen_h]
                    )

                    # Smooth cursor
                    smooth_x = self.prev_x + (screen_x - self.prev_x) / self.smoothing
                    smooth_y = self.prev_y + (screen_y - self.prev_y) / self.smoothing
                    self.prev_x, self.prev_y = smooth_x, smooth_y

                    # Execute gestures
                    if gesture == "CURSOR":
                        pyautogui.moveTo(int(smooth_x), int(smooth_y))
                        self._show_status(frame, "MOVE", (0, 255, 0))

                    elif gesture == "PINCH":
                        if current_time - self.last_click_time > self.click_cooldown:
                            pyautogui.click()
                            self.last_click_time = current_time
                            self._show_status(frame, "CLICK", (0, 0, 255))

                    elif gesture == "RIGHT_CLICK":
                        if current_time - self.last_click_time > self.click_cooldown:
                            pyautogui.rightClick()
                            self.last_click_time = current_time
                            self._show_status(frame, "RIGHT CLICK", (255, 0, 0))

                    elif gesture == "SCROLL":
                        if current_time - self.last_scroll_time > self.scroll_cooldown:
                            if index_y < h // 2:
                                pyautogui.scroll(5)
                                self._show_status(frame, "SCROLL UP", (255, 255, 0))
                            else:
                                pyautogui.scroll(-5)
                                self._show_status(frame, "SCROLL DOWN", (255, 200, 0))
                            self.last_scroll_time = current_time

                    elif gesture == "SCREENSHOT":
                        if current_time - self.last_gesture_time > self.gesture_cooldown:
                            import datetime, os
                            filename = f"screenshot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                            path = os.path.join(os.path.expanduser("~"), "Pictures", filename)
                            os.makedirs(os.path.dirname(path), exist_ok=True)
                            pyautogui.screenshot(path)
                            self.last_gesture_time = current_time
                            self._show_status(frame, "SCREENSHOT!", (255, 0, 255))
                            print(f"Screenshot saved: {path}")

                    elif gesture == "SWITCH_TAB":
                        if current_time - self.last_gesture_time > self.gesture_cooldown:
                            pyautogui.hotkey('ctrl', 'tab')
                            self.last_gesture_time = current_time
                            self._show_status(frame, "NEXT TAB", (0, 255, 255))

                    elif gesture == "FIST":
                        if current_time - self.last_gesture_time > self.gesture_cooldown:
                            pyautogui.press('space')
                            self.last_gesture_time = current_time
                            self._show_status(frame, "PLAY/PAUSE", (255, 128, 0))

                    # Show gesture name
                    cv2.putText(frame, f"Gesture: {gesture}",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                        0.7, (255, 255, 255), 2)

            else:
                cv2.putText(frame, "No hand detected",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                    0.7, (100, 100, 100), 2)
 
            # VOXIS branding
            cv2.putText(frame, "VOXIS",
                (w - 100, 30), cv2.FONT_HERSHEY_SIMPLEX,
                0.8, (0, 255, 0), 2)

            cv2.imshow("VOXIS - Gesture Engine", frame)

            key = cv2.waitKey (1) & 0xFF
            if key == 27 or key == ord('q'):
                print("VOXIS Gesture Engine - STOPPED")
                break

        cap.release()
        cv2.destroyAllWindows()

    def _show_status(self, frame, text, color):
        cv2.putText(frame, text,
            (10, 90), cv2.FONT_HERSHEY_SIMPLEX,
            1.2, color, 3)

if __name__ == "__main__":
    engine = GestureEngine()
    engine.run()
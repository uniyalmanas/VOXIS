import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import time
import datetime
import os

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
            model_complexity=0
        )
        self.mp_draw = mp.solutions.drawing_utils
        self.screen_w, self.screen_h = pyautogui.size()
        self.cam_w, self.cam_h = 640, 480

        # Cursor smoothing
        self.prev_x, self.prev_y = 0, 0
        self.smoothing = 4
        self.margin = 0.1

        # Cooldowns
        self.last_click_time = 0
        self.click_cooldown = 0.5
        self.last_scroll_time = 0
        self.scroll_cooldown = 0.15
        self.last_gesture_time = 0
        self.gesture_cooldown = 0.8

        # Thresholds
        self.click_threshold = 35

        # Drag state
        self.is_dragging = False
        self.pinch_start_time = 0
        self.pinch_start_pos = (0, 0)
        self.drag_threshold = 0.3

        # ACTIVATION STATE
        self.is_active = False
        self.last_hand_time = time.time()
        self.auto_deactivate_timeout = 5.0

        # Palm detection
        self.palm_start_time = 0
        self.palm_hold_required = 1.0
        self.last_toggle_time = 0
        self.toggle_cooldown = 1.5

        print("VOXIS Gesture Engine - Initialized")

    def get_landmarks(self, hand_landmarks, w, h):
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
        return tip[1] < base[1] - 15

    def distance(self, p1, p2):
        return np.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)

    def is_open_palm(self, lm):
        """All 4 fingers extended = open palm"""
        index_up  = self.finger_extended(lm['index_tip'],  lm['index_base'])
        middle_up = self.finger_extended(lm['middle_tip'], lm['middle_base'])
        ring_up   = self.finger_extended(lm['ring_tip'],   lm['ring_base'])
        pinky_up  = self.finger_extended(lm['pinky_tip'],  lm['pinky_base'])
        return index_up and middle_up and ring_up and pinky_up

    def detect_gesture(self, lm):
        index_up  = self.finger_extended(lm['index_tip'],  lm['index_base'])
        middle_up = self.finger_extended(lm['middle_tip'], lm['middle_base'])
        ring_up   = self.finger_extended(lm['ring_tip'],   lm['ring_base'])
        pinky_up  = self.finger_extended(lm['pinky_tip'],  lm['pinky_base'])

        pinch_dist   = self.distance(lm['index_tip'], lm['thumb_tip'])
        middle_pinch = self.distance(lm['middle_tip'], lm['thumb_tip'])
        fingers_up   = sum([index_up, middle_up, ring_up, pinky_up])

        if pinch_dist < self.click_threshold:
            return "PINCH"
        if middle_pinch < self.click_threshold and not index_up:
            return "RIGHT_CLICK"
        if index_up and not middle_up and not ring_up and not pinky_up:
            return "CURSOR"
        if index_up and middle_up and not ring_up and not pinky_up:
            return "SCROLL"
        if index_up and middle_up and ring_up and not pinky_up:
            return "SCREENSHOT"
        if fingers_up == 0:
            return "FIST"
        if fingers_up == 4:
            return "OPEN_PALM"
        return "NONE"

    def run(self):
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.cam_w)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.cam_h)
        cap.set(cv2.CAP_PROP_FPS, 30)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        print("VOXIS Gesture Engine - ACTIVE")
        print("Open palm     -> Activate/Deactivate")
        print("One finger    -> Move cursor")
        print("Pinch         -> Click")
        print("Pinch+drag    -> Select text")
        print("Two fingers   -> Scroll")
        print("Three fingers -> Screenshot")
        print("Fist          -> Play/Pause")
        print("Press ESC     -> Quit")

        while True:
            success, frame = cap.read()
            if not success:
                continue

            frame = cv2.flip(frame, 1)
            h, w, _ = frame.shape

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            rgb_frame.flags.writeable = False
            results = self.hands.process(rgb_frame)
            rgb_frame.flags.writeable = True

            current_time = time.time()

            # Auto deactivate if no hand detected
            if not results.multi_hand_landmarks:
                if self.is_active:
                    if current_time - self.last_hand_time > self.auto_deactivate_timeout:
                        self.is_active = False
                        print("Auto deactivated: no hand detected")
                        # Release drag if active
                        if self.is_dragging:
                            pyautogui.mouseUp()
                            self.is_dragging = False
            else:
                self.last_hand_time = current_time

            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    self.mp_draw.draw_landmarks(
                        frame,
                        hand_landmarks,
                        self.mp_hands.HAND_CONNECTIONS,
                        self.mp_draw.DrawingSpec(
                            color=(0, 255, 0) if self.is_active else (100, 100, 100),
                            thickness=2,
                            circle_radius=3
                        ),
                        self.mp_draw.DrawingSpec(
                            color=(0, 200, 255) if self.is_active else (80, 80, 80),
                            thickness=2
                        )
                    )

                    lm = self.get_landmarks(hand_landmarks, w, h)
                    gesture = self.detect_gesture(lm)

                    # Cursor position always calculated
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

                    smooth_x = self.prev_x + (screen_x - self.prev_x) / self.smoothing
                    smooth_y = self.prev_y + (screen_y - self.prev_y) / self.smoothing
                    self.prev_x, self.prev_y = smooth_x, smooth_y

                    # Palm toggle works in both modes.
                    if gesture == "OPEN_PALM":
                        if self.palm_start_time == 0:
                            self.palm_start_time = current_time

                        held = current_time - self.palm_start_time
                        cooldown_ok = current_time - self.last_toggle_time > self.toggle_cooldown

                        # Show progress bar
                        progress = min(held / self.palm_hold_required, 1.0)
                        bar_w = int(progress * 200)
                        cv2.rectangle(frame, (w//2 - 100, h - 40),
                                     (w//2 - 100 + bar_w, h - 20),
                                     (0, 255, 0), -1)
                        cv2.rectangle(frame, (w//2 - 100, h - 40),
                                     (w//2 + 100, h - 20),
                                     (255, 255, 255), 2)
                        cv2.putText(frame, "Hold to toggle...",
                                   (w//2 - 80, h - 45),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                                   (255, 255, 255), 1)

                        if held >= self.palm_hold_required and cooldown_ok:
                            self.is_active = not self.is_active
                            self.last_toggle_time = current_time
                            self.palm_start_time = 0
                            if self.is_active:
                                print("Gesture control ACTIVATED")
                            else:
                                print("Gesture control DEACTIVATED")
                    else:
                        self.palm_start_time = 0

                    # ONLY execute gestures when ACTIVE
                    if self.is_active and gesture != "OPEN_PALM":

                        if gesture == "CURSOR":
                            pyautogui.moveTo(int(smooth_x), int(smooth_y))
                            self._show_status(frame, "MOVE", (0, 255, 0))

                        elif gesture == "PINCH":
                            pinch_pos = (int(smooth_x), int(smooth_y))
                            if not self.is_dragging:
                                if self.pinch_start_time == 0:
                                    self.pinch_start_time = current_time
                                    self.pinch_start_pos = pinch_pos
                                held_time = current_time - self.pinch_start_time
                                moved = self.distance(pinch_pos, self.pinch_start_pos) > 10
                                if held_time > self.drag_threshold and moved:
                                    pyautogui.mouseDown()
                                    self.is_dragging = True
                                    self._show_status(frame, "SELECTING...", (255, 165, 0))
                                else:
                                    self._show_status(frame, "PINCH HOLD", (0, 200, 255))
                            else:
                                pyautogui.moveTo(pinch_pos[0], pinch_pos[1])
                                self._show_status(frame, "SELECTING...", (255, 165, 0))

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
                                filename = f"screenshot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                                path = os.path.join(os.path.expanduser("~"), "Pictures", filename)
                                os.makedirs(os.path.dirname(path), exist_ok=True)
                                pyautogui.screenshot(path)
                                self.last_gesture_time = current_time
                                self._show_status(frame, "SCREENSHOT!", (255, 0, 255))
                                print(f"Screenshot: {path}")

                        elif gesture == "FIST":
                            if current_time - self.last_gesture_time > self.gesture_cooldown:
                                pyautogui.press('space')
                                self.last_gesture_time = current_time
                                self._show_status(frame, "PLAY/PAUSE", (255, 128, 0))

                        # Handle pinch release
                        if gesture != "PINCH":
                            if self.is_dragging:
                                pyautogui.mouseUp()
                                self.is_dragging = False
                                self._show_status(frame, "SELECTED!", (0, 255, 0))
                            elif self.pinch_start_time > 0:
                                if current_time - self.last_click_time > self.click_cooldown:
                                    pyautogui.click()
                                    self.last_click_time = current_time
                                    self._show_status(frame, "CLICK", (0, 0, 255))
                            self.pinch_start_time = 0
                            self.pinch_start_pos = (0, 0)

                    # Show gesture name
                    cv2.putText(frame, f"{gesture}",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                        0.7, (255, 255, 255), 2)

            # Status indicator
            status_color = (0, 255, 0) if self.is_active else (100, 100, 100)
            status_text = "ACTIVE" if self.is_active else "INACTIVE - Show palm to activate"
            cv2.circle(frame, (w - 30, 30), 12, status_color, -1)
            cv2.putText(frame, status_text,
                (10, h - 10), cv2.FONT_HERSHEY_SIMPLEX,
                0.55, status_color, 2)

            # VOXIS branding
            cv2.putText(frame, "VOXIS",
                (w - 100, 30), cv2.FONT_HERSHEY_SIMPLEX,
                0.8, (0, 255, 0), 2)

            cv2.imshow("VOXIS - Gesture Engine", frame)

            key = cv2.waitKey(1) & 0xFF
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

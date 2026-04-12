import queue
import threading
import tkinter as tk
from tkinter import ttk


class CompanionWindow:
    def __init__(self):
        self._events: queue.Queue[tuple[str, object]] = queue.Queue()
        self._thread = threading.Thread(
            target=self._run,
            daemon=True,
            name="VoxisUI",
        )
        self._thread.start()

    def set_status(self, text: str) -> None:
        self._events.put(("status", text))

    def set_mode(self, text: str) -> None:
        self._events.put(("mode", text))

    def set_language(self, text: str) -> None:
        self._events.put(("language", text))

    def add_user_message(self, text: str) -> None:
        self._events.put(("user", text))

    def add_assistant_message(self, text: str) -> None:
        self._events.put(("assistant", text))

    def _run(self) -> None:
        root = tk.Tk()
        root.title("VOXIS")
        root.geometry("380x420+980+140")
        root.configure(bg="#0f172a")
        root.attributes("-topmost", True)
        root.resizable(False, False)

        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass

        frame = tk.Frame(root, bg="#0f172a", padx=14, pady=14)
        frame.pack(fill="both", expand=True)

        title = tk.Label(
            frame,
            text="VOXIS",
            font=("Segoe UI Semibold", 18),
            fg="#e2e8f0",
            bg="#0f172a",
        )
        title.pack(anchor="w")

        self._status_var = tk.StringVar(value="Starting")
        self._mode_var = tk.StringVar(value="Mode: auto")
        self._language_var = tk.StringVar(value="Language: en-IN")

        tk.Label(
            frame,
            textvariable=self._status_var,
            font=("Segoe UI", 10),
            fg="#93c5fd",
            bg="#0f172a",
        ).pack(anchor="w", pady=(4, 2))

        meta_row = tk.Frame(frame, bg="#0f172a")
        meta_row.pack(fill="x", pady=(0, 10))

        tk.Label(
            meta_row,
            textvariable=self._mode_var,
            font=("Segoe UI", 9),
            fg="#cbd5e1",
            bg="#0f172a",
        ).pack(side="left")

        tk.Label(
            meta_row,
            textvariable=self._language_var,
            font=("Segoe UI", 9),
            fg="#cbd5e1",
            bg="#0f172a",
        ).pack(side="right")

        self._transcript = tk.Text(
            frame,
            wrap="word",
            bg="#111827",
            fg="#e5e7eb",
            insertbackground="#e5e7eb",
            relief="flat",
            font=("Segoe UI", 10),
            padx=10,
            pady=10,
            state="disabled",
        )
        self._transcript.pack(fill="both", expand=True)

        self._transcript.tag_configure("user", foreground="#93c5fd")
        self._transcript.tag_configure("assistant", foreground="#a7f3d0")
        self._transcript.tag_configure("label", font=("Segoe UI Semibold", 10))

        root.after(120, self._drain_events, root)
        root.mainloop()

    def _drain_events(self, root: tk.Tk) -> None:
        try:
            while True:
                kind, payload = self._events.get_nowait()
                if kind == "status":
                    self._status_var.set(str(payload))
                elif kind == "mode":
                    self._mode_var.set(f"Mode: {payload}")
                elif kind == "language":
                    self._language_var.set(f"Language: {payload}")
                elif kind == "user":
                    self._append_message("You", str(payload), "user")
                elif kind == "assistant":
                    self._append_message("VOXIS", str(payload), "assistant")
        except queue.Empty:
            pass
        finally:
            root.after(120, self._drain_events, root)

    def _append_message(self, speaker: str, text: str, tag: str) -> None:
        self._transcript.configure(state="normal")
        self._transcript.insert("end", f"{speaker}: ", ("label", tag))
        self._transcript.insert("end", f"{text}\n\n", (tag,))
        self._transcript.see("end")
        self._transcript.configure(state="disabled")

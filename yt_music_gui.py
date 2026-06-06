import queue
import threading
import tkinter as tk
from tkinter import ttk

from yt_music_dl import download_youtube_music, validate_youtube_url


class YTDLApp:
    def __init__(self, root):
        self.root = root
        self.root.title("YT Music Downloader")
        self.root.geometry("1200x700")
        self.root.minsize(980, 620)

        self.bg_top = "#07112B"
        self.bg_bottom = "#1D2F54"
        self.card_bg = "#0C1938"
        self.card_border = "#2B4D86"
        self.text_main = "#F3F7FF"
        self.text_sub = "#8DB2EB"
        self.input_bg = "#071230"
        self.input_border = "#2E5A9B"
        self.progress_bg = "#2B487E"
        self.progress_fg = "#FF7A59"
        self.button_bg = "#FF6A58"
        self.button_active = "#F89B3D"
        self.mode_active_bg = "#2F5FB0"
        self.mode_active_fg = "#F2F6FF"
        self.mode_inactive_bg = "#112142"
        self.mode_inactive_fg = "#A8C4F1"

        self.log_queue = queue.Queue()
        self.url_var = tk.StringVar(value="https://www.youtube.com/watch?v=")
        self.mode_var = tk.StringVar(value="2")
        self.mode_buttons = {}
        self.download_btn_state = "normal"
        self.download_btn_hover = False

        self.canvas = tk.Canvas(self.root, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", self.on_resize)

        self.build_ui()
        self.poll_log_queue()

    def hex_to_rgb(self, h):
        h = h.lstrip("#")
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

    def rgb_to_hex(self, rgb):
        return "#%02x%02x%02x" % rgb

    def draw_gradient(self, width, height):
        self.canvas.delete("bg")
        r1, g1, b1 = self.hex_to_rgb(self.bg_top)
        r2, g2, b2 = self.hex_to_rgb(self.bg_bottom)
        steps = max(height, 1)
        for i in range(steps):
            ratio = i / steps
            r = int(r1 + (r2 - r1) * ratio)
            g = int(g1 + (g2 - g1) * ratio)
            b = int(b1 + (b2 - b1) * ratio)
            self.canvas.create_line(0, i, width, i, fill=self.rgb_to_hex((r, g, b)), tags="bg")

    def build_ui(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "Horizontal.TProgressbar",
            troughcolor=self.progress_bg,
            background=self.progress_fg,
            bordercolor=self.progress_bg,
            lightcolor=self.progress_fg,
            darkcolor=self.progress_fg,
        )

        self.card = tk.Frame(self.canvas, bg=self.card_bg, bd=0)
        self.card_window = self.canvas.create_window(0, 0, window=self.card, anchor="nw")

        content = tk.Frame(self.card, bg=self.card_bg)
        content.pack(fill="both", expand=True, padx=48, pady=34)
        content.grid_columnconfigure(0, weight=5)
        content.grid_columnconfigure(1, weight=3)

        left = tk.Frame(content, bg=self.card_bg)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 36))

        right = tk.Frame(content, bg=self.card_bg)
        right.grid(row=0, column=1, sticky="nsew")

        tk.Label(
            left,
            text="YT Music Downloader",
            fg=self.text_main,
            bg=self.card_bg,
            font=("Segoe UI", 40, "bold"),
        ).pack(anchor="w")

        tk.Label(
            left,
            text="Best audio • MP3 320 • Opus info • Auto rename",
            fg=self.text_sub,
            bg=self.card_bg,
            font=("Segoe UI", 20),
        ).pack(anchor="w", pady=(8, 22))

        entry_wrap = tk.Frame(left, bg=self.input_border)
        entry_wrap.pack(fill="x")

        self.url_entry = tk.Entry(
            entry_wrap,
            textvariable=self.url_var,
            bg=self.input_bg,
            fg="#DCEBFF",
            insertbackground="#DCEBFF",
            relief="flat",
            font=("Consolas", 22),
            bd=0,
        )
        self.url_entry.pack(fill="x", padx=2, pady=2, ipady=13)

        self.download_btn_canvas = tk.Canvas(
            left,
            width=360,
            height=86,
            bg=self.card_bg,
            highlightthickness=0,
            cursor="hand2",
        )
        self.download_btn_canvas.pack(anchor="w", pady=(32, 0))
        self.download_btn_canvas.bind("<Button-1>", self.on_download_click)
        self.download_btn_canvas.bind("<Enter>", self.on_download_enter)
        self.download_btn_canvas.bind("<Leave>", self.on_download_leave)
        self.draw_download_button()

        self.status_label = tk.Label(
            left,
            text="Ready",
            fg=self.text_sub,
            bg=self.card_bg,
            font=("Segoe UI", 12),
        )
        self.status_label.pack(anchor="w", pady=(18, 0))

        self.audio_info_label = tk.Label(
            left,
            text="音訊資訊: -",
            fg="#9FC1F2",
            bg=self.card_bg,
            font=("Consolas", 11),
        )
        self.audio_info_label.pack(anchor="w", pady=(8, 0))

        self.play_canvas = tk.Canvas(right, width=230, height=230, bg=self.card_bg, highlightthickness=0)
        self.play_canvas.pack(pady=(34, 28))
        self.play_canvas.create_oval(30, 30, 200, 200, fill="#213C73", outline="#213C73")
        # Keep the play glyph centered in the circle.
        self.play_canvas.create_polygon(96, 84, 96, 146, 150, 115, fill="#F4F8FF", outline="#F4F8FF")

        self.progress = ttk.Progressbar(right, orient="horizontal", mode="indeterminate", length=300)
        self.progress.pack(pady=(8, 8))

        tk.Label(
            right,
            text="downloads/",
            fg="#9FC1F2",
            bg=self.card_bg,
            font=("Segoe UI", 19),
        ).pack()

        mode_row = tk.Frame(right, bg=self.card_bg)
        mode_row.pack(pady=(20, 0))

        self.mode_buttons["1"] = tk.Button(
            mode_row,
            text="Best",
            command=lambda: self.set_mode("1"),
            relief="flat",
            bd=0,
            width=7,
            pady=6,
            font=("Segoe UI", 10, "bold"),
            cursor="hand2",
        )
        self.mode_buttons["1"].grid(row=0, column=0, padx=(0, 8))

        self.mode_buttons["2"] = tk.Button(
            mode_row,
            text="MP3 320",
            command=lambda: self.set_mode("2"),
            relief="flat",
            bd=0,
            width=7,
            pady=6,
            font=("Segoe UI", 10, "bold"),
            cursor="hand2",
        )
        self.mode_buttons["2"].grid(row=0, column=1, padx=(0, 8))

        self.mode_buttons["3"] = tk.Button(
            mode_row,
            text="Opus",
            command=lambda: self.set_mode("3"),
            relief="flat",
            bd=0,
            width=7,
            pady=6,
            font=("Segoe UI", 10, "bold"),
            cursor="hand2",
        )
        self.mode_buttons["3"].grid(row=0, column=2)

        self.mode_buttons["4"] = tk.Button(
            mode_row,
            text="FLAC",
            command=lambda: self.set_mode("4"),
            relief="flat",
            bd=0,
            width=7,
            pady=6,
            font=("Segoe UI", 10, "bold"),
            cursor="hand2",
        )
        self.mode_buttons["4"].grid(row=0, column=3, padx=(8, 0))

        self.mode_text_label = tk.Label(
            right,
            text="Mode: 2 MP3 320 (Default)",
            fg="#A9C3EA",
            bg=self.card_bg,
            font=("Segoe UI", 10),
        )
        self.mode_text_label.pack(pady=(8, 0))

        self.update_mode_buttons()

    def on_resize(self, event):
        w = event.width
        h = event.height
        self.draw_gradient(w, h)

        margin = 22
        max_w = max(w - margin * 2, 400)
        max_h = max(h - margin * 2, 300)
        card_w = min(max(int(w * 0.88), 820), 1120, max_w)
        card_h = min(max(int(h * 0.76), 500), 590, max_h)
        x = max((w - card_w) // 2, margin)
        y = max((h - card_h) // 2, margin)

        self.canvas.coords(self.card_window, x, y)
        self.canvas.itemconfigure(self.card_window, width=card_w, height=card_h)

        self.canvas.delete("card_outline")
        self.canvas.create_rectangle(
            x,
            y,
            x + card_w,
            y + card_h,
            outline=self.card_border,
            width=2,
            fill="",
            tags="card_outline",
        )

    def set_mode(self, mode):
        self.mode_var.set(mode)
        self.update_mode_buttons()

    def mix_hex(self, color1, color2, ratio):
        c1 = self.hex_to_rgb(color1)
        c2 = self.hex_to_rgb(color2)
        mixed = (
            int(c1[0] + (c2[0] - c1[0]) * ratio),
            int(c1[1] + (c2[1] - c1[1]) * ratio),
            int(c1[2] + (c2[2] - c1[2]) * ratio),
        )
        return self.rgb_to_hex(mixed)

    def draw_download_button(self):
        c = self.download_btn_canvas
        c.delete("all")

        x1, y1, x2, y2 = 8, 8, 352, 78
        radius = 18

        if self.download_btn_state == "disabled":
            left_color = "#5F6B84"
            right_color = "#7A869F"
            text_color = "#CED7EA"
        elif self.download_btn_hover:
            left_color = "#FF6E61"
            right_color = "#FFB04A"
            text_color = "#08122A"
        else:
            left_color = "#FF5757"
            right_color = "#F89B3D"
            text_color = "#08122A"

        # Draw a smooth rounded gradient button without stroke to avoid edge artifacts.
        width = x2 - x1
        for x in range(x1, x2 + 1):
            ratio = (x - x1) / max(width, 1)
            color = self.mix_hex(left_color, right_color, ratio)

            if x < x1 + radius:
                dx = (x1 + radius) - x
                delta = radius * radius - dx * dx
                y_offset = int((delta ** 0.5)) if delta > 0 else 0
            elif x > x2 - radius:
                dx = x - (x2 - radius)
                delta = radius * radius - dx * dx
                y_offset = int((delta ** 0.5)) if delta > 0 else 0
            else:
                y_offset = radius

            top = y1 + radius - y_offset
            bottom = y2 - radius + y_offset
            c.create_line(x, top, x, bottom, fill=color)

        c.create_text(
            (x1 + x2) // 2,
            (y1 + y2) // 2 + 1,
            text="Download",
            fill=text_color,
            font=("Segoe UI", 28, "bold"),
        )

    def on_download_click(self, _event):
        if self.download_btn_state == "normal":
            self.on_download()

    def on_download_enter(self, _event):
        if self.download_btn_state == "normal":
            self.download_btn_hover = True
            self.draw_download_button()

    def on_download_leave(self, _event):
        if self.download_btn_state == "normal":
            self.download_btn_hover = False
            self.draw_download_button()

    def update_mode_buttons(self):
        mode_desc = {
            "1": "Mode: 1 原始最佳",
            "2": "Mode: 2 MP3 320 (Default)",
            "3": "Mode: 3 Opus + 資訊",
            "4": "Mode: 4 FLAC",
        }
        active_mode = self.mode_var.get()
        self.mode_text_label.config(text=mode_desc.get(active_mode, "Mode: 2 MP3 320 (Default)"))

        for mode, button in self.mode_buttons.items():
            is_active = mode == active_mode
            button.configure(
                bg=self.mode_active_bg if is_active else self.mode_inactive_bg,
                fg=self.mode_active_fg if is_active else self.mode_inactive_fg,
                activebackground=self.mode_active_bg if is_active else self.mode_inactive_bg,
                activeforeground=self.mode_active_fg if is_active else self.mode_inactive_fg,
            )

    def poll_log_queue(self):
        while not self.log_queue.empty():
            item = self.log_queue.get_nowait()
            if isinstance(item, tuple) and item[0] == "audio_info":
                self.audio_info_label.config(text=item[1])
            else:
                self.status_label.config(text=item)
        self.root.after(120, self.poll_log_queue)

    def on_download(self):
        url = self.url_var.get().strip()
        if not url:
            self.status_label.config(text="請先輸入 URL")
            return
        is_valid, error_message = validate_youtube_url(url)
        if not is_valid:
            self.status_label.config(text=error_message)
            return

        self.download_btn_state = "disabled"
        self.download_btn_hover = False
        self.draw_download_button()
        self.progress.start(10)
        self.status_label.config(text="下載中...")
        self.audio_info_label.config(text="音訊資訊: -")

        threading.Thread(target=self.run_download, args=(url, self.mode_var.get()), daemon=True).start()

    def run_download(self, url, mode):
        keep_original = True
        prefer_opus = False
        show_audio_info = True
        output_codec = None

        if mode == "2":
            keep_original = False
            output_codec = "mp3"
        elif mode == "3":
            prefer_opus = True
        elif mode == "4":
            keep_original = False
            output_codec = "flac"

        def cb(message):
            self.log_queue.put(message)

        result = download_youtube_music(
            url,
            keep_original=keep_original,
            mp3_quality="320",
            prefer_opus=prefer_opus,
            show_audio_info=show_audio_info,
            status_callback=cb,
            output_codec=output_codec,
        )

        if result.get("success"):
            audio = result.get("audio_info")
            if audio:
                abr = audio.get("abr")
                self.log_queue.put(
                    (
                        "audio_info",
                        f"音訊資訊: codec={audio.get('codec', 'unknown')} ext={audio.get('ext', 'unknown')} abr={abr if abr else 'N/A'} kbps",
                    )
                )
            self.log_queue.put("任務完成")
        else:
            self.log_queue.put("任務失敗")

        self.root.after(0, self.download_done)

    def download_done(self):
        self.progress.stop()
        self.download_btn_state = "normal"
        self.draw_download_button()


def main():
    root = tk.Tk()
    YTDLApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

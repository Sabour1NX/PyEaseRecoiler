#搭配CompEditor使用(Ai也干了)

import os
import sys
import json
import random
import math
import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import win32api
import win32con
import ctypes
from PIL import Image, ImageTk

VERSION = "0.2"
BUILD_DATE = "2025-5-17"
DEFAULT_CONFIG = {
    "mode": "comp",
    "stages": [
        {
            "isExecuteTime": 300,
            "distance": 10,
            "angle": 90,
            "activation_delay": 50,
            "interval": 100,
            "random_interval": 20
        }
    ]
}

class CompConfigLoader:
    @staticmethod
    def load_config(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            messagebox.showerror("错误", f"配置加载失败: {str(e)}")
            return None

    @staticmethod
    def save_default_config(path):
        config_dir = os.path.dirname(path)
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(DEFAULT_CONFIG, f, indent=4)
            return True
        except Exception as e:
            messagebox.showerror("错误", f"创建默认配置失败: {str(e)}")
            return False

class CompRecoilThread(threading.Thread):
    def __init__(self, config_path, status_callback):
        super().__init__()
        self.config_path = config_path
        self.status_callback = status_callback
        self.daemon = True
        self.running = False
        self.lock = threading.Lock()
        self.current_stage = 0
        self.stage_start = 0

    def stop(self):
        with self.lock:
            self.running = False

    def run(self):
        try:
            with self.lock:
                self.running = True
            self.status_callback("正在启动...")
            
            config = CompConfigLoader.load_config(self.config_path)
            if not config:
                self.status_callback("配置加载失败")
                return

            stages = config.get("stages", [])
            if not stages:
                self.status_callback("无效配置: 无有效阶段")
                return

            self.status_callback("运行中 - 按下F10停止")
            last_left_button = False
            
            while self.running:
                current_time = time.perf_counter() * 1000
                current_stage = stages[self.current_stage % len(stages)]
                if current_time - self.stage_start > current_stage["isExecuteTime"]:
                    self.current_stage += 1
                    self.stage_start = current_time
                    if self.current_stage >= len(stages):
                        self.current_stage = 0
                current_button = win32api.GetAsyncKeyState(win32con.VK_LBUTTON) < 0
                if current_button:
                    if not last_left_button:
                        activation_start = current_time
                    
                    if (current_time - activation_start) >= current_stage["activation_delay"]:
                        dx = int(current_stage["distance"] * math.cos(math.radians(current_stage["angle"])))
                        dy = int(current_stage["distance"] * math.sin(math.radians(current_stage["angle"])))
                        win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, dx, dy, 0, 0)
                        interval = current_stage["interval"] + random.randint(0, current_stage["random_interval"])
                        time.sleep(interval / 1000)
                else:
                    time.sleep(0.005)
                
                last_left_button = current_button
        except Exception as e:
            self.status_callback(f"错误: {str(e)}")
            messagebox.showerror("运行时错误", f"程序遇到错误已停止:\n{str(e)}")
        finally:
            with self.lock:
                self.running = False
            self.status_callback("已停止")

class CompApplication(tk.Tk):
    def __init__(self):
        super().__init__()
        self.check_admin()
        self.initialize_paths()
        self.create_default_config()
        
        self.title(f"PyEaseRecoiler_ComplexMode {VERSION}")
        self.geometry("400x300")
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        self.thread = None
        self.hotkey_listener_running = True
        
        self.create_widgets()
        self.bind_hotkeys()
        self.update_status("就绪")

        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            image_path = os.path.join(current_dir, "Resen.png")
            image = Image.open(image_path)
            self.photo = ImageTk.PhotoImage(image)  
            self.image_label = ttk.Label(self, image=self.photo)
            self.image_label.place(x=133, y=100)
        except Exception as e:
            print(f"图片加载失败: {str(e)}")
            self.image_label = ttk.Label(self, text="[图片加载失败]")
            self.image_label.pack(pady=10)
    
    def check_admin(self):
        if not ctypes.windll.shell32.IsUserAnAdmin():
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
            sys.exit()

    def initialize_paths(self):
        self.app_dir = os.path.dirname(sys.executable)
        self.config_dir = os.path.join(self.app_dir, "recoil_config_Comp")
        self.default_config = os.path.join(self.config_dir, "default.json")

    def create_default_config(self):
        if not os.path.exists(self.default_config):
            if not CompConfigLoader.save_default_config(self.default_config):
                sys.exit(1)

    def create_widgets(self):
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        control_frame = ttk.LabelFrame(main_frame, text="控制面板")
        control_frame.pack(fill=tk.X, pady=5)
        self.status_var = tk.StringVar()
        status_label = ttk.Label(control_frame, textvariable=self.status_var)
        status_label.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(control_frame, text="启动(F10)", command=self.toggle).pack(side=tk.RIGHT, padx=5)
        ttk.Button(control_frame, text="加载配置", command=self.load_config).pack(side=tk.RIGHT, padx=5)
        ttk.Button(control_frame, text="打开编辑器", command=self.open_editor).pack(side=tk.RIGHT, padx=5)
        self.config_label = ttk.Label(main_frame, text=f"当前配置: {os.path.basename(self.default_config)}")
        self.config_label.pack(pady=5)
        info_frame = ttk.Frame(self)
        info_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(info_frame, text=f"版本: {VERSION} 构建日期: {BUILD_DATE}").pack(side=tk.LEFT)
        ttk.Label(info_frame, text="※ 不要与简单模式同时运行").pack(side=tk.RIGHT)

    def bind_hotkeys(self):
        def hotkey_listener():
            while self.hotkey_listener_running:
                try:
                    if win32api.GetAsyncKeyState(win32con.VK_F10) & 0x8000:
                        self.after(0, self.toggle)
                        while win32api.GetAsyncKeyState(win32con.VK_F10) & 0x8000:
                            time.sleep(0.01)
                    time.sleep(0.01)
                except Exception as e:
                    print(f"热键监听错误: {str(e)}")
            print("热键监听已停止")
        threading.Thread(target=hotkey_listener, daemon=True).start()
    def toggle(self):
        if self.thread and self.thread.running:
            self.thread.stop()
            self.thread = None
            self.update_status("已停止")
        else:
            if self.thread:
                self.thread.stop()
            self.thread = CompRecoilThread(self.default_config, self.update_status)
            self.thread.start()
            self.update_status("正在启动...")
    def load_config(self):
        path = filedialog.askopenfilename(
            initialdir=self.config_dir,
            filetypes=[("JSON配置", "*.json")]
        )
        if path:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    if "stages" not in config or not isinstance(config["stages"], list):
                        raise ValueError("无效的配置文件格式")
                self.default_config = path
                self.config_label.config(text=f"当前配置: {os.path.basename(path)}")
                self.update_status(f"已加载配置: {os.path.basename(path)}")
            except Exception as e:
                messagebox.showerror("错误", f"配置验证失败: {str(e)}")
                self.default_config = os.path.join(self.config_dir, "default.json")
                self.config_label.config(text=f"当前配置: default.json")
    def open_editor(self):
        editor_path = os.path.join(self.app_dir, "CompEditor.exe")
        if os.path.exists(editor_path):
            try:
                ctypes.windll.shell32.ShellExecuteW(None, "runas", editor_path, None, None, 1)
            except Exception as e:
                try:
                    os.startfile(editor_path)
                except Exception as e:
                    messagebox.showerror("错误", f"无法启动编辑器: {str(e)}")
        else:
            messagebox.showerror("错误", f"找不到编辑器程序: {editor_path}")

    def update_status(self, message):
        self.status_var.set(message)
        self.update()

    def on_close(self):
        self.hotkey_listener_running = False
        if self.thread:
            self.thread.stop()
            self.thread.join(0.5)
        self.destroy()
if __name__ == "__main__":
    app = CompApplication()
    app.mainloop()
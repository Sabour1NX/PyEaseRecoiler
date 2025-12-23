# 2025-05-11  



import os
import sys
import json
import threading
import time
import math
import random
import ctypes
import tkinter as tk
from tkinter import ttk, messagebox
import win32api
import win32con
import subprocess


class AdminCheck:
    @staticmethod
    def request_admin():
        MB_YESNO = 0x04
        MB_ICONQUESTION = 0x20
        IDYES = 6
        
        response = ctypes.windll.user32.MessageBoxW(
            None,
            "本程序需要管理员权限才能正常运行\n是否立即以管理员权限启动？",
            "权限要求",
            MB_YESNO | MB_ICONQUESTION
        )
        
        if response == IDYES:
            try:
                ctypes.windll.shell32.ShellExecuteW(
                    None, 
                    "runas", 
                    sys.executable, 
                    " ".join([sys.argv[0]] + sys.argv[1:]), 
                    None, 
                    1
                )
            except Exception as e:
                ctypes.windll.user32.MessageBoxW(
                    None,
                    f"提权失败：{str(e)}\n请手动以管理员权限运行程序",
                    "错误",
                    0x10
                )
                sys.exit(1)
            sys.exit(0)
        else:
            ctypes.windll.user32.MessageBoxW(
                None,
                "必须使用管理员权限运行本程序\n点击确定退出",
                "权限不足",
                0x10
            )
            sys.exit(1)

if not ctypes.windll.shell32.IsUserAnAdmin():
    AdminCheck.request_admin()
CONFIG_FILE = "recoil_config.json"
is_running = False
mouse_pressed = False
lock = threading.Lock()

class ConfigManager:
    @staticmethod
    def load_config():
        default_config = {
            "distance": 10,
            "angle": 270,
            "activation_delay": 300,
            "interval": 100,
            "random_interval": 25
        }
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    if all(key in config for key in default_config.keys()):
                        return config
            return default_config
        except:
            return default_config

    @staticmethod
    def save_config(config):
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)

class MouseController:
    @staticmethod
    def move_mouse(distance, angle):
        radians = angle * (math.pi / 180)
        dx = int(distance * math.cos(radians))
        dy = int(distance * math.sin(radians))
        
        # DPI
        ctypes.windll.user32.SetProcessDPIAware()
        win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, dx, dy, 0, 0)

class RecoilThread(threading.Thread):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.daemon = True

    def run(self):
        global is_running, mouse_pressed
        last_activation = 0
        activation_time = 0
        
        while is_running:
            current_time = time.time() * 1000
            if mouse_pressed:
                if activation_time == 0:
                    activation_time = current_time
                
                if (current_time - activation_time) >= self.config["activation_delay"]:
                    #if self.config["activation_delay"] > 0:
                        # 连续
                        interval = self.config["interval"] + random.randint(0, self.config["random_interval"])
                        if current_time - last_activation >= interval:
                            MouseController.move_mouse(self.config["distance"], self.config["angle"])
                            last_activation = current_time
                    #else:
                    #    # 单次
                    #    MouseController.move_mouse(self.config["distance"], self.config["angle"])
                    #    time.sleep(0.001)
            else:
                activation_time = 0
            time.sleep(0.001)


class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PyEaseRecoiler v2.0")
        self.geometry("600x400")
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.config = ConfigManager.load_config()
        self.thread = None
        self.create_widgets()
        self.create_comp_mode_button()
        self.bind_hotkeys()
        self.update_config_display()

    def create_comp_mode_button(self):
        
        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=5)
        
        self.comp_mode_btn = ttk.Button(
            btn_frame, 
            text="启动复杂模式", 
            command=self.launch_complex_mode
        )
        self.comp_mode_btn.pack(side="left", padx=5)
        
        ttk.Label(btn_frame, text="启动同目录下的 PyEaseRecoiler_Comp.exe").pack(side="left", padx=5)

    def launch_complex_mode(self):
        
        try:
            current_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
            comp_exe_path = os.path.join(current_dir, "PyEaseRecoiler_Comp.exe")
            
            if os.path.exists(comp_exe_path):
                try:
                    ctypes.windll.shell32.ShellExecuteW(
                        None, 
                        "runas", 
                        comp_exe_path, 
                        None, 
                        None, 
                        1
                    )
                except Exception as e:
                    try:
                        subprocess.Popen(comp_exe_path)
                    except Exception as e:
                        messagebox.showerror(
                            "错误", 
                            f"无法启动复杂模式程序:\n{str(e)}"
                        )
            else:
                messagebox.showerror(
                    "错误", 
                    "找不到复杂模式程序:\n{comp_exe_path}\n请确保PyEaseRecoiler_Comp.exe与主程序在同一目录下"
                )
        except Exception as e:
            messagebox.showerror(
                "错误", 
                f"发生未知错误:\n{str(e)}"
            )


    def create_widgets(self):
        style = ttk.Style()
        style.configure("TScale", troughcolor="#404040", sliderthickness=15)
        param_frame = ttk.LabelFrame(self, text="参数设置")
        param_frame.pack(pady=10, padx=10, fill="x")

        self.sliders = {}
        self.entries = {}
        params = [
            ("distance", "鼠标移动距离 (像素):", 0, 100),
            ("angle", "移动方向 (角度):", 0, 360),
            ("activation_delay", "启动延迟 (ms):", 0, 1000),
            ("interval", "连续间隔 (ms):", 0, 500),
            ("random_interval", "随机间隔 (ms):", 0, 100)
        ]

        for i, (key, label, min_val, max_val) in enumerate(params):
            frame = ttk.Frame(param_frame)
            frame.grid(row=i, column=0, sticky="ew", padx=5, pady=2)
            
            lbl = ttk.Label(frame, text=label, width=20)
            lbl.pack(side="left")
            
            self.sliders[key] = ttk.Scale(frame, from_=min_val, to=max_val, 
                                       command=lambda v, k=key: self.slider_changed(k, v))
            self.sliders[key].pack(side="left", expand=True, fill="x")
            
            self.entries[key] = ttk.Entry(frame, width=8)
            self.entries[key].bind("<Return>", lambda e, k=key: self.entry_changed(k))
            self.entries[key].pack(side="left", padx=5)
        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=10)
        
        self.start_btn = ttk.Button(btn_frame, text="启动", command=self.toggle_program)
        self.start_btn.pack(side="left", padx=5)
        
        ttk.Label(btn_frame, text="切换键: F9").pack(side="left", padx=5)

    def bind_hotkeys(self):
        self.hotkey_listener_thread = threading.Thread(target=self.hotkey_listener)
        self.hotkey_listener_thread.daemon = True
        self.hotkey_listener_thread.start()

    def hotkey_listener(self):
        last_press_time = 0
        debounce_time = 0.3  # 防抖
        
        while True:
            try:
                if win32api.GetAsyncKeyState(win32con.VK_F9) & 0x8000:
                    current_time = time.time()
                    if current_time - last_press_time > debounce_time:
                        self.after(0, self.toggle_program)
                        last_press_time = current_time
                    while win32api.GetAsyncKeyState(win32con.VK_F9) & 0x8000:
                        time.sleep(0.01)
                time.sleep(0.01)
            except Exception as e:
                print(f"热键监听异常: {str(e)}")
                break

    def slider_changed(self, key, value):
        value = float(value)
        slider = self.sliders[key]
        min_val = slider.cget("from")
        max_val = slider.cget("to")
        value = max(min_val, min(value, max_val))
        self.entries[key].delete(0, tk.END)
        self.entries[key].insert(0, f"{int(value)}")
        self.config[key] = int(value)

    def entry_changed(self, key):
        try:
            value = int(self.entries[key].get())
            slider = self.sliders[key]
            min_val = slider.cget("from")
            max_val = slider.cget("to")
            value = max(min_val, min(value, max_val))
            slider.set(value)
            self.config[key] = value
        except:
            pass

    def update_config_display(self):
        for key in self.config:
            if key in self.sliders:
                self.sliders[key].set(self.config[key])
                self.entries[key].delete(0, tk.END)
                self.entries[key].insert(0, str(self.config[key]))

    def toggle_program(self):
        global is_running
        if not is_running:
            self.start_program()
        else:
            self.stop_program()

    def start_program(self):
        global is_running
        with lock:
            if not is_running:
                is_running = True
                self.start_btn.config(text="停止")
                ConfigManager.save_config(self.config)
                self.mouse_listener_thread = threading.Thread(target=self.mouse_listener)
                self.mouse_listener_thread.daemon = True
                self.mouse_listener_thread.start()
                self.thread = RecoilThread(self.config)
                self.thread.start()

    def stop_program(self):
        global is_running
        with lock:
            if is_running:
                is_running = False
                self.start_btn.config(text="启动")
                if self.thread and self.thread.is_alive():
                    self.thread.join(timeout=0.1)

    def mouse_listener(self):
        global mouse_pressed
        prev_state = win32api.GetKeyState(win32con.VK_LBUTTON)
        
        while is_running:
            current_state = win32api.GetKeyState(win32con.VK_LBUTTON)
            if current_state != prev_state:
                mouse_pressed = current_state < 0
                prev_state = current_state
            time.sleep(0.01)

    def on_close(self):
        self.stop_program()
        self.destroy()

if __name__ == "__main__":
    app = Application()
    app.mainloop()
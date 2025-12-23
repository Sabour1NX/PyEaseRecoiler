# 注：低代码平台生成



import os
import json
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

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

class CompConfigEditor:
    def __init__(self, master):
        self.master = master
        master.title("ComplexEditor")
        master.geometry("500x300")
        self.current_section = 0
        self.config = DEFAULT_CONFIG.copy()
        self.filename = "未命名配置"
        self.var_dict = {}
        self.create_widgets()
        self.update_display()

    def create_widgets(self):
        toolbar = ttk.Frame(self.master)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(toolbar, text="加载配置", command=self.load_config).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="保存配置", command=self.save_config).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="新增段", command=self.add_section).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="删除段", command=self.delete_section).pack(side=tk.LEFT)
        self.filename_label = ttk.Label(toolbar, text=f"当前文件: {self.filename}")
        self.filename_label.pack(side=tk.RIGHT)
        edit_frame = ttk.LabelFrame(self.master, text="参数编辑")
        edit_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        params = [
            ("isExecuteTime", "执行时间(ms)", 0, 2000),
            ("distance", "移动距离", 0, 50),
            ("angle", "移动角度", 0, 360),
            ("activation_delay", "启动延迟", 0, 500),
            ("interval", "间隔基准", 0, 200),
            ("random_interval", "随机偏移", 0, 100)
        ]

        self.entries = {}
        self.sliders = {}
        for i, (key, label, min_val, max_val) in enumerate(params):
            frame = ttk.Frame(edit_frame)
            frame.grid(row=i, column=0, sticky="ew", padx=5, pady=2)
            
            ttk.Label(frame, text=label, width=15).pack(side=tk.LEFT)
            
            self.var_dict[key] = tk.IntVar()
            
            slider = ttk.Scale(frame, from_=min_val, to=max_val, 
                             variable=self.var_dict[key],
                             command=lambda v, k=key: self.slider_changed(k, v))
            slider.pack(side=tk.LEFT, expand=True, fill=tk.X)
            self.sliders[key] = slider
            
            entry = ttk.Entry(frame, width=8)
            entry.bind("<Return>", lambda e, k=key: self.entry_changed(k))
            entry.pack(side=tk.LEFT, padx=5)
            self.entries[key] = entry

        nav_frame = ttk.Frame(self.master)
        nav_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(nav_frame, text="-", width=3, command=lambda: self.change_section(-1)).pack(side=tk.LEFT)
        self.section_label = ttk.Label(nav_frame, text="1/1")
        self.section_label.pack(side=tk.LEFT, padx=10)
        ttk.Button(nav_frame, text="+", width=3, command=lambda: self.change_section(1)).pack(side=tk.LEFT)

    def update_display(self):
        if not self.config["stages"]:
            return
            
        current_stage = self.config["stages"][self.current_section]
        for key in self.var_dict:
            self.var_dict[key].set(current_stage.get(key, 0))
            self.entries[key].delete(0, tk.END)
            self.entries[key].insert(0, str(current_stage.get(key, 0)))
            
        total = len(self.config["stages"])
        self.section_label.config(text=f"{self.current_section+1}/{total}")
        self.filename_label.config(text=f"当前文件: {self.filename}")

    def slider_changed(self, key, value):
        value = int(float(value))
        self.entries[key].delete(0, tk.END)
        self.entries[key].insert(0, str(value))
        self.save_current_section()

    def entry_changed(self, key):
        try:
            value = int(self.entries[key].get())
            slider = self.sliders[key]
            min_val = slider.cget("from")
            max_val = slider.cget("to")
            value = max(min_val, min(value, max_val))
            self.var_dict[key].set(value)
            self.save_current_section()
        except:
            pass

    def save_current_section(self):
        if not self.config["stages"]:
            return
            
        current_stage = self.config["stages"][self.current_section]
        for key in self.var_dict:
            current_stage[key] = self.var_dict[key].get()

    def change_section(self, delta):
        self.save_current_section()
        new_index = self.current_section + delta
        
        if 0 <= new_index < len(self.config["stages"]):
            self.current_section = new_index
        elif new_index >= len(self.config["stages"]):
            self.add_section()
            self.current_section = len(self.config["stages"]) - 1
            
        self.update_display()

    def add_section(self):
        new_section = {
            "isExecuteTime": 300,
            "distance": 10,
            "angle": 90,
            "activation_delay": 50,
            "interval": 100,
            "random_interval": 20
        }
        self.config["stages"].append(new_section)
        self.update_display()

    def delete_section(self):
        if len(self.config["stages"]) > 1:
            del self.config["stages"][self.current_section]
            if self.current_section >= len(self.config["stages"]):
                self.current_section = len(self.config["stages"]) - 1
            self.update_display()

    def load_config(self):
        initial_dir = os.path.join(os.getcwd(), "recoil_config_Comp")
        path = filedialog.askopenfilename(
            initialdir=initial_dir,
            filetypes=[("JSON文件", "*.json")]
        )
        if path:
            try:
                with open(path, 'r') as f:
                    self.config = json.load(f)
                    self.current_section = 0
                    self.filename = os.path.basename(path)
                    self.update_display()
            except Exception as e:
                messagebox.showerror("错误", f"加载失败: {str(e)}")

    def save_config(self):
        self.save_current_section()
        initial_dir = os.path.join(os.getcwd(), "recoil_config_Comp")
        if not os.path.exists(initial_dir):
            os.makedirs(initial_dir)
            
        default_name = self.filename if self.filename != "未命名配置" else f"config_{int(time.time())}.json"
        path = filedialog.asksaveasfilename(
            initialdir=initial_dir,
            initialfile=default_name,
            filetypes=[("JSON文件", "*.json")]
        )
        if path:
            if not path.endswith(".json"):
                path += ".json"
            try:
                with open(path, 'w') as f:
                    json.dump(self.config, f, indent=4)
                    self.filename = os.path.basename(path)
                    self.update_display()
            except Exception as e:
                messagebox.showerror("错误", f"保存失败: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = CompConfigEditor(root)
    root.mainloop()
import threading
import win32api
import time
import json
import os
import shutil
import tkinter as tk
import customtkinter as ctk
from yolov8检测模块 import *
from 罗技旧版调用 import 罗技驱动键鼠初始化
from PID自瞄算法模块 import PID初始化
from 仿生轨迹模块 import 生成贝塞尔曲线轨迹

running = True
自瞄开启 = False

CONFIG_FILE = "settings.json"

# 【优化1：多套预设配置架构】
DEFAULT_PROFILES = {
    "步枪/冲锋 (常规)": {
        "kp": 0.6, "kd": 0.012, "平滑": 0.65, "死区": 2.0, 
        "视觉平滑": 0.20, "粘滞半径": 120, "切换延迟时间": 0.35, 
        "锁头比例": 0.30, "微观磁吸": 1.5, "坐标防抖": 3.0
    },
    "狙击/沙鹰 (单发硬锁)": {
        "kp": 0.85, "kd": 0.005, "平滑": 0.85, "死区": 1.5, 
        "视觉平滑": 0.10, "粘滞半径": 80, "切换延迟时间": 0.50, 
        "锁头比例": 0.40, "微观磁吸": 2.5, "坐标防抖": 2.0
    }
}

current_profile_name = "步枪/冲锋 (常规)"
config = DEFAULT_PROFILES[current_profile_name].copy()
all_profiles = DEFAULT_PROFILES.copy()

# --- 【优化2：高级配置存档模块】 ---
def load_config():
    global config, all_profiles, current_profile_name
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                
                # 兼容旧版本单配置格式或新版本多配置格式
                if "profiles" in data:
                    all_profiles = data["profiles"]
                    current_profile_name = data.get("current_profile", "步枪/冲锋 (常规)")
                else:
                    all_profiles["步枪/冲锋 (常规)"].update(data)
                    current_profile_name = "步枪/冲锋 (常规)"
                
                # 确保当前配置存在，提取参数
                if current_profile_name not in all_profiles:
                    current_profile_name = list(all_profiles.keys())[0]
                config = all_profiles[current_profile_name].copy()
            print(f"成功加载配置方案: {current_profile_name}")
        except Exception as e:
            print(f"配置加载失败，使用默认参数: {e}")

def save_config():
    """【优化3：防崩溃的原子化安全写入】"""
    global config, all_profiles, current_profile_name
    try:
        # 将当前活跃配置同步回总集
        all_profiles[current_profile_name] = config.copy()
        
        save_data = {
            "current_profile": current_profile_name,
            "profiles": all_profiles
        }
        
        # 先写入临时文件
        temp_file = CONFIG_FILE + ".tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(save_data, f, indent=4, ensure_ascii=False)
            
        # 写入成功后，原子化替换原文件，杜绝0kb损坏
        os.replace(temp_file, CONFIG_FILE)
    except Exception as e:
        print(f"配置后台保存失败: {e}")

# 程序启动时读取配置
load_config()

def 精准延时(秒数):
    目标时间 = time.perf_counter() + 秒数
    while time.perf_counter() < 目标时间:
        time.sleep(0)

def aimbot_thread():
    global 自瞄开启, config
    
    mouse = 罗技驱动键鼠初始化()
    yolo = YOLOv8初始化("cs2-10万数据集四个目标.onnx")
    
    pid_x = PID初始化(0.01, config["kp"], 0.0, config["kd"])
    pid_y = PID初始化(0.01, config["kp"], 0.0, config["kd"])
    
    SCREEN_CX, SCREEN_CY = yolo.屏幕宽度 // 2, yolo.屏幕高度 // 2
    上次移动X, 上次移动Y = 0, 0
    上次视觉X, 上次视觉Y = 320, 320
    
    上次目标中心X, 上次目标中心Y = 0, 0
    切换禁令截止时间 = 0  
    上次时间 = time.perf_counter()
    锚点X, 锚点Y = 0, 0
    
    while running:
        if win32api.GetAsyncKeyState(0x77) & 1:
            自瞄开启 = not 自瞄开启
            
        if not 自瞄开启:
            精准延时(0.01)
            上次时间 = time.perf_counter()
            锚点X = 锚点Y = 0
            continue

        当前时间 = time.perf_counter()
        动态dt = 当前时间 - 上次时间
        if 动态dt <= 0: 动态dt = 0.001
        上次时间 = 当前时间

        try:
            pid_x.dt = pid_y.dt = 动态dt
        except:
            pass

        结果列表 = yolo.执行检测(
            左上X=SCREEN_CX-320, 左上Y=SCREEN_CY-320, 
            右下X=SCREEN_CX+320, 右下Y=SCREEN_CY+320, 
            置信度阈值=0.45, 显示画面=False
        )

        按下开火键 = win32api.GetAsyncKeyState(0x01)

        if 按下开火键:
            最佳目标 = None
            
            if 上次目标中心X != 0:
                最近距离 = 99999
                for 目标 in 结果列表:
                    预估偏移 = int(目标['高度'] * config["锁头比例"])
                    目标头部Y = 目标['中心Y'] - 预估偏移
                    距离 = ((目标['中心X'] - 上次目标中心X)**2 + (目标头部Y - 上次目标中心Y)**2)**0.5
                    
                    if 距离 < 最近距离:
                        最近距离 = 距离
                        最佳目标 = 目标
                
                if 最近距离 > config["粘滞半径"]:
                    最佳目标 = None
                    切换禁令截止时间 = 当前时间 + config["切换延迟时间"]
                    上次目标中心X = 上次目标中心Y = 上次移动X = 上次移动Y = 0
                    上次视觉X = 上次视觉Y = 320
                    锚点X = 锚点Y = 0
            
            if 上次目标中心X == 0:
                if 当前时间 < 切换禁令截止时间:
                    最佳目标 = None
                else:
                    最近准星距离 = 99999
                    for 目标 in 结果列表:
                        预估偏移 = int(目标['高度'] * config["锁头比例"])
                        目标头部Y = 目标['中心Y'] - 预估偏移
                        准星距离 = ((目标['中心X'] - 320)**2 + (目标头部Y - 320)**2)**0.5
                        
                        if 准星距离 < 最近准星距离:
                            最近准星距离 = 准星距离
                            最佳目标 = 目标
                            
                    if 最佳目标:
                        try:
                            pid_x.上次偏差 = pid_y.上次偏差 = 0
                        except: pass
                        切换禁令截止时间 = 0

            if 最佳目标:
                上次目标中心X = 最佳目标['中心X']
                目标当前X = 最佳目标['中心X']
                偏移量 = int(最佳目标['高度'] * config["锁头比例"])
                目标当前Y = 最佳目标['中心Y'] - 偏移量
                上次目标中心Y = 目标当前Y
                
                if 锚点X == 0:
                    锚点X, 锚点Y = 目标当前X, 目标当前Y
                else:
                    跳动偏差 = ((目标当前X - 锚点X)**2 + (目标当前Y - 锚点Y)**2)**0.5
                    if 跳动偏差 > config["坐标防抖"]:
                        锚点X = 锚点X * 0.5 + 目标当前X * 0.5
                        锚点Y = 锚点Y * 0.5 + 目标当前Y * 0.5
                    else:
                        目标当前X, 目标当前Y = 锚点X, 锚点Y
                
                v_smooth = config["视觉平滑"]
                平滑后X = 上次视觉X * (1 - v_smooth) + 目标当前X * v_smooth
                平滑后Y = 上次视觉Y * (1 - v_smooth) + 目标当前Y * v_smooth
                
                上次视觉X, 上次视觉Y = 平滑后X, 平滑后Y

                偏差X = 平滑后X - 320
                偏差Y = 平滑后Y - 320
                综合距离 = (偏差X**2 + 偏差Y**2)**0.5

                if 综合距离 < config["死区"]:
                    最终X = 最终Y = 0
                    上次移动X = 上次移动Y = 0
                    try:
                        pid_x.上次偏差 = pid_y.上次偏差 = 0
                    except: pass
                else:
                    有效距离 = min(综合距离, 80.0)
                    距离比例 = 有效距离 / 80.0 

                    动态Kp = config["kp"] + config["kp"] * (config["微观磁吸"] - 1.0) * (1.0 - 距离比例)
                    
                    pid_x.kp = 动态Kp
                    pid_y.kp = 动态Kp
                    pid_x.kd = pid_y.kd = config["kd"]

                    计算X = pid_x.PID算法_Position_X(320 + 偏差X, 320)
                    计算Y = pid_y.PID算法_Position_Y(320 + 偏差Y, 320)
                    
                    基础平滑 = max(0.15, config["平滑"] * 0.3)
                    动态平滑 = 基础平滑 + (config["平滑"] - 基础平滑) * 距离比例
                    
                    最终X = 上次移动X * (1 - 动态平滑) + 计算X * 动态平滑
                    最终Y = 上次移动Y * (1 - 动态平滑) + 计算Y * 动态平滑
                    
                    最终X = max(-35.0, min(35.0, 最终X))
                    最终Y = max(-35.0, min(35.0, 最终Y))
                    
                    步长序列 = 生成贝塞尔曲线轨迹(最终X, 最终Y, 步数=3)
                    for 步X, 步Y in 步长序列:
                        mouse.相对移动卡尔曼(步X, 步Y, 步数=2, 噪声=0)
                    
                    上次移动X, 上次移动Y = 最终X, 最终Y
            else:
                锚点X = 锚点Y = 0
                if 上次目标中心X == 0:
                    上次移动X = 上次移动Y = 0
        else:
            上次目标中心X = 上次目标中心Y = 上次移动X = 上次移动Y = 0
            上次视觉X = 上次视觉Y = 320
            锚点X = 锚点Y = 0
            切换禁令截止时间 = 0
            try:
                pid_x.上次偏差 = pid_y.上次偏差 = 0
            except: pass
        
        精准延时(0.002)

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        if self.tipwindow or not self.text:
            return
        x = self.widget.winfo_rootx() + 25
        y = self.widget.winfo_rooty() + 20
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tw.attributes("-topmost", True)
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                         background="#333333", foreground="#FFFFFF", 
                         relief=tk.FLAT, font=("Microsoft YaHei", 10))
        label.pack(ipadx=8, ipady=4)

    def hide_tip(self, event=None):
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("System Host Process 配置")
        self.geometry("420x820")  # 调整高度适应新UI
        ctk.set_appearance_mode("dark")
        
        # 顶部标题与预设选择区域
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(pady=(15, 10), fill="x", padx=20)
        
        self.label_title = ctk.CTkLabel(header_frame, text="物理引擎参数微调", font=("Microsoft YaHei", 20, "bold"))
        self.label_title.pack()

        # 方案切换下拉菜单
        self.profile_var = ctk.StringVar(value=current_profile_name)
        self.profile_menu = ctk.CTkOptionMenu(
            header_frame, 
            values=list(all_profiles.keys()),
            variable=self.profile_var,
            command=self.change_profile,
            font=("Microsoft YaHei", 12),
            fg_color="#2b719e",
            button_color="#1f5374"
        )
        self.profile_menu.pack(pady=(10, 0))

        # 保存所有滑块对象的字典，以便动态更新
        self.sliders = {}

        self.create_slider("远距离爆发拉力", "kp", 0.1, 0.8, "决定准星开始移动时的初速度。\n调大更暴力，调小更平滑。")
        self.create_slider("近距离磁吸倍率", "微观磁吸", 1.0, 3.0, "靠近目标时的额外拉力倍数。")
        self.create_slider("准星急停防抖", "kd", 0.0, 0.05, "靠近目标时的减速力度。")
        self.create_slider("模型识别防抖", "坐标防抖", 0.0, 8.0, "强行过滤YOLO识别框的闪烁。推荐3.0左右。")
        self.create_slider("绝对静止死区", "死区", 0.0, 5.0, "进入该范围准星彻底断连。建议配合防抖使用，设在1.5到3.0之间。")
        self.create_slider("拉枪拟真度", "平滑", 0.1, 1.0, "数值越大，响应越直接；数值越小，越圆润。")
        self.create_slider("视觉坐标平滑", "视觉平滑", 0.05, 0.9, "基础坐标过渡速度。")
        self.create_slider("目标强锁半径", "粘滞半径", 50, 200, "连续跟踪一个目标的有效距离。")
        self.create_slider("目标切换延迟", "切换延迟时间", 0.0, 1.0, "当前目标消失后，阻断锁定新目标的时间。")
        self.create_slider("锁头偏移比例", "锁头比例", 0.0, 0.5, "0代表肚子，0.5代表头皮。")

        # 底部开关
        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.pack(pady=10)

        self.switch_var = ctk.StringVar(value="off")
        self.switch = ctk.CTkSwitch(bottom_frame, text="自瞄主开关 (F8)", command=self.toggle_aim,
                                    variable=self.switch_var, onvalue="on", offvalue="off")
        self.switch.pack()
        
        # 增加后台自动保存的提示标签（取代原来的手动保存按钮）
        self.save_status_label = ctk.CTkLabel(self, text="✔️ 参数修改已自动安全保存", text_color="gray", font=("Microsoft YaHei", 10))
        self.save_status_label.pack(side="bottom", pady=(0, 10))

        self.label_hotkey = ctk.CTkLabel(self, text="按 Insert 键隐藏/呼出本界面", text_color="#aaaaaa", font=("Microsoft YaHei", 12))
        self.label_hotkey.pack(side="bottom", pady=5)

        self.is_ui_visible = True
        self.check_visibility_hotkey()

    def change_profile(self, selected_profile):
        """切换配置方案时，更新当前 config 并刷新所有滑块的显示"""
        global config, current_profile_name
        current_profile_name = selected_profile
        config = all_profiles[selected_profile].copy()
        
        for key, elements in self.sliders.items():
            elements['slider'].set(config[key])
            elements['label'].configure(text=f"{elements['text']}: {config[key]:.3f}")
        
        save_config()
        self.flash_save_status()

    def check_visibility_hotkey(self):
        if win32api.GetAsyncKeyState(0x2D) & 1:
            if self.is_ui_visible:
                self.withdraw()
                self.is_ui_visible = False
            else:
                self.deiconify()
                self.is_ui_visible = True
                
        self.after(50, self.check_visibility_hotkey)

    def create_slider(self, text, key, from_, to_, desc):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="x", padx=20)
        
        label = ctk.CTkLabel(frame, text=f"{text}: {config[key]:.3f}", font=("Microsoft YaHei", 13))
        label.pack(side="left")
        
        info = ctk.CTkLabel(frame, text=" [?]", text_color="#1f6aa5", font=("Microsoft YaHei", 13, "bold"), cursor="hand2")
        info.pack(side="left")
        ToolTip(info, desc)

        def update_val(val):
            # 滑块拖动时实时更新内存参数
            config[key] = float(val)
            label.configure(text=f"{text}: {config[key]:.3f}")

        def on_slider_release(event):
            # 滑块松开时触发静默后台保存
            save_config()
            self.flash_save_status()

        slider = ctk.CTkSlider(self, from_=from_, to=to_, command=update_val)
        slider.set(config[key])
        slider.bind("<ButtonRelease-1>", on_slider_release)
        slider.pack(pady=(0, 6), padx=20, fill="x")
        
        # 记录引用以便切换方案时更新
        self.sliders[key] = {'slider': slider, 'label': label, 'text': text}

    def flash_save_status(self):
        """让底部的自动保存提示闪烁一下绿光"""
        self.save_status_label.configure(text_color="#28a745")
        def reset_color():
            self.save_status_label.configure(text_color="gray")
        self.after(800, reset_color)

    def toggle_aim(self):
        global 自瞄开启
        自瞄开启 = (self.switch_var.get() == "on")

def main():
    global running
    t = threading.Thread(target=aimbot_thread, daemon=True)
    t.start()
    
    app = App()
    app.mainloop()
    running = False

if __name__ == "__main__":
    main()
import time,os,sys,ctypes
from ctypes import wintypes


user32 = ctypes.windll.user32
def find_dll(dll_name):
    # 获取系统的 PATH 环境变量
    paths = os.environ.get("PATH", "").split(os.pathsep)

    # 在每个路径下查找是否有该 DLL
    for path in paths:
        potential_path = os.path.join(path, dll_name)
        if os.path.exists(potential_path):
            return os.path.abspath(potential_path)

    return None

def ClientToScreen(hwnd, x, y) -> tuple:
    point = ctypes.wintypes.POINT()
    point.x = x
    point.y = y
    is_ok: bool = user32.ClientToScreen(hwnd, ctypes.byref(point))
    if not is_ok:
        raise Exception('call ClientToScreen failed')
    return (point.x, point.y)
def 切换输入法为英语美国():
    # 加载 user32.dll 和 kernel32.dll
    user32 = ctypes.WinDLL('user32', use_last_error=True)
    kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

    # 常量定义
    WM_INPUTLANGCHANGEREQUEST = 0x0050
    HWND_BROADCAST = 0xFFFF
    KLF_ACTIVATE = 0x00000001
    KL_INPUTLANGCHANGE = 0x0001  # 触发输入语言更改

    # 英语（美国）的 KLID
    KLID_ENGLISH_US = "00000409"

    # 定义函数原型
    user32.LoadKeyboardLayoutW.argtypes = [wintypes.LPCWSTR, wintypes.UINT]
    user32.LoadKeyboardLayoutW.restype = wintypes.HKL

    user32.ActivateKeyboardLayout.argtypes = [wintypes.HKL, wintypes.UINT]
    user32.ActivateKeyboardLayout.restype = wintypes.HKL

    user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    user32.PostMessageW.restype = wintypes.BOOL

    kernel32.GetLastError.restype = wintypes.DWORD
    kernel32.GetLastError.argtypes = []

    # 步骤 1: 加载英语（美国）键盘布局
    hkl_english = user32.LoadKeyboardLayoutW(KLID_ENGLISH_US, KLF_ACTIVATE)
    if not hkl_english:
        error_code = kernel32.GetLastError()
        print(f"无法加载英语（美国）输入法，错误代码: {error_code}")
        return
    else:
        print(f"已加载英语（美国）输入法，HKL: {hkl_english:#010x}")

    # 步骤 2: 激活英语（美国）键盘布局
    activated_hkl = user32.ActivateKeyboardLayout(hkl_english, KL_INPUTLANGCHANGE)
    if not activated_hkl:
        error_code = kernel32.GetLastError()
        print(f"无法激活英语（美国）输入法，错误代码: {error_code}")
    else:
        print(f"已激活英语（美国）输入法，HKL: {activated_hkl:#010x}")

    # 步骤 3: 通过消息广播请求切换输入法
    result = user32.PostMessageW(HWND_BROADCAST, WM_INPUTLANGCHANGEREQUEST, 0, hkl_english)
    if not result:
        error_code = kernel32.GetLastError()
        print(f"无法通过消息广播切换到英语（美国）输入法，错误代码: {error_code}")
    else:
        print("已通过消息广播切换到英语（美国）输入法")

    # 可选步骤: 确认当前输入法
    user32.GetKeyboardLayout.restype = wintypes.HKL
    user32.GetKeyboardLayout.argtypes = [wintypes.DWORD]
    current_hkl = user32.GetKeyboardLayout(0)
    print(f"当前活动的键盘布局 HKL: {current_hkl:#010x}")

class KMLJ:
    keys = [
        "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m",
        "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z",
        "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"
    ]
    shift_keys = {
        "!": "1",
        "@": "2",
        "#": "3",
        "$": "4",
        "%": "5",
        "^": "6",
        "&": "7",
        "*": "8",
        "(": "9",
        ")": "0"
    }

    vk_key_map = {
        'shift': 0x10,
        'ctrl': 0x11,
        'alt': 0x12,
        ':capslock': 0x14,
        'tab': 0x09,
        'enter': 0x0D,
        'esc': 0x1B,
        'space': 0x20,
        'backspace': 0x08,
    }
    gm = None
    def __init__(self, hwnd=0):
        if not sys.maxsize > 2 ** 32:
            raise ValueError('KMLJ不支持32,请使用64位python!!!')

        self.hwnd = hwnd

        device_path = os.path.join(os.path.dirname(__file__),"lj.dll")
        if not device_path:
            raise ValueError(f"找不到 {device_path}")
        try:
            if KMLJ.gm is None:
                self.gm = ctypes.CDLL(device_path)
                self.gm.device_close()
                self.gmok = self.gm.device_open() == 1
                if not self.gmok:
                    raise ValueError('未安装ghub或者lgs驱动!!!')
                else:
                    print('初始化成功!')
            else:
                self.gm = KMLJ.gm
        except FileNotFoundError:
            raise ValueError('缺少文件!!!')
        self.init_mouse()
        self.init_keypress()
        self.now_x, self.now_y = self.GetCursorPos()
        self.key_delay = 0.01
        self.mouse_delay = 0.01
        self.all_up()

    def __del__(self):
        self.all_up()

    def all_up(self):
        for key in self.keys:
            self.KeyUpChar(key)
        self.LeftUp()
        self.RightUp()

    def release(self):
        self.init_mouse()
        self.init_keypress()

    def init_mouse(self):
        self.LeftUp()
        self.RightUp()

    def init_keypress(self):
        for key in self.keys:
            self.KeyUpChar(key)

    def set_delay(self, key_delay=0.01, mouse_delay=0.01):
        self.key_delay = key_delay
        self.mouse_delay = mouse_delay

    # 按下鼠标按键
    def LeftDown(self):
        self.gm.mouse_down(1)

    # 松开鼠标按键
    def LeftUp(self):
        self.gm.mouse_up(1)

    def RightDown(self):
        self.gm.mouse_down(3)

    def RightUp(self):
        self.gm.mouse_up(3)

    def LeftClick(self):
        self.LeftDown()
        time.sleep(self.mouse_delay)
        self.LeftUp()

    def RightClick(self):
        self.RightDown()
        time.sleep(self.mouse_delay)
        self.RightUp()

    def KeyDownChar(self, code: str):
        if code.isupper():
            code = code.lower()
            self.press_capslock(True)
        else:
            self.press_capslock(False)
        if code in self.shift_keys:
            self.press_controller_down("shift")
            self.gm.key_down(self.shift_keys[code])


        self.gm.key_down(code)


    def KeyUpChar(self, code: str):
        if code.isupper():
            code = code.lower()
        self.gm.key_up(code)
        if code in self.shift_keys:                  # 弹起特殊操控键
            self.press_controller_up("shift")


    def KeyPressChar(self, code: str):
        self.KeyDownChar(code)
        time.sleep(self.key_delay)
        self.KeyUpChar(code)

    def MoveTo(self, x: int, y: int):
        self.now_x, self.now_y = self.GetCursorPos()
        if self.hwnd:
            x, y = ClientToScreen(self.hwnd, x, y)
        self.MoveR(x - self.now_x, y - self.now_y)

    def MoveR(self, x: int, y: int):
        self.gm.moveR(int(x), int(y), False)
        self.now_x, self.now_y = self.now_x + x, self.now_y + y

    def KeyPressStr(self, key_str: str, delay: float = 0.01):
        for i in key_str:
            self.KeyPressChar(i)
            time.sleep(delay)

    def slide(self, x1: int, y1: int, x2: int, y2: int, delay=1):
        self.MoveTo(x1, y1)
        time.sleep(0.01)
        self.LeftDown()
        time.sleep(0.01)
        self.MoveR(x2 - x1, y2 - y1)
        self.LeftUp()
        time.sleep(delay)

    @staticmethod
    def GetCursorPos():
        class POINT(ctypes.Structure):
            _fields_ = [
                ("x", ctypes.c_long),
                ("y", ctypes.c_long)
            ]

        point = POINT()
        user32.GetCursorPos(ctypes.byref(point))
        return point.x, point.y

    # 模拟按下 Caps Lock 键
    def press_capslock(self, open=True):
        if open:
            if not user32.GetKeyState(self.vk_key_map[":capslock"]) & 1:
                self.press_controller_key(":capslock")
        else:
            if user32.GetKeyState(self.vk_key_map[":capslock"]) & 1:
                self.press_controller_key(":capslock")

    def press_controller_key(self, key):
        self.press_controller_down(key)
        time.sleep(self.key_delay)
        self.press_controller_up(key)

    def press_controller_down(self, key):
        if not key in self.vk_key_map:
            raise ValueError("无效的按键")
        user32.keybd_event(self.vk_key_map[key], 0, 0, 0)

    def press_controller_up(self, key):
        if not key in self.vk_key_map:
            raise ValueError("无效的按键")
        # 模拟释放 Caps Lock
        user32.keybd_event(self.vk_key_map[key], 0, 2, 0)

class 罗技驱动键鼠初始化:
    def __init__(self,句柄=0):
        #句柄 = 0  # 表示桌面窗口
        self.km = KMLJ(句柄)

    def __del__(self):
        self.km.__del__()

    def 设置间隔(self, 按键间隔=0.01, 鼠标间隔=0.01):
        self.km.set_delay(按键间隔, 鼠标间隔)

    # 按下鼠标按键
    def 鼠标左键按下(self):
        self.km.LeftDown()

    # 松开鼠标按键
    def 鼠标左键抬起(self):
        self.km.LeftUp()

    def 鼠标右键按下(self):
        self.km.RightDown()

    def 鼠标右键抬起(self):
        self.km.RightUp()

    def 鼠标左键点击(self):
        """
        鼠标左键原地点击,一般要配合绝对移动，在点击
        :return:
        """
        self.km.LeftClick()

    def 鼠标右键点击(self):
        """
        鼠标右键原地点击,一般要配合绝对移动，在点击
        :return:
        """
        self.km.RightClick()

    def 按键按下(self, 按键字符: str):
        """
        只支持a-z，0-9
        :param 按键字符: 比如"a",或者"b"，单个字符
        :return:
        """
        self.km.KeyDownChar(按键字符)



    def 按键抬起(self, 按键字符: str):
        """
        只支持a-z，0-9
        :param 按键字符: 比如"a",或者"b"，单个字符
        :return:
        """
        self.km.KeyUpChar(按键字符)


    def 按键(self, 按键字符: str):
        """
        按下并抬起某个键
        只支持a-z，0-9
        :param 按键字符: 比如"a",或者"b"，单个字符
        :return:
        """
        self.km.KeyPressStr(按键字符)

    def 绝对移动(self, x: int, y: int):
        """
        绝对移动
        :param x: 横坐标
        :param y: 纵坐标
        :return:
        """
        self.km.MoveTo(x, y)

    def 相对移动(self, x: int, y: int):
        """
        相对当前位置进行移动，可以是负数，表示相反方向
        :param x: 横坐标
        :param y: 纵坐标
        :return:
        """
        self.km.MoveR(x, y)


    def 按键输出字符串(self, 字符串: str, 字符串间隔: float = 0.01):
        """
        :param 字符串: 只支持a-z,0-9
        :param 字符串间隔: 默认0.01秒
        :return:
        """
        self.km.KeyPressStr(字符串, 字符串间隔)

    def 滑动(self, x1: int, y1: int, x2: int, y2: int, 间隔=1):
        """
        :param x1:横坐标
        :param y1: 纵坐标
        :param x2: 横坐标
        :param y2: 纵坐标
        :param 间隔: 单位秒
        :return:
        """
        self.km.slide(x1, y1, x2, y2, 间隔)
    def 获取鼠标坐标(self):
        """
        获取鼠标当前位置
        :return: (x,y)
        """
        x, y = self.km.GetCursorPos()
        print("当前鼠标位置:", x, y)
        return x, y
    def 相对移动卡尔曼(self, x: int, y: int, 步数: int = 15, 噪声: float = 0.5):
        """
        使用卡尔曼滤波进行平滑的相对移动
        :param x: 相对横坐标偏移量
        :param y: 相对纵坐标偏移量
        :param 步数: 移动分解的步数，越多越平滑
        :param 噪声: 噪声系数，增加随机性使轨迹更自然
        :return:
        """
        import random
        
        # 简化的卡尔曼滤波参数
        过程噪声 = 0.01
        测量噪声 = 噪声
        
        # 初始化状态
        x估计 = 0
        y估计 = 0
        x误差 = 1
        y误差 = 1
        
        # 记录已移动的总距离
        已移动x = 0
        已移动y = 0
        
        for i in range(步数):
            # 最后一步直接移动到目标位置，确保精确
            if i == 步数 - 1:
                剩余x = x - 已移动x
                剩余y = y - 已移动y
                if 剩余x != 0 or 剩余y != 0:
                    self.km.MoveR(剩余x, 剩余y)
                break
            
            # 计算目标位置（线性插值）
            进度 = (i + 1) / 步数
            x目标 = x * 进度
            y目标 = y * 进度
            
            # 添加随机噪声模拟真实移动
            x测量 = x目标 + random.uniform(-噪声, 噪声)
            y测量 = y目标 + random.uniform(-噪声, 噪声)
            
            # 卡尔曼滤波预测
            x预测 = x估计
            y预测 = y估计
            x预测误差 = x误差 + 过程噪声
            y预测误差 = y误差 + 过程噪声
            
            # 卡尔曼增益
            x增益 = x预测误差 / (x预测误差 + 测量噪声)
            y增益 = y预测误差 / (y预测误差 + 测量噪声)
            
            # 更新估计
            x新估计 = x预测 + x增益 * (x测量 - x预测)
            y新估计 = y预测 + y增益 * (y测量 - y预测)
            
            # 计算本次移动增量
            dx = int(x新估计 - x估计)
            dy = int(y新估计 - y估计)
            
            # 执行相对移动
            if dx != 0 or dy != 0:
                self.km.MoveR(dx, dy)
                已移动x += dx
                已移动y += dy
                time.sleep(0.01)
            
            # 更新状态
            x估计 = x新估计
            y估计 = y新估计
            x误差 = (1 - x增益) * x预测误差
            y误差 = (1 - y增益) * y预测误差

    def 绝对移动卡尔曼(self, x: int, y: int, 步数: int = 15, 噪声: float = 0.5):
        """
        使用卡尔曼滤波进行平滑的绝对移动
        :param x: 目标横坐标
        :param y: 目标纵坐标
        :param 步数: 移动分解的步数，越多越平滑
        :param 噪声: 噪声系数，增加随机性使轨迹更自然
        :return:
        """
        import random
        import math
        
        # 获取起始位置
        起始x, 起始y = self.km.GetCursorPos()
        总偏移x = x - 起始x
        总偏移y = y - 起始y
        
        # 简化的卡尔曼滤波参数
        过程噪声 = 0.01
        测量噪声 = 噪声
        
        # 初始化状态
        x估计 = 0
        y估计 = 0
        x误差 = 1
        y误差 = 1
        
        # 记录已移动的总距离
        已移动x = 0
        已移动y = 0
        
        for i in range(步数):
            # 最后一步：获取当前实际位置，直接移动到目标
            if i == 步数 - 1:
                当前x, 当前y = self.km.GetCursorPos()
                剩余x = x - 当前x
                剩余y = y - 当前y
                if 剩余x != 0 or 剩余y != 0:
                    self.km.MoveR(剩余x, 剩余y)
                break
            
            # 使用缓动函数（ease-out）使移动更平滑
            进度 = (i + 1) / 步数
            # ease-out-cubic: 开始快，结束慢
            缓动进度 = 1 - math.pow(1 - 进度, 3)
            
            # 计算目标位置（使用缓动后的进度）
            x目标 = 总偏移x * 缓动进度
            y目标 = 总偏移y * 缓动进度
            
            # 添加随机噪声模拟真实移动
            x测量 = x目标 + random.uniform(-噪声, 噪声)
            y测量 = y目标 + random.uniform(-噪声, 噪声)
            
            # 卡尔曼滤波预测
            x预测 = x估计
            y预测 = y估计
            x预测误差 = x误差 + 过程噪声
            y预测误差 = y误差 + 过程噪声
            
            # 卡尔曼增益
            x增益 = x预测误差 / (x预测误差 + 测量噪声)
            y增益 = y预测误差 / (y预测误差 + 测量噪声)
            
            # 更新估计
            x新估计 = x预测 + x增益 * (x测量 - x预测)
            y新估计 = y预测 + y增益 * (y测量 - y预测)
            
            # 计算本次移动增量
            dx = int(x新估计 - x估计)
            dy = int(y新估计 - y估计)
            
            # 执行相对移动
            if dx != 0 or dy != 0:
                self.km.MoveR(dx, dy)
                已移动x += dx
                已移动y += dy
                time.sleep(0.01)
            
            # 更新状态
            x估计 = x新估计
            y估计 = y新估计
            x误差 = (1 - x增益) * x预测误差
            y误差 = (1 - y增益) * y预测误差

if __name__ == '__main__':
    import  time
    lj = 罗技驱动键鼠初始化()
    time.sleep(0.5)
    # 切换输入法为英语美国()
    # lj.按键输出字符串("abc123@") #只支持字母a-z,数字0-9
    lj.绝对移动(1577,699)
    time.sleep(0.5)
    lj.鼠标左键点击()
    # lj.相对移动(100,100)
    # lj.相对移动卡尔曼(603,403,步数=15,噪声=0.5)
    # lj.绝对移动卡尔曼(707,771,步数=15,噪声=0.5)
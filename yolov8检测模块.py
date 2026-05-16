import cv2
import numpy as np
import onnxruntime as ort
import win32gui
import win32ui
import win32con
import win32api

#pip install opencv-python numpy onnxruntime-directml pywin32

class YOLOv8初始化:
    """YOLOv8屏幕检测器 - 直接检测屏幕指定区域"""
    
    def __init__(self, 模型路径="sjzv8-640.onnx", 设备ID=0):
        """
        初始化检测器
        :param 模型路径: ONNX模型文件路径
        :param 设备ID: GPU设备ID
        """
        self.模型路径 = 模型路径
        self.设备ID = 设备ID
        self.类别列表 = ["0", "1", "2", "3"]
        self._窗口已创建 = False  # 标记窗口是否已创建
        
        # 加载模型
        self._加载模型()
        
        # 初始化屏幕捕获资源
        self.hwin = win32gui.GetDesktopWindow()
        self.hwindc = win32gui.GetWindowDC(self.hwin)
        self.srcdc = win32ui.CreateDCFromHandle(self.hwindc)
        self.memdc = self.srcdc.CreateCompatibleDC()
        
        # 获取屏幕尺寸
        self.屏幕宽度 = win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN)
        self.屏幕高度 = win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)
        
        print(f"屏幕捕获初始化完成: 屏幕尺寸 {self.屏幕宽度}x{self.屏幕高度}")
    
    def _加载模型(self):
        """加载ONNX模型"""
        sess_options = ort.SessionOptions()
        sess_options.log_severity_level = 3
        sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        
        # 获取可用的 providers
        available_providers = ort.get_available_providers()
        
        # 优先使用 GPU
        providers = []
        if 'DmlExecutionProvider' in available_providers:
            providers.append(('DmlExecutionProvider', {'device_id': self.设备ID}))
            print("使用 DirectML (GPU) 加速")
        elif 'CUDAExecutionProvider' in available_providers:
            providers.append('CUDAExecutionProvider')
            print("使用 CUDA (NVIDIA GPU) 加速")
        else:
            print("使用 CPU 运行")
        
        providers.append('CPUExecutionProvider')
        
        self.session = ort.InferenceSession(self.模型路径, sess_options, providers=providers)
        self.输入形状 = self.session.get_inputs()[0].shape
        
        # 处理动态形状（如 'height', 'width'）或固定形状（如 640）
        高度值 = self.输入形状[2]
        宽度值 = self.输入形状[3]
        
        # 如果是字符串或符号，使用默认值640
        self.输入高度 = int(高度值) if isinstance(高度值, (int, float)) else 640
        self.输入宽度 = int(宽度值) if isinstance(宽度值, (int, float)) else 640
        
        print(f"模型加载成功: {self.模型路径}, 输入尺寸: {self.输入宽度}x{self.输入高度}")
    
    def 截取屏幕(self, x, y, 宽度, 高度):
        """
        截取屏幕指定区域
        :param x: 左上角X坐标
        :param y: 左上角Y坐标
        :param 宽度: 截取宽度
        :param 高度: 截取高度
        :return: RGB图像
        """
        # 创建临时位图
        bmp = win32ui.CreateBitmap()
        bmp.CreateCompatibleBitmap(self.srcdc, 宽度, 高度)
        self.memdc.SelectObject(bmp)
        
        # 截取屏幕
        self.memdc.BitBlt((0, 0), (宽度, 高度), self.srcdc, (x, y), win32con.SRCCOPY)
        signed_ints_array = bmp.GetBitmapBits(True)
        img = np.frombuffer(signed_ints_array, dtype='uint8')
        img.shape = (高度, 宽度, 4)
        frame = cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)
        
        # 清理临时位图
        win32gui.DeleteObject(bmp.GetHandle())
        
        return frame
    
    def 预处理图像(self, 图像):
        """预处理图像用于模型推理"""
        img = cv2.resize(图像, (self.输入宽度, self.输入高度), interpolation=cv2.INTER_LINEAR)
        img = img.astype(np.float32) / 255.0
        img = img.transpose(2, 0, 1)
        return np.expand_dims(img, axis=0)
    
    def 后处理结果(self, 输出, 图像宽度, 图像高度, 置信度阈值=0.5, IOU阈值=0.5):
        """后处理模型输出"""
        输出 = 输出[0].astype(float).T
        boxes, scores, class_ids = [], [], []

        for row in 输出:
            confidence = np.max(row[4:])
            if confidence < 置信度阈值:
                continue

            class_id = np.argmax(row[4:])
            score = row[4 + class_id]
            cx, cy, w, h = row[:4]

            x1 = int((cx - w / 2) / self.输入宽度 * 图像宽度)
            y1 = int((cy - h / 2) / self.输入高度 * 图像高度)
            x2 = int((cx + w / 2) / self.输入宽度 * 图像宽度)
            y2 = int((cy + h / 2) / self.输入高度 * 图像高度)

            boxes.append([x1, y1, x2, y2])
            scores.append(score)
            class_ids.append(class_id)

        indices = cv2.dnn.NMSBoxes(boxes, scores, 置信度阈值, IOU阈值)

        检测结果 = []
        if len(indices) > 0:
            actual_indices = indices.flatten() if isinstance(indices, np.ndarray) else indices
            for i in actual_indices:
                box = boxes[i]
                x1, y1, x2, y2 = box[0], box[1], box[2], box[3]
                类别 = self.类别列表[class_ids[i]]
                置信度 = scores[i]
                
                检测结果.append({
                    '类别ID': int(类别),
                    '类别名称': 类别,
                    'x1': x1,
                    'y1': y1,
                    'x2': x2,
                    'y2': y2,
                    '宽度': x2 - x1,
                    '高度': y2 - y1,
                    '中心X': (x1 + x2) // 2,
                    '中心Y': (y1 + y2) // 2,
                    '置信度': float(置信度)
                })

        return 检测结果
    
    def 执行检测(self, 左上X=None, 左上Y=None, 右下X=None, 右下Y=None, 置信度阈值=0.5, IOU阈值=0.5, 显示画面=False):
        """
        执行一次完整的屏幕检测
        :param 左上X: 检测区域左上角X坐标（默认0，全屏）
        :param 左上Y: 检测区域左上角Y坐标（默认0，全屏）
        :param 右下X: 检测区域右下角X坐标（默认屏幕宽度，全屏）
        :param 右下Y: 检测区域右下角Y坐标（默认屏幕高度，全屏）
        :param 置信度阈值: 检测置信度阈值
        :param IOU阈值: NMS的IOU阈值
        :param 显示画面: 是否使用cv2显示检测画面
        :return: 检测结果列表
        """
        try:
            # 设置默认值为全屏
            if 左上X is None:
                左上X = 0
            else:
                左上X = int(左上X)
            if 左上Y is None:
                左上Y = 0
            else:
                左上Y = int(左上Y)
            if 右下X is None:
                右下X = self.屏幕宽度
            else:
                右下X = int(右下X)
            if 右下Y is None:
                右下Y = self.屏幕高度
            else:
                右下Y = int(右下Y)
            
            # 计算宽度和高度
            宽度 = 右下X - 左上X
            高度 = 右下Y - 左上Y
            
            # 1. 截取屏幕
            图像 = self.截取屏幕(左上X, 左上Y, 宽度, 高度)
            
            # 2. 预处理
            输入张量 = self.预处理图像(图像)
            
            # 3. 模型推理
            inputs = {self.session.get_inputs()[0].name: 输入张量}
            outputs = self.session.run(None, inputs)
            
            # 4. 后处理
            结果 = self.后处理结果(outputs[0], 图像.shape[1], 图像.shape[0], 置信度阈值, IOU阈值)
            
            # 5. 显示检测画面
            if 显示画面:
                self._显示检测画面(图像, 结果)
            
            return 结果
            
        except Exception as e:
            print(f"检测错误: {e}")
            return []
    
    def _显示检测画面(self, 图像, 检测结果):
        """
        使用cv2显示检测画面
        :param 图像: 原始图像
        :param 检测结果: 检测结果列表
        """
        显示图像 = 图像.copy()
        显示图像 = cv2.cvtColor(显示图像, cv2.COLOR_RGB2BGR)
        
        # 绘制检测框
        for 目标 in 检测结果:
            x1, y1, x2, y2 = 目标['x1'], 目标['y1'], 目标['x2'], 目标['y2']
            类别 = 目标['类别名称']
            置信度 = 目标['置信度']
            
            # 绘制矩形框
            cv2.rectangle(显示图像, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # 绘制标签
            标签 = f"{类别}: {置信度:.2%}"
            (文本宽, 文本高), _ = cv2.getTextSize(标签, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(显示图像, (x1, y1 - 文本高 - 5), (x1 + 文本宽, y1), (0, 255, 0), -1)
            cv2.putText(显示图像, 标签, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
        
        # 第一次调用时创建窗口，设置为检测画面的实际大小
        if not self._窗口已创建:
            cv2.namedWindow('YOLOv8检测', cv2.WINDOW_NORMAL)
            cv2.resizeWindow(
            'YOLOv8检测',
            显示图像.shape[1],
            显示图像.shape[0]
    )
            self._窗口已创建 = True
        
        # 显示图像（复用同一个窗口）
        cv2.imshow('YOLOv8检测', 显示图像)
        cv2.waitKey(1)  # 等待1ms，允许窗口刷新
    
    def 释放资源(self):
        """释放屏幕捕获资源"""
        try:
            cv2.destroyAllWindows()  # 关闭所有cv2窗口
            self.srcdc.DeleteDC()
            self.memdc.DeleteDC()
            win32gui.ReleaseDC(self.hwin, self.hwindc)
            print("资源已释放")
        except:
            pass


# 使用示例
if __name__ == "__main__":
    import time
    
    # 1. 初始化时只传入模型，支持所有v8所有尺寸
    检测器 = YOLOv8初始化(模型路径="sjzv8-640.onnx")
    
    try:
        print("\n开始检测屏幕...")
        # print("按 Ctrl+C 停止\n")
        
        while True:
            # 2. 检测时指定范围
            # 示例1: 检测全屏（默认），显示检测画面
            # 结果列表 = 检测器.执行检测(显示画面=True)

            # 示例2: 检测指定矩形区域（左上角到右下角）
            # 结果列表 = 检测器.执行检测(左上X=100, 左上Y=100, 右下X=500, 右下Y=500, 显示画面=True)
            # 结果列表 = 检测器.执行检测(218,280,460,660, 显示画面=True)

            # 示例3: 检测屏幕中心 640x640 区域
            中心X = 检测器.屏幕宽度 // 2
            中心Y = 检测器.屏幕高度 // 2
            结果列表 = 检测器.执行检测(左上X=中心X-320, 左上Y=中心Y-320, 右下X=中心X+320, 右下Y=中心Y+320, 显示画面=True)

            if 结果列表:
                print(f"检测到 {len(结果列表)} 个目标:")
                for i, 目标 in enumerate(结果列表, 1):
                    print(f"  [{i}] 类别: {目标['类别名称']} | "
                          f"位置: ({目标['x1']}, {目标['y1']}) -> ({目标['x2']}, {目标['y2']}) | "
                          f"中心: ({目标['中心X']}, {目标['中心Y']}) | "
                          f"尺寸: {目标['宽度']}x{目标['高度']} | "
                          f"置信度: {目标['置信度']:.2%}")
            else:
                print("未检测到目标")

            time.sleep(0.01)  # 控制检测频率
            
    except KeyboardInterrupt:
        print("\n\n检测已停止")
    finally:
        print("释放资源中...")
        检测器.释放资源()

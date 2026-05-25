import cv2
import numpy as np
import onnxruntime as ort
import win32gui
import win32ui
import win32con
import win32api
import traceback
import time

class YOLOv8初始化:
    """YOLOv8屏幕检测器 稳健基准版"""
    
    def __init__(self, 模型路径="cs2警0胸1头匪2胸3头.onnx", 设备ID=0, 自身阵营="匪"):
        """
        初始化检测器
        :param 模型路径: ONNX模型文件路径
        :param 设备ID: GPU设备ID
        :param 自身阵营: 阵营选项只能为 警 或 匪
        """
        if 自身阵营 not in ["警", "匪"]:
            raise ValueError("自身阵营只能为 警 或 匪")
            
        self.模型路径 = 模型路径
        self.设备ID = 设备ID
        self.类别列表 = ["警胸", "警头", "匪胸", "匪头"]
        self.自己阵营 = 自身阵营
        
        self.警类别ID = [0, 1]
        self.匪类别ID = [2, 3]
        
        self.部位映射 = {
            0: "胸部",
            1: "头部",
            2: "胸部",
            3: "头部"
        }
        
        self.配置模板 = [
            {"名称": "高精度", "置信度": 0.50, "IOU": 0.45, "渲染": False},
            {"名称": "调试", "置信度": 0.25, "IOU": 0.50, "渲染": True}
        ]
        self.当前模板索引 = 0
        
        self.hwin = None
        self.hwindc = None
        self.srcdc = None
        self.memdc = None
        self._窗口已创建 = False 
        
        self.颜色字典 = {
            "enemy_head": (0, 0, 255),
            "enemy_body": (0, 128, 255),
            "team_head": (255, 0, 0),
            "team_body": (255, 128, 0)
        }
        
        try:
            self._加载模型()
            self._初始化屏幕捕获()
        except Exception as e:
            traceback.print_exc()
            self.释放资源()
            raise

    def 切换参数模板(self, 索引):
        """在线切换预设参数模板"""
        if 0 <= 索引 < len(self.配置模板):
            self.当前模板索引 = 索引

    def _初始化屏幕捕获(self):
        """初始化屏幕捕获资源"""
        self.hwin = win32gui.GetDesktopWindow()
        self.hwindc = win32gui.GetWindowDC(self.hwin)
        self.srcdc = win32ui.CreateDCFromHandle(self.hwindc)
        self.memdc = self.srcdc.CreateCompatibleDC()
        
        self.屏幕宽度 = win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN)
        self.屏幕高度 = win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)

    def _加载模型(self):
        """安全加载ONNX模型"""
        sess_options = ort.SessionOptions()
        sess_options.log_severity_level = 3
        sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        
        available_providers = ort.get_available_providers()
        providers = []
        if 'DmlExecutionProvider' in available_providers:
            providers.append(('DmlExecutionProvider', {'device_id': self.设备ID}))
        elif 'CUDAExecutionProvider' in available_providers:
            providers.append('CUDAExecutionProvider')
        
        providers.append('CPUExecutionProvider')
        
        self.session = ort.InferenceSession(self.模型路径, sess_options, providers=providers)
        输入形状 = self.session.get_inputs()[0].shape
        
        高度值 = 输入形状[2]
        宽度值 = 输入形状[3]
        self.输入高度 = int(高度值) if isinstance(高度值, (int, float)) else 640
        self.输入宽度 = int(宽度值) if isinstance(宽度值, (int, float)) else 640
    
    def 截取屏幕(self, x, y, 宽度, 高度):
        """截取屏幕指定区域"""
        bmp = win32ui.CreateBitmap()
        bmp.CreateCompatibleBitmap(self.srcdc, 宽度, 高度)
        self.memdc.SelectObject(bmp)
        
        self.memdc.BitBlt((0, 0), (宽度, 高度), self.srcdc, (x, y), win32con.SRCCOPY)
        signed_ints_array = bmp.GetBitmapBits(True)
        img = np.frombuffer(signed_ints_array, dtype='uint8')
        img.shape = (高度, 宽度, 4)
        frame = cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)
        
        win32gui.DeleteObject(bmp.GetHandle())
        return frame
    
    def 预处理图像(self, 图像):
        """图像标准化变换"""
        img = cv2.resize(图像, (self.输入宽度, self.输入高度), interpolation=cv2.INTER_LINEAR)
        img = img.astype(np.float32) / 255.0
        img = img.transpose(2, 0, 1)
        return np.expand_dims(img, axis=0)
    
    def 后处理结果(self, 输出, 图像宽度, 图像高度, 置信度阈值=0.5, IOU阈值=0.45, 偏移X=0, 偏移Y=0):
        """矩阵化后处理与敌我逻辑转换"""
        if isinstance(输出, (tuple, list)):
            predictions = 输出[0]
        else:
            predictions = 输出
            
        if hasattr(predictions, 'ndim') and predictions.ndim == 3:
            predictions = predictions[0]
            
        obj = predictions[:, 4]
        scores = predictions[:, 5:]
        
        if obj.max() > 1 or obj.min() < 0:
            obj = 1 / (1 + np.exp(-np.clip(obj, -88, 88)))
            
        if scores.max() > 1 or scores.min() < 0:
            scores = 1 / (1 + np.exp(-np.clip(scores, -88, 88)))
            
        class_ids = np.argmax(scores, axis=1)
        class_scores = np.max(scores, axis=1)
        confidences = obj * class_scores
        
        mask = confidences > 置信度阈值
        if not np.any(mask):
            return []
            
        filtered_preds = predictions[mask]
        filtered_confs = confidences[mask]
        filtered_ids = class_ids[mask]
        
        cx = filtered_preds[:, 0] / self.输入宽度 * 图像宽度
        cy = filtered_preds[:, 1] / self.输入高度 * 图像高度
        w = filtered_preds[:, 2] / self.输入宽度 * 图像宽度
        h = filtered_preds[:, 3] / self.输入高度 * 图像高度
        
        x1 = (cx - w / 2).astype(int)
        y1 = (cy - h / 2).astype(int)
        w_int = w.astype(int)
        h_int = h.astype(int)
        
        nms_boxes = np.stack([x1, y1, w_int, h_int], axis=1).tolist()
        nms_scores = filtered_confs.astype(float).tolist()
        
        indices = cv2.dnn.NMSBoxes(nms_boxes, nms_scores, 置信度阈值, IOU阈值)
        
        检测结果 = []
        if len(indices) > 0:
            actual_indices = indices.flatten() if isinstance(indices, np.ndarray) else indices
            敌方类别 = self.匪类别ID if self.自己阵营 == "警" else self.警类别ID
            
            for i in actual_indices:
                idx = int(i)
                cid = int(filtered_ids[idx])
                
                部位文本 = self.部位映射.get(cid, "胸部")
                is_head = (部位文本 == "头部")
                is_enemy = cid in 敌方类别
                
                role = "enemy" if is_enemy else "team"
                part = "head" if is_head else "body"
                显示名称 = f"{role}_{part}"
                
                角色文本 = "敌人" if is_enemy else "队友"
                中文标签 = f"{角色文本}{部位文本}"
                
                rx1 = int(x1[idx])
                ry1 = int(y1[idx])
                rw = int(w_int[idx])
                rh = int(h_int[idx])
                
                原始名称 = self.类别列表[cid] if 0 <= cid < len(self.类别列表) else f"id_{cid}"
                
                检测结果.append({
                    'class_id': cid,
                    '原始名称': 原始名称,
                    '显示名称': 显示名称,
                    '中文标签': 中文标签,
                    'is_enemy': is_enemy,
                    'x1': rx1,
                    'y1': ry1,
                    'x2': rx1 + rw,
                    'y2': ry1 + rh,
                    '宽度': rw,
                    '高度': rh,
                    '中心X': rx1 + rw // 2,
                    '中心Y': ry1 + rh // 2,
                    'abs_center_x': rx1 + rw // 2 + 偏移X,
                    'abs_center_y': ry1 + rh // 2 + 偏移Y,
                    '置信度': float(nms_scores[idx])
                })
        return 检测结果
    
    def 执行检测(self, 左上X=None, 左上Y=None, 右下X=None, 右下Y=None, 置信度阈值=None, IOU阈值=None, 显示画面=None):
        """单次捕获检测视窗"""
        try:
            模板 = self.配置模板[self.当前模板索引]
            conf = 置信度阈值 if 置信度阈值 is not None else 模板["置信度"]
            iou = IOU阈值 if IOU阈值 is not None else 模板["IOU"]
            show = 显示画面 if 显示画面 is not None else 模板["渲染"]

            val_x1 = max(0, int(左上X) if 左上X is not None else 0)
            val_y1 = max(0, int(左上Y) if 左上Y is not None else 0)
            val_x2 = min(self.屏幕宽度, int(右下X) if 右下X is not None else self.屏幕宽度)
            val_y2 = min(self.屏幕高度, int(右下Y) if 右下Y is not None else self.屏幕高度)
            
            if val_x1 >= val_x2 or val_y1 >= val_y2:
                return []
            
            roi_w = val_x2 - val_x1
            roi_h = val_y2 - val_y1
            
            src_frame = self.截取屏幕(val_x1, val_y1, roi_w, roi_h)
            tensor = self.预处理图像(src_frame)
            
            bindings = {self.session.get_inputs()[0].name: tensor}
            raw_outputs = self.session.run(None, bindings)
            
            parsed_data = self.后处理结果(
                raw_outputs[0], src_frame.shape[1], src_frame.shape[0], 
                conf, iou, 偏移X=val_x1, 偏移Y=val_y1
            )
            
            if show:
                self._渲染画面(src_frame, parsed_data)
            
            return parsed_data
            
        except Exception as e:
            print(f"执行检测失败: {e}")
            traceback.print_exc()
            return None 
    
    def _渲染画面(self, frame, results):
        """多色可视化渲染窗口"""
        canvas = frame.copy()
        canvas = cv2.cvtColor(canvas, cv2.COLOR_RGB2BGR)
        
        for item in results:
            bx1, by1, bx2, by2 = item['x1'], item['y1'], item['x2'], item['y2']
            txt = item['显示名称']
            score = item['置信度']
            
            color = self.颜色字典.get(txt, (0, 255, 0))
            
            cv2.rectangle(canvas, (bx1, by1), (bx2, by2), color, 2)
            display_str = f"{txt}: {score:.2%}"
            (tw, th), _ = cv2.getTextSize(display_str, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(canvas, (bx1, by1 - th - 5), (bx1 + tw, by1), color, -1)
            cv2.putText(canvas, display_str, (bx1, by1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
        
        if not self._窗口已创建:
            cv2.namedWindow('YOLOv8_Generic_Detector', cv2.WINDOW_NORMAL)
            cv2.resizeWindow('YOLOv8_Generic_Detector', canvas.shape[1], canvas.shape[0])
            self._窗口已创建 = True
        
        cv2.imshow('YOLOv8_Generic_Detector', canvas)
        cv2.waitKey(1)
    
    def 释放资源(self):
        """带安全校验的资源释放"""
        try:
            if self._窗口已创建:
                cv2.destroyAllWindows()
            if self.srcdc is not None:
                self.srcdc.DeleteDC()
                self.srcdc = None
            if self.memdc is not None:
                self.memdc.DeleteDC()
                self.memdc = None
            if self.hwin is not None and self.hwindc is not None:
                win32gui.ReleaseDC(self.hwin, self.hwindc)
                self.hwin = None
                self.hwindc = None
            print("系统资源安全卸载完毕")
        except Exception as e:
            print(f"释放资源时产生次生异常: {e}")

# 别名注册以兼容主程序调用
YOLOv8检测器 = YOLOv8初始化

if __name__ == "__main__":
    检测器 = YOLOv8初始化(模型路径="cs2警0胸1头匪2胸3头.onnx", 自身阵营="匪")
    检测器.切换参数模板(1) # 默认启动调试参数与画框渲染
    
    检测半径 = 320
    
    try:
        print(f"\n开启独立测试轮询 当前自身阵营: {检测器.自己阵营}")
        while True:
            mid_x = 检测器.屏幕宽度 // 2
            mid_y = 检测器.屏幕高度 // 2
            
            data_list = 检测器.执行检测(
                左上X=mid_x - 检测半径, 左上Y=mid_y - 检测半径, 
                右下X=mid_x + 检测半径, 右下Y=mid_y + 检测半径
            )

            if data_list is None:
                print("检测模块异常")
                time.sleep(1)
                continue

            敌人列表 = [t for t in (data_list or []) if t.get("is_enemy") is True]

            if 敌人列表:
                print(f"检测到敌人目标数: {len(敌人列表)}")
                for entry in 敌人列表:
                    print(f"  判定: {entry['中文标签']} | 置信度: {entry['置信度']:.2%} | 全屏绝对中心: ({entry['abs_center_x']}, {entry['abs_center_y']})")
            
            time.sleep(0.01)
            
    except KeyboardInterrupt:
        print("\n主动中止检测")
    except Exception as top_error:
        print(f"主进程崩溃: {top_error}")
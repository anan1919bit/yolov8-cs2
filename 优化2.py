import win32api
import time
import math
import tkinter as tk
import multiprocessing
import sys
import os
import json

# 工业级诊断隔离配置开关
DISABLE_MOUSE_OUTPUT = False   

# 状态机常量定义
ST_SEARCH = 0
ST_CONFIRM = 1
ST_LOCKED = 2
ST_LOSS = 3

# 统一视野与锁定参数
CROP_RADIUS = 320          
CENTER_OFFSET = float(CROP_RADIUS)
LOSE_RADIUS = 120.0        

# =====================================================================
# 弹道数据契约矩阵
# =====================================================================
RECOIL_DATABASE = {
    1: [ # AK47
        {"x":0, "y":0, "d":2}, {"x":0, "y":0, "d":2}, {"x":0, "y":0, "d":2}, {"x":0, "y":0, "d":2}, {"x":0, "y":0, "d":2}, {"x":0, "y":0, "d":2}, {"x":0, "y":0, "d":2}, {"x":0, "y":0, "d":3}, {"x":0, "y":0, "d":3}, {"x":0, "y":0, "d":3}, {"x":0, "y":0, "d":3}, {"x":0, "y":0, "d":3}, {"x":0, "y":0, "d":8}, {"x":0, "y":0, "d":8}, {"x":0, "y":0, "d":8}, {"x":0, "y":0, "d":8}, {"x":0, "y":0, "d":8}, {"x":0, "y":0, "d":8}, {"x":0, "y":0, "d":8}, {"x":0, "y":0, "d":8}, {"x":0, "y":0, "d":8}, {"x":0, "y":0, "d":9}, {"x":0, "y":0, "d":9}, {"x":0, "y":0, "d":9}, 
        {"x":0, "y":8, "d":8}, {"x":0, "y":8, "d":8}, {"x":0, "y":7, "d":8}, {"x":0, "y":7, "d":8}, {"x":0, "y":7, "d":8}, {"x":0, "y":7, "d":8}, {"x":0, "y":7, "d":8}, {"x":0, "y":7, "d":8}, {"x":0, "y":7, "d":8}, {"x":0, "y":7, "d":8}, {"x":0, "y":7, "d":9}, {"x":0, "y":7, "d":9}, {"x":-1, "y":7, "d":8}, {"x":-1, "y":6, "d":8}, {"x":-1, "y":6, "d":8}, {"x":-1, "y":7, "d":8}, {"x":-1, "y":7, "d":8}, {"x":0, "y":7, "d":8}, {"x":0, "y":7, "d":8}, {"x":0, "y":7, "d":8}, {"x":0, "y":7, "d":8}, {"x":0, "y":7, "d":9}, {"x":0, "y":7, "d":9}, {"x":0, "y":7, "d":9},
        {"x":-1, "y":5, "d":8}, {"x":-1, "y":5, "d":8}, {"x":-1, "y":6, "d":8}, {"x":0, "y":6, "d":8}, {"x":0, "y":6, "d":8}, {"x":0, "y":6, "d":8}, {"x":0, "y":6, "d":8}, {"x":0, "y":6, "d":8}, {"x":0, "y":6, "d":8}, {"x":0, "y":6, "d":8}, {"x":0, "y":6, "d":9}, {"x":0, "y":6, "d":9}, {"x":4, "y":5, "d":8}, {"x":4, "y":5, "d":8}, {"x":4, "y":6, "d":8}, {"x":4, "y":6, "d":8}, {"x":3, "y":6, "d":8}, {"x":3, "y":6, "d":8}, {"x":3, "y":6, "d":8}, {"x":3, "y":6, "d":8}, {"x":3, "y":6, "d":8}, {"x":3, "y":6, "d":8}, {"x":3, "y":6, "d":9}, {"x":3, "y":6, "d":9}
    ],
    2: [ # 加利尔
        {"x":0,"y":0,"d":2}, {"x":0,"y":0,"d":2}, {"x":0,"y":0,"d":2}, {"x":0,"y":0,"d":2}, {"x":0,"y":0,"d":2}, {"x":0,"y":0,"d":2}, {"x":0,"y":0,"d":2}, {"x":0,"y":0,"d":2}, {"x":0,"y":0,"d":2}, {"x":0,"y":0,"d":2}, {"x":0,"y":0,"d":2}, {"x":0,"y":0,"d":2}, {"x":0,"y":0,"d":2}, {"x":0,"y":0,"d":2}, {"x":0,"y":0,"d":2}, {"x":0,"y":0,"d":3}, {"x":0,"y":0,"d":5}, {"x":0,"y":0,"d":5}, {"x":0,"y":0,"d":5}, {"x":0,"y":0,"d":5}, {"x":0,"y":0,"d":5}, {"x":0,"y":0,"d":5}, {"x":0,"y":0,"d":6}, {"x":0,"y":0,"d":6}, {"x":0,"y":0,"d":6}, {"x":0,"y":0,"d":6}, {"x":0,"y":0,"d":6}, {"x":0,"y":0,"d":6}, {"x":0,"y":0,"d":6}, {"x":0,"y":0,"d":6}, {"x":0,"y":0,"d":6}, {"x":2,"y":2,"d":6}, {"x":0,"y":2,"d":5}, {"x":0,"y":2,"d":5}, {"x":0,"y":2,"d":5}, {"x":0,"y":2,"d":5}, {"x":0,"y":2,"d":5}, {"x":0,"y":1,"d":5}, {"x":0,"y":1,"d":5}, {"x":0,"y":1,"d":6}, {"x":0,"y":1,"d":6}, {"x":0,"y":1,"d":6}, {"x":0,"y":1,"d":6}, {"x":2,"y":1,"d":6}, {"x":1,"y":1,"d":6}, {"x":1,"y":1,"d":6}, {"x":1,"y":1,"d":6}, {"x":1,"y":1,"d":6}
    ],
    3: [ # SG553
        {"x":0,"y":0,"d":2}, {"x":0,"y":0,"d":2}, {"x":0,"y":0,"d":2}, {"x":0,"y":0,"d":2}, {"x":0,"y":0,"d":2}, {"x":0,"y":0,"d":2}, {"x":0,"y":0,"d":2}, {"x":0,"y":0,"d":2}, {"x":0,"y":0,"d":2}, {"x":0,"y":0,"d":2}, {"x":0,"y":0,"d":2}, {"x":0,"y":0,"d":2}, {"x":0,"y":0,"d":9}, {"x":0,"y":0,"d":9}, {"x":0,"y":0,"d":9}, {"x":0,"y":0,"d":9}, {"x":0,"y":0,"d":9}, {"x":0,"y":0,"d":9}, {"x":0,"y":0,"d":9}, {"x":0,"y":0,"d":9}, {"x":0,"y":0,"d":9}, {"x":0,"y":0,"d":9}, {"x":0,"y":0,"d":10}, {"x":0,"y":0,"d":10}, {"x":-3,"y":4,"d":9}, {"x":-3,"y":4,"d":9}, {"x":-3,"y":4,"d":9}, {"x":-3,"y":4,"d":9}, {"x":-3,"y":4,"d":9}, {"x":-3,"y":4,"d":9}, {"x":-3,"y":4,"d":9}, {"x":-3,"y":4,"d":9}, {"x":-2,"y":3,"d":9}, {"x":-2,"y":3,"d":10}, {"x":-2,"y":3,"d":10}, {"x":-2,"y":3,"d":10}
    ],
    4: [ # M4A4
        {"x":0,"y":0,"d":1}, {"x":0,"y":0,"d":1}, {"x":0,"y":0,"d":2}, {"x":0,"y":0,"d":2}, {"x":0,"y":0,"d":2}, {"x":0,"y":0,"d":2}, {"x":0,"y":0,"d":2}, {"x":0,"y":0,"d":2}, {"x":0,"y":0,"d":2}, {"x":0,"y":0,"d":2}, {"x":0,"y":0,"d":2}, {"x":0,"y":0,"d":2}, {"x":0,"y":0,"d":7}, {"x":0,"y":0,"d":7}, {"x":0,"y":0,"d":7}, {"x":0,"y":0,"d":7}, {"x":0,"y":0,"d":7}, {"x":0,"y":0,"d":7}, {"x":0,"y":0,"d":8}, {"x":0,"y":0,"d":8}, {"x":0,"y":0,"d":8}, {"x":0,"y":0,"d":8}, {"x":0,"y":0,"d":8}, {"x":0,"y":2,"d":8}, 
        {"x":0, "y":7, "d":7}, {"x":0, "y":7, "d":7}, {"x":0, "y":6, "d":7}, {"x":0, "y":6, "d":7}, {"x":0, "y":3, "d":7}, {"x":0, "y":3, "d":7}, {"x":0, "y":3, "d":8}, {"x":0, "y":3, "d":8}, {"x":0, "y":3, "d":8}, {"x":1, "y":3, "d":8}, {"x":1, "y":3, "d":8}, {"x":1, "y":3, "d":8}
    ],
    5: [ # M4A1
        {"x":0,"y":0,"d":5}, {"x":0,"y":0,"d":5}, {"x":0,"y":0,"d":5}, {"x":0,"y":0,"d":5}, {"x":0,"y":0,"d":5}, {"x":0,"y":0,"d":5}, {"x":0,"y":0,"d":5}, {"x":0,"y":0,"d":5}, {"x":0,"y":0,"d":5}, {"x":0,"y":0,"d":5}, {"x":0,"y":0,"d":6}, {"x":0,"y":0,"d":6}, {"x":0,"y":0,"d":8}, {"x":0,"y":0,"d":8}, {"x":0,"y":0,"d":8}, {"x":0,"y":0,"d":8}, {"x":0,"y":0,"d":8}, {"x":0,"y":0,"d":8}, {"x":0,"y":0,"d":8}, {"x":0,"y":0,"d":8}, {"x":0,"y":0,"d":8}, {"x":0,"y":0,"d":8}, {"x":0,"y":0,"d":9}, {"x":0,"y":0,"d":9}, {"x":0,"y":2, "d":8}, {"x":0,"y":2, "d":8}, {"x":0,"y":2, "d":8}, {"x":0,"y":2, "d":8}, {"x":0,"y":2, "d":8}, {"x":0,"y":2, "d":8}, {"x":0,"y":2, "d":8}, {"x":0,"y":2, "d":8}, {"x":0,"y":2, "d":8}, {"x":0,"y":2, "d":8}, {"x":1,"y":1,"d":8}, {"x":1,"y":1,"d":9}
    ],
    6: [ # AUG
        {"x":0,"y":0,"d":2}, {"x":0,"y":0,"d":2}, {"x":0,"y":0,"d":3}, {"x":0,"y":0,"d":3}, {"x":0,"y":0,"d":3}, {"x":0,"y":0,"d":3}, {"x":0,"y":0,"d":3}, {"x":0,"y":0,"d":3}, {"x":0,"y":0,"d":3}, {"x":0,"y":0,"d":3}, {"x":0,"y":0,"d":3}, {"x":0,"y":0,"d":3}, {"x":0,"y":0,"d":8}, {"x":0,"y":0,"d":8}, {"x":0,"y":0,"d":8}, {"x":0,"y":0,"d":8}, {"x":0,"y":0, "d":8}, {"x":0,"y":0,"d":8}, {"x":0,"y":0,"d":8}, {"x":0,"y":0,"d":8}, {"x":0,"y":0,"d":8}, {"x":0,"y":0,"d":9}, {"x":0,"y":0,"d":9}, {"x":0,"y":0,"d":9}, {"x":0,"y":3,"d":8}, {"x":0,"y":3,"d":8}, {"x":0,"y":3,"d":8}, {"x":0,"y":3,"d":8}, {"x":0,"y":3,"d":8}, {"x":1,"y":3,"d":8}, {"x":1,"y":2,"d":8}, {"x":1,"y":2,"d":8}
    ]
}

WEAPON_NAME_MAP = {0: "未选择 (宏已关闭)", 1: "AK47 压枪", 2: "加利尔 压枪", 3: "SG553 压枪", 4: "M4A4 压枪", 5: "M4A1 压枪", 6: "AUG 压枪"}

# =====================================================================
# 1. 数据契约层：状态一包化原子缓冲区
# =====================================================================
class AtomicTargetState:
    def __init__(self):
        self.data_array = multiprocessing.Array('d', [ -1.0, CENTER_OFFSET, CENTER_OFFSET, CENTER_OFFSET, CENTER_OFFSET, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0 ])
        self.lock = multiprocessing.Lock()

    def update(self, target_id, rx, ry, fx, fy, vx, vy, timestamp, loss, state, suspicious=0.0):
        with self.lock:
            self.data_array[0] = float(target_id)
            self.data_array[1] = float(rx)
            self.data_array[2] = float(ry)
            self.data_array[3] = float(fx)
            self.data_array[4] = float(fy)
            self.data_array[5] = float(vx)
            self.data_array[6] = float(vy)
            self.data_array[7] = float(timestamp)
            self.data_array[8] = float(loss)
            self.data_array[9] = float(state)
            self.data_array[10] = float(suspicious)

    def fetch(self):
        with self.lock:
            return {
                "target_id": int(self.data_array[0]),
                "raw_x": self.data_array[1],
                "raw_y": self.data_array[2],
                "filt_x": self.data_array[3],
                "filt_y": self.data_array[4],
                "vel_x": self.data_array[5],
                "vel_y": self.data_array[6],
                "timestamp": self.data_array[7],
                "loss": int(self.data_array[8]),
                "state": int(self.data_array[9]),
                "suspicious": int(self.data_array[10])
            }

    def reset(self):
        with self.lock:
            self.data_array[0] = -1.0
            self.data_array[7] = 0.0
            self.data_array[8] = -1.0
            self.data_array[9] = float(ST_SEARCH)
            self.data_array[10] = 0.0

# =====================================================================
# 2. 视觉观测层：深度预判与死锁闸门
# =====================================================================
def vision_observation_process(state_buffer, shared_active, shared_conf, shared_switch_thru, shared_aim_part, shared_team_is_t, shared_deathmatch):
    from yolov8检测模块2 import YOLOv8初始化
    import math
    import time

    yolo = YOLOv8初始化(模型路径="cs2警0胸1头匪2胸3头.onnx", 自身阵营="匪")
    SCREEN_CENTER_X = yolo.屏幕宽度 // 2
    SCREEN_CENTER_Y = yolo.屏幕高度 // 2
    
    current_state = ST_SEARCH
    virtual_locked_id = 1000
    confirm_counter = 0
    lost_frame_counter = 0
    suspicious_counter = 0
    
    filter_x, filter_y = CENTER_OFFSET, CENTER_OFFSET
    filter_h = 100.0
    v_filter_x, v_filter_y = 0.0, 0.0
    last_filt_x, last_filt_y = CENTER_OFFSET, CENTER_OFFSET
    filter_initialized = False

    last_raw_x, last_raw_y, last_raw_h = CENTER_OFFSET, CENTER_OFFSET, 100.0
    target_vel_x, target_vel_y = 0.0, 0.0

    def reset_filter_state(init_x, init_y, init_h):
        nonlocal filter_x, filter_y, filter_h, v_filter_x, v_filter_y, last_filt_x, last_filt_y, filter_initialized
        nonlocal target_vel_x, target_vel_y
        filter_x, filter_y, filter_h = init_x, init_y, init_h
        v_filter_x, v_filter_y = 0.0, 0.0
        last_filt_x, last_filt_y = init_x, init_y
        target_vel_x, target_vel_y = 0.0, 0.0
        filter_initialized = True

    while True:
        yolo.自己阵营 = "匪" if shared_team_is_t.value else "警"

        if not shared_active.value:
            time.sleep(0.01)
            current_state = ST_SEARCH
            filter_initialized = False
            suspicious_counter = 0
            state_buffer.reset()
            continue

        raw_detections = yolo.执行检测(
            左上X=SCREEN_CENTER_X - CROP_RADIUS, 左上Y=SCREEN_CENTER_Y - CROP_RADIUS, 
            右下X=SCREEN_CENTER_X + CROP_RADIUS, 右下Y=SCREEN_CENTER_Y + CROP_RADIUS, 
            置信度阈值=shared_conf.value, 
            显示画面=True
        )
        
        frame_time = time.perf_counter()
        
        if raw_detections is None:
            time.sleep(0.01)
            continue
            
        detections = []
        if shared_deathmatch.value:
            for t in raw_detections:
                if not any(math.hypot(t["中心X"] - d["中心X"], t["中心Y"] - d["中心Y"]) < 50.0 for d in detections):
                    detections.append(t)
        else:
            队友列表 = [t for t in raw_detections if not t.get("is_enemy")]
            原始敌人列表 = [t for t in raw_detections if t.get("is_enemy") is True]

            for 敌 in 原始敌人列表:
                被双框污染 = False
                for 友 in 队友列表:
                    距离 = math.hypot(敌["中心X"] - 友["中心X"], 敌["中心Y"] - 友["中心Y"])
                    if 距离 < 80.0:
                        被双框污染 = True
                        break
                if not 被双框污染:
                    detections.append(敌)
        
        active_target = None
        aim_height_ratio = shared_aim_part.value

        best_candidate = None
        if detections:
            best_candidate = min(
                detections,
                key=lambda t: math.hypot(t["中心X"] - CROP_RADIUS, (t["y1"] + t["高度"] * aim_height_ratio) - CROP_RADIUS)
            )

        match_target = None
        if detections and filter_initialized:
            if current_state in [ST_CONFIRM, ST_LOCKED]:
                gated_candidates = []
                
                # 预测位置：基于上一帧加上速度惯性
                predicted_x = last_raw_x + target_vel_x
                predicted_y = last_raw_y + target_vel_y

                for t in detections:
                    t_y = t["y1"] + t["高度"] * aim_height_ratio
                    dist_to_predicted = math.hypot(t["中心X"] - predicted_x, t_y - predicted_y)
                    height_diff = abs(t["高度"] - last_raw_h) / max(last_raw_h, 1.0)
                    
                    # 【核心优化 1】极其严苛的排他性闸门：锁定后只看半径40像素内的目标，绝对屏蔽周围干扰
                    if dist_to_predicted < 40.0 and height_diff < 0.40:
                        gated_candidates.append((dist_to_predicted, t))
                if gated_candidates:
                    match_target = min(gated_candidates, key=lambda x: x[0])[1]

            if match_target is None:
                valid_candidates = []
                for t in detections:
                    t_y = t["y1"] + t["高度"] * aim_height_ratio
                    dist = math.hypot(t["中心X"] - filter_x, t_y - filter_y)
                    height_ratio = abs(t["高度"] - filter_h) / max(filter_h, 1.0)
                    if dist < LOSE_RADIUS and height_ratio < 0.35:
                        valid_candidates.append((dist, t))
                if valid_candidates:
                    match_target = min(valid_candidates, key=lambda x: x[0])[1]

        if current_state == ST_SEARCH:
            if best_candidate:
                virtual_locked_id += 1  
                active_target = best_candidate
                t_y = best_candidate["y1"] + best_candidate["高度"] * aim_height_ratio
                reset_filter_state(best_candidate["中心X"], t_y, best_candidate["高度"])
                last_raw_x = float(best_candidate["中心X"])
                last_raw_y = float(t_y)
                last_raw_h = float(best_candidate["高度"])
                confirm_counter, lost_frame_counter, suspicious_counter = 1, 0, 0
                current_state = ST_CONFIRM
                
        elif current_state == ST_CONFIRM:
            if match_target:
                active_target = match_target
                confirm_counter += 1
                if confirm_counter >= 3:
                    current_state = ST_LOCKED
            else:
                current_state = ST_SEARCH
                filter_initialized = False

        elif current_state == ST_LOCKED:
            if match_target:
                active_target = match_target
            else:
                current_state = ST_LOSS
                lost_frame_counter = 1

        elif current_state == ST_LOSS:
            if match_target:
                active_target = match_target
                current_state = ST_LOCKED
                lost_frame_counter = 0
            else:
                lost_frame_counter += 1
                # 【核心优化 2】高容忍度死等：消失 15 帧（约 0.5秒）内绝不换人，保证目标闪身时的绝对黏性
                if lost_frame_counter > 15:
                    current_state = ST_SEARCH
                    filter_initialized = False
                    state_buffer.reset()
                    continue

        if (current_state == ST_LOCKED or current_state == ST_CONFIRM) and active_target:
            raw_x = float(active_target["中心X"])
            raw_y = float(active_target["y1"] + active_target["高度"] * aim_height_ratio)
            raw_h = float(active_target["高度"])

            jump_too_large = filter_initialized and (math.hypot(raw_x - filter_x, raw_y - filter_y) > LOSE_RADIUS or abs(raw_h - filter_h) / max(filter_h, 1.0) > 0.40)
            is_suspicious_logged = 0.0
            
            if jump_too_large:
                suspicious_counter += 1
                if suspicious_counter < 3:
                    is_suspicious_logged = 1.0
                else:
                    reset_filter_state(raw_x, raw_y, raw_h)
                    suspicious_counter = 0
            else:
                suspicious_counter = 0
                # 【核心优化 3】极重度 EMA 滤波：极大压制 YOLO 边框自然跳动，只引入 20% 的新观测值
                filter_x = filter_x * 0.80 + raw_x * 0.20
                filter_y = filter_y * 0.85 + raw_y * 0.15
                filter_h = filter_h * 0.90 + raw_h * 0.10

            target_vel_x = target_vel_x * 0.8 + (raw_x - last_raw_x) * 0.2
            target_vel_y = target_vel_y * 0.8 + (raw_y - last_raw_y) * 0.2

            last_raw_x = raw_x
            last_raw_y = raw_y
            last_raw_h = raw_h

            instant_vx = filter_x - last_filt_x
            instant_vy = filter_y - last_filt_y
            v_filter_x = v_filter_x * 0.8 + instant_vx * 0.2
            v_filter_y = v_filter_y * 0.8 + instant_vy * 0.2
            last_filt_x, last_filt_y = filter_x, filter_y

            state_buffer.update(
                target_id=virtual_locked_id, rx=raw_x, ry=raw_y, fx=filter_x, fy=filter_y,
                vx=v_filter_x, vy=v_filter_y, timestamp=frame_time, loss=lost_frame_counter, state=current_state, suspicious=is_suspicious_logged
            )
        elif current_state == ST_LOSS:
            filter_x += v_filter_x
            filter_y += v_filter_y
            v_filter_x *= 0.85
            v_filter_y *= 0.85
            
            last_raw_x = filter_x
            last_raw_y = filter_y
            target_vel_x *= 0.5
            target_vel_y *= 0.5

            state_buffer.update(
                target_id=virtual_locked_id, rx=CENTER_OFFSET, ry=CENTER_OFFSET, fx=filter_x, fy=filter_y,
                vx=v_filter_x, vy=v_filter_y, timestamp=frame_time, loss=lost_frame_counter, state=current_state, suspicious=0.0
            )

# =====================================================================
# 3. 物理控制层：纯净非线性动态 PID 伺服中心
# =====================================================================
def control_driving_process(state_buffer, shared_active, shared_smooth_x, shared_smooth_y, shared_deadzone, shared_max_disp, shared_kp, shared_kd, shared_weapon_id):
    from 罗技旧版调用 import 罗技驱动键鼠初始化
    from PID自瞄算法模块 import PID初始化
    import win32api
    import math
    import time

    pid_x = PID初始化(0.007, 0.22, 0.0, 0.015)
    pid_y = PID初始化(0.007, 0.22, 0.0, 0.015)
    mouse = 罗技驱动键鼠初始化()

    渲染比例, 摄像机视角 = 1.20, 90.0
    residual_x, residual_y = 0.0, 0.0
    
    last_processed_timestamp = 0.0
    last_target_id = -1
    last_state = ST_SEARCH
    
    last_output_x = 0.0
    last_output_y = 0.0
    # 【核心优化 4】锁死物理最高瞬移速度，从根源掐断甩枪闪烁
    MAX_SLEW_RATE = 18.0  

    last_click_timestamps = {0x04: 0.0, 0x06: 0.0}
    
    recoil_index = 0
    last_recoil_step_time = 0.0
    recoil_active = False

    def 计算投影矩阵位移(偏差X, 偏差Y, 屏幕宽, 屏幕高, 渲染比例, 摄像机视角):
        M_YAW, M_PITCH = 0.022, 0.022
        FOV_弧度 = math.radians(摄像机视角)
        真实角度_X = math.degrees(math.atan((偏差X / (屏幕宽 / 2)) * math.tan(FOV_弧度 / 2)))
        真实角度_Y = math.degrees(math.atan((偏差Y / (屏幕高 / 2)) * math.tan(FOV_弧度 / 2)))
        return 真实角度_X / (渲染比例 * M_YAW), 真实角度_Y / (渲染比例 * M_PITCH)

    print("高频硬件级联控制环路已就位")

    while True:
        now_time = time.perf_counter()

        if win32api.GetAsyncKeyState(0x77) & 1:
            shared_active.value = not shared_active.value
            time.sleep(0.2)

        ctrl_pressed = bool(win32api.GetAsyncKeyState(0x11) & 0x8000)

        if win32api.GetAsyncKeyState(0x76) & 1:
            shared_weapon_id.value = 0
            print("武器压枪宏状态: [已关闭]")

        if win32api.GetAsyncKeyState(0x04) & 1:
            if ctrl_pressed:
                shared_weapon_id.value = 3  
            else:
                if now_time - last_click_timestamps[0x04] < 0.40:
                    shared_weapon_id.value = 2  
                else:
                    shared_weapon_id.value = 1  
            last_click_timestamps[0x04] = now_time
            print(f"武器状态变更: {WEAPON_NAME_MAP[shared_weapon_id.value]}")

        if win32api.GetAsyncKeyState(0x06) & 1:
            if ctrl_pressed:
                shared_weapon_id.value = 6  
            else:
                if now_time - last_click_timestamps[0x06] < 0.40:
                    shared_weapon_id.value = 5  
                else:
                    shared_weapon_id.value = 4  
            last_click_timestamps[0x06] = now_time
            print(f"武器状态变更: {WEAPON_NAME_MAP[shared_weapon_id.value]}")

        if not shared_active.value:
            time.sleep(0.01)
            residual_x = residual_y = last_output_x = last_output_y = 0.0
            last_processed_timestamp = 0.0
            recoil_active = False
            continue

        left_clicked = bool(win32api.GetAsyncKeyState(0x01) & 0x8000)
        recoil_dx = 0
        recoil_dy = 0

        if left_clicked and shared_weapon_id.value in RECOIL_DATABASE:
            if not recoil_active:
                recoil_active = True
                recoil_index = 0
                last_recoil_step_time = time.perf_counter()
            
            pattern = RECOIL_DATABASE[shared_weapon_id.value]
            if recoil_index < len(pattern):
                step = pattern[recoil_index]
                if time.perf_counter() - last_recoil_step_time >= (step["d"] / 1000.0):
                    recoil_dx = step["x"]
                    recoil_dy = step["y"]
                    recoil_index += 1
                    last_recoil_step_time = time.perf_counter()
        else:
            recoil_active = False
            recoil_index = 0

        state = state_buffer.fetch()

        id_changed = (state["target_id"] != last_target_id)
        state_changed = (state["state"] != last_state)
        is_danger_transition = state_changed and ((last_state, state["state"]) in [(ST_LOSS, ST_LOCKED), (ST_LOCKED, ST_CONFIRM), (ST_SEARCH, ST_CONFIRM)])

        if id_changed or is_danger_transition or (not left_clicked):
            pid_x.上次偏差 = pid_y.上次偏差 = 0
            residual_x = residual_y = 0.0
            if not left_clicked:
                last_output_x *= 0.5
                last_output_y *= 0.5
            else:
                last_output_x = last_output_y = 0.0
            last_target_id = state["target_id"]

        if state["target_id"] != -1 and state["timestamp"] > last_processed_timestamp:
            last_processed_timestamp = state["timestamp"]

            error_x = state["filt_x"] - CENTER_OFFSET
            error_y = state["filt_y"] - CENTER_OFFSET
            dist = math.hypot(error_x, error_y)
            
            hardware_x, hardware_y = 计算投影矩阵位移(error_x, error_y, CROP_RADIUS*2, CROP_RADIUS*2, 渲染比例, 摄像机视角)
            
            base_kp = shared_kp.value
            base_kd = shared_kd.value
            
            # 【核心优化 5】非线性动态微调降速刹车：大范围快拉，小范围碎步死锁
            if dist < 25.0:
                dynamic_kp = base_kp * 0.2  # 切断 80% 的过激拉力
                dynamic_kd = base_kd * 3.0  # 提供 3 倍的物理粘性刹车
            else:
                dynamic_kp = base_kp
                dynamic_kd = base_kd
                
            pid_x.Kp = pid_y.Kp = dynamic_kp
            pid_x.Kd = pid_y.Kd = dynamic_kd
            
            control_x = pid_x.PID算法_Position_X(hardware_x, 0)
            control_y = pid_y.PID算法_Position_Y(hardware_y, 0)
            
            damping_radius = 40.0
            proximity_factor = max(0.5, min(1.0, dist / damping_radius))

            if left_clicked and state["state"] == ST_LOCKED:
                if dist <= shared_deadzone.value:
                    last_output_x = last_output_y = 0.0
                    continue

                max_limit = shared_max_disp.value

                raw_output_x = max(min(control_x * shared_smooth_x.value * proximity_factor, max_limit), -max_limit)
                raw_output_y = max(min(control_y * shared_smooth_y.value * proximity_factor, max_limit), -max_limit)

                delta_x = raw_output_x - last_output_x
                delta_y = raw_output_y - last_output_y
                filtered_output_x = last_output_x + max(min(delta_x, MAX_SLEW_RATE), -MAX_SLEW_RATE)
                filtered_output_y = last_output_y + max(min(delta_y, MAX_SLEW_RATE), -MAX_SLEW_RATE)

                last_output_x, last_output_y = filtered_output_x, filtered_output_y
            else:
                last_output_x *= 0.8
                last_output_y *= 0.8
                filtered_output_x = 0.0
                filtered_output_y = 0.0

            total_x = filtered_output_x + residual_x + recoil_dx
            total_y = filtered_output_y + residual_y + recoil_dy
            output_x, output_y = int(total_x), int(total_y)
            residual_x = total_x - output_x
            residual_y = total_y - output_y

            if not DISABLE_MOUSE_OUTPUT:
                if output_x != 0 or output_y != 0:
                    try:
                        mouse.相对移动(output_x, output_y)
                    except AttributeError:
                        try:
                            mouse.relative_move(output_x, output_y)
                        except:
                            mouse.相对移动卡尔曼(output_x, output_y, 步数=1, 噪声=0)
        else:
            if not left_clicked or state["target_id"] == -1:
                last_output_x *= 0.8
                last_output_y *= 0.8
            if not DISABLE_MOUSE_OUTPUT and (recoil_dx != 0 or recoil_dy != 0):
                try:
                    mouse.相对移动(recoil_dx, recoil_dy)
                except AttributeError:
                    try:
                        mouse.relative_move(recoil_dx, recoil_dy)
                    except:
                        mouse.相对移动卡尔曼(recoil_dx, recoil_dy, 步数=1, 噪声=0)

        last_state = state["state"]
        time.sleep(0.001)

# =====================================================================
# 4. 主进程 UI 面板与参数持久化
# =====================================================================
if __name__ == '__main__':
    multiprocessing.freeze_support()

    CONFIG_FILE = "aim_config.json"
    
    # 【核心优化 6】注入全新“稳如泰山”级出厂预设
    DEFAULT_CFG = {
        "smooth_x": 0.10, "smooth_y": 0.20, "deadzone": 5.0, "max_disp": 15.0,
        "switch_thru": 80.0, "conf": 0.25, "aim_part": 0.25, "kp": 0.10, "kd": 0.045
    }
    
    def load_cfg():
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    return {**DEFAULT_CFG, **loaded}
            except: pass
        return DEFAULT_CFG.copy()
        
    cfg = load_cfg()
    
    state_buffer = AtomicTargetState()
    shared_active = multiprocessing.Value('b', True)
    shared_team_is_t = multiprocessing.Value('b', True)
    shared_deathmatch = multiprocessing.Value('b', False)
    
    shared_smooth_x = multiprocessing.Value('d', cfg["smooth_x"])   
    shared_smooth_y = multiprocessing.Value('d', cfg["smooth_y"])   
    shared_deadzone = multiprocessing.Value('d', cfg["deadzone"])    
    shared_max_disp = multiprocessing.Value('d', cfg["max_disp"])   
    shared_switch_thru = multiprocessing.Value('d', cfg["switch_thru"])
    shared_conf = multiprocessing.Value('d', cfg["conf"])
    shared_aim_part = multiprocessing.Value('d', cfg["aim_part"])
    shared_kp = multiprocessing.Value('d', cfg["kp"])          
    shared_kd = multiprocessing.Value('d', cfg["kd"])         
    
    shared_weapon_id = multiprocessing.Value('i', 0)      

    p_vision = multiprocessing.Process(
        target=vision_observation_process, 
        args=(state_buffer, shared_active, shared_conf, shared_switch_thru, shared_aim_part, shared_team_is_t, shared_deathmatch),
        daemon=True
    )
    p_vision.start()

    p_control = multiprocessing.Process(
        target=control_driving_process,
        args=(state_buffer, shared_active, shared_smooth_x, shared_smooth_y, shared_deadzone, shared_max_disp, shared_kp, shared_kd, shared_weapon_id),
        daemon=True
    )
    p_control.start()

    root = tk.Tk()
    root.title("硬核自瞄级联中控台")
    root.geometry("360x860")
    root.attributes("-topmost", True)
    root.configure(padx=10, pady=10)
    
    def on_closing():
        print("系统正在安全关闭子进程...")
        p_vision.terminate()
        p_control.terminate()
        root.destroy()
        sys.exit()
    root.protocol("WM_DELETE_WINDOW", on_closing)

    top_btn_frame = tk.Frame(root)
    top_btn_frame.pack(fill=tk.X, pady=(0, 10))
    
    btn_active = tk.Button(top_btn_frame, font=("", 9, "bold"), height=2, command=lambda: setattr(shared_active, 'value', not shared_active.value))
    btn_active.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1)
    
    btn_team = tk.Button(top_btn_frame, font=("", 9, "bold"), height=2, command=lambda: setattr(shared_team_is_t, 'value', not shared_team_is_t.value))
    btn_team.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1)

    btn_deathmatch = tk.Button(top_btn_frame, font=("", 9, "bold"), height=2, command=lambda: setattr(shared_deathmatch, 'value', not shared_deathmatch.value))
    btn_deathmatch.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1)

    weapon_lbl = tk.Label(root, text="当前武器: 初始化中", font=("", 11, "bold"), fg="#ff6600", bg="#f0f0f0", pady=4)
    weapon_lbl.pack(fill=tk.X, pady=(0, 5))

    ui_controls = {}

    preset_frame = tk.LabelFrame(root, text="防抖核心预设", fg="#cc3333", padx=5, pady=5, font=("", 9, "bold"))
    preset_frame.pack(fill=tk.X, pady=5)
    
    PRESETS = {
        "稳如泰山": {
            "smooth_x": 0.10, "smooth_y": 0.20, "deadzone": 5.0, "max_disp": 15.0,
            "switch_thru": 80.0, "conf": 0.25, "aim_part": 0.25, "kp": 0.10, "kd": 0.045
        },
        "死锁追踪": {
            "smooth_x": 0.15, "smooth_y": 0.30, "deadzone": 4.0, "max_disp": 18.0,
            "switch_thru": 50.0, "conf": 0.20, "aim_part": 0.15, "kp": 0.12, "kd": 0.035
        }
    }

    def apply_preset(name):
        if name in PRESETS:
            for k, v in PRESETS[name].items():
                if k in ui_controls:
                    ui_controls[k][0].set(v)
                    
    def save_current_cfg():
        current_cfg = {k: v.value for k, (s, v) in ui_controls.items()}
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(current_cfg, f, indent=4)
            btn_save.config(text="✔ 保存成功", bg="#4CAF50", fg="white")
            root.after(1500, lambda: btn_save.config(text="💾 保存参数", bg="SystemButtonFace", fg="black"))
        except Exception as e:
            pass

    btn_tpl1 = tk.Button(preset_frame, text="🛡️ 稳如泰山(推荐)", command=lambda: apply_preset("稳如泰山"))
    btn_tpl1.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

    btn_tpl2 = tk.Button(preset_frame, text="🎯 死锁追踪", command=lambda: apply_preset("死锁追踪"))
    btn_tpl2.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

    btn_save = tk.Button(preset_frame, text="💾 保存", command=save_current_cfg)
    btn_save.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

    说明文本 = tk.Label(root, text="[系统就绪] 重构底层防抖，死锁动态闸门已开启", fg="gray", wraplength=300, justify="left", height=3)

    def 创建同步滑块(父容器, 标签文本, 内部键名, 共享变量, 最小值, Max值, 步长, 提示):
        frame = tk.Frame(父容器)
        frame.pack(fill=tk.X, pady=1)
        
        lbl_frame = tk.Frame(frame)
        lbl_frame.pack(side=tk.LEFT)
        tk.Label(lbl_frame, text=标签文本, width=9, anchor="w").pack(side=tk.LEFT)
        
        help_lbl = tk.Label(lbl_frame, text="[?]", fg="#0066cc", cursor="hand2", font=("", 9, "bold"))
        help_lbl.pack(side=tk.LEFT)
        help_lbl.bind("<Enter>", lambda e: 说明文本.config(text=提示, fg="black"))
        help_lbl.bind("<Leave>", lambda e: 说明文本.config(text="鼠标悬停在 [?] 上查看参数说明", fg="gray"))
        
        def on_slide(val):
            共享变量.value = float(val)
            
        scale = tk.Scale(frame, from_=最小值, to=Max值, resolution=步长, orient=tk.HORIZONTAL, command=on_slide)
        scale.set(共享变量.value)
        scale.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5,0))
        
        ui_controls[内部键名] = (scale, 共享变量)

    frame_track = tk.LabelFrame(root, text="追踪与平滑参数", fg="black")
    frame_track.pack(fill=tk.X, pady=4)
    创建同步滑块(frame_track, "X轴增益", "smooth_x", shared_smooth_x, 0.02, 1.0, 0.01, "决定准星在横向向目标移动时的速度与黏性。")
    创建同步滑块(frame_track, "Y轴增益", "smooth_y", shared_smooth_y, 0.02, 1.0, 0.01, "决定准星在纵向向目标移动时的速度与黏性。")
    创建同步滑块(frame_track, "最大拉力", "max_disp", shared_max_disp, 5.0, 100.0, 1.0, "限制鼠标每帧允许移动的最大像素，强制物理平滑。")

    frame_vision = tk.LabelFrame(root, text="视觉与靶区", fg="black")
    frame_vision.pack(fill=tk.X, pady=4)
    创建同步滑块(frame_vision, "视觉置信度", "conf", shared_conf, 0.1, 0.9, 0.05, "过滤模型画框的阈值，实战建议0.2-0.3。")
    创建同步滑块(frame_vision, "瞄准高度", "aim_part", shared_aim_part, 0.05, 0.9, 0.05, "决定准星锁定在目标身体的哪个部位。0.1偏头，0.3偏胸。")
    创建同步滑块(frame_vision, "死区防抖", "deadzone", shared_deadzone, 0.0, 10.0, 0.5, "极度关键：距离胸口多少像素时强制切断拉力，调高防帕金森抖动。")
    
    frame_pid = tk.LabelFrame(root, text="底层 PID 硬件干预", fg="black")
    frame_pid.pack(fill=tk.X, pady=4)
    创建同步滑块(frame_pid, "Kp (响应)", "kp", shared_kp, 0.05, 1.0, 0.01, "基础拉力参数，过大会导致准星甩过头。")
    创建同步滑块(frame_pid, "Kd (阻尼)", "kd", shared_kd, 0.0, 0.1, 0.005, "防抖阻尼刹车，调大可以像吸铁石一样吸住小碎步的敌人。")

    说明文本.pack(side=tk.TOP, fill=tk.X, pady=(2, 0))

    help_frame = tk.LabelFrame(root, text="宏快捷键与提示", fg="blue", padx=8, pady=4, font=("", 9, "bold"))
    help_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(0, 0))
    tk.Label(help_frame, text="F7: 关闭压枪宏状态 | 中键(G3): AK/Galil/553", anchor="w", justify="left").pack(fill=tk.X)
    tk.Label(help_frame, text="上侧(G5): M4/AUG", anchor="w", justify="left").pack(fill=tk.X)
    tk.Label(help_frame, text="F8 快捷挂起或唤醒全局自瞄程序", anchor="w", justify="left", fg="green").pack(fill=tk.X)

    def update_gui_loop():
        if shared_active.value:
            btn_active.config(text="自瞄状态\n运行中", bg="#cc3333", fg="white")
        else:
            btn_active.config(text="自瞄状态\n已挂起", bg="#339933", fg="white")
            
        if shared_deathmatch.value:
            btn_deathmatch.config(text="死斗模式\n【开启】", bg="#990000", fg="white")
            btn_team.config(text="当前阵营\n已失效", bg="gray", fg="white", state=tk.DISABLED)
        else:
            btn_deathmatch.config(text="死斗模式\n【关闭】", bg="#f0f0f0", fg="black")
            btn_team.config(state=tk.NORMAL)
            if shared_team_is_t.value:
                btn_team.config(text="当前阵营\n【匪】", bg="#cca300", fg="white")
            else:
                btn_team.config(text="当前阵营\n【警】", bg="#0066cc", fg="white")
        
        current_w_id = shared_weapon_id.value
        w_name = WEAPON_NAME_MAP.get(current_w_id, "未知武器")
        if current_w_id == 0:
            weapon_lbl.config(text=f"当前武器: {w_name}", fg="gray")
        else:
            weapon_lbl.config(text=f"当前武器: {w_name}", fg="#0066cc")

        root.after(100, update_gui_loop)
    
    update_gui_loop()
    root.mainloop()
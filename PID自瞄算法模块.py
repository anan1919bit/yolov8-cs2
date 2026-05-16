
class PID初始化:
    '''1. 初始化方法'''
    def __init__(self, 采样周期,kp,ki,kd):#最大调整值,最小调整值,
        self.采样周期 = 采样周期
        # self.最大调整值 = 最大调整值
        # self.最小调整值 = 最小调整值
        # 获取PID 参数
        self.kp, self.ki, self.kd = kp, ki, kd
        self.积分和 = 0
        self.上次偏差 = 0
        self.当前偏差 = 0
    def PID算法_Position_Y(self,目标Y,识别区域高度除2):
        self.当前偏差 = 目标Y - 识别区域高度除2
        局_比例项P结果 = self.kp*self.当前偏差
        self.积分和 = self.积分和 + self.当前偏差*self.采样周期
        局_积分项I结果 = self.ki*self.积分和
        局_微分项值 = (self.当前偏差-self.上次偏差)/self.采样周期
        局_微分项D结果 = self.kd*局_微分项值
        局_PID结果 = 局_比例项P结果 + 局_积分项I结果 + 局_微分项D结果
        self.上次偏差 = self.当前偏差
        return int(round(局_PID结果, 0))
    def PID算法_Position_X(self,目标X,识别区域宽度除2):
        self.当前偏差 = 目标X - 识别区域宽度除2
        局_比例项P结果 = self.kp*self.当前偏差
        self.积分和 = self.积分和 + self.当前偏差*self.采样周期
        局_积分项I结果 = self.ki*self.积分和
        局_微分项值 = (self.当前偏差-self.上次偏差)/self.采样周期
        局_微分项D结果 = self.kd*局_微分项值
        局_PID结果 = 局_比例项P结果 + 局_积分项I结果 + 局_微分项D结果
        self.上次偏差 = self.当前偏差
        return int(round(局_PID结果, 0))


import math


def YOLO取准星最近敌人(x, y, w, h, X瞄准位置, y瞄准位置, 识别区域宽度除2, 识别区域高度除2):
    """
    计算YOLO检测框中心点到准星位置的距离

    参数:
        x, y: 检测框左上角坐标
        w, h: 检测框的宽度和高度
        X瞄准位置, y瞄准位置: 准星在识别区域中的位置（比例坐标，0-1之间）
        识别区域宽度除2: 识别区域宽度的一半,例如识别区域宽度640像素这里就输入320
        识别区域高度除2: 识别区域高度的一半,例如识别区域高度800像素 这里就输入400

    返回:
        检测框中心点到准星的距离
    """

    # 计算检测框中心点坐标
    # x + w * X瞄准位置 表示检测框中心的X坐标
    # y + h * y瞄准位置 表示检测框中心的Y坐标

    # 计算中心点相对于识别区域中心的偏移
    center_x = x + w * X瞄准位置
    center_y = y + h * y瞄准位置

    # 计算偏移量（相对于识别区域中心）
    offset_x = center_x - 识别区域宽度除2
    offset_y = center_y - 识别区域高度除2

    # 计算距离：sqrt((offset_x)^2 + (offset_y)^2)
    result = math.sqrt(offset_x ** 2 + offset_y ** 2)

    return result
def 取两点之间距离(x1,y1,x2,y2):
    return math.sqrt((x1-x2)**2+(y1-y2)**2)

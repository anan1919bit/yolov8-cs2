"""
***
LG丶狐小明
2025-01-31


匈牙利目标匹配＋卡尔曼滤波
***
"""

from scipy.optimize import linear_sum_assignment

import numpy as np
import cv2


class HungarianAlgorithm:
    def __init__(self):

        self.target_list = []
        self.new_target_list = []
        self.target_num = 0

    def opt_targets(self, new_target_list):
        self.new_target_list.clear()  # 清空新目标列表

        self.new_target_list = new_target_list
        target_match_result_list = self.hungarian_algorithm()
        matched_previous_index_dict = {}
        matched_index_list = []
        for match_relation in target_match_result_list:
            matched_previous_index_dict[match_relation[0]] = match_relation[1]
            matched_index_list.append(match_relation[1])

        expired_target_list = []
        for index, target in enumerate(self.target_list):
            if index not in matched_previous_index_dict.keys():
                expired_target_list.append(target)
                continue
            target.update_position(
                self.new_target_list[matched_previous_index_dict[index]][1],
                self.new_target_list[matched_previous_index_dict[index]][2],
            )
        for expired_target in expired_target_list:
            self.target_list.remove(expired_target)

        for index in range(0, len(self.new_target_list)):
            if index in matched_index_list:
                continue
            new_target = self.new_target_list[index]
            target = Target(
                new_target[0], self.target_num, new_target[1], new_target[2]
            )
            self.target_num += 1
            self.target_list.append(target)

        return self.target_list

    def hungarian_algorithm(self):
        # 匈牙利算法，用于目标匹配
        matche_result = []
        previous_targets_num = len(self.target_list)
        targets_num = len(self.new_target_list)
        if previous_targets_num > 0 and targets_num > 0:
            distances = [[0] * targets_num for i in range(previous_targets_num)]
            for i in range(previous_targets_num):
                for j in range(targets_num):
                    if self.target_list[i].label != self.new_target_list[j][0]:
                        continue
                    distances[i][j] = (
                        abs(
                            self.target_list[i].left_top[0]
                            - self.new_target_list[j][1][0]
                        )
                        + abs(
                            self.target_list[i].left_top[1]
                            - self.new_target_list[j][1][1]
                        )
                        + abs(
                            self.target_list[i].right_bottom[0]
                            - self.new_target_list[j][2][0]
                        )
                        + abs(
                            self.target_list[i].right_bottom[1]
                            - self.new_target_list[j][2][1]
                        )
                    )
            row_ind, col_ind = linear_sum_assignment(distances)
            for i in range(len(row_ind)):
                matche_result.append((row_ind[i], col_ind[i]))
        return matche_result


class Target:
    def __init__(self, label, index, left_top, right_bottom):
        self.label = label
        self.index = index
        self.left_top_kf = KalmanFilter(
            left_top[0],
            left_top[1],  # process_noise_cov=1e-2, measurement_noise_cov=1e-1
        )
        self.right_bottom_kf = KalmanFilter(
            right_bottom[0],
            right_bottom[1],
            # process_noise_cov=1e-2,
            # measurement_noise_cov=1e-1,
        )
        self.left_top = left_top
        self.right_bottom = right_bottom
        self.update_time = 0

    def update_position(self, left_top, right_bottom):
        # 直接更新
        self.left_top = left_top
        self.right_bottom = right_bottom

        # # 卡尔曼滤波
        # self.update_time += 1
        # # 平滑因子
        # alpha = min(0.5, self.update_time / 100.0)
        # # 预测并校正左上角位置
        # self.left_top_kf.predict()
        # corrected_left_top = self.left_top_kf.correct(left_top[0], left_top[1])
        # self.left_top = (
        #     (1 - alpha) * left_top[0] + alpha * corrected_left_top[0],
        #     (1 - alpha) * left_top[1] + alpha * corrected_left_top[1],
        # )
        # # 预测并校正右下角位置
        # self.right_bottom_kf.predict()
        # corrected_right_bottom = self.right_bottom_kf.correct(
        #     right_bottom[0], right_bottom[1]
        # )
        # self.right_bottom = (
        #     (1 - alpha) * right_bottom[0] + alpha * corrected_right_bottom[0],
        #     (1 - alpha) * right_bottom[1] + alpha * corrected_right_bottom[1],
        # )

    def __repr__(self):
        return f"label: {self.label}, id: {self.index}, box: {self.left_top}, {self.right_bottom}"


class KalmanFilter:
    def __init__(
        self, init_x, init_y, process_noise_cov=1e-4, measurement_noise_cov=1e-1
    ):
        self.kf = cv2.KalmanFilter(1, 4)
        self.kf.measurementMatrix = np.array([[1, 0, 0, 0], [0, 1, 0, 0]], np.float32)
        self.kf.transitionMatrix = np.array(
            [[1, 0, 1, 0], [0, 1, 0, 1], [0, 0, 1, 0], [0, 0, 0, 1]], np.float32
        )
        self.kf.processNoiseCov = np.eye(4, dtype=np.float32) * process_noise_cov
        self.kf.measurementNoiseCov = (
            np.eye(2, dtype=np.float32) * measurement_noise_cov
        )
        self.kf.statePost = np.array([[init_x], [init_y], [0], [0]], np.float32)
        self.kf.statePre = np.array([[init_x], [init_y], [0], [0]], np.float32)

    def predict(self):
        predicted = self.kf.predict()
        return predicted[0, 0], predicted[1, 0]

    def correct(self, x, y):
        measured_value = np.array([[np.float32(x)], [np.float32(y)]])
        self.kf.correct(measured_value)
        corrected = self.kf.statePost
        return corrected[0, 0], corrected[1, 0]


if __name__ == "__main__":
    hungarian_algorithm = HungarianAlgorithm()
    box = hungarian_algorithm.opt_targets(
        new_target_list=[
            ("car", (100, 100), (200, 200)),
            ("person", (300, 300), (400, 400)),
            ("car", (500, 500), (600, 600)),
            ("person", (700, 700), (800, 800)),
            ("car", (900, 900), (1000, 1000)),
        ]
    )

    print(box)

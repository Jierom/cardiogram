
import numpy as np
from variables import *

def strengthen_point(im_arr, point):
    (height, width, depth) = im_arr.shape
    (y, x) = point
    im_arr[y, x] = STRENGTHEN_COLOR
    if 0 <= y+1 < height and 0 <= x < width: im_arr[y+1, x] = STRENGTHEN_COLOR
    if 0 <= y < height and 0 <= x+1 < width: im_arr[y, x+1] = STRENGTHEN_COLOR
    if 0 <= y-1 < height and 0 <= x < width: im_arr[y-1, x] = STRENGTHEN_COLOR
    if 0 <= y < height and 0 <= x-1 < width: im_arr[y, x-1] = STRENGTHEN_COLOR
    if 0 <= y+1 < height and 0 <= x+1 < width: im_arr[y+1, x+1] = STRENGTHEN_COLOR
    if 0 <= y+1 < height and 0 <= x-1 < width: im_arr[y+1, x-1] = STRENGTHEN_COLOR
    if 0 <= y-1 < height and 0 <= x+1 < width: im_arr[y-1, x+1] = STRENGTHEN_COLOR
    if 0 <= y-1 < height and 0 <= x-1 < width: im_arr[y-1, x-1] = STRENGTHEN_COLOR

def draw_line(im_arr, yline, xline):
    (height, width, depth) = im_arr.shape
    if yline == None:
        for y in range(0, height):
            im_arr[y, xline] = STRENGTHEN_COLOR
    if xline == None:
        for x in range(0, width):
            im_arr[yline, x] = STRENGTHEN_COLOR

def draw_points(im_arr, points):
    for point in points:
        im_arr[point[0], point[1]] = STRENGTHEN_COLOR

def is_white(point):
    return point[0] == 255 and point[1] == 255 and point[2] == 255

class PictureResult:
    # 初始化
    def __init__(self, name, r_max, j_values):
        self.name = name
        self.r_max = r_max
        self.j_values = j_values

class Picture:
    # 初始化
    def __init__(self, im_arr):
        # 图片数组
        self.im_arr = im_arr
        self.bin_arr = None
        self.show_arr = None

        # 曲线点
        self.points = []

        # 结果点
        self.r_points = []
        self.r_values = []
        self.j_points = []
        self.j_values = []

        # 坐标对应数值
        self.ymaps = []

    '''
    二值化
    '''
    # 曲线二值化
    def line_binary(self):
        (height, width, depth) = self.im_arr.shape
        dst = np.zeros((height, width, 3))
        for y in range(0, height):
            for x in range(0, width):
                (r, g, b) = self.im_arr[y, x]
                if r > 100 and g < 100 and b < 100:
                    dst[y, x] = PURE_WHITE
                    self.points.append((y, x))
                else:
                    dst[y, x] = PURE_BLACK
        self.bin_arr = dst

    # 网格二值化
    def mesh_binary(self):
        (height, width, depth) = self.im_arr.shape
        dst = np.zeros((height, width, 3))
        for y in range(0, height):
            for x in range(0, width):
                (r, g, b) = self.im_arr[y, x]
                if r < 200 and g < 200 and b < 200:
                    dst[y, x] = PURE_WHITE
                else:
                    dst[y, x] = PURE_BLACK
        self.mesh_arr = dst

    '''
    寻找 R 点
    '''
    def find_r_points(self):
        (height, width, depth) = self.bin_arr.shape
        y_limit = height
        for y in range(0, height):
            if y >= y_limit:
                break
            for x in range(0, width):
                point = self.bin_arr[y, x]
                if is_white(point):
                    if y_limit == height:
                        y_limit = y + R_ylimit
                        self.r_points.append((y,x))
                    else:
                        # 检查间隙判断是否添加为 r 点
                        if_add = True
                        for r_point in self.r_points:
                            if abs(x - r_point[1]) < R_xlimit:
                                if_add = False
                        if if_add:
                            self.r_points.append((y, x))
        self.r_points = sorted(self.r_points, key=lambda p: p[1])

    '''
    寻找 J 点
    '''
    # 同一列只保留一个最高值
    def del_duplicated(self, points):
        new_points = []
        for i in range(len(points)):
            point = points[i]
            if i == 0:
                new_points.append(point)
            elif point[1] != points[i-1][1]:
                new_points.append(point)
        return new_points

    # 找到 filter_points 中即考察期内第一个极大值点
    def find_localmax_point(self, filter_points, r_point):
        for i in range(len(filter_points)):
            point = filter_points[i]
            # 排除 R 点附近的极大值点
            if point[1] == r_point[1] or point[0] == r_point[0]:
                continue
            l = i
            r = i
            lmax = False
            rmax = False
            while l >= 0:
                if filter_points[l][0] > point[0]:
                    lmax = True
                    break
                elif filter_points[l][0] < point[0]:
                    lmax = False
                    break
                l = l - 1
            while r < len(filter_points):
                if filter_points[r][0] > point[0]:
                    rmax = True
                    break
                elif filter_points[r][0] < point[0]:
                    rmax = False
                    break
                r = r + 1
            if lmax and rmax:
                return point

    # 找到 filter_points 中即考察期内最高的平台点
    def find_platform_point(self, filter_points, r_point):
        min_y = 10000
        result = None
        for i in range(len(filter_points)):
            point = filter_points[i]
            # 排除 R 点附近的点
            if point[1] == r_point[1] or point[0] == r_point[0]:
                continue
            if i == 0:
                continue
            if point[0] == filter_points[i-1][0] and point[0] <= min_y:
                min_y = point[0]
                result = point
        return result

    def find_j_points(self):
        # 从每个 r 点开始看一段考察期
        for r_point in self.r_points:
            xbegin = r_point[1]
            xend = xbegin + R_xlimit
            filter_points = sorted(list(filter(lambda p: xbegin <= p[1] <= xend, self.points)), key=lambda p: p[1])
            filter_points = self.del_duplicated(filter_points)

            localmax_point = self.find_localmax_point(filter_points, r_point)
            platform_point = self.find_platform_point(filter_points, r_point)

            # 如果平台点来得更靠左且更高
            if platform_point is not None and localmax_point is None:
                j_point = platform_point
            elif localmax_point is not None and platform_point is None:
                j_point = localmax_point
            elif platform_point is not None and localmax_point is not None and platform_point[1] < localmax_point[1] and platform_point[0] < localmax_point[0]:
                j_point = platform_point
            else:
                j_point = localmax_point
            if j_point is not None:
                self.j_points.append(j_point)
        self.j_points = sorted(self.j_points, key=lambda p: p[1])

    '''
    计算网格坐标
    '''
    def find_base_line(self):
        find_one = False
        for y in range(BASE_LINE_RANGE[0], BASE_LINE_RANGE[1]):
            cnt = 0
            for x in range(self.mesh_arr.shape[1]):
                point = self.mesh_arr[y, x]
                if is_white(point):
                    cnt = cnt + 1
            if cnt > 600:
                if find_one:
                    return y - 1
                else:
                    find_one = True

    def find_ymap(self):
        base_line = self.find_base_line()
        line_begin = base_line + 20
        num = -1
        for y in range(line_begin, -1, -1):  # 反着取
            if y == base_line + 1:
                continue
            cnt = -1
            for x in range(self.mesh_arr.shape[1]):
                point = self.mesh_arr[y, x]
                if is_white(point):
                    cnt = cnt + 1
            if cnt > 600:
                self.ymaps.append((y, round(num * 0.1, 2)))
                num = num + 1

    '''
    代入计算点的真实值
    '''
    def calc_value(self, point):
        for i in range(1, len(self.ymaps)):
            if self.ymaps[i][0] <= point[0] < self.ymaps[i-1][0]:
                rate = (self.ymaps[i-1][0] - point[0]) / (self.ymaps[i-1][0] - self.ymaps[i][0])
                return round(self.ymaps[i-1][1] + 0.1 * rate, 2)

    def calc_r_values(self):
        r_points = sorted(self.r_points, key=lambda p: p[1])
        for point in r_points:
            self.r_values.append(self.calc_value(point))
        print(self.r_values)

    def calc_j_values(self):
        j_points = sorted(self.j_points, key=lambda p: p[1])
        for point in j_points:
            self.j_values.append(self.calc_value(point))
        print(self.j_values)

    '''
    准备展示用图片
    '''
    def prepare_show(self):
        self.show_arr = self.im_arr
        # self.show_arr = self.bin_arr
        min_y = 10000
        max_r_point = None
        for point in self.r_points:
            if point[0] <= min_y:
                min_y = point[0]
                max_r_point = point
        strengthen_point(self.show_arr, max_r_point)
        # for point in self.r_points:
            # draw_points(self.show_arr, [point])
            # strengthen_point(self.show_arr, point)
        for point in self.j_points:
            # draw_points(self.show_arr, [point])
            strengthen_point(self.show_arr, point)
        # draw_points(self.show_arr, self.filter_points)

import os
import csv
from PIL import Image
import numpy as np

from picture import Picture, PictureResult
from variables import *
raw_data_path = "raw-data"

file_lists = []
results = []

'''
遍历指定目录下所有文件
'''
def traverse_path(rootDir):
    for root, dirs, files in os.walk(rootDir):
        for file in files:
            file_lists.append(os.path.join(root, file))
        for dir in dirs:
            traverse_path(dir)


def treatment(filename):
    im = Image.open(filename)
    # print(im.size)
    im = im.crop(CUT_INDEX)
    # im.show()
    im_arr = np.array(im)
    picture = Picture(im_arr)

    # 线路图二值化
    picture.line_binary()
    picture.find_r_points()
    picture.find_j_points()

    # 网格图二值化
    picture.mesh_binary()
    picture.find_ymap()

    # 计算 r 和 j 结果
    picture.calc_r_values()
    picture.calc_j_values()

    # 生成结果数据
    name = filename.split('/')[-1]
    name = name.replace('.jpg', '')
    picture_result = PictureResult(name, max(picture.r_values), picture.j_values)
    results.append(picture_result)

    # 存入处理图
    target_filename = "target/" + filename
    if not os.path.exists(os.path.dirname(target_filename)):
        os.makedirs(os.path.dirname(target_filename))
    if not os.path.exists(target_filename):
        os.mknod(target_filename)
    picture.prepare_show()
    im2 = Image.fromarray(np.uint8(picture.show_arr))
    im2.save(target_filename, quality=90,subsampling=0)



if __name__ == "__main__":
    traverse_path(raw_data_path)
    # file_lists = sorted(file_lists, key=lambda f: f.split('/')[-1])
    file_lists = ["raw-data/wt+PBS/1-3.1.jpg"]
    for file in file_lists:
        print(file)
        treatment(file)

    # 结果写入csv
    f = open('result.csv', 'w', encoding='utf-8')
    csv_writer = csv.writer(f)
    for result in results:
        data = []
        data.append(result.name)
        data.append(result.r_max)
        data.append(' ')
        data = data + result.j_values
        csv_writer.writerow(data)
    f.close()

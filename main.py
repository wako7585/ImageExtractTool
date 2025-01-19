import os
import sys
import shutil
import json
import hashlib
import time

import cv2
import numpy as np

APP_SERVER = ["jp", "tw"]
IMAGE_RES_PATH = "D:\\BotProject\\MonsterStrikeBot\\resource"
EXTRACT_ASSETS_PATH = "D:\\BotProject\\MSBotUpdate\\assets"
EXTRACT_ASSETS_MD5_PATH = "D:\\BotProject\\MSBotUpdate\\assets\\assets.md5"
EXTRACT_M_COLOR_PATH = "D:\\BotProject\\MonsterStrikeBot\\脚本\\M_COLOR.lua"
EMULATOR_ASSETS_PATH = "/sdcard/assets"

M_COLOR = {}
FILE_MD5 = {}


def get_file_name(input_file):
    dir, temp_file_name = os.path.split(input_file)  # split path & file name
    name, _ = os.path.splitext(temp_file_name)  # split file name & file type
    return name


def traversal_folder(input_folder_path):
    file_list = []
    for root, dir, files in os.walk(input_folder_path, topdown=False):
        for name in files:
            file_path = os.path.join(root, name)
            file_list.append(file_path)

    return file_list


def create_dir(input_file):
    dir_path = os.path.dirname(input_file)
    if os.path.exists(dir_path):
        pass
    else:
        os.makedirs(dir_path)


def delete_duplicate(compare_server):
    temp_file = {}
    file_B = traversal_folder(os.path.join(IMAGE_RES_PATH, compare_server))
    for i in range(len(file_B)):
        temp_file[i] = file_B[i].replace(compare_server, APP_SERVER[0])
        if os.path.exists(temp_file[i]):
            pass
        else:
            print("Remove %s" % file_B[i])
            os.remove(file_B[i])


def complete_image(input_server):
    if input_server == APP_SERVER[0]:
        print("No need to complete image from main server")
        return

    temp_file = {}
    file_A = traversal_folder(os.path.join(IMAGE_RES_PATH, APP_SERVER[0]))
    for i in range(len(file_A)):
        temp_file[i] = file_A[i].replace(APP_SERVER[0], input_server)
        if os.path.exists(temp_file[i]):
            pass
        else:
            try:
                print("Copy file from %s" % file_A[i])
                create_dir(temp_file[i])
                shutil.copy(file_A[i], temp_file[i])
            except IOError as e:
                print("Unable to copy file %s" % e)
                sys.exit(1)
            except:
                print("Unexpected error : ", sys.exc_info())
                sys.exit(1)


def get_image_size(image):
    shape = image.shape
    return shape[1], shape[0]


def crop_image(input_file):
    img = cv2.imread(input_file)
    try:
        size = get_image_size(img)
        if size != (720, 1280):
            raise ValueError("Resource image is not 720x1280")
    except ValueError as e:
        print("Unexpected error : ", repr(e))
        sys.exit(1)

    y_nonzero, x_nonzero, _ = np.nonzero(img)
    y1 = np.min(y_nonzero)
    y2 = np.max(y_nonzero)
    x1 = np.min(x_nonzero)
    x2 = np.max(x_nonzero)
    # print(input_file)
    # print(f'Crop area : [{x1},{y1},{x2},{y2}]')
    create_dir(input_file.replace(IMAGE_RES_PATH, EXTRACT_ASSETS_PATH))
    cv2.imwrite(input_file.replace(IMAGE_RES_PATH, EXTRACT_ASSETS_PATH), img[y1: y2, x1: x2])
    return [x1, y1, x2, y2]


def extract_image(input_server, input_file):
    extract_file = input_file.replace(IMAGE_RES_PATH, EXTRACT_ASSETS_PATH)
    file_name = get_file_name(extract_file)
    if "TEMPLATE_" in input_file:
        create_dir(extract_file)
        shutil.copy(input_file, extract_file)
    else:
        crop_area = crop_image(input_file)
        # print(input_file, crop_area)
        M_COLOR[file_name]["AREA"][input_server] = crop_area

    M_COLOR[file_name]["PATH"][input_server] = extract_file.replace(EXTRACT_ASSETS_PATH, EMULATOR_ASSETS_PATH).replace("\\", "/")
    img = cv2.imread(extract_file)
    shape = get_image_size(img)
    M_COLOR[file_name]["W"][input_server] = shape[0]
    M_COLOR[file_name]["H"][input_server] = shape[1]


def create_data_M_COLOR():
    file_M = traversal_folder(os.path.join(IMAGE_RES_PATH, APP_SERVER[0]))
    for j in range(len(file_M)):
        # 宣告 M_COLOR key
        file_name = get_file_name(file_M[j])
        M_COLOR[file_name] = {}
        M_COLOR[file_name]["W"] = {}
        M_COLOR[file_name]["H"] = {}
        M_COLOR[file_name]["PATH"] = {}
        if "TEMPLATE_" not in file_name:
            M_COLOR[file_name]["AREA"] = {}

        for i in range(len(APP_SERVER)):
            file_M[j] = file_M[j].replace(APP_SERVER[0], APP_SERVER[i])
            # print(file_M[j])
            extract_image(APP_SERVER[i], file_M[j])


def turn_into_color_format(array):
    file_name = get_file_name(array["PATH"][APP_SERVER[0]])
    if "TEMPLATE_" in file_name:
        PATH = []
        W = []
        H = []
        for i in range(len(APP_SERVER)):
            PATH.append(format("%s = '%s'" % (APP_SERVER[i].upper(), array["PATH"][APP_SERVER[i]])))
            W.append(format("%s = '%s'" % (APP_SERVER[i].upper(), array["W"][APP_SERVER[i]])))
            H.append(format("%s = '%s'" % (APP_SERVER[i].upper(), array["H"][APP_SERVER[i]])))

        path_f = format("PATH = { %s }" % (", ".join(PATH)))
        # print(path_f)
        width_f = format("W = { %s }" % (", ".join(W)))
        # print(width_f)
        height_f = format("H = { %s }" % (", ".join(H)))
        # print(height_f)
        all_f = format("M_COLOR.%s = { %s, %s, %s }" % (file_name, path_f, width_f, height_f))
        # print(all_f)
        return all_f

    if "BUTTON_" in file_name:
        AREA = []
        W = []
        H = []
        for i in range(len(APP_SERVER)):
            AREA.append(format("%s = { %s, %s, %s, %s}" % (APP_SERVER[i].upper(), array["AREA"][APP_SERVER[i]][0], array["AREA"]
                        [APP_SERVER[i]][1], array["AREA"][APP_SERVER[i]][2], array["AREA"][APP_SERVER[i]][3])))
            W.append(format("%s = '%s'" % (APP_SERVER[i].upper(), array["W"][APP_SERVER[i]])))
            H.append(format("%s = '%s'" % (APP_SERVER[i].upper(), array["H"][APP_SERVER[i]])))

        area_f = format("AREA = { %s }" % (", ".join(AREA)))
        # print(area_f)
        width_f = format("W = { %s }" % (", ".join(W)))
        height_f = format("H = { %s }" % (", ".join(H)))
        all_f = format("M_COLOR.%s = { %s, %s, %s }" % (file_name, area_f, width_f, height_f))
        # print(all_f)
        return all_f
    else:
        AREA = []
        PATH = []
        W = []
        H = []
        for i in range(len(APP_SERVER)):
            AREA.append(format("%s = { %s, %s, %s, %s}" % (APP_SERVER[i].upper(), array["AREA"][APP_SERVER[i]][0], array["AREA"]
                        [APP_SERVER[i]][1], array["AREA"][APP_SERVER[i]][2], array["AREA"][APP_SERVER[i]][3])))
            PATH.append(format("%s = '%s'" % (APP_SERVER[i].upper(), array["PATH"][APP_SERVER[i]])))
            W.append(format("%s = '%s'" % (APP_SERVER[i].upper(), array["W"][APP_SERVER[i]])))
            H.append(format("%s = '%s'" % (APP_SERVER[i].upper(), array["H"][APP_SERVER[i]])))

        area_f = format("AREA = { %s }" % (", ".join(AREA)))
        path_f = format("PATH = { %s }" % (", ".join(PATH)))
        width_f = format("W = { %s }" % (", ".join(W)))
        height_f = format("H = { %s }" % (", ".join(H)))
        all_f = format("M_COLOR.%s = { %s, %s, %s, %s }" % (file_name, area_f, path_f, width_f, height_f))
        # print(all_f)
        return all_f


def output_M_COLOR_md5():
    create_dir(EXTRACT_M_COLOR_PATH)
    f = open(EXTRACT_M_COLOR_PATH, "w")
    f.write("M_COLOR = {}\n")
    for key, v in M_COLOR.items():
        result = turn_into_color_format(M_COLOR[key])
        f.write("M_COLOR.%s\n" % result)

    f.close()


def get_MD5(input_file):
    with open(input_file, 'rb') as file_obj:
        file_contents = file_obj.read()

    return hashlib.md5(file_contents).hexdigest()


def create_data_extract_file_MD5():
    for root, dir, files in os.walk(EXTRACT_ASSETS_PATH, topdown=False):
        for name in files:
            file_path = os.path.join(root, name)
            file_key_name = file_path.replace(EXTRACT_ASSETS_PATH, EMULATOR_ASSETS_PATH).replace("\\", "/")
            FILE_MD5[file_key_name] = get_MD5(file_path)

    file_MD5_json = json.dumps(FILE_MD5)
    f = open(EXTRACT_ASSETS_MD5_PATH, "w")
    f.write(file_MD5_json)
    f.close()


t0 = time.time()

if os.path.exists(EXTRACT_ASSETS_PATH):
    shutil.rmtree(EXTRACT_ASSETS_PATH)

# 删除多余、补足缺少图片
delete_duplicate(APP_SERVER[1])
complete_image(APP_SERVER[1])

# 开始crop、copy、create data
create_data_M_COLOR()

# 输出 M_COLOR.md5到指定路径
output_M_COLOR_md5()

# 输出 assets.md5到指定路径
create_data_extract_file_MD5()

print(f'Total time use : {time.time()-t0} seconds')

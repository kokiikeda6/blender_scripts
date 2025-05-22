from mathutils import Vector
import cv2
import numpy as np
import tempfile
import os
import subprocess
import math

### パラメータ ###
# 投影
IMAGE_SIZE = 1000
ANGLE = math.radians(45)
CENTER_X = 400
CENTER_Y = 400
RADIUS = 100

def judgment(point):
    x,y = point
    line1 = math.cos(ANGLE+math.pi/2)*(x - CENTER_X) + math.sin(ANGLE+math.pi/2)*(y - CENTER_Y) - RADIUS
    line2 = math.cos(ANGLE+math.pi/2)*(x - CENTER_X) + math.sin(ANGLE+math.pi/2)*(y - CENTER_Y) + RADIUS
    obst_point = Vector((x, y))
    center_point = Vector((CENTER_X, CENTER_Y))
    center_to_obst_vec = obst_point - center_point
    dir_vec = Vector((math.cos(ANGLE), math.sin(ANGLE)))
    limited_dir = center_to_obst_vec.dot(dir_vec)

    return line1 <= 0 and line2 >= 0 and (center_to_obst_vec).length > RADIUS and limited_dir > 0

def main():
    image = np.zeros((IMAGE_SIZE, IMAGE_SIZE), dtype=np.uint8)
    cv2.circle(image, (CENTER_X,CENTER_Y), RADIUS, 255)

    for x in range(1, IMAGE_SIZE, 10):
        for y in range (1, IMAGE_SIZE, 10):
            point = x,y
            if judgment(point):
                cv2.circle(image, point, 1, 255, -1)


    # 一時ファイルに画像を保存
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    cv2.imwrite(temp_file.name, image)
    print(f"2D projection image saved to {temp_file.name}")

    # 保存した画像を自動で開く
    os.startfile(temp_file.name)  # Windowsの場合。macOSやLinuxでは代わりに適切なビューアで開く
    # subprocess.run(["xdg-open", temp_file.name])  # Linuxの場合

main()
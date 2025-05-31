import bpy
import bmesh
from mathutils import Vector
import cv2
import numpy as np
import matplotlib.pyplot as plt
import tempfile
import os
import subprocess
import open3d

### パラメータ ###
# 投影
TOLERANCE = 0.005 # [m] 選択した点からどの高さまでの頂点を収集するか
DISTANCE_THRESHOLD = 0.05 # [m] 選択した点からどの距離までの頂点を収集するか
IMAGE_SIZE = 100
# ハフ変換
DP = 1.2
MIN_DIST = 10
PARAM1 = 50
PARAM2 = 30
MIN_RADIUS = 10
MAX_RADIUS = 25

def projection_to_image(bm, base_vertex, target_z, tolerance, distance_threshold, image_size):


    # 基準点のX-y座標
    base_point_2d = Vector((base_vertex.co.x, base_vertex.co.y))

    # 指定した高さにある頂点を収集し、基準点の近くのみに絞る
    vertices_near_base = []
    for v in bm.verts:
        if abs(v.co.z - target_z) < tolerance:
            point_2d = Vector((v.co.x, v.co.y))
            if (point_2d - base_point_2d).length < distance_threshold:
                vertices_near_base.append(v.co)
    
    if not vertices_near_base:
        print("No vertices found near the base point at the target height.")
        bm.free()
        return
    
    # 2D座標への投影（X-y平面）
    points_2d = [(int((v.x - base_vertex.co.x) / distance_threshold * image_size / 2 + image_size / 2), int((v.y - base_vertex.co.y) / distance_threshold * image_size / 2 + image_size / 2)) for v in vertices_near_base]

    # 空の画像を作成して、ポイントを描画
    image = np.zeros((image_size, image_size), dtype=np.uint8)
    for point in points_2d:
        cv2.circle(image, point, 3, 255, -1)
    image = cv2.flip(image, 1) # 画像反転

    return image

def center_point_estimation(image, base_vertex, dp, min_dist, param1, param2, min_radius, max_radius):
    # blur
    image = cv2.GaussianBlur(image, ksize=(9,9), sigmaX=0, sigmaY=0)
    
    # canny
    med_val = np.median(image)
    sigma = 0.33  # 0.33
    min_val = int(max(0, (1.0 - sigma) * med_val))
    max_val = int(max(255, (1.0 + sigma) * med_val))
    image = cv2.Canny(image, threshold1 = min_val, threshold2 = max_val)

    # ハフ変換で円を検出
    circles = cv2.HoughCircles(image, cv2.HOUGH_GRADIENT, dp=dp, minDist=min_dist, param1=param1, param2=param2, minRadius=min_radius, maxRadius=max_radius)
    
    if circles is not None:
        circles = np.uint16(np.around(circles))
        for i, circle in enumerate(circles[0, :]):
            center_x = circle[0]  # X座標をスケールに合わせて戻す
            center_y = circle[1]  # y座標をスケールに合わせて戻す
            radius = circle[2]    # 半径もスケールに合わせて戻す

            # ワールド座標系に変換
            world_center_x = (2*center_x - IMAGE_SIZE)*DISTANCE_THRESHOLD/IMAGE_SIZE + base_vertex.co.x
            world_center_y = (2*center_y - IMAGE_SIZE)*DISTANCE_THRESHOLD/IMAGE_SIZE + base_vertex.co.y
            world_radius = 2*radius*DISTANCE_THRESHOLD/IMAGE_SIZE
    else:
        print("No circles detected.")

    return [world_center_x, world_center_y, world_radius]

def obst_dist_measure(bm, world_cicle, target_z):

    center_x = world_cicle[0]
    center_y = world_cicle[1]
    radius = world_cicle[2]

    center_point_2d = Vector((center_x, center_y))

    # 指定した高さにある頂点を収集し、一方向のみに絞る
    vertices_left = []
    vertices_right = []
    vertices_front = []
    vertices_behind = []

    for v in bm.verts:
        if abs(v.co.z - target_z) < TOLERANCE: #高さ絞る
            point_2d = Vector((v.co.x, v.co.y))
            if (point_2d - center_point_2d).length > radius + 0.008: # 検知した円より外の点に絞る，0.01は要調整
                if v.co.x > center_x and v.co.y < center_y + radius and v.co.y > center_y - radius: # 円の左側に絞る
                    vertices_left.append(v.co)
                if v.co.x < center_x and v.co.y < center_y + radius and v.co.y > center_y - radius: # 円の右側に絞る
                    vertices_right.append(v.co)
                if v.co.y > center_y and v.co.x < center_x + radius and v.co.x > center_x - radius: # 円の前側に絞る
                    vertices_front.append(v.co)
                if v.co.y < center_y and v.co.x < center_x + radius and v.co.x > center_x - radius: # 円の後側に絞る
                    vertices_behind.append(v.co)
    
    # 最小の距離を求める
    if not vertices_left:
        left_obst_dist = None
    else:
        left_obst_dist = min([abs(center_x - v.x) for v in vertices_left])
    if not vertices_right:
        right_obst_dist = None
    else:
        right_obst_dist = min([abs(center_x - v.x) for v in vertices_right])
        print([abs(center_x - v.x) for v in vertices_right]) #debug
    if not vertices_front:
        front_obst_dist = None
    else:
        front_obst_dist = min([abs(center_y - v.y) for v in vertices_front])
    if not vertices_behind:
        behind_obst_dist = None
    else:
        behind_obst_dist = min([abs(center_y - v.y) for v in vertices_behind])
    # [print(v.x) for v in vertices_right] #debug
    # [print(v.y) for v in vertices_front] #debug
    # print(len(vertices_right)) #debug
    # print(len(vertices_front)) #debug
    return [left_obst_dist, right_obst_dist, front_obst_dist, behind_obst_dist]

def main():

    obj = bpy.context.object
    if obj is None or obj.type != 'MESH':
        print("No mesh object selected.")
        return

    # メッシュデータの準備
    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    
    # 選択された頂点のz座標を取得
    selected_vertices = [v for v in bm.verts if v.select]
    if not selected_vertices:
        print("No vertices selected.")
        bm.free()
        return

    # 最初の選択頂点を基準点とする
    base_vertex = selected_vertices[0]
    target_z = base_vertex.co.z

    center_image = projection_to_image(bm, base_vertex, target_z, tolerance=TOLERANCE, distance_threshold=DISTANCE_THRESHOLD, image_size=IMAGE_SIZE)
    world_circle = center_point_estimation(center_image, base_vertex, dp=DP, min_dist=MIN_DIST, param1=PARAM1, param2=PARAM2, min_radius=MIN_RADIUS, max_radius=MAX_RADIUS)
    image = projection_to_image(bm, base_vertex, target_z, tolerance=TOLERANCE, distance_threshold=0.5, image_size=1000)
    obst_dist = obst_dist_measure(bm, world_circle, target_z)

    cv2.putText(image, f"x= {world_circle[0]}, y= {world_circle[1]}, r= {world_circle[2]}", (0, 90), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255,255,255))
    cv2.putText(image, f"left_obst_dist= {obst_dist[0]}", (0, 140), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255,255,255))
    cv2.putText(image, f"right_obst_dist= {obst_dist[1]}", (0, 190), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255,255,255))
    cv2.putText(image, f"front_obst_dist= {obst_dist[2]}", (0, 240), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255,255,255))
    cv2.putText(image, f"behind_obst_dist= {obst_dist[3]}", (0, 290), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255,255,255))


    # 一時ファイルに画像を保存
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    cv2.imwrite(temp_file.name, image)
    print(f"2D projection image saved to {temp_file.name}")

    # メッシュデータの解放
    bm.free()

    # 保存した画像を自動で開く
    os.startfile(temp_file.name)  # Windowsの場合。macOSやLinuxでは代わりに適切なビューアで開く
    # subprocess.run(["xdg-open", temp_file.name])  # Linuxの場合

# スクリプトを実行
main()
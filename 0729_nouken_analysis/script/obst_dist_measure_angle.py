import bpy
import bmesh
from mathutils import Vector
import cv2
import numpy as np
import tempfile
import os
import subprocess #linuxで実行する用
import math

### パラメータ ###
# 投影
TOLERANCE = 0.01 # [m] 選択した点からどの高さまでの頂点を収集するか
DISTANCE_THRESHOLD = 0.05 # [m] 選択した点からどの距離までの頂点を収集するか
IMAGE_SIZE = 100
POINT_SIZE = 2 # [pixel] 投影する点のサイズ
# ハフ変換
DP = 1.2
MIN_DIST = 15
PARAM1 = 50
PARAM2 = 30
MIN_RADIUS = 10
MAX_RADIUS = 25


# 障害物距離計算
CORRECT_PARAM = 0.008 # 円の半径補正 (収穫物自身を障害物として検出することを防ぐ)
APPROACH_ANGLE = 90 # [degree] アプローチする角度 x,yのワールド座標系

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
        cv2.circle(image, point, POINT_SIZE, 255, -1)
        
    # モデルにより調整
    image = cv2.flip(image, 1) # 画像反転
    image = cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE) # 画像を反時計回りに90°回転

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
        return None

    return [world_center_x, world_center_y, world_radius, center_x, center_y, radius]

def point_between_lines_judgment(point, circle, angle): # 指定した角度の方向にある点のみ抽出
    x,y = point
    center_x = circle[0]
    center_y = circle[1]
    radius = circle[2]

    line1 = math.cos(angle+math.pi/2)*(x - center_x) + math.sin(angle+math.pi/2)*(y - center_y) - radius
    line2 = math.cos(angle+math.pi/2)*(x - center_x) + math.sin(angle+math.pi/2)*(y - center_y) + radius

    obst_point = Vector((x, y))
    center_point = Vector((center_x, center_y))
    center_to_obst_vec = obst_point - center_point
    dir_vec = Vector((math.cos(angle), math.sin(angle)))
    limited_dir = center_to_obst_vec.dot(dir_vec)

    return line1 <= 0 and line2 >= 0 and limited_dir > 0

def min_dist(vertices, circle, angle):
    min_distance = None

    center_x = circle[0]
    center_y = circle[1]

    dir_vec = Vector((math.cos(angle), math.sin(angle)))
    for v in vertices:
        vec = Vector((v.x - center_x, v.y - center_y))
        obst_distance = (vec.project(dir_vec)).length
        if min_distance is None or obst_distance < min_distance:
            min_distance = obst_distance

    return min_distance

def obst_dist_measure(bm, world_circle, target_z, approach_angle):

    center_x = world_circle[0]
    center_y = world_circle[1]
    radius = world_circle[2]

    center_point_2d = Vector((center_x, center_y))

    # 指定した高さにある頂点を収集し、一方向のみに絞る
    vertices_left = []
    vertices_right = []
    vertices_front = []
    vertices_behind = []

    for v in bm.verts:
        if abs(v.co.z - target_z) < TOLERANCE: #高さ絞る
            point_2d = Vector((v.co.x, v.co.y))
            corrected_radius = radius + CORRECT_PARAM
            if (point_2d - center_point_2d).length > corrected_radius: # 検知した円より外の点に絞る，0.01は要調整
                if point_between_lines_judgment(point=[v.co.x, v.co.y], circle=world_circle, angle=approach_angle): # 円の手前側に絞る
                    vertices_front.append(v.co)
                if point_between_lines_judgment(point=[v.co.x, v.co.y], circle=world_circle, angle=approach_angle-math.pi/2): # 円の左側に絞る
                    vertices_left.append(v.co)
                if point_between_lines_judgment(point=[v.co.x, v.co.y], circle=world_circle, angle=approach_angle+math.pi): # 円の奥側に絞る
                    vertices_behind.append(v.co)
                if point_between_lines_judgment(point=[v.co.x, v.co.y], circle=world_circle, angle=approach_angle+math.pi/2): # 円の右側に絞る
                    vertices_right.append(v.co)
    
    # 最小の距離を求める
    front_obst_dist = min_dist(vertices_front, world_circle, approach_angle)
    left_obst_dist = min_dist(vertices_left, world_circle, approach_angle-math.pi/2)
    behind_obst_dist = min_dist(vertices_behind, world_circle, approach_angle+math.pi)
    right_obst_dist = min_dist(vertices_right, world_circle, approach_angle+math.pi/2)


    # [print(f"front point: ({v.x}, {v.y})") for v in vertices_front] #debug
    # [print(f"right point: ({v.x}, {v.y})") for v in vertices_right] #debug
    # [print(f"left point: ({v.x}, {v.y})") for v in vertices_left] #debug
    # [print(f"behind point: ({v.x}, {v.y})") for v in vertices_behind] #debug

    # print(len(vertices_right)) #debug
    # print(len(vertices_front)) #debug
    # print(len(vertices_behind)) #debug

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
    if world_circle is None:
        bm.free()
        return
    image = projection_to_image(bm, base_vertex, target_z, tolerance=TOLERANCE, distance_threshold=0.5, image_size=1000)
    obst_dist = obst_dist_measure(bm, world_circle, target_z, approach_angle=math.radians(APPROACH_ANGLE))
    
    # [m] から [mm] に変換
    obst_dist_mm = [d * 1000 for d in obst_dist]
    print(world_circle)
    world_circle_mm = [d * 1000 for d in world_circle]
    print(world_circle)

    cv2.putText(image, f"x= {world_circle[0]}, y= {world_circle[1]}, r= {world_circle[2]}", (0, 90), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255,255,255))
    cv2.putText(image, f"left_obst_dist= {obst_dist[0]}", (0, 140), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255,255,255))
    cv2.putText(image, f"right_obst_dist= {obst_dist[1]}", (0, 190), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255,255,255))
    cv2.putText(image, f"front_obst_dist= {obst_dist[2]}", (0, 240), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255,255,255))
    cv2.putText(image, f"behind_obst_dist= {obst_dist[3]}", (0, 290), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255,255,255))

    print(f"x= {world_circle_mm[0]} [mm], y= {world_circle_mm[1]} [mm], r= {world_circle_mm[2]} [mm]")
    print(f"left_obst_dist= {obst_dist_mm[0]} [mm]")
    print(f"right_obst_dist= {obst_dist_mm[1]} [mm]")
    print(f"front_obst_dist= {obst_dist_mm[2]} [mm]")
    print(f"behind_obst_dist= {obst_dist_mm[3]} [mm]")

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
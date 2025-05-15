import bpy
import bmesh
from mathutils import Vector
import cv2
import numpy as np
import matplotlib.pyplot as plt
import tempfile
import os
import subprocess

### パラメータ ###
# 投影
TOLERANCE = 0.005 # [m] 選択した点からどの高さまでの頂点を収集するか
DISTANCE_THRESHOLD = 0.5 # [m] 選択した点からどの距離までの頂点を収集するか
IMAGE_SIZE = 1000
# ハフ変換
DP = 1.2
MIN_DIST = 10
PARAM1 = 50
PARAM2 = 30
MIN_RADIUS = 10
MAX_RADIUS = 25

def extract_circles_near_point_with_hough_transform(tolerance=10, distance_threshold=100, image_size=500, dp=1.2, min_dist=20, param1=50, param2=30, min_radius=10, max_radius=100):
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
            world_center = obj.matrix_world @ Vector((center_x, center_y, target_z))
            world_radius = radius * obj.matrix_world.to_scale()[0]  # スケールを適用

            print(f"Detected Circle {i + 1}: Center = {world_center}, Radius = {world_radius}")
            print("circle: "+str(circle))
            cv2.circle(image, [center_x, center_y], radius, 255, thickness=2)
#            cv2.circle(image, [center_x, center_y], radius, 255, -1)
    else:
        print("No circles detected.")

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
extract_circles_near_point_with_hough_transform(tolerance=TOLERANCE, distance_threshold=DISTANCE_THRESHOLD, image_size=IMAGE_SIZE, dp=DP, min_dist=MIN_DIST, param1=PARAM1, param2=PARAM2, min_radius=MIN_DIST, max_radius=MAX_RADIUS)
import bpy
import bmesh
from mathutils import Vector
import cv2
import numpy as np
import tempfile
import os
import subprocess

def ellipse_detector(tolerance, distance_threshold, image_size):
    obj = bpy.context.object
    if obj is None or obj.type != 'MESH':
        print("No mesh object selected.")
        return
    
    # メッシュデータの準備
    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    
    # 選択された頂点のY座標を取得
    selected_vertices = [v for v in bm.verts if v.select]
    number_of_points = len(selected_vertices)
    if not selected_vertices:
        print("No vertices selected.")
        bm.free()
        return

    # 隣接する点のみにする
     # 再帰的に訪問するためのキュー
    to_visit = list(selected_vertices)
    visited = set(selected_vertices)

     # 再帰的にすべての隣接点を訪問
    while to_visit:
        current_vert = to_visit.pop()
        for edge in current_vert.link_edges:
            linked_vert = edge.other_vert(current_vert)
            if linked_vert not in visited:
                visited.add(linked_vert)
                to_visit.append(linked_vert)

    # 最初の選択頂点を基準点とする
    base_vertex = selected_vertices[0]
    target_y = base_vertex.co.y

    # 基準点のX-Z座標
    base_point_2d = Vector((base_vertex.co.x, base_vertex.co.z))

    # 指定した高さにある頂点を収集し、基準点の近くのみに絞る
    vertices_near_base = []
    for v in visited:
        if abs(v.co.y - target_y) < tolerance:
            point_2d = Vector((v.co.x, v.co.z))
            if (point_2d - base_point_2d).length < distance_threshold:
                vertices_near_base.append(v.co)


    # 最初の選択頂点を基準点とする
    base_vertex = selected_vertices[0]    

    # 2D座標への投影（X-Z平面）
    points_2d = [(int((v.x - base_vertex.co.x) / distance_threshold * image_size / 2 + image_size / 2), \
                  int((v.z - base_vertex.co.z) / distance_threshold * image_size / 2 + image_size / 2)) for v in vertices_near_base]

    # 空の画像を作成して、ポイントを描画
    image = np.zeros((image_size, image_size), dtype=np.uint8)
    for point in points_2d:
        cv2.circle(image, point, 1, 255, -1)

    # blur
    image = cv2.GaussianBlur(image, ksize=(9,9), sigmaX=0, sigmaY=0)

    # 楕円フィッティング
    contours,hierarchy =  cv2.findContours(image,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contours:
        ellipse = cv2.fitEllipse(cnt)
        print(ellipse)

        cx = int(ellipse[0][0])
        cy = int(ellipse[0][1])

        # 楕円描画
        image = cv2.ellipse(image,ellipse,(255,0,0),2)
        cv2.drawMarker(image, (cx,cy), (255), markerType=cv2.MARKER_CROSS, markerSize=10, thickness=1)

    # image 回転
    image = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)

    # 一時ファイルに画像を保存
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    cv2.imwrite(temp_file.name, image)
    print(f"2D projection image saved to {temp_file.name}")

    # メッシュデータの解放
    bm.free()

    # 保存した画像を自動で開く
    subprocess.run(["xdg-open", temp_file.name])  # Linuxの場合

ellipse_detector(tolerance=5, \
                 distance_threshold=100, \
                 image_size=500)
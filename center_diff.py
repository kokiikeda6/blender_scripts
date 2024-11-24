import bpy
import bmesh
from mathutils import Vector
import cv2
import numpy as np
import tempfile
# import os
import subprocess
import math

def distance(point1, point2):
    (x1, y1) = point1
    (x2, y2) = point2
    dist = math.sqrt((x1 - x2)**2 + (y1 - y2)**2)
    return(dist)

def CircleFitting(x,y):
    sumx  = sum(x)
    sumy  = sum(y)
    sumx2 = sum([ix ** 2 for ix in x])
    sumy2 = sum([iy ** 2 for iy in y])
    sumxy = sum([ix * iy for (ix,iy) in zip(x,y)])

    F = np.array([[sumx2,sumxy,sumx],
                  [sumxy,sumy2,sumy],
                  [sumx,sumy,len(x)]])

    G = np.array([[-sum([ix ** 3 + ix*iy **2 for (ix,iy) in zip(x,y)])],
                  [-sum([ix ** 2 *iy + iy **3 for (ix,iy) in zip(x,y)])],
                  [-sum([ix ** 2 + iy **2 for (ix,iy) in zip(x,y)])]])

    T=np.linalg.inv(F).dot(G)

    cxe=float(T[0]/-2)
    cye=float(T[1]/-2)
    re=math.sqrt(cxe**2+cye**2-T[2])
    #print (cxe,cye,re)
    return (cxe,cye,re)

def line_detector(tolerance, distance_threshold, image_size):
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

    # 花柄の点
    peduncle_vertex = selected_vertices[1]
    points_2d.extend([(int((peduncle_vertex.co.x - base_vertex.co.x) / distance_threshold * image_size / 2 + image_size / 2), \
                       int((peduncle_vertex.co.z - base_vertex.co.z) / distance_threshold * image_size / 2 + image_size / 2))])

    # 空の画像を作成して、ポイントを描画
    image = np.zeros((image_size, image_size), dtype=np.uint8)
    for point in points_2d:
        cv2.circle(image, point, 1, 255, -1)

    # 円のフィッティング
    points_x = [x for x, y in points_2d]
    points_y = [y for x, y in points_2d]
    (cx,cy,r) = CircleFitting(points_x, points_y)
    print("cx =", cx, "cy =", cy, "r =", r)

    # 花柄の点とフィッティングした円の中心点の距離を計算
    print(type(points_2d[-1]))
    print(type((cx, cy)))
    dist = distance(points_2d[-1], (cx, cy))
    print("diffarence: ", dist)

    # 円描画
    image = cv2.circle(image, [int(cx), int(cy)], int(r), 255, thickness=1)
    cv2.drawMarker(image, (int(cx),int(cy)), (255), markerType=cv2.MARKER_CROSS, markerSize=10, thickness=1)
#    cv2.drawMarker(image, points_2d[-1], (255), markerType=cv2.MARKER_TILTED_CROSS, markerSize=5, thickness=1)

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

line_detector(tolerance=5, \
              distance_threshold=100, \
              image_size=500)
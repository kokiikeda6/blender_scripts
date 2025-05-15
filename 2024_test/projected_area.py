import bpy
import bmesh
from shapely.geometry import Polygon

def projected_area():
    obj = bpy.context.object
    if obj is None or obj.type != 'MESH':
        print("No mesh object selected.")
        return

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(obj.data)

    # メッシュデータの準備
    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)

    # 選択された頂点の座標を取得. 選択順を取得するために, bmeshのヒストリーを使用
    selected_vertices = []
    for elem in reversed(bm.select_history):  # select_historyは選択順が記録されている
        if isinstance(elem, bmesh.types.BMVert):  # 頂点だけをチェック
            selected_vertices.append(elem.co)

    if len(selected_vertices) <= 2:
        print("Please select 3 or more points.")
        bm.free()
        return

    # 多角形の座標点
    points = []
    for i in range(len(selected_vertices)):
        points.extend([(selected_vertices[i].y, selected_vertices[i].z)])

    #print(points)

    # Polygonオブジェクトを作成
    polygon = Polygon(points)

    # 面積を計算
    area = polygon.area

    print("area:", area, "[mm^2]")

projected_area()
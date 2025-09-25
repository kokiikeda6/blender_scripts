import bpy
import bmesh
import math
from mathutils import Vector


ANGLE = 0 # Y軸上距離：0[deg]，X軸上距離：90[deg]

def points_distance():
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
    
    # 選択された頂点のY座標を取得
    selected_vertices = [v for v in bm.verts if v.select]
    if not len(selected_vertices) == 2:
        print("Please select two points.")
        bm.free()
        return
    
    # 距離計算
    angle =math.radians(ANGLE + 90)
    dir_vec = Vector((math.cos(angle), math.sin(angle)))
    vec = Vector((selected_vertices[0].co.x - selected_vertices[1].co.x, selected_vertices[0].co.y - selected_vertices[1].co.y))
    distance = (vec.project(dir_vec)).length
#    distance = abs(selected_vertices[0].co.z - selected_vertices[1].co.z) # Z軸方向を計測する場合はコメントアウト外す


    distance_mm = distance*1000

    print("distance:", distance_mm, "[mm]")


points_distance()
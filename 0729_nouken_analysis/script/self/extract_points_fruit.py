import bpy
import bmesh
import math
from mathutils import Vector

ANGLE = 0

def keep_vertices_at_same_height():
    obj = bpy.context.object
    if obj is None or obj.type != 'MESH':
        print("No mesh object selected.")
        return

    bpy.ops.object.mode_set(mode='OBJECT')

    # メッシュデータの準備
    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    
    # 選択された頂点のx座標を取得
    selected_vertices = [v for v in bm.verts if v.select]
    if not selected_vertices:
        print("No vertices selected.")
        bm.free()
        return

    # 最初の選択頂点を基準にする

    angle =math.radians(ANGLE + 90)
    dir_vec = Vector((math.cos(angle), math.sin(angle)))
    vec = Vector((selected_vertices[0].co.x - v.co.x, selected_vertices[0].co.y - v.co.y))

    # 選択した点より後ろの点削除
    for v in bm.verts:
        if target_x - 0.03 >= v.co.x:
            bm.verts.remove(v)

    # メッシュの更新と選択反映
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    
    print(f"Vertices at height {target_x} kept, others deleted.")

# スクリプトを実行
keep_vertices_at_same_height()

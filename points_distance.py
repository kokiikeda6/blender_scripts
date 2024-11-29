import bpy
import bmesh

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
    
    distance = abs(selected_vertices[0].co.y - selected_vertices[1].co.y)
    print("distance:", distance, "[mm]")


points_distance()
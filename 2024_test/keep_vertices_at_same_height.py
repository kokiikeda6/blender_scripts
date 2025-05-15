import bpy
import bmesh

def keep_vertices_at_same_height(tolerance=0.001):
    obj = bpy.context.object
    if obj is None or obj.type != 'MESH':
        print("No mesh object selected.")
        return

    # メッシュデータの準備
    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    
    # 選択された頂点のZ座標を取得
    selected_vertices = [v for v in bm.verts if v.select]
    if not selected_vertices:
        print("No vertices selected.")
        bm.free()
        return

    # 最初の選択頂点のZ座標を基準にする
    target_z = selected_vertices[0].co.z

    # 同じ高さにない頂点を削除対象にする
    for v in bm.verts:
        if abs(v.co.z - target_z) >= tolerance:
            bm.verts.remove(v)

    # メッシュの更新と選択反映
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    
    print(f"Vertices at height {target_z} kept, others deleted.")

# スクリプトを実行
keep_vertices_at_same_height(tolerance=10)

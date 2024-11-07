import bpy
import bmesh

def select_vertices_at_same_height(tolerance=10):
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

    # すべての頂点を確認し、同じ高さの頂点を選択
    for v in bm.verts:
        if abs(v.co.z - target_z) < tolerance:
            v.select = True

    # メッシュの更新と選択反映
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    
    print(f"Vertices at height {target_z} selected.")

# スクリプトを実行
select_vertices_at_same_height(tolerance=10)
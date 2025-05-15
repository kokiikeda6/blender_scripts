import bpy
import bmesh   # 追加でインポートが必要

obj = bpy.context.active_object

bpy.ops.object.mode_set(mode='EDIT')  # 処理はEDITモードで行う必要がある
bm = bmesh.from_edit_mesh(obj.data)

# blenderのバージョンが2.73以上の時に必要
if bpy.app.version[0] >= 2 and bpy.app.version[1] >= 73:
    bm.verts.ensure_lookup_table()

# 頂点の選択順序を表示
for e in bm.select_history:
    if isinstance(e, bmesh.types.BMVert) and e.select:
        print(repr(e))

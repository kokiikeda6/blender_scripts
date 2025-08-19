import bpy
import bmesh
import sys
sys.path.append("c:\users\hikou\appdata\roaming\python\python311\site-packages")
import open3d as o3d
import numpy as np
import tempfile
import os

def get_selected_vertex_world_coords():
    obj = bpy.context.object
    if obj is None or obj.type != 'MESH':
        raise Exception("メッシュオブジェクトを選択してください。")

    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(obj.data)
    coords = [obj.matrix_world @ v.co for v in bm.verts if v.select]
    bpy.ops.object.mode_set(mode='OBJECT')

    return np.array([[v.x, v.y, v.z] for v in coords])

# Blenderで選択された頂点の座標を取得
points = get_selected_vertex_world_coords()

# 一時ファイルに保存
with tempfile.NamedTemporaryFile(delete=False, suffix=".npy") as tmp_file:
    np.save(tmp_file, points)
    tmp_path = tmp_file.name  # 一時ファイルのパスを保存

# 一時ファイルから読み込む
loaded_points = np.load(tmp_path)

# Open3Dで表示
pcd = o3d.geometry.PointCloud()
pcd.points = o3d.utility.Vector3dVector(loaded_points)
o3d.visualization.draw_geometries([pcd])

# 一時ファイルを削除（必要に応じて）
os.remove(tmp_path)

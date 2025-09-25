import bpy
import bmesh
import math
from mathutils import Vector


ANGLE = 0 # Y軸上距離：0[deg]，X軸上距離：90[deg]
CAMERA_REVERSE_MODE = False # True: 選択した点を中心に視点反転

def main():
    select_blender_mode(select_mode="object")

    # メッシュデータの準備
    obj = bpy.context.object
    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    
    # 選択された頂点のY座標を取得
    selected_vertices = [v for v in bm.verts if v.select]
    
    if CAMERA_REVERSE_MODE:
        camera_reverse(selected_vertices)
        select_blender_mode(select_mode="edit")
        bm.free()
        return
    
    if not len(selected_vertices) == 2:
        print("Please select two points.")
        select_blender_mode(select_mode="edit")
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
    select_blender_mode(select_mode="edit")

def select_blender_mode(select_mode):
    # メッシュタイプのオブジェクトのみ選択
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            obj.select_set(True)
        else:
            obj.select_set(False)

    # 選択されたすべてのオブジェクトをアクティブにする
    bpy.context.view_layer.objects.active = bpy.context.selected_objects[0]

    # モード切り替え
    match select_mode:
        case "edit":
            bpy.ops.object.mode_set(mode='EDIT')
        case "object":
            bpy.ops.object.mode_set(mode='OBJECT')
        case _:
            print("error: そのモードは存在しません.")
    return

def camera_reverse(selected_vertices):
    # アクティブなカメラオブジェクトを取得
    camera_object = bpy.context.scene.camera
    if not camera_object:
        print("error: シーンにカメラはありません．")
        return

    if selected_vertices:
        center_point = selected_vertices[0].co
    else:
        print("error: 回転中心を選択してください．カメラを回転できません．")

    # 現在のカメラの位置
    cam_location = camera_object.location
    
    # 回転中心から現在のカメラ位置へのベクトル
    vec_to_cam = cam_location - center_point
    
    # ベクトルを180度回転
    new_cam_location = center_point - vec_to_cam
        
    # カメラの位置を更新
    camera_object.location = new_cam_location
    
    # カメラが常に回転中心を向くように設定
    # 新しいカメラ位置から回転中心への方向ベクトル
    direction = center_point - new_cam_location
    
    # Blenderのカメラは-Z軸が前方、Y軸が上方を向くのが標準
    rot_quat = direction.to_track_quat('-Z', 'Y')
    
    # カメラの回転（クォータニオン）をオイラー角に変換して適用
    camera_object.rotation_euler = rot_quat.to_euler()

    return

main()
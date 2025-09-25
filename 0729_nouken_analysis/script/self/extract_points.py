import bpy
import bmesh
import math
from mathutils import Vector

ANGLE = 0 # カメラ視点（ヨー方向） [degree]
DISTANCE = 0.5 #選択点からカメラまでの距離 [m]
SCRIPT_PATH = "c:/Users/hikou/OneDrive/ドキュメント/Blender/blender_scripts/0729_nouken_analysis/script/self/points_distance.py" #実行後に開くスクリプトのパス

def main():

    mode_select(select_mode="object")

    # メッシュデータの準備
    obj = bpy.context.object
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
    target_x = selected_vertices[0].co.x
    target_y = selected_vertices[0].co.y

    angle =math.radians(ANGLE)
    dir_vec = Vector((math.cos(angle), math.sin(angle)))

    # 選択した点より後ろの点削除
    for v in bm.verts:
        vec = Vector((target_x - v.co.x, target_y - v.co.y))
        distance = (vec.project(dir_vec)).length
        if distance >= 0.035 and vec.project(dir_vec).dot(dir_vec) > 0:
            bm.verts.remove(v)

    # カメラを生成
    set_camera(selected_vertices)

    # メッシュの更新と選択反映
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    print("Vertices deleted.")

    # スクリプトを開く
    open_script(script_path=SCRIPT_PATH)
    mode_select(select_mode="edit")

def set_camera(selected_vertices):
    # カメラを作成
    camera_data = bpy.data.cameras.new(name="Target_Camera")
    camera_object = bpy.data.objects.new("Target_Camera", camera_data)
    bpy.context.collection.objects.link(camera_object)

    center_world = selected_vertices[0].co

    # ターゲットオブジェクトを作成してカメラの注視点にする
    bpy.ops.object.empty_add(type='PLAIN_AXES')
    target_object = bpy.context.active_object
    target_object.location = center_world
    target_object.name = "Camera_Target"

    # カメラをターゲットの方向に向けるためのコンストレイントを追加
    track_to = camera_object.constraints.new(type='TRACK_TO')
    track_to.target = target_object
    track_to.track_axis = 'TRACK_NEGATIVE_Z'
    track_to.up_axis = 'UP_Y'

    # 角度をラジアンに変換
    angle_rad = math.radians(ANGLE)
    
    # カメラの位置を計算
    # X座標は0、Y座標は角度、Z座標は距離で計算
    x_pos = DISTANCE * math.cos(angle_rad)
    y_pos = DISTANCE * math.sin(angle_rad)
    z_pos = 0
    
    camera_object.location = center_world + Vector((x_pos, y_pos, z_pos))

    # シーンの現在のカメラを新しく作成したカメラに設定
    bpy.context.scene.camera = camera_object

    # 3Dビューのエリアを見つける
    area = next((a for a in bpy.context.screen.areas if a.type == 'VIEW_3D'), None)
    if area:
        # 3Dビューのスペースデータを取得
        space_data = area.spaces.active  
        # カメラをアクティブなビューの視点に設定
        space_data.region_3d.view_perspective = 'CAMERA'
    else:
        print("エラー: 3Dビューが見つかりません。")
    return

def open_script(script_path):
    bpy.ops.text.open(filepath=script_path)
    return

def mode_select(select_mode):
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
            print("そのモードは存在しません.")
    return

# スクリプトを実行
main()

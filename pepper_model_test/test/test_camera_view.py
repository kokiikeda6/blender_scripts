import bpy

# 現在アクティブなシーンを取得
scene = bpy.context.scene

# シーンのカメラを取得
camera = scene.camera

# カメラが存在するか確認
if camera:
    # 3Dビューのエリアを見つける
    area = next((a for a in bpy.context.screen.areas if a.type == 'VIEW_3D'), None)
    
    if area:
        # 3Dビューのスペースデータを取得
        space_data = area.spaces.active
        
        # カメラをアクティブなビューの視点に設定
        space_data.region_3d.view_perspective = 'CAMERA'
    else:
        print("エラー: 3Dビューが見つかりません。")
else:
    print("エラー: シーンにカメラが設定されていません。")
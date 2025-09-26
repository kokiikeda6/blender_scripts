import bpy
import bmesh

# --- 設定 ---
# この数以下のポリゴン数で構成される、リンクしたメッシュの塊を削除します
THRESHOLD = 20 
# --- 設定ここまで ---


def remove_small_islands():
    """
    選択中のオブジェクトから、指定したポリゴン数以下の
    メッシュアイランドを削除する
    """
    
    # オブジェクトモードであることを確認
    if bpy.context.object.mode == 'EDIT':
        bpy.ops.object.mode_set(mode='OBJECT')

    # アクティブなオブジェクトを取得
    obj = bpy.context.active_object
    if obj is None or obj.type != 'MESH':
        print("メッシュオブジェクトを選択してください。")
        return

    # BMeshを作成してメッシュデータを取得
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()

    # すべての面を「未訪問」としてセットアップ
    unvisited_faces = set(bm.faces)
    faces_to_delete = []

    # 未訪問の面がなくなるまでループ
    while unvisited_faces:
        # ランダムに開始面を取得
        start_face = unvisited_faces.pop()
        
        # 連結している面のグループ（アイランド）を探す
        island = {start_face}
        # これからチェックする面のリスト
        faces_to_check = [start_face]
        
        while faces_to_check:
            current_face = faces_to_check.pop()
            
            # 現在の面にリンクしているすべての面をループ
            for edge in current_face.edges:
                for linked_face in edge.link_faces:
                    # まだ訪問しておらず、アイランドにも含まれていない面なら追加
                    if linked_face in unvisited_faces and linked_face not in island:
                        unvisited_faces.remove(linked_face)
                        island.add(linked_face)
                        faces_to_check.append(linked_face)
        
        # 見つかったアイランドのポリゴン数がしきい値以下かチェック
        if len(island) <= THRESHOLD:
            # 削除リストに追加
            faces_to_delete.extend(list(island))

    if faces_to_delete:
        print(f"{len(faces_to_delete)} 個の面を削除します...")
        # BMeshで面を削除
        bmesh.ops.delete(bm, geom=faces_to_delete, context='FACES')
        
        # メッシュデータを更新
        bm.to_mesh(obj.data)
        obj.data.update()
        print("削除が完了しました。")
    else:
        print("削除対象の面は見つかりませんでした。")
        
    # BMeshを解放
    bm.free()
    
    # 編集モードに戻る
    bpy.ops.object.mode_set(mode='EDIT')

# スクリプトを実行
remove_small_islands()
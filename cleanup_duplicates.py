"""
清理資料庫中的重複文法資料

此腳本會：
1. 備份現有資料庫
2. 找出所有重複的文法項目
3. 保留每組重複中最早的一筆，刪除其他重複項
4. 更新 user_progress 外鍵引用
"""

import sqlite3
import shutil
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "knowledge_base.db")
BACKUP_PATH = os.path.join(os.path.dirname(__file__), f"knowledge_base_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")

def backup_database():
    """備份資料庫"""
    if os.path.exists(DB_PATH):
        shutil.copy2(DB_PATH, BACKUP_PATH)
        print(f"✅ 資料庫已備份至: {BACKUP_PATH}")
        return True
    else:
        print("❌ 找不到資料庫檔案")
        return False

def cleanup_duplicates():
    """清理重複的文法項目"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 找出所有重複的文法項目（根據 jlpt_level + grammar_concept）
    cursor.execute('''
        SELECT jlpt_level, grammar_concept, COUNT(*) as count
        FROM grammar_points
        GROUP BY jlpt_level, grammar_concept
        HAVING COUNT(*) > 1
    ''')
    
    duplicates = cursor.fetchall()
    
    if not duplicates:
        print("✅ 沒有發現重複資料！")
        conn.close()
        return
    
    print(f"🔍 發現 {len(duplicates)} 組重複資料")
    
    total_deleted = 0
    
    for level, concept, count in duplicates:
        print(f"\n處理: {level} - {concept} (重複 {count} 次)")
        
        # 找出這組重複中的所有 ID（按創建時間排序，保留最早的）
        cursor.execute('''
            SELECT id FROM grammar_points
            WHERE jlpt_level = ? AND grammar_concept = ?
            ORDER BY created_at ASC
        ''', (level, concept))
        
        ids = [row[0] for row in cursor.fetchall()]
        keep_id = ids[0]  # 保留第一筆（最早的）
        delete_ids = ids[1:]  # 刪除其他重複項
        
        print(f"  保留 ID: {keep_id}")
        print(f"  刪除 ID: {delete_ids}")
        
        # 更新 user_progress 中的外鍵引用
        for delete_id in delete_ids:
            cursor.execute('''
                UPDATE user_progress
                SET grammar_id = ?
                WHERE grammar_id = ?
            ''', (keep_id, delete_id))
        
        # 刪除重複的 grammar_points
        cursor.execute('''
            DELETE FROM grammar_points
            WHERE id IN ({})
        '''.format(','.join('?' * len(delete_ids))), delete_ids)
        
        total_deleted += len(delete_ids)
    
    conn.commit()
    
    # 驗證結果
    cursor.execute('SELECT COUNT(*) FROM grammar_points')
    final_count = cursor.fetchone()[0]
    
    print(f"\n✅ 清理完成！")
    print(f"   刪除了 {total_deleted} 筆重複資料")
    print(f"   資料庫目前有 {final_count} 筆文法資料")
    
    conn.close()

def main():
    print("=" * 60)
    print("文法庫重複資料清理工具")
    print("=" * 60)
    
    # 備份資料庫
    if not backup_database():
        return
    
    # 清理重複資料
    cleanup_duplicates()
    
    print("\n" + "=" * 60)
    print("處理完成！")
    print("=" * 60)

if __name__ == "__main__":
    main()

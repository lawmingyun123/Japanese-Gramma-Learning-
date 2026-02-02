"""
測試資料庫架構更新

此腳本會重建資料庫以應用新的 UNIQUE 約束。
注意：這會刪除現有資料庫並重新創建！僅用於測試。
"""

import os
import shutil
from datetime import datetime
from database_manager import DatabaseManager

DB_PATH = os.path.join(os.path.dirname(__file__), "knowledge_base.db")
BACKUP_PATH = os.path.join(os.path.dirname(__file__), f"knowledge_base_before_rebuild_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")

def rebuild_database():
    """重建資料庫以應用新的架構"""
    
    print("=" * 60)
    print("資料庫架構更新工具")
    print("=" * 60)
    
    # 備份現有資料庫
    if os.path.exists(DB_PATH):
        shutil.copy2(DB_PATH, BACKUP_PATH)
        print(f"\n✅ 已備份現有資料庫至: {BACKUP_PATH}")
        
        # 刪除舊資料庫
        os.remove(DB_PATH)
        print(f"🗑️  已刪除舊資料庫")
    else:
        print("\n⚠️  沒有找到現有資料庫")
    
    # 創建新資料庫（會使用新的架構）
    print("\n🔨 正在創建新資料庫...")
    db = DatabaseManager()
    
    print("✅ 新資料庫已創建，包含 UNIQUE 約束")
    print("\n" + "=" * 60)
    print("完成！現在可以重新導入資料。")
    print("=" * 60)

if __name__ == "__main__":
    rebuild_database()

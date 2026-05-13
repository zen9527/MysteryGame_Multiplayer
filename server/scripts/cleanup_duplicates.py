#!/usr/bin/env python3
"""
Script to detect and clean up duplicate scripts in the database.
Run: python server/scripts/cleanup_duplicates.py
       python server/scripts/cleanup_duplicates.py --non-interactive
"""

import sqlite3
import json
import sys
import argparse
from collections import defaultdict

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = "scripts.db"

def connect_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def find_duplicates(conn):
    """Find scripts with same title + genre + player_count"""
    cursor = conn.execute("""
        SELECT id, title, genre, player_count, created_at, is_active
        FROM scripts
        WHERE is_active = 1
        ORDER BY title, genre, player_count, created_at DESC
    """)
    
    scripts = [dict(row) for row in cursor.fetchall()]
    
    # Group by (title, genre, player_count)
    groups = defaultdict(list)
    for script in scripts:
        key = (script['title'], script['genre'], script['player_count'])
        groups[key].append(script)
    
    # Filter to only groups with duplicates
    duplicates = {k: v for k, v in groups.items() if len(v) > 1}
    return duplicates

def cleanup_duplicates(conn, duplicates, interactive=True):
    """Remove duplicates by soft-deleting older versions"""
    total_removed = 0
    
    for key, scripts in duplicates.items():
        title, genre, player_count = key
        print(f"\n📚 重复剧本：{title} ({genre}, {player_count}人)")
        print(f"   共 {len(scripts)} 个版本:")
        
        # Keep the first one (most recent due to ORDER BY)
        keep = scripts[0]
        print(f"   ✅ 保留：{keep['id']} (创建于 {keep['created_at']})")
        
        # Soft delete the rest
        for script in scripts[1:]:
            if interactive:
                confirm = input(f"   删除 {script['id']}? (y/n): ")
                if confirm.lower() != 'y':
                    print(f"   ⏭️  跳过")
                    continue
            
            conn.execute(
                "UPDATE scripts SET is_active = 0 WHERE id = ?",
                (script['id'],)
            )
            print(f"   🗑️  已删除：{script['id']}")
            total_removed += 1
    
    conn.commit()
    return total_removed

def main():
    parser = argparse.ArgumentParser(description='Detect and clean duplicate scripts')
    parser.add_argument('--non-interactive', action='store_true', 
                        help='Auto-delete all duplicates without confirmation')
    args = parser.parse_args()
    
    print("=== 剧本重复清理工具 ===\n")
    
    conn = connect_db()
    duplicates = find_duplicates(conn)
    
    if not duplicates:
        print("✅ 没有发现重复剧本！")
        conn.close()
        return
    
    print(f"🔍 发现 {len(duplicates)} 组重复剧本:\n")
    
    for key, scripts in duplicates.items():
        title, genre, player_count = key
        print(f"  - {title} ({genre}, {player_count}人): {len(scripts)} 个版本")
    
    if args.non_interactive:
        print("\n⚠️  非交互模式：将自动删除所有旧版本")
        confirm = 'y'
    else:
        print()
        confirm = input("是否继续清理？(y/n): ")
    
    if confirm.lower() != 'y':
        print("取消清理")
        conn.close()
        return
    
    removed = cleanup_duplicates(conn, duplicates, interactive=not args.non_interactive)
    
    print(f"\n✅ 清理完成！共删除 {removed} 个重复剧本")
    conn.close()

if __name__ == "__main__":
    main()

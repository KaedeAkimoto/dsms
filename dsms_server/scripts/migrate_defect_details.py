#!/usr/bin/env python3
"""
数据库迁移脚本

修复 defect_details 表结构
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config.database import db_config
from sqlalchemy import text

def check_table_structure(conn):
    """检查表结构"""
    result = conn.execute(text("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'defect_details'
    """))
    columns = {row[0]: row[1] for row in result.fetchall()}
    print(f"当前表结构: {columns}")
    return columns

def migrate_defect_details_table():
    """迁移 defect_details 表结构"""
    print("=" * 50)
    print("开始迁移 defect_details 表...")
    print("=" * 50)

    with db_config.engine.connect() as conn:
        columns = check_table_structure(conn)

        changes = []

        if 'original_img' in columns and 'image' not in columns:
            print("\n执行迁移: 添加 image 字段...")
            conn.execute(text("ALTER TABLE defect_details ADD COLUMN image bytea"))
            conn.execute(text("UPDATE defect_details SET image = decode(original_img, 'base64') WHERE original_img IS NOT NULL AND original_img != ''"))
            changes.append("original_img -> image")
            print("  完成: 添加 image 字段并复制数据")

        if 'img_format' in columns and 'image_format' not in columns:
            print("\n执行迁移: img_format -> image_format...")
            conn.execute(text("ALTER TABLE defect_details RENAME COLUMN img_format TO image_format"))
            changes.append("img_format -> image_format")
            print("  完成: 重命名 img_format -> image_format")

        if 'image' in columns and 'image_format' not in columns:
            print("\n执行迁移: 添加 image_format 字段...")
            conn.execute(text("ALTER TABLE defect_details ADD COLUMN image_format varchar(20)"))
            conn.execute(text("UPDATE defect_details SET image_format = 'jpeg' WHERE image IS NOT NULL"))
            changes.append("添加 image_format")
            print("  完成: 添加 image_format 字段并设为 'jpeg'")

        if not changes:
            print("\n表结构已经是最新的或不需要迁移")
        else:
            conn.commit()
            print(f"\n迁移完成! 变更: {changes}")

        print("\n迁移后表结构:")
        check_table_structure(conn)

    print("=" * 50)
    print("迁移完成!")
    print("=" * 50)


if __name__ == "__main__":
    migrate_defect_details_table()

'''import sqlite3
conn = sqlite3.connect('data/worldlens.db')
cur = conn.cursor()

print('=' * 50)
print('📊 WorldLens 采集状态')
print('=' * 50)

cur.execute('SELECT COUNT(*) FROM articles')
print(f'📰 总文章数: {cur.fetchone()[0]}')

cur.execute('SELECT s.category, COUNT(a.id) FROM sources s LEFT JOIN articles a ON a.source_id=s.id GROUP BY s.category')
for cat, count in cur.fetchall():
    print(f'   {cat or "未分类"}: {count} 篇')

cur.execute('SELECT COUNT(*) FROM articles WHERE image_url IS NOT NULL')
print(f'🖼️ 有图片的文章: {cur.fetchone()[0]} 篇')

cur.execute('SELECT COUNT(*) FROM articles WHERE published_at IS NOT NULL')
print(f'📅 有日期的文章: {cur.fetchone()[0]} 篇')

print('=' * 50)'''


import sqlite3
conn = sqlite3.connect('data/worldlens.db')
cur = conn.cursor()
cur.execute('''
    SELECT s.name, COUNT(a.id) 
    FROM articles a 
    JOIN sources s ON a.source_id = s.id 
    GROUP BY s.name 
    ORDER BY COUNT(a.id) DESC
''')
for row in cur.fetchall():
    print(f'{row[0]}: {row[1]} 篇')
model = {
    'execution': '''CREATE TABLE IF NOT EXISTS execution (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    time_start INTEGER, chord_name TEXT, execution_time FLOAT,
    status INTEGER, output BLOB )''',
    'state': '''CREATE TABLE IF NOT EXISTS state (
    key TEXT NOT NULL UNIQUE,
    value BLOB NOT NULL)'''
}

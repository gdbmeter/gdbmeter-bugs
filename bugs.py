#!/usr/bin/env python3

"""This script provides functionality to validate, manipulate, and transform the bugs.json file. Taken from
https://github.com/sqlancer/bugs with consent of the original author and adjusted to our needs. """

import argparse
import json
import sqlite3
import sys
from jsonschema import validate

parser = argparse.ArgumentParser(prog='bugs.py')
parser.add_argument('action', choices=['check', 'format', 'export_database'])
args = parser.parse_args()

f = open("bugs.json", "r")
original_content = f.read()
parsed_content = json.loads(original_content)


def check():
    """Checks that the JSON file is correctly formatted."""
    formatted_content = json.dumps(parsed_content, indent=4) + '\n'
    correctly_formatted = original_content == formatted_content
    if not correctly_formatted:
        sys.exit(-1)
    schema = {
        "type": "array",
        "items": {
            "required": ["date", "dbms", "status", "test", "title", "link", "type"],
            "properties": {
                "date": {"type": "string"},
                "dbms": {
                    "type": "string",
                    "pattern": r"^(Neo4j|RedisGraph|Jedis|JanusGraph)$",
                },
                "link": {"type": "string"},
                "status": {
                    "type": "string",
                    # verified means that it's a bug but it hasn't been closed yet!
                    "pattern": r"^(closed \(not a bug\)|fixed|"
                               r"closed \(duplicate\)|"
                               r"fixed \(in documentation\)|verified|open)$"
                },
                "type": {
                    "type": "string",
                    "pattern": r"^(logic|error|crash|hang|client)$"
                },
                "comment": {"type": "string"},
                "test": {"type": "array", "items": {"type": "string"}},
                "title": {"type": "string"},
            }
        }
    }
    validate(instance=parsed_content, schema=schema)


def format_json():
    """Consistently formats the JSON file."""
    formatted_content = json.dumps(parsed_content,
                                   indent=4,
                                   sort_keys=True,
                                   separators=(',', ': ')) + '\n'
    f.close()
    f_w = open("bugs.json", "w")
    f_w.write(formatted_content)


def export_database():
    """Exports the JSON bug file as a SQLite3 database."""
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE DBMS_BUGS (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        DBMS STRING,
        TYPE STRING,
        COMMENT STRING,
        STATUS STRING,
        DATE STRING,
        TEST STRING,
        URL_BUGTRACKER STRING
    );
    """)
    cursor.execute("""
    CREATE TABLE BUG_TEST_CASES(
        id INTEGER,
        STATEMENT STRING,
        POSITION INTEGER,
        FOREIGN KEY(id) REFERENCES DBMS_BUGS(id)
    );
    """)
    cursor.execute("""
    CREATE VIEW DBMS_BUGS_TRUE_POSITIVES AS
    SELECT * FROM DBMS_BUGS
    WHERE STATUS IN ('fixed', 'open', 'verified', 'fixed (in documentation)')
    """)
    cursor.execute("""
    CREATE VIEW DBMS_BUGS_FALSE_POSITIVES AS
    SELECT * FROM DBMS_BUGS
    WHERE id not IN (SELECT id FROM DBMS_BUGS_TRUE_POSITIVES);
    """)
    cursor.execute("""
    CREATE VIEW DBMS_BUGS_STATUS AS
    SELECT d1.DBMS, d2.status, (SELECT COUNT(*) FROM DBMS_BUGS d3
        WHERE d3.DBMS = d1.DBMS AND d3.STATUS = d2.STATUS) as count
        FROM DBMS_BUGS d1, DBMS_BUGS d2 GROUP BY d1.DBMS, d2.STATUS;
    """)
    for bug_entry in parsed_content:
        cursor.execute("""INSERT INTO DBMS_BUGS (DBMS, TYPE, COMMENT, STATUS, DATE, TEST, URL_BUGTRACKER)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
                       (bug_entry['dbms'],
                        bug_entry['type'],
                        bug_entry.get('comment', None),
                        bug_entry['status'],
                        bug_entry['date'],
                        '\n'.join(bug_entry['test']),
                        bug_entry['link']))
        rid = cursor.execute('select last_insert_rowid();').fetchall()[0][0]
        seq = 0
        for statement in bug_entry['test']:
            if not (statement.startswith('--') or statement == ''):
                cursor.execute('INSERT INTO BUG_TEST_CASES'
                               '(id, STATEMENT, POSITION) '
                               'VALUES(%d, "%s", %d)'
                               % (rid, statement.replace('"', '""'), seq))
                seq += 1
    conn.commit()


{
    'check': check,
    'format': format_json,
    'export_database': export_database
}[args.action]()

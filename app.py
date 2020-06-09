import os
import struct
import pyodbc
from azure.identity import DefaultAzureCredential

from flask import Flask, jsonify

app = Flask(__name__)



def connect_db(server=None, database=None, driver=None):
    DB_SERVER = 'tcp:' + (server or os.environ['DB_SERVER']) + '.database.windows.net'
    DB_NAME = database or os.environ['DB_NAME']
    DB_DRIVER = driver or '{ODBC Driver 17 for SQL Server}'
    DB_RESOURCE_URI = 'https://database.windows.net/'

    az_credential = DefaultAzureCredential()
    access_token = az_credential.get_token(DB_RESOURCE_URI)
    
    token = bytes(access_token.token, 'utf-8')
    exptoken = b"";
    for i in token:
        exptoken += bytes({i});
        exptoken += bytes(1);
    tokenstruct = struct.pack("=i", len(exptoken)) + exptoken;
    
    connection_string = 'driver='+DB_DRIVER+';server='+DB_SERVER+';database='+DB_NAME
    conn = pyodbc.connect(connection_string, attrs_before = { 1256:bytearray(tokenstruct) });
    
    return conn

def resultset_to_dictlist(resultset):
    result = []
    for row in resultset:
        entry = { f[1][0]:row[f[0]] for f in enumerate(row.cursor_description) }
        result.append(entry)
    return result


@app.route('/')
def hello_world():
    db = connect_db()
    result = {}
    with db.execute("SELECT @@version") as resultset:
        # result['columns'] = row.cursor_description
        result['rows']  = resultset_to_dictlist(resultset)
    return jsonify(result)

"""FollowUp Flow: dependency-free local web app for tracking customer inquiries."""
import csv
import io
import json
import os
import sqlite3
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get('FOLLOWUP_DB', str(ROOT / 'leads.sqlite3')))


def connect():
    db = sqlite3.connect(DB_PATH, timeout=10)
    db.row_factory = sqlite3.Row
    return db


def initialize():
    with connect() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS inquiries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer TEXT NOT NULL,
            contact TEXT NOT NULL,
            request TEXT NOT NULL,
            value REAL NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'new' CHECK(status IN ('new','contacted','won','lost')),
            created_at TEXT NOT NULL
        )""")


def add_inquiry(data):
    customer = str(data.get('customer', '')).strip()
    contact = str(data.get('contact', '')).strip()
    request = str(data.get('request', '')).strip()
    if not customer or not contact or not request:
        raise ValueError('Customer, contact, and request are required.')
    if max(map(len, [customer,contact,request])) > 500:
        raise ValueError('Fields must be 500 characters or shorter.')
    try:
        value = float(data.get('value') or 0)
    except (TypeError, ValueError):
        raise ValueError('Potential value must be a number.')
    if value < 0 or value > 100000000:
        raise ValueError('Potential value must be between 0 and 100 million.')
    now = datetime.now(timezone.utc).isoformat(timespec='seconds')
    with connect() as db:
        cur = db.execute('INSERT INTO inquiries (customer, contact, request, value, created_at) VALUES (?,?,?,?,?)',
                         (customer,contact,request,value,now))
        return dict(db.execute('SELECT * FROM inquiries WHERE id=?', (cur.lastrowid,)).fetchone())


def list_inquiries():
    with connect() as db:
        return [dict(x) for x in db.execute('SELECT * FROM inquiries ORDER BY id DESC')]


def update_status(id_, status):
    if status not in ('new', 'contacted', 'won', 'lost'):
        raise ValueError('Invalid status.')
    try:
        number = int(id_)
    except (ValueError, TypeError):
        raise ValueError('Invalid inquiry ID.')
    with connect() as db:
        cur = db.execute('UPDATE inquiries SET status=? WHERE id=?', (status,number))
        if not cur.rowcount:
            raise LookupError('Inquiry not found.')
        return dict(db.execute('SELECT * FROM inquiries WHERE id=?', (number,)).fetchone())


class Handler(BaseHTTPRequestHandler):
    def send(self, status, payload, content_type='application/json; charset=utf-8', extras=None):
        encoded = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(encoded)))
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Cache-Control', 'no-store')
        for k,v in (extras or {}).items(): self.send_header(k,v)
        self.end_headers()
        self.wfile.write(encoded)

    def body(self):
        length = int(self.headers.get('Content-Length', '0'))
        if length > 16384: raise ValueError('Request too large.')
        try: return json.loads(self.rfile.read(length))
        except (json.JSONDecodeError, UnicodeDecodeError): raise ValueError('Invalid JSON.')

    def do_GET(self):
        path = urlparse(self.path).path
        if path == '/':
            return self.send(200, (ROOT/'index.html').read_bytes(), 'text/html; charset=utf-8')
        if path == '/api/inquiries': return self.send(200, list_inquiries())
        if path == '/api/export':
            rows = list_inquiries()
            out = io.StringIO()
            writer = csv.writer(out)
            writer.writerow(['id','customer','contact','request','value','status','created_at'])
            for row in rows: writer.writerow([row[k] for k in ('id','customer','contact','request','value','status','created_at')])
            return self.send(200,out.getvalue().encode('utf-8-sig'),'text/csv; charset=utf-8',{'Content-Disposition':'attachment; filename="followup-inquiries.csv"'})
        self.send(404, {'error':'Not found'})

    def do_POST(self):
        try:
            path = urlparse(self.path).path
            if path == '/api/inquiries': return self.send(201,add_inquiry(self.body()))
            if path.startswith('/api/inquiries/') and path.endswith('/status'):
                parts = path.split('/')
                if len(parts) == 5: return self.send(200,update_status(parts[3],self.body().get('status')))
            return self.send(404,{'error':'Not found'})
        except (ValueError, TypeError) as ex: self.send(400, {'error':str(ex)})
        except LookupError as ex: self.send(404, {'error':str(ex)})


if __name__ == '__main__':
    initialize()
    port=int(os.environ.get('PORT','8000'))
    print(f'FollowUp Flow running at http://localhost:{port}')
    ThreadingHTTPServer(('127.0.0.1',port),Handler).serve_forever()

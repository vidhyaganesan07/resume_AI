"""
Django-style admin panel served at /admin
- Login / logout with session cookie
- Dashboard with model list + row counts
- List view  (sortable, paginated)
- Detail/Edit view (inline form for every field)
- Delete confirmation
- Add new record
"""
import base64
import hashlib
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from typing import Any, Iterator

from fastapi import APIRouter, Cookie, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from config import ADMIN_PASSWORD, ADMIN_USERNAME, DB_PATH

router = APIRouter()

SESSION_TTL = 8  # hours

# ─────────────────────────── session helpers ────────────────────────────────

def _make_token(username: str) -> str:
    ts = datetime.now(timezone.utc).isoformat()
    raw = f"{username}:{ts}"
    sig = hashlib.sha256((raw + ADMIN_PASSWORD).encode()).hexdigest()[:16]
    return base64.urlsafe_b64encode(f"{raw}:{sig}".encode()).decode()


def _valid_session(token: str | None) -> bool:
    if not token:
        return False
    try:
        decoded = base64.urlsafe_b64decode(token.encode()).decode()
        username, ts, sig = decoded.rsplit(":", 2)
        raw = f"{username}:{ts}"
        if sig != hashlib.sha256((raw + ADMIN_PASSWORD).encode()).hexdigest()[:16]:
            return False
        return datetime.now(timezone.utc) - datetime.fromisoformat(ts) < timedelta(hours=SESSION_TTL)
    except Exception:
        return False


def _auth(token: str | None):
    """Return redirect if not authenticated, else None."""
    if not _valid_session(token):
        return RedirectResponse("/admin/login", status_code=302)


# ─────────────────────────── DB helpers ─────────────────────────────────────

@contextmanager
def _conn() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def _tables() -> list[str]:
    with _conn() as c:
        rows = c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
        return [r["name"] for r in rows]


def _columns(table: str) -> list[str]:
    with _conn() as c:
        rows = c.execute(f"PRAGMA table_info({table})").fetchall()
        return [r["name"] for r in rows]


def _pk(table: str) -> str:
    with _conn() as c:
        rows = c.execute(f"PRAGMA table_info({table})").fetchall()
        for r in rows:
            if r["pk"]:
                return r["name"]
    return "id"


def _count(table: str) -> int:
    with _conn() as c:
        return c.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def _rows(table: str, page: int = 1, per: int = 25) -> list[dict]:
    offset = (page - 1) * per
    with _conn() as c:
        rows = c.execute(f"SELECT * FROM {table} LIMIT ? OFFSET ?", (per, offset)).fetchall()
        return [dict(r) for r in rows]


def _get_row(table: str, pk_col: str, pk_val: str) -> dict | None:
    with _conn() as c:
        row = c.execute(f"SELECT * FROM {table} WHERE {pk_col}=?", (pk_val,)).fetchone()
        return dict(row) if row else None


def _delete_row(table: str, pk_col: str, pk_val: str):
    with _conn() as c:
        c.execute(f"DELETE FROM {table} WHERE {pk_col}=?", (pk_val,))
        c.commit()


def _update_row(table: str, pk_col: str, pk_val: str, data: dict):
    sets = ", ".join(f"{k}=?" for k in data)
    vals = list(data.values()) + [pk_val]
    with _conn() as c:
        c.execute(f"UPDATE {table} SET {sets} WHERE {pk_col}=?", vals)
        c.commit()


def _insert_row(table: str, data: dict):
    cols = ", ".join(data.keys())
    placeholders = ", ".join("?" * len(data))
    with _conn() as c:
        c.execute(f"INSERT INTO {table} ({cols}) VALUES ({placeholders})", list(data.values()))
        c.commit()


# ─────────────────────────── HTML helpers ───────────────────────────────────

_STYLE = """
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
     font-size:14px;background:#f8f9fa;color:#212529;min-height:100vh}

/* top nav */
#header{background:#417690;color:#fff;padding:0;display:flex;align-items:stretch}
#header .brand{font-size:18px;font-weight:700;padding:12px 20px;
               background:#205067;display:flex;align-items:center;gap:8px}
#header nav{display:flex;align-items:center;gap:2px;padding:0 8px;flex:1}
#header nav a{color:#c7dfe6;padding:8px 12px;border-radius:4px;font-size:13px}
#header nav a:hover{background:#205067;color:#fff;text-decoration:none}
#header .user-info{padding:8px 20px;display:flex;align-items:center;gap:12px;
                   color:#c7dfe6;font-size:13px;margin-left:auto}
#header .user-info a{color:#c7dfe6}
#header .user-info a:hover{color:#fff}

/* breadcrumbs */
.breadcrumbs{background:#fff;border-bottom:1px solid #dee2e6;padding:8px 20px;
             font-size:13px;color:#6c757d}
.breadcrumbs a{color:#417690}
.breadcrumbs span{margin:0 6px}

/* content */
.content-wrap{padding:20px}
h1{font-size:24px;font-weight:300;color:#333;margin-bottom:20px}
h2{font-size:18px;color:#333;margin-bottom:12px}

/* messages */
.messages{margin-bottom:16px}
.msg{padding:10px 16px;border-radius:4px;margin-bottom:6px;font-size:13px}
.msg.success{background:#d4edda;color:#155724;border:1px solid #c3e6cb}
.msg.error  {background:#f8d7da;color:#721c24;border:1px solid #f5c6cb}

/* module index */
.module{background:#fff;border:1px solid #dee2e6;border-radius:4px;
        margin-bottom:20px;overflow:hidden}
.module caption,.module .caption{background:#417690;color:#fff;padding:8px 16px;
                                  font-size:15px;font-weight:600;display:block}
.module table{width:100%;border-collapse:collapse}
.module td,.module th{padding:8px 16px;border-bottom:1px solid #f0f0f0;text-align:left}
.module th{background:#f8f9fa;font-weight:600;color:#666;font-size:12px;text-transform:uppercase}
.module tr:last-child td{border-bottom:none}
.module tr:hover td{background:#f8f9fa}
.module td a{color:#417690;font-weight:500}

/* change-list */
#changelist{background:#fff;border:1px solid #dee2e6;border-radius:4px;overflow:hidden}
#changelist .actions{padding:10px 16px;background:#f8f9fa;border-bottom:1px solid #dee2e6;
                     display:flex;align-items:center;justify-content:space-between}
#changelist table{width:100%;border-collapse:collapse}
#changelist th{background:#f8f9fa;padding:8px 12px;border-bottom:2px solid #dee2e6;
               font-size:12px;color:#666;text-transform:uppercase;white-space:nowrap}
#changelist td{padding:8px 12px;border-bottom:1px solid #f0f0f0;
               max-width:220px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
#changelist tr:hover td{background:#f9f9f9}
#changelist td a{color:#417690;font-weight:500}
.pagination{padding:10px 16px;background:#f8f9fa;border-top:1px solid #dee2e6;
            font-size:13px;display:flex;align-items:center;gap:8px}
.pagination a{color:#417690}

/* change-form */
.change-form{background:#fff;border:1px solid #dee2e6;border-radius:4px;overflow:hidden}
.form-row{display:flex;border-bottom:1px solid #f0f0f0}
.form-row label{width:200px;min-width:200px;padding:12px 16px;font-weight:600;
                color:#333;font-size:13px;border-right:1px solid #f0f0f0;background:#f8f9fa}
.form-row .field{flex:1;padding:10px 16px}
.form-row input[type=text],.form-row textarea,.form-row select{
  width:100%;padding:7px 10px;border:1px solid #ccc;border-radius:4px;font-size:14px;
  font-family:inherit;color:#333}
.form-row textarea{height:120px;resize:vertical}
.form-row input[type=text]:focus,.form-row textarea:focus{
  border-color:#417690;outline:none;box-shadow:0 0 0 2px #41769033}
.form-row .help{font-size:12px;color:#999;margin-top:4px}
.submit-row{padding:14px 20px;background:#f8f9fa;border-top:1px solid #dee2e6;
            display:flex;gap:10px;align-items:center}

/* buttons */
.btn{display:inline-block;padding:7px 14px;border-radius:4px;font-size:13px;
     cursor:pointer;border:none;font-family:inherit;text-decoration:none}
.btn-primary{background:#417690;color:#fff}
.btn-primary:hover{background:#205067}
.btn-danger{background:#ba2121;color:#fff}
.btn-danger:hover{background:#a41515}
.btn-secondary{background:#f8f9fa;color:#333;border:1px solid #ccc}
.btn-secondary:hover{background:#e9ecef}
.btn-add{background:#417690;color:#fff;padding:6px 12px;font-size:13px;
         border-radius:4px;border:none;cursor:pointer;text-decoration:none;float:right}

/* delete confirm */
.delete-confirm{background:#fff;border:1px solid #dee2e6;border-radius:4px;
                padding:24px;max-width:600px}
.delete-confirm h2{color:#ba2121;margin-bottom:12px}
.delete-confirm ul{margin:12px 0 20px 20px;color:#555}

/* login */
.login-wrap{display:flex;align-items:center;justify-content:center;min-height:100vh;
            background:#417690}
.login-box{background:#fff;border-radius:6px;padding:0;width:380px;
           box-shadow:0 4px 20px rgba(0,0,0,.3);overflow:hidden}
.login-box h1{background:#417690;color:#fff;padding:20px 24px;font-size:20px;
              font-weight:300;display:flex;align-items:center;gap:10px}
.login-body{padding:24px}
.login-body label{display:block;font-weight:600;font-size:13px;
                  color:#333;margin-bottom:4px;margin-top:14px}
.login-body input{width:100%;padding:9px 12px;border:1px solid #ccc;
                  border-radius:4px;font-size:14px}
.login-body input:focus{border-color:#417690;outline:none}
.login-body .btn-primary{width:100%;margin-top:20px;padding:10px}
.login-error{background:#f8d7da;color:#721c24;border:1px solid #f5c6cb;
             padding:10px 14px;border-radius:4px;font-size:13px;margin-top:12px}
</style>
"""

def _base(title: str, breadcrumbs: str, content: str, msg: str = "") -> HTMLResponse:
    tables = _tables()
    nav_links = "".join(f'<a href="/admin/{t}">{t.replace("_"," ").title()}</a>' for t in tables)
    msg_html = f'<div class="messages"><div class="msg success">{msg}</div></div>' if msg else ""
    html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} | ResumeScout Admin</title>{_STYLE}</head>
<body>
<div id="header">
  <div class="brand">🛡️ ResumeScout</div>
  <nav>{nav_links}</nav>
  <div class="user-info">
    <span>Welcome, <strong>{ADMIN_USERNAME}</strong></span>
    <a href="/admin/logout">Log out</a>
  </div>
</div>
<div class="breadcrumbs">{breadcrumbs}</div>
<div class="content-wrap">
  {msg_html}
  {content}
</div>
</body></html>"""
    return HTMLResponse(html)


def _truncate(v: Any, n: int = 60) -> str:
    s = str(v) if v is not None else "—"
    return s[:n] + "…" if len(s) > n else s


# ─────────────────────────── routes ─────────────────────────────────────────

# Login / logout
@router.get("/admin/login", response_class=HTMLResponse)
def login_page(error: str = ""):
    err = "<div class='login-error'>Please enter the correct username and password.</div>" if error else ""
    html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<title>Log in | ResumeScout Admin</title>{_STYLE}</head>
<body>
<div class="login-wrap">
  <div class="login-box">
    <h1>🛡️ ResumeScout Admin</h1>
    <div class="login-body">
      <form method="post" action="/admin/login">
        <label>Username</label>
        <input name="username" type="text" autofocus autocomplete="username">
        <label>Password</label>
        <input name="password" type="password" autocomplete="current-password">
        <button class="btn btn-primary" type="submit">Log in</button>
        {err}
      </form>
    </div>
  </div>
</div>
</body></html>"""
    return HTMLResponse(html)


@router.post("/admin/login")
def login_post(username: str = Form(...), password: str = Form(...)):
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        resp = RedirectResponse("/admin", status_code=302)
        resp.set_cookie("admin_session", _make_token(username),
                        httponly=True, samesite="lax", max_age=SESSION_TTL * 3600)
        return resp
    return RedirectResponse("/admin/login?error=1", status_code=302)


@router.get("/admin/logout")
def logout():
    resp = RedirectResponse("/admin/login", status_code=302)
    resp.delete_cookie("admin_session")
    return resp


# Dashboard
@router.get("/admin", response_class=HTMLResponse)
def dashboard(admin_session: str | None = Cookie(default=None)):
    if r := _auth(admin_session): return r
    tables = _tables()
    rows_html = "".join(f"""
      <tr>
        <td><a href="/admin/{t}">{t.replace('_',' ').title()}</a></td>
        <td>{_count(t)}</td>
        <td>
          <a href="/admin/{t}">Change</a> &nbsp;|&nbsp;
          <a href="/admin/{t}/add">Add</a>
        </td>
      </tr>""" for t in tables)
    content = f"""
    <h1>Site Administration</h1>
    <div class="module">
      <div class="caption">Database Tables</div>
      <table>
        <thead><tr><th>Table</th><th>Records</th><th>Actions</th></tr></thead>
        <tbody>{rows_html}</tbody>
      </table>
    </div>"""
    return _base("Site Administration",
                 '<a href="/admin">Home</a>', content)


# List view
@router.get("/admin/{table}", response_class=HTMLResponse)
def list_view(table: str, page: int = 1,
              admin_session: str | None = Cookie(default=None),
              msg: str = ""):
    if r := _auth(admin_session): return r
    if table not in _tables():
        return HTMLResponse("Table not found", status_code=404)

    cols = _columns(table)
    pk = _pk(table)
    per = 25
    total = _count(table)
    rows = _rows(table, page, per)
    pages = max(1, (total + per - 1) // per)

    header = "".join(f"<th>{c}</th>" for c in cols)
    body = ""
    for row in rows:
        pk_val = row.get(pk, "")
        cells = ""
        for i, c in enumerate(cols):
            val = _truncate(row.get(c))
            if i == 0:
                cells += f'<td><a href="/admin/{table}/{pk_val}/change">{val}</a></td>'
            else:
                cells += f"<td title='{row.get(c)}'>{val}</td>"
        body += f"<tr>{cells}</tr>"

    if not rows:
        body = f"<tr><td colspan='{len(cols)}' style='padding:20px;color:#999;text-align:center'>No records found.</td></tr>"

    pag = ""
    if pages > 1:
        prev = f'<a href="/admin/{table}?page={page-1}">← Previous</a>' if page > 1 else ""
        nxt  = f'<a href="/admin/{table}?page={page+1}">Next →</a>' if page < pages else ""
        pag  = f'<div class="pagination">{prev} <span>Page {page} of {pages} — {total} records</span> {nxt}</div>'

    content = f"""
    <h1>{table.replace('_',' ').title()}
      <a class="btn-add" href="/admin/{table}/add">+ Add {table[:-1] if table.endswith('s') else table}</a>
    </h1>
    <div id="changelist">
      <div class="actions"><span>{total} total records</span></div>
      <table>
        <thead><tr>{header}</tr></thead>
        <tbody>{body}</tbody>
      </table>
      {pag}
    </div>"""

    crumbs = f'<a href="/admin">Home</a> <span>›</span> {table.replace("_"," ").title()}'
    return _base(table.title(), crumbs, content, msg)


# Add view
@router.get("/admin/{table}/add", response_class=HTMLResponse)
def add_view(table: str, admin_session: str | None = Cookie(default=None)):
    if r := _auth(admin_session): return r
    if table not in _tables(): return HTMLResponse("Table not found", 404)
    cols = _columns(table)
    rows_html = "".join(f"""
      <div class="form-row">
        <label>{c}</label>
        <div class="field">
          <input type="text" name="{c}" value="">
          <div class="help">Column: {c}</div>
        </div>
      </div>""" for c in cols)
    content = f"""
    <h1>Add {table.replace('_',' ').title()}</h1>
    <form method="post" action="/admin/{table}/add">
      <div class="change-form">
        {rows_html}
        <div class="submit-row">
          <button class="btn btn-primary" type="submit">Save</button>
          <a class="btn btn-secondary" href="/admin/{table}">Cancel</a>
        </div>
      </div>
    </form>"""
    crumbs = f'<a href="/admin">Home</a> <span>›</span> <a href="/admin/{table}">{table.title()}</a> <span>›</span> Add'
    return _base(f"Add {table}", crumbs, content)


@router.post("/admin/{table}/add")
async def add_post(table: str, request: Request,
                   admin_session: str | None = Cookie(default=None)):
    if r := _auth(admin_session): return r
    if table not in _tables(): return HTMLResponse("Table not found", 404)
    form = await request.form()
    data = {k: v for k, v in form.items() if v != ""}
    try:
        _insert_row(table, data)
    except Exception as e:
        return HTMLResponse(f"<pre>Error: {e}</pre>", 400)
    return RedirectResponse(f"/admin/{table}?msg=Record+added+successfully", status_code=302)


# Change (edit) view
@router.get("/admin/{table}/{pk_val}/change", response_class=HTMLResponse)
def change_view(table: str, pk_val: str,
                admin_session: str | None = Cookie(default=None)):
    if r := _auth(admin_session): return r
    if table not in _tables(): return HTMLResponse("Table not found", 404)
    pk = _pk(table)
    row = _get_row(table, pk, pk_val)
    if not row: return HTMLResponse("Record not found", 404)

    cols = _columns(table)
    rows_html = ""
    for c in cols:
        val = row.get(c, "") or ""
        # Use textarea for long text fields
        if len(str(val)) > 80 or c in ("raw_text", "summary", "skills", "experience",
                                        "education", "suggestions", "missing_keywords",
                                        "skill_match", "matched_skills", "missing_skills",
                                        "required_skills", "recommendation"):
            field = f'<textarea name="{c}">{val}</textarea>'
        else:
            field = f'<input type="text" name="{c}" value="{val}">'
        rows_html += f"""
        <div class="form-row">
          <label>{c}</label>
          <div class="field">{field}</div>
        </div>"""

    content = f"""
    <h1>Change {table.replace('_',' ').title()}</h1>
    <form method="post" action="/admin/{table}/{pk_val}/change">
      <div class="change-form">
        {rows_html}
        <div class="submit-row">
          <button class="btn btn-primary" type="submit">Save</button>
          <a class="btn btn-secondary" href="/admin/{table}">Cancel</a>
          <a class="btn btn-danger" href="/admin/{table}/{pk_val}/delete"
             style="margin-left:auto">Delete</a>
        </div>
      </div>
    </form>"""
    crumbs = (f'<a href="/admin">Home</a> <span>›</span> '
              f'<a href="/admin/{table}">{table.title()}</a> <span>›</span> {pk_val[:12]}…')
    return _base(f"Change {table}", crumbs, content)


@router.post("/admin/{table}/{pk_val}/change")
async def change_post(table: str, pk_val: str, request: Request,
                      admin_session: str | None = Cookie(default=None)):
    if r := _auth(admin_session): return r
    if table not in _tables(): return HTMLResponse("Table not found", 404)
    pk = _pk(table)
    form = await request.form()
    data = {k: v for k, v in form.items() if k != pk}
    try:
        _update_row(table, pk, pk_val, data)
    except Exception as e:
        return HTMLResponse(f"<pre>Error: {e}</pre>", 400)
    return RedirectResponse(f"/admin/{table}?msg=Record+updated+successfully", status_code=302)


# Delete view
@router.get("/admin/{table}/{pk_val}/delete", response_class=HTMLResponse)
def delete_view(table: str, pk_val: str,
                admin_session: str | None = Cookie(default=None)):
    if r := _auth(admin_session): return r
    if table not in _tables(): return HTMLResponse("Table not found", 404)
    pk = _pk(table)
    row = _get_row(table, pk, pk_val)
    if not row: return HTMLResponse("Record not found", 404)
    fields = "".join(f"<li><strong>{k}:</strong> {_truncate(v)}</li>" for k, v in row.items())
    content = f"""
    <div class="delete-confirm">
      <h2>Are you sure?</h2>
      <p>The following <strong>{table}</strong> record will be deleted:</p>
      <ul style="margin:12px 0 20px 20px;color:#555">{fields}</ul>
      <p style="color:#ba2121;margin-bottom:20px"><strong>This action cannot be undone.</strong></p>
      <form method="post" action="/admin/{table}/{pk_val}/delete" style="display:flex;gap:10px">
        <button class="btn btn-danger" type="submit">Yes, I'm sure</button>
        <a class="btn btn-secondary" href="/admin/{table}/{pk_val}/change">No, take me back</a>
      </form>
    </div>"""
    crumbs = (f'<a href="/admin">Home</a> <span>›</span> '
              f'<a href="/admin/{table}">{table.title()}</a> <span>›</span> Delete')
    return _base(f"Delete {table}", crumbs, content)


@router.post("/admin/{table}/{pk_val}/delete")
def delete_post(table: str, pk_val: str,
                admin_session: str | None = Cookie(default=None)):
    if r := _auth(admin_session): return r
    if table not in _tables(): return HTMLResponse("Table not found", 404)
    pk = _pk(table)
    _delete_row(table, pk, pk_val)
    return RedirectResponse(f"/admin/{table}?msg=Record+deleted+successfully", status_code=302)

import os

from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse

from sqladmin import BaseView, expose


def _log_path(name: str) -> str | None:
    base = os.getenv("LOG_FILE", "/app/logs/admin.log")
    dirname = os.path.dirname(base)
    if name == "api":
        return os.path.join(dirname, "api.log")
    if name == "admin":
        return base
    return base


def _read_last_lines(path: str, n: int = 500) -> tuple[list[str], int]:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            f.seek(0, 2)
            size = f.tell()
            if size == 0:
                return [], 0
            chunk_size = min(65536, size)
            f.seek(max(0, size - chunk_size))
            tail = f.read()
            lines = tail.splitlines()
            result = lines[-n:] if len(lines) > n else lines
            return result, size
    except (FileNotFoundError, OSError):
        return [], 0


CHUNK_BYTES = 256 * 1024
MAX_LINES_CHUNK = 3000


def _read_from_offset(path: str, offset: int) -> tuple[list[str], int]:
    try:
        with open(path, "rb") as f:
            f.seek(0, 2)
            size = f.tell()
            if offset < 0:
                return [], size
            if offset >= size or size == 0:
                return [], size
            f.seek(offset)
            raw = f.read(CHUNK_BYTES)
            text = raw.decode("utf-8", errors="replace")
            lines = [ln for ln in text.splitlines() if ln.strip()]
            if len(lines) > MAX_LINES_CHUNK:
                lines = lines[:MAX_LINES_CHUNK]
            next_off = offset + len(raw)
            return lines, next_off
    except (FileNotFoundError, OSError):
        return [], offset


LOGS_PAGE_HTML = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Логи — Taskify Admin</title>
<style>
* { box-sizing: border-box; }
body { font-family: ui-sans-serif, system-ui, sans-serif; margin: 0; padding: 1rem; background: #0f172a; color: #e2e8f0; min-height: 100vh; }
h1 { font-size: 1.25rem; margin: 0 0 1rem 0; font-weight: 600; }
.controls { display: flex; gap: 0.75rem; align-items: center; margin-bottom: 0.75rem; flex-wrap: wrap; }
.controls label { display: flex; align-items: center; gap: 0.35rem; }
.controls select { padding: 0.4rem 0.6rem; border-radius: 6px; border: 1px solid #475569; background: #1e293b; color: #e2e8f0; font-size: 0.875rem; }
.search-wrap { flex: 1; min-width: 180px; max-width: 320px; }
.search-wrap input { width: 100%; padding: 0.4rem 0.6rem; border-radius: 6px; border: 1px solid #475569; background: #1e293b; color: #e2e8f0; font-size: 0.875rem; }
.search-wrap input::placeholder { color: #64748b; }
.btn { padding: 0.4rem 0.75rem; border-radius: 6px; border: none; cursor: pointer; font-size: 0.875rem; font-weight: 500; }
.btn-pause { background: #475569; color: #fff; }
.btn-pause.paused { background: #22c55e; color: #0f172a; }
.btn-clear { background: #334155; color: #e2e8f0; }
.btn-admin { background: #1e40af; color: #fff; text-decoration: none; }
.btn:hover { opacity: 0.9; }
.btn-admin:hover { opacity: 0.9; color: #fff; }
.controls .cb-wrap { display: flex; align-items: center; gap: 0.35rem; font-size: 0.875rem; color: #94a3b8; }
.status { font-size: 0.8rem; color: #94a3b8; }
#log-container { background: #0f172a; border: 1px solid #334155; border-radius: 8px; padding: 0.75rem 1rem; height: 72vh; overflow: auto; font-family: ui-monospace, "SF Mono", monospace; font-size: 0.8125rem; line-height: 1.5; }
#log-container .line { margin: 0.2em 0; padding: 0.2em 0; border-bottom: 1px solid #1e293b; }
#log-container .line.hidden { display: none; }
#log-container .line .ts { color: #64748b; margin-right: 0.5em; }
#log-container .line .lv { font-weight: 600; margin-right: 0.5em; min-width: 4.5em; display: inline-block; }
#log-container .line .msg { color: #e2e8f0; }
#log-container .line.error .lv { color: #f87171; }
#log-container .line.warning .lv { color: #fbbf24; }
#log-container .line.info .lv { color: #7dd3fc; }
#log-container .line.debug .lv { color: #94a3b8; }
#log-container .line.raw { white-space: pre-wrap; word-break: break-all; }
#log-container .line .extra { font-size: 0.75rem; color: #64748b; margin-top: 0.2em; }
</style>
</head>
<body>
<h1>Логи сервера</h1>
<div class="controls">
<label>Файл: <select id="log-sel"><option value="admin">Admin</option><option value="api">API</option></select></label>
<div class="search-wrap"><input type="text" id="search" placeholder="Поиск по логам…" autocomplete="off"></div>
<label class="cb-wrap"><input type="checkbox" id="auto-scroll" checked> Автоскролл</label>
<button type="button" class="btn btn-pause" id="btn-pause">Пауза</button>
<button type="button" class="btn btn-clear" id="btn-clear">Очистить</button>
<a href="/" class="btn btn-admin">В админку</a>
<span class="status" id="status">—</span>
</div>
<div id="log-container"></div>
<script>
(function() {
var container = document.getElementById('log-container');
var btnPause = document.getElementById('btn-pause');
var btnClear = document.getElementById('btn-clear');
var logSel = document.getElementById('log-sel');
var statusEl = document.getElementById('status');
var searchEl = document.getElementById('search');
var autoScrollEl = document.getElementById('auto-scroll');
var paused = false;
var offset = 0;
var timer = null;

function formatLine(text) {
try {
var o = JSON.parse(text);
var ts = (o.timestamp || '').replace('T', ' ').replace(/\.\\d+Z?$/, '');
var lv = (o.level || '').toLowerCase();
var msg = o.message || '';
var extra = [];
if (o.request_id) extra.push('request_id=' + o.request_id);
if (o.method && o.path) extra.push(o.method + ' ' + o.path);
if (o.status_code != null) extra.push('status=' + o.status_code);
if (o.duration_ms != null) extra.push(o.duration_ms + 'ms');
if (o.exception) extra.push(o.exception);
var extraStr = extra.length ? extra.join(' | ') : '';
return { ts: ts, lv: lv, msg: msg, extra: extraStr, raw: text };
} catch (e) {
return { ts: '', lv: 'raw', msg: text, extra: '', raw: text };
}
}

function applySearch() {
var q = (searchEl.value || '').trim().toLowerCase();
var lines = container.querySelectorAll('.line');
for (var i = 0; i < lines.length; i++) {
var el = lines[i];
if (!q) { el.classList.remove('hidden'); continue; }
var raw = el.getAttribute('data-raw') || '';
el.classList.toggle('hidden', raw.toLowerCase().indexOf(q) === -1);
}
}

function escapeHtml(s) { var d = document.createElement('div'); d.textContent = s; return d.innerHTML; }

function addLine(text, scroll) {
var data = formatLine(text);
var div = document.createElement('div');
div.setAttribute('data-raw', text);
div.className = 'line ' + data.lv;
if (data.lv === 'raw') {
div.textContent = data.msg;
} else {
var html = '';
if (data.ts) html += '<span class="ts">' + escapeHtml(data.ts) + '</span>';
html += '<span class="lv">' + escapeHtml(data.lv.toUpperCase()) + '</span>';
html += '<span class="msg">' + escapeHtml(data.msg) + '</span>';
if (data.extra) html += '<div class="extra">' + escapeHtml(data.extra) + '</div>';
div.innerHTML = html;
}
container.appendChild(div);
var q = (searchEl.value || '').trim();
if (q && data.raw.toLowerCase().indexOf(q.toLowerCase()) === -1) div.classList.add('hidden');
if (scroll && autoScrollEl.checked) container.scrollTop = container.scrollHeight;
}

function poll() {
if (paused) { statusEl.textContent = 'Пауза'; return; }
var file = logSel.value;
var url = '/logs-stream?file=' + encodeURIComponent(file) + '&offset=' + offset;
statusEl.textContent = 'Обновление…';
fetch(url, { credentials: 'same-origin' }).then(function(r) {
if (!r.ok) { statusEl.textContent = 'Ошибка ' + r.status; return null; }
return r.json();
}).then(function(d) {
if (!d) return;
if (d.error) { statusEl.textContent = d.error; return; }
offset = d.next_offset;
if (d.lines && d.lines.length) {
for (var i = 0; i < d.lines.length; i++) addLine(d.lines[i], true);
}
statusEl.textContent = 'В эфире';
}).catch(function() { statusEl.textContent = 'Ошибка'; });
}

function startPolling() {
if (timer) clearInterval(timer);
poll();
timer = setInterval(poll, 2000);
}

function stopPolling() {
if (timer) { clearInterval(timer); timer = null; }
}

btnPause.addEventListener('click', function() {
paused = !paused;
btnPause.textContent = paused ? 'Продолжить' : 'Пауза';
btnPause.classList.toggle('paused', paused);
if (paused) stopPolling(); else startPolling();
statusEl.textContent = paused ? 'Пауза' : 'В эфире';
});

btnClear.addEventListener('click', function() {
container.innerHTML = '';
fetch('//logs?file=' + encodeURIComponent(logSel.value) + '&offset=-1', { credentials: 'same-origin' })
.then(function(r) { return r.ok ? r.json() : null; })
.then(function(d) { if (d) offset = d.next_offset; if (!paused) poll(); });
});

logSel.addEventListener('change', function() {
container.innerHTML = '';
offset = 0;
if (!paused) poll();
});

searchEl.addEventListener('input', function() { applySearch(); });

startPolling();
})();
</script>
</body>
</html>
"""


async def logs_stream_handler(request: Request) -> JSONResponse:
    if not request.session.get("admin_actor"):
        return JSONResponse({"error": "Unauthorized", "lines": [], "next_offset": 0}, status_code=401)
    file_name = request.query_params.get("file", "admin")
    try:
        offset = int(request.query_params.get("offset", "0"))
    except ValueError:
        offset = 0
    path = _log_path(file_name)
    if not path:
        return JSONResponse({"error": "Unknown log", "lines": [], "next_offset": 0})
    if not os.path.isfile(path):
        return JSONResponse({"error": "File not found", "lines": [], "next_offset": 0})
    if offset == 0:
        lines, next_offset = _read_last_lines(path)
    else:
        lines, next_offset = _read_from_offset(path, offset)
    if offset < 0:
        lines = []
    return JSONResponse({"lines": lines, "next_offset": next_offset})


class LogsView(BaseView):
    name = "Logs"
    icon = "fa-solid fa-terminal"
    category = "System"

    @expose("/logs", methods=["GET"])
    async def logs_page(self, request: Request):
        return HTMLResponse(LOGS_PAGE_HTML)


class PgAdminView(BaseView):
    name = "pgAdmin"
    icon = "fa-solid fa-database"
    category = "System"

    @expose("/open-pgadmin", methods=["GET"])
    async def open_pgadmin(self, request: Request):
        return RedirectResponse(url="/pgadmin/browser/", status_code=302)

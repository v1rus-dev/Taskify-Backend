import html
import os
import json
from typing import List, Dict, Any, Optional
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session
from fastapi import APIRouter, Query, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from app.database import get_db, engine
from app.models import Base, User, Task
from app.depends import require_admin


router = APIRouter(prefix="/admin", tags=["Admin"], dependencies=[Depends(require_admin)])


def _read_log(log_file: str, tail: int) -> str:
    if not os.path.exists(log_file):
        return "Log file not found."
    with open(log_file, "r", encoding="utf-8") as handle:
        content = handle.read()
    if tail > 0:
        return content[-tail:]
    return content


def _get_table_names() -> List[str]:
    """Получает список всех таблиц в БД."""
    inspector = inspect(engine)
    return inspector.get_table_names()


def _get_table_columns(table_name: str) -> List[Dict[str, Any]]:
    """Получает информацию о колонках таблицы."""
    inspector = inspect(engine)
    columns = inspector.get_columns(table_name)
    return [{"name": col["name"], "type": str(col["type"]), "nullable": col.get("nullable", True)} for col in columns]


def _get_table_data(table_name: str, db: Session, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    """Получает данные из таблицы."""
    try:
        # Используем параметризованный запрос для безопасности
        result = db.execute(text(f'SELECT * FROM "{table_name}" LIMIT :limit OFFSET :offset'), {
            "limit": limit,
            "offset": offset
        })
        columns = result.keys()
        rows = result.fetchall()
        return [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching data: {str(e)}")


def _get_table_count(table_name: str, db: Session) -> int:
    """Получает количество записей в таблице."""
    try:
        result = db.execute(text(f'SELECT COUNT(*) FROM "{table_name}"'))
        return result.scalar()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error counting records: {str(e)}")


@router.get("", response_class=HTMLResponse)
def admin_panel() -> HTMLResponse:
    """Главная страница админ-панели."""
    body = """<!doctype html>
<html lang="ru">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Taskify Admin Panel</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: #ffffff;
            min-height: 100vh;
            width: 100%;
        }
        .container {
            width: 100%;
            margin: 0;
            background: white;
            min-height: 100vh;
        }
        .header {
            background: rgba(0, 47, 255, 0.6);
            color: white;
            padding: 24px 40px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        .header h1 {
            font-size: 24px;
            font-weight: 600;
            margin-bottom: 4px;
        }
        .header p {
            opacity: 0.9;
            font-size: 14px;
            font-weight: 400;
        }
        .tabs {
            display: flex;
            border-bottom: 1px solid #e5e7eb;
            background: white;
            padding: 0 40px;
        }
        .tab {
            padding: 16px 24px;
            cursor: pointer;
            font-weight: 500;
            color: #6b7280;
            border-bottom: 2px solid transparent;
            transition: all 0.2s;
            font-size: 14px;
        }
        .tab:hover {
            color: #002FFF;
            background: #fafafa;
        }
        .tab.active {
            color: #002FFF;
            border-bottom-color: #002FFF;
        }
        .tab-content {
            display: none;
            padding: 32px 40px;
            width: 100%;
        }
        .tab-content.active {
            display: block;
        }
        .controls {
            display: flex;
            gap: 12px;
            margin-bottom: 24px;
            flex-wrap: wrap;
            align-items: center;
        }
        button {
            background: rgba(0, 47, 255, 0.6);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.2s;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }
        button:hover {
            background: rgba(0, 47, 255, 0.8);
        }
        button:active {
            transform: scale(0.98);
        }
        button.danger {
            background: #dc2626;
        }
        button.danger:hover {
            background: #b91c1c;
        }
        button.warning {
            background: #f59e0b;
        }
        button.warning:hover {
            background: #d97706;
        }
        button.secondary {
            background: #6b7280;
        }
        button.secondary:hover {
            background: #4b5563;
        }
        button.primary {
            background: rgba(0, 47, 255, 0.6);
        }
        button.primary:hover {
            background: rgba(0, 47, 255, 0.8);
        }
        button.paused {
            background: #dc2626;
        }
        .meta {
            color: #6b7280;
            font-size: 14px;
            margin-left: auto;
        }
        pre {
            background: #1a1a1a;
            color: #e5e7eb;
            padding: 20px;
            border-radius: 8px;
            white-space: pre-wrap;
            word-break: break-word;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 13px;
            line-height: 1.6;
            overflow-x: auto;
            max-height: calc(100vh - 300px);
            overflow-y: auto;
            border: 1px solid #e5e7eb;
        }
        .tables-list {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }
        .table-card {
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 20px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .table-card:hover {
            border-color: #002FFF;
            box-shadow: 0 2px 8px rgba(0, 47, 255, 0.1);
        }
        .table-card.active {
            border-color: #002FFF;
            background: rgba(0, 47, 255, 0.05);
        }
        .table-card h3 {
            font-size: 16px;
            color: #111827;
            margin-bottom: 8px;
            font-weight: 600;
        }
        .table-card p {
            color: #6b7280;
            font-size: 14px;
        }
        .table-wrapper {
            width: 100%;
            overflow-x: auto;
            margin-top: 24px;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
        }
        .data-table {
            width: 100%;
            min-width: 800px;
            border-collapse: collapse;
            background: white;
        }
        .data-table thead {
            background: #f9fafb;
        }
        .data-table th {
            padding: 12px 16px;
            text-align: left;
            font-weight: 600;
            color: #374151;
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            border-bottom: 1px solid #e5e7eb;
            white-space: nowrap;
        }
        .data-table td {
            padding: 12px 16px;
            border-bottom: 1px solid #e5e7eb;
            color: #111827;
            font-size: 14px;
            white-space: nowrap;
        }
        .data-table tbody tr:hover {
            background: #f9fafb;
        }
        .data-table tbody tr:last-child td {
            border-bottom: none;
        }
        .action-btn {
            padding: 6px 12px;
            font-size: 12px;
            margin: 0 4px;
        }
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #6b7280;
        }
        .empty-state svg {
            width: 64px;
            height: 64px;
            margin: 0 auto 16px;
            opacity: 0.5;
        }
        .pagination {
            display: flex;
            gap: 8px;
            align-items: center;
            margin-top: 24px;
            justify-content: center;
        }
        .pagination button {
            min-width: 40px;
            padding: 8px 12px;
        }
        .pagination span {
            color: #6b7280;
            font-size: 14px;
        }
        .loading {
            text-align: center;
            padding: 40px;
            color: #6b7280;
        }
        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 500;
        }
        .badge-primary {
            background: rgba(0, 47, 255, 0.1);
            color: #002FFF;
        }
        .badge-success {
            background: #d1fae5;
            color: #065f46;
        }
        .badge-danger {
            background: #fee2e2;
            color: #991b1b;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚙️ Taskify Admin Panel</h1>
            <p>Системная панель управления логами и базой данных</p>
        </div>
        <div class="tabs">
            <div class="tab active" data-tab="logs">📋 Логи</div>
            <div class="tab" data-tab="database">🗄️ База данных</div>
        </div>
        
        <div id="logs-tab" class="tab-content active">
            <div class="controls">
                <button id="pauseBtn">⏸️ Пауза</button>
                <button id="clearBtn" class="warning">🗑️ Очистить логи</button>
                <button id="filterBtn" class="secondary">🔍 Только запросы/ответы</button>
                <div class="meta" id="meta">Auto-refreshing...</div>
            </div>
            <pre id="log"></pre>
        </div>
        
        <div id="database-tab" class="tab-content">
            <div class="controls">
                <button id="refreshTablesBtn">🔄 Обновить</button>
                <button id="dropAllTablesBtn" class="danger">🧨 Удалить все таблицы</button>
                <div class="meta" id="db-meta"></div>
            </div>
            <div id="tables-container" class="tables-list"></div>
            <div id="table-view-controls" style="display: none; margin-top: 24px; margin-bottom: 16px;">
                <button id="viewDataBtn" class="primary">📊 Данные</button>
                <button id="viewStructureBtn" class="secondary">🏗️ Структура</button>
            </div>
            <div id="table-data-container"></div>
        </div>
    </div>
    
    <script>
        // Tabs
        function switchTab(tab, element) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            if (element) element.classList.add('active');
            document.getElementById(tab + '-tab').classList.add('active');
            
            if (tab === 'database') {
                loadTables();
            }
        }
        
        // Инициализация обработчиков событий для вкладок
        document.addEventListener('DOMContentLoaded', function() {
            document.querySelectorAll('.tab').forEach(tab => {
                tab.addEventListener('click', function() {
                    const tabName = this.getAttribute('data-tab');
                    switchTab(tabName, this);
                });
            });
            
            // Обработчики для кнопок
            const pauseBtn = document.getElementById('pauseBtn');
            const clearBtn = document.getElementById('clearBtn');
            const filterBtn = document.getElementById('filterBtn');
            const refreshTablesBtn = document.getElementById('refreshTablesBtn');
            const dropAllTablesBtn = document.getElementById('dropAllTablesBtn');
            const viewDataBtn = document.getElementById('viewDataBtn');
            const viewStructureBtn = document.getElementById('viewStructureBtn');
            
            if (pauseBtn) pauseBtn.addEventListener('click', togglePause);
            if (clearBtn) clearBtn.addEventListener('click', clearLogs);
            if (filterBtn) filterBtn.addEventListener('click', toggleFilter);
            if (refreshTablesBtn) refreshTablesBtn.addEventListener('click', loadTables);
            if (dropAllTablesBtn) dropAllTablesBtn.addEventListener('click', dropAllTables);
            if (viewDataBtn) viewDataBtn.addEventListener('click', function() {
                if (currentTable) {
                    viewDataBtn.classList.remove('secondary');
                    viewDataBtn.classList.add('primary');
                    viewStructureBtn.classList.remove('primary');
                    viewStructureBtn.classList.add('secondary');
                    loadTableData(currentTable, 0);
                }
            });
            if (viewStructureBtn) viewStructureBtn.addEventListener('click', function() {
                if (currentTable) {
                    viewStructureBtn.classList.remove('secondary');
                    viewStructureBtn.classList.add('primary');
                    viewDataBtn.classList.remove('primary');
                    viewDataBtn.classList.add('secondary');
                    loadTableStructure(currentTable);
                }
            });
        });
        
        // Logs
        const logEl = document.getElementById('log');
        const metaEl = document.getElementById('meta');
        const pauseBtn = document.getElementById('pauseBtn');
        const filterBtn = document.getElementById('filterBtn');
        let isPaused = false;
        let filterMode = false; // false = все логи, true = только запросы/ответы
        let refreshInterval = null;
        let currentTable = null;
        let currentPage = 0;
        const pageSize = 50;
        let allLogs = ''; // Храним все логи для фильтрации
        
        function filterLogs(text) {
            const lines = text.split('\\n');
            // Убираем строки с запросами к /admin/logs/raw
            const cleaned = lines.filter(line => {
                return !/\\/admin\\/logs\\/raw/i.test(line);
            });
            
            if (!filterMode) {
                return cleaned.join('\\n');
            }
            
            // Фильтруем только строки с запросами и ответами
            const filtered = cleaned.filter(line => {
                const lowerLine = line.toLowerCase();
                return (
                    /(GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD)\\s+\\//.test(line) ||
                    /\\d{3}\\s+(OK|NOT FOUND|UNAUTHORIZED|FORBIDDEN|BAD REQUEST|INTERNAL SERVER ERROR|CREATED|NO CONTENT)/i.test(line) ||
                    /status code:\\s*\\d{3}/i.test(lowerLine) ||
                    /http.*\\d{3}/i.test(lowerLine) ||
                    /\\[.*\\]\\s*(GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD)\\s+\\//.test(line) ||
                    /request.*method/i.test(lowerLine) ||
                    /response.*status/i.test(lowerLine) ||
                    (/path.*=/i.test(lowerLine) && /(GET|POST|PUT|PATCH|DELETE)/i.test(line))
                );
            });
            
            return filtered.join('\\n');
        }
        
        async function refreshLogs() {
            if (isPaused) return;
            try {
                const response = await fetch('/admin/logs/raw?tail=20000', { cache: 'no-store' });
                if (!response.ok) {
                    throw new Error('Failed to fetch logs');
                }
                const text = await response.text();
                allLogs = text;
                
                if (logEl) {
                    const displayText = filterLogs(text);
                    logEl.textContent = displayText;
                    const status = filterMode ? ' (фильтр: только запросы/ответы)' : ' (все логи)';
                    metaEl.textContent = 'Последнее обновление: ' + new Date().toLocaleTimeString() + status;
                }
            } catch (error) {
                console.error('Error refreshing logs:', error);
                if (metaEl) metaEl.textContent = 'Ошибка обновления логов: ' + error.message;
            }
        }
        
        function toggleFilter() {
            filterMode = !filterMode;
            if (filterMode) {
                filterBtn.textContent = '📋 Все логи';
                filterBtn.classList.remove('secondary');
                filterBtn.classList.add('primary');
            } else {
                filterBtn.textContent = '🔍 Только запросы/ответы';
                filterBtn.classList.remove('primary');
                filterBtn.classList.add('secondary');
            }
            
            if (logEl && allLogs) {
                const displayText = filterLogs(allLogs);
                logEl.textContent = displayText;
                const status = filterMode ? ' (фильтр: только запросы/ответы)' : ' (все логи)';
                metaEl.textContent = 'Последнее обновление: ' + new Date().toLocaleTimeString() + status;
            }
        }
        
        function togglePause() {
            isPaused = !isPaused;
            if (isPaused) {
                if (refreshInterval) {
                    clearInterval(refreshInterval);
                    refreshInterval = null;
                }
                pauseBtn.textContent = '▶️ Возобновить';
                pauseBtn.classList.add('paused');
                metaEl.textContent = 'Обновление приостановлено - можно копировать логи';
            } else {
                refreshInterval = setInterval(refreshLogs, 2000);
                pauseBtn.textContent = '⏸️ Пауза';
                pauseBtn.classList.remove('paused');
                metaEl.textContent = 'Auto-refreshing...';
                refreshLogs();
            }
        }
        
        async function clearLogs() {
            if (!confirm('Вы уверены, что хотите очистить логи?')) return;
            try {
                const response = await fetch('/admin/logs/clear', { method: 'POST' });
                if (response.ok) {
                    logEl.textContent = '';
                    metaEl.textContent = 'Логи очищены: ' + new Date().toLocaleTimeString();
                    if (!isPaused) setTimeout(refreshLogs, 500);
                } else {
                    alert('Ошибка при очистке логов.');
                }
            } catch (error) {
                alert('Ошибка при очистке логов.');
            }
        }
        
        // Database
        async function loadTables() {
            const container = document.getElementById('tables-container');
            container.innerHTML = '<div class="loading">Загрузка таблиц...</div>';
            
            try {
                const response = await fetch('/admin/db/tables');
                const tables = await response.json();
                
                if (tables.length === 0) {
                    container.innerHTML = '<div class="empty-state"><p>Таблицы не найдены</p></div>';
                    return;
                }
                
                container.innerHTML = '';
                for (const table of tables) {
                    const card = document.createElement('div');
                    card.className = 'table-card';
                    card.onclick = (e) => selectTable(table.name, table.count, card);
                    card.innerHTML = `
                        <h3>${table.name}</h3>
                        <p>${table.count} записей</p>
                    `;
                    container.appendChild(card);
                }
            } catch (error) {
                container.innerHTML = '<div class="empty-state"><p>Ошибка загрузки таблиц</p></div>';
            }
        }
        
        async function selectTable(tableName, count, cardElement) {
            currentTable = tableName;
            currentPage = 0;
            
            document.querySelectorAll('.table-card').forEach(c => c.classList.remove('active'));
            if (cardElement) {
                cardElement.classList.add('active');
            }
            
            document.getElementById('table-view-controls').style.display = 'flex';
            document.getElementById('viewDataBtn').classList.remove('secondary');
            document.getElementById('viewDataBtn').classList.add('primary');
            document.getElementById('viewStructureBtn').classList.remove('primary');
            document.getElementById('viewStructureBtn').classList.add('secondary');
            
            await loadTableData(tableName, 0);
        }
        
        async function loadTableStructure(tableName) {
            const container = document.getElementById('table-data-container');
            container.innerHTML = '<div class="loading">Загрузка структуры...</div>';
            
            try {
                const encodedTableName = encodeURIComponent(tableName);
                const response = await fetch(`/admin/db/table/${encodedTableName}/structure`);
                if (!response.ok) {
                    throw new Error('Failed to fetch table structure');
                }
                const columns = await response.json();
                
                if (columns.length === 0) {
                    container.innerHTML = '<div class="empty-state"><p>Структура не найдена</p></div>';
                    return;
                }
                
                let html = '<div class="controls" style="margin-top: 24px;"><button class="danger delete-table-btn" data-table="' + tableName + '">🗑️ Удалить таблицу</button></div>';
                html += '<div class="table-wrapper"><table class="data-table"><thead><tr>';
                html += '<th>Поле</th><th>Тип</th><th>Nullable</th>';
                html += '</tr></thead><tbody>';
                
                columns.forEach(col => {
                    html += '<tr>';
                    html += `<td><strong>${col.name}</strong></td>`;
                    html += `<td>${col.type}</td>`;
                    html += `<td>${col.nullable ? '<span class="badge badge-success">Да</span>' : '<span class="badge badge-danger">Нет</span>'}</td>`;
                    html += '</tr>';
                });
                
                html += '</tbody></table></div>';
                container.innerHTML = html;
                
                // Привязываем обработчик для кнопки удаления
                container.querySelectorAll('.delete-table-btn').forEach(btn => {
                    btn.addEventListener('click', function() {
                        deleteTable(this.getAttribute('data-table'));
                    });
                });
            } catch (error) {
                container.innerHTML = '<div class="empty-state"><p>Ошибка загрузки структуры</p></div>';
            }
        }
        
        async function loadTableData(tableName, page) {
            currentPage = page;
            const container = document.getElementById('table-data-container');
            container.innerHTML = '<div class="loading">Загрузка данных...</div>';
            
            try {
                const encodedTableName = encodeURIComponent(tableName);
                const response = await fetch(`/admin/db/table/${encodedTableName}?limit=${pageSize}&offset=${page * pageSize}`);
                if (!response.ok) {
                    throw new Error('Failed to fetch table data');
                }
                const data = await response.json();
                
                // Всегда показываем кнопку удаления таблицы
                let html = '<div class="controls" style="margin-top: 24px;"><button class="danger delete-table-btn" data-table="' + tableName + '">🗑️ Удалить таблицу</button></div>';
                
                if (data.length === 0) {
                    html += '<div class="empty-state"><p>Таблица пуста</p></div>';
                    container.innerHTML = html;
                    
                    // Привязываем обработчик для кнопки удаления
                    container.querySelectorAll('.delete-table-btn').forEach(btn => {
                        btn.addEventListener('click', function() {
                            deleteTable(this.getAttribute('data-table'));
                        });
                    });
                    return;
                }
                
                const columns = Object.keys(data[0]);
                html += '<div class="table-wrapper"><table class="data-table"><thead><tr>';
                columns.forEach(col => html += `<th>${col}</th>`);
                html += '<th>Действия</th></tr></thead><tbody>';
                
                data.forEach(row => {
                    html += '<tr>';
                    columns.forEach(col => {
                        let value = row[col];
                        if (value === null) value = '<span style="color: #9ca3af;">NULL</span>';
                        else if (typeof value === 'object') value = JSON.stringify(value);
                        else if (typeof value === 'boolean') value = value ? '<span class="badge badge-success">Да</span>' : '<span class="badge badge-danger">Нет</span>';
                        html += `<td>${value}</td>`;
                    });
                    const idValue = String(row[columns[0]]);
                    html += `<td><button class="action-btn danger delete-record-btn" data-table="${tableName}" data-column="${columns[0]}" data-value="${idValue.replace(/"/g, '&quot;')}">Удалить</button></td>`;
                    html += '</tr>';
                });
                
                html += '</tbody></table></div>';
                
                const countResponse = await fetch(`/admin/db/table/${encodeURIComponent(tableName)}/count`);
                if (!countResponse.ok) {
                    throw new Error('Failed to fetch count');
                }
                const totalCount = await countResponse.json();
                const totalPages = Math.ceil(totalCount / pageSize);
                
                if (totalPages > 1) {
                    html += '<div class="pagination">';
                    if (page > 0) html += `<button class="page-btn" data-table="${tableName}" data-page="${page - 1}">←</button>`;
                    html += `<span>Страница ${page + 1} из ${totalPages}</span>`;
                    if (page < totalPages - 1) html += `<button class="page-btn" data-table="${tableName}" data-page="${page + 1}">→</button>`;
                    html += '</div>';
                }
                
                container.innerHTML = html;
                
                // Привязываем обработчики событий для новых элементов
                container.querySelectorAll('.delete-table-btn').forEach(btn => {
                    btn.addEventListener('click', function() {
                        deleteTable(this.getAttribute('data-table'));
                    });
                });
                
                container.querySelectorAll('.delete-record-btn').forEach(btn => {
                    btn.addEventListener('click', function() {
                        deleteRecord(
                            this.getAttribute('data-table'),
                            this.getAttribute('data-column'),
                            this.getAttribute('data-value')
                        );
                    });
                });
                
                container.querySelectorAll('.page-btn').forEach(btn => {
                    btn.addEventListener('click', function() {
                        loadTableData(
                            this.getAttribute('data-table'),
                            parseInt(this.getAttribute('data-page'))
                        );
                    });
                });
            } catch (error) {
                container.innerHTML = '<div class="empty-state"><p>Ошибка загрузки данных</p></div>';
            }
        }
        
        async function deleteRecord(tableName, idColumn, idValue) {
            if (!confirm(`Удалить запись ${idColumn}=${idValue}?`)) return;
            try {
                const encodedTableName = encodeURIComponent(tableName);
                const encodedIdColumn = encodeURIComponent(idColumn);
                const encodedIdValue = encodeURIComponent(idValue);
                const response = await fetch(`/admin/db/table/${encodedTableName}/record/${encodedIdColumn}/${encodedIdValue}`, { method: 'DELETE' });
                if (response.ok) {
                    alert('Запись удалена');
                    await loadTableData(tableName, currentPage);
                    await loadTables();
                } else {
                    const error = await response.json();
                    alert('Ошибка: ' + (error.detail || 'Unknown error'));
                }
            } catch (error) {
                alert('Ошибка при удалении записи: ' + error.message);
            }
        }
        
        async function deleteTable(tableName) {
            if (!confirm(`ВНИМАНИЕ! Вы уверены, что хотите полностью удалить таблицу "${tableName}"? Это действие необратимо!`)) return;
            if (!confirm('Это удалит ВСЕ данные в таблице. Продолжить?')) return;
            try {
                const encodedTableName = encodeURIComponent(tableName);
                const response = await fetch(`/admin/db/table/${encodedTableName}`, { method: 'DELETE' });
                if (response.ok) {
                    alert('Таблица удалена');
                    document.getElementById('table-data-container').innerHTML = '';
                    await loadTables();
                } else {
                    const error = await response.json();
                    alert('Ошибка: ' + (error.detail || 'Unknown error'));
                }
            } catch (error) {
                alert('Ошибка при удалении таблицы: ' + error.message);
            }
        }

        async function dropAllTables() {
            if (!confirm('ВНИМАНИЕ! Это удалит ВСЕ таблицы и данные в базе. Продолжить?')) return;
            if (!confirm('Это действие необратимо. Точно удалить все таблицы?')) return;
            try {
                const response = await fetch('/admin/db/tables', { method: 'DELETE' });
                if (response.ok) {
                    alert('Все таблицы удалены');
                    document.getElementById('table-data-container').innerHTML = '';
                    await loadTables();
                } else {
                    const error = await response.json();
                    alert('Ошибка: ' + (error.detail || 'Unknown error'));
                }
            } catch (error) {
                alert('Ошибка при удалении таблиц: ' + error.message);
            }
        }
        
        // Initialize
        if (logEl && metaEl) {
            refreshLogs();
            refreshInterval = setInterval(refreshLogs, 2000);
        }
    </script>
</body>
</html>"""
    return HTMLResponse(content=body)


def _api_log_file() -> str:
    return os.getenv("API_LOG_FILE") or os.getenv("LOG_FILE", "python-project/app/logs/server.log")


@router.get("/logs/raw", response_class=HTMLResponse)
def raw_logs(tail: int = Query(20000, ge=0, le=200000)) -> HTMLResponse:
    return HTMLResponse(content=_read_log(_api_log_file(), tail=tail))


@router.post("/logs/clear")
def clear_logs() -> JSONResponse:
    log_file = _api_log_file()
    try:
        if os.path.exists(log_file):
            with open(log_file, "w", encoding="utf-8") as handle:
                handle.write("")
        return JSONResponse(content={"message": "Logs cleared successfully"})
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"message": f"Error clearing logs: {str(e)}"}
        )


@router.get("/db/tables")
def get_tables(db: Session = Depends(get_db)) -> JSONResponse:
    """Получает список всех таблиц с количеством записей."""
    try:
        tables = _get_table_names()
        result = []
        for table_name in tables:
            count = _get_table_count(table_name, db)
            result.append({"name": table_name, "count": count})
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": f"Error fetching tables: {str(e)}"}
        )


@router.get("/db/table/{table_name}")
def get_table_data(
    table_name: str,
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
) -> JSONResponse:
    """Получает данные из таблицы."""
    if table_name not in _get_table_names():
        raise HTTPException(status_code=404, detail="Table not found")
    try:
        data = _get_table_data(table_name, db, limit, offset)
        # Преобразуем UUID и datetime в строки для JSON
        for row in data:
            for key, value in row.items():
                if hasattr(value, '__str__'):
                    try:
                        row[key] = str(value)
                    except:
                        pass
        return JSONResponse(content=data)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": f"Error fetching data: {str(e)}"}
        )


@router.get("/db/table/{table_name}/count")
def get_table_count(table_name: str, db: Session = Depends(get_db)) -> JSONResponse:
    """Получает количество записей в таблице."""
    if table_name not in _get_table_names():
        raise HTTPException(status_code=404, detail="Table not found")
    try:
        count = _get_table_count(table_name, db)
        return JSONResponse(content=count)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": f"Error counting records: {str(e)}"}
        )


@router.get("/db/table/{table_name}/structure")
def get_table_structure(table_name: str) -> JSONResponse:
    """Получает структуру таблицы (колонки и их типы)."""
    if table_name not in _get_table_names():
        raise HTTPException(status_code=404, detail="Table not found")
    try:
        columns = _get_table_columns(table_name)
        return JSONResponse(content=columns)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": f"Error fetching structure: {str(e)}"}
        )


@router.delete("/db/table/{table_name}/record/{id_column}/{id_value}")
def delete_record(
    table_name: str,
    id_column: str,
    id_value: str,
    db: Session = Depends(get_db)
) -> JSONResponse:
    """Удаляет запись из таблицы."""
    if table_name not in _get_table_names():
        raise HTTPException(status_code=404, detail="Table not found")
    try:
        # Безопасное удаление через параметризованный запрос
        db.execute(text(f'DELETE FROM "{table_name}" WHERE "{id_column}" = :id_value'), {"id_value": id_value})
        db.commit()
        return JSONResponse(content={"message": "Record deleted successfully"})
    except Exception as e:
        db.rollback()
        return JSONResponse(
            status_code=500,
            content={"detail": f"Error deleting record: {str(e)}"}
        )


@router.delete("/db/table/{table_name}")
def delete_table(table_name: str, db: Session = Depends(get_db)) -> JSONResponse:
    """Полностью удаляет таблицу."""
    if table_name not in _get_table_names():
        raise HTTPException(status_code=404, detail="Table not found")
    
    # Защита от удаления системных таблиц
    protected_tables = ['alembic_version']
    if table_name in protected_tables:
        raise HTTPException(status_code=403, detail="Cannot delete protected table")
    
    try:
        db.execute(text(f'DROP TABLE IF EXISTS "{table_name}" CASCADE'))
        db.commit()
        return JSONResponse(content={"message": f"Table {table_name} deleted successfully"})
    except Exception as e:
        db.rollback()
        return JSONResponse(
            status_code=500,
            content={"detail": f"Error deleting table: {str(e)}"}
        )


@router.delete("/db/tables")
def delete_all_tables(db: Session = Depends(get_db)) -> JSONResponse:
    """Полностью удаляет все таблицы кроме защищённых."""
    protected_tables = {"alembic_version"}
    try:
        tables = _get_table_names()
        for table_name in tables:
            if table_name in protected_tables:
                continue
            db.execute(text(f'DROP TABLE IF EXISTS "{table_name}" CASCADE'))
        db.commit()
        return JSONResponse(content={"message": "All tables deleted successfully"})
    except Exception as e:
        db.rollback()
        return JSONResponse(
            status_code=500,
            content={"detail": f"Error deleting tables: {str(e)}"}
        )

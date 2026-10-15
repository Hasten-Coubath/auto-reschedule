"""Servidor HTTP local (somente biblioteca padrão do Python).

Serve a interface (pasta ``web/``) e uma API JSON em ``/api``. Escuta apenas
em 127.0.0.1, ou seja, só o seu próprio computador consegue acessar.
"""

from __future__ import annotations

import json
import mimetypes
import re
import sys
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from . import core
from .storage import Store

APP_ID = "auto-reschedule"
# No executável do PyInstaller os arquivos da interface ficam em sys._MEIPASS.
WEB_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent)).resolve() / "web"
MAX_BODY = 1_000_000
# Pedidos que alteram dados precisam deste cabeçalho. Um site qualquer aberto
# no navegador não consegue enviá-lo para cá sem permissão (CORS), o que
# impede que páginas de terceiros mexam nas suas tarefas.
GUARD_HEADER = "X-Auto-Reschedule"
# O registro do Windows às vezes informa tipos errados (ex.: .js como text/plain).
CONTENT_TYPES = {
    ".html": "text/html",
    ".css": "text/css",
    ".js": "application/javascript",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".ico": "image/x-icon",
    ".webmanifest": "application/manifest+json",
}


class ApiError(Exception):
    def __init__(self, status: HTTPStatus, message: str):
        super().__init__(message)
        self.status = status
        self.message = message


class Api:
    """Rotas da API. Cada rota recebe (params, query, body) e devolve um dict."""

    def __init__(self, store: Store):
        self.store = store
        self.server: ThreadingHTTPServer | None = None
        self.routes: list[tuple[str, re.Pattern, callable]] = []
        add = self._add
        add("GET", r"/api/ping", self.ping)
        add("GET", r"/api/state", self.get_state)
        add("GET", r"/api/export", self.export)
        add("POST", r"/api/shutdown", self.shutdown)
        add("PATCH", r"/api/settings", self.update_settings)
        add("POST", r"/api/tasks", self.create_task)
        add("PATCH", r"/api/tasks/(?P<id>\w+)", self.update_task)
        add("DELETE", r"/api/tasks/(?P<id>\w+)", self.delete_task)
        add("POST", r"/api/tasks/(?P<id>\w+)/complete", self.complete_task)
        add("POST", r"/api/tasks/(?P<id>\w+)/reopen", self.reopen_task)
        add("POST", r"/api/tasks/(?P<id>\w+)/subtasks", self.add_subtask)
        add("DELETE", r"/api/tasks/(?P<id>\w+)/subtasks/(?P<sub>\w+)", self.remove_subtask)
        add("POST", r"/api/tasks/(?P<id>\w+)/subtasks/(?P<sub>\w+)/toggle", self.toggle_subtask)
        add("POST", r"/api/routines", self.create_routine)
        add("PATCH", r"/api/routines/(?P<id>\w+)", self.update_routine)
        add("DELETE", r"/api/routines/(?P<id>\w+)", self.delete_routine)
        add("GET", r"/api/routines/(?P<id>\w+)/history", self.routine_history)
        add("POST", r"/api/routines/(?P<id>\w+)/entries", self.add_entry)
        add("DELETE", r"/api/routines/(?P<id>\w+)/entries/(?P<entry>\w+)", self.remove_entry)
        add("POST", r"/api/routines/(?P<id>\w+)/pause", self.pause_routine)
        add("POST", r"/api/routines/(?P<id>\w+)/resume", self.resume_routine)
        add("POST", r"/api/routines/(?P<id>\w+)/timer/(?P<action>start|pause|stop|cancel)", self.timer)

    def _add(self, method: str, pattern: str, handler) -> None:
        self.routes.append((method, re.compile(pattern + r"/?"), handler))

    def dispatch(self, method: str, path: str, query: dict, body: dict) -> dict:
        path_matched = False
        for route_method, pattern, handler in self.routes:
            match = pattern.fullmatch(path)
            if not match:
                continue
            path_matched = True
            if route_method == method:
                try:
                    return handler(match.groupdict(), query, body)
                except core.ValidationError as exc:
                    raise ApiError(HTTPStatus.BAD_REQUEST, str(exc)) from None
                except core.NotFoundError as exc:
                    raise ApiError(HTTPStatus.NOT_FOUND, str(exc)) from None
        if path_matched:
            raise ApiError(HTTPStatus.METHOD_NOT_ALLOWED, "Método não permitido.")
        raise ApiError(HTTPStatus.NOT_FOUND, "Rota não encontrada.")

    # -- utilitários ------------------------------------------------------

    @staticmethod
    def _day(query: dict, today_):
        value = query.get("date", [None])[0]
        return core.parse_date(value) if value else today_

    # -- geral ------------------------------------------------------------

    def ping(self, params, query, body):
        return {"app": APP_ID}

    def get_state(self, params, query, body):
        today_ = core.today()
        with self.store.read() as data:
            return core.build_state(data, self._day(query, today_), today_)

    def export(self, params, query, body):
        return self.store.export()

    def shutdown(self, params, query, body):
        if self.server is not None:
            threading.Thread(target=self.server.shutdown, daemon=True).start()
        return {"ok": True}

    def update_settings(self, params, query, body):
        with self.store.write() as data:
            return core.update_settings(data, body)

    # -- tarefas ----------------------------------------------------------

    def create_task(self, params, query, body):
        today_ = core.today()
        with self.store.write() as data:
            task = core.make_task(body, default_date=today_)
            data["tasks"].append(task)
            return task

    def update_task(self, params, query, body):
        with self.store.write() as data:
            task = core.find(data["tasks"], params["id"], "Tarefa")
            core.update_task(task, body)
            return task

    def delete_task(self, params, query, body):
        with self.store.write() as data:
            data["tasks"].remove(core.find(data["tasks"], params["id"], "Tarefa"))
            return {"ok": True}

    def complete_task(self, params, query, body):
        today_ = core.today()
        with self.store.write() as data:
            task = core.find(data["tasks"], params["id"], "Tarefa")
            core.complete_task(task, core.parse_date(body.get("date") or today_), today_)
            return task

    def reopen_task(self, params, query, body):
        today_ = core.today()
        with self.store.write() as data:
            task = core.find(data["tasks"], params["id"], "Tarefa")
            core.reopen_task(task, core.parse_date(body.get("date") or today_))
            return task

    def add_subtask(self, params, query, body):
        with self.store.write() as data:
            task = core.find(data["tasks"], params["id"], "Tarefa")
            return core.add_subtask(task, body)

    def remove_subtask(self, params, query, body):
        with self.store.write() as data:
            task = core.find(data["tasks"], params["id"], "Tarefa")
            core.remove_subtask(task, params["sub"])
            return {"ok": True}

    def toggle_subtask(self, params, query, body):
        today_ = core.today()
        with self.store.write() as data:
            task = core.find(data["tasks"], params["id"], "Tarefa")
            return {"task_change": core.toggle_subtask(task, params["sub"], body, today_=today_)}

    # -- rotinas ----------------------------------------------------------

    def create_routine(self, params, query, body):
        today_ = core.today()
        with self.store.write() as data:
            routine = core.make_routine(body, today_=today_)
            data["routines"].append(routine)
            return core._public(routine)

    def update_routine(self, params, query, body):
        today_ = core.today()
        with self.store.write() as data:
            routine = core.find(data["routines"], params["id"], "Rotina")
            core.update_routine(routine, body, today_=today_)
            return core._public(routine)

    def delete_routine(self, params, query, body):
        with self.store.write() as data:
            data["routines"].remove(core.find(data["routines"], params["id"], "Rotina"))
            return {"ok": True}

    def routine_history(self, params, query, body):
        today_ = core.today()
        try:
            limit = max(1, min(365, int(query.get("days", ["30"])[0])))
        except ValueError:
            limit = 30
        with self.store.read() as data:
            routine = core.find(data["routines"], params["id"], "Rotina")
            return core.routine_history(routine, self._day(query, today_), limit)

    def add_entry(self, params, query, body):
        today_ = core.today()
        with self.store.write() as data:
            routine = core.find(data["routines"], params["id"], "Rotina")
            return core.add_entry(routine, body, today_=today_)

    def remove_entry(self, params, query, body):
        with self.store.write() as data:
            routine = core.find(data["routines"], params["id"], "Rotina")
            core.remove_entry(routine, params["entry"])
            return {"ok": True}

    def pause_routine(self, params, query, body):
        today_ = core.today()
        with self.store.write() as data:
            routine = core.find(data["routines"], params["id"], "Rotina")
            core.pause_routine(routine, today_=today_)
            return {"ok": True}

    def resume_routine(self, params, query, body):
        today_ = core.today()
        with self.store.write() as data:
            routine = core.find(data["routines"], params["id"], "Rotina")
            core.resume_routine(routine, today_=today_)
            return {"ok": True}

    def timer(self, params, query, body):
        today_, at = core.today(), core.now()
        with self.store.write() as data:
            routine = core.find(data["routines"], params["id"], "Rotina")
            action = params["action"]
            if action == "start":
                return {"timer": core.timer_start(routine, today_=today_, at=at)}
            if action == "pause":
                return {"timer": core.timer_pause(routine, at=at)}
            if action == "stop":
                return {"entry": core.timer_stop(routine, body, today_=today_, at=at)}
            core.timer_cancel(routine)
            return {"ok": True}


class Handler(BaseHTTPRequestHandler):
    server_version = "AutoReschedule/1.1"
    api: Api  # definido em create_server

    def do_GET(self):
        self._handle("GET")

    def do_POST(self):
        self._handle("POST")

    def do_PATCH(self):
        self._handle("PATCH")

    def do_DELETE(self):
        self._handle("DELETE")

    def log_message(self, format, *args):  # noqa: A002 - silencia o log de cada requisição
        pass

    def _handle(self, method: str) -> None:
        url = urlparse(self.path)
        try:
            self._check_host()
            if url.path.startswith("/api/"):
                if method != "GET" and self.headers.get(GUARD_HEADER) != "1":
                    raise ApiError(HTTPStatus.FORBIDDEN, "Requisição recusada.")
                body = self._read_json() if method in ("POST", "PATCH") else {}
                payload = self.api.dispatch(method, url.path, parse_qs(url.query), body)
                extra = {}
                if url.path.rstrip("/") == "/api/export":
                    extra["Content-Disposition"] = 'attachment; filename="auto-reschedule-backup.json"'
                self._send_json(HTTPStatus.OK, payload, extra)
            elif method == "GET":
                self._serve_static(url.path)
            else:
                raise ApiError(HTTPStatus.METHOD_NOT_ALLOWED, "Método não permitido.")
        except ApiError as exc:
            self._send_json(exc.status, {"error": exc.message})
        except Exception as exc:  # pragma: no cover - rede de segurança
            self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": f"Erro interno: {exc}"})
            raise

    def _check_host(self) -> None:
        # Protege contra "DNS rebinding": só aceita acessos endereçados ao próprio PC.
        host = (self.headers.get("Host") or "").rsplit(":", 1)[0].strip("[]")
        if host not in ("127.0.0.1", "localhost", "::1"):
            raise ApiError(HTTPStatus.FORBIDDEN, "Host não permitido.")

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        if length > MAX_BODY:
            raise ApiError(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "Requisição grande demais.")
        raw = self.rfile.read(length) if length else b""
        if not raw:
            return {}
        try:
            body = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ApiError(HTTPStatus.BAD_REQUEST, "JSON inválido.") from None
        if not isinstance(body, dict):
            raise ApiError(HTTPStatus.BAD_REQUEST, "O corpo deve ser um objeto JSON.")
        return body

    def _send_json(self, status: HTTPStatus, payload, extra_headers: dict | None = None) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        for key, value in (extra_headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(data)

    def _serve_static(self, path: str) -> None:
        relative = "index.html" if path in ("", "/") else path.lstrip("/")
        target = (WEB_DIR / relative).resolve()
        if not target.is_relative_to(WEB_DIR) or not target.is_file():
            raise ApiError(HTTPStatus.NOT_FOUND, "Arquivo não encontrado.")
        data = target.read_bytes()
        ctype = CONTENT_TYPES.get(target.suffix.lower()) or mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        if ctype.startswith("text/") or ctype in ("application/javascript", "image/svg+xml", "application/manifest+json"):
            ctype += "; charset=utf-8"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(data)


def create_server(store: Store, port: int, host: str = "127.0.0.1") -> ThreadingHTTPServer:
    api = Api(store)
    handler = type("BoundHandler", (Handler,), {"api": api})
    server = ThreadingHTTPServer((host, port), handler)
    server.daemon_threads = True
    api.server = server
    return server

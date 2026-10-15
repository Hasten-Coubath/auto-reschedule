"""Persistência em um arquivo JSON local, com gravação atômica e backups diários."""

from __future__ import annotations

import copy
import json
import os
import shutil
import threading
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path

SCHEMA_VERSION = 2
BACKUPS_TO_KEEP = 14


def empty_data() -> dict:
    return {"version": SCHEMA_VERSION, "tasks": [], "routines": [], "settings": {}}


def migrate(data: dict) -> dict:
    """Completa arquivos de versões anteriores com os campos novos."""
    data.setdefault("tasks", [])
    data.setdefault("routines", [])
    data.setdefault("settings", {})
    for task in data["tasks"]:
        task.setdefault("priority", "normal")
        task.setdefault("tags", [])
        task.setdefault("subtasks", [])
        task.setdefault("repeat", None)
        task.setdefault("completions", {})
    for routine in data["routines"]:
        routine.setdefault("pauses", [])
        routine.setdefault("timer", None)
    data["version"] = SCHEMA_VERSION
    return data


class Store:
    """Mantém os dados em memória e grava no disco a cada alteração.

    Use ``with store.read() as data`` para consultar e
    ``with store.write() as data`` para alterar: se der erro no meio,
    a alteração é desfeita e nada é gravado.
    """

    def __init__(self, path: str | os.PathLike):
        self.path = Path(path)
        self.backup_dir = self.path.parent / "backups"
        self._lock = threading.RLock()
        self._data = self._load()

    def _load(self) -> dict:
        if not self.path.exists():
            return empty_data()
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError("raiz do JSON não é um objeto")
        except (json.JSONDecodeError, ValueError):
            # Não apaga nada: guarda o arquivo problemático e começa do zero.
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            broken = self.path.with_name(f"{self.path.stem}.corrompido-{stamp}{self.path.suffix}")
            self.path.rename(broken)
            print(f"[aviso] {self.path.name} estava corrompido e foi renomeado para {broken.name}")
            return empty_data()
        return migrate(data)

    @contextmanager
    def read(self):
        with self._lock:
            yield self._data

    @contextmanager
    def write(self):
        with self._lock:
            before = copy.deepcopy(self._data)
            try:
                yield self._data
            except BaseException:
                self._data = before
                raise
            self._save()

    def export(self) -> dict:
        with self._lock:
            return copy.deepcopy(self._data)

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._backup_once_a_day()
        tmp = self.path.with_name(self.path.name + ".tmp")
        tmp.write_text(json.dumps(self._data, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, self.path)

    def _backup_once_a_day(self) -> None:
        if not self.path.exists():
            return
        target = self.backup_dir / f"{self.path.stem}-{date.today().isoformat()}{self.path.suffix}"
        if target.exists():
            return
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(self.path, target)
        backups = sorted(self.backup_dir.glob(f"{self.path.stem}-*{self.path.suffix}"))
        for old in backups[:-BACKUPS_TO_KEEP]:
            old.unlink(missing_ok=True)

"""Regras de negócio do Auto Reschedule.

Existem dois tipos de item:

* **Tarefas** (``tasks``): têm uma data. Enquanto não forem concluídas,
  continuam aparecendo em todos os dias seguintes, com a indicação de há
  quantos dias estão atrasadas. Podem ter prioridade, etiquetas, subtarefas
  e se repetir (tarefas recorrentes simples, sem acúmulo: cada repetição
  pendente passa para o dia seguinte só até a próxima repetição chegar).
* **Rotinas acumulativas** (``routines``): têm uma meta por dia (ex.: 60 min
  de estudo). O que não for feito vira *dívida* e soma na meta do dia
  seguinte; o que for feito a mais vira *saldo*, que pode ser gasto depois
  para cobrir uma pendência.

Nada é gravado "virando o dia": o estado de qualquer data é sempre
recalculado a partir dos registros, então o app funciona mesmo que fique dias
fechado. Este módulo é puro (sem I/O) para facilitar os testes.
"""

from __future__ import annotations

import calendar
import math
import os
import re
import uuid
from datetime import date, datetime, timedelta

EPS = 1e-9
ALL_WEEKDAYS = [0, 1, 2, 3, 4, 5, 6]  # 0 = segunda ... 6 = domingo
UNITS = ("time", "count")  # "time" é medido em minutos
ENTRY_TYPES = ("progress", "spend", "skip")

TASK_ORDER = {"pending": 0, "rolled": 0, "missed": 0, "planned": 0, "done": 1}
PRIORITIES = ("high", "normal", "low")
PRIORITY_ORDER = {"high": 0, "normal": 1, "low": 2}
MAX_TAGS = 10
MAX_SUBTASKS = 50
REPEAT_LOOKBACK = 400  # quantos dias a busca da repetição vigente olha para trás

DEFAULT_SETTINGS = {
    "notify_end_of_day": True,  # lembrete do que ficou pendente no fim do dia
    "notify_time": "20:00",
    "notify_timer": True,  # avisa quando o cronômetro atinge a meta do dia
    "sound": True,
}


class ValidationError(ValueError):
    """Erro causado por dado inválido enviado pelo usuário (vira HTTP 400)."""


class NotFoundError(LookupError):
    """Item não encontrado (vira HTTP 404)."""


# ---------------------------------------------------------------------------
# Utilitários
# ---------------------------------------------------------------------------


def today() -> date:
    """Data de hoje. ``AUTO_RESCHEDULE_TODAY`` permite simular outro dia."""
    forced = os.environ.get("AUTO_RESCHEDULE_TODAY")
    if forced:
        return parse_date(forced)
    return date.today()


def parse_date(value) -> date:
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        raise ValidationError(f"Data inválida: {value!r}") from None


def new_id() -> str:
    return uuid.uuid4().hex[:12]


def now() -> datetime:
    return datetime.now().replace(microsecond=0)


def now_iso() -> str:
    return now().isoformat(timespec="seconds")


def _num(value: float) -> float:
    """Arredonda para evitar lixo de ponto flutuante acumulando ao longo dos dias."""
    return round(float(value), 6)


def _clean_title(value) -> str:
    title = str(value or "").strip()
    if not title:
        raise ValidationError("O título não pode ficar vazio.")
    if len(title) > 200:
        raise ValidationError("O título pode ter no máximo 200 caracteres.")
    return title


def _clean_notes(value) -> str:
    notes = str(value or "").strip()
    if len(notes) > 2000:
        raise ValidationError("As anotações podem ter no máximo 2000 caracteres.")
    return notes


def _clean_amount(value, what: str = "Quantidade") -> float:
    try:
        amount = float(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{what} inválida.") from None
    if not math.isfinite(amount) or amount <= 0:
        raise ValidationError(f"{what} precisa ser maior que zero.")
    return _num(amount)


def _clean_optional_amount(value, what: str) -> float | None:
    if value is None or value == "":
        return None
    return _clean_amount(value, what)


def _clean_weekdays(value) -> list[int]:
    try:
        days = sorted({int(d) for d in value})
    except (TypeError, ValueError):
        raise ValidationError("Dias da semana inválidos.") from None
    if not days:
        raise ValidationError("Escolha pelo menos um dia da semana.")
    if any(d < 0 or d > 6 for d in days):
        raise ValidationError("Dias da semana devem estar entre 0 (segunda) e 6 (domingo).")
    return days


def _clean_priority(value) -> str:
    priority = value or "normal"
    if priority not in PRIORITIES:
        raise ValidationError("Prioridade inválida (use 'high', 'normal' ou 'low').")
    return priority


def _clean_tags(value) -> list[str]:
    """Aceita lista ou texto separado por vírgulas. Remove '#', vazios e repetidos."""
    if value is None or value == "":
        return []
    if isinstance(value, str):
        value = value.split(",")
    if not isinstance(value, list):
        raise ValidationError("Etiquetas inválidas.")
    tags: list[str] = []
    seen: set[str] = set()
    for raw in value:
        tag = re.sub(r"\s+", " ", str(raw or "").strip().lstrip("#").strip())
        if not tag:
            continue
        if len(tag) > 30:
            raise ValidationError("Cada etiqueta pode ter no máximo 30 caracteres.")
        if tag.casefold() not in seen:
            seen.add(tag.casefold())
            tags.append(tag)
    if len(tags) > MAX_TAGS:
        raise ValidationError(f"Use no máximo {MAX_TAGS} etiquetas por tarefa.")
    return tags


def _clean_int(value, what: str, low: int, high: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{what} inválido.") from None
    if not low <= number <= high:
        raise ValidationError(f"{what} deve estar entre {low} e {high}.")
    return number


def find(items: list[dict], item_id: str, what: str) -> dict:
    for item in items:
        if item["id"] == item_id:
            return item
    raise NotFoundError(f"{what} não encontrada.")


# ---------------------------------------------------------------------------
# Tarefas avulsas
# ---------------------------------------------------------------------------


def _clean_repeat(value, start: date) -> dict | None:
    """Regra de repetição: semanal (dias da semana), mensal (dia do mês) ou a cada N dias."""
    if not value:
        return None
    if not isinstance(value, dict):
        raise ValidationError("Repetição inválida.")
    kind = value.get("type")
    if kind == "weekly":
        repeat = {"type": "weekly", "weekdays": _clean_weekdays(value.get("weekdays", ALL_WEEKDAYS))}
    elif kind == "monthly":
        repeat = {"type": "monthly", "day": _clean_int(value.get("day", start.day), "Dia do mês", 1, 31)}
    elif kind == "interval":
        repeat = {"type": "interval", "every": _clean_int(value.get("every", 1), "Intervalo de dias", 1, 365)}
    else:
        raise ValidationError("Tipo de repetição inválido (use 'weekly', 'monthly' ou 'interval').")
    until = value.get("until")
    repeat["until"] = None
    if until:
        until = parse_date(until)
        if until < start:
            raise ValidationError("O fim da repetição é anterior ao início.")
        repeat["until"] = until.isoformat()
    return repeat


def _make_subtask(title) -> dict:
    return {"id": new_id(), "title": _clean_title(title), "done_on": None}


def _set_subtasks(task: dict, items) -> None:
    """Substitui a lista de subtarefas, mantendo o estado das que já existiam (pelo id)."""
    if not isinstance(items, list):
        raise ValidationError("Subtarefas inválidas.")
    if len(items) > MAX_SUBTASKS:
        raise ValidationError(f"Use no máximo {MAX_SUBTASKS} subtarefas.")
    current = {sub["id"]: sub for sub in task.get("subtasks", [])}
    result = []
    for item in items:
        if isinstance(item, str):
            item = {"title": item}
        if not isinstance(item, dict):
            raise ValidationError("Subtarefa inválida.")
        existing = current.get(item.get("id"))
        if existing:
            existing["title"] = _clean_title(item.get("title", existing["title"]))
            result.append(existing)
        else:
            result.append(_make_subtask(item.get("title")))
    task["subtasks"] = result


def make_task(data: dict, *, default_date: date) -> dict:
    start = parse_date(data.get("date") or default_date)
    task = {
        "id": new_id(),
        "title": _clean_title(data.get("title")),
        "notes": _clean_notes(data.get("notes")),
        "date": start.isoformat(),
        "priority": _clean_priority(data.get("priority")),
        "tags": _clean_tags(data.get("tags")),
        "subtasks": [],
        "repeat": _clean_repeat(data.get("repeat"), start),
        "completed_on": None,
        "completions": {},  # só para recorrentes: {data da repetição: dia em que foi feita}
        "created_at": now_iso(),
    }
    _set_subtasks(task, data.get("subtasks") or [])
    return task


def update_task(task: dict, data: dict) -> None:
    if "title" in data:
        task["title"] = _clean_title(data["title"])
    if "notes" in data:
        task["notes"] = _clean_notes(data["notes"])
    if "priority" in data:
        task["priority"] = _clean_priority(data["priority"])
    if "tags" in data:
        task["tags"] = _clean_tags(data["tags"])
    if "subtasks" in data:
        _set_subtasks(task, data["subtasks"])
    if "date" in data:
        new_date = parse_date(data["date"]).isoformat()
        if new_date != task["date"] and task.get("completed_on"):
            raise ValidationError("Desmarque a tarefa como concluída antes de mudar a data.")
        task["date"] = new_date
    if "repeat" in data or ("date" in data and task.get("repeat")):
        repeat = _clean_repeat(data.get("repeat", task.get("repeat")), parse_date(task["date"]))
        if repeat and task.get("completed_on"):
            raise ValidationError("Desmarque a tarefa como concluída antes de fazê-la se repetir.")
        if not repeat:
            task["completions"] = {}
        task["repeat"] = repeat


def occurs_on(task: dict, day: date) -> bool:
    """A tarefa recorrente tem uma repetição marcada para ``day``?"""
    repeat = task["repeat"]
    start = parse_date(task["date"])
    if day < start or (repeat.get("until") and day > parse_date(repeat["until"])):
        return False
    kind = repeat["type"]
    if kind == "weekly":
        return day.weekday() in repeat["weekdays"]
    if kind == "interval":
        return (day - start).days % repeat["every"] == 0
    last_day = calendar.monthrange(day.year, day.month)[1]
    return day.day == min(repeat["day"], last_day)


def occurrence_for(task: dict, day: date) -> date | None:
    """Repetição vigente em ``day``: a mais recente que já chegou."""
    lower = max(parse_date(task["date"]), day - timedelta(days=REPEAT_LOOKBACK))
    probe = day
    while probe >= lower:
        if occurs_on(task, probe):
            return probe
        probe -= timedelta(days=1)
    return None


def next_occurrence(task: dict, day: date) -> date | None:
    probe = day + timedelta(days=1)
    for _ in range(REPEAT_LOOKBACK):
        if occurs_on(task, probe):
            return probe
        probe += timedelta(days=1)
    return None


def _period(task: dict, day: date) -> tuple[date | None, date | None]:
    """(data de referência, dia em que foi concluída) da tarefa vista em ``day``.

    Para tarefas comuns a referência é a data da tarefa; para recorrentes, a
    repetição vigente naquele dia.
    """
    if task.get("repeat"):
        occ = occurrence_for(task, day)
        if occ is None:
            return None, None
        done = task.get("completions", {}).get(occ.isoformat())
        return occ, parse_date(done) if done else None
    done = task.get("completed_on")
    return parse_date(task["date"]), parse_date(done) if done else None


def complete_task(task: dict, on: date, today_: date) -> None:
    """Marca como concluída no dia ``on`` (nunca no futuro)."""
    on = min(on, today_)
    if task.get("repeat"):
        occ = occurrence_for(task, on)
        if occ is None:
            raise ValidationError("Essa repetição ainda não chegou.")
        task.setdefault("completions", {})[occ.isoformat()] = on.isoformat()
        return
    if on < parse_date(task["date"]):
        # Feita antes da data planejada: passa a contar no dia em que foi feita.
        task["date"] = on.isoformat()
    task["completed_on"] = on.isoformat()


def reopen_task(task: dict, day: date | None = None) -> None:
    if task.get("repeat"):
        occ = occurrence_for(task, day or today())
        if occ is not None:
            task.get("completions", {}).pop(occ.isoformat(), None)
        return
    task["completed_on"] = None


def _subtask_floor(task: dict, day: date) -> date | None:
    """Nas recorrentes, as subtarefas "zeram" a cada nova repetição."""
    return occurrence_for(task, day) if task.get("repeat") else None


def _subtask_done(sub: dict, floor: date | None, day: date) -> bool:
    if not sub.get("done_on"):
        return False
    done = parse_date(sub["done_on"])
    return done <= day and (floor is None or done >= floor)


def add_subtask(task: dict, data: dict) -> dict:
    if len(task.get("subtasks", [])) >= MAX_SUBTASKS:
        raise ValidationError(f"Use no máximo {MAX_SUBTASKS} subtarefas.")
    sub = _make_subtask(data.get("title"))
    task.setdefault("subtasks", []).append(sub)
    return sub


def remove_subtask(task: dict, sub_id: str) -> None:
    task["subtasks"].remove(find(task.get("subtasks", []), sub_id, "Subtarefa"))


def toggle_subtask(task: dict, sub_id: str, data: dict, *, today_: date) -> str | None:
    """Marca/desmarca uma subtarefa no dia ``data['date']`` (nunca no futuro).

    Quando todas ficam marcadas a tarefa é concluída sozinha; desmarcar uma
    subtarefa de uma tarefa concluída a reabre. Devolve ``"completed"``,
    ``"reopened"`` ou ``None`` para a interface avisar o que aconteceu.
    """
    sub = find(task.get("subtasks", []), sub_id, "Subtarefa")
    day = min(parse_date(data.get("date") or today_), today_)
    floor = _subtask_floor(task, day)
    if task.get("repeat") and floor is None:
        raise ValidationError("Essa repetição ainda não chegou.")
    done = data.get("done")
    if done is None:
        done = not _subtask_done(sub, floor, day)
    sub["done_on"] = day.isoformat() if done else None

    _, task_done = _period(task, day)
    if done and task_done is None and all(_subtask_done(s, floor, day) for s in task["subtasks"]):
        complete_task(task, day, today_)
        return "completed"
    if not done and task_done is not None:
        reopen_task(task, day)
        return "reopened"
    return None


def task_view(task: dict, day: date, today_: date) -> dict | None:
    """Como a tarefa aparece no dia ``day`` (``None`` = não aparece).

    Status possíveis:
    * ``done``    – concluída neste dia;
    * ``pending`` – hoje, ainda por fazer;
    * ``rolled``  – dia passado em que ficou pendente e foi para o dia seguinte;
    * ``missed``  – (recorrente) dia passado em que ficou pendente e foi
      substituída pela repetição seguinte (não acumula);
    * ``planned`` – dia futuro.
    """
    due, done_on = _period(task, day)
    if due is None or day < due:
        return None
    if done_on is not None and done_on < day:
        return None

    if done_on == day:
        status = "done"
    elif day < today_:
        replaced = task.get("repeat") and occurs_on(task, day + timedelta(days=1))
        status = "missed" if replaced else "rolled"
    elif day == today_:
        status = "pending"
    else:
        status = "planned"

    floor = _subtask_floor(task, day)
    view = {k: v for k, v in task.items() if k != "completions"}
    view.update(
        {
            "priority": task.get("priority", "normal"),
            "tags": task.get("tags", []),
            "repeat": task.get("repeat"),
            "subtasks": [
                {"id": sub["id"], "title": sub["title"], "done": _subtask_done(sub, floor, day)}
                for sub in task.get("subtasks", [])
            ],
            "status": status,
            "due": due.isoformat(),
            "days_late": (day - due).days,
            "can_complete": due <= today_,
        }
    )
    if task.get("repeat"):
        upcoming = next_occurrence(task, day)
        view["next_occurrence"] = upcoming.isoformat() if upcoming else None
    return view


# ---------------------------------------------------------------------------
# Rotinas acumulativas
# ---------------------------------------------------------------------------


def make_routine(data: dict, *, today_: date) -> dict:
    unit = data.get("unit", "time")
    if unit not in UNITS:
        raise ValidationError("Unidade inválida (use 'time' ou 'count').")
    start = parse_date(data.get("start_date") or today_)
    unit_label = str(data.get("unit_label") or "").strip()[:30] if unit == "count" else "min"
    return {
        "id": new_id(),
        "title": _clean_title(data.get("title")),
        "notes": _clean_notes(data.get("notes")),
        "unit": unit,
        "unit_label": unit_label or "vezes",
        "start_date": start.isoformat(),
        "versions": [
            {
                "from": start.isoformat(),
                "amount": _clean_amount(data.get("amount"), "Meta diária"),
                "weekdays": _clean_weekdays(data.get("weekdays", ALL_WEEKDAYS)),
            }
        ],
        "max_debt": _clean_optional_amount(data.get("max_debt"), "Limite de acúmulo"),
        "auto_use_balance": bool(data.get("auto_use_balance", False)),
        "pauses": [],
        "entries": [],
        "timer": None,
        "created_at": now_iso(),
    }


def update_routine(routine: dict, data: dict, *, today_: date) -> None:
    """Atualiza a rotina.

    Mudanças de meta ou de dias da semana **não reescrevem o passado**: elas
    criam uma nova "versão" do plano que vale a partir de ``effective_from``
    (padrão: hoje).
    """
    if "title" in data:
        routine["title"] = _clean_title(data["title"])
    if "notes" in data:
        routine["notes"] = _clean_notes(data["notes"])
    if "unit" in data and data["unit"] != routine["unit"]:
        raise ValidationError("Não é possível trocar a unidade de uma rotina existente.")
    if "unit_label" in data and routine["unit"] == "count":
        routine["unit_label"] = str(data["unit_label"] or "").strip()[:30] or "vezes"
    if "max_debt" in data:
        routine["max_debt"] = _clean_optional_amount(data["max_debt"], "Limite de acúmulo")
    if "auto_use_balance" in data:
        routine["auto_use_balance"] = bool(data["auto_use_balance"])
    if "start_date" in data:
        start = parse_date(data["start_date"])
        if any(parse_date(e["date"]) < start for e in routine["entries"]):
            raise ValidationError("Já existem registros antes dessa data de início.")
        routine["start_date"] = start.isoformat()
        if len(routine["versions"]) == 1:
            routine["versions"][0]["from"] = start.isoformat()

    if "amount" in data or "weekdays" in data:
        effective = parse_date(data.get("effective_from") or today_)
        current = version_on(routine, effective)
        new_version = {
            "from": effective.isoformat(),
            "amount": _clean_amount(data["amount"], "Meta diária") if "amount" in data else current["amount"],
            "weekdays": _clean_weekdays(data["weekdays"]) if "weekdays" in data else current["weekdays"],
        }
        if (new_version["amount"], new_version["weekdays"]) != (current["amount"], current["weekdays"]):
            kept = [v for v in routine["versions"] if parse_date(v["from"]) < effective]
            if not kept:
                new_version["from"] = min(effective, parse_date(routine["start_date"])).isoformat()
            routine["versions"] = kept + [new_version]


def version_on(routine: dict, day: date) -> dict:
    """Plano (meta + dias da semana) vigente em ``day``."""
    chosen = routine["versions"][0]
    for version in routine["versions"]:
        if parse_date(version["from"]) <= day:
            chosen = version
    return chosen


def is_paused(routine: dict, day: date) -> bool:
    for pause in routine.get("pauses", []):
        start = parse_date(pause["start"])
        end = parse_date(pause["end"]) if pause.get("end") else None
        if start <= day and (end is None or day <= end):
            return True
    return False


def pause_routine(routine: dict, *, today_: date) -> None:
    if is_paused(routine, today_):
        raise ValidationError("A rotina já está pausada.")
    routine.setdefault("pauses", []).append({"start": today_.isoformat(), "end": None})


def resume_routine(routine: dict, *, today_: date) -> None:
    """Retoma a rotina: a meta volta a valer já a partir de hoje."""
    open_pauses = [p for p in routine.get("pauses", []) if not p.get("end")]
    if not open_pauses:
        raise ValidationError("A rotina não está pausada.")
    for pause in open_pauses:
        end = today_ - timedelta(days=1)
        if end < parse_date(pause["start"]):
            routine["pauses"].remove(pause)  # pausou e retomou no mesmo dia
        else:
            pause["end"] = end.isoformat()


def simulate(routine: dict, until: date) -> list[dict]:
    """Recalcula a rotina dia a dia, do início até ``until`` (inclusive).

    Para cada dia:

    * ``required`` = meta do dia + dívida acumulada dos dias anteriores;
    * o que foi feito (``done``) e o saldo gasto (``spent``) abatem o ``required``;
    * se sobrar pendência, ela vira dívida para o dia seguinte;
    * se passar da conta, o excedente vira saldo.

    Dias pausados, dispensados ("pular dia") ou fora dos dias da semana da
    rotina não geram meta nova, mas a dívida antiga continua lá (e pode ser
    abatida neles).
    """
    start = parse_date(routine["start_date"])
    if until < start:
        return []

    by_day: dict[str, dict] = {}
    for entry in routine["entries"]:
        slot = by_day.setdefault(entry["date"], {"progress": 0.0, "spend": 0.0, "skip": False})
        if entry["type"] == "progress":
            slot["progress"] += entry["amount"]
        elif entry["type"] == "spend":
            slot["spend"] += entry["amount"]
        elif entry["type"] == "skip":
            slot["skip"] = True

    cap = routine.get("max_debt")
    auto = routine.get("auto_use_balance", False)
    empty = {"progress": 0.0, "spend": 0.0, "skip": False}

    debt = credit = 0.0
    days: list[dict] = []
    day = start
    while day <= until:
        plan = version_on(routine, day)
        logged = by_day.get(day.isoformat(), empty)
        paused = is_paused(routine, day)
        skipped = logged["skip"]
        planned_weekday = day.weekday() in plan["weekdays"]
        goal = plan["amount"] if planned_weekday and not paused and not skipped else 0.0

        debt_in, credit_in = debt, credit
        required = _num(debt_in + goal)
        done = _num(logged["progress"])

        # Saldo gasto manualmente (nunca mais do que se tem).
        spent = _num(min(logged["spend"], credit))
        credit = _num(credit - spent)

        # Saldo gasto automaticamente, se a rotina estiver configurada assim.
        auto_spent = 0.0
        if auto:
            gap = required - done - spent
            if gap > EPS:
                auto_spent = _num(min(gap, credit))
                credit = _num(credit - auto_spent)

        paid = _num(done + spent + auto_spent)
        balance = _num(required - paid)
        forgiven = 0.0
        if balance <= EPS:
            credit = _num(credit - balance)
            debt = 0.0
        else:
            debt = balance
            if cap is not None and debt > cap:
                forgiven = _num(debt - cap)
                debt = _num(cap)

        if paused:
            status = "paused"
        elif skipped:
            status = "skipped"
        elif required <= EPS:
            status = "free"
        elif balance <= EPS:
            status = "done"
        elif paid > EPS:
            status = "partial"
        else:
            status = "pending"

        days.append(
            {
                "date": day.isoformat(),
                "weekday": day.weekday(),
                "planned_weekday": planned_weekday,
                "paused": paused,
                "skipped": skipped,
                "goal": _num(goal),
                "debt_in": _num(debt_in),
                "credit_in": _num(credit_in),
                "required": required,
                "done": done,
                "spent": _num(spent + auto_spent),
                "auto_spent": auto_spent,
                "paid": paid,
                "remaining": _num(max(0.0, balance)),
                "extra": _num(max(0.0, -balance)),
                "debt_out": _num(debt),
                "credit_out": _num(credit),
                "forgiven": forgiven,
                "status": status,
            }
        )
        day += timedelta(days=1)
    return days


def snapshot_on(routine: dict, day: date) -> dict | None:
    days = simulate(routine, day)
    return days[-1] if days else None


def add_entry(routine: dict, data: dict, *, today_: date) -> dict:
    """Registra progresso, uso de saldo ou dispensa de um dia."""
    kind = data.get("type")
    if kind not in ENTRY_TYPES:
        raise ValidationError("Tipo de registro inválido.")
    day = parse_date(data.get("date") or today_)
    if day > today_:
        raise ValidationError("Não dá para registrar em um dia que ainda não chegou.")
    if day < parse_date(routine["start_date"]):
        raise ValidationError("Essa data é anterior ao início da rotina.")

    if kind == "progress":
        amount = _clean_amount(data.get("amount"))
    elif kind == "spend":
        snap = snapshot_on(routine, day)
        available = min(snap["credit_out"], snap["remaining"])
        requested = data.get("amount")
        amount = available if requested in (None, "") else min(_clean_amount(requested), available)
        amount = _num(amount)
        if amount <= EPS:
            raise ValidationError("Não há saldo disponível (ou nada pendente) para usar neste dia.")
    else:  # skip
        if any(e["type"] == "skip" and e["date"] == day.isoformat() for e in routine["entries"]):
            raise ValidationError("Este dia já foi dispensado.")
        amount = 0.0

    entry = {"id": new_id(), "type": kind, "date": day.isoformat(), "amount": amount, "created_at": now_iso()}
    routine["entries"].append(entry)
    return entry


def remove_entry(routine: dict, entry_id: str) -> None:
    entry = find(routine["entries"], entry_id, "Registro")
    routine["entries"].remove(entry)


# -- Cronômetro ---------------------------------------------------------------
#
# O cronômetro fica salvo na própria rotina (``routine["timer"]``), então
# continua contando mesmo que a janela seja fechada ou o PC reiniciado:
#
#   {"id", "date": dia em que foi iniciado, "started_at",
#    "running_since": quando voltou a rodar (None = pausado),
#    "elapsed": segundos acumulados antes de ``running_since``}
#
# Ao parar, o tempo vira um registro de progresso normal no dia em que o
# cronômetro foi iniciado.


def timer_elapsed(timer: dict, at: datetime) -> float:
    """Segundos contados pelo cronômetro até ``at``."""
    elapsed = float(timer.get("elapsed", 0.0))
    if timer.get("running_since"):
        elapsed += max(0.0, (at - datetime.fromisoformat(timer["running_since"])).total_seconds())
    return elapsed


def _require_timer(routine: dict) -> dict:
    timer = routine.get("timer")
    if not timer:
        raise ValidationError("O cronômetro desta rotina não está ligado.")
    return timer


def timer_start(routine: dict, *, today_: date, at: datetime) -> dict:
    """Liga o cronômetro (ou retoma, se estiver pausado)."""
    if routine["unit"] != "time":
        raise ValidationError("O cronômetro só funciona em rotinas medidas em tempo.")
    timer = routine.get("timer")
    if timer:
        if timer.get("running_since"):
            raise ValidationError("O cronômetro já está rodando.")
        timer["running_since"] = at.isoformat(timespec="seconds")
        return timer
    if today_ < parse_date(routine["start_date"]):
        raise ValidationError("Esta rotina ainda não começou.")
    stamp = at.isoformat(timespec="seconds")
    routine["timer"] = {"id": new_id(), "date": today_.isoformat(), "started_at": stamp, "running_since": stamp, "elapsed": 0.0}
    return routine["timer"]


def timer_pause(routine: dict, *, at: datetime) -> dict:
    timer = _require_timer(routine)
    if not timer.get("running_since"):
        raise ValidationError("O cronômetro já está pausado.")
    timer["elapsed"] = round(timer_elapsed(timer, at), 3)
    timer["running_since"] = None
    return timer


def timer_stop(routine: dict, data: dict, *, today_: date, at: datetime) -> dict | None:
    """Desliga o cronômetro e registra o tempo como progresso.

    ``data['amount']`` (minutos) permite corrigir o tempo antes de salvar, por
    exemplo se o cronômetro ficou ligado depois de terminar a atividade. Sem
    ele, vale o tempo contado, arredondado para minutos inteiros. Devolve o
    registro criado (ou ``None`` se deu menos de meio minuto).
    """
    timer = _require_timer(routine)
    requested = data.get("amount")
    if requested in (None, ""):
        amount = float(round(timer_elapsed(timer, at) / 60))
    else:
        amount = _clean_amount(requested, "Tempo")
    entry = None
    if amount > EPS:
        day = min(parse_date(timer["date"]), today_)
        entry = add_entry(routine, {"type": "progress", "date": day.isoformat(), "amount": amount}, today_=today_)
        entry["source"] = "timer"
    routine["timer"] = None
    return entry


def timer_cancel(routine: dict) -> None:
    _require_timer(routine)
    routine["timer"] = None


# -- Configurações -------------------------------------------------------------


def settings_of(data: dict) -> dict:
    return {**DEFAULT_SETTINGS, **data.get("settings", {})}


def update_settings(data: dict, changes: dict) -> dict:
    settings = settings_of(data)
    for key in ("notify_end_of_day", "notify_timer", "sound"):
        if key in changes:
            settings[key] = bool(changes[key])
    if "notify_time" in changes:
        value = str(changes["notify_time"] or "").strip()
        if not re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", value):
            raise ValidationError("Horário inválido (use HH:MM, ex.: 20:00).")
        settings["notify_time"] = value
    data["settings"] = settings
    return settings


def _public(routine: dict) -> dict:
    return {k: v for k, v in routine.items() if k != "entries"}


def routine_view(routine: dict, day: date, today_: date) -> dict | None:
    days = simulate(routine, day)
    if not days:
        return None
    iso = day.isoformat()
    return {
        **_public(routine),
        "plan": version_on(routine, day),
        "day": days[-1],
        "recent": [{"date": d["date"], "status": d["status"]} for d in days[-7:]],
        "entries_on_day": sorted(
            (e for e in routine["entries"] if e["date"] == iso), key=lambda e: e["created_at"]
        ),
        "total_done": _num(sum(d["done"] for d in days)),
        "paused_now": is_paused(routine, today_),
    }


def routine_history(routine: dict, until: date, limit: int = 30) -> dict:
    days = simulate(routine, until)
    return {
        **_public(routine),
        "days": list(reversed(days[-limit:])),
        "entries": sorted(routine["entries"], key=lambda e: (e["date"], e["created_at"]), reverse=True),
    }


# ---------------------------------------------------------------------------
# Visão geral de um dia
# ---------------------------------------------------------------------------


def active_timers(data: dict, at: datetime) -> list[dict]:
    """Cronômetros ligados, com o que faltava da meta no dia em que começaram."""
    timers = []
    for routine in data["routines"]:
        timer = routine.get("timer")
        if not timer:
            continue
        snap = snapshot_on(routine, parse_date(timer["date"]))
        timers.append(
            {
                "routine_id": routine["id"],
                "title": routine["title"],
                **timer,
                "elapsed_now": round(timer_elapsed(timer, at), 3),
                "remaining": snap["remaining"] if snap else 0.0,
                "required": snap["required"] if snap else 0.0,
            }
        )
    return timers


def build_state(data: dict, day: date, today_: date, at: datetime | None = None) -> dict:
    at = at or now()
    tasks = [view for t in data["tasks"] if (view := task_view(t, day, today_))]
    tasks.sort(
        key=lambda t: (
            TASK_ORDER[t["status"]],
            PRIORITY_ORDER.get(t["priority"], 1),
            -t["days_late"],
            t["created_at"],
        )
    )

    routines = [view for r in data["routines"] if (view := routine_view(r, day, today_))]
    routines.sort(key=lambda r: (r["day"]["remaining"] <= EPS, r["created_at"]))

    tags = {tag.casefold(): tag for t in data["tasks"] for tag in t.get("tags", [])}

    open_tasks = [t for t in tasks if t["status"] != "done"]
    open_routines = [r for r in routines if r["day"]["remaining"] > EPS]
    return {
        "today": today_.isoformat(),
        "date": day.isoformat(),
        "now": at.isoformat(timespec="seconds"),
        "tasks": tasks,
        "routines": routines,
        "timers": active_timers(data, at),
        "tags": sorted(tags.values(), key=str.casefold),
        "settings": settings_of(data),
        "summary": {
            "tasks_open": len(open_tasks),
            "tasks_late": sum(1 for t in open_tasks if t["days_late"] > 0),
            "tasks_high": sum(1 for t in open_tasks if t["priority"] == "high"),
            "tasks_done": len(tasks) - len(open_tasks),
            "routines_open": len(open_routines),
            "routines_total": len(routines),
        },
    }

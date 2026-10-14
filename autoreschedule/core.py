"""Regras de negócio do Auto Reschedule.

Existem dois tipos de item:

* **Tarefas** (``tasks``): têm uma data. Enquanto não forem concluídas,
  continuam aparecendo em todos os dias seguintes, com a indicação de há
  quantos dias estão atrasadas.
* **Rotinas acumulativas** (``routines``): têm uma meta por dia (ex.: 60 min
  de estudo). O que não for feito vira *dívida* e soma na meta do dia
  seguinte; o que for feito a mais vira *saldo*, que pode ser gasto depois
  para cobrir uma pendência.

Nada é gravado "virando o dia": o estado de qualquer data é sempre
recalculado a partir dos registros, então o app funciona mesmo que fique dias
fechado. Este módulo é puro (sem I/O) para facilitar os testes.
"""

from __future__ import annotations

import math
import os
import uuid
from datetime import date, datetime, timedelta

EPS = 1e-9
ALL_WEEKDAYS = [0, 1, 2, 3, 4, 5, 6]  # 0 = segunda ... 6 = domingo
UNITS = ("time", "count")  # "time" é medido em minutos
ENTRY_TYPES = ("progress", "spend", "skip")

TASK_ORDER = {"pending": 0, "rolled": 0, "planned": 0, "done": 1}


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


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


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


def find(items: list[dict], item_id: str, what: str) -> dict:
    for item in items:
        if item["id"] == item_id:
            return item
    raise NotFoundError(f"{what} não encontrada.")


# ---------------------------------------------------------------------------
# Tarefas avulsas
# ---------------------------------------------------------------------------


def make_task(data: dict, *, default_date: date) -> dict:
    return {
        "id": new_id(),
        "title": _clean_title(data.get("title")),
        "notes": _clean_notes(data.get("notes")),
        "date": parse_date(data.get("date") or default_date).isoformat(),
        "completed_on": None,
        "created_at": now_iso(),
    }


def update_task(task: dict, data: dict) -> None:
    if "title" in data:
        task["title"] = _clean_title(data["title"])
    if "notes" in data:
        task["notes"] = _clean_notes(data["notes"])
    if "date" in data:
        new_date = parse_date(data["date"]).isoformat()
        if new_date != task["date"] and task.get("completed_on"):
            raise ValidationError("Desmarque a tarefa como concluída antes de mudar a data.")
        task["date"] = new_date


def complete_task(task: dict, on: date, today_: date) -> None:
    """Marca como concluída no dia ``on`` (nunca no futuro)."""
    on = min(on, today_)
    if on < parse_date(task["date"]):
        # Feita antes da data planejada: passa a contar no dia em que foi feita.
        task["date"] = on.isoformat()
    task["completed_on"] = on.isoformat()


def reopen_task(task: dict) -> None:
    task["completed_on"] = None


def task_view(task: dict, day: date, today_: date) -> dict | None:
    """Como a tarefa aparece no dia ``day`` (``None`` = não aparece).

    Status possíveis:
    * ``done``    – concluída neste dia;
    * ``pending`` – hoje, ainda por fazer;
    * ``rolled``  – dia passado em que ficou pendente e foi para o dia seguinte;
    * ``planned`` – dia futuro.
    """
    due = parse_date(task["date"])
    if day < due:
        return None
    done_on = parse_date(task["completed_on"]) if task.get("completed_on") else None
    if done_on is not None and done_on < day:
        return None

    if done_on == day:
        status = "done"
    elif day < today_:
        status = "rolled"
    elif day == today_:
        status = "pending"
    else:
        status = "planned"
    return {**task, "status": status, "days_late": (day - due).days}


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


def build_state(data: dict, day: date, today_: date) -> dict:
    tasks = [view for t in data["tasks"] if (view := task_view(t, day, today_))]
    tasks.sort(key=lambda t: (TASK_ORDER[t["status"]], -t["days_late"], t["created_at"]))

    routines = [view for r in data["routines"] if (view := routine_view(r, day, today_))]
    routines.sort(key=lambda r: (r["day"]["remaining"] <= EPS, r["created_at"]))

    open_tasks = [t for t in tasks if t["status"] != "done"]
    open_routines = [r for r in routines if r["day"]["remaining"] > EPS]
    return {
        "today": today_.isoformat(),
        "date": day.isoformat(),
        "tasks": tasks,
        "routines": routines,
        "summary": {
            "tasks_open": len(open_tasks),
            "tasks_late": sum(1 for t in open_tasks if t["days_late"] > 0),
            "tasks_done": len(tasks) - len(open_tasks),
            "routines_open": len(open_routines),
            "routines_total": len(routines),
        },
    }

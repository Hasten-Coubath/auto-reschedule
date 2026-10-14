"""Testes das regras de negócio. Rode com:  python -m unittest discover -s tests"""

import sys
import unittest
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from autoreschedule import core  # noqa: E402

# 2026-10-12 é uma segunda-feira.
MON = date(2026, 10, 12)


def d(offset: int) -> date:
    return MON + timedelta(days=offset)


def routine(**kw):
    data = {"title": "Estudar o curso", "amount": 60, "start_date": MON.isoformat()}
    data.update(kw)
    return core.make_routine(data, today_=MON)


def log(r, offset, amount, kind="progress", today_offset=None):
    today_ = d(today_offset if today_offset is not None else offset)
    return core.add_entry(r, {"type": kind, "date": d(offset).isoformat(), "amount": amount}, today_=today_)


def snap(r, offset):
    return core.snapshot_on(r, d(offset))


class RoutineAccumulationTests(unittest.TestCase):
    def test_missed_day_accumulates(self):
        r = routine()
        self.assertEqual(snap(r, 0)["required"], 60)
        s = snap(r, 1)
        self.assertEqual(s["debt_in"], 60)
        self.assertEqual(s["required"], 120)  # 1h de hoje + 1h de ontem
        self.assertEqual(snap(r, 2)["required"], 180)

    def test_partial_progress_reduces_what_carries_over(self):
        r = routine()
        log(r, 0, 30)
        self.assertEqual(snap(r, 0)["status"], "partial")
        self.assertEqual(snap(r, 0)["remaining"], 30)
        self.assertEqual(snap(r, 1)["required"], 90)

    def test_paying_debt_on_the_next_day(self):
        r = routine()
        log(r, 1, 90)  # devia 2h, fez 1h30
        s = snap(r, 1)
        self.assertEqual(s["remaining"], 30)
        self.assertEqual(snap(r, 2)["required"], 90)

    def test_extra_becomes_credit_and_is_kept_until_spent(self):
        r = routine()
        log(r, 0, 180)  # 3h numa meta de 1h
        s0 = snap(r, 0)
        self.assertEqual(s0["status"], "done")
        self.assertEqual(s0["extra"], 120)
        self.assertEqual(s0["credit_out"], 120)

        # Sem uso automático, o saldo fica guardado e a meta do dia continua.
        s1 = snap(r, 1)
        self.assertEqual(s1["credit_in"], 120)
        self.assertEqual(s1["remaining"], 60)

        entry = log(r, 1, None, kind="spend")
        self.assertEqual(entry["amount"], 60)  # gasta só o necessário
        s1 = snap(r, 1)
        self.assertEqual(s1["status"], "done")
        self.assertEqual(s1["credit_out"], 60)

    def test_spend_more_than_available_is_capped(self):
        r = routine()
        log(r, 0, 90)  # 30 de saldo
        entry = log(r, 1, 999, kind="spend")
        self.assertEqual(entry["amount"], 30)
        self.assertEqual(snap(r, 1)["remaining"], 30)

    def test_spend_without_credit_is_rejected(self):
        r = routine()
        with self.assertRaises(core.ValidationError):
            log(r, 0, None, kind="spend")

    def test_auto_use_balance(self):
        r = routine(auto_use_balance=True)
        log(r, 0, 180)
        s1 = snap(r, 1)
        self.assertEqual(s1["status"], "done")
        self.assertEqual(s1["auto_spent"], 60)
        self.assertEqual(snap(r, 2)["status"], "done")
        s3 = snap(r, 3)
        self.assertEqual(s3["status"], "pending")
        self.assertEqual(s3["required"], 60)

    def test_extra_first_pays_debt(self):
        r = routine()
        log(r, 1, 180)  # devia 2h, fez 3h
        s = snap(r, 1)
        self.assertEqual(s["debt_out"], 0)
        self.assertEqual(s["credit_out"], 60)

    def test_weekdays_only_add_goal_on_selected_days(self):
        r = routine(weekdays=[0, 1, 2, 3, 4])  # seg a sex
        log(r, 0, 60, today_offset=4)
        log(r, 1, 60, today_offset=4)
        log(r, 2, 60, today_offset=4)
        log(r, 3, 60, today_offset=4)
        # sexta sem nada -> acumula no fim de semana, mas sábado/domingo não somam meta nova
        sat = snap(r, 5)
        self.assertEqual(sat["goal"], 0)
        self.assertEqual(sat["required"], 60)
        self.assertEqual(snap(r, 7)["required"], 120)  # segunda: 1h + 1h da sexta

    def test_skip_day(self):
        r = routine()
        log(r, 1, None, kind="skip")
        s1 = snap(r, 1)
        self.assertEqual(s1["goal"], 0)
        self.assertEqual(s1["required"], 60)  # a dívida de segunda continua
        self.assertEqual(s1["status"], "skipped")
        with self.assertRaises(core.ValidationError):
            log(r, 1, None, kind="skip")

    def test_pause_and_resume(self):
        r = routine()
        core.pause_routine(r, today_=d(1))
        self.assertTrue(snap(r, 3)["paused"])
        self.assertEqual(snap(r, 3)["required"], 60)  # só a dívida de segunda, congelada
        core.resume_routine(r, today_=d(4))
        self.assertFalse(snap(r, 4)["paused"])
        self.assertEqual(snap(r, 4)["required"], 120)

    def test_pause_and_resume_same_day_removes_pause(self):
        r = routine()
        core.pause_routine(r, today_=d(2))
        core.resume_routine(r, today_=d(2))
        self.assertEqual(r["pauses"], [])

    def test_max_debt(self):
        r = routine(max_debt=120)
        s = snap(r, 5)
        self.assertEqual(s["required"], 180)  # 2h (limite) + 1h do dia
        self.assertEqual(s["debt_out"], 120)
        self.assertEqual(s["forgiven"], 60)

    def test_changing_goal_does_not_rewrite_the_past(self):
        r = routine()
        core.update_routine(r, {"amount": 30}, today_=d(2))
        self.assertEqual(snap(r, 0)["goal"], 60)
        self.assertEqual(snap(r, 1)["goal"], 60)
        s2 = snap(r, 2)
        self.assertEqual(s2["goal"], 30)
        self.assertEqual(s2["required"], 150)

    def test_count_unit(self):
        r = routine(unit="count", unit_label="páginas", amount=10)
        log(r, 0, 4)
        self.assertEqual(snap(r, 1)["required"], 16)
        self.assertEqual(r["unit_label"], "páginas")

    def test_cannot_log_in_the_future_or_before_start(self):
        r = routine()
        with self.assertRaises(core.ValidationError):
            core.add_entry(r, {"type": "progress", "date": d(3).isoformat(), "amount": 10}, today_=d(1))
        with self.assertRaises(core.ValidationError):
            core.add_entry(r, {"type": "progress", "date": d(-1).isoformat(), "amount": 10}, today_=d(1))

    def test_removing_entry_recalculates(self):
        r = routine()
        entry = log(r, 0, 60)
        self.assertEqual(snap(r, 1)["required"], 60)
        core.remove_entry(r, entry["id"])
        self.assertEqual(snap(r, 1)["required"], 120)

    def test_invalid_values(self):
        with self.assertRaises(core.ValidationError):
            routine(amount=0)
        with self.assertRaises(core.ValidationError):
            routine(title="  ")
        with self.assertRaises(core.ValidationError):
            routine(weekdays=[])
        with self.assertRaises(core.ValidationError):
            routine(unit="litros")

    def test_float_amounts_do_not_drift(self):
        r = routine(unit="count", amount=0.1)
        for i in range(30):
            log(r, i, 0.1, today_offset=30)
        self.assertEqual(snap(r, 30)["required"], 0.1)


class TaskRolloverTests(unittest.TestCase):
    def make(self, offset=0):
        return core.make_task({"title": "Pagar boleto", "date": d(offset).isoformat()}, default_date=MON)

    def test_unfinished_task_rolls_to_next_days(self):
        t = self.make()
        today_ = d(3)
        self.assertIsNone(core.task_view(t, d(-1), today_))
        self.assertEqual(core.task_view(t, d(0), today_)["status"], "rolled")
        self.assertEqual(core.task_view(t, d(2), today_)["status"], "rolled")
        view = core.task_view(t, today_, today_)
        self.assertEqual(view["status"], "pending")
        self.assertEqual(view["days_late"], 3)
        self.assertEqual(core.task_view(t, d(5), today_)["status"], "planned")

    def test_completed_task_stays_on_completion_day_only(self):
        t = self.make()
        core.complete_task(t, d(2), today_=d(2))
        self.assertEqual(core.task_view(t, d(1), d(2))["status"], "rolled")
        self.assertEqual(core.task_view(t, d(2), d(2))["status"], "done")
        self.assertIsNone(core.task_view(t, d(3), d(3)))

    def test_completing_early_moves_task_to_today(self):
        t = self.make(offset=5)
        core.complete_task(t, d(5), today_=d(1))
        self.assertEqual(t["completed_on"], d(1).isoformat())
        self.assertEqual(t["date"], d(1).isoformat())

    def test_reopen(self):
        t = self.make()
        core.complete_task(t, d(0), today_=d(0))
        core.reopen_task(t)
        self.assertEqual(core.task_view(t, d(2), d(2))["status"], "pending")

    def test_cannot_change_date_of_completed_task(self):
        t = self.make()
        core.complete_task(t, d(0), today_=d(0))
        with self.assertRaises(core.ValidationError):
            core.update_task(t, {"date": d(3).isoformat()})

    def test_build_state_orders_and_summarizes(self):
        data = {"tasks": [], "routines": [routine()]}
        old = self.make(0)
        new = self.make(2)
        done = self.make(2)
        core.complete_task(done, d(2), today_=d(2))
        data["tasks"] += [new, done, old]
        state = core.build_state(data, d(2), d(2))
        self.assertEqual([t["id"] for t in state["tasks"]], [old["id"], new["id"], done["id"]])
        self.assertEqual(state["summary"]["tasks_open"], 2)
        self.assertEqual(state["summary"]["tasks_late"], 1)
        self.assertEqual(state["summary"]["routines_open"], 1)
        self.assertEqual(state["routines"][0]["day"]["required"], 180)


if __name__ == "__main__":
    unittest.main()

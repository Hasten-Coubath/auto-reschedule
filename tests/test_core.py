"""Testes das regras de negócio. Rode com:  python -m unittest discover -s tests"""

import sys
import unittest
from datetime import date, datetime, timedelta
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

    def test_priority_comes_first_among_open_tasks(self):
        low = core.make_task({"title": "Baixa", "date": d(0).isoformat(), "priority": "low"}, default_date=MON)
        normal = self.make(0)
        high = core.make_task({"title": "Alta", "date": d(0).isoformat(), "priority": "high"}, default_date=MON)
        state = core.build_state({"tasks": [low, normal, high], "routines": []}, d(0), d(0))
        self.assertEqual([t["id"] for t in state["tasks"]], [high["id"], normal["id"], low["id"]])
        self.assertEqual(state["summary"]["tasks_high"], 1)
        with self.assertRaises(core.ValidationError):
            core.make_task({"title": "x", "priority": "urgente"}, default_date=MON)

    def test_tags_are_cleaned(self):
        t = core.make_task({"title": "x", "tags": "#Faculdade, faculdade,  casa ,,"}, default_date=MON)
        self.assertEqual(t["tags"], ["Faculdade", "casa"])
        state = core.build_state({"tasks": [t], "routines": []}, d(0), d(0))
        self.assertEqual(state["tags"], ["casa", "Faculdade"])
        with self.assertRaises(core.ValidationError):
            core.make_task({"title": "x", "tags": ["a" * 31]}, default_date=MON)


class SubtaskTests(unittest.TestCase):
    def make(self, **kw):
        data = {"title": "Trabalho de BD", "date": MON.isoformat(), "subtasks": ["Modelo ER", "Scripts SQL"]}
        data.update(kw)
        return core.make_task(data, default_date=MON)

    def toggle(self, t, index, offset, **kw):
        return core.toggle_subtask(t, t["subtasks"][index]["id"], {"date": d(offset).isoformat(), **kw}, today_=d(offset))

    def test_completing_all_subtasks_completes_the_task(self):
        t = self.make()
        self.assertIsNone(self.toggle(t, 0, 0))
        view = core.task_view(t, d(0), d(0))
        self.assertEqual([s["done"] for s in view["subtasks"]], [True, False])
        self.assertEqual(view["status"], "pending")
        self.assertEqual(self.toggle(t, 1, 1), "completed")
        self.assertEqual(t["completed_on"], d(1).isoformat())
        # Desmarcar uma subtarefa reabre a tarefa.
        self.assertEqual(self.toggle(t, 0, 1), "reopened")
        self.assertIsNone(t["completed_on"])

    def test_subtask_progress_is_shown_by_day(self):
        t = self.make()
        self.toggle(t, 0, 2)
        self.assertFalse(core.task_view(t, d(1), d(2))["subtasks"][0]["done"])
        self.assertTrue(core.task_view(t, d(2), d(2))["subtasks"][0]["done"])

    def test_edit_subtasks_keeps_state(self):
        t = self.make()
        self.toggle(t, 0, 0)
        first = t["subtasks"][0]
        core.update_task(t, {"subtasks": [{"id": first["id"], "title": "Modelo ER v2"}, "Relatório"]})
        self.assertEqual([s["title"] for s in t["subtasks"]], ["Modelo ER v2", "Relatório"])
        self.assertEqual(t["subtasks"][0]["done_on"], d(0).isoformat())
        core.add_subtask(t, {"title": "Slides"})
        core.remove_subtask(t, first["id"])
        self.assertEqual([s["title"] for s in t["subtasks"]], ["Relatório", "Slides"])


class RecurringTaskTests(unittest.TestCase):
    def make(self, repeat, offset=0):
        return core.make_task({"title": "Lavar roupa", "date": d(offset).isoformat(), "repeat": repeat}, default_date=MON)

    def test_weekly_missed_occurrence_is_replaced_not_accumulated(self):
        t = self.make({"type": "weekly", "weekdays": [0, 3]})  # seg e qui
        today_ = d(4)  # sexta
        self.assertEqual(core.task_view(t, d(1), today_)["status"], "rolled")  # ter: segue até qui
        self.assertEqual(core.task_view(t, d(2), today_)["status"], "missed")  # qua: quinta substitui
        view = core.task_view(t, today_, today_)
        self.assertEqual(view["due"], d(3).isoformat())  # só a repetição de quinta está pendente
        self.assertEqual(view["days_late"], 1)
        self.assertEqual(view["next_occurrence"], d(7).isoformat())

    def test_completing_an_occurrence(self):
        t = self.make({"type": "interval", "every": 2})
        core.complete_task(t, d(1), today_=d(1))  # repetição de seg feita na ter
        self.assertEqual(core.task_view(t, d(1), d(1))["status"], "done")
        self.assertEqual(core.task_view(t, d(2), d(2))["status"], "pending")  # nova repetição na qua
        core.reopen_task(t, d(1))
        self.assertEqual(core.task_view(t, d(1), d(1))["status"], "pending")

    def test_cannot_complete_before_the_first_occurrence(self):
        t = self.make({"type": "weekly", "weekdays": [4]}, offset=0)  # só sextas, hoje é segunda
        self.assertIsNone(core.task_view(t, d(0), d(0)))
        view = core.task_view(t, d(4), d(0))
        self.assertEqual(view["status"], "planned")
        self.assertFalse(view["can_complete"])
        with self.assertRaises(core.ValidationError):
            core.complete_task(t, d(4), today_=d(0))

    def test_monthly_uses_last_day_of_short_months(self):
        t = core.make_task(
            {"title": "Pagar aluguel", "date": "2027-01-31", "repeat": {"type": "monthly", "day": 31}}, default_date=MON
        )
        self.assertTrue(core.occurs_on(t, date(2027, 2, 28)))
        self.assertFalse(core.occurs_on(t, date(2027, 2, 27)))
        self.assertTrue(core.occurs_on(t, date(2027, 3, 31)))

    def test_until_stops_new_occurrences(self):
        t = self.make({"type": "interval", "every": 1, "until": d(2).isoformat()})
        core.complete_task(t, d(2), today_=d(2))
        self.assertIsNone(core.task_view(t, d(3), d(3)))
        with self.assertRaises(core.ValidationError):
            self.make({"type": "weekly", "weekdays": [0], "until": d(-1).isoformat()})

    def test_subtasks_reset_on_each_occurrence(self):
        t = self.make({"type": "weekly", "weekdays": [0]})
        core.add_subtask(t, {"title": "Separar"})
        core.add_subtask(t, {"title": "Estender"})
        for sub in t["subtasks"]:
            core.toggle_subtask(t, sub["id"], {"date": d(0).isoformat()}, today_=d(0))
        self.assertEqual(core.task_view(t, d(0), d(0))["status"], "done")
        view = core.task_view(t, d(7), d(7))
        self.assertEqual(view["status"], "pending")
        self.assertEqual([s["done"] for s in view["subtasks"]], [False, False])

    def test_turning_off_repeat(self):
        t = self.make({"type": "interval", "every": 1})
        core.complete_task(t, d(0), today_=d(0))
        core.update_task(t, {"repeat": None})
        self.assertIsNone(t["repeat"])
        self.assertEqual(t["completions"], {})


class TimerTests(unittest.TestCase):
    T0 = datetime(2026, 10, 12, 9, 0, 0)

    def at(self, minutes):
        return self.T0 + timedelta(minutes=minutes)

    def test_start_pause_resume_stop(self):
        r = routine()
        core.timer_start(r, today_=MON, at=self.at(0))
        core.timer_pause(r, at=self.at(20))
        self.assertEqual(core.timer_elapsed(r["timer"], self.at(50)), 20 * 60)
        core.timer_start(r, today_=MON, at=self.at(30))
        entry = core.timer_stop(r, {}, today_=MON, at=self.at(75))
        self.assertEqual(entry["amount"], 65)
        self.assertEqual(entry["source"], "timer")
        self.assertIsNone(r["timer"])
        self.assertEqual(snap(r, 0)["credit_out"], 5)  # passou da meta: vira saldo

    def test_stop_with_corrected_amount_and_on_start_day(self):
        r = routine()
        core.timer_start(r, today_=MON, at=self.at(0))
        # Esqueceu ligado de um dia para o outro: corrige para 50 min.
        entry = core.timer_stop(r, {"amount": 50}, today_=d(1), at=self.at(60 * 20))
        self.assertEqual(entry["date"], MON.isoformat())
        self.assertEqual(snap(r, 0)["remaining"], 10)

    def test_short_timer_records_nothing(self):
        r = routine()
        core.timer_start(r, today_=MON, at=self.at(0))
        self.assertIsNone(core.timer_stop(r, {}, today_=MON, at=self.T0 + timedelta(seconds=20)))
        self.assertEqual(r["entries"], [])

    def test_invalid_timer_actions(self):
        r = routine()
        with self.assertRaises(core.ValidationError):
            core.timer_pause(r, at=self.at(0))
        core.timer_start(r, today_=MON, at=self.at(0))
        with self.assertRaises(core.ValidationError):
            core.timer_start(r, today_=MON, at=self.at(1))
        core.timer_cancel(r)
        self.assertIsNone(r["timer"])
        with self.assertRaises(core.ValidationError):
            core.timer_start(routine(unit="count", unit_label="páginas"), today_=MON, at=self.at(0))

    def test_active_timers_in_state(self):
        r = routine()
        log(r, 0, 15)
        core.timer_start(r, today_=MON, at=self.at(0))
        state = core.build_state({"tasks": [], "routines": [r]}, MON, MON, at=self.at(10))
        (timer,) = state["timers"]
        self.assertEqual(timer["remaining"], 45)
        self.assertEqual(timer["elapsed_now"], 600)


class SettingsAndMigrationTests(unittest.TestCase):
    def test_settings(self):
        data = {}
        self.assertEqual(core.settings_of(data)["notify_time"], "20:00")
        core.update_settings(data, {"notify_time": "21:30", "sound": False})
        self.assertEqual(data["settings"]["notify_time"], "21:30")
        self.assertFalse(core.settings_of(data)["sound"])
        with self.assertRaises(core.ValidationError):
            core.update_settings(data, {"notify_time": "25:00"})

    def test_old_files_are_migrated(self):
        from autoreschedule.storage import migrate

        old = {
            "version": 1,
            "tasks": [{"id": "a1", "title": "Antiga", "notes": "", "date": MON.isoformat(), "completed_on": None, "created_at": "x"}],
            "routines": [],
        }
        data = migrate(old)
        self.assertEqual(data["version"], 2)
        view = core.task_view(data["tasks"][0], d(1), d(1))
        self.assertEqual((view["priority"], view["tags"], view["subtasks"]), ("normal", [], []))


if __name__ == "__main__":
    unittest.main()

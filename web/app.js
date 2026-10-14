/* Auto Reschedule — interface. Autor: Hasten-Coubath */
"use strict";

const EPS = 1e-6;
// 0 = segunda ... 6 = domingo (mesma convenção do Python)
const WEEKDAYS = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"];
const STATUS_LABEL = {
  done: "meta cumprida",
  partial: "feita em parte",
  pending: "não feita",
  free: "dia livre",
  skipped: "dia dispensado",
  paused: "pausada",
};

const state = {
  view: null, // data em exibição (ISO) ou null = hoje
  today: null,
  date: null,
  data: null,
  localDay: toISO(new Date()),
  taskDateFor: null,
};

const $ = (sel, root = document) => root.querySelector(sel);

const ICONS = {
  check: '<svg viewBox="0 0 24 24"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>',
  more: '<svg viewBox="0 0 24 24"><circle cx="5" cy="12" r="1.6" class="fill"/><circle cx="12" cy="12" r="1.6" class="fill"/><circle cx="19" cy="12" r="1.6" class="fill"/></svg>',
  edit: '<svg viewBox="0 0 24 24"><path d="M4 20h4L19 9l-4-4L4 16z"/><path d="M13.5 6.5l4 4"/></svg>',
  trash: '<svg viewBox="0 0 24 24"><path d="M4 7h16M10 11v6M14 11v6M6 7l1 13h10l1-13M9 7V4h6v3"/></svg>',
  x: '<svg viewBox="0 0 24 24"><path d="M6 6l12 12M18 6L6 18"/></svg>',
  history: '<svg viewBox="0 0 24 24"><path d="M3 12a9 9 0 1 0 3-6.7L3 8"/><path d="M3 3v5h5M12 7v5l3 2"/></svg>',
  pause: '<svg viewBox="0 0 24 24"><path d="M9 5v14M15 5v14"/></svg>',
  play: '<svg viewBox="0 0 24 24"><path d="M7 5l12 7-12 7z"/></svg>',
  skip: '<svg viewBox="0 0 24 24"><path d="M5 5l9 7-9 7zM18 5v14"/></svg>',
  coin: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="8"/><path d="M12 8v8M9.5 10.5h4a1.5 1.5 0 0 1 0 3h-3a1.5 1.5 0 0 0 0 3h4"/></svg>',
  download: '<svg viewBox="0 0 24 24"><path d="M12 4v11M7 10l5 5 5-5M5 20h14"/></svg>',
  info: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7.5v.5"/></svg>',
  power: '<svg viewBox="0 0 24 24"><path d="M12 3v9M6.3 6.3a8 8 0 1 0 11.4 0"/></svg>',
};

// ---------------------------------------------------------------------------
// Utilitários
// ---------------------------------------------------------------------------

function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
}

function parseISO(iso) {
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(y, m - 1, d);
}

function toISO(d) {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

function addDays(iso, n) {
  const d = parseISO(iso);
  d.setDate(d.getDate() + n);
  return toISO(d);
}

function diffDays(a, b) {
  return Math.round((parseISO(a) - parseISO(b)) / 86400000);
}

const fmtWeekday = new Intl.DateTimeFormat("pt-BR", { weekday: "long" });
const fmtDayMonth = new Intl.DateTimeFormat("pt-BR", { day: "numeric", month: "long" });
const fmtDayMonthYear = new Intl.DateTimeFormat("pt-BR", { day: "numeric", month: "long", year: "numeric" });
const fmtShort = new Intl.DateTimeFormat("pt-BR", { day: "2-digit", month: "2-digit" });
const fmtShortWeekday = new Intl.DateTimeFormat("pt-BR", { weekday: "short", day: "2-digit", month: "2-digit" });

const capitalize = (s) => s.charAt(0).toUpperCase() + s.slice(1);

function dayName(iso) {
  const n = diffDays(iso, state.today);
  if (n === 0) return "Hoje";
  if (n === -1) return "Ontem";
  if (n === 1) return "Amanhã";
  return capitalize(fmtWeekday.format(parseISO(iso)));
}

function longDate(iso) {
  const d = parseISO(iso);
  const sameYear = d.getFullYear() === parseISO(state.today).getFullYear();
  return (sameYear ? fmtDayMonth : fmtDayMonthYear).format(d);
}

function shortDate(iso) {
  return fmtShort.format(parseISO(iso));
}

function plural(n, one, many) {
  return `${n} ${n === 1 ? one : many}`;
}

function fmtMinutes(min) {
  const total = Math.round(min);
  const h = Math.floor(total / 60);
  const m = total % 60;
  if (h && m) return `${h}h${String(m).padStart(2, "0")}`;
  if (h) return `${h}h`;
  return `${m}min`;
}

function fmtNumber(x) {
  return Number(x.toFixed(2)).toLocaleString("pt-BR");
}

function fmtAmount(r, x) {
  return r.unit === "time" ? fmtMinutes(x) : `${fmtNumber(x)} ${r.unit_label}`;
}

/** Converte "1h30", "1:30", "90", "45min", "1,5h" em minutos. */
function parseDuration(text) {
  const s = String(text ?? "").trim().toLowerCase().replace(/,/g, ".").replace(/\s+/g, "");
  if (!s) return null;
  let m;
  if ((m = s.match(/^(\d+):(\d{1,2})$/))) return +m[1] * 60 + +m[2];
  if ((m = s.match(/^(\d+(?:\.\d+)?)(?:h|hr|hrs|hora|horas)(?:(\d+)(?:m|min|minutos?)?)?$/))) {
    return Math.round(parseFloat(m[1]) * 60 + (m[2] ? +m[2] : 0));
  }
  if ((m = s.match(/^(\d+(?:\.\d+)?)(?:m|min|mins|minutos?)?$/))) return Math.round(parseFloat(m[1]));
  return null;
}

function parseNumber(text) {
  const n = parseFloat(String(text ?? "").replace(",", "."));
  return Number.isFinite(n) ? n : null;
}

function parseAmount(r, text) {
  const v = r.unit === "time" ? parseDuration(text) : parseNumber(text);
  return v !== null && v > 0 ? v : null;
}

function weekdaysText(days) {
  const key = days.join(",");
  if (key === "0,1,2,3,4,5,6") return "todos os dias";
  if (key === "0,1,2,3,4") return "seg a sex";
  if (key === "5,6") return "fins de semana";
  return days.map((d) => WEEKDAYS[d]).join(", ");
}

function versionOn(r, iso) {
  let chosen = r.versions[0];
  for (const v of r.versions) if (v.from <= iso) chosen = v;
  return chosen;
}

function when(iso = state.date) {
  if (iso < state.today) return "past";
  if (iso > state.today) return "future";
  return "today";
}

// ---------------------------------------------------------------------------
// API
// ---------------------------------------------------------------------------

async function api(method, path, body) {
  const options = { method, headers: { "X-Auto-Reschedule": "1" } };
  if (body !== undefined) {
    options.headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(body);
  }
  let res;
  try {
    res = await fetch(path, options);
  } catch {
    throw new Error("Não foi possível falar com o servidor. Ele ainda está rodando?");
  }
  const payload = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(payload.error || `Erro ${res.status}`);
  return payload;
}

async function load() {
  try {
    const qs = state.view ? `?date=${state.view}` : "";
    const data = await api("GET", `/api/state${qs}`);
    state.data = data;
    state.today = data.today;
    state.date = data.date;
    render();
  } catch (err) {
    toast(err.message, "error");
  }
}

/** Executa uma ação, recarrega a tela e mostra o erro (se houver). */
async function act(fn, success) {
  try {
    const result = await fn();
    await load();
    if (success) toast(typeof success === "function" ? success(result) : success);
    return result;
  } catch (err) {
    toast(err.message, "error");
    return undefined;
  }
}

// ---------------------------------------------------------------------------
// Renderização
// ---------------------------------------------------------------------------

function render() {
  renderHeader();
  renderSummary();
  renderRoutines();
  renderTasks();
}

function renderHeader() {
  $("#day-title").textContent = dayName(state.date);
  const sub = longDate(state.date);
  const showWeekday = ["Hoje", "Ontem", "Amanhã"].includes(dayName(state.date));
  $("#day-sub").textContent = capitalize(showWeekday ? `${fmtWeekday.format(parseISO(state.date))}, ${sub}` : sub);
  $("#day-picker").value = state.date;
  $("#go-today").hidden = state.date === state.today;
  document.title = state.date === state.today ? "Auto Reschedule" : `${dayName(state.date)} · Auto Reschedule`;

  const banner = $("#banner");
  const w = when();
  if (w === "today") {
    banner.hidden = true;
  } else {
    banner.hidden = false;
    banner.innerHTML =
      (w === "past"
        ? "<span>Você está vendo um <b>dia passado</b>. Pode registrar aqui o que esqueceu de marcar — tudo é recalculado.</span>"
        : "<span>Você está vendo uma <b>previsão</b>: considera que nada mais será feito até lá. Registros só podem ser feitos até hoje.</span>") +
      '<button class="btn small" data-action="go-today">Voltar para hoje</button>';
  }

  if (state.taskDateFor !== state.date) {
    state.taskDateFor = state.date;
    $("#task-date").value = state.date < state.today ? state.today : state.date;
  }
}

function renderSummary() {
  const s = state.data.summary;
  const chips = [];
  chips.push(
    `<span class="chip ${s.tasks_late ? "bad" : ""}"><b>${s.tasks_open}</b> ${s.tasks_open === 1 ? "tarefa aberta" : "tarefas abertas"}` +
      (s.tasks_late ? ` · ${plural(s.tasks_late, "atrasada", "atrasadas")}` : "") +
      "</span>"
  );
  if (s.tasks_done) chips.push(`<span class="chip ok"><b>${s.tasks_done}</b> ${s.tasks_done === 1 ? "concluída" : "concluídas"}</span>`);
  if (s.routines_total) {
    const doneR = s.routines_total - s.routines_open;
    chips.push(`<span class="chip ${s.routines_open ? "" : "ok"}"><b>${doneR}/${s.routines_total}</b> rotinas em dia</span>`);
  }
  $("#summary").innerHTML = chips.join("");
}

function renderRoutines() {
  const list = $("#routine-list");
  const routines = state.data.routines;
  if (!routines.length) {
    list.innerHTML = `<div class="empty"><strong>Nenhuma rotina para este dia.</strong>
      Crie uma meta diária, por exemplo <em>"Estudar 1h do curso"</em>.<br>Se num dia faltar, a diferença soma no dia seguinte.</div>`;
    return;
  }
  list.innerHTML = routines.map(routineCard).join("");
}

function routineStatus(r, s) {
  const A = (x) => fmtAmount(r, x);
  const w = when();
  if (s.paused && s.required <= EPS) return { main: "Pausada", sub: "sem meta enquanto estiver pausada" };
  if (s.required <= EPS) {
    if (s.extra > EPS) return { main: `+${A(s.extra)} de saldo`, sub: "feito em um dia sem meta" };
    return { main: s.skipped ? "Dia dispensado" : "Dia livre", sub: "sem meta neste dia" };
  }
  if (s.remaining <= EPS) {
    return { main: "Concluída ✓", sub: s.extra > EPS ? `e ainda sobrou ${A(s.extra)} de saldo` : `${A(s.required)} cumprido` };
  }
  if (w === "future") return { main: `Previsão: ${A(s.remaining)}`, sub: "se nada mais for feito até lá" };
  if (w === "past") return { main: `Faltou ${A(s.remaining)}`, sub: `de ${A(s.required)} — foi somado ao dia seguinte` };
  return { main: `Faltam ${A(s.remaining)}`, sub: `de ${A(s.required)} hoje` };
}

function routineCard(r) {
  const s = r.day;
  const A = (x) => fmtAmount(r, x);
  const w = when();
  const st = routineStatus(r, s);
  const hasDebt = s.debt_in > EPS && s.remaining > EPS;

  const badges = [];
  if (s.credit_out > EPS) badges.push(`<span class="badge credit" title="Saldo disponível para gastar">Saldo ${A(s.credit_out)}</span>`);
  if (hasDebt) badges.push(`<span class="badge debt" title="Acumulado dos dias anteriores">+${A(s.debt_in)} acumulado</span>`);
  if (s.paused) badges.push('<span class="badge warn">Pausada</span>');
  else if (s.skipped) badges.push('<span class="badge">Dia dispensado</span>');
  else if (!s.planned_weekday) badges.push('<span class="badge">Dia sem meta</span>');

  const meta = [`${A(r.plan.amount)} por dia`, weekdaysText(r.plan.weekdays)];
  if (r.max_debt) meta.push(`acumula até ${A(r.max_debt)}`);
  if (r.auto_use_balance) meta.push("usa saldo automaticamente");

  // Barra: verde = feito, azul-petróleo = coberto com saldo.
  const req = s.required;
  const donePct = req > EPS ? Math.min(100, (s.done / req) * 100) : s.done > EPS ? 100 : 0;
  const spentPct = req > EPS ? Math.min(100 - donePct, (s.spent / req) * 100) : 0;

  const breakdown = [];
  breakdown.push(`<li>Meta do dia <b>${s.goal > EPS ? A(s.goal) : "—"}</b></li>`);
  if (s.debt_in > EPS) breakdown.push(`<li class="debt">Acumulado <b>${A(s.debt_in)}</b></li>`);
  breakdown.push(`<li>Feito <b>${A(s.done)}</b></li>`);
  if (s.spent > EPS) breakdown.push(`<li class="credit">Coberto com saldo <b>${A(s.spent)}</b></li>`);
  if (s.forgiven > EPS) breakdown.push(`<li title="Passou do limite de acúmulo">Descartado pelo limite <b>${A(s.forgiven)}</b></li>`);

  const actions = [];
  if (w !== "future") {
    if (r.paused_now && w === "today") {
      actions.push(`<button class="btn small" data-action="resume">${ICONS.play} Retomar rotina</button>`);
    }
    const quick = r.unit === "time" ? [15, 30, 60] : [1, 5];
    for (const q of quick) {
      const label = r.unit === "time" ? A(q) : fmtNumber(q);
      actions.push(`<button class="btn small" data-action="log" data-amount="${q}" title="Registrar +${esc(A(q))}">+${esc(label)}</button>`);
    }
    actions.push('<button class="btn small" data-action="log-custom">Outro valor…</button>');
    if (s.remaining > EPS) {
      actions.push(`<button class="btn small ok" data-action="finish" title="Registra o que falta">${ICONS.check} Concluir (${A(s.remaining)})</button>`);
      if (s.credit_out > EPS) {
        const use = Math.min(s.credit_out, s.remaining);
        actions.push(`<button class="btn small credit" data-action="spend" title="Cobre a pendência com o saldo">${ICONS.coin} Usar saldo (${A(use)})</button>`);
      }
    }
  }

  const dots = r.recent
    .map((d) => {
      let cls = d.status;
      if (d.date === state.today) cls += " today";
      else if (d.date > state.today) cls = "future";
      const label = d.date > state.today ? "previsão" : d.date === state.today && d.status === "pending" ? "em aberto" : STATUS_LABEL[d.status];
      return `<span class="dot ${cls}" title="${esc(fmtShortWeekday.format(parseISO(d.date)))} — ${label}"></span>`;
    })
    .join("");

  const entries = r.entries_on_day
    .map((e) => {
      const label = e.type === "progress" ? `+${A(e.amount)}` : e.type === "spend" ? `saldo −${A(e.amount)}` : "dia dispensado";
      return `<span class="entry-chip">${label}<button data-action="del-entry" data-entry="${e.id}" title="Desfazer este registro">${ICONS.x}</button></span>`;
    })
    .join("");

  const classes = ["routine", `st-${s.status}`];
  if (hasDebt) classes.push("has-debt");

  return `<article class="${classes.join(" ")}" data-id="${r.id}">
    <header class="r-head">
      <div class="r-titles">
        <h3>${esc(r.title)}</h3>
        <p class="r-meta">${esc(meta.join(" · "))}</p>
      </div>
      <div class="r-badges">${badges.join("")}</div>
      <button class="icon-btn sm" data-action="routine-menu" title="Mais opções" aria-label="Mais opções">${ICONS.more}</button>
    </header>
    <div class="r-status"><strong>${esc(st.main)}</strong><span>${esc(st.sub)}</span></div>
    <div class="progress" role="progressbar" aria-valuenow="${Math.round(donePct + spentPct)}" aria-valuemin="0" aria-valuemax="100">
      <div class="seg done" style="width:${donePct}%"></div><div class="seg spent" style="width:${spentPct}%"></div>
    </div>
    <ul class="breakdown">${breakdown.join("")}</ul>
    ${r.notes ? `<p class="task-notes">${esc(r.notes)}</p>` : ""}
    ${actions.length ? `<div class="r-actions">${actions.join("")}</div>` : ""}
    <footer class="r-foot">
      <div class="dots"><span class="lbl">Últimos dias</span>${dots}</div>
      <div class="entries">${entries}</div>
    </footer>
  </article>`;
}

function renderTasks() {
  const list = $("#task-list");
  const tasks = state.data.tasks;
  if (!tasks.length) {
    const msg = when() === "past" ? "Nenhuma tarefa neste dia." : "Nada pendente por aqui. 🎉";
    list.innerHTML = `<li class="empty"><strong>${msg}</strong>Adicione uma tarefa acima — se não der tempo, ela passa sozinha para o dia seguinte.</li>`;
    return;
  }
  const open = tasks.filter((t) => t.status !== "done");
  const done = tasks.filter((t) => t.status === "done");
  let html = open.map(taskItem).join("");
  if (done.length) {
    html += `<li class="task-group-title">Concluídas</li>` + done.map(taskItem).join("");
  }
  list.innerHTML = html;
}

function taskItem(t) {
  const tags = [];
  const late = t.days_late;
  if (t.status === "rolled") {
    tags.push('<span class="badge warn">Não concluída — passou para o dia seguinte</span>');
  }
  if (late > 0 && t.status !== "done") {
    tags.push(`<span class="badge late" title="Data original: ${shortDate(t.date)}">Adiada há ${plural(late, "dia", "dias")} · desde ${shortDate(t.date)}</span>`);
  } else if (late > 0) {
    tags.push(`<span class="badge">Concluída com ${plural(late, "dia", "dias")} de atraso</span>`);
  }
  const doneTitle = t.status === "done" ? "Desmarcar" : "Marcar como concluída";
  return `<li class="task st-${t.status}" data-id="${t.id}">
    <button class="check" data-action="toggle-task" title="${doneTitle}" aria-label="${doneTitle}">${ICONS.check}</button>
    <div class="task-body">
      <div class="task-title">${esc(t.title)}</div>
      <div class="task-tags">${tags.join("")}</div>
      ${t.notes ? `<p class="task-notes">${esc(t.notes)}</p>` : ""}
    </div>
    <div class="task-actions">
      <button class="icon-btn sm" data-action="edit-task" title="Editar" aria-label="Editar">${ICONS.edit}</button>
      <button class="icon-btn sm" data-action="delete-task" title="Excluir" aria-label="Excluir">${ICONS.trash}</button>
    </div>
  </li>`;
}

// ---------------------------------------------------------------------------
// Modal, menu e toasts
// ---------------------------------------------------------------------------

const modal = { el: $("#modal"), form: $("#modal-form"), onSubmit: null, onClose: null };

function openModal({ title, body, submitLabel = "Salvar", danger = false, wide = false, hideSubmit = false, cancelLabel = "Cancelar", onSubmit, onOpen, onClose }) {
  $("#modal-title").textContent = title;
  $("#modal-body").innerHTML = body;
  const submit = $("#modal-submit");
  submit.textContent = submitLabel;
  submit.className = `btn ${danger ? "danger" : "primary"}`;
  submit.hidden = hideSubmit;
  submit.disabled = false;
  modal.form.querySelector(".modal-foot [data-close]").textContent = cancelLabel;
  modal.el.classList.toggle("wide", wide);
  setModalError(null);
  modal.onSubmit = onSubmit || null;
  modal.onClose = onClose || null;
  modal.el.showModal();
  onOpen?.($("#modal-body"));
  const first = $("#modal-body").querySelector("input:not([type=hidden]):not([type=radio]):not([type=checkbox]):not([disabled]), textarea");
  if (first) {
    first.focus();
    first.select?.();
  } else if (!hideSubmit) {
    submit.focus();
  }
}

function closeModal() {
  if (modal.el.open) modal.el.close();
}

function setModalError(message) {
  const el = $("#modal-error");
  el.hidden = !message;
  el.textContent = message || "";
}

modal.form.addEventListener("submit", async (ev) => {
  ev.preventDefault();
  if (!modal.onSubmit) return closeModal();
  const btn = $("#modal-submit");
  btn.disabled = true;
  try {
    const result = await modal.onSubmit(new FormData(modal.form), modal.form);
    if (result !== false) closeModal();
  } catch (err) {
    setModalError(err.message);
  } finally {
    btn.disabled = false;
  }
});

modal.form.addEventListener("click", (ev) => {
  if (ev.target.closest("[data-close]")) closeModal();
});

modal.el.addEventListener("close", () => {
  if (modal.el.open) return; // outro modal já foi aberto em seguida
  const cb = modal.onClose;
  modal.onSubmit = modal.onClose = null;
  cb?.();
});

function confirmDialog(title, message, label = "Excluir") {
  return new Promise((resolve) => {
    let ok = false;
    openModal({
      title,
      body: `<p style="margin:0">${message}</p>`,
      submitLabel: label,
      danger: true,
      onSubmit: () => {
        ok = true;
      },
      onClose: () => resolve(ok),
    });
  });
}

function openMenu(anchor, items) {
  const menu = $("#menu");
  menu.innerHTML = items
    .map((it, i) => (it === "-" ? "<hr>" : `<button data-i="${i}" class="${it.danger ? "danger" : ""}" role="menuitem">${it.icon || ""}${esc(it.label)}</button>`))
    .join("");
  menu.hidden = false;
  const rect = anchor.getBoundingClientRect();
  const mw = menu.offsetWidth;
  const mh = menu.offsetHeight;
  let left = Math.min(rect.right - mw, window.innerWidth - mw - 8);
  left = Math.max(8, left);
  let top = rect.bottom + 6;
  if (top + mh > window.innerHeight - 8) top = Math.max(8, rect.top - mh - 6);
  menu.style.left = `${left}px`;
  menu.style.top = `${top}px`;
  menu.onclick = (ev) => {
    const btn = ev.target.closest("button[data-i]");
    if (!btn) return;
    closeMenu();
    items[+btn.dataset.i].run();
  };
  menu.querySelector("button")?.focus();
}

function closeMenu() {
  $("#menu").hidden = true;
}

document.addEventListener("mousedown", (ev) => {
  if (!$("#menu").hidden && !ev.target.closest("#menu")) closeMenu();
});
window.addEventListener("resize", closeMenu);
window.addEventListener("scroll", closeMenu, true);

function toast(message, kind = "") {
  const el = document.createElement("div");
  el.className = `toast ${kind}`;
  el.textContent = message;
  $("#toasts").append(el);
  setTimeout(() => el.remove(), kind === "error" ? 5000 : 2800);
}

// ---------------------------------------------------------------------------
// Tarefas
// ---------------------------------------------------------------------------

$("#task-form").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const input = $("#task-title");
  const title = input.value.trim();
  if (!title) return;
  const date = $("#task-date").value || state.today;
  const ok = await act(() => api("POST", "/api/tasks", { title, date }), date === state.date ? "Tarefa adicionada" : `Tarefa adicionada para ${dayName(date).toLowerCase()} (${shortDate(date)})`);
  if (ok) {
    input.value = "";
    input.focus();
  }
});

$("#task-list").addEventListener("click", async (ev) => {
  const btn = ev.target.closest("[data-action]");
  if (!btn) return;
  const id = btn.closest("[data-id]").dataset.id;
  const task = state.data.tasks.find((t) => t.id === id);
  if (!task) return;

  switch (btn.dataset.action) {
    case "toggle-task":
      if (task.status === "done") {
        await act(() => api("POST", `/api/tasks/${id}/reopen`), "Tarefa reaberta");
      } else {
        const msg = when() === "future" ? "Concluída hoje, antes do prazo!" : "Tarefa concluída ✓";
        await act(() => api("POST", `/api/tasks/${id}/complete`, { date: state.date }), msg);
      }
      break;
    case "edit-task":
      openTaskModal(task);
      break;
    case "delete-task":
      if (await confirmDialog("Excluir tarefa", `Excluir <b>${esc(task.title)}</b>? Isso não pode ser desfeito.`)) {
        await act(() => api("DELETE", `/api/tasks/${id}`), "Tarefa excluída");
      }
      break;
  }
});

function openTaskModal(task) {
  const done = task.status === "done";
  openModal({
    title: "Editar tarefa",
    body: `
      <label class="field"><span>Título</span><input name="title" maxlength="200" value="${esc(task.title)}" required></label>
      <label class="field"><span>Data</span><input type="date" name="date" value="${task.date}" ${done ? "disabled" : ""}>
        <small>${done ? "Desmarque a tarefa para mudar a data." : "Mudar a data é uma forma de adiar manualmente. Se ficar pendente, ela continua passando para o dia seguinte."}</small></label>
      <label class="field"><span>Anotações</span><textarea name="notes" maxlength="2000" placeholder="Opcional">${esc(task.notes)}</textarea></label>`,
    onSubmit: async (fd) => {
      const body = { title: fd.get("title"), notes: fd.get("notes") };
      if (!done) body.date = fd.get("date");
      await api("PATCH", `/api/tasks/${task.id}`, body);
      await load();
      toast("Tarefa atualizada");
    },
  });
}

// ---------------------------------------------------------------------------
// Rotinas
// ---------------------------------------------------------------------------

$("#new-routine").addEventListener("click", () => openRoutineModal(null));

$("#routine-list").addEventListener("click", async (ev) => {
  const btn = ev.target.closest("[data-action]");
  if (!btn) return;
  const id = btn.closest("[data-id]").dataset.id;
  const r = state.data.routines.find((x) => x.id === id);
  if (!r) return;
  const s = r.day;

  switch (btn.dataset.action) {
    case "log":
      await logProgress(r, +btn.dataset.amount);
      break;
    case "log-custom":
      openLogModal(r);
      break;
    case "finish":
      await logProgress(r, s.remaining);
      break;
    case "spend":
      await act(() => api("POST", `/api/routines/${id}/entries`, { type: "spend", date: state.date }), (e) => `Usou ${fmtAmount(r, e.amount)} do saldo`);
      break;
    case "resume":
      await act(() => api("POST", `/api/routines/${id}/resume`), "Rotina retomada — a meta volta a valer hoje");
      break;
    case "del-entry":
      await act(() => api("DELETE", `/api/routines/${id}/entries/${btn.dataset.entry}`), "Registro desfeito");
      break;
    case "routine-menu":
      openRoutineMenu(btn, r);
      break;
  }
});

async function logProgress(r, amount) {
  const before = r.day;
  await act(
    () => api("POST", `/api/routines/${r.id}/entries`, { type: "progress", date: state.date, amount }),
    () => {
      const after = state.data.routines.find((x) => x.id === r.id)?.day;
      if (after && before.remaining > EPS && after.remaining <= EPS) {
        return after.extra > EPS ? `Meta cumprida! 🎉 +${fmtAmount(r, after.extra)} foi para o saldo` : "Meta do dia cumprida! 🎉";
      }
      if (after && before.remaining <= EPS && after.extra > EPS) return `+${fmtAmount(r, amount)} no saldo`;
      return `Registrado +${fmtAmount(r, amount)}`;
    }
  );
}

function openRoutineMenu(anchor, r) {
  const s = r.day;
  const w = when();
  const items = [];
  if (w !== "future") {
    if (s.credit_out > EPS && s.remaining > EPS) {
      items.push({ label: "Usar parte do saldo…", icon: ICONS.coin, run: () => openSpendModal(r) });
    }
    if (!s.skipped && !s.paused && s.goal > EPS) {
      items.push({
        label: "Dispensar este dia (sem meta)",
        icon: ICONS.skip,
        run: () => act(() => api("POST", `/api/routines/${r.id}/entries`, { type: "skip", date: state.date }), "Dia dispensado — a meta de hoje não vai acumular"),
      });
    }
  }
  if (r.paused_now) {
    items.push({ label: "Retomar rotina", icon: ICONS.play, run: () => act(() => api("POST", `/api/routines/${r.id}/resume`), "Rotina retomada") });
  } else {
    items.push({
      label: "Pausar rotina (férias, doença…)",
      icon: ICONS.pause,
      run: () => act(() => api("POST", `/api/routines/${r.id}/pause`), "Rotina pausada a partir de hoje — nada novo vai acumular"),
    });
  }
  items.push({ label: "Histórico", icon: ICONS.history, run: () => openHistoryModal(r) });
  items.push({ label: "Editar", icon: ICONS.edit, run: () => openRoutineModal(r) });
  items.push("-");
  items.push({
    label: "Excluir rotina",
    icon: ICONS.trash,
    danger: true,
    run: async () => {
      if (await confirmDialog("Excluir rotina", `Excluir <b>${esc(r.title)}</b> e todo o seu histórico? Isso não pode ser desfeito.`)) {
        await act(() => api("DELETE", `/api/routines/${r.id}`), "Rotina excluída");
      }
    },
  });
  openMenu(anchor, items);
}

function amountInput(r, name, value = "", extra = "") {
  return r.unit === "time"
    ? `<input name="${name}" value="${esc(value)}" placeholder="ex.: 45min, 1h, 1h30" ${extra}>`
    : `<input name="${name}" type="number" step="any" min="0" value="${esc(value)}" ${extra}>`;
}

function quickFill(r, values) {
  return `<div class="quick">${values.map((v) => `<button type="button" class="btn small" data-fill="${esc(r.unit === "time" ? fmtMinutes(v) : v)}">${fmtAmount(r, v)}</button>`).join("")}</div>`;
}

function bindQuickFill(body, name) {
  body.addEventListener("click", (ev) => {
    const b = ev.target.closest("[data-fill]");
    if (!b) return;
    const input = body.querySelector(`[name="${name}"]`);
    input.value = b.dataset.fill;
    input.focus();
  });
}

function openLogModal(r) {
  const s = r.day;
  const A = (x) => fmtAmount(r, x);
  const suggestions = new Set(r.unit === "time" ? [15, 30, 45, 60, 90, 120] : [1, 2, 5, 10]);
  if (s.remaining > EPS) suggestions.add(s.remaining);
  const pendingText = s.remaining > EPS ? `Pendente neste dia: <b>${A(s.remaining)}</b>. O que passar disso vira saldo.` : "A meta deste dia já foi cumprida — tudo o que registrar agora vira saldo.";
  openModal({
    title: `Registrar — ${r.title}`,
    body: `
      <label class="field"><span>Quanto você fez?</span>${amountInput(r, "amount", "", "required")}
        <small>Registrando em ${esc(dayName(state.date).toLowerCase())} (${shortDate(state.date)}).</small></label>
      ${quickFill(r, [...suggestions].sort((a, b) => a - b))}
      <p class="note">${pendingText}</p>`,
    submitLabel: "Registrar",
    onOpen: (body) => bindQuickFill(body, "amount"),
    onSubmit: async (fd) => {
      const amount = parseAmount(r, fd.get("amount"));
      if (!amount) throw new Error(r.unit === "time" ? "Informe um tempo válido, ex.: 45min, 1h ou 1h30." : "Informe um número maior que zero.");
      closeModal();
      await logProgress(r, amount);
    },
  });
}

function openSpendModal(r) {
  const s = r.day;
  const max = Math.min(s.credit_out, s.remaining);
  openModal({
    title: `Usar saldo — ${r.title}`,
    body: `
      <label class="field"><span>Quanto do saldo usar?</span>${amountInput(r, "amount", r.unit === "time" ? fmtMinutes(max) : fmtNumber(max), "required")}
        <small>Saldo disponível: ${fmtAmount(r, s.credit_out)} · pendente: ${fmtAmount(r, s.remaining)} · máximo: ${fmtAmount(r, max)}.</small></label>`,
    submitLabel: "Usar saldo",
    onSubmit: async (fd) => {
      const amount = parseAmount(r, fd.get("amount"));
      if (!amount) throw new Error("Informe uma quantidade válida.");
      await api("POST", `/api/routines/${r.id}/entries`, { type: "spend", date: state.date, amount });
      await load();
      toast(`Usou ${fmtAmount(r, Math.min(amount, max))} do saldo`);
    },
  });
}

function openRoutineModal(r) {
  const editing = !!r;
  const unit = r ? r.unit : "time";
  const plan = r ? versionOn(r, state.today) : { amount: 60, weekdays: [0, 1, 2, 3, 4, 5, 6] };
  const timeValue = unit === "time" ? fmtMinutes(plan.amount) : "1h";
  const countValue = unit === "count" ? plan.amount : 1;
  const maxDebt = r?.max_debt ? (unit === "time" ? fmtMinutes(r.max_debt) : r.max_debt) : "";
  const fakeR = { unit };

  const weekdayChips = WEEKDAYS.map(
    (name, i) => `<label><input type="checkbox" name="weekdays" value="${i}" ${plan.weekdays.includes(i) ? "checked" : ""}>${name}</label>`
  ).join("");

  openModal({
    title: editing ? "Editar rotina" : "Nova rotina acumulativa",
    body: `
      <label class="field"><span>Nome</span><input name="title" maxlength="200" placeholder="ex.: Estudar o curso de Python" value="${esc(r?.title || "")}" required></label>

      <div class="field"><span>Medir em</span>
        <div class="segmented">
          <label><input type="radio" name="unit" value="time" ${unit === "time" ? "checked" : ""} ${editing ? "disabled" : ""}>Tempo</label>
          <label><input type="radio" name="unit" value="count" ${unit === "count" ? "checked" : ""} ${editing ? "disabled" : ""}>Quantidade</label>
        </div>
        ${editing ? "<small>A unidade não pode ser trocada depois de criada.</small>" : ""}
      </div>

      <div class="field" data-unit="time"><span>Meta por dia</span>
        <input name="amount_time" value="${esc(timeValue)}" placeholder="ex.: 1h, 30min, 1h30">
        <small>Aceita 1h, 30min, 1h30, 1:30 ou só minutos (90).</small></div>

      <div class="row" data-unit="count">
        <label class="field"><span>Meta por dia</span><input name="amount_count" type="number" step="any" min="0" value="${esc(countValue)}"></label>
        <label class="field"><span>Unidade</span><input name="unit_label" maxlength="30" placeholder="ex.: páginas, exercícios" value="${esc(r?.unit === "count" ? r.unit_label : "")}"></label>
      </div>

      <div class="field"><span>Dias da semana com meta</span>
        <div class="weekdays">${weekdayChips}</div>
        <div class="weekday-presets">
          <button type="button" class="btn small ghost" data-preset="0,1,2,3,4,5,6">Todos</button>
          <button type="button" class="btn small ghost" data-preset="0,1,2,3,4">Seg a sex</button>
          <button type="button" class="btn small ghost" data-preset="5,6">Fim de semana</button>
        </div>
        <small>Nos outros dias não entra meta nova, mas o acumulado continua esperando.</small>
      </div>

      ${
        editing
          ? `<label class="field"><span>Mudanças de meta/dias valem a partir de</span><input type="date" name="effective_from" value="${state.today}">
              <small>O passado não é reescrito: os dias anteriores continuam com a meta antiga.</small></label>`
          : `<label class="field"><span>Começa em</span><input type="date" name="start_date" value="${state.date > state.today ? state.date : state.today}"></label>`
      }

      <label class="field"><span>Limite de acúmulo <small>(opcional)</small></span>
        <input name="max_debt" value="${esc(maxDebt)}" placeholder="vazio = acumula sem limite">
        <small>Ex.: com limite de 5h, a dívida nunca passa de 5h — o excedente é descartado.</small></label>

      <label class="checkline"><input type="checkbox" name="auto_use_balance" ${r?.auto_use_balance ? "checked" : ""}>
        <span>Usar o saldo automaticamente<small>Se desmarcado, o saldo fica guardado e você decide quando gastar (botão "Usar saldo").</small></span></label>

      <label class="field"><span>Anotações</span><textarea name="notes" maxlength="2000" placeholder="Opcional">${esc(r?.notes || "")}</textarea></label>`,
    submitLabel: editing ? "Salvar" : "Criar rotina",
    onOpen: (body) => {
      const sync = () => {
        const u = body.querySelector('[name="unit"]:checked').value;
        fakeR.unit = u;
        body.querySelectorAll("[data-unit]").forEach((el) => (el.hidden = el.dataset.unit !== u));
        body.querySelector('[name="max_debt"]').placeholder = u === "time" ? "ex.: 5h (vazio = sem limite)" : "ex.: 20 (vazio = sem limite)";
      };
      body.addEventListener("change", (ev) => ev.target.name === "unit" && sync());
      body.addEventListener("click", (ev) => {
        const p = ev.target.closest("[data-preset]");
        if (!p) return;
        const days = p.dataset.preset.split(",");
        body.querySelectorAll('[name="weekdays"]').forEach((cb) => (cb.checked = days.includes(cb.value)));
      });
      sync();
    },
    onSubmit: async (fd) => {
      const u = editing ? r.unit : fd.get("unit");
      const amount = u === "time" ? parseDuration(fd.get("amount_time")) : parseNumber(fd.get("amount_count"));
      if (!amount || amount <= 0) throw new Error(u === "time" ? "Informe a meta diária, ex.: 1h, 30min ou 1h30." : "Informe a meta diária (um número maior que zero).");
      const weekdays = fd.getAll("weekdays").map(Number);
      if (!weekdays.length) throw new Error("Escolha pelo menos um dia da semana.");
      const rawMax = String(fd.get("max_debt") || "").trim();
      let max_debt = null;
      if (rawMax) {
        max_debt = u === "time" ? parseDuration(rawMax) : parseNumber(rawMax);
        if (!max_debt || max_debt <= 0) throw new Error("Limite de acúmulo inválido (deixe vazio para não ter limite).");
      }
      const body = {
        title: fd.get("title"),
        notes: fd.get("notes"),
        amount,
        weekdays,
        max_debt,
        auto_use_balance: fd.get("auto_use_balance") === "on",
      };
      if (u === "count") body.unit_label = fd.get("unit_label");
      if (editing) {
        body.effective_from = fd.get("effective_from") || state.today;
        await api("PATCH", `/api/routines/${r.id}`, body);
      } else {
        body.unit = u;
        body.start_date = fd.get("start_date") || state.today;
        await api("POST", "/api/routines", body);
      }
      await load();
      toast(editing ? "Rotina atualizada" : "Rotina criada");
    },
  });
}

async function openHistoryModal(r) {
  let h;
  try {
    h = await api("GET", `/api/routines/${r.id}/history?date=${state.date}&days=60`);
  } catch (err) {
    return toast(err.message, "error");
  }
  const A = (x) => (x > EPS ? fmtAmount(r, x) : "—");
  const rows = h.days
    .map(
      (d) => `<tr>
        <td>${esc(fmtShortWeekday.format(parseISO(d.date)))}</td>
        <td>${A(d.goal)}</td>
        <td class="${d.debt_in > EPS ? "debt" : ""}">${A(d.debt_in)}</td>
        <td>${A(d.done)}</td>
        <td>${A(d.spent)}</td>
        <td class="${d.debt_out > EPS ? "debt" : ""}">${A(d.debt_out)}</td>
        <td class="${d.credit_out > EPS ? "credit" : ""}">${A(d.credit_out)}</td>
        <td>${d.date === state.today && d.status === "pending" ? "em aberto" : d.date > state.today ? "previsão" : STATUS_LABEL[d.status]}</td>
      </tr>`
    )
    .join("");
  const entryLabel = (e) => (e.type === "progress" ? `Fez +${fmtAmount(r, e.amount)}` : e.type === "spend" ? `Usou ${fmtAmount(r, e.amount)} do saldo` : "Dia dispensado");
  const entries = h.entries.length
    ? h.entries
        .slice(0, 200)
        .map(
          (e) => `<li><span><b>${esc(fmtShortWeekday.format(parseISO(e.date)))}</b> — ${entryLabel(e)}</span>
            <button type="button" class="icon-btn sm" data-del="${e.id}" title="Excluir registro">${ICONS.trash}</button></li>`
        )
        .join("")
    : '<li class="empty">Nenhum registro ainda.</li>';

  openModal({
    title: `Histórico — ${r.title}`,
    wide: true,
    hideSubmit: true,
    cancelLabel: "Fechar",
    body: `
      <p class="note">Leitura de cada linha: <b>meta</b> do dia + <b>acumulado</b> que veio de antes, menos o que foi <b>feito</b> e o <b>saldo usado</b>.
        Se faltar, vira <b>dívida</b> para o dia seguinte; se sobrar, vira <b>saldo</b>.</p>
      <div style="overflow:auto">
        <table class="hist-table">
          <thead><tr><th>Dia</th><th>Meta</th><th>Acumulado</th><th>Feito</th><th>Saldo usado</th><th>Dívida</th><th>Saldo</th><th>Situação</th></tr></thead>
          <tbody>${rows || '<tr><td colspan="8">Sem dias para mostrar.</td></tr>'}</tbody>
        </table>
      </div>
      <p class="hist-section-title">Registros</p>
      <ul class="hist-entries">${entries}</ul>`,
    onOpen: (body) => {
      body.addEventListener("click", async (ev) => {
        const b = ev.target.closest("[data-del]");
        if (!b) return;
        closeModal();
        await act(() => api("DELETE", `/api/routines/${r.id}/entries/${b.dataset.del}`), "Registro excluído");
        const fresh = state.data.routines.find((x) => x.id === r.id) || r;
        openHistoryModal(fresh);
      });
    },
  });
}

// ---------------------------------------------------------------------------
// Navegação, tema e menu principal
// ---------------------------------------------------------------------------

function setView(iso) {
  state.view = !iso || iso === state.today ? null : iso;
  load();
}

$("#prev-day").addEventListener("click", () => setView(addDays(state.date, -1)));
$("#next-day").addEventListener("click", () => setView(addDays(state.date, 1)));
$("#go-today").addEventListener("click", () => setView(null));
$("#banner").addEventListener("click", (ev) => ev.target.closest('[data-action="go-today"]') && setView(null));
$("#day-picker").addEventListener("change", (ev) => ev.target.value && setView(ev.target.value));

function currentTheme() {
  return document.documentElement.dataset.theme || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
}

$("#theme-toggle").addEventListener("click", () => {
  const next = currentTheme() === "dark" ? "light" : "dark";
  document.documentElement.dataset.theme = next;
  try {
    localStorage.setItem("ar-theme", next);
  } catch {}
});

$("#app-menu-btn").addEventListener("click", (ev) => {
  openMenu(ev.currentTarget, [
    {
      label: "Exportar backup (JSON)",
      icon: ICONS.download,
      run: () => {
        const a = document.createElement("a");
        a.href = "/api/export";
        a.download = `auto-reschedule-backup-${state.today}.json`;
        a.click();
      },
    },
    { label: "Como funciona", icon: ICONS.info, run: openHelp },
    "-",
    {
      label: "Encerrar aplicativo",
      icon: ICONS.power,
      danger: true,
      run: async () => {
        if (!(await confirmDialog("Encerrar", "Encerrar o servidor do Auto Reschedule? Seus dados já estão salvos.", "Encerrar"))) return;
        try {
          await api("POST", "/api/shutdown");
        } catch {}
        document.body.innerHTML = '<div class="empty" style="margin:20vh auto;max-width:420px"><strong>Aplicativo encerrado.</strong>Pode fechar esta janela.</div>';
        window.close();
      },
    },
  ]);
});

function openHelp() {
  openModal({
    title: "Como funciona",
    hideSubmit: true,
    cancelLabel: "Entendi",
    body: `
      <p style="margin:0"><b>Tarefas</b> têm uma data. Se o dia passar e ela não for marcada, ela aparece no dia seguinte com a etiqueta <i>"Adiada há N dias"</i> — e continua assim até você concluir.</p>
      <p style="margin:0"><b>Rotinas acumulativas</b> têm uma meta por dia (ex.: 1h de estudo).</p>
      <ul style="margin:0;padding-left:20px;display:grid;gap:4px">
        <li>Não fez? A meta do dia seguinte vira <b>meta + acumulado</b> (1h + 1h = 2h).</li>
        <li>Fez só parte? Registre o que fez (ex.: +30min) e só o resto acumula.</li>
        <li>Fez a mais? O excedente vira <b>saldo</b>. Use o botão <i>"Usar saldo"</i> para cobrir uma pendência quando quiser (ou ative o uso automático na rotina).</li>
        <li>Imprevisto? <i>Dispensar este dia</i> zera a meta só daquele dia; <i>Pausar</i> congela a rotina por vários dias.</li>
        <li>Esqueceu de marcar ontem? Volte para o dia (←) e registre lá — tudo é recalculado.</li>
      </ul>
      <p class="note">Atalhos: <b>←</b>/<b>→</b> mudam o dia, <b>T</b> vai para hoje, <b>N</b> cria uma tarefa.</p>
      <p class="note">Feito por <b>Hasten-Coubath</b>. Os dados ficam salvos só no seu computador (pasta <code>data/</code>).</p>`,
  });
}

document.addEventListener("keydown", (ev) => {
  if (ev.key === "Escape") closeMenu();
  if (modal.el.open || ev.ctrlKey || ev.metaKey || ev.altKey) return;
  if (ev.target.closest("input, textarea, select")) return;
  if (ev.key === "ArrowLeft") setView(addDays(state.date, -1));
  else if (ev.key === "ArrowRight") setView(addDays(state.date, 1));
  else if (ev.key.toLowerCase() === "t") setView(null);
  else if (ev.key.toLowerCase() === "n") {
    ev.preventDefault();
    $("#task-title").focus();
  } else return;
});

// Recarrega quando a janela volta ao foco e quando vira o dia.
document.addEventListener("visibilitychange", () => document.visibilityState === "visible" && load());
setInterval(() => {
  const now = toISO(new Date());
  if (now !== state.localDay) {
    state.localDay = now;
    load();
  }
}, 30000);

load();

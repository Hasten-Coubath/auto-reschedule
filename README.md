<p align="center">
  <img src="web/icon-192.png" alt="Ícone do Auto Reschedule" width="88">
</p>

<h1 align="center">Auto Reschedule</h1>

<p align="center">
  <b>Uma lista de tarefas que não deixa nada para trás.</b><br>
  O que você não concluiu hoje vai sozinho para amanhã, e as metas diárias que ficaram pela metade <b>acumulam</b> até você pagar a diferença.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/vers%C3%A3o-1.1.0-4f46e5" alt="Versão 1.1.0">
  <img src="https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white" alt="Python 3.9+">
  <img src="https://img.shields.io/badge/depend%C3%AAncias-nenhuma-success" alt="Sem dependências">
  <img src="https://img.shields.io/badge/plataforma-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey" alt="Plataformas">
  <img src="https://img.shields.io/badge/licen%C3%A7a-MIT-blue" alt="Licença MIT">
</p>

<p align="center"><b>Autor:</b> <a href="https://github.com/Hasten-Coubath">Hasten-Coubath</a></p>

![Tela principal do Auto Reschedule](docs/screenshot.png)

<details>
<summary>🌙 Ver no tema escuro</summary>

![Tela principal no tema escuro](docs/screenshot-escuro.png)

</details>

---

## 📑 Sumário

- [Sobre o projeto](#-sobre-o-projeto)
- [Novidades da versão 1.1](#-novidades-da-versão-11)
- [Funcionalidades](#-funcionalidades)
- [Como funciona (as regras)](#-como-funciona-as-regras)
  - [1. Tarefas que passam para o dia seguinte](#1-tarefas-que-passam-para-o-dia-seguinte)
  - [2. Prioridades e etiquetas](#2-prioridades-e-etiquetas)
  - [3. Subtarefas](#3-subtarefas)
  - [4. Tarefas recorrentes (sem acúmulo)](#4-tarefas-recorrentes-sem-acúmulo)
  - [5. Rotinas acumulativas](#5-rotinas-acumulativas)
  - [6. Saldo](#6-saldo-fazer-a-mais-para-gastar-depois)
  - [7. Cronômetro](#7-cronômetro)
  - [8. Imprevistos: dispensar dia, pausar e limite de acúmulo](#8-imprevistos-dispensar-dia-pausar-e-limite-de-acúmulo)
  - [9. Avisos e notificações](#9-avisos-e-notificações)
- [Requisitos](#-requisitos)
- [Instalação](#-instalação)
- [Como usar](#-como-usar)
- [Atalho com ícone e iniciar junto com o Windows](#-atalho-com-ícone-e-iniciar-junto-com-o-windows)
- [Gerar o executável (.exe)](#-gerar-o-executável-exe)
- [Onde ficam os dados e como fazer backup](#-onde-ficam-os-dados-e-como-fazer-backup)
- [Estrutura do projeto](#-estrutura-do-projeto)
- [Arquitetura](#-arquitetura)
- [API local](#-api-local)
- [Testes](#-testes)
- [Privacidade e segurança](#-privacidade-e-segurança)
- [Solução de problemas](#-solução-de-problemas)
- [Ideias para o futuro](#-ideias-para-o-futuro)
- [Licença](#-licença)
- [Autor](#-autor)

---

## 💡 Sobre o projeto

Listas de tarefas comuns têm dois problemas:

1. Quando o dia acaba e você não marcou uma tarefa, ela simplesmente **some** (ou fica esquecida no passado).
2. Hábitos do tipo *"estudar 1h do curso por dia"* são tratados como "feito / não feito". Se você pulou um dia, a lista não te cobra a hora que ficou faltando.

O **Auto Reschedule** resolve os dois:

- **Tarefas não concluídas são reagendadas automaticamente** para o dia seguinte, com uma etiqueta mostrando há quantos dias estão atrasadas.
- **Rotinas acumulativas** guardam a diferença: se a meta é 1h e você não estudou hoje, amanhã a meta é **2h**. Fez só uma parte? Só o resto acumula. Estudou a mais? O excedente vira **saldo** para gastar em outro dia.

Ele roda **inteiramente no seu computador**: um pequeno servidor local em Python (sem nenhuma biblioteca externa) e uma interface que abre em uma janela própria. Nada vai para a internet.

---

## 🆕 Novidades da versão 1.1

| Novidade | Resumo |
|---|---|
| ⏱️ **Cronômetro** | Ligue enquanto faz a atividade de uma rotina de tempo. Ao atingir a meta, um aviso lembra você de parar — ou de continuar e ganhar saldo. |
| 🧩 **Subtarefas** | Quebre tarefas grandes em etapas. Marcou todas, a tarefa é concluída sozinha. |
| 🔁 **Tarefas recorrentes** | Semanal, mensal ou a cada N dias — sem acúmulo. |
| 🚩 **Prioridades** | Alta, normal ou baixa. As de prioridade alta aparecem primeiro. |
| 🏷️ **Etiquetas** | `#faculdade`, `#casa`… com filtro por etiqueta. |
| 🔔 **Notificações** | Lembrete de fim do dia com o que ainda falta e aviso de meta do cronômetro. |
| 📦 **Executável** | Gere um `AutoReschedule.exe` que roda sem Python instalado. |
| 🖼️ **Ícone** | Ícone novo em todos os lugares: janela, barra de tarefas, atalho e `.exe`. |

---

## ✨ Funcionalidades

**Tarefas**
- ✅ Criar tarefas com data, anotações, **prioridade** e **etiquetas**.
- ⏭️ Tarefa não concluída **passa sozinha para o dia seguinte** (e para o outro, e para o outro…) até ser marcada.
- 🏷️ Etiqueta "**Adiada há N dias · desde dd/mm**" para você ver o que está enrolando.
- ⚡ Criação rápida: digite `Entregar trabalho #faculdade !alta` e a tarefa já sai com etiqueta e prioridade.
- 🧩 **Subtarefas** com progresso (`2/3`). Marcar todas conclui a tarefa; desmarcar uma reabre.
- 🔁 **Tarefas recorrentes simples**: toda semana em dias escolhidos, todo mês num dia fixo ou a cada N dias, com data final opcional.
- 🔎 **Filtro por etiqueta** com um clique.
- ✏️ Editar, reabrir, excluir e adiar manualmente (mudando a data).
- 🏁 Concluir antes do prazo: a tarefa é registrada no dia em que foi feita.

**Rotinas acumulativas**
- ⏱️ Meta diária em **tempo** (`1h`, `30min`, `1h30`…) ou em **quantidade** (páginas, exercícios, questões…).
- 📈 **Acúmulo automático**: o que faltar hoje soma na meta de amanhã.
- ➖ **Abater parte**: registre o quanto fez (`+15min`, `+30min`, `+1h` ou qualquer valor) e só o restante acumula.
- 💰 **Saldo**: fez a mais? O excedente fica guardado. Gaste quando quiser com o botão **"Usar saldo"** (total ou parcial) — ou ative o **uso automático**.
- ⏲️ **Cronômetro** com pausar/continuar, aviso ao atingir a meta e correção do tempo antes de registrar.
- 📅 **Dias da semana**: escolha em quais dias a meta vale (todos, seg–sex, fins de semana ou qualquer combinação).
- 🛑 **Dispensar um dia** (imprevisto), **pausar** a rotina (férias, doença) e **limite de acúmulo** opcional.
- 🔁 Mudar a meta **não reescreve o passado**: a nova meta vale a partir da data que você escolher.
- 📊 **Histórico** dia a dia (meta, acumulado, feito, saldo usado, dívida, saldo) com opção de desfazer qualquer registro.
- 🟩 Mini-calendário dos **últimos 7 dias** em cada rotina.

**Geral**
- 🗓️ Navegue entre os dias (← →): veja o **passado** (e registre o que esqueceu de marcar) ou a **previsão** de dias futuros.
- 🔔 **Notificações na área de trabalho**: lembrete de fim do dia (horário configurável) e aviso de meta do cronômetro, com som opcional.
- 🌗 Tema claro e escuro (segue o sistema, com botão para alternar).
- 💾 Dados em um arquivo JSON local, com **gravação atômica** e **backup automático diário** (últimos 14 dias).
- 📤 Exportar backup com um clique.
- 🖥️ Atalho com ícone na Área de Trabalho e no Menu Iniciar, e opção de **executável `.exe`**.
- 🔌 **Zero dependências**: só precisa do Python instalado (ou nem isso, usando o `.exe`).

---

## 📐 Como funciona (as regras)

> O app **não precisa ficar aberto** para "virar o dia". Tudo é recalculado a partir dos seus registros sempre que você abre a tela. Pode ficar uma semana sem abrir que, ao voltar, as contas estarão certas.

### 1. Tarefas que passam para o dia seguinte

Uma tarefa tem uma **data**. A partir dessa data, ela aparece em **todos os dias** até ser concluída.

| Dia          | O que você vê                                                        |
|--------------|----------------------------------------------------------------------|
| Seg (12/10)  | "Entregar relatório" — pendente                                      |
| Ter (13/10)  | "Entregar relatório" — 🔴 *Adiada há 1 dia · desde 12/10*             |
| Qua (14/10)  | "Entregar relatório" — 🔴 *Adiada há 2 dias · desde 12/10* → ✅ feito |
| Qui (15/10)  | (não aparece mais)                                                   |

Se você navegar para um dia passado, verá a tarefa com a etiqueta *"Não concluída — passou para o dia seguinte"*.

### 2. Prioridades e etiquetas

- **Prioridade:** `Alta`, `Normal` (padrão) ou `Baixa`. Entre as tarefas abertas, as de prioridade **alta** aparecem primeiro (com uma faixa vermelha); depois vêm as normais e por último as baixas. Dentro de cada grupo, as mais atrasadas vêm antes.
- **Etiquetas:** palavras livres para agrupar tarefas (`faculdade`, `casa`, `trabalho`…). Clique numa etiqueta, ou use a barra de filtros acima da lista, para ver só as tarefas dela.

**Atalho no campo "Adicionar tarefa":**

| Você digita | Resultado |
|---|---|
| `Estudar para a prova #faculdade` | etiqueta **faculdade** |
| `Pagar boleto #casa #contas !alta` | etiquetas **casa** e **contas**, prioridade **alta** |
| `Organizar fotos !baixa` | prioridade **baixa** |
| `Ligar para o banco !` | `!` sozinho (ou `!!`) também vale **alta** |

Também dá para escolher a prioridade na caixa ao lado do campo, ou abrir o formulário completo (repetição, subtarefas, etiquetas…) pelo botão **Mais opções**, ao lado de "Adicionar".

### 3. Subtarefas

Tarefas grandes podem ser divididas em **subtarefas** ("requisitos"). Exemplo:

```
☐ Entregar trabalho de Banco de Dados   🧩 2/3
   ☑ Modelo ER
   ☑ Scripts SQL
   ☐ Relatório final
```

- Adicione pelo ícone de lista no item da tarefa (ou no formulário de edição). No campo inline, `Enter` salva e já deixa pronto para a próxima.
- Ao marcar **a última** subtarefa, a tarefa é **concluída sozinha**. Se você desmarcar uma subtarefa de uma tarefa concluída, ela é **reaberta**.
- As subtarefas acompanham a tarefa quando ela passa para o dia seguinte. Nos dias passados, você vê o que já estava marcado naquele dia.
- Em tarefas **recorrentes**, as subtarefas são desmarcadas a cada nova repetição (útil para checklists, ex.: "Faxina: banheiro, cozinha, quartos").

### 4. Tarefas recorrentes (sem acúmulo)

Para coisas que se repetem mas **não devem acumular** (ex.: tomar remédio, regar as plantas, pagar a fatura todo dia 10):

| Tipo | Exemplo | Quando aparece |
|---|---|---|
| **Semanal** | Regar as plantas — seg e qui | Nos dias da semana escolhidos |
| **Mensal** | Pagar a fatura — todo dia 15 | No dia do mês escolhido (em meses mais curtos, no último dia: "dia 31" vira 30/04, 28/02…) |
| **A cada N dias** | Trocar a água do filtro — a cada 3 dias | A cada N dias, contando da data de início |

Todas aceitam uma data final opcional ("Até").

**Regra:** cada repetição pendente continua aparecendo (com a etiqueta *"Atrasada há N dias"*) **só até a próxima repetição chegar**. Aí ela é substituída — não se acumulam várias pendências da mesma tarefa.

| Dia | "Regar as plantas" (seg e qui) |
|---|---|
| Seg | pendente |
| Ter | 🔴 atrasada há 1 dia (a repetição de segunda continua) |
| Qua | 🔴 atrasada há 2 dias → no histórico: *"Não feita — substituída pela próxima repetição"* |
| Qui | pendente (só a repetição de quinta; a de segunda saiu) |

Não dá para marcar uma repetição que ainda não chegou (a caixinha fica bloqueada nos dias futuros).

### 5. Rotinas acumulativas

Uma rotina tem uma **meta por dia**. A cada dia o app calcula:

```
necessário hoje = meta do dia + acumulado dos dias anteriores
acumulado de amanhã = necessário hoje − (o que você fez + saldo que você usou)
```

**Exemplo** — rotina *"Estudar 1h do curso"*, todos os dias:

| Dia | Meta | Acumulado (veio de antes) | Necessário | Feito    | Resultado                         |
|-----|------|---------------------------|------------|----------|-----------------------------------|
| Seg | 1h   | —                         | 1h         | 30min    | faltou 30min → acumula            |
| Ter | 1h   | 30min                     | **1h30**   | —        | faltou 1h30 → acumula             |
| Qua | 1h   | 1h30                      | **2h30**   | 1h + 2h  | cumpriu e sobrou **30min de saldo** |
| Qui | 1h   | —                         | 1h         | …        |                                   |

Para **abater uma parte**, basta registrar o que você fez (botões `+15min`, `+30min`, `+1h`, "Outro valor…", "Concluir" ou o **cronômetro**). Você pode registrar várias vezes no mesmo dia; cada registro aparece como uma etiqueta no rodapé do cartão (com um ✕ para desfazer).

Formatos aceitos para tempo: `1h`, `30min`, `1h30`, `1h 30m`, `1:30`, `1,5h` ou só minutos (`90`).

### 6. Saldo (fazer a mais para gastar depois)

O que você fizer **além** do necessário vira **saldo**. Existem dois modos (configurável em cada rotina):

- **Manual (padrão):** o saldo fica guardado e você decide quando gastar. Quando houver pendência e saldo disponível, aparece o botão **"Usar saldo (X)"**, que cobre a pendência com o saldo. Pelo menu `⋯ → Usar parte do saldo…` dá para usar só uma parte.
- **Automático:** marque *"Usar o saldo automaticamente"* e o saldo cobre sozinho as pendências dos próximos dias.

Exemplo com uso automático, meta de 30min/dia: estudou 1h30 na segunda → sobrou 1h de saldo → terça e quarta já ficam ✅ automaticamente, cobertas pelo saldo.

> O que você faz a mais primeiro **paga o acumulado**; só o que sobra depois disso vira saldo.

### 7. Cronômetro

Disponível nas rotinas medidas em **tempo**. Em vez de anotar quanto estudou, ligue o cronômetro quando começar:

1. Clique em **⏱ Cronômetro** no cartão da rotina. O tempo aparece no cartão, na barra de progresso (faixa listrada), no topo da janela e no título da janela, então dá para acompanhar mesmo com o app minimizado.
2. Precisou parar um pouco? Use **Pausar** e depois **Continuar**.
3. Quando o tempo contado **atingir o que falta da meta do dia**, você recebe um **aviso** (notificação na área de trabalho + som + janela no app):
   - **Parar e registrar** → o tempo vira um registro de progresso.
   - **Continuar contando** → o cronômetro segue; tudo o que passar da meta vira **saldo** quando você parar.
4. Ao parar, o app mostra o tempo contado e deixa você **corrigir antes de salvar**. Isso serve para quando você esqueceu o cronômetro ligado depois de terminar. Também há a opção **Descartar** (🗑), que não registra nada.

Detalhes:
- O cronômetro fica salvo no arquivo de dados. Se você fechar a janela, reiniciar o PC ou abrir no dia seguinte, ele **continua contando** de onde estava.
- O tempo é registrado **no dia em que o cronômetro foi ligado** (se você ligou às 23h e parou à 1h, conta para o dia em que começou).
- Se o cronômetro contou menos de 1 minuto, o campo vem vazio: digite o tempo ou descarte.
- O aviso de meta aparece uma vez por sessão de cronômetro. Se a meta do dia já estava cumprida quando você ligou, não há aviso: tudo vira saldo.

### 8. Imprevistos: dispensar dia, pausar e limite de acúmulo

| Recurso | Para quê | Efeito |
|---|---|---|
| **Dias da semana** | A rotina só vale em certos dias (ex.: seg–sex) | Nos outros dias não entra meta nova, mas o acumulado continua esperando (e pode ser abatido). |
| **Dispensar este dia** (`⋯`) | Um imprevisto pontual | A meta *daquele dia* não é somada. O acumulado antigo continua. Pode ser desfeito. |
| **Pausar rotina** (`⋯`) | Férias, doença, semana de provas… | Enquanto pausada, nenhuma meta nova acumula. Ao **retomar**, a meta volta a valer a partir do dia da retomada. |
| **Limite de acúmulo** | Evitar uma "bola de neve" impossível | A dívida nunca passa do limite (ex.: 5h). O excedente é descartado e aparece como *"Descartado pelo limite"*. |
| **Mudar a meta** | Ex.: passar de 1h para 45min | Cria uma nova versão do plano que vale **a partir da data escolhida**. Os dias anteriores continuam calculados com a meta antiga. |

**Esqueceu de registrar ontem?** Volte para o dia (seta ← ou clique na data) e registre lá. Tudo é recalculado em cascata.

**Dias futuros** mostram uma **previsão**: quanto será necessário naquele dia se nada mais for feito até lá. Registros só podem ser feitos até hoje.

### 9. Avisos e notificações

Configure em `⋯ → Configurações e avisos`:

| Opção | Padrão | O que faz |
|---|---|---|
| **Lembrete no fim do dia** | ligado, **20:00** | Uma vez por dia, depois do horário escolhido, se ainda houver tarefas abertas ou rotinas pendentes, mostra uma notificação com o resumo (ex.: *"Estudar 1h do curso: falta 1h30 · 3 tarefas abertas"*). |
| **Avisar quando o cronômetro atingir a meta** | ligado | O aviso descrito no item 7. |
| **Tocar um som nos avisos** | ligado | Um "plim" curto junto com a notificação. |

- Na primeira vez, o navegador pede **permissão para mostrar notificações**. Clique em **Permitir** (ou use o botão *Permitir notificações* nas configurações). Use **Testar aviso** para conferir.
- As notificações aparecem na central de notificações do Windows (ou do sistema) **enquanto a janela do app estiver aberta**. Ela pode ficar minimizada.
- Se a permissão for negada, os avisos continuam aparecendo **dentro do app**.
- Se você abrir o app depois do horário do lembrete, o lembrete aparece logo ao abrir (uma vez por dia).

---

## 🧰 Requisitos

- **Python 3.9 ou mais recente**: [python.org/downloads](https://www.python.org/downloads/)
  - No Windows, marque a opção **"Add python.exe to PATH"** durante a instalação.
  - *Não precisa de Python* se você usar o [executável `.exe`](#-gerar-o-executável-exe).
- Um navegador moderno. Para abrir em **janela própria** (sem barra de endereço), o app usa o **Microsoft Edge** (já vem no Windows) ou o **Google Chrome/Chromium**. Se nenhum for encontrado, abre no navegador padrão.

Não há `pip install` para usar o app: o projeto usa apenas a biblioteca padrão do Python. (O PyInstaller só é necessário se você quiser **gerar** o `.exe`.)

---

## 📥 Instalação

```bash
git clone https://github.com/Hasten-Coubath/auto-reschedule.git
cd auto-reschedule
```

Ou baixe o ZIP pelo botão **Code → Download ZIP** no GitHub e extraia em qualquer pasta.

---

## ▶️ Como usar

### Windows

- **Dê dois cliques em `iniciar.bat`.** Uma janela de console abre (deixe-a aberta) e o app aparece em uma janela própria.
- Prefere sem console? Use **`iniciar-sem-console.bat`**. Para encerrar, use o menu `⋯ → Encerrar aplicativo` dentro do app.
- Quer um ícone na Área de Trabalho? Dê dois cliques em **`criar-atalho.bat`** (veja [abaixo](#-atalho-com-ícone-e-iniciar-junto-com-o-windows)).

### Linux / macOS

```bash
chmod +x iniciar.sh   # só na primeira vez
./iniciar.sh
```

### Pela linha de comando (qualquer sistema)

```bash
python app.py
```

| Opção | Descrição |
|---|---|
| `--tab` | Abre como uma aba comum do navegador, em vez de janela própria. |
| `--no-browser` | Só inicia o servidor, sem abrir janela (útil para iniciar com o sistema). |
| `--port 9000` | Usa outra porta (padrão: `8765`). |
| `--data CAMINHO` | Usa outro arquivo de dados (ex.: uma pasta do OneDrive/Dropbox para sincronizar). |
| `--criar-atalho` | Cria atalhos com o ícone do app na Área de Trabalho e no Menu Iniciar (Windows) e sai. |

Variáveis de ambiente equivalentes: `AUTO_RESCHEDULE_PORT` e `AUTO_RESCHEDULE_DATA`.

Depois de iniciado, o app também pode ser acessado em **http://127.0.0.1:8765**. Se você rodar o `iniciar.bat` com o app já aberto, ele apenas abre uma nova janela (não dá erro de porta ocupada).

### Atalhos de teclado

| Tecla | Ação |
|---|---|
| `←` / `→` | Dia anterior / próximo dia |
| `T` | Voltar para hoje |
| `N` | Ir para o campo "Adicionar tarefa" |
| `Enter` | Salvar (no campo de tarefa, de subtarefa ou nos formulários) |
| `Esc` | Fechar janela/menu ou o campo de nova subtarefa |

### Fluxo típico do dia

1. Abra o app. Ele já mostra **hoje**, com o que ficou de ontem somado.
2. Vai estudar? Clique em **⏱ Cronômetro** e comece. Quando a meta for atingida, o app avisa.
3. Fez um pedaço sem cronômetro? Clique em `+30min` (ou "Outro valor…").
4. Terminou uma tarefa (ou uma subtarefa)? Clique no quadradinho ✓.
5. Não deu tempo? Não faça nada: amanhã estará tudo lá. Às 20h o lembrete de fim do dia mostra o que ainda falta.

---

## 🖥️ Atalho com ícone e iniciar junto com o Windows

**Criar atalho com o ícone do app** (Área de Trabalho + Menu Iniciar):

- Dê dois cliques em **`criar-atalho.bat`**, ou rode `python app.py --criar-atalho`.
- O atalho abre o app **sem janela de console** e usa o ícone `web/icon.ico`.
- Se você mover a pasta do projeto, rode de novo para atualizar o atalho.

**Iniciar junto com o Windows:**

1. Crie o atalho como acima.
2. Pressione `Win + R`, digite `shell:startup` e dê Enter.
3. Copie o atalho **Auto Reschedule** da Área de Trabalho para essa pasta.
4. (Opcional) Para iniciar só o servidor, sem abrir a janela, clique com o botão direito no atalho → *Propriedades* e acrescente ` --no-browser` no fim do campo **Destino**. Depois é só abrir o app pelo atalho normal quando quiser ver a lista. Nesse caso, os avisos só aparecem com a janela aberta.

> **Sobre o ícone:** o ícone oficial é o [`web/icon.svg`](web/icon.svg). Os arquivos `icon.ico`, `icon-192.png` e `icon-512.png` são gerados a partir dele com `python tools/gerar_icones.py`, que usa o próprio Edge/Chrome para desenhar o SVG. Se você mudar o SVG, rode esse comando de novo.

---

## 📦 Gerar o executável (.exe)

Dá para empacotar o app em **um único arquivo `AutoReschedule.exe`**, que roda em qualquer Windows **sem Python instalado**:

1. Dê dois cliques em **`gerar-exe.bat`**. Ele instala o [PyInstaller](https://pyinstaller.org) e gera o executável.
   Ou, manualmente:
   ```bash
   python -m pip install -r requirements-build.txt
   python tools/build_exe.py
   ```
2. O resultado fica em **`dist/AutoReschedule.exe`** (~9 MB), já com o ícone do app.

Como o executável funciona:
- Abre o app direto, **sem janela de console**. Para encerrar, use `⋯ → Encerrar aplicativo`.
- Os dados ficam na pasta **`data/` ao lado do `.exe`**. Copie o `.exe` para onde quiser (ex.: `Documentos\AutoReschedule\`) antes de começar a usar.
- Aceita as mesmas opções da linha de comando (`--port`, `--data`, `--criar-atalho`…).
- As pastas `build/` e `dist/` estão no `.gitignore`. Para distribuir o `.exe`, anexe-o a uma *Release* do GitHub em vez de colocá-lo no repositório.

> O Windows SmartScreen ou o antivírus podem desconfiar de executáveis recém-gerados e sem assinatura digital. Isso é comum com PyInstaller. Clique em *Mais informações → Executar assim mesmo* se confiar no arquivo que você mesmo gerou.

---

## 💾 Onde ficam os dados e como fazer backup

| Item | Local |
|---|---|
| Dados | `data/dados.json` (dentro da pasta do projeto, ou ao lado do `.exe`) |
| Backups automáticos | `data/backups/dados-AAAA-MM-DD.json` (um por dia, mantém os últimos 14) |

- A pasta `data/` está no `.gitignore`, então **seus dados pessoais não vão para o GitHub**.
- A gravação é **atômica** (escreve em um arquivo temporário e substitui): mesmo que o PC desligue no meio, o arquivo não corrompe.
- Se o arquivo de dados estiver corrompido (ex.: editado à mão com erro), ele é renomeado para `dados.corrompido-<data>.json` e o app começa vazio. Nada é apagado.
- Arquivos da versão 1.0 são **atualizados automaticamente** para o formato novo ao abrir (as tarefas antigas ganham prioridade "normal", sem etiquetas nem subtarefas).

**Exportar:** menu `⋯ → Exportar backup (JSON)`.

**Restaurar:** feche o app, copie o backup desejado para `data/dados.json` e abra o app de novo.

**Usar em mais de um computador:** aponte o `--data` para uma pasta sincronizada (OneDrive, Dropbox, Google Drive), por exemplo:

```bash
python app.py --data "C:/Users/voce/OneDrive/auto-reschedule/dados.json"
```

> Evite deixar o app aberto em dois computadores ao mesmo tempo com o mesmo arquivo.

---

## 🗂️ Estrutura do projeto

```
auto-reschedule/
├── app.py                    # Ponto de entrada: sobe o servidor, abre a janela, cria atalhos
├── autoreschedule/
│   ├── __init__.py           # Versão e autor
│   ├── core.py               # Regras de negócio (rolagem, recorrência, subtarefas, acúmulo,
│   │                         #   saldo, cronômetro, configurações) — puro, sem I/O
│   ├── storage.py            # Persistência em JSON, gravação atômica, backups, migração
│   └── server.py             # Servidor HTTP local + API JSON (biblioteca padrão)
├── web/
│   ├── index.html            # Estrutura da interface
│   ├── styles.css            # Visual (tema claro/escuro, responsivo)
│   ├── app.js                # Lógica da interface (JavaScript puro, sem frameworks)
│   ├── icon.svg              # Ícone oficial
│   ├── icon.ico              # Ícone do Windows (atalho e .exe) — gerado do SVG
│   ├── icon-192.png          # Ícones PNG da janela/notificações — gerados do SVG
│   ├── icon-512.png
│   └── manifest.webmanifest  # Nome, cores e ícones da janela do app
├── tools/
│   ├── gerar_icones.py       # Gera .ico/.png a partir do icon.svg
│   └── build_exe.py          # Gera o executável com o PyInstaller
├── tests/
│   └── test_core.py          # Testes das regras de negócio
├── docs/                     # Imagens do README
├── iniciar.bat               # Inicia no Windows
├── iniciar-sem-console.bat   # Inicia no Windows sem janela de console
├── criar-atalho.bat          # Cria atalho com ícone na Área de Trabalho/Menu Iniciar
├── gerar-exe.bat             # Gera dist/AutoReschedule.exe
├── iniciar.sh                # Inicia no Linux/macOS
├── requirements-build.txt    # Só para gerar o .exe (PyInstaller)
├── LICENSE
└── README.md
```

---

## 🏗️ Arquitetura

```
┌──────────────────────┐   HTTP (127.0.0.1)   ┌──────────────────────────┐
│  Janela do app       │ ───────────────────▶ │ server.py (http.server)  │
│  web/ (HTML/CSS/JS)  │ ◀─────────────────── │   └── core.py (regras)   │
│  + notificações      │        JSON          │   └── storage.py (JSON)  │
└──────────────────────┘                      └────────────┬─────────────┘
                                                           ▼
                                                  data/dados.json
```

**Princípio central: nada é "rolado" na virada do dia.** O app guarda apenas *fatos* (tarefas com data e data de conclusão; rotinas com seus registros de progresso, uso de saldo e dias dispensados). O estado de qualquer dia é **recalculado** por uma simulação dia a dia em `core.simulate()`:

```
para cada dia, do início da rotina até o dia consultado:
    meta      = meta do plano vigente (0 se pausado, dispensado ou fora dos dias da semana)
    necessário = meta + dívida
    pago       = feito + saldo usado (manual) + saldo usado (automático, se ativo)
    se pago ≥ necessário: saldo += pago − necessário; dívida = 0
    senão:                dívida = necessário − pago (respeitando o limite, se houver)
```

As **tarefas recorrentes** seguem a mesma ideia: para um dia D, o app procura a **repetição vigente** (a mais recente que já chegou até D) e verifica se ela foi concluída. Não existe "gerar a próxima repetição"; tudo sai da regra de repetição.

O **cronômetro** guarda só o momento em que foi ligado e o tempo acumulado nas pausas. O tempo atual é calculado na hora, por isso ele sobrevive a janelas fechadas e reinicializações.

Vantagens dessa abordagem:
- Funciona mesmo se o app ficar dias fechado (não depende de tarefa agendada).
- Registrar algo em um dia passado, ou desfazer um registro, corrige automaticamente todos os dias seguintes.
- Permite navegar no passado e ver previsões do futuro com a mesma função.

### Formato dos dados (`data/dados.json`)

```jsonc
{
  "version": 2,
  "settings": {                         // configurações de avisos
    "notify_end_of_day": true, "notify_time": "20:00",
    "notify_timer": true, "sound": true
  },
  "tasks": [
    {
      "id": "a1b2c3d4e5f6",
      "title": "Entregar trabalho de Banco de Dados",
      "notes": "",
      "date": "2026-10-12",             // data planejada (nas recorrentes: início)
      "priority": "high",               // "high" | "normal" | "low"
      "tags": ["faculdade"],
      "subtasks": [
        { "id": "...", "title": "Modelo ER", "done_on": "2026-10-13" },  // null = não feita
        { "id": "...", "title": "Relatório final", "done_on": null }
      ],
      "repeat": null,                   // ou uma regra de repetição (abaixo)
      "completed_on": null,             // data em que foi concluída (tarefas comuns)
      "completions": {},                // recorrentes: { "data da repetição": "dia em que foi feita" }
      "created_at": "2026-10-12T09:00:00"
    }
  ],
  // Regras de repetição possíveis ("until" é opcional):
  //   { "type": "weekly",   "weekdays": [0, 3], "until": null }
  //   { "type": "monthly",  "day": 15,          "until": null }
  //   { "type": "interval", "every": 3,         "until": "2026-12-31" }
  "routines": [
    {
      "id": "f6e5d4c3b2a1",
      "title": "Estudar 1h do curso",
      "unit": "time",                   // "time" (minutos) ou "count"
      "unit_label": "min",              // ex.: "páginas" quando unit = "count"
      "start_date": "2026-10-12",
      "versions": [                     // histórico de metas (o passado não é reescrito)
        { "from": "2026-10-12", "amount": 60, "weekdays": [0,1,2,3,4,5,6] }
      ],
      "max_debt": null,                 // limite de acúmulo (opcional)
      "auto_use_balance": false,        // usar saldo automaticamente
      "pauses": [ { "start": "2026-12-20", "end": "2027-01-05" } ],
      "timer": {                        // cronômetro ligado (null = desligado)
        "id": "...", "date": "2026-10-15",
        "started_at": "2026-10-15T14:00:00",
        "running_since": "2026-10-15T14:20:00",  // null = pausado
        "elapsed": 600                  // segundos contados antes de running_since
      },
      "entries": [                      // fatos registrados
        { "id": "...", "type": "progress", "date": "2026-10-12", "amount": 30 },
        { "id": "...", "type": "progress", "date": "2026-10-13", "amount": 65, "source": "timer" },
        { "id": "...", "type": "spend",    "date": "2026-10-14", "amount": 15 },
        { "id": "...", "type": "skip",     "date": "2026-10-15", "amount": 0 }
      ]
    }
  ]
}
```

Dias da semana seguem a convenção do Python: `0 = segunda … 6 = domingo`. Quantidades de tempo são guardadas em **minutos**.

---

## 🔌 API local

A interface conversa com o servidor por uma API JSON simples (útil se você quiser criar scripts ou integrações). Requisições que **alteram** dados precisam do cabeçalho `X-Auto-Reschedule: 1`.

**Geral**

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/api/ping` | Verifica se o app está rodando |
| `GET` | `/api/state?date=AAAA-MM-DD` | Estado de um dia (padrão: hoje): tarefas, rotinas, cronômetros ligados, etiquetas, configurações e resumo |
| `GET` | `/api/export` | Baixa todos os dados (backup) |
| `PATCH` | `/api/settings` | Altera `{notify_end_of_day?, notify_time?, notify_timer?, sound?}` |
| `POST` | `/api/shutdown` | Encerra o servidor |

**Tarefas**

| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/api/tasks` | Cria `{title, date?, notes?, priority?, tags?, subtasks?, repeat?}` |
| `PATCH` | `/api/tasks/{id}` | Edita os mesmos campos (em `subtasks`, itens com `id` mantêm o estado) |
| `DELETE` | `/api/tasks/{id}` | Exclui |
| `POST` | `/api/tasks/{id}/complete` | Conclui `{date?}` (nas recorrentes, conclui a repetição vigente nesse dia) |
| `POST` | `/api/tasks/{id}/reopen` | Reabre `{date?}` |
| `POST` | `/api/tasks/{id}/subtasks` | Adiciona subtarefa `{title}` |
| `POST` | `/api/tasks/{id}/subtasks/{subId}/toggle` | Marca/desmarca `{date?, done?}`; responde `{task_change: "completed" \| "reopened" \| null}` |
| `DELETE` | `/api/tasks/{id}/subtasks/{subId}` | Exclui subtarefa |

**Rotinas**

| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/api/routines` | Cria `{title, unit, amount, weekdays?, start_date?, unit_label?, max_debt?, auto_use_balance?, notes?}` |
| `PATCH` | `/api/routines/{id}` | Edita (mudança de `amount`/`weekdays` vale a partir de `effective_from`) |
| `DELETE` | `/api/routines/{id}` | Exclui a rotina e seu histórico |
| `GET` | `/api/routines/{id}/history?date=&days=30` | Histórico dia a dia + registros |
| `POST` | `/api/routines/{id}/entries` | Registra `{type: "progress" \| "spend" \| "skip", date?, amount?}` |
| `DELETE` | `/api/routines/{id}/entries/{entryId}` | Desfaz um registro |
| `POST` | `/api/routines/{id}/pause` | Pausa a partir de hoje |
| `POST` | `/api/routines/{id}/resume` | Retoma a partir de hoje |
| `POST` | `/api/routines/{id}/timer/start` | Liga (ou continua) o cronômetro |
| `POST` | `/api/routines/{id}/timer/pause` | Pausa o cronômetro |
| `POST` | `/api/routines/{id}/timer/stop` | Para e registra `{amount?}` (minutos; sem `amount`, usa o tempo contado) |
| `POST` | `/api/routines/{id}/timer/cancel` | Descarta o cronômetro sem registrar |

Exemplos (PowerShell):

```powershell
$h = @{ "X-Auto-Reschedule" = "1" }

# Tarefa com prioridade, etiqueta e subtarefas
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8765/api/tasks -Headers $h -ContentType "application/json" `
  -Body '{"title": "Trabalho de BD", "priority": "high", "tags": ["faculdade"], "subtasks": ["Modelo ER", "Scripts SQL"]}'

# Tarefa recorrente: todo dia 10
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8765/api/tasks -Headers $h -ContentType "application/json" `
  -Body '{"title": "Pagar a fatura", "repeat": {"type": "monthly", "day": 10}}'
```

---

## 🧪 Testes

As regras de negócio têm testes automatizados com `unittest`, também sem dependências. São 44 testes, cobrindo:
- acúmulo, saldo, pausa, limite e rolagem de tarefas;
- prioridades, etiquetas e subtarefas;
- tarefas recorrentes (semanal, mensal com meses curtos, a cada N dias, data final);
- cronômetro e configurações;
- migração de arquivos antigos.

```bash
python -m unittest discover -s tests -v
```

Para **simular outro dia** sem mexer no relógio do computador (útil para testar o acúmulo), defina a variável `AUTO_RESCHEDULE_TODAY`:

```powershell
# PowerShell
$env:AUTO_RESCHEDULE_TODAY = "2026-12-25"; python app.py --data teste.json
```

```bash
# Linux/macOS
AUTO_RESCHEDULE_TODAY=2026-12-25 python3 app.py --data teste.json
```

---

## 🔒 Privacidade e segurança

- O servidor escuta **somente em `127.0.0.1`**: nenhum outro computador da rede consegue acessá-lo.
- Nenhum dado é enviado para a internet; não há contas, telemetria nem bibliotecas de terceiros. As notificações são geradas localmente pelo navegador.
- Requisições que alteram dados exigem um cabeçalho próprio, o que impede que **sites abertos no seu navegador** mexam nas suas tarefas (proteção contra CSRF).
- O cabeçalho `Host` é validado, protegendo contra ataques de *DNS rebinding*.

---

## 🛠️ Solução de problemas

<details>
<summary><b>"python" não é reconhecido como um comando</b></summary>

O Python não está instalado ou não está no PATH. Instale pelo [python.org](https://www.python.org/downloads/) marcando **"Add python.exe to PATH"**. O `iniciar.bat` também tenta usar o lançador `py`, que vem com o instalador oficial. Outra opção é usar o [`.exe`](#-gerar-o-executável-exe).
</details>

<details>
<summary><b>"Não foi possível usar a porta 8765"</b></summary>

Outro programa está usando a porta. Inicie com outra: `python app.py --port 8800`.
</details>

<details>
<summary><b>Abriu como aba do navegador em vez de janela própria</b></summary>

O modo janela depende do Edge, Chrome ou Chromium. Se nenhum for encontrado, o app abre no navegador padrão. Funciona igual.
</details>

<details>
<summary><b>As notificações não aparecem</b></summary>

1. Abra `⋯ → Configurações e avisos` e veja o status da permissão. Clique em **Permitir notificações** e depois em **Testar aviso**.
2. Se aparecer "bloqueadas": clique no ícone à esquerda do endereço (ou nas configurações do site no Edge/Chrome) → **Notificações → Permitir**.
3. No Windows, confira se as notificações do **Microsoft Edge/Google Chrome** estão ativadas em *Configurações → Sistema → Notificações* e se o **Não incomodar** está desligado.
4. A janela do app precisa estar aberta (pode estar minimizada). Com a janela minimizada por muito tempo, o navegador pode atrasar o aviso em até ~1 minuto.
</details>

<details>
<summary><b>A janela ainda mostra o ícone antigo</b></summary>

O navegador guarda ícones em cache. Feche todas as janelas do app e abra de novo. Se continuar, recrie o atalho com `criar-atalho.bat`. O Windows também guarda cache de ícones de atalho; reiniciar o Explorer (ou o PC) resolve.
</details>

<details>
<summary><b>Esqueci o cronômetro ligado</b></summary>

Clique em **Parar e registrar** e corrija o tempo no campo *"Quanto registrar?"* antes de salvar, ou use a lixeira para descartar. O tempo vai para o dia em que o cronômetro foi ligado.
</details>

<details>
<summary><b>Usei o iniciar-sem-console.bat (ou o .exe) e não sei como fechar</b></summary>

Use o menu `⋯ → Encerrar aplicativo` na janela do app. Fechar só a janela deixa o servidor rodando em segundo plano (ele usa pouquíssimos recursos); ao abrir de novo, ele reaproveita o servidor existente.
</details>

<details>
<summary><b>A meta acumulou demais e ficou impossível</b></summary>

Edite a rotina e defina um **limite de acúmulo**, use **Dispensar este dia** nos dias de imprevisto, ou **pause** a rotina durante férias. Você também pode excluir registros no **Histórico**.
</details>

<details>
<summary><b>Registrei algo errado</b></summary>

Clique no ✕ da etiqueta do registro (rodapé do cartão da rotina) ou abra `⋯ → Histórico` e exclua o registro. Tudo é recalculado.
</details>

---

## 🧭 Ideias para o futuro

Já feito na versão 1.1:

- [x] Notificações na área de trabalho no fim do dia
- [x] Categorias / etiquetas e prioridades para tarefas
- [x] Tarefas recorrentes simples (sem acúmulo)
- [x] Empacotar como executável (`.exe`) com PyInstaller
- [x] Cronômetro para atividades de tempo, com aviso ao atingir a meta
- [x] Subtarefas para tarefas maiores

Próximos passos:

- [ ] Gráficos de evolução por rotina
- [ ] Importar backup pela própria interface

Sugestões e *pull requests* são bem-vindos!

---

## 📄 Licença

Distribuído sob a licença **MIT**. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

## 👤 Autor

Desenvolvido por **Hasten-Coubath**.

- GitHub: [@Hasten-Coubath](https://github.com/Hasten-Coubath)

Se este projeto te ajudou a não deixar os estudos acumularem, deixe uma ⭐ no repositório!

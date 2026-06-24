ADMIN_HTML = r"""
<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>TG Publisher Admin</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f5f7fa;
      --panel: #ffffff;
      --panel-soft: #f8fafc;
      --text: #16202a;
      --muted: #64748b;
      --line: #d8e0ea;
      --accent: #1267a8;
      --accent-strong: #0b4e82;
      --danger: #b42318;
      --danger-bg: #fff1f0;
      --ok: #067647;
      --ok-bg: #e7f8ee;
      --warn: #9a6700;
      --warn-bg: #fff6d7;
      --shadow: 0 10px 28px rgba(22, 32, 42, 0.08);
    }

    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: var(--bg);
      color: var(--text);
    }
    header {
      background: #101820;
      color: #fff;
      padding: 18px 28px;
      display: flex;
      justify-content: space-between;
      gap: 18px;
      align-items: center;
    }
    h1, h2, h3 { margin: 0; letter-spacing: 0; }
    header h1 { font-size: 20px; font-weight: 750; }
    header p {
      margin: 4px 0 0;
      color: #cbd5e1;
      font-size: 13px;
      line-height: 1.35;
    }
    .top-meta {
      color: #e2e8f0;
      font-size: 13px;
      text-align: right;
      line-height: 1.45;
    }
    main {
      display: grid;
      grid-template-columns: 340px minmax(0, 1fr);
      min-height: calc(100vh - 76px);
    }
    aside {
      border-right: 1px solid var(--line);
      background: #fbfcfe;
      padding: 18px;
    }
    .workspace {
      padding: 22px;
      max-width: 1220px;
      width: 100%;
    }
    .panel, .side-box {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: var(--shadow);
    }
    .panel-head {
      padding: 18px 20px;
      border-bottom: 1px solid var(--line);
      display: flex;
      justify-content: space-between;
      gap: 16px;
      align-items: flex-start;
    }
    .panel-head h2 { font-size: 20px; }
    .panel-head p {
      margin: 5px 0 0;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.45;
    }
    .panel-body { padding: 20px; }
    .toolbar {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      align-items: center;
    }
    button {
      border: 1px solid var(--line);
      border-radius: 7px;
      background: #fff;
      color: var(--text);
      min-height: 38px;
      padding: 0 13px;
      font: inherit;
      font-size: 14px;
      cursor: pointer;
    }
    button.primary {
      background: var(--accent);
      border-color: var(--accent);
      color: #fff;
      font-weight: 700;
    }
    button.primary:hover { background: var(--accent-strong); }
    button.danger {
      color: var(--danger);
      border-color: #efb5ae;
    }
    button:disabled {
      opacity: .55;
      cursor: not-allowed;
    }
    .side-box {
      padding: 14px;
      margin-bottom: 14px;
      box-shadow: none;
    }
    .side-box h2 {
      font-size: 15px;
      margin-bottom: 8px;
    }
    .side-box p, .small {
      color: var(--muted);
      font-size: 13px;
      line-height: 1.45;
      margin: 0;
    }
    .system-list {
      display: grid;
      gap: 6px;
      margin-top: 10px;
    }
    .system-row {
      display: flex;
      justify-content: space-between;
      gap: 10px;
      font-size: 13px;
      color: var(--muted);
    }
    .system-row strong {
      color: var(--text);
      font-weight: 700;
      text-align: right;
    }
    .channel-list {
      display: grid;
      gap: 8px;
      margin-top: 12px;
    }
    .channel-item {
      width: 100%;
      min-height: 76px;
      text-align: left;
      border-radius: 8px;
      padding: 11px 12px;
      background: #fff;
    }
    .channel-item.active {
      border-color: var(--accent);
      box-shadow: 0 0 0 2px rgba(18, 103, 168, 0.13);
    }
    .channel-title {
      display: flex;
      justify-content: space-between;
      gap: 8px;
      font-weight: 750;
      margin-bottom: 5px;
    }
    .channel-sub {
      color: var(--muted);
      font-size: 12px;
      line-height: 1.35;
      word-break: break-word;
    }
    .badge {
      display: inline-flex;
      align-items: center;
      min-height: 22px;
      border-radius: 999px;
      padding: 0 8px;
      font-size: 12px;
      font-weight: 750;
      white-space: nowrap;
    }
    .badge.on { color: var(--ok); background: var(--ok-bg); }
    .badge.off { color: var(--muted); background: #edf1f5; }
    .badge.warn { color: var(--warn); background: var(--warn-bg); }
    .badge.err { color: var(--danger); background: var(--danger-bg); }
    form {
      display: grid;
      gap: 20px;
    }
    .section {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
      padding: 16px;
    }
    .section h3 {
      font-size: 16px;
      margin-bottom: 4px;
    }
    .section-note {
      color: var(--muted);
      font-size: 13px;
      line-height: 1.45;
      margin: 0 0 14px;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 14px;
    }
    .grid.three { grid-template-columns: repeat(3, minmax(0, 1fr)); }
    label.field {
      display: grid;
      gap: 6px;
      color: var(--text);
      font-size: 13px;
      font-weight: 750;
    }
    .hint {
      color: var(--muted);
      font-size: 12px;
      line-height: 1.35;
      font-weight: 500;
    }
    input, select, textarea {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 7px;
      background: #fff;
      color: var(--text);
      font: inherit;
      font-size: 14px;
      padding: 10px 11px;
      outline: none;
    }
    input:focus, select:focus, textarea:focus {
      border-color: var(--accent);
      box-shadow: 0 0 0 3px rgba(18, 103, 168, 0.12);
    }
    input[type="checkbox"] {
      width: 18px;
      height: 18px;
      padding: 0;
    }
    textarea {
      min-height: 124px;
      resize: vertical;
      line-height: 1.45;
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace;
    }
    textarea.prompt { min-height: 360px; }
    .check-row {
      display: grid;
      grid-template-columns: 22px minmax(0, 1fr);
      gap: 8px;
      align-items: start;
      padding: 12px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--panel-soft);
    }
    .check-row strong {
      display: block;
      font-size: 13px;
      margin-bottom: 3px;
    }
    .status {
      min-height: 28px;
      color: var(--muted);
      font-size: 14px;
      margin-top: 14px;
      white-space: pre-wrap;
      line-height: 1.45;
    }
    .status.ok, .notice.ok { color: var(--ok); background: var(--ok-bg); border-color: #abefc6; }
    .status.err, .notice.err { color: var(--danger); background: var(--danger-bg); border-color: #fecdca; }
    .status.warn, .notice.warn { color: var(--warn); background: var(--warn-bg); border-color: #f6d58a; }
    .notice {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      color: var(--muted);
      background: var(--panel-soft);
      font-size: 13px;
      line-height: 1.45;
      margin-top: 12px;
    }
    .preview {
      white-space: pre-wrap;
      background: #f8fafc;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
      color: #334155;
      line-height: 1.45;
      max-height: 240px;
      overflow: auto;
      margin-top: 12px;
    }
    details {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
      padding: 0;
    }
    summary {
      cursor: pointer;
      padding: 14px 16px;
      font-weight: 750;
    }
    details .details-body {
      border-top: 1px solid var(--line);
      padding: 16px;
    }
    @media (max-width: 960px) {
      header { align-items: flex-start; flex-direction: column; }
      .top-meta { text-align: left; }
      main { grid-template-columns: 1fr; }
      aside { border-right: 0; border-bottom: 1px solid var(--line); }
      .workspace { padding: 16px; }
      .panel-head { flex-direction: column; }
      .grid, .grid.three { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <header>
    <div>
      <h1>TG Publisher</h1>
      <p>Панель управления автопубликацией в Telegram-каналы.</p>
    </div>
    <div class="top-meta" id="meta">Загрузка...</div>
  </header>

  <main>
    <aside>
      <div class="side-box">
        <h2>Что делать</h2>
        <p>Выбери канал слева, измени настройки справа и нажми «Сохранить». После сохранения расписание применяется сразу.</p>
      </div>

      <div class="side-box" id="systemBox">
        <h2>Состояние</h2>
        <p id="systemText">Проверяю сервис...</p>
        <div class="system-list" id="systemList"></div>
      </div>

      <div class="toolbar">
        <button class="primary" id="newBtn" type="button">Новый канал</button>
        <button id="reloadBtn" type="button">Обновить</button>
      </div>

      <div class="channel-list" id="channelList"></div>
      <div class="status" id="sideStatus"></div>
    </aside>

    <section class="workspace">
      <div class="panel">
        <div class="panel-head">
          <div>
            <h2 id="formTitle">Канал</h2>
            <p id="formSubtitle">Основные настройки, расписание, генерация и текст промпта.</p>
          </div>
          <div class="toolbar">
            <button class="primary" id="saveBtn" type="button">Сохранить</button>
            <button id="publishBtn" type="button">Тестовая публикация</button>
            <button class="danger" id="deleteBtn" type="button">Удалить</button>
          </div>
        </div>

        <div class="panel-body">
          <div class="notice" id="channelNotice">
            Выключенный канал можно сохранить и настроить, но cron не будет публиковать его автоматически.
          </div>

          <form id="channelForm">
            <section class="section">
              <h3>1. Канал</h3>
              <p class="section-note">Здесь указывается, куда бот будет публиковать посты.</p>
              <div class="grid">
                <label class="field">Ключ канала
                  <input id="key" autocomplete="off" placeholder="test_ai_news">
                  <span class="hint">Внутреннее имя без пробелов: латиница, цифры, _ или -. Используется в webhook-командах.</span>
                </label>
                <label class="field">Название
                  <input id="title" autocomplete="off" placeholder="AI News">
                  <span class="hint">Понятное имя для списка слева. На публикацию не влияет.</span>
                </label>
                <label class="field">Telegram chat_id
                  <input id="chatId" autocomplete="off" placeholder="@channel или -1001234567890">
                  <span class="hint">Для публичного канала можно @username. Для приватного обычно нужен id вида -100...</span>
                </label>
                <label class="field">Prompt-файл
                  <input id="promptFile" autocomplete="off" placeholder="prompts/test_ai_news.md">
                  <span class="hint">Файл с инструкцией для OpenAI. Новый файл будет создан в папке prompts.</span>
                </label>
              </div>
            </section>

            <section class="section">
              <h3>2. Расписание</h3>
              <p class="section-note">Публикация запускается автоматически по cron в указанном часовом поясе.</p>
              <div class="grid">
                <label class="field">Cron
                  <input id="schedule" autocomplete="off" placeholder="0 10 * * *">
                  <span class="hint">Формат: минута час день месяц день-недели. Пример: 0 10 * * * = каждый день в 10:00.</span>
                </label>
                <label class="field">Часовой пояс
                  <input id="timezone" autocomplete="off" value="Europe/Moscow">
                  <span class="hint">Например: Europe/Moscow. В этом времени считается cron.</span>
                </label>
              </div>
            </section>

            <section class="section">
              <h3>3. Генерация поста</h3>
              <p class="section-note">Эти поля управляют тем, как OpenAI пишет текст.</p>
              <div class="grid three">
                <label class="field">Модель
                  <input id="model" autocomplete="off" placeholder="пусто = модель из .env">
                  <span class="hint">Оставь пустым, если хочешь использовать OPENAI_DEFAULT_MODEL.</span>
                </label>
                <label class="field">Лимит ответа
                  <input id="maxOutputTokens" type="number" min="100" max="8000" value="1200">
                  <span class="hint">Чем больше число, тем длиннее может быть ответ. Для Telegram обычно хватает 900-1800.</span>
                </label>
                <label class="field">Пауза между постами
                  <input id="minSeconds" type="number" min="0" value="300">
                  <span class="hint">Защита от случайных повторов. 300 = минимум 5 минут.</span>
                </label>
                <label class="field">Постов в истории
                  <input id="historyPostsLimit" type="number" min="1" max="30" value="10">
                  <span class="hint">Сколько последних публикаций передавать модели, когда история включена.</span>
                </label>
                <label class="field">Reasoning effort
                  <select id="reasoningEffort">
                    <option value="">по умолчанию</option>
                    <option value="minimal">minimal</option>
                    <option value="low">low</option>
                    <option value="medium">medium</option>
                    <option value="high">high</option>
                  </select>
                  <span class="hint">Обычно low достаточно для обычных постов.</span>
                </label>
                <label class="field">Text verbosity
                  <select id="textVerbosity">
                    <option value="">по умолчанию</option>
                    <option value="low">low</option>
                    <option value="medium">medium</option>
                    <option value="high">high</option>
                  </select>
                  <span class="hint">Насколько подробно модель пишет текст.</span>
                </label>
                <label class="field">Формат Telegram
                  <select id="parseMode">
                    <option value="">без форматирования</option>
                    <option value="HTML">HTML</option>
                    <option value="Markdown">Markdown</option>
                    <option value="MarkdownV2">MarkdownV2</option>
                  </select>
                  <span class="hint">Для текущих prompt-шаблонов лучше HTML.</span>
                </label>
              </div>
            </section>

            <section class="section">
              <h3>4. Переключатели</h3>
              <p class="section-note">Чаще всего достаточно включить канал и оставить остальные значения как есть.</p>
              <div class="grid three">
                <label class="check-row">
                  <input id="enabled" type="checkbox">
                  <span><strong>Канал включен</strong><span class="hint">Если выключено, cron не публикует посты.</span></span>
                </label>
                <label class="check-row">
                  <input id="disablePreview" type="checkbox">
                  <span><strong>Не показывать preview ссылок</strong><span class="hint">Telegram не будет раскрывать ссылки карточками.</span></span>
                </label>
                <label class="check-row">
                  <input id="protectContent" type="checkbox">
                  <span><strong>Protect content</strong><span class="hint">Telegram ограничит пересылку и сохранение контента.</span></span>
                </label>
                <label class="check-row">
                  <input id="historyEnabled" type="checkbox">
                  <span><strong>Учитывать историю постов</strong><span class="hint">Модель увидит последние публикации этого канала и постарается не повторяться.</span></span>
                </label>
              </div>
            </section>

            <details>
              <summary>Дополнительные данные для промпта</summary>
              <div class="details-body">
                <label class="field">Context JSON
                  <textarea id="contextJson" spellcheck="false">{}</textarea>
                  <span class="hint">Эти данные доступны в prompt-файле как context.topic, context.audience и т.д.</span>
                </label>
              </div>
            </details>

            <section class="section">
              <h3>5. Prompt</h3>
              <p class="section-note">Это главная инструкция для OpenAI. Пиши здесь стиль, тему, ограничения и формат ответа.</p>
              <label class="field">Текст prompt-файла
                <textarea class="prompt" id="promptContent" spellcheck="false"></textarea>
                <span class="hint">Можно использовать переменные: {{ date_ru }}, {{ time }}, {{ context.topic }}, {{ channel.title }}.</span>
              </label>
            </section>
          </form>

          <div class="status" id="mainStatus"></div>
          <div class="preview" id="publishPreview" hidden></div>
        </div>
      </div>
    </section>
  </main>

  <script>
    const els = {
      meta: document.querySelector("#meta"),
      systemText: document.querySelector("#systemText"),
      systemList: document.querySelector("#systemList"),
      channelList: document.querySelector("#channelList"),
      sideStatus: document.querySelector("#sideStatus"),
      mainStatus: document.querySelector("#mainStatus"),
      publishPreview: document.querySelector("#publishPreview"),
      formTitle: document.querySelector("#formTitle"),
      formSubtitle: document.querySelector("#formSubtitle"),
      channelNotice: document.querySelector("#channelNotice"),
      newBtn: document.querySelector("#newBtn"),
      reloadBtn: document.querySelector("#reloadBtn"),
      saveBtn: document.querySelector("#saveBtn"),
      publishBtn: document.querySelector("#publishBtn"),
      deleteBtn: document.querySelector("#deleteBtn"),
      key: document.querySelector("#key"),
      title: document.querySelector("#title"),
      chatId: document.querySelector("#chatId"),
      promptFile: document.querySelector("#promptFile"),
      timezone: document.querySelector("#timezone"),
      schedule: document.querySelector("#schedule"),
      model: document.querySelector("#model"),
      maxOutputTokens: document.querySelector("#maxOutputTokens"),
      minSeconds: document.querySelector("#minSeconds"),
      historyPostsLimit: document.querySelector("#historyPostsLimit"),
      reasoningEffort: document.querySelector("#reasoningEffort"),
      textVerbosity: document.querySelector("#textVerbosity"),
      parseMode: document.querySelector("#parseMode"),
      enabled: document.querySelector("#enabled"),
      disablePreview: document.querySelector("#disablePreview"),
      protectContent: document.querySelector("#protectContent"),
      historyEnabled: document.querySelector("#historyEnabled"),
      contextJson: document.querySelector("#contextJson"),
      promptContent: document.querySelector("#promptContent"),
    };

    let state = { channels: [], jobs: [], storage: {} };
    let selectedKey = null;
    let originalKey = null;

    async function api(path, options = {}) {
      const token = localStorage.getItem("tgPublisherAdminToken");
      const response = await fetch(path, {
        ...options,
        headers: {
          "Content-Type": "application/json",
          ...(token ? {"X-Admin-Token": token} : {}),
          ...(options.headers || {}),
        },
      });

      if (response.status === 403 || response.status === 503) {
        const entered = prompt("Введите ADMIN_API_TOKEN для прямого доступа без nginx:");
        if (entered) {
          localStorage.setItem("tgPublisherAdminToken", entered);
          return api(path, options);
        }
      }

      if (!response.ok) {
        throw new Error(await readError(response));
      }

      return response.json();
    }

    async function readError(response) {
      const contentType = response.headers.get("content-type") || "";
      if (contentType.includes("application/json")) {
        try {
          const payload = await response.json();
          if (typeof payload.detail === "string") return payload.detail;
          if (Array.isArray(payload.detail)) {
            return payload.detail.map((item) => item.msg || JSON.stringify(item)).join("\n");
          }
          return JSON.stringify(payload);
        } catch {
          return response.statusText;
        }
      }
      return (await response.text()) || response.statusText;
    }

    function setStatus(target, message, kind = "") {
      target.textContent = message;
      target.className = `status ${kind}`;
    }

    async function loadState(selectKey = null) {
      state = await api("/api/admin/state");
      renderSystem();
      renderList();
      els.meta.textContent = `${state.enabled_channels}/${state.channels.length} включено · задач: ${state.jobs.length}`;
      const key = selectKey || selectedKey || state.channels[0]?.key;
      if (key) {
        await selectChannel(key);
      } else {
        newChannel();
      }
    }

    function renderSystem() {
      const storage = state.storage || {};
      const storageOk = Boolean(
        storage.config_parent_writable &&
        storage.config_file_writable &&
        storage.prompts_dir_writable &&
        storage.history_db_writable
      );
      els.systemText.textContent = storageOk
        ? "Файлы настроек доступны для записи."
        : "Есть проблема с правами на файлы. Сохранение может не работать.";
      els.systemText.className = storageOk ? "small" : "small";
      els.systemList.innerHTML = `
        <div class="system-row"><span>Каналы</span><strong>${state.enabled_channels}/${state.channels.length}</strong></div>
        <div class="system-row"><span>Cron-задачи</span><strong>${state.jobs.length}</strong></div>
        <div class="system-row"><span>config writable</span><strong>${yesNo(storage.config_file_writable)}</strong></div>
        <div class="system-row"><span>prompts writable</span><strong>${yesNo(storage.prompts_dir_writable)}</strong></div>
        <div class="system-row"><span>history writable</span><strong>${yesNo(storage.history_db_writable)}</strong></div>
      `;
    }

    function renderList() {
      els.channelList.innerHTML = "";
      if (!state.channels.length) {
        els.channelList.innerHTML = `<div class="notice">Каналов пока нет. Нажми «Новый канал».</div>`;
        return;
      }

      for (const channel of state.channels) {
        const nextRun = nextRunFor(channel.key);
        const button = document.createElement("button");
        button.type = "button";
        button.className = `channel-item ${channel.key === selectedKey ? "active" : ""}`;
        button.innerHTML = `
          <div class="channel-title">
            <span>${escapeHtml(channel.title)}</span>
            <span class="badge ${channel.enabled ? "on" : "off"}">${channel.enabled ? "вкл" : "выкл"}</span>
          </div>
          <div class="channel-sub">${escapeHtml(channel.key)} · ${escapeHtml(channel.schedule)}</div>
          <div class="channel-sub">${escapeHtml(String(channel.chat_id))}</div>
          <div class="channel-sub">${nextRun ? `Следующий запуск: ${escapeHtml(nextRun)}` : "Нет активной cron-задачи"}</div>
        `;
        button.addEventListener("click", () => selectChannel(channel.key));
        els.channelList.appendChild(button);
      }
    }

    async function selectChannel(key) {
      const channel = state.channels.find((item) => item.key === key);
      if (!channel) return;
      selectedKey = key;
      originalKey = key;
      renderList();
      fillForm(channel);
      els.formTitle.textContent = channel.title || channel.key;
      els.formSubtitle.textContent = `${channel.key} · ${channel.enabled ? "автопубликация включена" : "автопубликация выключена"}`;
      updateChannelNotice(channel);
      try {
        const prompt = await api(`/api/admin/prompts?path=${encodeURIComponent(channel.prompt_file)}`);
        els.promptContent.value = prompt.content || "";
      } catch (error) {
        els.promptContent.value = "";
        setStatus(els.mainStatus, `Prompt не загружен: ${error.message}`, "err");
      }
    }

    function fillForm(channel) {
      els.key.value = channel.key || "";
      els.title.value = channel.title || "";
      els.chatId.value = channel.chat_id ?? "";
      els.promptFile.value = channel.prompt_file || "";
      els.timezone.value = channel.timezone || "Europe/Moscow";
      els.schedule.value = channel.schedule || "0 10 * * *";
      els.model.value = channel.model || "";
      els.maxOutputTokens.value = channel.max_output_tokens || 1200;
      els.minSeconds.value = channel.min_seconds_between_posts ?? 300;
      els.historyPostsLimit.value = channel.history_posts_limit ?? 10;
      els.reasoningEffort.value = channel.reasoning_effort || "";
      els.textVerbosity.value = channel.text_verbosity || "";
      els.parseMode.value = channel.telegram?.parse_mode || "HTML";
      els.enabled.checked = Boolean(channel.enabled);
      els.disablePreview.checked = channel.telegram?.disable_web_page_preview !== false;
      els.protectContent.checked = Boolean(channel.telegram?.protect_content);
      els.historyEnabled.checked = Boolean(channel.history_enabled);
      els.contextJson.value = JSON.stringify(channel.context || {}, null, 2);
      els.publishPreview.hidden = true;
      setStatus(els.mainStatus, "");
    }

    function buildChannelFromForm() {
      let context;
      try {
        context = JSON.parse(els.contextJson.value || "{}");
      } catch (error) {
        throw new Error(`Context JSON некорректный: ${error.message}`);
      }

      return {
        key: els.key.value.trim(),
        title: els.title.value.trim(),
        chat_id: parseChatId(els.chatId.value.trim()),
        enabled: els.enabled.checked,
        timezone: els.timezone.value.trim() || "Europe/Moscow",
        schedule: els.schedule.value.trim(),
        prompt_file: els.promptFile.value.trim(),
        model: emptyToNull(els.model.value),
        max_output_tokens: Number(els.maxOutputTokens.value || 1200),
        reasoning_effort: emptyToNull(els.reasoningEffort.value),
        text_verbosity: emptyToNull(els.textVerbosity.value),
        telegram: {
          parse_mode: emptyToNull(els.parseMode.value),
          disable_web_page_preview: els.disablePreview.checked,
          protect_content: els.protectContent.checked,
        },
        min_seconds_between_posts: Number(els.minSeconds.value || 0),
        history_enabled: els.historyEnabled.checked,
        history_posts_limit: Number(els.historyPostsLimit.value || 10),
        context,
      };
    }

    function parseChatId(value) {
      if (/^-?\d+$/.test(value)) return Number(value);
      return value;
    }

    function emptyToNull(value) {
      const trimmed = String(value || "").trim();
      return trimmed ? trimmed : null;
    }

    function newChannel() {
      selectedKey = null;
      originalKey = null;
      renderList();
      fillForm({
        key: "new_channel",
        title: "Новый канал",
        chat_id: "@your_channel",
        enabled: false,
        timezone: "Europe/Moscow",
        schedule: "0 10 * * *",
        prompt_file: "prompts/new_channel.md",
        max_output_tokens: 1200,
        min_seconds_between_posts: 300,
        history_enabled: false,
        history_posts_limit: 10,
        telegram: {
          parse_mode: "HTML",
          disable_web_page_preview: true,
          protect_content: false,
        },
        context: {
          topic: "тема канала",
          audience: "кто читает",
          style: "практично и понятно",
        },
      });
      els.promptContent.value = `Ты пишешь посты для Telegram-канала "{{ channel.title }}".

Тема: {{ context.topic }}
Аудитория: {{ context.audience }}
Дата: {{ date_ru }}

Напиши один полезный пост на русском языке.
Используй Telegram-safe HTML: <b>, <i>, <code>, <a href="">.
Не выдумывай свежие новости и статистику без источника.
Сделай сильный первый абзац, 3-5 практичных пунктов и короткий вывод.
`;
      els.formTitle.textContent = "Новый канал";
      els.formSubtitle.textContent = "Заполни поля, сохрани, затем включи канал.";
      updateChannelNotice({ enabled: false });
    }

    async function saveChannel() {
      els.saveBtn.disabled = true;
      setStatus(els.mainStatus, "Сохраняю канал, prompt и расписание...");
      try {
        const channel = buildChannelFromForm();
        const result = await api("/api/admin/channels", {
          method: "POST",
          body: JSON.stringify({
            original_key: originalKey,
            channel,
            prompt_content: els.promptContent.value,
          }),
        });
        selectedKey = result.selected_key;
        originalKey = result.selected_key;
        setStatus(els.mainStatus, "Сохранено. Расписание перечитано и уже применено.", "ok");
        await loadState(result.selected_key);
      } catch (error) {
        setStatus(els.mainStatus, friendlyError(error.message), "err");
      } finally {
        els.saveBtn.disabled = false;
      }
    }

    async function publishChannel() {
      const key = els.key.value.trim();
      if (!key) return;
      els.publishBtn.disabled = true;
      els.publishPreview.hidden = true;
      setStatus(els.mainStatus, "Генерирую пост и отправляю его в Telegram...");
      try {
        const result = await api(`/publish/${encodeURIComponent(key)}?force=true`, { method: "POST" });
        setStatus(els.mainStatus, "Тестовая публикация завершена.", "ok");
        els.publishPreview.hidden = false;
        els.publishPreview.textContent = result.result.preview || "Telegram принял сообщение, но preview пустой.";
      } catch (error) {
        setStatus(els.mainStatus, friendlyError(error.message), "err");
      } finally {
        els.publishBtn.disabled = false;
      }
    }

    async function deleteChannel() {
      const key = originalKey;
      if (!key) return;
      if (!confirm(`Удалить канал ${key} из списка? Prompt-файл останется на диске.`)) return;
      els.deleteBtn.disabled = true;
      try {
        await api(`/api/admin/channels/${encodeURIComponent(key)}`, { method: "DELETE" });
        setStatus(els.sideStatus, `Канал ${key} удален.`, "ok");
        selectedKey = null;
        originalKey = null;
        await loadState();
      } catch (error) {
        setStatus(els.mainStatus, friendlyError(error.message), "err");
      } finally {
        els.deleteBtn.disabled = false;
      }
    }

    async function reloadConfig() {
      els.reloadBtn.disabled = true;
      try {
        await api("/admin/reload", { method: "POST" });
        await loadState();
        setStatus(els.sideStatus, "Конфиг перечитан. Список каналов обновлен.", "ok");
      } catch (error) {
        setStatus(els.sideStatus, friendlyError(error.message), "err");
      } finally {
        els.reloadBtn.disabled = false;
      }
    }

    function updateChannelNotice(channel) {
      if (channel.enabled) {
        els.channelNotice.className = "notice ok";
        els.channelNotice.textContent = "Канал включен: cron будет автоматически публиковать посты по расписанию.";
      } else {
        els.channelNotice.className = "notice warn";
        els.channelNotice.textContent = "Канал выключен: настройки можно сохранять, но автоматической публикации не будет.";
      }
    }

    function nextRunFor(key) {
      const job = (state.jobs || []).find((item) => item.id === `publish:${key}`);
      if (!job?.next_run_time) return "";
      try {
        return new Date(job.next_run_time).toLocaleString("ru-RU");
      } catch {
        return job.next_run_time;
      }
    }

    function yesNo(value) {
      return value ? "да" : "нет";
    }

    function friendlyError(message) {
      if (!message) return "Неизвестная ошибка.";
      if (message.includes("OpenAI")) {
        return `${message}\n\nПосле изменения ENV_FILE перезапусти GitHub Actions, чтобы контейнер получил новый .env.`;
      }
      if (message.includes("Cannot write prompt file") || message.includes("Permission denied")) {
        return `${message}\n\nНа VPS проверь права: chown -R APP_UID:APP_GID data/config data/prompts`;
      }
      if (message.includes("Context JSON")) {
        return message;
      }
      if (message.includes("Telegram")) {
        return `${message}\n\nПроверь, что бот добавлен администратором в канал и chat_id указан верно.`;
      }
      return message;
    }

    function escapeHtml(value) {
      return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;");
    }

    els.newBtn.addEventListener("click", newChannel);
    els.reloadBtn.addEventListener("click", reloadConfig);
    els.saveBtn.addEventListener("click", saveChannel);
    els.publishBtn.addEventListener("click", publishChannel);
    els.deleteBtn.addEventListener("click", deleteChannel);
    els.enabled.addEventListener("change", () => updateChannelNotice({ enabled: els.enabled.checked }));

    loadState().catch((error) => {
      setStatus(els.sideStatus, friendlyError(error.message), "err");
      els.meta.textContent = "Ошибка загрузки";
    });
  </script>
</body>
</html>
"""

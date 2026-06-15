ADMIN_HTML = """
<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>TG Publisher Admin</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f6f7f9;
      --panel: #ffffff;
      --text: #18202a;
      --muted: #657386;
      --line: #d9e0e8;
      --accent: #1769aa;
      --accent-strong: #0f4d7c;
      --danger: #b42318;
      --ok: #067647;
      --shadow: 0 8px 30px rgba(28, 39, 49, 0.08);
    }

    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: var(--bg);
      color: var(--text);
    }
    header {
      background: #111827;
      color: #fff;
      padding: 18px 28px;
      display: flex;
      justify-content: space-between;
      gap: 16px;
      align-items: center;
    }
    header h1 {
      font-size: 20px;
      margin: 0;
      font-weight: 700;
      letter-spacing: 0;
    }
    header .meta {
      color: #c8d2df;
      font-size: 13px;
      text-align: right;
    }
    main {
      display: grid;
      grid-template-columns: 320px minmax(0, 1fr);
      min-height: calc(100vh - 68px);
    }
    aside {
      border-right: 1px solid var(--line);
      background: #fbfcfd;
      padding: 20px;
    }
    .workspace {
      padding: 24px;
      max-width: 1180px;
      width: 100%;
    }
    .panel {
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
      gap: 12px;
      align-items: center;
    }
    .panel-head h2 {
      margin: 0;
      font-size: 18px;
      letter-spacing: 0;
    }
    .panel-body { padding: 20px; }
    .toolbar {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-bottom: 16px;
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
      font-weight: 650;
    }
    button.primary:hover { background: var(--accent-strong); }
    button.danger {
      color: var(--danger);
      border-color: #f1b8b1;
    }
    button:disabled {
      opacity: .55;
      cursor: not-allowed;
    }
    .channel-list {
      display: grid;
      gap: 8px;
      margin-top: 12px;
    }
    .channel-item {
      width: 100%;
      min-height: 66px;
      text-align: left;
      border-radius: 8px;
      padding: 10px 12px;
      background: #fff;
    }
    .channel-item.active {
      border-color: var(--accent);
      box-shadow: 0 0 0 2px rgba(23, 105, 170, 0.12);
    }
    .channel-title {
      display: flex;
      justify-content: space-between;
      gap: 8px;
      font-weight: 700;
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
      font-weight: 700;
      white-space: nowrap;
    }
    .badge.on { color: var(--ok); background: #dcfae6; }
    .badge.off { color: var(--muted); background: #edf1f5; }
    form {
      display: grid;
      gap: 18px;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 14px;
    }
    .grid.three {
      grid-template-columns: repeat(3, minmax(0, 1fr));
    }
    label {
      display: grid;
      gap: 6px;
      color: var(--muted);
      font-size: 13px;
      font-weight: 650;
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
    input[type="checkbox"] {
      width: 18px;
      height: 18px;
      padding: 0;
    }
    textarea {
      min-height: 130px;
      resize: vertical;
      line-height: 1.45;
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace;
    }
    textarea.prompt {
      min-height: 360px;
    }
    .check-row {
      display: flex;
      gap: 10px;
      align-items: center;
      padding-top: 24px;
      color: var(--text);
      font-weight: 650;
    }
    .status {
      min-height: 26px;
      color: var(--muted);
      font-size: 14px;
      margin-top: 12px;
      white-space: pre-wrap;
    }
    .status.ok { color: var(--ok); }
    .status.err { color: var(--danger); }
    .preview {
      white-space: pre-wrap;
      background: #f8fafc;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
      color: #334155;
      line-height: 1.45;
      max-height: 220px;
      overflow: auto;
    }
    @media (max-width: 900px) {
      header { align-items: flex-start; flex-direction: column; }
      header .meta { text-align: left; }
      main { grid-template-columns: 1fr; }
      aside { border-right: 0; border-bottom: 1px solid var(--line); }
      .workspace { padding: 16px; }
      .grid, .grid.three { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <header>
    <h1>TG Publisher</h1>
    <div class="meta" id="meta">Загрузка...</div>
  </header>
  <main>
    <aside>
      <div class="toolbar">
        <button class="primary" id="newBtn" type="button">+ Канал</button>
        <button id="reloadBtn" type="button">↻ Reload</button>
      </div>
      <div class="channel-list" id="channelList"></div>
      <div class="status" id="sideStatus"></div>
    </aside>

    <section class="workspace">
      <div class="panel">
        <div class="panel-head">
          <h2 id="formTitle">Канал</h2>
          <div class="toolbar" style="margin:0">
            <button class="primary" id="saveBtn" type="button">Сохранить</button>
            <button id="publishBtn" type="button">Опубликовать тест</button>
            <button class="danger" id="deleteBtn" type="button">Удалить</button>
          </div>
        </div>
        <div class="panel-body">
          <form id="channelForm">
            <div class="grid">
              <label>Ключ
                <input id="key" autocomplete="off" placeholder="test_ai_news">
              </label>
              <label>Название
                <input id="title" autocomplete="off" placeholder="AI News">
              </label>
              <label>Chat ID
                <input id="chatId" autocomplete="off" placeholder="@channel или -100...">
              </label>
              <label>Prompt file
                <input id="promptFile" autocomplete="off" placeholder="prompts/test_ai_news.md">
              </label>
              <label>Timezone
                <input id="timezone" autocomplete="off" value="Europe/Moscow">
              </label>
              <label>Cron
                <input id="schedule" autocomplete="off" placeholder="0 10 * * *">
              </label>
            </div>

            <div class="grid three">
              <label>Модель
                <input id="model" autocomplete="off" placeholder="пусто = default">
              </label>
              <label>Max output tokens
                <input id="maxOutputTokens" type="number" min="100" max="8000" value="1200">
              </label>
              <label>Min seconds between posts
                <input id="minSeconds" type="number" min="0" value="300">
              </label>
              <label>Reasoning effort
                <select id="reasoningEffort">
                  <option value="">default</option>
                  <option value="minimal">minimal</option>
                  <option value="low">low</option>
                  <option value="medium">medium</option>
                  <option value="high">high</option>
                </select>
              </label>
              <label>Text verbosity
                <select id="textVerbosity">
                  <option value="">default</option>
                  <option value="low">low</option>
                  <option value="medium">medium</option>
                  <option value="high">high</option>
                </select>
              </label>
              <label>Parse mode
                <select id="parseMode">
                  <option value="">none</option>
                  <option value="HTML">HTML</option>
                  <option value="Markdown">Markdown</option>
                  <option value="MarkdownV2">MarkdownV2</option>
                </select>
              </label>
            </div>

            <div class="grid three">
              <label class="check-row"><input id="enabled" type="checkbox"> Включен</label>
              <label class="check-row"><input id="disablePreview" type="checkbox"> Без preview ссылок</label>
              <label class="check-row"><input id="protectContent" type="checkbox"> Protect content</label>
            </div>

            <label>Context JSON
              <textarea id="contextJson" spellcheck="false">{}</textarea>
            </label>

            <label>Prompt
              <textarea class="prompt" id="promptContent" spellcheck="false"></textarea>
            </label>
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
      channelList: document.querySelector("#channelList"),
      sideStatus: document.querySelector("#sideStatus"),
      mainStatus: document.querySelector("#mainStatus"),
      publishPreview: document.querySelector("#publishPreview"),
      formTitle: document.querySelector("#formTitle"),
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
      reasoningEffort: document.querySelector("#reasoningEffort"),
      textVerbosity: document.querySelector("#textVerbosity"),
      parseMode: document.querySelector("#parseMode"),
      enabled: document.querySelector("#enabled"),
      disablePreview: document.querySelector("#disablePreview"),
      protectContent: document.querySelector("#protectContent"),
      contextJson: document.querySelector("#contextJson"),
      promptContent: document.querySelector("#promptContent"),
    };

    let state = { channels: [], jobs: [] };
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
        const text = await response.text();
        throw new Error(text || response.statusText);
      }
      return response.json();
    }

    function setStatus(target, message, kind = "") {
      target.textContent = message;
      target.className = `status ${kind}`;
    }

    async function loadState(selectKey = null) {
      state = await api("/api/admin/state");
      renderList();
      els.meta.textContent = `${state.enabled_channels}/${state.channels.length} включено · jobs: ${state.jobs.length}`;
      const key = selectKey || selectedKey || state.channels[0]?.key;
      if (key) {
        await selectChannel(key);
      } else {
        newChannel();
      }
    }

    function renderList() {
      els.channelList.innerHTML = "";
      for (const channel of state.channels) {
        const button = document.createElement("button");
        button.type = "button";
        button.className = `channel-item ${channel.key === selectedKey ? "active" : ""}`;
        button.innerHTML = `
          <div class="channel-title">
            <span>${escapeHtml(channel.title)}</span>
            <span class="badge ${channel.enabled ? "on" : "off"}">${channel.enabled ? "on" : "off"}</span>
          </div>
          <div class="channel-sub">${escapeHtml(channel.key)} · ${escapeHtml(channel.schedule)}</div>
          <div class="channel-sub">${escapeHtml(String(channel.chat_id))}</div>
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
      els.reasoningEffort.value = channel.reasoning_effort || "";
      els.textVerbosity.value = channel.text_verbosity || "";
      els.parseMode.value = channel.telegram?.parse_mode || "";
      els.enabled.checked = Boolean(channel.enabled);
      els.disablePreview.checked = channel.telegram?.disable_web_page_preview !== false;
      els.protectContent.checked = Boolean(channel.telegram?.protect_content);
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
        context,
      };
    }

    function parseChatId(value) {
      if (/^-?\\d+$/.test(value)) return Number(value);
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
        title: "New Channel",
        chat_id: "@your_channel",
        enabled: false,
        timezone: "Europe/Moscow",
        schedule: "0 10 * * *",
        prompt_file: "prompts/new_channel.md",
        max_output_tokens: 1200,
        min_seconds_between_posts: 300,
        telegram: {
          parse_mode: "HTML",
          disable_web_page_preview: true,
          protect_content: false,
        },
        context: {
          topic: "тема канала",
          audience: "кто читает",
        },
      });
      els.promptContent.value = "Напиши один полезный пост для Telegram-канала на русском языке.\\n";
      els.formTitle.textContent = "Новый канал";
    }

    async function saveChannel() {
      els.saveBtn.disabled = true;
      setStatus(els.mainStatus, "Сохраняю...");
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
        setStatus(els.mainStatus, "Сохранено и применено.", "ok");
        await loadState(result.selected_key);
      } catch (error) {
        setStatus(els.mainStatus, error.message, "err");
      } finally {
        els.saveBtn.disabled = false;
      }
    }

    async function publishChannel() {
      const key = els.key.value.trim();
      if (!key) return;
      els.publishBtn.disabled = true;
      els.publishPreview.hidden = true;
      setStatus(els.mainStatus, "Генерирую и публикую...");
      try {
        const result = await api(`/publish/${encodeURIComponent(key)}?force=true`, { method: "POST" });
        setStatus(els.mainStatus, "Публикация завершена.", "ok");
        els.publishPreview.hidden = false;
        els.publishPreview.textContent = result.result.preview || "";
      } catch (error) {
        setStatus(els.mainStatus, error.message, "err");
      } finally {
        els.publishBtn.disabled = false;
      }
    }

    async function deleteChannel() {
      const key = originalKey;
      if (!key) return;
      if (!confirm(`Удалить канал ${key} из конфига? Prompt-файл останется на диске.`)) return;
      els.deleteBtn.disabled = true;
      try {
        await api(`/api/admin/channels/${encodeURIComponent(key)}`, { method: "DELETE" });
        setStatus(els.sideStatus, `Канал ${key} удалён.`, "ok");
        selectedKey = null;
        originalKey = null;
        await loadState();
      } catch (error) {
        setStatus(els.mainStatus, error.message, "err");
      } finally {
        els.deleteBtn.disabled = false;
      }
    }

    async function reloadConfig() {
      els.reloadBtn.disabled = true;
      try {
        await api("/admin/reload", { method: "POST" });
        await loadState();
        setStatus(els.sideStatus, "Конфиг перечитан.", "ok");
      } catch (error) {
        setStatus(els.sideStatus, error.message, "err");
      } finally {
        els.reloadBtn.disabled = false;
      }
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

    loadState().catch((error) => {
      setStatus(els.sideStatus, error.message, "err");
      els.meta.textContent = "Ошибка загрузки";
    });
  </script>
</body>
</html>
"""

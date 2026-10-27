const API = "/api/v1";
const POLARITY = {
  positive: { label: "正向", cls: "pos" },
  negative: { label: "负面", cls: "neg" },
  neutral: { label: "中性", cls: "neu" },
};

const $ = (id) => document.getElementById(id);
let page = 1, totalPages = 1;

function fmtTime(s) {
  return new Date(s).toLocaleString("zh-CN", { hour12: false });
}

function badgeEl(polarity) {
  const span = document.createElement("span");
  span.className = `badge ${POLARITY[polarity].cls}`;
  span.textContent = POLARITY[polarity].label;
  return span;
}

async function api(path, options) {
  const res = await fetch(API + path, options);
  if (res.status === 204) return null;
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || `请求失败(${res.status})`);
  return data;
}

/* ---------- 分析 ---------- */
async function analyze() {
  const text = $("input-text").value.trim();
  const errBox = $("error");
  errBox.classList.add("hidden");
  if (!text) {
    errBox.textContent = "请输入评价文本";
    errBox.classList.remove("hidden");
    return;
  }
  $("btn-analyze").disabled = true;
  $("btn-analyze").textContent = "分析中…";
  try {
    const data = await api("/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    renderResult(data);
    loadRecords(1);
  } catch (e) {
    errBox.textContent = e.message;
    errBox.classList.remove("hidden");
  } finally {
    $("btn-analyze").disabled = false;
    $("btn-analyze").textContent = "开始分析";
  }
}

function renderResult(d) {
  $("result").classList.remove("hidden");
  const badge = $("badge");
  badge.className = `badge ${POLARITY[d.polarity].cls}`;
  badge.textContent = POLARITY[d.polarity].label;
  const pct = Math.round(d.confidence * 100);
  $("conf-value").textContent = pct + "%";
  $("conf-fill").style.width = pct + "%";
  $("result-text").textContent = d.preview;
  $("result-time").textContent = fmtTime(d.created_at);

  const chips = $("hit-words");
  chips.innerHTML = "";
  if (!d.hit_words.length) {
    chips.innerHTML = '<span class="muted">未命中情感词（按中性处理）</span>';
  } else {
    d.hit_words.forEach((h) => {
      const chip = document.createElement("span");
      chip.className = `chip ${h.polarity === "positive" ? "c-pos" : "c-neg"}`;
      const arrow = h.contribution > 0 ? "▲" : "▼";
      chip.textContent = `${h.word} ${arrow}${Math.abs(h.contribution).toFixed(2)}`;
      chips.appendChild(chip);
    });
  }
}

/* ---------- 历史记录 ---------- */
async function loadRecords(p = 1) {
  page = p;
  const polarity = $("f-polarity").value;
  const q = $("f-q").value.trim();
  const params = new URLSearchParams({ page, size: 10 });
  if (polarity) params.set("polarity", polarity);
  if (q) params.set("q", q);
  try {
    const data = await api(`/records?${params}`);
    totalPages = Math.max(1, Math.ceil(data.total / data.size));
    $("page-info").textContent = `第 ${data.page} / ${totalPages} 页 · 共 ${data.total} 条`;
    const tbody = $("records-body");
    tbody.innerHTML = "";
    if (!data.items.length) {
      tbody.innerHTML = '<tr><td colspan="5" class="muted">暂无记录</td></tr>';
      return;
    }
    data.items.forEach((r) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${fmtTime(r.created_at)}</td>
        <td class="preview">${r.preview}</td>
        <td></td>
        <td>${Math.round(r.confidence * 100)}%</td>
        <td><button class="btn ghost small">详情</button></td>`;
      tr.children[2].appendChild(badgeEl(r.polarity));
      tr.querySelector("button").onclick = () => showDetail(r.id);
      tbody.appendChild(tr);
    });
  } catch (e) {
    $("records-body").innerHTML = `<tr><td colspan="5" class="muted">加载失败：${e.message}</td></tr>`;
  }
}

async function showDetail(id) {
  try {
    const d = await api(`/records/${id}`);
    $("d-content").textContent = d.content;
    const badge = $("d-badge");
    badge.className = `badge ${POLARITY[d.polarity].cls}`;
    badge.textContent = POLARITY[d.polarity].label;
    $("d-conf").textContent = Math.round(d.confidence * 100) + "%";
    $("d-raw").textContent = d.raw_score;
    const chips = $("d-hits");
    chips.innerHTML = "";
    (d.hit_words || []).forEach((h) => {
      const chip = document.createElement("span");
      chip.className = `chip ${h.polarity === "positive" ? "c-pos" : "c-neg"}`;
      const arrow = h.contribution > 0 ? "▲" : "▼";
      chip.textContent = `${h.word} ${arrow}${Math.abs(h.contribution).toFixed(2)}`;
      chips.appendChild(chip);
    });
    if (!(d.hit_words || []).length) chips.innerHTML = '<span class="muted">无</span>';
    $("detail-mask").classList.remove("hidden");
  } catch (e) {
    alert(e.message);
  }
}

/* ---------- 事件绑定 ---------- */
$("input-text").addEventListener("input", (e) => {
  $("char-count").textContent = `${e.target.value.length} / 2000`;
});
$("btn-analyze").addEventListener("click", analyze);
$("btn-refresh").addEventListener("click", () => loadRecords(1));
$("f-polarity").addEventListener("change", () => loadRecords(1));
$("f-q").addEventListener("keydown", (e) => { if (e.key === "Enter") loadRecords(1); });
$("btn-prev").addEventListener("click", () => { if (page > 1) loadRecords(page - 1); });
$("btn-next").addEventListener("click", () => { if (page < totalPages) loadRecords(page + 1); });
$("btn-close").addEventListener("click", () => $("detail-mask").classList.add("hidden"));
$("detail-mask").addEventListener("click", (e) => {
  if (e.target === $("detail-mask")) $("detail-mask").classList.add("hidden");
});

loadRecords(1);

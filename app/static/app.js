/**
 * Ask-the-Numbers — Premium Client App
 * Features: Particles, Trust Meter, Advisor, Challenge Sandbox, Break-It Demo, CSV Export
 * All DOM IDs matched to redesigned index.html
 */

/* ─── State ─── */
let activeChart = null;
let currentQuestion = "What is the total revenue?";

/* ─── Bootstrap ─── */
document.addEventListener("DOMContentLoaded", () => {
  initParticles();
  loadHealth();
  loadInsights();
  setupEventListeners();
});

/* ═══════════════════════════════════════════════
   PARTICLE CANVAS
   ═══════════════════════════════════════════════ */
function initParticles() {
  const canvas = document.getElementById("particles-canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  let W = (canvas.width = window.innerWidth);
  let H = (canvas.height = window.innerHeight);

  window.addEventListener("resize", () => {
    W = canvas.width = window.innerWidth;
    H = canvas.height = window.innerHeight;
  });

  const PARTICLE_COUNT = 60;
  const particles = Array.from({ length: PARTICLE_COUNT }, () => ({
    x: Math.random() * W,
    y: Math.random() * H,
    r: Math.random() * 1.5 + 0.4,
    vx: (Math.random() - 0.5) * 0.3,
    vy: (Math.random() - 0.5) * 0.3,
    alpha: Math.random() * 0.5 + 0.1,
    color: Math.random() > 0.5 ? "0,212,255" : "99,102,241",
  }));

  function draw() {
    ctx.clearRect(0, 0, W, H);
    particles.forEach((p) => {
      p.x += p.vx;
      p.y += p.vy;
      if (p.x < 0) p.x = W;
      if (p.x > W) p.x = 0;
      if (p.y < 0) p.y = H;
      if (p.y > H) p.y = 0;

      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(${p.color},${p.alpha})`;
      ctx.fill();
    });

    // Draw connections between close particles
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 120) {
          ctx.beginPath();
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.strokeStyle = `rgba(0,212,255,${0.07 * (1 - dist / 120)})`;
          ctx.lineWidth = 0.6;
          ctx.stroke();
        }
      }
    }

    requestAnimationFrame(draw);
  }

  draw();
}

/* ═══════════════════════════════════════════════
   EVENT LISTENERS
   ═══════════════════════════════════════════════ */
function setupEventListeners() {
  const queryInput = document.getElementById("queryInput");
  const btnAsk = document.getElementById("btnAsk");

  btnAsk.addEventListener("click", () => handleAsk());
  queryInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") handleAsk();
  });

  // Quick-answer chips
  document.querySelectorAll(".chip[data-q]").forEach((chip) => {
    chip.addEventListener("click", () => {
      const q = chip.getAttribute("data-q");
      if (q) {
        queryInput.value = q;
        handleAsk();
      }
    });
  });

  // Tabs
  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => switchTab(btn.getAttribute("data-tab")));
  });

  // Data Quality toggle
  const btnToggleDQ = document.getElementById("btnToggleDQ");
  const btnCloseDQ = document.getElementById("btnCloseDQ");
  if (btnToggleDQ) {
    btnToggleDQ.addEventListener("click", () => {
      const sec = document.getElementById("dqSection");
      const open = sec.style.display === "block";
      sec.style.display = open ? "none" : "block";
      if (!open) loadDataQuality();
    });
  }
  if (btnCloseDQ) {
    btnCloseDQ.addEventListener("click", () => {
      document.getElementById("dqSection").style.display = "none";
    });
  }

  // Break-It
  const btnBreakItDemo = document.getElementById("btnBreakItDemo");
  const btnCloseBreakIt = document.getElementById("btnCloseBreakIt");
  if (btnBreakItDemo) {
    btnBreakItDemo.addEventListener("click", () => runBreakItDemo());
  }
  if (btnCloseBreakIt) {
    btnCloseBreakIt.addEventListener("click", () => {
      document.getElementById("breakItSection").style.display = "none";
    });
  }

  // Challenge sandbox
  const btnChallengeAnswer = document.getElementById("btnChallengeAnswer");
  const btnCloseChallenge = document.getElementById("btnCloseChallenge");
  if (btnChallengeAnswer) {
    btnChallengeAnswer.addEventListener("click", () => runChallengeSandbox());
  }
  if (btnCloseChallenge) {
    btnCloseChallenge.addEventListener("click", () => {
      document.getElementById("challengeSection").style.display = "none";
    });
  }

  // Trust badge → proof tab
  const trustBadge = document.getElementById("trustBadge");
  if (trustBadge) {
    trustBadge.addEventListener("click", () => {
      switchTab("proof");
      document.getElementById("proofTrustBadge")?.scrollIntoView({ behavior: "smooth" });
    });
  }

  // Copy SQL
  const btnCopySQL = document.getElementById("btnCopySQL");
  if (btnCopySQL) {
    btnCopySQL.addEventListener("click", () => {
      const sql = document.getElementById("sqlDisplay").innerText;
      navigator.clipboard.writeText(sql).catch(() => {});
      btnCopySQL.innerText = "✓ Copied";
      setTimeout(() => (btnCopySQL.innerText = "Copy"), 1800);
    });
  }

  // Download CSV
  const btnDownloadCSV = document.getElementById("btnDownloadCSV");
  if (btnDownloadCSV) {
    btnDownloadCSV.addEventListener("click", () => exportTableToCSV());
  }
}

/* ═══════════════════════════════════════════════
   API: HEALTH CHECK
   ═══════════════════════════════════════════════ */
async function loadHealth() {
  try {
    const res = await fetch("/api/health");
    if (!res.ok) return;
    const data = await res.json();

    const modeBadge = document.getElementById("modeBadge");
    if (modeBadge) {
      if (data.mode === "gemini") {
        modeBadge.innerText = "⚡ Gemini Flash";
        modeBadge.className = "pill pill-blue";
      } else {
        modeBadge.innerText = "⬤ Rule-Based Engine";
        modeBadge.className = "pill pill-emerald";
      }
    }

    const healthBadge = document.getElementById("healthBadge");
    if (healthBadge) {
      healthBadge.innerText = `${data.valid_rows} clean · ${data.quarantined_rows} quarantined`;
      healthBadge.className = "pill pill-electric";
    }
  } catch (err) {
    console.error("Health check error:", err);
  }
}

/* ═══════════════════════════════════════════════
   API: KPI INSIGHTS
   ═══════════════════════════════════════════════ */
async function loadInsights() {
  try {
    const res = await fetch("/api/insights");
    if (!res.ok) return;
    const cards = await res.json();
    const grid = document.getElementById("kpiGrid");
    if (!grid) return;

    const iconMap = {
      peak_month: { icon: "📅", cls: "kpi-icon-blue" },
      top_product: { icon: "🏆", cls: "kpi-icon-emerald" },
      top_region: { icon: "🌍", cls: "kpi-icon-purple" },
      returns_alert: { icon: "⚠️", cls: "kpi-icon-amber" },
    };

    const colorMap = {
      emerald: "pill-emerald",
      blue: "pill-blue",
      indigo: "pill-indigo",
      amber: "pill-amber",
      rose: "pill-rose",
      electric: "pill-electric",
    };

    grid.innerHTML = "";
    cards.forEach((c) => {
      const { icon = "📊", cls = "kpi-icon-blue" } = iconMap[c.id] || {};
      const pillCls = colorMap[c.badge_color] || "pill-blue";
      const el = document.createElement("div");
      el.className = "kpi-card";
      el.innerHTML = `
        <div class="kpi-top">
          <span class="kpi-label">${c.title}</span>
          <div class="kpi-icon ${cls}">${icon}</div>
        </div>
        <div class="kpi-value">${c.value}</div>
        <div style="display:flex;align-items:center;justify-content:space-between;margin-top:8px;">
          <span class="kpi-sub">${c.subtitle}</span>
          <span class="pill ${pillCls}" style="font-size:10px;">${c.badge}</span>
        </div>
      `;
      // Click a KPI card to auto-ask a related question
      const questionMap = {
        peak_month: "Show monthly revenue trend",
        top_product: "Which product has the highest revenue?",
        top_region: "Which region has the highest sales?",
        returns_alert: "How many orders were returned?",
      };
      if (questionMap[c.id]) {
        el.style.cursor = "pointer";
        el.title = `Click to ask: "${questionMap[c.id]}"`;
        el.addEventListener("click", () => {
          document.getElementById("queryInput").value = questionMap[c.id];
          handleAsk();
        });
      }
      grid.appendChild(el);
    });
  } catch (err) {
    console.error("Failed to load KPIs:", err);
  }
}

/* ═══════════════════════════════════════════════
   HANDLE ASK
   ═══════════════════════════════════════════════ */
async function handleAsk() {
  const queryInput = document.getElementById("queryInput");
  const query = queryInput.value.trim();
  if (!query) return;
  currentQuestion = query;

  const btnAsk = document.getElementById("btnAsk");
  const btnText = document.getElementById("btnAskText");
  const spinner = document.getElementById("btnAskSpinner");
  const includeRet = document.getElementById("toggleReturned")?.checked || false;

  btnText.style.display = "none";
  spinner.style.display = "inline-block";
  btnAsk.disabled = true;

  try {
    const res = await fetch("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: query, options: { include_returned: includeRet } }),
    });
    const data = await res.json();
    renderAnswer(data, query);
  } catch (err) {
    showToast("Error communicating with server: " + err.message, "rose");
  } finally {
    btnText.style.display = "inline";
    spinner.style.display = "none";
    btnAsk.disabled = false;
  }
}

/* ═══════════════════════════════════════════════
   RENDER ANSWER
   ═══════════════════════════════════════════════ */
function renderAnswer(data, query) {
  const container = document.getElementById("answerContainer");
  container.style.display = "block";

  // Headline
  document.getElementById("headlineAnswer").innerText = data.answer || "—";
  document.getElementById("queryLabel").innerText = `"${query}"`;
  document.getElementById("latencyBadge").innerText = `${data.latency_ms} ms`;

  // Lane badge
  const laneBadge = document.getElementById("laneBadge");
  laneBadge.innerText = `Lane ${data.lane} · ${data.intent || "Query"}`;
  laneBadge.className = data.lane === "A" ? "pill pill-electric" : data.lane === "B" ? "pill pill-blue" : "pill pill-rose";

  // Status badge
  const statusBadge = document.getElementById("statusBadge");
  if (data.lane === "C") {
    statusBadge.className = "pill pill-rose";
    statusBadge.innerText = "⛔ Refused";
  } else if (data.verified) {
    statusBadge.className = "pill pill-emerald";
    statusBadge.innerText = "✅ Dual-Engine Verified";
  } else {
    statusBadge.className = "pill pill-amber";
    statusBadge.innerText = "⚠️ Guarded (Lane B)";
  }

  // Trust meter
  const trustBadge = document.getElementById("trustBadge");
  const proofTrustBadge = document.getElementById("proofTrustBadge");
  const proofTrustHeadline = document.getElementById("proofTrustHeadline");
  const proofTrustFactors = document.getElementById("proofTrustFactors");

  if (data.trust_score) {
    const ts = data.trust_score;
    const scoreClass = ts.score >= 90 ? "pill-emerald" : ts.score >= 70 ? "pill-blue" : "pill-amber";
    trustBadge.innerText = `Trust ${ts.score}/100`;
    trustBadge.className = `pill ${scoreClass}`;
    proofTrustBadge.innerText = `Trust Score: ${ts.score} / 100 (${ts.grade || ""})`;
    proofTrustHeadline.innerText = ts.headline || "Verified by dual engines";
    proofTrustFactors.innerHTML = "";
    (ts.factors || []).forEach((f) => {
      const card = document.createElement("div");
      card.className = "trust-factor-card";
      const impactColor = f.status === "positive" ? "var(--emerald-bright)" : f.status === "warning" ? "var(--rose-bright)" : "var(--blue-bright)";
      card.innerHTML = `
        <div class="trust-factor-top">
          <span>${f.name}</span>
          <span style="color:${impactColor};">${f.impact}</span>
        </div>
        <div class="trust-factor-desc">${f.description}</div>
      `;
      proofTrustFactors.appendChild(card);
    });
  }

  // Advisor
  if (data.advisor) {
    const adv = data.advisor;
    document.getElementById("advisorHeadline").innerText = adv.headline || "Strategic Briefing";
    renderList("advisorFacts", adv.verified_facts || []);
    renderList("advisorRisks", adv.risk_observations || []);
    renderList("advisorActions", adv.actionable_recommendations || []);
  }

  // Data table
  renderTable(data.columns, data.rows);

  // Chart
  renderChart(data.chart);

  // SQL
  document.getElementById("sqlDisplay").innerText = data.sql || "-- No SQL available";

  // Proof panel
  document.getElementById("proofFormula").innerText = data.formula || "N/A";
  document.getElementById("proofCounts").innerText =
    `Used: ${data.row_counts?.used ?? "—"} rows | Excluded: ${data.row_counts?.excluded ?? "—"} | Returned: ${data.row_counts?.returned ?? "—"}`;
  document.getElementById("proofVerifierMsg").innerText = data.verification_message || "N/A";

  const assumptionsList = document.getElementById("proofAssumptions");
  assumptionsList.innerHTML = "";
  (data.assumptions || []).forEach((a) => {
    const li = document.createElement("li");
    li.innerText = a;
    assumptionsList.appendChild(li);
  });

  // Follow-ups
  const followupsContainer = document.getElementById("followupsContainer");
  followupsContainer.innerHTML = "";
  (data.followups || []).forEach((f) => {
    const chip = document.createElement("button");
    chip.className = "followup-chip";
    chip.innerText = f;
    chip.addEventListener("click", () => {
      document.getElementById("queryInput").value = f;
      handleAsk();
    });
    followupsContainer.appendChild(chip);
  });

  // Switch to chart tab if data exists, else table
  if (data.chart && data.chart.type !== "none" && data.chart.datasets?.length > 0) {
    switchTab("chart");
  } else {
    switchTab("table");
  }

  container.scrollIntoView({ behavior: "smooth" });
}

function renderList(id, items) {
  const el = document.getElementById(id);
  if (!el) return;
  el.innerHTML = "";
  if (!items || items.length === 0) {
    el.innerHTML = "<li>No data.</li>";
    return;
  }
  items.forEach((txt) => {
    const li = document.createElement("li");
    li.innerText = txt;
    el.appendChild(li);
  });
}

/* ═══════════════════════════════════════════════
   TAB SWITCHING
   ═══════════════════════════════════════════════ */
function switchTab(tabId) {
  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.getAttribute("data-tab") === tabId);
  });
  document.querySelectorAll(".tab-content").forEach((c) => {
    c.classList.toggle("active", c.id === `tab-${tabId}`);
  });
}

/* ═══════════════════════════════════════════════
   TABLE RENDERER
   ═══════════════════════════════════════════════ */
function renderTable(columns, rows) {
  const thead = document.getElementById("tableHead");
  const tbody = document.getElementById("tableBody");
  thead.innerHTML = "";
  tbody.innerHTML = "";

  if (!columns || columns.length === 0 || !rows || rows.length === 0) {
    thead.innerHTML = "<tr><th>Status</th></tr>";
    tbody.innerHTML = "<tr><td style='color:var(--text-muted);padding:24px;text-align:center;'>No tabular rows returned.</td></tr>";
    return;
  }

  const hRow = document.createElement("tr");
  columns.forEach((c) => {
    const th = document.createElement("th");
    th.innerText = c.replace(/_/g, " ").toUpperCase();
    hRow.appendChild(th);
  });
  thead.appendChild(hRow);

  rows.forEach((r) => {
    const rowEl = document.createElement("tr");
    columns.forEach((c) => {
      const td = document.createElement("td");
      const val = r[c];
      const isMonetary = c.includes("revenue") || c.includes("price") || c.includes("value") || c.includes("discount") || c.includes("diff");
      if (typeof val === "number" && isMonetary) {
        td.innerText = "₹" + Number(val).toLocaleString("en-IN");
      } else {
        td.innerText = val !== null && val !== undefined ? val : "—";
      }
      rowEl.appendChild(td);
    });
    tbody.appendChild(rowEl);
  });
}

/* ═══════════════════════════════════════════════
   CHART RENDERER
   ═══════════════════════════════════════════════ */
function renderChart(chartSpec) {
  const canvas = document.getElementById("analyticsChart");
  const emptyMsg = document.getElementById("chartEmptyMessage");

  if (activeChart) {
    activeChart.destroy();
    activeChart = null;
  }

  if (!chartSpec || chartSpec.type === "none" || !chartSpec.datasets || chartSpec.datasets.length === 0) {
    emptyMsg.style.display = "flex";
    canvas.style.display = "none";
    return;
  }

  emptyMsg.style.display = "none";
  canvas.style.display = "block";

  const isLine = chartSpec.type === "line";
  const totalSum = (chartSpec.datasets[0]?.data || []).reduce((s, v) => s + (typeof v === "number" ? v : 0), 0);

  // Premium color palette for bars
  const COLORS = [
    "rgba(0,212,255,0.75)", "rgba(99,102,241,0.75)", "rgba(16,185,129,0.75)",
    "rgba(245,158,11,0.75)", "rgba(239,68,68,0.75)", "rgba(168,85,247,0.75)",
  ];
  const BORDER = [
    "#00d4ff", "#6366f1", "#10b981", "#f59e0b", "#ef4444", "#a855f7",
  ];

  activeChart = new Chart(canvas.getContext("2d"), {
    type: isLine ? "line" : "bar",
    data: {
      labels: chartSpec.labels,
      datasets: chartSpec.datasets.map((ds, i) => ({
        label: ds.label,
        data: ds.data,
        backgroundColor: isLine ? "rgba(0,212,255,0.08)" : (ds.backgroundColor || COLORS[i % COLORS.length]),
        borderColor: ds.borderColor || BORDER[i % BORDER.length],
        borderWidth: isLine ? 2.5 : 1.5,
        borderRadius: isLine ? 0 : 8,
        tension: 0.35,
        fill: isLine,
        pointRadius: isLine ? 5 : 0,
        pointHoverRadius: isLine ? 8 : 0,
        pointBackgroundColor: "#00d4ff",
        pointBorderColor: "#020510",
        pointBorderWidth: 2,
      })),
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      plugins: {
        legend: {
          labels: { color: "#7d9bc1", font: { size: 12, weight: "600", family: "Inter" } },
        },
        title: {
          display: !!chartSpec.title,
          text: chartSpec.title || "",
          color: "#e2e8f0",
          font: { size: 14, weight: "700", family: "Inter" },
          padding: { bottom: 16 },
        },
        tooltip: {
          enabled: true,
          backgroundColor: "rgba(2,5,16,0.97)",
          titleColor: "#00d4ff",
          titleFont: { size: 13, weight: "700", family: "Inter" },
          bodyColor: "#e2e8f0",
          bodyFont: { size: 12.5, family: "Inter" },
          borderColor: "rgba(0,212,255,0.25)",
          borderWidth: 1,
          padding: 14,
          displayColors: true,
          callbacks: {
            title: (items) => items[0]?.label || "",
            label: (ctx) => {
              const val = ctx.raw;
              const lbl = ctx.dataset.label || "Value";
              if (typeof val === "number") {
                const formatted = "₹" + Number(val).toLocaleString("en-IN");
                if (totalSum > 0 && val >= 0) {
                  const share = ((val / totalSum) * 100).toFixed(1);
                  return `  ${lbl}: ${formatted}  (${share}% share)`;
                }
                return `  ${lbl}: ${formatted}`;
              }
              return `  ${lbl}: ${val}`;
            },
            afterBody: () => ["", "  ✅ Dual-Engine Verified"],
          },
        },
      },
      scales: {
        x: {
          ticks: { color: "#7d9bc1", font: { size: 12, family: "Inter" } },
          grid: { color: "rgba(255,255,255,0.04)", drawBorder: false },
        },
        y: {
          ticks: {
            color: "#7d9bc1",
            font: { size: 12, family: "Inter" },
            callback: (v) => "₹" + Number(v).toLocaleString("en-IN"),
          },
          grid: { color: "rgba(255,255,255,0.04)", drawBorder: false },
          beginAtZero: true,
        },
      },
    },
  });
}

/* ═══════════════════════════════════════════════
   BREAK-IT DEMO
   ═══════════════════════════════════════════════ */
async function runBreakItDemo() {
  const sec = document.getElementById("breakItSection");
  sec.style.display = "block";
  sec.scrollIntoView({ behavior: "smooth" });

  const tbody = document.getElementById("breakItTableBody");
  tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;padding:28px;color:var(--text-muted);">
    <span style="display:inline-block;animation:spin 0.6s linear infinite;border:2px solid rgba(0,212,255,0.2);border-top-color:#00d4ff;border-radius:50%;width:20px;height:20px;"></span>
    &nbsp; Firing attack battery…
  </td></tr>`;

  try {
    const res = await fetch("/api/break-it", { method: "POST" });
    const data = await res.json();
    const badge = document.getElementById("breakItRateBadge");
    badge.innerText = `${data.attacks_blocked}/${data.attacks_tested} Blocked`;
    badge.className = data.attacks_blocked === data.attacks_tested ? "pill pill-emerald" : "pill pill-rose";

    tbody.innerHTML = "";
    data.results.forEach((atk) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><strong style="color:#fff;">${atk.name}</strong><br><span style="font-size:11px;color:var(--text-muted);">${atk.attack_type}</span></td>
        <td><code style="color:var(--rose-bright);font-family:var(--font-mono);font-size:11.5px;">${escapeHtml(atk.payload)}</code></td>
        <td style="color:var(--blue-bright);font-size:12px;">${atk.defense_layer}</td>
        <td><span class="pill pill-emerald">🛡️ BLOCKED</span></td>
        <td style="font-family:var(--font-mono);font-size:12px;">${atk.latency_ms} ms</td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="5" style="color:var(--rose-bright);padding:20px;">Failed: ${err.message}</td></tr>`;
  }
}

/* ═══════════════════════════════════════════════
   CHALLENGE SANDBOX
   ═══════════════════════════════════════════════ */
async function runChallengeSandbox() {
  const sec = document.getElementById("challengeSection");
  sec.style.display = "block";
  sec.scrollIntoView({ behavior: "smooth" });

  const tbody = document.getElementById("challengeTableBody");
  tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;padding:28px;color:var(--text-muted);">Calculating multi-definition variance…</td></tr>`;

  try {
    const res = await fetch("/api/challenge", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: currentQuestion }),
    });
    const data = await res.json();

    const badge = document.getElementById("challengeVerdictBadge");
    badge.innerText = data.is_stable ? "100% Stable" : "Scope-Sensitive";
    badge.className = data.is_stable ? "pill pill-emerald" : "pill pill-amber";

    document.getElementById("challengeVerdictText").innerHTML = `
      <strong>Sensitivity Audit:</strong> ${data.verdict}
      <div style="margin-top:6px;font-size:11.5px;color:var(--text-secondary);">${data.takeaway}</div>
    `;

    tbody.innerHTML = "";
    data.scenarios.forEach((s) => {
      const deltaClass = s.delta_formatted.startsWith("+") && s.delta_formatted !== "+₹0" ? "pill-blue" : "pill-emerald";
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><strong style="color:#fff;">${s.name}</strong><br><span style="font-size:11px;color:var(--text-muted);">${s.description}</span></td>
        <td><strong style="color:var(--electric);">${s.total_revenue_formatted}</strong></td>
        <td><span class="pill ${deltaClass}">${s.delta_formatted} (${s.pct_formatted})</span></td>
        <td><span style="color:var(--emerald-bright);font-weight:600;">${s.top_product}</span></td>
        <td><span style="color:var(--emerald-bright);font-weight:600;">${s.top_region}</span></td>
        <td style="font-size:11px;color:var(--text-muted);">${s.assumptions}</td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="6" style="color:var(--rose-bright);padding:20px;">Failed: ${err.message}</td></tr>`;
  }
}

/* ═══════════════════════════════════════════════
   DATA QUALITY
   ═══════════════════════════════════════════════ */
async function loadDataQuality() {
  try {
    const res = await fetch("/api/data-quality");
    const dq = await res.json();

    document.getElementById("dqLoaded").innerText = dq.total_rows_loaded;
    document.getElementById("dqValid").innerText = dq.valid_rows_count;
    document.getElementById("dqQuarantined").innerText = dq.quarantined_rows_count;
    document.getElementById("dqHygieneScore").innerText = dq.data_hygiene_score_pct + "% Hygiene";
    document.getElementById("dqDateRange").innerText = `${dq.date_range_start} → ${dq.date_range_end}`;

    const tbody = document.getElementById("dqQuarantineTableBody");
    tbody.innerHTML = "";
    dq.quarantined_records.forEach((r) => {
      const row = document.createElement("tr");
      row.innerHTML = `
        <td><code style="color:var(--electric);font-size:12px;">${r.transaction_id}</code></td>
        <td><span class="pill pill-amber">${r.reason}</span></td>
        <td>${r.details?.product || "—"}</td>
        <td style="font-size:12.5px;">${r.details?.note || "—"}</td>
      `;
      tbody.appendChild(row);
    });
  } catch (err) {
    console.error("Failed to load DQ report:", err);
  }
}

/* ═══════════════════════════════════════════════
   CSV EXPORT
   ═══════════════════════════════════════════════ */
function exportTableToCSV() {
  const table = document.getElementById("resultsTable");
  const rows = Array.from(table.querySelectorAll("tr")).map((row) =>
    Array.from(row.querySelectorAll("th, td"))
      .map((cell) => `"${cell.innerText.replace(/"/g, '""')}"`)
      .join(",")
  );
  const blob = new Blob([rows.join("\n")], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `ask_the_numbers_${Date.now()}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

/* ═══════════════════════════════════════════════
   TOAST NOTIFICATION
   ═══════════════════════════════════════════════ */
function showToast(msg, type = "blue") {
  const toast = document.createElement("div");
  toast.style.cssText = `
    position:fixed;bottom:24px;right:24px;z-index:9999;
    background:rgba(2,5,16,0.97);border:1px solid ${type === "rose" ? "rgba(239,68,68,0.4)" : "rgba(0,212,255,0.3)"};
    color:${type === "rose" ? "#f87171" : "#00d4ff"};
    padding:14px 20px;border-radius:12px;font-size:13.5px;font-weight:600;
    box-shadow:0 8px 32px rgba(0,0,0,0.6);
    animation:slide-down 0.3s ease;max-width:380px;
  `;
  toast.innerText = msg;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 4000);
}

/* ═══════════════════════════════════════════════
   HELPERS
   ═══════════════════════════════════════════════ */
function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

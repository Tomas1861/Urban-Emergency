<script setup>
import { onMounted, onUnmounted } from "vue";

// 态势大屏：人群疏散仿真演示。移植自 复兴岛应急决策MVP演示.html，
// 逻辑保持不变（canvas 仿真 + 剧本化多智能体会商日志），仅包裹进 Vue 生命周期，
// 用于展示现场开场，与真实可操作应用（其余页面）配合使用。
let cleanup = () => {};

onMounted(() => {
  cleanup = initDashboard();
});
onUnmounted(() => cleanup());

function initDashboard() {
  const root = document.getElementById("dash-root");
  const $ = (id) => root.querySelector("#" + id);
  const map = $("map"), mctx = map.getContext("2d");
  const chart = $("chart"), cctx = chart.getContext("2d");
  let W, H, CW, CH;

  function resize() {
    const r = map.parentElement.getBoundingClientRect();
    W = map.width = r.width * devicePixelRatio; H = map.height = r.height * devicePixelRatio;
    mctx.setTransform(devicePixelRatio, 0, 0, devicePixelRatio, 0, 0);
    const c = chart.parentElement.getBoundingClientRect();
    CW = chart.width = c.width * devicePixelRatio; CH = chart.height = c.height * devicePixelRatio;
    cctx.setTransform(devicePixelRatio, 0, 0, devicePixelRatio, 0, 0);
    layout();
  }
  window.addEventListener("resize", resize);

  let isl, venue, gates, zoneEast;
  function layout() {
    const w = map.parentElement.clientWidth, h = map.parentElement.clientHeight;
    const cx = w * 0.5, cy = h * 0.52, rw = Math.min(w * 0.36, 380), rh = Math.min(h * 0.33, 235);
    isl = { cx, cy, rw, rh, rot: -0.28 };
    const P = (t) => {
      const a = Math.cos(isl.rot), b = Math.sin(isl.rot);
      const x = Math.cos(t) * rw, y = Math.sin(t) * rh;
      return { x: cx + x * a - y * b, y: cy + x * b + y * a };
    };
    venue = { ...P(Math.PI * 0.95), r: Math.min(rw, rh) * 0.42 };
    venue.x = cx - (rw * 0.35) * Math.cos(isl.rot); venue.y = cy - (rw * 0.35) * Math.sin(isl.rot);
    gates = {
      A: { ...P(-Math.PI * 0.62), label: "A口·定海路桥", open: true, cap: 34 },
      B: { ...P(-Math.PI * 0.05), label: "B口·东主通道", open: true, cap: 46 },
      C: { ...P(Math.PI * 0.42), label: "C口·南侧通道", open: true, cap: 22 },
      D: { ...P(Math.PI * 0.78), label: "D口·西侧便桥", open: false, cap: 18 },
    };
    for (const g of Object.values(gates)) {
      const dx = g.x - cx, dy = g.y - cy, L = Math.hypot(dx, dy);
      g.bx = g.x + dx / L * 70; g.by = g.y + dy / L * 70;
    }
    zoneEast = { x: (gates.B.x * 2 + venue.x) / 3, y: (gates.B.y * 2 + venue.y) / 3, r: Math.min(rw, rh) * 0.52 };
  }

  const N = 1000; let agents = [], evacuated = 0, peakDen = 0;
  const GRID = 26; let gridMap = new Map();
  function spawn() {
    agents = []; evacuated = 0; peakDen = 0;
    for (let i = 0; i < N; i++) {
      const a = Math.random() * Math.PI * 2, r = Math.sqrt(Math.random()) * venue.r;
      agents.push({
        x: venue.x + Math.cos(a) * r, y: venue.y + Math.sin(a) * r,
        tgt: pick({ B: .58, A: .22, C: .14, D: .06 }), evac: false, comp: true,
        sp: (0.55 + Math.random() * 0.35), ph: Math.random() * 7,
      });
    }
  }
  function pick(w) { const r = Math.random(); let s = 0; for (const k in w) { s += w[k]; if (r < s) return k; } return "B"; }
  function reassign(weights, complianceKeep) {
    for (const a of agents) {
      if (a.evac) continue;
      if (!a.comp && complianceKeep) continue;
      a.tgt = pick(weights);
    }
  }
  function stepSim(dt) {
    gridMap.clear();
    for (const a of agents) {
      if (a.evac) continue;
      const k = ((a.x / GRID) | 0) + "," + ((a.y / GRID) | 0);
      gridMap.set(k, (gridMap.get(k) || 0) + 1);
    }
    let gq = { A: 0, B: 0, C: 0, D: 0 };
    for (const a of agents) {
      if (a.evac) continue;
      const g = gates[a.tgt];
      let dx = g.x - a.x, dy = g.y - a.y; const d = Math.hypot(dx, dy);
      if (d < 14) {
        if (g.open && gq[a.tgt] < g.cap * dt) { gq[a.tgt]++; a.evac = true; evacuated++; continue; }
        a.ph += dt * 3; a.x += Math.cos(a.ph) * 0.35; a.y += Math.sin(a.ph) * 0.35; continue;
      }
      const k = ((a.x / GRID) | 0) + "," + ((a.y / GRID) | 0);
      const local = gridMap.get(k) || 0;
      const slow = 1 / (1 + Math.max(0, local - 4) * 0.32);
      const v = a.sp * 34 * slow * dt;
      a.x += dx / d * v + (Math.random() - .5) * 0.5;
      a.y += dy / d * v + (Math.random() - .5) * 0.5;
    }
  }
  function densityEast() {
    let c = 0; const r2 = zoneEast.r * zoneEast.r;
    for (const a of agents) {
      if (a.evac) continue;
      const dx = a.x - zoneEast.x, dy = a.y - zoneEast.y;
      if (dx * dx + dy * dy < r2) c++;
    }
    return c / 112;
  }

  function evalPlan(open) {
    const cap = { A: 34, B: 0, C: 22, D: 18 };
    const remain = agents.filter((a) => !a.evac).length;
    const tot = open.reduce((s, g) => s + cap[g], 0) || 1;
    return { evac_s: Math.round(remain / tot * 10) * 10, peak: +(2.4 + remain / (tot * 46)).toFixed(1) };
  }

  let phase = "idle", simT = 0, round = 0, expected = null, deviated = false;
  const hist = [];
  const S = { eventAt: 7, consultAt: 9 };
  let consultQueue = [], consultTimer = 0;

  function setPhase(p, cls, txt) { phase = p; const el = $("phase"); el.textContent = txt; el.className = "chip " + (cls || ""); }
  function banner(t) { const b = $("banner"); if (!t) { b.style.display = "none"; return; } b.textContent = t; b.style.display = "block"; }

  function entry(agent, cls, rows, extra) {
    const e = document.createElement("div"); e.className = "entry";
    const t = fmtT(simT);
    e.innerHTML = `<div class="ehd"><span class="badge ${cls}">${agent}</span><time>${t}</time></div>
      <div class="body">${rows.map((r) => `<div class="kv"><span class="k">${r[0]}</span><span class="v">${r[1]}</span></div>`).join("")}${extra || ""}</div>`;
    $("stream").appendChild(e);
    requestAnimationFrame(() => e.classList.add("show"));
    $("stream").scrollTop = 1e9;
    return e;
  }
  const CITES = {
    "YA-2024-017": "《大型群众性活动安全预案》第17条：当区域人群密度持续超过4人/㎡达3分钟，应启动橙色预警并实施分流管制。",
    "YA-2024-023": "《大型群众性活动安全预案》第23条：主要疏散通道因故障关闭时，须同步开放不少于两条替代通道并调整现场引导。",
    "YA-2024-031": "《跨江通道运行细则》第31条：散场高峰期跨江桥梁通行接近饱和时，应实施分批放行与错峰引导。",
  };
  const cite = (id) => `<span class="cite" data-tip="${CITES[id]}">${id}</span>`;

  function consult1() {
    round = 1; $("round").textContent = "第 1 轮"; $("sRound").textContent = round;
    const den = densityEast().toFixed(1);
    consultQueue = [
      [0.4, () => entry("态势感知", "b-sit", [
        ["判断", `东区人群异常聚集，密度 <b style="color:var(--red)">${den} 人/㎡</b> 持续上升`],
        ["依据", "B口设施状态 closed；东区容量比 1.2 且 rising"],
        ["建议", "移交风险研判"]])],
      [1.6, () => entry("风险研判", "b-risk", [
        ["判断", `<b style="color:#dc2626">橙色预警</b>，建议定级 L3（多方案推演）`],
        ["依据", `密度超限触发 ${cite("YA-2024-017")}；主通道封闭适用 ${cite("YA-2024-023")}；事发邻近桥头敏感点位`],
        ["约束", "硬规则：桥头点位事件 ≥ L3，与研判一致"]])],
      [1.8, () => {
        const p1 = evalPlan(["A", "C"]), p2 = evalPlan(["A", "C", "D"]);
        window._p1 = p1; window._p2 = p2;
        entry("疏导策略", "b-strat", [
          ["判断", "生成 2 套分流候选，指标由流量模型计算"],
          ["依据", "可用通道拓扑：A/C 现开，D 可启用"]],
          `<div class="plancard"><div class="pn">方案一 · 开放 A/C 双通道</div>
            <div class="pm">预计疏散 <b>${fmtS(p1.evac_s)}</b> · 预测峰值 <b>${p1.peak} 人/㎡</b></div></div>
           <div class="plancard rec"><div class="pn">方案二 · 开放 A/C/D 三通道 <span class="tag">推荐</span></div>
            <div class="pm">预计疏散 <b>${fmtS(p2.evac_s)}</b> · 预测峰值 <b>${p2.peak} 人/㎡</b> · 需增派 D 口引导力量</div></div>`);
      }],
      [2.0, () => {
        entry("总指挥", "b-cmd", [
          ["结论", `并行推演比较完成：<b>方案二疏散时间缩短 ${Math.round((1 - window._p2.evac_s / window._p1.evac_s) * 100)}%</b>，推荐执行`],
          ["依据", "三分屏推演指标对比（演示版为解析推演）"],
          ["约束", "L3 级别 —— 系统无权自决，待指挥员选择"]]);
        $("approvewrap").style.display = "flex";
        setPhase("await", "warn", "待指挥员决策");
      }],
    ];
    consultTimer = 0;
  }

  function consult2() {
    round = 2; $("round").textContent = "第 2 轮 · 自动触发"; $("sRound").textContent = round;
    banner("⚠ 预期-实际偏差超阈值 —— 系统自动重新会商");
    setPhase("reconsult", "warn", "滚动闭环 · 重会商");
    const den = densityEast().toFixed(1);
    consultQueue = [
      [0.6, () => entry("态势感知", "b-sit", [
        ["判断", `<b style="color:#dc2626">偏差告警</b>：东区实际密度 ${den}，超出预期曲线 35% 以上`],
        ["依据", "效果跟踪：部分人群未按引导改道（服从率低于假设）"],
        ["建议", "自动触发重新会商（无人工干预）"]])],
      [1.6, () => entry("疏导策略", "b-strat", [
        ["判断", "修正方案：强化 B口截流引导 + A/C/D 全通道均衡分流"],
        ["依据", `${cite("YA-2024-031")}；引导强度参数上调`],
        ["建议", "立即下发，L2 单方案确认"]])],
      [1.4, () => {
        entry("总指挥", "b-cmd", [["结论", "修正方案指标可行，按 L2 待批准后执行"], ["约束", "超时不执行，仅持续告警"]]);
        $("approveBtn").textContent = "批准修正方案";
        $("approvewrap").style.display = "flex";
      }],
    ];
    consultTimer = 0;
  }

  $("approveBtn").onclick = () => {
    $("approvewrap").style.display = "none";
    if (round === 1) {
      gates.B.open = false; gates.D.open = true;
      reassign({ A: .42, C: .32, D: .26 }, true);
      expected = { t0: simT, d0: densityEast(), tau: 26 };
      entry("总指挥", "b-cmd", [["结论", "指挥员已批准方案二，指令经调度服务下发；登记预期态势曲线用于效果跟踪"]]);
      banner(""); setPhase("exec", "live", "处置执行中");
      setTimeout(() => { if (round === 1 && !deviated) perturb(); }, 8000);
    } else {
      for (const a of agents) a.comp = true;
      reassign({ A: .36, C: .32, D: .32 }, false);
      for (const a of agents) a.sp *= 1.12;
      expected = { t0: simT, d0: densityEast(), tau: 18 };
      entry("总指挥", "b-cmd", [["结论", "修正方案已批准执行，继续效果跟踪"]]);
      banner(""); setPhase("exec2", "live", "修正处置执行中");
    }
  };
  $("rejectBtn").onclick = () => {
    entry("总指挥", "b-cmd", [["结论", "方案被驳回 —— 按安全原则：超时/驳回不执行，维持告警并等待新指令（演示中请点批准继续）"]]);
  };

  function perturb() {
    deviated = false; let n = 0;
    for (const a of agents) { if (!a.evac && n < agents.length * 0.34) { a.comp = false; a.tgt = "B"; n++; } }
    entry("态势感知", "b-sit", [["判断", "检测到现场扰动：约三成人群仍向已封闭的 B 口移动"], ["依据", "效果跟踪比对进行中…"]]);
  }

  let reported = false;
  function report() {
    reported = true;
    const base = evalBaseline();
    const mins = fmtS(Math.round(simT - S.eventAt));
    entry("评估复盘", "b-cmd", [
      ["结论", `处置完成：${mins} 完成 85% 疏散，峰值密度 <b style="color:var(--teal)">${peakDen.toFixed(1)} 人/㎡</b>`],
      ["对照", `无处置基线（仅A/C自然分流）：预计峰值 <b style="color:#dc2626">${base.peak} 人/㎡</b>，疏散 ${fmtS(base.evac_s)} —— <b style="color:var(--teal)">疏散提速约 ${Math.round((1 - ((simT - S.eventAt) / base.evac_s)) * 100)}%</b>`],
      ["依据", "2 轮会商 · 3 条预案条文溯源 · 1 次滚动闭环自动触发"],
      ["建议", "已生成教学案例：B口故障+低服从率复合场景，存入案例库"]]);
    setPhase("done", "live", "演示完成");
    banner("");
    const b = document.createElement("button"); b.className = "btn"; b.textContent = "重置演示";
    b.style.margin = "4px 14px 14px"; b.onclick = () => { running = false; resetAll(); };
    $("log").appendChild(b);
  }
  function evalBaseline() { const remain = N; const tot = 34 + 22; return { evac_s: Math.round(remain / tot / 0.62 * 10) * 10, peak: 5.6 }; }

  function drawMap() {
    const w = map.parentElement.clientWidth, h = map.parentElement.clientHeight;
    mctx.clearRect(0, 0, w, h);
    mctx.fillStyle = "#dbeafe"; mctx.fillRect(0, 0, w, h);
    mctx.strokeStyle = "rgba(37,99,235,.08)";
    for (let y = 0; y < h; y += 26) {
      mctx.beginPath(); mctx.moveTo(0, y + Math.sin(y * .4 + simT * .6) * 3);
      mctx.lineTo(w, y + Math.sin(y * .4 + simT * .6 + 2) * 3); mctx.stroke();
    }
    for (const g of Object.values(gates)) {
      mctx.strokeStyle = g.open ? "rgba(13,148,136,.55)" : "rgba(220,38,38,.5)";
      mctx.lineWidth = 7; mctx.beginPath(); mctx.moveTo(g.x, g.y); mctx.lineTo(g.bx, g.by); mctx.stroke();
    }
    mctx.save(); mctx.translate(isl.cx, isl.cy); mctx.rotate(isl.rot);
    mctx.beginPath(); mctx.ellipse(0, 0, isl.rw, isl.rh, 0, 0, Math.PI * 2);
    mctx.fillStyle = "#f1f5f9"; mctx.fill();
    mctx.strokeStyle = "#94a3b8"; mctx.lineWidth = 1.5; mctx.stroke(); mctx.restore();
    const den = densityEast();
    if (den > 1.8) {
      const a = Math.min(.42, (den - 1.8) * 0.16);
      const grd = mctx.createRadialGradient(zoneEast.x, zoneEast.y, 10, zoneEast.x, zoneEast.y, zoneEast.r);
      grd.addColorStop(0, `rgba(220,38,38,${a})`); grd.addColorStop(1, "rgba(220,38,38,0)");
      mctx.fillStyle = grd; mctx.beginPath();
      mctx.arc(zoneEast.x, zoneEast.y, zoneEast.r, 0, Math.PI * 2); mctx.fill();
    }
    mctx.beginPath(); mctx.arc(venue.x, venue.y, venue.r, 0, Math.PI * 2);
    mctx.fillStyle = "rgba(37,99,235,.06)"; mctx.fill();
    mctx.strokeStyle = "rgba(37,99,235,.35)"; mctx.setLineDash([4, 4]); mctx.stroke(); mctx.setLineDash([]);
    mctx.fillStyle = "#2563eb"; mctx.font = "11px sans-serif"; mctx.textAlign = "center";
    mctx.fillText("船台公园·主舞台", venue.x, venue.y - venue.r - 8);
    for (const a of agents) {
      if (a.evac) continue;
      mctx.fillStyle = a.comp ? "rgba(180,83,9,.8)" : "rgba(220,38,38,.85)";
      mctx.fillRect(a.x - 1.3, a.y - 1.3, 2.6, 2.6);
    }
    mctx.font = "11px sans-serif";
    for (const [k, g] of Object.entries(gates)) {
      mctx.beginPath(); mctx.arc(g.x, g.y, 7, 0, Math.PI * 2);
      mctx.fillStyle = g.open ? "#0d9488" : "#dc2626"; mctx.fill();
      mctx.fillStyle = "#ffffff"; mctx.textAlign = "center"; mctx.font = "bold 9px sans-serif";
      mctx.fillText(k, g.x, g.y + 3);
      mctx.font = "10px sans-serif";
      mctx.fillStyle = g.open ? "rgba(13,148,136,.95)" : "rgba(220,38,38,.95)";
      const oy = g.y < isl.cy ? -14 : 20;
      mctx.fillText(g.label + (g.open ? "" : " · 封闭"), g.x, g.y + oy);
    }
    mctx.fillStyle = "rgba(37,99,235,.5)"; mctx.font = "10px sans-serif"; mctx.textAlign = "left";
    mctx.fillText("黄浦江", 18, 26);
  }
  function drawChart() {
    const w = chart.parentElement.clientWidth - 16, h = chart.parentElement.clientHeight - 14;
    cctx.clearRect(0, 0, w + 16, h + 14);
    const maxT = Math.max(60, simT), maxD = 6;
    const X = (t) => 10 + (t / maxT) * (w - 16), Y = (d) => h - 4 - (d / maxD) * (h - 22);
    cctx.strokeStyle = "#e3e8f0"; cctx.lineWidth = 1;
    for (const d of [2, 4]) {
      cctx.beginPath(); cctx.moveTo(10, Y(d)); cctx.lineTo(w, Y(d)); cctx.stroke();
      cctx.fillStyle = "#94a3b8"; cctx.font = "9px monospace"; cctx.fillText(d, 2, Y(d) + 3);
    }
    cctx.strokeStyle = "rgba(220,38,38,.4)"; cctx.setLineDash([2, 3]);
    cctx.beginPath(); cctx.moveTo(10, Y(4)); cctx.lineTo(w, Y(4)); cctx.stroke(); cctx.setLineDash([]);
    if (expected) {
      cctx.strokeStyle = "rgba(13,148,136,.85)"; cctx.setLineDash([5, 4]); cctx.beginPath();
      for (let t = expected.t0; t <= simT + 20; t += 1) {
        const d = Math.max(0.7, expected.d0 * Math.exp(-(t - expected.t0) / expected.tau));
        const x = X(t); if (t === expected.t0) cctx.moveTo(x, Y(d)); else cctx.lineTo(x, Y(d));
      }
      cctx.stroke(); cctx.setLineDash([]);
    }
    cctx.strokeStyle = "#b45309"; cctx.lineWidth = 1.6; cctx.beginPath();
    hist.forEach((p, i) => { const x = X(p[0]), y = Y(p[1]); i ? cctx.lineTo(x, y) : cctx.moveTo(x, y); });
    cctx.stroke();
  }

  let last = 0, running = false, rafId = null;
  function loop(ts) {
    const dt = Math.min(0.05, (ts - last) / 1000); last = ts;
    if (running) {
      simT += dt; stepSim(dt);
      const den = densityEast(); peakDen = Math.max(peakDen, den);
      if ((simT * 10 | 0) % 3 === 0) hist.push([simT, den]);
      if (phase === "run" && simT >= S.eventAt) {
        gates.B.open = false;
        banner("突发事件：B口·东主通道设施故障，临时封闭");
        setPhase("event", "warn", "突发事件");
      }
      if (phase === "event" && simT >= S.consultAt) { setPhase("consult", "warn", "智能体会商中"); consult1(); }
      if (consultQueue.length) {
        consultTimer += dt;
        if (consultTimer >= consultQueue[0][0]) { consultTimer = 0; consultQueue.shift()[1](); }
      }
      if (expected && !deviated && phase === "exec" && simT > expected.t0 + 6) {
        const exp = Math.max(0.7, expected.d0 * Math.exp(-(simT - expected.t0) / expected.tau));
        if (den > exp * 1.35 && den > 1.6) { deviated = true; expected = null; consult2(); }
      }
      if (!reported && evacuated >= N * 0.85) report();
      $("sEvac").textContent = Math.round(evacuated / N * 100) + "%";
      $("sEvac").className = "n " + (evacuated / N > 0.5 ? "good" : "");
      $("sDen").textContent = den.toFixed(1);
      $("sDen").className = "n " + (den > 4 ? "bad" : den > 2.5 ? "" : "good");
      $("sPeak").textContent = peakDen.toFixed(1);
      $("clock").textContent = fmtT(simT);
    }
    drawMap(); drawChart();
    rafId = requestAnimationFrame(loop);
  }
  function fmtT(t) { const m = (t / 60) | 0, s = (t % 60) | 0; return `T+${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`; }
  function fmtS(s) { return s >= 60 ? `${(s / 60).toFixed(1)} 分钟` : `${s} 秒`; }

  function resetAll() {
    simT = 0; round = 0; expected = null; deviated = false; reported = false;
    hist.length = 0; consultQueue = [];
    $("stream").innerHTML = ""; $("approvewrap").style.display = "none";
    $("approveBtn").textContent = "批准推荐方案";
    setPhase("idle", "", "待命");
    $("overlay").style.display = "flex";
    layout(); spawn();
  }

  $("startBtn").onclick = () => {
    $("overlay").style.display = "none";
    spawn(); running = true; setPhase("run", "live", "散场进行中");
    entry("态势感知", "b-sit", [["判断", "散场开始，约1,000名观众离场，各通道状态正常"], ["依据", "仿真态势 Schema · tick 0"]]);
  };

  resize(); spawn(); rafId = requestAnimationFrame(loop);

  return () => {
    running = false;
    window.removeEventListener("resize", resize);
    if (rafId) cancelAnimationFrame(rafId);
  };
}
</script>

<template>
  <div id="dash-root">
    <div id="dash-app">
      <header>
        <h1>复兴岛 <b>·</b> 大型演艺活动应急决策演示</h1>
        <span class="chip" id="phase">待命</span>
        <span class="chip">四智能体会商 MVP</span>
        <span id="clock">T+00:00</span>
      </header>

      <div id="mapwrap">
        <canvas id="map"></canvas>
        <div id="banner"></div>
        <div id="legend">
          <span class="dot" style="background:#b45309"></span>观众
          &nbsp;<span class="dot" style="background:var(--teal)"></span>开放通道
          &nbsp;<span class="dot" style="background:var(--red)"></span>封闭通道
          &nbsp;<span class="dot" style="background:rgba(229,72,77,.4)"></span>高密度区
        </div>
        <div id="overlay">
          <button class="btn primary" id="startBtn" style="font-size:15px;padding:12px 34px">开始散场演示</button>
          <p>演出结束，约 1,000 名观众开始离场。演示将自动注入突发事件，展示多智能体会商、人机确认与滚动闭环全流程，约 90 秒。</p>
        </div>
      </div>

      <div id="log">
        <div class="hd"><span>AGENT 会商记录</span><span id="round" style="letter-spacing:.05em">—</span></div>
        <div id="stream"></div>
        <div id="approvewrap">
          <button class="btn primary pulse" id="approveBtn">批准推荐方案</button>
          <button class="btn" id="rejectBtn">驳回</button>
          <span class="hint">L3 · 待指挥员决策</span>
        </div>
      </div>

      <div id="ft">
        <div id="chartbox">
          <span class="cl">东区人群密度(人/㎡) — 实线:实际 · 虚线:预期</span>
          <canvas id="chart"></canvas>
        </div>
        <div id="stats">
          <div class="st"><div class="n" id="sEvac">0%</div><div class="l">已疏散</div></div>
          <div class="st"><div class="n" id="sDen">0.0</div><div class="l">东区密度</div></div>
          <div class="st"><div class="n" id="sPeak">0.0</div><div class="l">峰值密度</div></div>
          <div class="st"><div class="n" id="sRound">0</div><div class="l">会商轮次</div></div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
#dash-root {
  --amber: #d97706; --teal: #0d9488; --red: #dc2626; --blue: #2563eb;
  --mono: ui-monospace, "SF Mono", "Cascadia Mono", Consolas, monospace;
  height: calc(100vh - 52px - 44px);
  margin: -22px -26px;
  overflow: hidden;
}
#dash-app { display: grid; height: 100%;
  grid-template-rows: 46px 1fr 128px;
  grid-template-columns: minmax(0,1.55fr) minmax(340px,1fr);
  grid-template-areas: "hd hd" "map log" "ft log";
}
header { grid-area: hd; display: flex; align-items: center; gap: 14px;
  padding: 0 16px; border-bottom: 1px solid var(--line); background: var(--panel); }
header h1 { font-size: 15px; font-weight: 600; letter-spacing: .06em; }
header h1 b { color: var(--amber); font-weight: 600; }
.chip { font-family: var(--mono); font-size: 11px; padding: 3px 9px; border-radius: 3px;
  border: 1px solid var(--line); color: var(--muted); letter-spacing: .08em; }
.chip.live { border-color: var(--teal); color: var(--teal); }
.chip.warn { border-color: var(--red); color: var(--red); animation: pulse 1.2s infinite; }
#clock { margin-left: auto; font-family: var(--mono); font-size: 12px; color: var(--muted); }
@keyframes pulse { 50% { opacity: .45; } }

#mapwrap { grid-area: map; position: relative; background: #eff6ff; overflow: hidden; }
canvas { display: block; width: 100%; height: 100%; }
#banner { position: absolute; top: 14px; left: 50%; transform: translateX(-50%);
  background: rgba(220,38,38,.08); border: 1px solid var(--red); color: var(--red);
  font-size: 13px; padding: 7px 18px; border-radius: 4px; display: none;
  backdrop-filter: blur(4px); white-space: nowrap; }
#legend { position: absolute; left: 14px; bottom: 12px; font-size: 11px; color: var(--muted);
  background: rgba(255,255,255,.85); padding: 8px 12px; border-radius: 4px; line-height: 1.9;
  border: 1px solid var(--line); }
.dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 6px; vertical-align: -1px; }
#overlay { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center;
  background: rgba(255,255,255,.92); flex-direction: column; gap: 18px; z-index: 5; }
#overlay p { color: var(--muted); max-width: 420px; text-align: center; line-height: 1.8; font-size: 13px; }

.btn { font-family: inherit; font-size: 13px; padding: 9px 22px; border-radius: 4px; cursor: pointer;
  border: 1px solid var(--line); background: var(--panel2); color: var(--ink); letter-spacing: .04em; }
.btn:hover { border-color: var(--muted); }
.btn.primary { background: var(--amber); border-color: var(--amber); color: #fff; font-weight: 600; }
.btn.primary:hover { filter: brightness(1.08); }
.btn.pulse { animation: glowp 1.4s infinite; }
@keyframes glowp { 50% { box-shadow: 0 0 14px rgba(217,119,6,.45); } }

#log { grid-area: log; border-left: 1px solid var(--line); background: var(--panel);
  display: flex; flex-direction: column; min-height: 0; }
#log > .hd { padding: 10px 16px; border-bottom: 1px solid var(--line); font-size: 12px;
  color: var(--muted); letter-spacing: .14em; display: flex; justify-content: space-between; }
#stream { flex: 1; overflow-y: auto; padding: 12px 14px; scroll-behavior: smooth; }
.entry { margin-bottom: 14px; border: 1px solid var(--line); border-radius: 5px;
  background: var(--panel2); overflow: hidden; opacity: 0; transform: translateY(6px);
  transition: opacity .3s, transform .3s; }
.entry.show { opacity: 1; transform: none; }
.entry .ehd { display: flex; align-items: center; gap: 8px; padding: 7px 12px;
  border-bottom: 1px solid var(--line); font-size: 12px; }
.badge { font-size: 11px; padding: 2px 8px; border-radius: 3px; font-weight: 600; letter-spacing: .05em; }
.b-sit { background: rgba(37,99,235,.1); color: var(--blue); }
.b-risk { background: rgba(220,38,38,.1); color: var(--red); }
.b-strat { background: rgba(13,148,136,.1); color: var(--teal); }
.b-cmd { background: rgba(217,119,6,.1); color: var(--amber); }
.ehd time { margin-left: auto; font-family: var(--mono); font-size: 10px; color: var(--dim); }
.entry .body { padding: 9px 12px; line-height: 1.75; font-size: 12.5px; }
.kv { display: flex; gap: 8px; margin-bottom: 3px; }
.kv .k { color: var(--dim); flex: none; font-size: 11px; padding-top: 2px; width: 34px; letter-spacing: .1em; }
.kv .v { color: var(--ink); }
.cite { font-family: var(--mono); font-size: 11px; color: var(--amber); cursor: help;
  border-bottom: 1px dashed rgba(217,119,6,.5); position: relative; }
.plancard { border: 1px solid var(--line); border-radius: 4px; margin-top: 8px; padding: 9px 11px;
  background: var(--panel2); }
.plancard.rec { border-color: var(--amber); }
.plancard .pn { font-size: 12.5px; font-weight: 600; display: flex; align-items: center; gap: 8px; }
.tag { font-size: 10px; color: var(--amber); border: 1px solid var(--amber); padding: 1px 6px; border-radius: 2px; }
.pm { font-family: var(--mono); font-size: 11px; color: var(--muted); margin-top: 5px; line-height: 1.8; }
.pm b { color: var(--teal); font-weight: 600; }
#approvewrap { padding: 12px 14px; border-top: 1px solid var(--line); display: none; gap: 10px; }
#approvewrap .hint { font-size: 11px; color: var(--muted); align-self: center; }

#ft { grid-area: ft; border-top: 1px solid var(--line); background: var(--panel);
  display: grid; grid-template-columns: 1fr 300px; min-width: 0; }
#chartbox { position: relative; padding: 8px 4px 4px 12px; min-width: 0; }
#chartbox .cl { position: absolute; top: 8px; left: 14px; font-size: 10px; color: var(--muted);
  letter-spacing: .12em; z-index: 2; }
#stats { border-left: 1px solid var(--line); padding: 10px 16px; display: grid;
  grid-template-columns: 1fr 1fr; gap: 2px 14px; align-content: center; }
.st .n { font-family: var(--mono); font-size: 19px; font-weight: 600; color: var(--ink); }
.st .n.good { color: var(--teal); }
.st .n.bad { color: var(--red); }
.st .l { font-size: 10px; color: var(--dim); letter-spacing: .1em; margin-top: 1px; }
</style>

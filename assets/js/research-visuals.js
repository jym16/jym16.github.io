(function () {
  "use strict";

  const canvases = Array.from(document.querySelectorAll("canvas[data-research-viz]"));
  if (!canvases.length) return;

  const networkNodes = [
    [0.10, 0.51], [0.20, 0.25], [0.22, 0.76], [0.36, 0.43],
    [0.48, 0.18], [0.50, 0.67], [0.64, 0.37], [0.72, 0.74],
    [0.82, 0.20], [0.90, 0.52]
  ];
  const networkEdges = [
    [0, 1], [0, 2], [0, 3], [1, 3], [1, 4], [2, 3], [2, 5],
    [3, 4], [3, 5], [3, 6], [4, 6], [4, 8], [5, 6], [5, 7],
    [6, 7], [6, 8], [6, 9], [7, 9], [8, 9]
  ];

  function theme(canvas) {
    const style = getComputedStyle(canvas);
    const read = (name) => style.getPropertyValue(name).trim();
    return {
      bg: read("--viz-bg"),
      grid: read("--viz-grid"),
      ink: read("--viz-ink"),
      muted: read("--viz-muted"),
      blue: read("--viz-blue"),
      blueSoft: read("--viz-blue-soft"),
      coral: read("--viz-coral"),
      gold: read("--viz-gold"),
      teal: read("--viz-teal"),
      violet: read("--viz-violet")
    };
  }

  function prepare(canvas) {
    const rect = canvas.getBoundingClientRect();
    const width = Math.max(280, rect.width || 400);
    const height = Math.max(210, rect.height || width * 0.75);
    const scale = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.round(width * scale);
    canvas.height = Math.round(height * scale);
    const ctx = canvas.getContext("2d");
    ctx.setTransform(scale, 0, 0, scale, 0, 0);
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    const colors = theme(canvas);
    ctx.fillStyle = colors.bg;
    ctx.fillRect(0, 0, width, height);
    return { ctx, width, height, colors };
  }

  function edge(ctx, x1, y1, x2, y2, color, width, dash) {
    ctx.save();
    ctx.strokeStyle = color;
    ctx.lineWidth = width || 1.4;
    ctx.setLineDash(dash || []);
    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.lineTo(x2, y2);
    ctx.stroke();
    ctx.restore();
  }

  function node(ctx, x, y, radius, fill, stroke, alpha) {
    ctx.save();
    ctx.globalAlpha = alpha === undefined ? 1 : alpha;
    ctx.beginPath();
    ctx.arc(x, y, radius, 0, Math.PI * 2);
    ctx.fillStyle = fill;
    ctx.fill();
    if (stroke) {
      ctx.strokeStyle = stroke;
      ctx.lineWidth = 1.25;
      ctx.stroke();
    }
    ctx.restore();
  }

  function label(ctx, text, x, y, color, align, size, weight) {
    ctx.save();
    ctx.fillStyle = color;
    ctx.textAlign = align || "left";
    ctx.textBaseline = "middle";
    ctx.font = `${weight || 600} ${size || 12}px "STIX Two Text", serif`;
    ctx.fillText(text, x, y);
    ctx.restore();
  }

  function arrow(ctx, x1, y1, x2, y2, color, width) {
    edge(ctx, x1, y1, x2, y2, color, width || 2);
    const angle = Math.atan2(y2 - y1, x2 - x1);
    const size = 7;
    ctx.save();
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.moveTo(x2, y2);
    ctx.lineTo(x2 - size * Math.cos(angle - Math.PI / 6), y2 - size * Math.sin(angle - Math.PI / 6));
    ctx.lineTo(x2 - size * Math.cos(angle + Math.PI / 6), y2 - size * Math.sin(angle + Math.PI / 6));
    ctx.closePath();
    ctx.fill();
    ctx.restore();
  }

  function drawNetwork(ctx, bounds, colors, amplitudes) {
    const [x, y, width, height] = bounds;
    const points = networkNodes.map(([px, py]) => [x + px * width, y + py * height]);
    networkEdges.forEach(([a, b]) => {
      edge(ctx, points[a][0], points[a][1], points[b][0], points[b][1], colors.grid, 1.15);
    });
    points.forEach(([px, py], index) => {
      const amp = amplitudes ? amplitudes[index] : 0.45;
      if (amp > 0.78) node(ctx, px, py, 12 + amp * 5, colors.coral, null, 0.12);
      node(ctx, px, py, 3.3 + amp * 4.5, amp > 0.62 ? colors.coral : colors.blueSoft, colors.bg, 1);
    });
  }

  function drawLocalization(canvas) {
    const { ctx, width: w, height: h, colors: c } = prepare(canvas);
    const pad = Math.max(22, w * 0.055);
    const gap = Math.max(20, w * 0.05);
    const panelW = (w - pad * 2 - gap) / 2;
    label(ctx, "localized", pad + panelW / 2, 27, c.ink, "center", 12, 600);
    label(ctx, "extended", pad + panelW + gap + panelW / 2, 27, c.ink, "center", 12, 600);
    const local = [0.08, 0.1, 0.1, 1, 0.2, 0.34, 0.18, 0.08, 0.06, 0.05];
    const extended = [0.62, 0.5, 0.57, 0.68, 0.45, 0.72, 0.58, 0.48, 0.55, 0.66];
    drawNetwork(ctx, [pad, 47, panelW, h - 76], c, local);
    drawNetwork(ctx, [pad + panelW + gap, 47, panelW, h - 76], c, extended);
    edge(ctx, w / 2, 42, w / 2, h - 24, c.grid, 1, [3, 5]);
    label(ctx, "mode amplitude", w / 2, h - 13, c.muted, "center", 10, 400);
  }

  function oscillatorModule(ctx, cx, cy, radius, phases, colors, active) {
    ctx.save();
    ctx.strokeStyle = colors.grid;
    ctx.lineWidth = 1.1;
    ctx.beginPath();
    ctx.arc(cx, cy, radius, 0, Math.PI * 2);
    ctx.stroke();
    phases.forEach((phase, i) => {
      const angle = (i / phases.length) * Math.PI * 2 - Math.PI / 2;
      const x = cx + Math.cos(angle) * radius;
      const y = cy + Math.sin(angle) * radius;
      const hand = phase - Math.PI / 2;
      node(ctx, x, y, 8, active, colors.bg);
      edge(ctx, x, y, x + Math.cos(hand) * 5.5, y + Math.sin(hand) * 5.5, colors.bg, 1.5);
    });
    node(ctx, cx, cy, 3.5, colors.ink);
    ctx.restore();
  }

  function drawSynchronization(canvas) {
    const { ctx, width: w, height: h, colors: c } = prepare(canvas);
    const r = Math.min(w, h) * 0.15;
    const modules = [
      [w * 0.28, h * 0.34, c.blue, 0.2],
      [w * 0.70, h * 0.34, c.teal, 1.9],
      [w * 0.50, h * 0.72, c.violet, 3.6]
    ];
    edge(ctx, modules[0][0] + r * 0.7, modules[0][1] + r * 0.35, modules[1][0] - r * 0.7, modules[1][1] + r * 0.35, c.muted, 1.5, [5, 6]);
    edge(ctx, modules[0][0] + r * 0.5, modules[0][1] + r * 0.75, modules[2][0] - r * 0.45, modules[2][1] - r * 0.7, c.muted, 1.5, [5, 6]);
    edge(ctx, modules[1][0] - r * 0.5, modules[1][1] + r * 0.75, modules[2][0] + r * 0.45, modules[2][1] - r * 0.7, c.muted, 1.5, [5, 6]);
    modules.forEach(([x, y, color, phase], index) => {
      const phases = Array.from({ length: 7 }, (_, i) => phase + (i % 2 ? 0.08 : -0.08));
      oscillatorModule(ctx, x, y, r, phases, c, color);
      label(ctx, `module ${index + 1}`, x, y + r + 20, c.muted, "center", 10, 400);
    });
    label(ctx, "strong local coupling", w * 0.5, 19, c.ink, "center", 11, 600);
    label(ctx, "weaker global coupling", w * 0.5, h - 12, c.muted, "center", 10, 400);
  }

  function drawPhysical(canvas) {
    const { ctx, width: w, height: h, colors: c } = prepare(canvas);
    const leftX = w * 0.26;
    const rightX = w * 0.74;
    label(ctx, "full physical network", leftX, 24, c.ink, "center", 11, 600);
    label(ctx, "coarse-grained", rightX, 24, c.ink, "center", 11, 600);
    const left = [
      [leftX - w * 0.12, h * 0.42, 21], [leftX + w * 0.09, h * 0.35, 30],
      [leftX - w * 0.04, h * 0.69, 16], [leftX + w * 0.14, h * 0.70, 23]
    ];
    const links = [[0, 1], [0, 2], [1, 2], [1, 3], [2, 3]];
    links.forEach(([a, b]) => edge(ctx, left[a][0], left[a][1], left[b][0], left[b][1], c.grid, 4));
    left.forEach(([x, y, r], i) => {
      node(ctx, x, y, r, i % 2 ? c.blueSoft : c.teal, c.ink, 0.88);
      const count = i === 1 ? 6 : i === 3 ? 5 : 4;
      for (let j = 0; j < count; j += 1) {
        const angle = (j / count) * Math.PI * 2 + i;
        node(ctx, x + Math.cos(angle) * r * 0.5, y + Math.sin(angle) * r * 0.5, 2.1, c.bg);
      }
    });
    arrow(ctx, w * 0.46, h * 0.53, w * 0.54, h * 0.53, c.accent || c.blue, 2);
    const right = left.map(([x, y, r]) => [rightX + (x - leftX) * 0.85, y, r * 0.62]);
    links.forEach(([a, b]) => edge(ctx, right[a][0], right[a][1], right[b][0], right[b][1], c.grid, 1.8));
    right.forEach(([x, y, r], i) => node(ctx, x, y, r, i % 2 ? c.blue : c.teal, c.bg));
    label(ctx, "volume → node weight", rightX, h - 18, c.muted, "center", 10, 400);
  }

  function neighborhood(ctx, cx, cy, scale, colors, hub) {
    const rings = hub ? [0.33, 0.62, 0.94] : [0.4, 0.68, 0.94];
    rings.forEach((ring, i) => {
      ctx.save();
      ctx.strokeStyle = colors.grid;
      ctx.lineWidth = 1;
      ctx.setLineDash([3, 5]);
      ctx.beginPath();
      ctx.arc(cx, cy, scale * ring, 0, Math.PI * 2);
      ctx.stroke();
      ctx.restore();
      const count = hub ? [8, 7, 5][i] : [4, 7, 10][i];
      for (let j = 0; j < count; j += 1) {
        const angle = (j / count) * Math.PI * 2 + i * 0.55;
        const x = cx + Math.cos(angle) * scale * ring;
        const y = cy + Math.sin(angle) * scale * ring;
        edge(ctx, cx, cy, x, y, colors.grid, 0.7);
        node(ctx, x, y, hub && i === 0 ? 3.7 : 3, colors.blueSoft, colors.bg);
      }
    });
    node(ctx, cx, cy, hub ? 11 : 6, hub ? colors.coral : colors.blue, colors.bg);
  }

  function drawBifractality(canvas) {
    const { ctx, width: w, height: h, colors: c } = prepare(canvas);
    const scale = Math.min(w * 0.18, h * 0.3);
    const y = h * 0.54;
    neighborhood(ctx, w * 0.28, y, scale, c, true);
    neighborhood(ctx, w * 0.72, y, scale, c, false);
    label(ctx, "hub neighborhood", w * 0.28, 24, c.ink, "center", 11, 600);
    label(ctx, "ordinary neighborhood", w * 0.72, 24, c.ink, "center", 11, 600);
    label(ctx, "lower local dimension", w * 0.28, h - 16, c.coral, "center", 10, 600);
    label(ctx, "global fractal dimension", w * 0.72, h - 16, c.blue, "center", 10, 600);
  }

  function drawRandomWalk(canvas) {
    const { ctx, width: w, height: h, colors: c } = prepare(canvas);
    const points = [
      [0.50, 0.50], [0.35, 0.36], [0.65, 0.34], [0.34, 0.65], [0.66, 0.66],
      [0.20, 0.23], [0.36, 0.18], [0.69, 0.18], [0.81, 0.31], [0.18, 0.67],
      [0.30, 0.82], [0.67, 0.84], [0.82, 0.70], [0.09, 0.12], [0.25, 0.08],
      [0.75, 0.07], [0.93, 0.25], [0.08, 0.77], [0.22, 0.92], [0.76, 0.94], [0.93, 0.79]
    ].map(([x, y]) => [x * w, y * h]);
    const branches = [
      [0, 1], [0, 2], [0, 3], [0, 4], [1, 5], [1, 6], [2, 7], [2, 8],
      [3, 9], [3, 10], [4, 11], [4, 12], [5, 13], [5, 14], [7, 15],
      [8, 16], [9, 17], [10, 18], [11, 19], [12, 20]
    ];
    branches.forEach(([a, b]) => edge(ctx, points[a][0], points[a][1], points[b][0], points[b][1], c.grid, 1.35));
    points.forEach(([x, y], i) => node(ctx, x, y, i === 0 ? 8 : 3.8, i === 0 ? c.coral : c.blueSoft, c.bg));
    const route = [14, 5, 1, 0, 2, 8, 16, 8, 2, 0, 4, 11, 19];
    ctx.save();
    ctx.strokeStyle = c.gold;
    ctx.lineWidth = 3.2;
    ctx.beginPath();
    route.forEach((index, i) => {
      const [x, y] = points[index];
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();
    ctx.restore();
    node(ctx, points[route[0]][0], points[route[0]][1], 5.5, c.teal, c.bg);
    node(ctx, points[route[route.length - 1]][0], points[route[route.length - 1]][1], 6, c.gold, c.bg);
    label(ctx, "start", points[route[0]][0] + 11, points[route[0]][1] - 8, c.muted, "left", 10, 400);
    label(ctx, "walker", points[route[route.length - 1]][0] - 10, points[route[route.length - 1]][1] - 11, c.muted, "right", 10, 400);
  }

  function drawCrossover(canvas) {
    const { ctx, width: w, height: h, colors: c } = prepare(canvas);
    const left = Math.max(48, w * 0.13);
    const right = w - Math.max(22, w * 0.055);
    const plotWidth = right - left;
    const crossX = left + plotWidth * 0.54;
    const topPlot = { top: h * 0.12, bottom: h * 0.42 };
    const bottomPlot = { top: h * 0.59, bottom: h * 0.89 };

    function axes(plot, yText, xText) {
      edge(ctx, left, plot.top, left, plot.bottom, c.grid, 1.2);
      edge(ctx, left, plot.bottom, right, plot.bottom, c.grid, 1.2);
      label(ctx, yText, left + 3, plot.top - 10, c.ink, "left", 10, 500);
      label(ctx, xText, right, plot.bottom + 13, c.muted, "right", 10, 400);
      edge(ctx, crossX, plot.top + 2, crossX, plot.bottom, c.muted, 1, [3, 5]);
    }

    function segment(points, color) {
      ctx.save();
      ctx.strokeStyle = color;
      ctx.lineWidth = 3;
      ctx.beginPath();
      points.forEach(([x, y], index) => {
        if (index === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      });
      ctx.stroke();
      ctx.restore();
    }

    axes(topPlot, "local volume V_i(ℓ)", "distance ℓ");
    const structureStart = [left + 7, topPlot.bottom - 7];
    const structureCross = [crossX, topPlot.top + (topPlot.bottom - topPlot.top) * 0.47];
    const structureEnd = [right - 4, topPlot.top + 7];
    segment([structureStart, structureCross], c.blue);
    segment([structureCross, structureEnd], c.coral);
    node(ctx, structureCross[0], structureCross[1], 4.5, c.gold, c.bg);
    label(ctx, "structural crossover", left + plotWidth * 0.5, topPlot.top - 10, c.ink, "center", 11, 500);
    label(ctx, "ℓ×", crossX, topPlot.bottom + 13, c.gold, "center", 10, 500);

    axes(bottomPlot, "return p_ii(t)", "time t");
    const dynamicsStart = [left + 7, bottomPlot.top + 7];
    const dynamicsCross = [crossX, bottomPlot.top + (bottomPlot.bottom - bottomPlot.top) * 0.48];
    const dynamicsEnd = [right - 4, bottomPlot.bottom - 7];
    segment([dynamicsStart, dynamicsCross], c.blue);
    segment([dynamicsCross, dynamicsEnd], c.coral);
    node(ctx, dynamicsCross[0], dynamicsCross[1], 4.5, c.gold, c.bg);
    label(ctx, "dynamical crossover", left + plotWidth * 0.5, bottomPlot.top - 10, c.ink, "center", 11, 500);
    label(ctx, "t×", crossX, bottomPlot.bottom + 13, c.gold, "center", 10, 500);
  }

  function triad(ctx, cx, cy, scale, colors, positive) {
    const left = [cx - scale * 0.62, cy + scale * 0.42];
    const right = [cx + scale * 0.62, cy + scale * 0.42];
    const top = [cx, cy - scale * 0.56];
    const action = positive ? colors.teal : colors.coral;
    edge(ctx, left[0], left[1], right[0], right[1], action, positive ? 4 : 2, positive ? [] : [5, 4]);
    node(ctx, left[0], left[1], 10, colors.blue, colors.bg);
    node(ctx, right[0], right[1], 10, colors.blue, colors.bg);
    node(ctx, top[0], top[1], 10, action, colors.bg);
    arrow(ctx, top[0], top[1] + 12, cx, cy + scale * 0.32, action, 2.2);
    label(ctx, positive ? "+" : "−", cx + 13, cy + scale * 0.15, action, "left", 17, 600);
    label(ctx, "i", left[0], left[1] + 23, colors.muted, "center", 10, 400);
    label(ctx, "j", right[0], right[1] + 23, colors.muted, "center", 10, 400);
    label(ctx, "modulator", top[0], top[1] - 18, colors.muted, "center", 10, 400);
  }

  function drawTriadic(canvas) {
    const { ctx, width: w, height: h, colors: c } = prepare(canvas);
    const scale = Math.min(w * 0.2, h * 0.3);
    triad(ctx, w * 0.28, h * 0.53, scale, c, true);
    triad(ctx, w * 0.72, h * 0.53, scale, c, false);
    label(ctx, "activation", w * 0.28, 22, c.ink, "center", 11, 600);
    label(ctx, "inhibition", w * 0.72, 22, c.ink, "center", 11, 600);
    edge(ctx, w / 2, 38, w / 2, h - 25, c.grid, 1, [3, 5]);
  }

  const renderers = {
    localization: drawLocalization,
    synchronization: drawSynchronization,
    crossover: drawCrossover,
    physical: drawPhysical,
    bifractality: drawBifractality,
    "random-walk": drawRandomWalk,
    triadic: drawTriadic
  };

  function draw(canvas) {
    const renderer = renderers[canvas.dataset.researchViz];
    if (renderer) renderer(canvas);
  }

  function drawAll() {
    canvases.forEach(draw);
  }

  let frame = 0;
  function scheduleDraw() {
    cancelAnimationFrame(frame);
    frame = requestAnimationFrame(drawAll);
  }

  const resizeObserver = new ResizeObserver(scheduleDraw);
  canvases.forEach((canvas) => resizeObserver.observe(canvas));

  const themeObserver = new MutationObserver(scheduleDraw);
  themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ["class", "data-bs-theme", "style"] });
  themeObserver.observe(document.body, { attributes: true, attributeFilter: ["class", "data-bs-theme", "style"] });

  window.addEventListener("beforeprint", drawAll);
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(drawAll);
  drawAll();
})();

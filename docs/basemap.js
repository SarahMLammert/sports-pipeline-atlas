// The physical basemap under the map pages: NASA's Blue Marble shaded relief and bathymetry, as web-map tiles
// (from FreeTiler, https://github.com/freetiler/nasa-bluemarble, MIT; zooms 0-6 kept in docs/tiles/bluemarble, since
// jsDelivr refuses that repo for being over its size limit), recoloured in the browser to
// look like a physical atlas: lighter, brighter land that keeps its relief shading, and the sea in atlas blues that
// deepen offshore.
//
//   Basemap.drawMercator(ctx, w, h, view, redraw)   for the zoomable Recruiting Map (Web Mercator, like the tiles)
//   Basemap.render(projection, w, h)                 for the fixed maps: a promise of a canvas w×h in that projection
//   Basemap.rivers(), riverPaths(), strokeRivers()   the rivers, drawn on top of the relief
//
// If the tiles can't load, nothing is drawn and the pages keep their plain land colours.
(function () {
  "use strict";
  // next to this script, so every page finds them wherever it sits
  const HERE = (document.currentScript && document.currentScript.src) || location.href;
  const URL = new window.URL("tiles/bluemarble/", HERE).href + "{z}/{x}/{y}.jpeg";
  const MAX_Z = 6, SIZE = 256;
  const DEEP = [92, 150, 205], SHALLOW = [208, 234, 247];
  const tiles = new Map();          // "z/x/y" -> { canvas, data } once loaded, null while loading, false if it failed

  // A tile's colours, as a physical atlas: the sea by depth (the picture's darker blues are deeper), the land lighter
  // and more colourful.
  function recolor(px) {
    for (let i = 0; i < px.length; i += 4) {
      const r = px[i], g = px[i + 1], b = px[i + 2], lum = 0.3 * r + 0.59 * g + 0.11 * b;
      if ((b > r + 10 && b >= g) || (lum < 45 && b >= r)) {
        const t = Math.min(1, Math.max(0, (lum - 20) / 110));
        px[i] = DEEP[0] + (SHALLOW[0] - DEEP[0]) * t;
        px[i + 1] = DEEP[1] + (SHALLOW[1] - DEEP[1]) * t;
        px[i + 2] = DEEP[2] + (SHALLOW[2] - DEEP[2]) * t;
      } else {
        const m = (r + g + b) / 3;
        for (let c = 0; c < 3; c++) {
          const v = m + (px[i + c] - m) * 1.45;
          px[i + c] = 255 - (255 - Math.min(255, Math.max(0, v))) * 0.6;
        }
      }
    }
  }
  const waiting = new Map();        // "z/x/y" -> the callbacks to run when it arrives
  function load(z, x, y, done) {
    const key = `${z}/${x}/${y}`, have = tiles.get(key);
    if (have || have === false) { if (done) done(); return have || null; }
    if (done) { if (!waiting.has(key)) waiting.set(key, []); if (!waiting.get(key).includes(done)) waiting.get(key).push(done); }
    if (have === null) return null;      // already on its way
    tiles.set(key, null);
    const settle = (value) => { tiles.set(key, value); const fns = waiting.get(key) || []; waiting.delete(key); fns.forEach((f) => f()); };
    const img = new Image();
    img.crossOrigin = "anonymous";
    img.onload = () => {
      try {
        const c = document.createElement("canvas");
        c.width = c.height = SIZE;
        const g = c.getContext("2d", { willReadFrequently: true });
        g.drawImage(img, 0, 0, SIZE, SIZE);
        const id = g.getImageData(0, 0, SIZE, SIZE);
        recolor(id.data);
        g.putImageData(id, 0, 0);
        settle({ canvas: c, data: id.data });
      } catch { settle(false); }
    };
    img.onerror = () => settle(false);
    img.src = URL.replace("{z}", z).replace("{x}", x).replace("{y}", y);
    return null;
  }
  const loaded = (z, x, y) => { const t = tiles.get(`${z}/${x}/${y}`); return t || null; };

  // ---- the zoomable map ----
  // view: { world: the whole world's width on screen in px, x0, y0: where the Web Mercator square's top-left corner
  // (180°W, 85.05°N) is on screen, dpr }. redraw is called (once per frame at most) as tiles arrive.
  let pending = false, again = null;
  const ask = () => { if (!pending && again) { pending = true; requestAnimationFrame(() => { pending = false; again(); }); } };
  function drawMercator(ctx, w, h, view, redraw) {
    again = redraw;
    const { world, x0, y0, dpr = 1 } = view;
    const z = Math.max(0, Math.min(MAX_Z, Math.ceil(Math.log2(world * dpr / SIZE))));
    const n = 2 ** z, ts = world / n;
    const txa = Math.floor(-x0 / ts), txb = Math.floor((w - x0) / ts), tya = Math.max(0, Math.floor(-y0 / ts)), tyb = Math.min(n - 1, Math.floor((h - y0) / ts));
    ctx.imageSmoothingEnabled = true;
    for (let ty = tya; ty <= tyb; ty++) {
      for (let tx = txa; tx <= txb; tx++) {
        const x = ((tx % n) + n) % n, sx = x0 + tx * ts, sy = y0 + ty * ts;
        const t = loaded(z, x, ty) || (tiles.get(`${z}/${x}/${ty}`) === false ? null : load(z, x, ty, ask));
        if (t) { ctx.drawImage(t.canvas, sx, sy, ts + 0.5, ts + 0.5); continue; }
        // not here yet: a blurrier piece of a lower zoom's tile meanwhile
        for (let up = 1; up <= z; up++) {
          const pz = z - up, px = x >> up, py = ty >> up, p = loaded(pz, px, py);
          if (!p) continue;
          const part = SIZE / 2 ** up, ox = (x - (px << up)) * part, oy = (ty - (py << up)) * part;
          ctx.drawImage(p.canvas, ox, oy, part, part, sx, sy, ts + 0.5, ts + 0.5);
          break;
        }
      }
    }
  }

  // ---- a fixed projection: each pixel looks up its place on the tiles ----
  const merc = (lon, lat) => {
    const s = Math.sin(Math.max(-85.0511, Math.min(85.0511, lat)) * Math.PI / 180);
    return [(lon + 180) / 360, 0.5 - Math.log((1 + s) / (1 - s)) / (4 * Math.PI)];
  };
  function render(projection, w, h, zoom = MAX_Z) {
    zoom = Math.min(zoom, MAX_Z);
    // drawn at up to ~700,000 pixels and scaled up: relief is soft, and this keeps a redraw under a second
    const k = Math.min(1, Math.sqrt(700000 / (w * h))), cw = Math.max(1, Math.round(w * k)), ch = Math.max(1, Math.round(h * k));
    const n = 2 ** zoom, where = new Float32Array(cw * ch * 2).fill(-1), need = new Set();
    for (let y = 0; y < ch; y++) {
      for (let x = 0; x < cw; x++) {
        const ll = projection.invert([(x + 0.5) / k, (y + 0.5) / k]);
        if (!ll || !Number.isFinite(ll[0]) || !Number.isFinite(ll[1])) continue;
        const p = projection(ll);              // outside the projection's own area (Albers USA's insets): leave blank
        if (!p || Math.abs(p[0] - (x + 0.5) / k) > 2 || Math.abs(p[1] - (y + 0.5) / k) > 2) continue;
        const [mx, my] = merc(ll[0], ll[1]), i = (y * cw + x) * 2;
        where[i] = mx * n * SIZE; where[i + 1] = my * n * SIZE;
        need.add(`${Math.floor(mx * n)}/${Math.floor(my * n)}`);
      }
    }
    return new Promise((resolve, reject) => {
      const keys = [...need];
      let left = keys.length;
      const finish = () => {
        if (--left > 0) return;
        const out = document.createElement("canvas");
        out.width = cw; out.height = ch;
        const g = out.getContext("2d"), id = g.createImageData(cw, ch), px = id.data;
        let any = false;
        for (let j = 0; j < cw * ch; j++) {
          const X = where[j * 2], Y = where[j * 2 + 1];
          if (X < 0) continue;
          const t = loaded(zoom, Math.floor(X / SIZE), Math.floor(Y / SIZE));
          if (!t) continue;
          const s = ((Math.floor(Y) % SIZE) * SIZE + (Math.floor(X) % SIZE)) * 4;
          px[j * 4] = t.data[s]; px[j * 4 + 1] = t.data[s + 1]; px[j * 4 + 2] = t.data[s + 2]; px[j * 4 + 3] = 255;
          any = true;
        }
        if (!any) { reject(new Error("no tiles")); return; }
        g.putImageData(id, 0, 0);
        resolve(out);
      };
      if (!left) { reject(new Error("nothing to draw")); return; }
      keys.forEach((key) => { const [x, y] = key.split("/").map(Number); load(zoom, x, y, finish); });
    });
  }

  // ---- rivers: Natural Earth's rivers and lake centerlines (docs/rivers.json, [scalerank, [lon, lat, lon, lat, ...]]) ----
  // scalerank 0 is the biggest (the Mississippi, the Missouri); 8 the smallest kept.
  let riversAsked = null;
  function rivers() {
    return riversAsked || (riversAsked = fetch("rivers.json").then((r) => (r.ok ? r.json() : Promise.reject(new Error(r.status))))
      .then((j) => j.rivers).catch((e) => { riversAsked = null; throw e; }));
  }
  // The rivers drawn through a projection, as [{ rank, path: Path2D }]; a point the projection can't show breaks the line.
  function riverPaths(list, projection, maxRank = 8) {
    const out = [];
    for (const [rank, c] of list) {
      if (rank > maxRank) continue;
      const path = new Path2D();
      let pen = false, any = false;
      for (let i = 0; i < c.length; i += 2) {
        const xy = projection([c[i], c[i + 1]]);
        if (!xy || !Number.isFinite(xy[0])) { pen = false; continue; }
        if (pen) { path.lineTo(xy[0], xy[1]); any = true; } else { path.moveTo(xy[0], xy[1]); pen = true; }
      }
      if (any) out.push({ rank, path });
    }
    return out;
  }
  // Stroke them, bigger rivers wider. unit: screen px per path unit (the zoomable map draws in map units), maxRank:
  // the smallest rivers to show.
  function strokeRivers(ctx, paths, unit = 1, maxRank = 8) {
    ctx.save();
    ctx.lineCap = "round"; ctx.lineJoin = "round"; ctx.strokeStyle = "rgba(37, 112, 186, 0.85)";
    for (const { rank, path } of paths) {
      if (rank > maxRank) continue;
      ctx.lineWidth = Math.max(0.55, 2.3 - rank * 0.22) / unit;
      ctx.stroke(path);
    }
    ctx.restore();
  }

  window.Basemap = { drawMercator, render, merc, rivers, riverPaths, strokeRivers,
    credit: "Relief: NASA Blue Marble (via FreeTiler); rivers: Natural Earth" };
})();

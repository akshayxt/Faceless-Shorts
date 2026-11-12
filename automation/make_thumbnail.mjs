import fs from 'node:fs';
import path from 'node:path';
import { spawn } from 'node:child_process';
import http from 'node:http';
import { sendNodeTelegram } from './telegram_node.mjs';

// Usage: node make_thumbnail.mjs <outPngOrJpg> "<THUMB TEXT>" "<CATEGORY>" "[SUBTITLE_BADGE]"
const [, , outFile, thumbText = 'WHY IT ITCHES!', category = 'body-science', badge = 'BABYBEATS RHYMO'] = process.argv;
if (!outFile) {
  console.error('Usage: node make_thumbnail.mjs <outFile> "<THUMB TEXT>" "<category>" "[badge]"');
  process.exit(1);
}

function findChrome() {
  const candidates = [
    process.env.CHROME_PATH,
    'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
    'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
    'C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe'
  ].filter(Boolean);
  for (const p of candidates) {
    if (fs.existsSync(p)) return p;
  }
  throw new Error('No Chrome/Edge executable found. Set CHROME_PATH.');
}

const palettes = {
  'body-science': { bg1: '#1E1B4B', bg2: '#312E81', ray: '#4338CA', accent: '#FFD43B', alert: '#EF4444', prop: 'microscope' },
  'animal-vs':    { bg1: '#064E3B', bg2: '#047857', ray: '#059669', accent: '#FDE047', alert: '#F97316', prop: 'creature' },
  'myth-bust':    { bg1: '#7F1D1D', bg2: '#991B1B', ray: '#B91C1C', accent: '#FEF08A', alert: '#38BDF8', prop: 'mythx' },
  'space-nature': { bg1: '#0F172A', bg2: '#1D4ED8', ray: '#2563EB', accent: '#FDE047', alert: '#22D3EE', prop: 'planet' },
  'moral-story':  { bg1: '#4C1D95', bg2: '#6D28D9', ray: '#7C3AED', accent: '#FDE047', alert: '#34D399', prop: 'star' }
};
const pal = palettes[category] || palettes['body-science'];

const html = `<!doctype html><html><body style="margin:0;overflow:hidden;background:#000">
<canvas id="c" width="1280" height="720"></canvas>
<script>
const c = document.getElementById('c'), ctx = c.getContext('2d');
const W = 1280, H = 720, TAU = Math.PI * 2;
const pal = ${JSON.stringify(pal)};
const text = ${JSON.stringify(thumbText)};
const badge = ${JSON.stringify(badge)};
const category = ${JSON.stringify(category)};

// Comic sunburst backdrop
const grad = ctx.createRadialGradient(360, 360, 60, 560, 360, 900);
grad.addColorStop(0, pal.bg2);
grad.addColorStop(1, pal.bg1);
ctx.fillStyle = grad;
ctx.fillRect(0, 0, W, H);

ctx.save();
ctx.translate(340, 380);
ctx.fillStyle = pal.ray;
ctx.globalAlpha = 0.35;
for (let i = 0; i < 18; i++) {
  ctx.beginPath();
  ctx.moveTo(0, 0);
  const a1 = (i / 18) * TAU, a2 = a1 + 0.14;
  ctx.lineTo(Math.cos(a1) * 1400, Math.sin(a1) * 1400);
  ctx.lineTo(Math.cos(a2) * 1400, Math.sin(a2) * 1400);
  ctx.closePath();
  ctx.fill();
}
ctx.restore();

function circle(x, y, r, fill, stroke = null, lw = 8) {
  ctx.beginPath(); ctx.arc(x, y, r, 0, TAU);
  if (fill) { ctx.fillStyle = fill; ctx.fill(); }
  if (stroke) { ctx.strokeStyle = stroke; ctx.lineWidth = lw; ctx.stroke(); }
}

// Left visual focal hero (Cartoon Mascot + Topic Prop)
ctx.save();
ctx.translate(335, 395);

// Glowing halo behind focal visual
circle(0, -10, 235, 'rgba(255,255,255,0.12)');
circle(0, -10, 190, 'rgba(255,212,59,0.22)');

if (category === 'space-nature') {
  // Bright ringed cartoon planet + shocked mascot face inside sunbeam
  ctx.save(); ctx.rotate(-0.25);
  ctx.beginPath(); ctx.ellipse(0, 15, 225, 58, 0, 0, TAU);
  ctx.strokeStyle = pal.accent; ctx.lineWidth = 22; ctx.stroke();
  ctx.restore();
  circle(0, 0, 140, '#38BDF8', '#18181B', 12);
  circle(-45, -35, 32, '#22C55E');
  circle(48, 30, 42, '#22C55E');
  circle(-38, -20, 22, '#FFFFFF', '#18181B', 5);
  circle(38, -20, 22, '#FFFFFF', '#18181B', 5);
  circle(-34, -20, 10, '#18181B'); circle(42, -20, 10, '#18181B');
  ctx.beginPath(); ctx.arc(0, 40, 32, 0, Math.PI); ctx.fillStyle = '#EF4444'; ctx.fill();
} else if (category === 'animal-vs') {
  // Big cartoon creature + lightning Bolt
  circle(0, 20, 150, '#F97316', '#18181B', 12);
  circle(-48, -25, 34, '#FFFFFF', '#18181B', 7);
  circle(48, -25, 34, '#FFFFFF', '#18181B', 7);
  circle(-40, -25, 16, '#18181B'); circle(40, -25, 16, '#18181B');
  ctx.beginPath(); ctx.ellipse(0, 45, 38, 28, 0, 0, TAU); ctx.fillStyle = '#18181B'; ctx.fill();
  ctx.fillStyle = '#F43F5E'; ctx.beginPath(); ctx.arc(0, 56, 20, 0, TAU); ctx.fill();
  // Lightning arrow
  ctx.fillStyle = pal.accent; ctx.strokeStyle = '#18181B'; ctx.lineWidth = 8;
  ctx.beginPath(); ctx.moveTo(145, -180); ctx.lineTo(80, -40); ctx.lineTo(135, -40); ctx.lineTo(75, 110); ctx.lineTo(195, -70); ctx.lineTo(135, -70); ctx.closePath();
  ctx.fill(); ctx.stroke();
} else if (category === 'myth-bust') {
  // Giant Shocked Kid + Giant Red X Stamp
  circle(-30, 20, 145, '#FDBA74', '#18181B', 12);
  circle(-75, -15, 32, '#FFFFFF', '#18181B', 7);
  circle(15, -15, 32, '#FFFFFF', '#18181B', 7);
  circle(-70, -15, 14, '#18181B'); circle(20, -15, 14, '#18181B');
  ctx.beginPath(); ctx.ellipse(-30, 62, 34, 42, 0, 0, TAU); ctx.fillStyle = '#D62839'; ctx.fill();
  ctx.lineWidth = 24; ctx.strokeStyle = '#EF4444'; ctx.lineCap = 'round';
  ctx.beginPath(); ctx.moveTo(75, -155); ctx.lineTo(205, -25); ctx.moveTo(205, -155); ctx.lineTo(75, -25); ctx.stroke();
} else {
  // Body Science / Story Hero: Cartoon Leo + Spyglass Magnifier over Bug / Night Brain!
  // Shoulders & teal/yellow shirt
  ctx.fillStyle = '#2A9D8F'; ctx.strokeStyle = '#18181B'; ctx.lineWidth = 10;
  ctx.beginPath(); ctx.roundRect(-145, 130, 230, 180, 48); ctx.fill(); ctx.stroke();
  ctx.fillStyle = '#FFD43B'; ctx.fillRect(-140, 185, 220, 34);

  // Friendly round kid head + spiky tufts
  circle(-30, 10, 135, '#FDBA74', '#18181B', 11);
  ctx.fillStyle = '#18181B';
  ctx.beginPath(); ctx.arc(-30, -35, 130, Math.PI + 0.35, -0.35); ctx.fill();
  circle(-70, -112, 32, '#18181B'); circle(-12, -124, 38, '#18181B'); circle(42, -104, 28, '#18181B');
  circle(-80, -8, 28, '#FFFFFF', '#18181B', 6);
  circle(18, -8, 28, '#FFFFFF', '#18181B', 6);
  circle(-74, -8, 12, '#18181B'); circle(24, -8, 12, '#18181B');
  circle(-70, -12, 4, '#FFFFFF'); circle(28, -12, 4, '#FFFFFF');
  ctx.beginPath(); ctx.ellipse(-30, 62, 26, 34, 0, 0, TAU); ctx.fillStyle = '#D62839'; ctx.fill();

  // Giant Magnifying Glass + handle angled down-left away from thumbnail text
  ctx.save(); ctx.translate(145, -80);
  ctx.save(); ctx.rotate(2.25);
  ctx.fillStyle = '#18181B'; ctx.beginPath(); ctx.roundRect(96, -18, 125, 36, 16); ctx.fill();
  ctx.restore();
  circle(0, 0, 114, '#18181B');
  circle(0, 0, 100, '#E0F2FE');
  if (text.includes('DREAM') || text.includes('NIGHT') || text.includes('SLEEP')) {
    // Glowing Brain & Dream Stars inside lens
    circle(-18, -4, 42, '#F472B6', '#18181B', 6);
    circle(20, 4, 40, '#F472B6', '#18181B', 6);
    circle(-46, -42, 11, '#FFD43B'); circle(48, -36, 14, '#FFD43B');
  } else {
    // Stylized Cartoon Mosquito inside Magnifier
    ctx.strokeStyle = '#18181B'; ctx.lineWidth = 6; ctx.lineCap = 'round';
    ctx.beginPath(); ctx.moveTo(-25, 10); ctx.lineTo(-48, 52); ctx.moveTo(5, 12); ctx.lineTo(-6, 56); ctx.moveTo(26, 8); ctx.lineTo(48, 45); ctx.stroke();
    ctx.save(); ctx.globalAlpha = 0.7;
    ctx.fillStyle = '#38BDF8'; ctx.beginPath(); ctx.ellipse(-18, -36, 36, 14, -0.45, 0, TAU); ctx.fill();
    ctx.restore();
    circle(-18, 6, 26, '#3F3F46', '#18181B', 5);
    circle(22, -6, 18, '#18181B');
    circle(28, -10, 7, '#FFFFFF'); circle(30, -10, 3, '#EF4444');
    ctx.strokeStyle = '#EF4444'; ctx.lineWidth = 7;
    ctx.beginPath(); ctx.moveTo(38, -2); ctx.lineTo(84, 18); ctx.stroke();
  }
  ctx.restore();
}
ctx.restore();

// Top-left brand pill
ctx.save();
ctx.beginPath(); ctx.roundRect(42, 36, 390, 64, 32);
ctx.fillStyle = '#18181B'; ctx.fill();
ctx.strokeStyle = '#FFD43B'; ctx.lineWidth = 5; ctx.stroke();
ctx.font = '900 30px "Arial Black", Impact, sans-serif';
ctx.fillStyle = '#FFD43B'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
ctx.fillText(badge.toUpperCase(), 237, 69);
ctx.restore();

// Right Side: Massive Mobile-Readable Comic Words (max 2-3 lines)
const words = text.trim().split(/\\s+/);
let lines = [];
if (words.length <= 2) {
  lines = words;
} else if (words.length === 3) {
  lines = [words[0], words.slice(1).join(' ')];
} else {
  const mid = Math.ceil(words.length / 2);
  lines = [words.slice(0, mid).join(' '), words.slice(mid).join(' ')];
}

ctx.save();
ctx.textAlign = 'center';
ctx.textBaseline = 'middle';
const rx = 905, startY = lines.length === 1 ? 370 : 285, stepY = 175;
lines.forEach((ln, idx) => {
  const y = startY + idx * stepY;
  let fs = 138;
  do {
    ctx.font = '900 ' + fs + 'px "Arial Black", Impact, sans-serif';
    fs -= 6;
  } while (ctx.measureText(ln).width > 640 && fs > 64);
  // Comic hard shadow
  ctx.fillStyle = '#09090B';
  ctx.fillText(ln, rx + 10, y + 12, 650);
  // Thick black border
  ctx.lineJoin = 'round';
  ctx.strokeStyle = '#18181B';
  ctx.lineWidth = Math.max(14, Math.round(fs * 0.18));
  ctx.strokeText(ln, rx, y, 650);
  // High contrast alternating yellow/white fill
  ctx.fillStyle = idx % 2 === 0 ? pal.accent : '#FFFFFF';
  ctx.fillText(ln, rx, y, 650);
});
ctx.restore();

// Bold comic frame border
ctx.strokeStyle = pal.accent;
ctx.lineWidth = 14;
ctx.strokeRect(7, 7, W - 14, H - 14);
window.__READY = true;
</script></body></html>`;

const chromePath = findChrome();
const server = http.createServer((req, res) => {
  res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
  res.end(html);
});

await new Promise((r) => server.listen(0, '127.0.0.1', r));
const port = server.address().port;

const userData = fs.mkdtempSync(path.join(process.env.TEMP || '.', 'thumb-chrome-'));
const proc = spawn(chromePath, [
  '--headless=new',
  '--disable-gpu',
  '--no-sandbox',
  '--remote-debugging-port=0',
  `--user-data-dir=${userData}`,
  '--window-size=1280,720',
  `http://127.0.0.1:${port}/`
], { stdio: ['ignore', 'ignore', 'pipe'] });

let wsUrl = null;
await new Promise((resolve, reject) => {
  const tm = setTimeout(() => reject(new Error('Chrome DevTools timeout')), 15000);
  proc.stderr.on('data', (d) => {
    const m = d.toString().match(/DevTools listening on (ws:\/\/[^\s]+)/);
    if (m) { wsUrl = m[1]; clearTimeout(tm); resolve(); }
  });
});

// Connect via WebSocket built into Node 22+
const targets = await (await fetch(wsUrl.replace('ws://', 'http://').replace(/\/devtools\/browser.*/, '/json/list'))).json();
const pageTarget = targets.find((t) => t.type === 'page');
const ws = new WebSocket(pageTarget.webSocketDebuggerUrl);
await new Promise((r) => ws.addEventListener('open', r, { once: true }));

let msgId = 0;
const call = (method, params = {}) => new Promise((resolve, reject) => {
  const id = ++msgId;
  const onMsg = (ev) => {
    const data = JSON.parse(ev.data);
    if (data.id === id) {
      ws.removeEventListener('message', onMsg);
      if (data.error) reject(new Error(data.error.message));
      else resolve(data.result);
    }
  };
  ws.addEventListener('message', onMsg);
  ws.send(JSON.stringify({ id, method, params }));
});

await call('Emulation.setDeviceMetricsOverride', { width: 1280, height: 720, deviceScaleFactor: 1, mobile: false });
for (let i = 0; i < 40; i++) {
  const res = await call('Runtime.evaluate', { expression: 'Boolean(window.__READY)', returnByValue: true });
  if (res.result?.value) break;
  await new Promise((r) => setTimeout(r, 100));
}
const ext = path.extname(outFile).toLowerCase();
const format = ext === '.jpg' || ext === '.jpeg' ? 'jpeg' : 'png';
const shot = await call('Page.captureScreenshot', { format, quality: format === 'jpeg' ? 92 : undefined });
fs.mkdirSync(path.dirname(path.resolve(outFile)), { recursive: true });
fs.writeFileSync(outFile, Buffer.from(shot.data, 'base64'));
console.log(`Thumbnail written: ${outFile} (1280x720 ${format})`);
await sendNodeTelegram('THUMBNAIL', `Thumbnail written: ${outFile} (1280x720 ${format})`);

ws.close();
try { proc.kill('SIGKILL'); } catch {}
try { server.closeAllConnections?.(); server.close(); } catch {}
setTimeout(() => { try { fs.rmSync(userData, { recursive: true, force: true }); } catch {} process.exit(0); }, 200);

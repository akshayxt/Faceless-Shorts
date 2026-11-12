import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import { spawn } from 'node:child_process';
import { sendNodeTelegram } from './telegram_node.mjs';

// Usage:
//   node longform_renderer.mjs sheet <projectDir> <outJpg> [stepSec=15] [cols=6]
//   node longform_renderer.mjs render <projectDir> <outMp4> [fps=24]
const [, , mode, projectDir, outPath, arg4, arg5] = process.argv;
if (!mode || !projectDir || !outPath) {
  console.error('Usage: node longform_renderer.mjs <sheet|render> <projectDir> <outPath> [arg4] [arg5]');
  process.exit(1);
}

const P = path.resolve(projectDir);
const scriptData = JSON.parse(fs.readFileSync(path.join(P, 'script.json'), 'utf-8'));
const linesData = JSON.parse(fs.readFileSync(path.join(P, 'data/lines.json'), 'utf-8'));
const dur = linesData.duration;
const mixWav = path.join(P, 'data/mix.wav');

function findChrome() {
  const candidates = [
    process.env.CHROME_PATH,
    'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
    'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
    'C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe'
  ].filter(Boolean);
  for (const c of candidates) if (fs.existsSync(c)) return c;
  throw new Error('Chrome/Edge not found');
}

const renderPageHtml = `<!doctype html>
<html>
<body style="margin:0;overflow:hidden;background:#0F172A">
<canvas id="c" width="1920" height="1080"></canvas>
<script>
const SCRIPT = ${JSON.stringify(scriptData)};
const LINES = ${JSON.stringify(linesData.lines)};
const DUR = ${dur};
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
const W = 1920, H = 1080, TAU = Math.PI * 2;

const clamp = (v, a=0, b=1) => Math.max(a, Math.min(b, v));
const lerp = (a, b, t) => a + (b - a) * t;
const eob = (t) => { const c=1.70158, c3=c+1; return 1 + c3*Math.pow(t-1,3) + c*Math.pow(t-1,2); };

function rr(x,y,w,h,r){ ctx.beginPath(); ctx.roundRect(x,y,w,h,r); }
function circle(x,y,r,fill,stroke,lw=6){
  ctx.beginPath(); ctx.arc(x,y,r,0,TAU);
  if(fill){ ctx.fillStyle=fill; ctx.fill(); }
  if(stroke){ ctx.strokeStyle=stroke; ctx.lineWidth=lw; ctx.stroke(); }
}

const THEMES = {
  bedroom:   { sky1:'#0F172A', sky2:'#1E1B4B', floor:'#312E81', accent:'#FFD43B', prop:'moon' },
  brainhq:   { sky1:'#1E1B4B', sky2:'#3B0764', floor:'#4C1D95', accent:'#F472B6', prop:'brain' },
  sleepwave: { sky1:'#064E3B', sky2:'#0F766E', floor:'#115E59', accent:'#34D399', prop:'stages' },
  cleanup:   { sky1:'#0C4A6E', sky2:'#0369A1', floor:'#075985', accent:'#38BDF8', prop:'broom' },
  theater:   { sky1:'#450A0A', sky2:'#7F1D1D', floor:'#991B1B', accent:'#FDE047', prop:'projector' },
  quiz:      { sky1:'#312E81', sky2:'#4338CA', floor:'#3730A3', accent:'#22D3EE', prop:'quiz' },
  takeaway:  { sky1:'#14532D', sky2:'#166534', floor:'#15803D', accent:'#FFD43B', prop:'sun' }
};

function drawMascot(x, y, s, t, mood='happy') {
  ctx.save(); ctx.translate(x, y); ctx.scale(s, s);
  // bounce animation synced to narration beats
  const bob = Math.sin(t * 4.5) * 8;
  ctx.translate(0, bob);

  // torso
  rr(-68, 20, 136, 160, 36); ctx.fillStyle='#2A9D8F'; ctx.fill(); ctx.lineWidth=8; ctx.strokeStyle='#18181B'; ctx.stroke();
  ctx.fillStyle='#FFD43B'; ctx.fillRect(-64, 78, 128, 28);

  // pointing arm
  ctx.strokeStyle='#FDBA74'; ctx.lineWidth=26; ctx.lineCap='round';
  ctx.beginPath(); ctx.moveTo(64, 52); ctx.lineTo(128, 12 + Math.sin(t*6)*20); ctx.stroke();

  // head
  circle(0, -68, 86, '#FDBA74', '#18181B', 8);
  ctx.fillStyle='#18181B'; ctx.beginPath(); ctx.arc(0, -96, 82, Math.PI+0.3, -0.3); ctx.fill();
  circle(-26, -152, 22, '#18181B'); circle(12, -160, 26, '#18181B'); circle(44, -142, 18, '#18181B');

  // eyes
  if (mood === 'sleep') {
    ctx.strokeStyle='#18181B'; ctx.lineWidth=6;
    ctx.beginPath(); ctx.arc(-28,-70,14,0,Math.PI); ctx.stroke();
    ctx.beginPath(); ctx.arc(28,-70,14,0,Math.PI); ctx.stroke();
  } else {
    circle(-28, -72, 17, '#FFFFFF', '#18181B', 5);
    circle(28, -72, 17, '#FFFFFF', '#18181B', 5);
    const ex = Math.sin(t*1.8)*3;
    circle(-28+ex, -72, 8, '#18181B'); circle(28+ex, -72, 8, '#18181B');
  }
  // mouth
  if (mood === 'shock') {
    circle(0, -32, 18, '#D62839');
  } else {
    ctx.beginPath(); ctx.arc(0, -44, 24, 0.15, Math.PI-0.15);
    ctx.strokeStyle='#18181B'; ctx.lineWidth=6; ctx.stroke();
  }
  ctx.restore();
}

function drawSceneProp(prop, cx, cy, t, lt) {
  ctx.save(); ctx.translate(cx, cy);
  if (prop === 'moon') {
    circle(0, 0, 145, '#FEF08A', '#18181B', 10);
    circle(42, -26, 118, '#1E1B4B');
    for (let i=0;i<8;i++){
      const sx = Math.cos(i*1.9)*260, sy = Math.sin(i*2.3)*180;
      const sc = 0.6 + 0.4*Math.sin(t*4+i);
      circle(sx, sy, 12*sc, '#FFD43B');
    }
    ctx.font = '900 58px "Arial Black", sans-serif'; ctx.fillStyle='#38BDF8';
    ctx.fillText('Zzz...', 110 + Math.sin(t*3)*16, -120 - ((t*35)%90));
  } else if (prop === 'brain') {
    const pulse = 1 + Math.sin(t*6)*0.05;
    ctx.scale(pulse, pulse);
    circle(-58, -10, 115, '#F472B6', '#18181B', 10);
    circle(58, -10, 115, '#F472B6', '#18181B', 10);
    circle(-42, 48, 86, '#F472B6', '#18181B', 10);
    circle(42, 48, 86, '#F472B6', '#18181B', 10);
    // glowing neuron sparks
    for (let i=0;i<6;i++){
      const a = t*2.5 + i*1.05;
      circle(Math.cos(a)*95, Math.sin(a)*65, 16, '#FFD43B');
    }
  } else if (prop === 'stages') {
    const bars = ['STAGE 1: DOZE', 'STAGE 2: LIGHT', 'STAGE 3: DEEP', 'REM: DREAM MOVIE!'];
    bars.forEach((b, i) => {
      const y = -150 + i*95;
      const active = Math.floor((t*0.5) % 4) === i || i === 3;
      rr(-260, y, 520, 70, 20);
      ctx.fillStyle = active ? '#FFD43B' : 'rgba(255,255,255,0.16)';
      ctx.fill(); ctx.lineWidth=6; ctx.strokeStyle='#18181B'; ctx.stroke();
      ctx.font='900 32px "Arial Black", sans-serif';
      ctx.fillStyle = active ? '#18181B' : '#FFFFFF';
      ctx.textAlign='center'; ctx.textBaseline='middle';
      ctx.fillText(b, 0, y+36);
    });
  } else if (prop === 'broom') {
    // Filing cabinets + floating memory cards
    for (let i=0;i<3;i++){
      const ox = -180 + i*180;
      const fly = Math.sin(t*3 + i)*24;
      rr(ox-65, -80+fly, 130, 165, 18);
      ctx.fillStyle = i===1 ? '#FFD43B' : '#38BDF8'; ctx.fill();
      ctx.lineWidth=7; ctx.strokeStyle='#18181B'; ctx.stroke();
      ctx.font='900 26px "Arial Black", sans-serif'; ctx.fillStyle='#18181B'; ctx.textAlign='center';
      ctx.fillText(['MATH','PLAY','FUN'][i], ox, 8+fly);
    }
  } else if (prop === 'projector') {
    // Dream cinema projector beam
    ctx.fillStyle='rgba(254,240,138,0.28)';
    ctx.beginPath(); ctx.moveTo(-180,0); ctx.lineTo(290,-180); ctx.lineTo(290,180); ctx.closePath(); ctx.fill();
    rr(-270,-70,130,110,16); ctx.fillStyle='#18181B'; ctx.fill();
    circle(-235,-95,38,'#FFD43B','#18181B',6); circle(-170,-95,32,'#FFD43B','#18181B',6);
    // Flying pizza / dinosaur / bicycle icon inside dream cloud!
    const bob = Math.sin(t*4)*22;
    circle(150, bob, 115, '#FFFFFF', '#18181B', 8);
    ctx.font='900 38px "Arial Black", sans-serif'; ctx.fillStyle='#D62839'; ctx.textAlign='center';
    ctx.fillText('FLYING', 150, bob-16, 195);
    ctx.fillText('BICYCLE!', 150, bob+32, 195);
  } else if (prop === 'quiz') {
    rr(-250, -145, 500, 290, 32); ctx.fillStyle='#0F172A'; ctx.fill();
    ctx.lineWidth=10; ctx.strokeStyle='#22D3EE'; ctx.stroke();
    ctx.font='900 58px "Arial Black", sans-serif'; ctx.fillStyle='#FFD43B'; ctx.textAlign='center';
    ctx.fillText('BRAIN QUIZ!', 0, -45, 440);
    ctx.font='900 34px "Arial Black", sans-serif'; ctx.fillStyle='#FFFFFF';
    ctx.fillText('95% DREAMS FADE FAST!', 0, 48, 440);
  } else {
    // Cheerful sun + energy battery 100%
    circle(-110, -20, 110, '#FFD43B', '#18181B', 8);
    rr(60, -110, 150, 210, 24); ctx.fillStyle='#FFFFFF'; ctx.fill(); ctx.lineWidth=8; ctx.strokeStyle='#18181B'; ctx.stroke();
    rr(78, -90, 114, 170, 14); ctx.fillStyle='#22C55E'; ctx.fill();
    ctx.font='900 38px "Arial Black", sans-serif'; ctx.fillStyle='#FFFFFF'; ctx.textAlign='center';
    ctx.fillText('100%', 135, 10);
  }
  ctx.restore();
}

window.renderAt = function(t) {
  let idx = 0;
  for (let i = 0; i < LINES.length; i++) {
    if (t >= LINES[i].start - 0.1) idx = i;
  }
  const ln = LINES[idx] || LINES[0];
  const srcLine = SCRIPT.lines[idx] || {};
  const sceneKey = srcLine.scene || 'bedroom';
  const chapter = srcLine.chapter || 'Chapter 1';
  const factCard = srcLine.card || '';
  const mood = srcLine.mood || 'happy';
  const th = THEMES[sceneKey] || THEMES.bedroom;
  const lt = Math.max(0, t - ln.start);

  // Gradient sky
  const g = ctx.createLinearGradient(0, 0, 0, H);
  g.addColorStop(0, th.sky1);
  g.addColorStop(1, th.sky2);
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, W, H);

  // Subtle geometric grid
  ctx.strokeStyle = 'rgba(255,255,255,0.06)';
  ctx.lineWidth = 2;
  for (let gx = 0; gx < W; gx += 120) { ctx.beginPath(); ctx.moveTo(gx,0); ctx.lineTo(gx,H); ctx.stroke(); }
  for (let gy = 0; gy < H; gy += 120) { ctx.beginPath(); ctx.moveTo(0,gy); ctx.lineTo(W,gy); ctx.stroke(); }

  // Floor stage
  ctx.fillStyle = th.floor;
  ctx.fillRect(0, 740, W, 340);

  // Top Header Bar (Chapter + BabyBeats Rhymo branding)
  rr(54, 42, 420, 62, 31); ctx.fillStyle='#18181B'; ctx.fill();
  ctx.strokeStyle='#FFD43B'; ctx.lineWidth=4; ctx.stroke();
  ctx.font='900 28px "Arial Black", sans-serif'; ctx.fillStyle='#FFD43B';
  ctx.textAlign='center'; ctx.textBaseline='middle';
  ctx.fillText('BABYBEATS RHYMO', 264, 74);

  rr(500, 42, 620, 62, 31); ctx.fillStyle='rgba(0,0,0,0.45)'; ctx.fill();
  ctx.font='700 28px Arial, sans-serif'; ctx.fillStyle='#FFFFFF';
  ctx.fillText(chapter.toUpperCase(), 810, 74, 580);

  // Timeline Progress Bar at Top Right
  rr(1480, 56, 380, 26, 13); ctx.fillStyle='rgba(255,255,255,0.2)'; ctx.fill();
  rr(1480, 56, Math.max(26, 380 * clamp(t / DUR)), 26, 13); ctx.fillStyle=th.accent; ctx.fill();

  // Left Mascot Host & Right Animated Science Prop
  drawMascot(360, 595, 1.55, t, mood);
  drawSceneProp(th.prop, 1290, 440, t, lt);

  // Floating key concept card when present
  if (factCard) {
    const pop = eob(clamp(lt / 0.35));
    ctx.save();
    ctx.translate(960, 200);
    ctx.scale(pop, pop);
    rr(-360, -44, 720, 88, 22);
    ctx.fillStyle = th.accent; ctx.fill();
    ctx.lineWidth=6; ctx.strokeStyle='#18181B'; ctx.stroke();
    ctx.font='900 38px "Arial Black", sans-serif'; ctx.fillStyle='#18181B';
    ctx.textAlign='center'; ctx.textBaseline='middle';
    ctx.fillText(factCard, 0, 2, 660);
    ctx.restore();
  }

  // Bottom 16:9 Cartoon Subtitle Box (high legibility!)
  if (t >= ln.start - 0.05 && t <= ln.end + 0.15) {
    rr(140, 865, 1640, 148, 28);
    ctx.fillStyle = 'rgba(15, 23, 42, 0.88)'; ctx.fill();
    ctx.lineWidth = 5; ctx.strokeStyle = th.accent; ctx.stroke();
    ctx.font = '900 46px "Arial Black", Arial, sans-serif';
    ctx.fillStyle = '#FFFFFF';
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    const txt = (ln.text || '').replace(/\\*/g, '');
    ctx.fillText(txt, 960, 939, 1560);
  }
  return true;
};
window.__READY = true;
</script>
</body>
</html>`;

const chrome = findChrome();
const server = http.createServer((req, res) => {
  res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
  res.end(renderPageHtml);
});
await new Promise((r) => server.listen(0, '127.0.0.1', r));
const port = server.address().port;

const userData = fs.mkdtempSync(path.join(process.env.TEMP || '.', 'long-chrome-'));
const proc = spawn(chrome, [
  '--headless=new', '--disable-gpu', '--no-sandbox', '--remote-debugging-port=0',
  `--user-data-dir=${userData}`, '--window-size=1920,1080', `http://127.0.0.1:${port}/`
], { stdio: ['ignore', 'ignore', 'pipe'] });

let wsUrl = null;
await new Promise((resolve, reject) => {
  const tm = setTimeout(() => reject(new Error('Chrome timeout')), 15000);
  proc.stderr.on('data', (d) => {
    const m = d.toString().match(/DevTools listening on (ws:\/\/[^\s]+)/);
    if (m) { wsUrl = m[1]; clearTimeout(tm); resolve(); }
  });
});

const targets = await (await fetch(wsUrl.replace('ws://', 'http://').replace(/\/devtools\/browser.*/, '/json/list'))).json();
const pageTarget = targets.find((t) => t.type === 'page');
const ws = new WebSocket(pageTarget.webSocketDebuggerUrl);
await new Promise((r) => ws.addEventListener('open', r, { once: true }));

let idSeq = 0;
const call = (method, params = {}) => new Promise((resolve, reject) => {
  const id = ++idSeq;
  const h = (ev) => {
    const msg = JSON.parse(ev.data);
    if (msg.id === id) {
      ws.removeEventListener('message', h);
      if (msg.error) reject(new Error(msg.error.message));
      else resolve(msg.result);
    }
  };
  ws.addEventListener('message', h);
  ws.send(JSON.stringify({ id, method, params }));
});

await call('Emulation.setDeviceMetricsOverride', { width: 1920, height: 1080, deviceScaleFactor: 1, mobile: false });
for (let i = 0; i < 40; i++) {
  const r = await call('Runtime.evaluate', { expression: 'Boolean(window.__READY)', returnByValue: true });
  if (r.result?.value) break;
  await new Promise((r) => setTimeout(r, 50));
}

fs.mkdirSync(path.dirname(path.resolve(outPath)), { recursive: true });

if (mode === 'sheet') {
  const step = Number(arg4 || 20);
  const cols = Number(arg5 || 5);
  const tmpDir = fs.mkdtempSync(path.join(process.env.TEMP || '.', 'long-sheet-'));
  let n = 0;
  for (let t = 0.5; t < dur; t += step) {
    await call('Runtime.evaluate', { expression: `window.renderAt(${t.toFixed(3)})`, returnByValue: true });
    const shot = await call('Page.captureScreenshot', { format: 'jpeg', quality: 85 });
    fs.writeFileSync(path.join(tmpDir, `f_${String(n++).padStart(4, '0')}.jpg`), Buffer.from(shot.data, 'base64'));
  }
  const ff = spawn('ffmpeg', [
    '-y', '-i', path.join(tmpDir, 'f_%04d.jpg'),
    '-vf', `tile=${cols}x${Math.ceil(n / cols)},scale=1920:-1`,
    '-frames:v', '1', outPath
  ], { stdio: 'inherit' });
  await new Promise((res, rej) => ff.on('close', (c) => c === 0 ? res() : rej(new Error('ffmpeg tile failed'))));
  try { fs.rmSync(tmpDir, { recursive: true, force: true }); } catch {}
  console.log(`Longform QA sheet written (${n} frames, step ${step}s): ${outPath}`);
} else if (mode === 'render') {
  const fps = Number(arg4 || 24);
  const total = Math.ceil(dur * fps);
  const args = [
    '-y', '-f', 'image2pipe', '-vcodec', 'mjpeg', '-r', String(fps), '-i', '-',
    ...(fs.existsSync(mixWav) ? ['-i', mixWav, '-c:a', 'aac', '-b:a', '192k'] : []),
    '-c:v', 'libx264', '-preset', 'fast', '-crf', '21', '-pix_fmt', 'yuv420p', '-shortest',
    outPath
  ];
  const ff = spawn('ffmpeg', args, { stdio: ['pipe', 'ignore', 'pipe'] });
  let errOut = '';
  ff.stderr.on('data', (d) => { errOut += d.toString(); });
  for (let f = 0; f < total; f++) {
    const t = f / fps;
    await call('Runtime.evaluate', { expression: `window.renderAt(${t.toFixed(3)})`, returnByValue: true });
    const shot = await call('Page.captureScreenshot', { format: 'jpeg', quality: 84 });
    const buf = Buffer.from(shot.data, 'base64');
    if (!ff.stdin.write(buf)) {
      await new Promise((r) => ff.stdin.once('drain', r));
    }
    if (f % 300 === 0) console.log(`  longform render: ${f}/${total} frames (${Math.round(f * 100 / total)}%)`);
  }
  ff.stdin.end();
  await new Promise((res, rej) => ff.on('close', (c) => c === 0 ? res() : rej(new Error(`ffmpeg exited ${c}: ${errOut.slice(-400)}`))));
  console.log(`Longform MP4 rendered: ${outPath} (${dur.toFixed(2)} s @ ${fps} fps, 1920x1080)`);
}

await sendNodeTelegram('LONGFORM_RENDERER', `Longform ${mode} complete -> ${outPath} (dur=${dur.toFixed(2)}s)`);
ws.close();
try { proc.kill('SIGKILL'); } catch {}
try { server.closeAllConnections?.(); server.close(); } catch {}
setTimeout(() => { try { fs.rmSync(userData, { recursive: true, force: true }); } catch {} process.exit(0); }, 250);

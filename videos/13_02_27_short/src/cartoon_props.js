import { ctx, C, TAU, clamp, lerp, rr, circle, ell, line, bigText } from './core/lib.js';

export function mosquito(x, y, s = 1, { wing = 0, bite = 0, flip = 1, sweat = false } = {}) {
  ctx.save(); ctx.translate(x, y); ctx.scale(s * flip, s);
  const wy = Math.sin(wing * 28) * 18;
  ctx.save(); ctx.globalAlpha = 0.72;
  ell(-18, -34 + wy * 0.4, 44, 16, C.cyan || '#4FD1E8', -0.45 + wy * 0.015);
  ell(-6, -42 - wy * 0.4, 38, 13, '#A5F3FC', -0.25 - wy * 0.015);
  ctx.restore();
  [[-12, 10, -45, 55, -70, 75], [10, 12, 12, 62, -15, 84], [32, 10, 62, 50, 88, 66]].forEach(([x1, y1, x2, y2, x3, y3]) => line([[x1, y1], [x2, y2], [x3, y3]], C.ink, 5));
  ctx.save(); ctx.translate(-38, 8); ctx.rotate(-0.2);
  ell(0, 0, 42, 20, '#3F3F46'); ctx.fillStyle = '#E4E4E7'; [-18, -2, 14].forEach((sx) => ctx.fillRect(sx, -14, 7, 28));
  ctx.restore();
  circle(8, -2, 24, '#27272A'); circle(38, -8, 18, '#18181B');
  circle(44, -14, 10, C.white); circle(47, -14, 5, '#D62839'); circle(49, -16, 2, C.white);
  const poke = bite * 24;
  ctx.strokeStyle = C.ink; ctx.lineWidth = 4; ctx.beginPath(); ctx.moveTo(52, -4); ctx.lineTo(106 + poke, 16 + bite * 18); ctx.stroke();
  if (bite > 0.25) circle(108 + poke, 17 + bite * 18, 6, C.yellow);
  if (sweat) ell(28, -36, 5, 9, '#4FD1E8', 0.2);
  ctx.restore();
}

export function skinScene(yFloor = 980, bump = 0, acidGlow = 0) {
  ctx.save();
  ctx.fillStyle = '#FDBA74'; ctx.beginPath(); ctx.moveTo(0, yFloor);
  for (let x = 0; x <= 1080; x += 20) {
    const dist = (x - 540) / 140;
    ctx.lineTo(x, yFloor - Math.exp(-dist * dist) * bump * 95);
  }
  ctx.lineTo(1080, 1250); ctx.lineTo(0, 1250); ctx.closePath(); ctx.fill();
  ctx.fillStyle = '#FB923C'; ctx.beginPath(); ctx.moveTo(0, yFloor + 58);
  for (let x = 0; x <= 1080; x += 30) {
    const dist = (x - 540) / 170;
    ctx.lineTo(x, yFloor + 58 - Math.exp(-dist * dist) * bump * 55);
  }
  ctx.lineTo(1080, 1250); ctx.lineTo(0, 1250); ctx.closePath(); ctx.fill();
  line([[0, yFloor + 150], [340, yFloor + 145], [540, yFloor + 165], [780, yFloor + 148], [1080, yFloor + 155]], '#991B1B', 42);
  line([[0, yFloor + 150], [340, yFloor + 145], [540, yFloor + 165], [780, yFloor + 148], [1080, yFloor + 155]], '#D62839', 26);
  if (acidGlow > 0) { ctx.save(); ctx.globalAlpha = clamp(acidGlow, 0, 0.75); circle(540, yFloor - bump * 45, 95 * acidGlow + 30, '#EF4444'); ctx.restore(); }
  ctx.restore();
}

export function magnifier(x, y, r = 180) {
  ctx.save(); ctx.translate(x, y);
  ctx.save(); ctx.rotate(0.75); rr(r - 12, -20, 150, 40, 18); ctx.fillStyle = '#18181B'; ctx.fill(); ctx.restore();
  circle(0, 0, r + 14, '#18181B'); circle(0, 0, r, '#E0F2FE');
  ctx.strokeStyle = 'rgba(255,255,255,0.8)'; ctx.lineWidth = 14; ctx.lineCap = 'round';
  ctx.beginPath(); ctx.arc(0, 0, r * 0.72, -2.5, -1.5); ctx.stroke();
  ctx.restore();
}

export function guardCell(x, y, s = 1, alert = 0, t = 0) {
  ctx.save(); ctx.translate(x, y + Math.sin(t * 7) * 8); ctx.scale(s, s);
  circle(0, 0, 54, alert > 0.5 ? '#FDE047' : '#F8FAFC'); ctx.lineWidth = 7; ctx.strokeStyle = '#18181B'; ctx.stroke();
  circle(-16, -8, 11, '#18181B'); circle(16, -8, 11, '#18181B'); circle(-14, -10, 4, '#FFFFFF'); circle(18, -10, 4, '#FFFFFF');
  ctx.beginPath();
  if (alert > 0.5) { ctx.arc(0, 16, 16, 0, TAU); ctx.fillStyle = '#D62839'; ctx.fill(); }
  else { ctx.arc(0, 12, 16, 0.2, Math.PI - 0.2); ctx.strokeStyle = '#18181B'; ctx.lineWidth = 5; ctx.stroke(); }
  rr(-28, -68, 56, 22, 8); ctx.fillStyle = '#2A9D8F'; ctx.fill(); bigText('GUARD', 0, -56, 15, '#FFFFFF');
  ctx.restore();
}

export function kidCartoon(x, y, s = 1, { mood = 'happy', scratch = 0, t = 0 } = {}) {
  ctx.save(); ctx.translate(x, y); ctx.scale(s, s);
  rr(-62, 15, 124, 150, 34); ctx.fillStyle = '#2A9D8F'; ctx.fill(); ctx.lineWidth = 8; ctx.strokeStyle = '#18181B'; ctx.stroke();
  ctx.fillStyle = '#FFD43B'; ctx.fillRect(-58, 72, 116, 26);
  circle(0, -68, 86, '#FDBA74'); ctx.lineWidth = 8; ctx.strokeStyle = '#18181B'; ctx.stroke();
  ctx.fillStyle = '#18181B'; ctx.beginPath(); ctx.arc(0, -96, 82, Math.PI + 0.3, -0.3); ctx.fill();
  circle(-26, -150, 22, '#18181B'); circle(12, -158, 26, '#18181B'); circle(44, -142, 18, '#18181B');
  circle(-28, -72, 16, '#FFFFFF'); circle(28, -72, 16, '#FFFFFF');
  const px = mood === 'lookDown' ? 2 : mood === 'shock' ? 0 : 3;
  const py = mood === 'lookDown' ? 5 : 0;
  circle(-28 + px, -72 + py, 8, '#18181B'); circle(28 + px, -72 + py, 8, '#18181B');
  circle(-25 + px, -75 + py, 3, '#FFFFFF'); circle(31 + px, -75 + py, 3, '#FFFFFF');
  ctx.strokeStyle = '#18181B'; ctx.lineWidth = 6; ctx.lineCap = 'round';
  if (mood === 'itch' || mood === 'shock') {
    line([[-44, -96], [-14, -104]], '#18181B', 6); line([[44, -96], [14, -104]], '#18181B', 6); ell(0, -34, 18, 22, '#D62839');
  } else {
    ctx.beginPath(); ctx.arc(0, -44, 24, 0.15, Math.PI - 0.15); ctx.stroke();
  }
  const wob = Math.sin(t * 22) * 18 * scratch;
  line([[62, 42], [116, 68 + wob], [82, 118 + wob]], '#FDBA74', 24); circle(82, 118 + wob, 16, '#FDBA74');
  if (scratch > 0.2) circle(80, 128, 14, '#D62839');
  ctx.restore();
}

export function planetGlobe(x, y, r = 160, t = 0, ringed = false) {
  ctx.save(); ctx.translate(x, y);
  if (ringed) {
    ctx.save(); ctx.rotate(-0.22);
    ctx.beginPath(); ctx.ellipse(0, 0, r * 1.55, r * 0.36, 0, 0, TAU);
    ctx.strokeStyle = '#FFD43B'; ctx.lineWidth = 18; ctx.stroke(); ctx.restore();
  }
  circle(0, 0, r, '#38BDF8'); ctx.lineWidth = 8; ctx.strokeStyle = '#18181B'; ctx.stroke();
  const drift = Math.sin(t * 1.2) * r * 0.15;
  ell(-r * 0.25 + drift, -r * 0.18, r * 0.34, r * 0.24, '#34D399', 0.2);
  ell(r * 0.28 + drift, r * 0.22, r * 0.28, r * 0.3, '#34D399', -0.3);
  ctx.restore();
}

export function creatureBuddy(x, y, s = 1, t = 0, col = '#F97316') {
  ctx.save(); ctx.translate(x, y + Math.sin(t * 4) * 10); ctx.scale(s, s);
  // Friendly octopus/creature mascot
  for (let i = -2; i <= 2; i++) {
    const wave = Math.sin(t * 6 + i) * 14;
    line([[i * 28, 45], [i * 36 + wave, 115]], col, 22);
  }
  circle(0, 0, 88, col); ctx.lineWidth = 8; ctx.strokeStyle = '#18181B'; ctx.stroke();
  circle(-28, -16, 18, '#FFFFFF'); circle(28, -16, 18, '#FFFFFF');
  circle(-26, -16, 9, '#18181B'); circle(30, -16, 9, '#18181B');
  ctx.beginPath(); ctx.arc(0, 14, 24, 0.15, Math.PI - 0.15); ctx.strokeStyle = '#18181B'; ctx.lineWidth = 6; ctx.stroke();
  ctx.restore();
}

export function batteryMeter(x, y, s = 1, pct = 1.0) {
  ctx.save(); ctx.translate(x, y); ctx.scale(s, s);
  rr(-36, -135, 72, 26, 10); ctx.fillStyle = '#18181B'; ctx.fill();
  rr(-85, -110, 170, 250, 28); ctx.fillStyle = '#FFFFFF'; ctx.fill(); ctx.lineWidth = 9; ctx.strokeStyle = '#18181B'; ctx.stroke();
  const hFill = 216 * clamp(pct, 0.05, 1);
  const col = pct > 0.6 ? '#22C55E' : pct > 0.3 ? '#FACC15' : '#EF4444';
  rr(-68, 122 - hFill, 136, hFill, 16); ctx.fillStyle = col; ctx.fill();
  bigText(`${Math.round(pct * 100)}%`, 0, 15, 52, '#18181B');
  ctx.restore();
}

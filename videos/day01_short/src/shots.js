import { ctx, C, W, H, TAU, clamp, lerp, seg, eo, eio, eob, rnd, bigText, fillAll, rr, circle, ell, line } from './core/lib.js';
import { L, Le, Wd, T } from './core/timing.js';
import * as K from './core/kit.js';
import * as P from './cartoon_props.js';

export function buildShots() {
  const S = [], CUES = [];
  const add = (o) => (S.push(o), o);
  const cue = (t, type, o = {}) => CUES.push({ t: +t.toFixed(3), type, ...o });
  const cut = (i) => (i === 0 ? 0 : L(i) - 0.08);

  // S01 — Hook: mosquito does NOT actually bite!
  {
    const st = cut(0), biteT = Wd('bite', 0) - st;
    add({
      id: 'S01', at: st, cam: [540, 800], note: 'Leo surprised by tiny swooping mosquito',
      draw(lt, d, t) {
        K.room();
        const shocked = lt > biteT;
        const bounce = eob(seg(lt, 0, 0.35));
        P.kidCartoon(340, 890, 1.55 * bounce, { mood: shocked ? 'shock' : 'happy', scratch: shocked ? 0.5 : 0, t });
        const mx = lerp(1020, 740, eio(seg(lt, 0.1, Math.max(0.5, biteT))));
        const my = 620 + Math.sin(lt * 10) * 28;
        P.mosquito(mx, my, 1.45, { wing: lt, bite: shocked ? 0.9 : 0.2, flip: -1 });
        if (shocked) {
          const pop = eob(seg(lt, biteT, biteT + 0.25));
          K.shockLines(740, my, 170, clamp((lt - biteT) * 4));
          K.pill('NO TEETH — TINY STRAW!', 540, 310, 40, C.red, C.white, pop);
          K.redX(740, 440, 0.45 * pop);
        }
      }
    });
    cue(st + 0.05, 'whoosh');
    cue(st + biteT, 'boing', { gain: 0.7 });
  }

  // S02 — Inside the mouth: 6 tiny needles under magnifier!
  {
    const st = cut(1), sixT = Wd('6', 1) - st;
    add({
      id: 'S02', at: st, cam: [540, 800], note: 'magnifying zoom into 6 tiny proboscis straws',
      draw(lt) {
        fillAll('#FEF3C7');
        K.pill('UNDER A MAGNIFYING GLASS', 540, 295, 36, C.ink, C.yellow, eob(seg(lt, 0, 0.3)));
        P.magnifier(540, 690, 255, '');
        const p = eob(seg(lt, 0.2, 0.7));
        ctx.save();
        ctx.beginPath();
        ctx.arc(540, 690, 240, 0, TAU);
        ctx.clip();
        P.mosquito(355, 675, 2.15 * p, { wing: lt, bite: 0.5 });
        const spread = eob(seg(lt, sixT - 0.1, sixT + 0.45));
        for (let i = 0; i < 6; i++) {
          const ang = (i - 2.5) * 0.11 * spread;
          const x2 = 540 + Math.cos(ang) * 220;
          const y2 = 690 + Math.sin(ang) * 200;
          line([[500, 690], [x2, y2]], i % 2 === 0 ? C.red : '#2A9D8F', 8);
          circle(x2, y2, 7, C.yellow);
        }
        ctx.restore();
        K.pill(lt > sixT ? '6 MICRO STRAWS!' : 'ZOOMING IN...', 540, 1085, 42, C.ink, lt > sixT ? C.yellow : C.white, 1);
      }
    });
    cue(st, 'whoosh');
    cue(st + sixT, 'pop', { gain: 0.8 });
  }

  // S03 — Stealth landing on skin
  {
    const st = cut(2), landT = Wd('lands', 2) - st;
    add({
      id: 'S03', at: st, cam: [540, 800], note: 'mosquito touches down quietly onto skin surface',
      draw(lt) {
        fillAll('#FFFBEB');
        P.skinScene(860, 0.05, 0);
        const drop = eio(seg(lt, 0.15, Math.max(0.6, landT + 0.4)));
        const my = lerp(370, 735, drop);
        P.mosquito(540, my, 1.9, { wing: lt * (1 - drop * 0.8), bite: drop > 0.85 ? 0.8 : 0.1, flip: 1 });
        if (lt > landT) {
          K.pill('STEALTH LANDING!', 540, 315, 44, '#2A9D8F', C.white, eob(seg(lt, landT, landT + 0.3)));
        }
      }
    });
    cue(st, 'slide', { dur: 0.7 });
    cue(st + landT + 0.25, 'plop', { gain: 0.65 });
  }

  // S04 — Saliva goes inside first!
  {
    const st = cut(3), salT = Wd('saliva', 3) - st;
    add({
      id: 'S04', at: st, cam: [540, 800], note: 'saliva drops injected inside skin cross section',
      draw(lt) {
        fillAll('#FEF2F2');
        P.skinScene(740, 0.18, 0.15);
        line([[540, 310], [540, 920]], '#18181B', 28);
        line([[540, 310], [540, 920]], '#52525B', 14);
        for (let i = 0; i < 5; i++) {
          const cycle = ((lt - salT * 0.4) * 1.4 - i * 0.18) % 1;
          if (cycle < 0) continue;
          const dy = lerp(740, 920, cycle);
          const dx = 540 + Math.sin(cycle * 9 + i) * 35;
          circle(dx, dy, 18, '#84CC16');
          circle(dx - 4, dy - 4, 7, '#ECFCCB');
        }
        if (lt > salT) {
          K.pill('STEP 1: SALIVA DROP', 540, 320, 42, C.ink, '#BEF264', eob(seg(lt, salT, salT + 0.3)));
        }
      }
    });
    cue(st, 'whoosh');
    cue(st + salT, 'bubbles', { dur: 1.6 });
  }

  // S05 — Why? Keeps blood flowing like juice instead of clotting!
  {
    const st = cut(4), bloodT = Wd('blood', 4) - st;
    add({
      id: 'S05', at: st, cam: [540, 800], note: 'inside blood vessel: anti-clot saliva keeps cells flowing',
      draw(lt, d, t) {
        fillAll('#450A0A');
        K.pill('ANTI-CLOT SALIVA!', 540, 310, 42, C.yellow, C.ink, eob(seg(lt, 0, 0.3)));
        ctx.fillStyle = '#7F1D1D';
        ctx.fillRect(0, 450, W, 620);
        line([[0, 450], [W, 450]], '#FCA5A5', 14);
        line([[0, 1070], [W, 1070]], '#FCA5A5', 14);
        for (let i = 0; i < 12; i++) {
          const spd = 260 + rnd(i) * 140;
          const bx = ((i * 125 + lt * spd) % (W + 160)) - 80;
          const by = 540 + (i % 4) * 125 + Math.sin(t * 4 + i) * 16;
          ell(bx, by, 44, 30, '#DC2626', Math.sin(t + i) * 0.25);
          ell(bx, by, 22, 13, '#F87171', Math.sin(t + i) * 0.25);
        }
        if (lt > bloodT) {
          K.pill('SMOOTH SIPPING!', 540, 1170, 44, C.ink, C.yellow, eob(seg(lt, bloodT, bloodT + 0.3)));
        }
      }
    });
    cue(st, 'whoosh');
    cue(st + bloodT, 'sparkle', { dur: 1.0 });
  }

  // S06 — Body defense team detects the trick!
  {
    const st = cut(5), defT = Wd('defense', 5) - st;
    add({
      id: 'S06', at: st, cam: [540, 800], note: 'immune guard cells spot mosquito saliva intruder',
      draw(lt, d, t) {
        K.xray(t);
        K.pill('BODY DEFENSE TEAM!', 540, 300, 42, C.yellow, C.ink, eob(seg(lt, 0, 0.3)));
        circle(540, 770, 52 + Math.sin(lt * 8) * 6, '#84CC16');
        K.pill('INTRUDER!', 540, 650, 32, C.ink, '#BEF264', 1);
        const rush = eob(seg(lt, 0.2, Math.max(0.7, defT + 0.4)));
        P.guardCell(lerp(120, 310, rush), 780, 1.85, rush > 0.7 ? 1 : 0, t);
        P.guardCell(lerp(960, 770, rush), 780, 1.85, rush > 0.7 ? 1 : 0, t + 1);
        K.warning(540, 470, lt > defT ? eob(seg(lt, defT, defT + 0.3)) : 0);
      }
    });
    cue(st, 'whoosh');
    cue(st + defT, 'boing', { gain: 0.7 });
  }

  // S07 — Guards trigger HISTAMINE alarm!
  {
    const st = cut(6), histT = Wd('histamine', 6) - st;
    add({
      id: 'S07', at: st, cam: [540, 800], note: 'histamine alarm waves burst from guard cells',
      draw(lt, d, t) {
        K.xray(t);
        const pulse = Math.sin(lt * 10) * 0.5 + 0.5;
        for (let r = 0; r < 3; r++) {
          ctx.save();
          ctx.beginPath();
          ctx.arc(540, 760, ((lt * 260 + r * 140) % 420) + 60, 0, TAU);
          ctx.strokeStyle = C.red;
          ctx.lineWidth = 14;
          ctx.globalAlpha = 0.55;
          ctx.stroke();
          ctx.restore();
        }
        P.guardCell(540, 760, 2.0 + pulse * 0.1, 1, t);
        if (lt > histT) {
          for (let i = 0; i < 10; i++) {
            const ang = (i / 10) * TAU + lt * 0.6;
            const rad = lerp(70, 300, eob(seg(lt, histT, histT + 0.6)));
            const hx = 540 + Math.cos(ang) * rad;
            const hy = 760 + Math.sin(ang) * rad;
            circle(hx, hy, 24, i % 2 === 0 ? C.yellow : C.red);
          }
          K.pill('HISTAMINE ALARM!', 540, 325, 48, C.red, C.white, eob(seg(lt, histT, histT + 0.25)));
        }
      }
    });
    cue(st, 'whoosh');
    cue(st + histT, 'alarm', { dur: 1.8 });
  }

  // S08 — Histamine swells skin into itchy red bump!
  {
    const st = cut(7), itchT = Wd('itch', 7) - st;
    add({
      id: 'S08', at: st, cam: [540, 800], note: 'skin swells red bump and cartoon scratches',
      draw(lt, d, t) {
        fillAll('#FEF2F2');
        const bump = eob(seg(lt, 0.15, 0.95));
        P.skinScene(950, bump, bump * 0.75);
        P.kidCartoon(320, 600, 1.35, { mood: lt > itchT ? 'itch' : 'shock', scratch: lt > itchT ? 1 : 0.2, t });
        if (lt > itchT) {
          K.pill('RED BUMP + ITCH!', 540, 305, 46, C.red, C.white, eob(seg(lt, itchT, itchT + 0.25)));
          bigText('SO ITCHY!', 760, 680, 68, C.red, -0.08, eob(seg(lt, itchT, itchT + 0.25)));
        }
      }
    });
    cue(st, 'whoosh');
    cue(st + itchT, 'heartbeat');
  }

  // S09 — Fun Fact: ONLY female mosquitoes bite!
  {
    const st = cut(8), femT = Wd('female', 8) - st;
    add({
      id: 'S09', at: st, cam: [540, 800], note: 'male mosquito drinks flower nectar vs female egg protein',
      draw(lt) {
        fillAll('#F0FDF4');
        K.pill('FUN FACT QUIZ!', 540, 295, 44, C.ink, C.yellow, eob(seg(lt, 0, 0.3)));
        line([[540, 370], [540, 1180]], '#CBD5E1', 6);
        P.mosquito(270, 630, 1.5, { wing: lt, bite: 0, flip: 1 });
        circle(330, 830, 48, '#34D399');
        circle(330, 830, 20, C.yellow);
        K.pill('BOY: NECTAR', 270, 1000, 34, '#2A9D8F', C.white, 1);

        const pop = lt > femT ? eob(seg(lt, femT, femT + 0.35)) : 0.8;
        P.mosquito(810, 630, 1.5 * pop, { wing: lt, bite: 0.7, flip: -1 });
        circle(800, 540, 24 * pop, '#F472B6');
        ell(790, 830, 34, 44, '#FEF08A');
        K.pill('GIRL: EGGS', 810, 1000, 34, C.red, C.white, pop);
      }
    });
    cue(st, 'whoosh');
    cue(st + femT, 'sparkle', { dur: 1.0 });
  }

  // S10 — Cool Kid Takeaway: Use Ice + Subscribe BabyBeats Rhymo!
  {
    const st = cut(9), iceT = Wd('ice', 9) - st;
    add({
      id: 'S10', at: st, cam: [540, 800], note: 'cooling ice pack + Leo waving goodbye',
      draw(lt, d, t) {
        K.room();
        P.kidCartoon(370, 850, 1.55, { mood: 'happy', scratch: 0, t });
        const iceDrop = eob(seg(lt, Math.max(0, iceT - 0.1), iceT + 0.4));
        ctx.save();
        ctx.translate(770, 740);
        ctx.scale(iceDrop, iceDrop);
        rr(-105, -105, 210, 210, 38);
        ctx.fillStyle = '#38BDF8';
        ctx.fill();
        ctx.lineWidth = 9;
        ctx.strokeStyle = '#18181B';
        ctx.stroke();
        bigText('ICE', 0, 18, 76, '#FFFFFF');
        ctx.restore();
        K.pill('BABYBEATS RHYMO', 540, 310, 46, C.ink, C.yellow, eob(seg(lt, 0.15, 0.5)));
        K.pill('COOL IT WITH ICE!', 540, 425, 38, '#2A9D8F', C.white, Math.max(0.85, iceDrop));
      }
    });
    cue(st, 'whoosh');
    cue(st + iceT, 'pop', { gain: 0.7 });
    cue(st + iceT + 0.3, 'sparkle', { dur: 1.2 });
  }

  return { shots: S, cues: CUES };
}

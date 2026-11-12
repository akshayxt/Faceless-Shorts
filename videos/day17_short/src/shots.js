import { ctx, C, W, H, TAU, clamp, lerp, seg, eo, eio, eob, rnd, bigText, fillAll, rr, circle, ell, line } from './core/lib.js';
import { L, Le, Wd, T } from './core/timing.js';
import * as K from './core/kit.js';
import * as P from './cartoon_props.js';

export function buildShots() {
  const S = [], CUES = [];
  const add = (o) => (S.push(o), o);
  const cue = (t, type, o = {}) => CUES.push({ t: +t.toFixed(3), type, ...o });
  const cut = (i) => (i === 0 ? 0 : L(i) - 0.08);

  {
    const st = cut(0);
    add({
      id: 'S01', at: st, cam: [540, 800], note: 'scene kid',
      draw(lt, d, t) {
        K.room();
        P.kidCartoon(540, 860, 1.65 * eob(seg(lt, 0, 0.35)), { mood: lt > 1.0 ? 'shock' : 'happy', t });
        K.pill('BRAIN BATTERY 5%!', 540, 315, 42, C.red, C.white, eob(seg(lt, 0.25, 0.6)));
        K.shockLines(540, 740, 260, clamp((lt - 0.8) * 3));
      }
    });
    cue(st, 'whoosh'); cue(st + 0.5, 'boing', { gain: 0.7 });
  }
  {
    const st = cut(1);
    add({
      id: 'S02', at: st, cam: [540, 800], note: 'scene batterylow',
      draw(lt, d, t) {
        K.room();
        P.batteryMeter(540, 760, 1.45, 0.18);
        K.pill('POWER LOW!', 540, 310, 44, C.ink, C.yellow, 1);
      }
    });
    cue(st, 'whoosh'); cue(st + 0.4, 'sparkle', { dur: 1.0 });
  }
  {
    const st = cut(2);
    add({
      id: 'S03', at: st, cam: [540, 800], note: 'scene spark',
      draw(lt, d, t) {
        fillAll('#EFF6FF');
        P.kidCartoon(360, 860, 1.45, { mood: 'happy', t });
        P.magnifier(720, 680, 155);
        K.pill('REAL TRUTH!', 540, 310, 44, '#2A9D8F', C.white, 1);
      }
    });
    cue(st, 'whoosh'); cue(st + 0.35, 'pop', { gain: 0.7 });
  }
  {
    const st = cut(3);
    add({
      id: 'S04', at: st, cam: [540, 800], note: 'scene kidhappy',
      draw(lt, d, t) {
        fillAll('#EFF6FF');
        P.kidCartoon(360, 860, 1.45, { mood: 'happy', t });
        P.magnifier(720, 680, 155);
        K.pill('REAL TRUTH!', 540, 310, 44, '#2A9D8F', C.white, 1);
      }
    });
    cue(st, 'whoosh'); cue(st + 0.35, 'pop', { gain: 0.7 });
  }
  {
    const st = cut(4);
    add({
      id: 'S05', at: st, cam: [540, 800], note: 'scene batteryhigh',
      draw(lt, d, t) {
        K.room();
        P.batteryMeter(540, 760, 1.45, 1.0);
        K.pill('100% RECHARGED!', 540, 310, 44, C.ink, C.yellow, 1);
      }
    });
    cue(st, 'whoosh'); cue(st + 0.4, 'sparkle', { dur: 1.0 });
  }
  {
    const st = cut(5);
    add({
      id: 'S06', at: st, cam: [540, 800], note: 'scene heart',
      draw(lt, d, t) {
        fillAll('#EFF6FF');
        P.kidCartoon(360, 860, 1.45, { mood: 'happy', t });
        P.magnifier(720, 680, 155);
        K.pill('REAL TRUTH!', 540, 310, 44, '#2A9D8F', C.white, 1);
      }
    });
    cue(st, 'whoosh'); cue(st + 0.35, 'pop', { gain: 0.7 });
  }
  {
    const st = cut(6);
    add({
      id: 'S07', at: st, cam: [540, 800], note: 'scene outro',
      draw(lt, d, t) {
        K.room();
        P.kidCartoon(540, 840, 1.65, { mood: 'happy', t });
        K.pill('BABYBEATS RHYMO!', 540, 315, 46, C.ink, C.yellow, eob(seg(lt, 0, 0.4)));
        K.heart(820, 560, 1.35 * eob(seg(lt, 0.3, 0.7)), Math.abs(Math.sin(lt * 8)));
      }
    });
    cue(st, 'whoosh'); cue(st + 0.4, 'sparkle', { dur: 1.2 });
  }
  {
    const st = cut(7);
    add({
      id: 'S08', at: st, cam: [540, 800], note: 'scene kid',
      draw(lt, d, t) {
        K.room();
        P.kidCartoon(540, 860, 1.65 * eob(seg(lt, 0, 0.35)), { mood: lt > 1.0 ? 'shock' : 'happy', t });
        K.pill('BRAIN BATTERY 5%!', 540, 315, 42, C.red, C.white, eob(seg(lt, 0.25, 0.6)));
        K.shockLines(540, 740, 260, clamp((lt - 0.8) * 3));
      }
    });
    cue(st, 'whoosh'); cue(st + 0.5, 'boing', { gain: 0.7 });
  }
  {
    const st = cut(8);
    add({
      id: 'S09', at: st, cam: [540, 800], note: 'scene outro',
      draw(lt, d, t) {
        K.room();
        P.kidCartoon(540, 840, 1.65, { mood: 'happy', t });
        K.pill('BABYBEATS RHYMO!', 540, 315, 46, C.ink, C.yellow, eob(seg(lt, 0, 0.4)));
        K.heart(820, 560, 1.35 * eob(seg(lt, 0.3, 0.7)), Math.abs(Math.sin(lt * 8)));
      }
    });
    cue(st, 'whoosh'); cue(st + 0.4, 'sparkle', { dur: 1.2 });
  }

  return { shots: S, cues: CUES };
}

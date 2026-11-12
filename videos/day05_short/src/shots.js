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
      id: 'S01', at: st, cam: [540, 800], note: 'scene planet',
      draw(lt, d, t) {
        fillAll('#0F172A');
        K.pill('SPACE & SKY WONDER!', 540, 305, 40, C.yellow, C.ink, 1);
        P.planetGlobe(540, 750, 200 * eob(seg(lt, 0, 0.4)), t, false);
      }
    });
    cue(st, 'whoosh'); cue(st + 0.5, 'sparkle', { dur: 1.1 });
  }
  {
    const st = cut(1);
    add({
      id: 'S02', at: st, cam: [540, 800], note: 'scene ray',
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
    const st = cut(2);
    add({
      id: 'S03', at: st, cam: [540, 800], note: 'scene planet2',
      draw(lt, d, t) {
        fillAll('#0F172A');
        K.pill('SPACE & SKY WONDER!', 540, 305, 40, C.yellow, C.ink, 1);
        P.planetGlobe(540, 750, 200 * eob(seg(lt, 0, 0.4)), t, true);
      }
    });
    cue(st, 'whoosh'); cue(st + 0.5, 'sparkle', { dur: 1.1 });
  }
  {
    const st = cut(3);
    add({
      id: 'S04', at: st, cam: [540, 800], note: 'scene xray',
      draw(lt, d, t) {
        K.xray(t);
        K.pill('INSIDE LOOK!', 540, 305, 42, C.yellow, C.ink, eob(seg(lt, 0, 0.3)));
        P.magnifier(540, 740, 230);
        K.heart(540, 740, 2.2, Math.abs(Math.sin(lt * 5)));
      }
    });
    cue(st, 'whoosh'); cue(st + 0.4, 'heartbeat');
  }
  {
    const st = cut(4);
    add({
      id: 'S05', at: st, cam: [540, 800], note: 'scene reveal',
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
    const st = cut(5);
    add({
      id: 'S06', at: st, cam: [540, 800], note: 'scene stars',
      draw(lt, d, t) {
        fillAll('#0F172A');
        K.pill('SPACE & SKY WONDER!', 540, 305, 40, C.yellow, C.ink, 1);
        P.planetGlobe(540, 750, 200 * eob(seg(lt, 0, 0.4)), t, false);
      }
    });
    cue(st, 'whoosh'); cue(st + 0.5, 'sparkle', { dur: 1.1 });
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
      id: 'S08', at: st, cam: [540, 800], note: 'scene planet',
      draw(lt, d, t) {
        fillAll('#0F172A');
        K.pill('SPACE & SKY WONDER!', 540, 305, 40, C.yellow, C.ink, 1);
        P.planetGlobe(540, 750, 200 * eob(seg(lt, 0, 0.4)), t, false);
      }
    });
    cue(st, 'whoosh'); cue(st + 0.5, 'sparkle', { dur: 1.1 });
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

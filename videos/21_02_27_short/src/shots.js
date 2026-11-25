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
      id: 'S01', at: st, cam: [540, 800], note: 'scene story_intro',
      draw(lt, d, t) {
        K.room(); P.kidCartoon(540, 860, 1.65 * eob(seg(lt, 0, 0.35)), { mood: 'happy', t }); K.pill('WHY DO WE DREAM?!', 540, 315, 42, C.red, C.white, eob(seg(lt, 0.25, 0.6))); K.burst(540, 740, 1.1, 0.5);
      }
    });
    cue(st, 'whoosh'); cue(st + 0.4, 'pop');
  }
  {
    const st = cut(1);
    add({
      id: 'S02', at: st, cam: [540, 800], note: 'scene problem',
      draw(lt, d, t) {
        fillAll('#FEF2F2'); P.kidCartoon(380, 860, 1.55, { mood: 'lookDown', t }); K.pill('UH OH!', 540, 310, 44, C.red, C.white, 1);
      }
    });
    cue(st, 'whoosh'); cue(st + 0.3, 'alarm', { dur: 0.6 });
  }
  {
    const st = cut(2);
    add({
      id: 'S03', at: st, cam: [540, 800], note: 'scene shock',
      draw(lt, d, t) {
        K.room(); P.kidCartoon(540, 860, 1.65, { mood: 'gasp', t }); K.pill('WAIT WHAT?!', 540, 310, 46, C.red, C.white, eob(seg(lt, 0, 0.4)));
      }
    });
    cue(st, 'whoosh'); cue(st + 0.3, 'alarm', { dur: 0.8 });
  }
  {
    const st = cut(3);
    add({
      id: 'S04', at: st, cam: [540, 800], note: 'scene discovery',
      draw(lt, d, t) {
        fillAll('#FFFBEB'); P.kidCartoon(380, 860, 1.5, { mood: 'think', t }); P.magnifier(700, 700, 140); K.pill('DID YOU KNOW?', 540, 310, 44, '#B45309', C.white, 1);
      }
    });
    cue(st, 'whoosh'); cue(st + 0.4, 'pop');
  }
  {
    const st = cut(4);
    add({
      id: 'S05', at: st, cam: [540, 800], note: 'scene action_step',
      draw(lt, d, t) {
        K.room(); P.kidCartoon(540, 860, 1.55, { mood: 'gasp', t }); K.pill('THE SECRET!', 540, 315, 44, C.ink, C.yellow, eob(seg(lt, 0, 0.4)));
      }
    });
    cue(st, 'whoosh'); cue(st + 0.4, 'pop');
  }
  {
    const st = cut(5);
    add({
      id: 'S06', at: st, cam: [540, 800], note: 'scene kindness',
      draw(lt, d, t) {
        fillAll('#FEFCE8'); P.kidCartoon(380, 860, 1.55, { mood: 'happy', t }); K.pill('TRY THIS!', 540, 310, 44, '#15803D', C.white, 1);
      }
    });
    cue(st, 'whoosh'); cue(st + 0.4, 'sparkle', { dur: 1.0 });
  }
  {
    const st = cut(6);
    add({
      id: 'S07', at: st, cam: [540, 800], note: 'scene heart_moment',
      draw(lt, d, t) {
        K.room(); P.kidCartoon(540, 860, 1.6, { mood: 'happy', t }); K.pill('SO POWERFUL!', 540, 310, 46, '#15803D', C.white, eob(seg(lt, 0, 0.4)));
      }
    });
    cue(st, 'whoosh'); cue(st + 0.4, 'sparkle', { dur: 1.0 });
  }
  {
    const st = cut(7);
    add({
      id: 'S08', at: st, cam: [540, 800], note: 'scene moral_truth',
      draw(lt, d, t) {
        fillAll('#F0FDF4'); P.kidCartoon(360, 860, 1.45, { mood: 'happy', t }); P.magnifier(720, 680, 155); K.pill('BIG LESSON!', 540, 310, 44, '#15803D', C.white, 1);
      }
    });
    cue(st, 'whoosh'); cue(st + 0.35, 'pop');
  }
  {
    const st = cut(8);
    add({
      id: 'S09', at: st, cam: [540, 800], note: 'scene outro',
      draw(lt, d, t) {
        K.room(); P.kidCartoon(540, 840, 1.65, { mood: 'happy', t }); K.pill('BABYBEATS RHYMO!', 540, 315, 46, C.ink, C.yellow, eob(seg(lt, 0, 0.4))); K.heart(820, 560, 1.35 * eob(seg(lt, 0.3, 0.7)), Math.abs(Math.sin(lt * 8)));
      }
    });
    cue(st, 'whoosh'); cue(st + 0.4, 'sparkle', { dur: 1.2 });
  }

  return { shots: S, cues: CUES };
}

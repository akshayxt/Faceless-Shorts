import fs from 'node:fs';
import dns from 'node:dns';

dns.setDefaultResultOrder('ipv4first');

const CFG_PATH = 'G:\\Faceless-Shorts\\automation\\data\\telegram_config.json';

export async function sendNodeTelegram(tag, text) {
  if (process.env.BABYBEATS_TG_PARENT === '1') return;
  try {
    if (!fs.existsSync(CFG_PATH)) return;
    const cfg = JSON.parse(fs.readFileSync(CFG_PATH, 'utf-8'));
    if (!cfg.enabled || !cfg.bot_token || !cfg.chat_id) return;
    const esc = String(text).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    const html = `<b>[${tag}]</b>\n<pre>${esc.slice(0, 3400)}</pre>`;
    await fetch(`https://api.telegram.org/bot${cfg.bot_token}/sendMessage`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ chat_id: String(cfg.chat_id), text: html, parse_mode: 'HTML', disable_web_page_preview: true })
    });
  } catch (e) {
    console.error('[TG_WARN]', e.message);
  }
}

import fs from 'node:fs';
import dns from 'node:dns';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

dns.setDefaultResultOrder('ipv4first');

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const CFG_PATH = path.join(__dirname, 'data', 'telegram_config.json');

export async function sendNodeTelegram(tag, text) {
  if (process.env.BABYBEATS_TG_PARENT === '1') return;
  try {
    let token = (process.env.TELEGRAM_BOT_TOKEN || '').trim();
    let chatId = (process.env.TELEGRAM_CHAT_ID || '').trim();
    let enabled = Boolean(token && chatId);
    if (!enabled && fs.existsSync(CFG_PATH)) {
      const cfg = JSON.parse(fs.readFileSync(CFG_PATH, 'utf-8'));
      enabled = Boolean(cfg.enabled);
      token = cfg.bot_token || '';
      chatId = String(cfg.chat_id || '');
    }
    if (!enabled || !token || !chatId) return;
    const esc = String(text).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    const html = `<b>[${tag}]</b>\n<pre>${esc.slice(0, 3400)}</pre>`;
    await fetch(`https://api.telegram.org/bot${token}/sendMessage`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ chat_id: String(chatId), text: html, parse_mode: 'HTML', disable_web_page_preview: true })
    });
  } catch (e) {
    console.error('[TG_WARN]', e.message);
  }
}

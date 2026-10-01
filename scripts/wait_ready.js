/**
 * 等 ChatGPT 结束响应。
 *
 * 用法（eval js）：
 *   const w = eval("(" + require("fs").readFileSync("<ROOT>/scripts/wait_ready.js","utf8") + ")");
 *   console.log(await tab.run(w, { timeout: 250000 }));    // 零参数！
 *
 * 判据：composer 可见输入框所属容器里，aria-label="发送" 的可见 button 出现。
 * ⚠ tab.run 有 300s 硬上限，轮询收在 200s 内。
 * ⚠ 不要用 args 传参 —— 见 ldc_send.js 坑 0。
 */
async () => {
  for (let i = 0; i < 40; i++) {
    const st = await page.evaluate(() => {
      const e = [...document.querySelectorAll('div.ProseMirror[contenteditable="true"]')]
        .find(x => x.offsetParent !== null);
      if (!e) return 'no-input';
      const n = e.closest('div[class*="ComposerLayoutBody"]')
        || e.closest('form') || e.parentElement.parentElement.parentElement;
      const btns = [...n.querySelectorAll('button')].filter(b => b.offsetParent !== null);
      return btns.some(b => /^(发送|send)$/i.test(b.getAttribute('aria-label') || '')) ? 'ready' : 'busy';
    });
    if (st !== 'busy') return st;
    await new Promise(r => setTimeout(r, 4000));
  }
  return 'timeout';
}

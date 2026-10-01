/**
 * E10 送图 —— 发送器（最终版）。
 *
 * 用法（eval js）：
 *   const send = eval("(" + require("fs").readFileSync("<ROOT>/scripts/send_board_prompt.js","utf8") + ")");
 *   console.log(await tab.run(send, { timeout: 250000 }));     // 零参数！
 * 每次发之前改函数体里的常量 N。
 */

/**
 * ── 坑 0（决定性）：`tab.run(fn, {args:[X]})` 的解构参数拿到的是
 *    `[object Object]`，不是 X。───────────────────────────
 * 实测数字 8 也中招：读文件变成 `page_0[object Object].txt`。
 * cell 里 `typeof MSG === 'string'` 的检查**没有意义**——
 * 只有到达页面/文件系统才知道真相。
 *
 * 正确做法：**零参数调用**，需要的值写死在函数体内。
 * 这一条解释了此前几乎所有怪象（发出去是 [object Object]、
 * 清空不干净、len=15），我曾把它们误判为时序竞争。
 *
 * ── 坑 1：必须选中「可见的」输入框 ────────────────────
 * 一个会话里会堆着多个 div.ProseMirror（旧的隐藏但仍在 DOM 里）。
 * document.querySelector 取第一个，于是所有操作落在隐藏元素上：
 *   · insertText 无效  -> len 停在 0
 *   · 清空后又冒出 [object Object] -> len=15
 *   · 位置全为 0，点击命中别的东西 -> "covered by <canvas>"
 *
 * ── 其它已踩的坑 ─────────────────────────────────────
 * · tab.run 第二参数必须 {timeout}；cell 闭包变量全部不可见。
 * · tab.evaluate(fn, arg) 的第二参数不是传值；用 page.evaluate。
 * · page.evaluate(fn, a, b) 只传第一个 arg；多值打包成对象。
 * · tab.waitForSelector() 的 handle 没有 .click()。
 * · 响应中按钮标签是「停止」不是「发送」。
 * · tab.run 有 300s 硬上限，传 timeout 压不下去。
 * · **不要为绕开 composer 异常态而新开标签**；在同一标签
 *   goto("https://chatgpt.com/") 开新会话即可。
 * · **sent 不等于成功**：点击后 ChatGPT 立刻回填 [object Object]，
 *   sent len=N 里的 N 与实际发出的内容无关，必须在整页文本复核。
 * · 多标签并发会触发「检测到可疑活动」账户锁；串行发送，用完即关。
 */
async () => {
  // ── 每集改这两行 ─────────────────────────────────────────
  const N = 8;                       // 页号 1..8
  const EP = "landianchang_video";   // 集目录名（在项目根下）
  // ───────────────────────────────────────────────────────
  const fs = await import("node:fs");
  const path = await import("node:path");
  // 项目根：优先 BOARD_ROOT 环境变量，其次当前工作目录。
  // ⚠ 不要用 import.meta.url —— 本文件是被 eval 成字符串注入 tab runtime 的，
  //   import.meta 在那种上下文里不可靠。
  const ROOT = process.env.BOARD_ROOT || process.cwd();
  const prompt = fs.readFileSync(path.join(ROOT, EP, "prompts", `page_0${N}.txt`), "utf8");
  const msg = `画 P${N}，保存为 /mnt/data/board_${N}.png（1672×941）。\n\n${prompt}`;
  const HEAD = `画 P${N}`;

  const PICK = "div.ProseMirror[contenteditable=\"true\"]";

  for (let attempt = 1; attempt <= 4; attempt++) {
    // 定位可见输入框
    const ok0 = await page.evaluate((sel) => {
      const e = [...document.querySelectorAll(sel)].find(x => x.offsetParent !== null);
      if (!e) return 'no-visible-input';
      e.focus();
      return 'ok';
    }, PICK);
    if (ok0 === 'no-visible-input') return 'FAIL:' + ok0;

    // 清空
    await page.evaluate((sel) => {
      const e = [...document.querySelectorAll(sel)].find(x => x.offsetParent !== null);
      e.focus();
      document.execCommand('selectAll');
      document.execCommand('delete');
    }, PICK);
    await new Promise(r => setTimeout(r, 350));

    // 插入
    await page.evaluate(({ sel, text }) => {
      const e = [...document.querySelectorAll(sel)].find(x => x.offsetParent !== null);
      e.focus();
      document.execCommand('insertText', false, text);
      e.dispatchEvent(new InputEvent('input', { bubbles: true, data: text }));
    }, { sel: PICK, text: msg });
    await new Promise(r => setTimeout(r, 1000));

    // 断言 + 发送
    const r = await page.evaluate(({ sel, head }) => {
      const e = [...document.querySelectorAll(sel)].find(x => x.offsetParent !== null);
      const v = e.innerText;
      if (!v.startsWith(head)) return 'RETRY:内容头不符 len=' + v.length + ' head=' + v.slice(0, 18);
      if (v.includes('[object Object]')) return 'RETRY:含 [object Object] len=' + v.length;
      const n = e.closest('div[class*="ComposerLayoutBody"]')
        || e.closest('form') || e.parentElement.parentElement.parentElement;
      const btns = [...n.querySelectorAll('button')].filter(b => b.offsetParent !== null);
      const labels = btns.map(x => x.getAttribute('aria-label'));
      if (labels.includes('停止')) return 'BUSY:正在响应 (输入已备好 len=' + v.length + ')';
      const b = btns.find(x => /^(发送|send)$/i.test(x.getAttribute('aria-label') || ''));
      if (b) { b.click(); return 'sent len=' + v.length; }
      return 'RETRY:无发送按钮 [' + labels.join(',') + ']';
    }, { sel: PICK, head: HEAD });

    if (r.startsWith('RETRY:')) {
      console.log('  第' + attempt + '轮重试: ' + r);
      await new Promise(x => setTimeout(x, 1500));
      continue;
    }
    if (r.startsWith('sent')) {
      await new Promise(x => setTimeout(x, 2500));
      const ok = await page.evaluate((m) => document.body.innerText.includes(m),
        `board_${N}.png`);
      return ok ? r : `WARN:sent 但页面未见 ldc_page_${N}`;
    }
    return r;
  }
  return 'FAIL:重试 4 轮仍不成功';
}

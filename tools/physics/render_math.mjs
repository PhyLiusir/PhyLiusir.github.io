#!/usr/bin/env node
/**
 * 把 tools/physics/notes-body.html 里的 LaTeX 渲染成静态 HTML，注入 notes.html。
 *
 * 为什么要有这一步
 * ----------------
 * 页面运行时不加载任何 JS，所以公式必须在构建期变成 HTML。源文件里写的是
 * LaTeX（可读、可改、可 diff），而不是几百个 <span>；渲染失败必须让构建失败。
 *
 * 为什么双语不用 data-zh
 * ----------------------
 * 全站的语言切换靠给元素挂 data-zh、再由 site.js 换 innerHTML。那一招会把已经
 * 渲染好的 KaTeX 结构整个丢掉——中文版就只剩文字、没有公式。所以这里给每个
 * 块生成英、中各一份，用 CSS 按 <html data-lang> 切换，两边的公式都是真的。
 *
 * 源文件格式
 * ----------
 *   <!-- block:<id>:en -->  ...英文...  <!-- /block:<id>:en -->
 *   <!-- block:<id>:zh -->  ...中文...  <!-- /block:<id>:zh -->
 *
 * 目标页面里对应
 *   <!-- mb:<id> -->   ...生成内容...   <!-- /mb:<id> -->
 *
 * 用法
 * ----
 *   node tools/physics/render_math.mjs          # 渲染并写回 notes.html
 *   node tools/physics/render_math.mjs --check  # 只校验是否过期
 */

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import katex from "katex";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const SRC = path.join(ROOT, "tools/physics/notes-body.html");
const PAGE = path.join(ROOT, "notes.html");

const KATEX = { throwOnError: true, strict: false, trust: false, output: "html" };
const LANGS = ["en", "zh"];

function renderMath(html) {
  // 先处理独立公式，再处理行内，避免 $$ 被行内规则先吃掉。
  let out = html.replace(/\$\$([\s\S]+?)\$\$/g, (_, tex) =>
    katex.renderToString(tex.trim(), { ...KATEX, displayMode: true }),
  );
  out = out.replace(/\$([^$\n]+?)\$/g, (_, tex) =>
    katex.renderToString(tex.trim(), { ...KATEX, displayMode: false }),
  );
  return out;
}

function parseSource(text) {
  const blocks = new Map(); // id -> { en, zh }
  const re = /<!-- block:([a-z0-9-]+):([a-z]{2}) -->([\s\S]*?)<!-- \/block:\1:\2 -->/g;
  let m;
  while ((m = re.exec(text)) !== null) {
    const [, id, lang, body] = m;
    if (!LANGS.includes(lang)) throw new Error(`unknown language "${lang}" in block ${id}`);
    if (!blocks.has(id)) blocks.set(id, {});
    const entry = blocks.get(id);
    if (entry[lang] !== undefined) throw new Error(`duplicate ${lang} block for ${id}`);
    entry[lang] = body.trim();
  }
  if (blocks.size === 0) throw new Error("no blocks found in notes-body.html");

  // 缺任何一种语言都直接失败：双语不是可选项。
  for (const [id, entry] of blocks) {
    for (const lang of LANGS) {
      if (entry[lang] === undefined) {
        throw new Error(`block ${id} is missing its "${lang}" version`);
      }
    }
  }
  return blocks;
}

const LF = String.fromCharCode(10);
const CRLF = String.fromCharCode(13, 10);

function indent(text, pad) {
  return text
    .split(LF)
    .map((line) => (line.length ? pad + line : line))
    .join(LF);
}

function main() {
  const src = fs.readFileSync(SRC, "utf8");
  const page = fs.readFileSync(PAGE, "utf8");
  const EOL = page.includes(CRLF) ? CRLF : LF;

  const blocks = parseSource(src);
  let out = page;

  for (const [id, entry] of blocks) {
    const open = `<!-- mb:${id} -->`;
    const close = `<!-- /mb:${id} -->`;
    const start = out.indexOf(open);
    const end = out.indexOf(close);
    if (start < 0 || end < 0 || end < start) {
      throw new Error(`markers missing or misordered for mb:${id}`);
    }
    const parts = LANGS.map((lang) => {
      const inner = indent(renderMath(entry[lang]), "  ");
      return `<div class="mbw" data-mb-lang="${lang}">` + EOL + inner + EOL + `</div>`;
    });
    const html = parts.join(EOL).split(LF).join(EOL);
    out = out.slice(0, start + open.length) + EOL + "      " + html + EOL + "      " + out.slice(end);
  }

  if (out.includes("katex-error")) {
    console.error("katex produced an error node — aborting");
    process.exit(1);
  }

  if (process.argv.includes("--check")) {
    if (out !== page) {
      console.error("notes.html is stale (math blocks) — rerun: node tools/physics/render_math.mjs");
      // 只说「过期」在 CI 日志里等于没说；把第一处差异指出来。
      let i = 0;
      while (i < out.length && i < page.length && out[i] === page[i]) i += 1;
      const ctx = (str) => JSON.stringify(str.slice(Math.max(0, i - 70), i + 70));
      console.error(`  first difference at index ${i} (rendered ${out.length}, on disk ${page.length} chars)`);
      console.error(`  rendered: ${ctx(out)}`);
      console.error(`  on disk : ${ctx(page)}`);
      console.error(`  page uses CRLF: ${page.includes(CRLF)}`);
      process.exit(1);
    }
    console.log(`phys-math: OK (${blocks.size} blocks, en+zh)`);
    return;
  }

  fs.writeFileSync(PAGE, out, "utf8");
  console.log(`rendered ${blocks.size} math blocks (en + zh) into notes.html`);
}

main();

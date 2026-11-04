#!/usr/bin/env node
/**
 * 把 tools/physics/notes-body.html 里的 LaTeX 渲染成静态 HTML，注入 notes.html。
 *
 * 为什么要有这一步
 * ----------------
 * 页面运行时不加载任何 JS，所以公式必须在构建期变成 HTML。源文件里写的是
 * LaTeX（可读、可改、可 diff），而不是几百个 <span>；渲染失败必须让构建失败。
 *
 * 源文件格式
 * ----------
 *   <!-- block:<id> -->
 *   ...HTML，其中 $...$ 是行内公式，$$...$$ 是独立公式...
 *   <!-- /block:<id> -->
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
  const blocks = new Map();
  const re = /<!-- block:([a-z0-9-]+) -->([\s\S]*?)<!-- \/block:\1 -->/g;
  let m;
  while ((m = re.exec(text)) !== null) {
    blocks.set(m[1], m[2].trim());
  }
  if (blocks.size === 0) throw new Error("no blocks found in notes-body.html");
  return blocks;
}

const LF = String.fromCharCode(10);
const CRLF = String.fromCharCode(13, 10);

function main() {
  const src = fs.readFileSync(SRC, "utf8");
  const page = fs.readFileSync(PAGE, "utf8");
  const EOL = page.includes(CRLF) ? CRLF : LF;

  const blocks = parseSource(src);
  let out = page;

  for (const [id, body] of blocks) {
    const open = `<!-- mb:${id} -->`;
    const close = `<!-- /mb:${id} -->`;
    const start = out.indexOf(open);
    const end = out.indexOf(close);
    if (start < 0 || end < 0 || end < start) {
      throw new Error(`markers missing or misordered for mb:${id}`);
    }
    const html = renderMath(body).split(LF).join(EOL);
    out = out.slice(0, start + open.length) + EOL + "      " + html + EOL + "      " + out.slice(end);
  }

  if (out.includes("katex-error")) {
    console.error("katex produced an error node — aborting");
    process.exit(1);
  }

  if (process.argv.includes("--check")) {
    if (out !== page) {
      console.error("notes.html is stale (math blocks) — rerun: node tools/physics/render_math.mjs");
      process.exit(1);
    }
    console.log(`phys-math: OK (${blocks.size} blocks)`);
    return;
  }

  fs.writeFileSync(PAGE, out, "utf8");
  console.log(`rendered ${blocks.size} math blocks into notes.html`);
}

main();

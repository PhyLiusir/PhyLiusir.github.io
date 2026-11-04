import pathlib

p = pathlib.Path(r"D:/PhyLiusir.github.io/tools/physics/render_section.mjs")
s = p.read_text(encoding="utf-8")

old = """    const start = out.indexOf(open);
    const end = out.indexOf(close);
    if (start < 0 || end < 0 || end < start) {
      throw new Error(`markers missing or misordered for ${claim.id}`);
    }"""
new = """    const start = out.indexOf(open);
    const end = out.indexOf(close);
    // 页面上已经不放这类块时，安静跳过；数据与自检仍然保留，
    // 哪天要把块放回去，插回标记即可。
    if (start < 0 && end < 0) continue;
    if (start < 0 || end < 0 || end < start) {
      throw new Error(`markers misordered for ${claim.id}`);
    }
    injected += 1;"""
assert old in s
s = s.replace(old, new, 1)

s = s.replace("  let out = page;\n  for (const claim of data.claims) {",
              "  let out = page;\n  let injected = 0;\n  for (const claim of data.claims) {", 1)
s = s.replace("  return out;\n}", "  return { out, injected };\n}", 1)

# 调用点
s = s.replace("const rendered = render(data, page);",
              "const { out: rendered, injected } = render(data, page);", 1)
s = s.replace(
    'console.log(`phys-render: OK (${data.claims.length} blocks, hash ${data.content_hash})`);',
    'console.log(`phys-render: OK (${injected} block(s) on the page, hash ${data.content_hash})`);',
    1,
)
s = s.replace(
    'console.log(\n  `rendered ${data.claims.length} blocks into notes.html · checks ${failed === 0 ? "all pass" : failed + " FAILED"} · ` +\n    `sympy ${data.provenance.sympy} · hash ${data.content_hash}`,\n);',
    'console.log(\n  (injected === 0\n    ? "phys-render: no symbolic/numeric blocks on the page (data still checked)"\n    : `rendered ${injected} blocks into notes.html`) +\n    ` · checks ${failed === 0 ? "all pass" : failed + " FAILED"} · ` +\n    `sympy ${data.provenance.sympy} · hash ${data.content_hash}`,\n);',
    1,
)

p.write_text(s, encoding="utf-8")
print("render_section.mjs: tolerant of missing markers")

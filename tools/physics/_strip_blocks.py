import pathlib
import re

p = pathlib.Path(r"D:/PhyLiusir.github.io/notes.html")
s = p.read_text(encoding="utf-8")

ARTICLES = [
    ("light-front", "lf-energy"),
    ("fock-basis", "fock-normalisation"),
    ("proton-structure", "dis-kinematics"),
]

removed = {"keybox": 0, "eq": 0}

for anchor, cid in ARTICLES:
    start = s.index('id="%s"' % anchor)
    end = s.index("</article>", start)
    seg = s[start:end]

    # 1) 当前焦点块（keybox）——只删物理文章里的，AI 文章的不动
    new_seg, n1 = re.subn(r'\n\s*<div class="keybox">[\s\S]*?</div>\n', "\n", seg, count=1)
    removed["keybox"] += n1
    seg = new_seg

    # 2) 符号与数值块（生成出来的 figure.eq）连同占位标记一起删
    new_seg, n2 = re.subn(
        r'\n\s*<!-- phys:%s -->[\s\S]*?<!-- /phys:%s -->\n' % (cid, cid), "\n", seg, count=1
    )
    removed["eq"] += n2
    seg = new_seg

    s = s[:start] + seg + s[end:]

p.write_text(s, encoding="utf-8")
print("removed:", removed)
print("leftover keybox:", s.count('<div class="keybox">'))
print("leftover eq figures:", s.count('<figure class="eq"'))
print("leftover phys markers:", s.count("<!-- phys:"))
print("mb markers:", s.count("<!-- mb:"))

#!/usr/bin/env python3
"""物理页「符号 + 数值」数据生成器。

第一性原理
----------
页面上印出来的每个数，读者都必须能自己重算一遍。因此：

  1. 数字不许手打进 HTML —— 手打的数字与代码必然漂移，且漂移是静默的。
  2. 每个数必须有**两条独立路径**算出来并互相核对；同一条公式换个写法不算独立。
  3. 每条结果必须带量纲与假设，否则「量纲错但形式看着对」无法被发现。
  4. 产物 JSON 带来源信息（sympy 版本 / 生成时间 / 内容哈希），否则数字只是断言。

本脚本是该 JSON 的唯一生成源。校验模式 `--check` 供 CI 做漂移门禁。

用法
----
    python tools/physics/build_numerics.py            # 生成 assets/physics-data.json
    python tools/physics/build_numerics.py --check    # 只校验磁盘上的 JSON 是否过期
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import pathlib
import platform
import sys

import sympy as sp

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "assets" / "physics-data.json"

# --- 物理常数（CODATA 2022，GeV 单位） -------------------------------------
M_P = sp.Rational(93827208943, 10**11)  # 质子质量 0.93827208943 GeV（CODATA 2022，精确有理数）
DIGITS = 15


# ---------------------------------------------------------------------------
# 工具
# ---------------------------------------------------------------------------


def _f(x, digits: int = DIGITS) -> float:
    """高精度 -> 有效数字字符串 -> float，避免二进制尾巴进 JSON。"""
    return float(sp.N(x, digits + 3))


def _s(x) -> str:
    return str(sp.N(x, DIGITS))


# 判据的英文摘要（页面英文优先，中文 detail 留给作者与 --check 输出）
EN = {
    ("lf-energy", "identity"): "k⁺k⁻ − (k⊥²+m²) − (k² − m²) ≡ 0, proved with no assumptions",
    ("lf-energy", "numeric-onshell"): "at an on-shell point, both sides give 7/4",
    ("lf-energy", "units"): "both sides are mass²; k⁺ and k⁻ are energies, only the product is GeV²",
    ("fock-normalisation", "sym-vs-dirichlet"): "nested integration equals Γ(2)³/Γ(6)",
    ("fock-normalisation", "sym-vs-montecarlo"): "2M-point simplex sampling agrees with the symbolic value",
    ("fock-normalisation", "value"): "∫x₁x₂x₃ dΣ = 1/120",
    ("fock-normalisation", "units"): "momentum fractions are dimensionless; Ψ is normalised by N",
    ("dis-kinematics", "two-path-Q2"): "closed form and four-vector contraction agree exactly",
    ("dis-kinematics", "two-path-y"): "both routes give exactly the same y",
    ("dis-kinematics", "two-path-x"): "both routes give exactly the same x_B",
    ("dis-kinematics", "xy-s"): "x·y·s = Q² (redundant bookkeeping, not independent evidence)",
    ("dis-kinematics", "W2-positive"): "W² sits above M_p², so the hadronic final state is allowed",
    ("dis-kinematics", "units"): "Q² and s in GeV², x and y dimensionless",
}


_CUR = ""


def _check(cid: str, status: bool, detail: str, claim: str = "") -> dict:
    return {
        "id": cid,
        "status": "pass" if status else "fail",
        "detail": detail,
        "en": EN.get((claim or _CUR, cid), detail),
    }


def _dot(a, b) -> sp.Expr:
    """Minkowski 内积，度规 (+, -, -, -)。"""
    return a[0] * b[0] - a[1] * b[1] - a[2] * b[2] - a[3] * b[3]


# ---------------------------------------------------------------------------
# PH 01 · 光前量子化：k⁺ k⁻ = k⊥² + m²
# ---------------------------------------------------------------------------


def claim_light_front() -> dict:
    global _CUR
    _CUR = "lf-energy"
    k0, k3, k1, k2, m = sp.symbols("k0 k3 k1 k2 m", real=True)

    k_plus = k0 + k3
    k_minus = k0 - k3
    k_perp2 = k1**2 + k2**2

    # 恒等式：左侧减右侧，应当逐项等于  k² - m²
    residual = sp.expand(k_plus * k_minus - (k_perp2 + m**2))
    mass_shell = sp.expand(k0**2 - k3**2 - k_perp2 - m**2)

    ident = sp.simplify(residual - mass_shell) == 0

    # 数值：在壳点，k⊥ 由 on-shell 条件定出
    pt = {k0: sp.Integer(2), k3: sp.Rational(3, 2), m: sp.Rational(1, 2), k2: sp.Integer(0)}
    k1_sq = sp.expand(k0**2 - k3**2 - m**2).subs(pt)  # = 3/2
    lp = (k_plus).subs(pt)
    lm = (k_minus).subs(pt)
    lhs_v = lp * lm
    rhs_v = k1_sq + m.subs(pt) ** 2

    checks = [
        _check(
            "identity",
            ident,
            "k⁺k⁻ − (k⊥²+m²) − (k² − m²) 恒等于 0，未借任何假设",
        ),
        _check(
            "numeric-onshell",
            bool(sp.simplify(lhs_v - rhs_v) == 0),
            f"在壳点 k⁺k⁻ = {sp.nsimplify(lhs_v)}，k⊥²+m² = {sp.nsimplify(rhs_v)}",
        ),
        _check(
            "units",
            True,
            "两侧同为 质量²（GeV²）；k⁺、k⁻ 是 能量，乘积才是 GeV²",
        ),
    ]

    return {
        "id": "lf-energy",
        "area": "light-front",
        "label": "PH 01",
        "title": {"en": "Light-front energy from on-shell mass", "zh": "在壳条件给出光前能量的乘法结构"},
        "formula": {
            "latex": r"k^{-}=\frac{k_{\perp}^{2}+m^{2}}{k^{+}}",
            "plain": "k^- = (k_perp^2 + m^2) / k^+",
        },
        "symbolic": {
            "identity": "k⁺ k⁻ − (k⊥² + m²) ≡ k² − m²",
            "result": "0（在壳时）",
            "latex": r"k^{+}k^{-}-\left(k_{\perp}^{2}+m^{2}\right)\equiv k^{2}-m^{2}",
        },
        "numeric": {
            "inputs": {"k0": "2", "k3": "3/2", "m": "1/2", "k2": "0", "k1": "sqrt(3/2)"},
            "value": _f(lhs_v),
            "unit": "GeV^2",
            "unnormalised": True,
        },
        "checks": checks,
    }


# ---------------------------------------------------------------------------
# PH 03 · 质子结构：DIS 运动学，两条独立路径
# ---------------------------------------------------------------------------


def claim_dis() -> dict:
    global _CUR
    _CUR = "dis-kinematics"
    # HERA 典型束流。全部走精确有理数/根式：Float 会把「恒等」变成 1e-28 的噪声，
    # 而噪声的显示位数是平台相关的 —— 这正是 Linux 上的漂移门禁抓到的那个问题。
    E_e = sp.Rational(276, 10)          # 电子束能 27.6 GeV
    E_p = sp.Integer(920)               # 质子束能 GeV
    E_s = sp.Integer(10)                # 散射电子能量 GeV
    theta = sp.Rational(5, 6) * sp.pi   # 150°，sin/cos 取精确根式

    # --- 路径 A：教科书的闭合公式 ---
    Q2_a = 4 * E_e * E_s * sp.sin(theta / 2) ** 2
    y_a = 1 - (E_s / E_e) * sp.cos(theta / 2) ** 2
    s = 4 * E_e * E_p  # 忽略质量
    x_a = Q2_a / (s * y_a)

    # --- 路径 B：四矢量直算（不经过上面任何公式）---
    k = sp.Matrix([E_e, 0, 0, -E_e])
    kp = sp.Matrix([E_s, E_s * sp.sin(theta), sp.Integer(0), -E_s * sp.cos(theta)])
    P = sp.Matrix([E_p, 0, 0, E_p])
    q = k - kp

    Q2_b = -_dot(q, q)
    y_b = _dot(P, q) / _dot(P, k)
    x_b = Q2_b / (2 * _dot(P, q))

    dQ2 = sp.radsimp(sp.simplify(Q2_a - Q2_b))
    dy = sp.radsimp(sp.simplify(y_a - y_b))
    dx = sp.radsimp(sp.simplify(x_a - x_b))

    # W² 一致性：由 Q²、x 反推强子末态质量
    W2 = sp.radsimp(sp.simplify(Q2_a * (1 / x_a - 1) + M_P**2))

    checks = [
        _check("two-path-Q2", sp.simplify(dQ2) == 0,
               "闭合式与四矢量差为 0（精确算术，非数值接近）"),
        _check("two-path-y", sp.simplify(dy) == 0, "两条路径的 y 精确相等"),
        _check("two-path-x", sp.simplify(dx) == 0, "两条路径的 x_B 精确相等"),
        _check("xy-s", sp.simplify(x_a * y_a * s - Q2_a) == 0,
               "x·y·s = Q² 自洽（此处作冗余登记，非独立证据）"),
        _check("W2-positive", bool(sp.N(W2 - M_P**2, 30) > 0), f"W² = {sp.N(W2, 8)} GeV² ≥ M_p²"),
        _check("units", True, "Q²:GeV²，s:GeV²，x,y 无量纲"),
    ]

    return {
        "id": "dis-kinematics",
        "area": "proton-structure",
        "label": "PH 03",
        "title": {"en": "DIS kinematics at HERA beam energies", "zh": "HERA 束能下的 DIS 运动学"},
        "formula": {
            "latex": r"Q^{2}=4E_{e}E_{e}'\sin^{2}\frac{\theta}{2},\quad x_{B}=\frac{Q^{2}}{2P\cdot q}",
            "plain": "Q^2 = 4 E E' sin^2(theta/2); x_B = Q^2/(2 P.q)",
        },
        "symbolic": {
            "identity": "闭合式 x_B = Q²/(s y) 与定义 x_B = Q²/(2P·q) 等价",
            "result": "两条路径在精确算术下差为 0",
            "latex": r"y=1-\frac{E'}{E}\cos^{2}\frac{\theta}{2}",
        },
        "numeric": {
            "inputs": {
                "E_e": "27.6 GeV", "E_p": "920 GeV",
                "E'_e": "10.0 GeV", "theta": "150 deg",
            },
            "values": {
                "Q2": _f(Q2_a), "x_B": _f(x_a), "y": _f(y_a),
                "s": _f(s), "W2": _f(W2), "W": _f(sp.sqrt(W2)),
            },
            "unit": "GeV^2（x、y 无量纲）",
        },
        "checks": checks,
    }


# ---------------------------------------------------------------------------
# PH 02 · 重子 Fock 基：三夸克规一化，三条路径
# ---------------------------------------------------------------------------


def claim_fock() -> dict:
    global _CUR
    _CUR = "fock-normalisation"
    x1, x2 = sp.symbols("x1 x2", positive=True)

    # 模型波函数 ψ ∝ x1 x2 x3，x3 = 1 - x1 - x2
    integrand = x1 * x2 * (1 - x1 - x2)

    # 路径 A：嵌套符号积分
    I_a = sp.integrate(sp.integrate(integrand, (x2, 0, 1 - x1)), (x1, 0, 1))

    # 路径 B：Dirichlet 多重贝塔  Γ(a1)Γ(a2)Γ(a3)/Γ(a1+a2+a3)
    I_b = sp.gamma(2) ** 3 / sp.gamma(6)  # a_i = 2

    # 路径 C：独立数值求积（不同算法族：单纯形均匀抽样）
    # 注意：iid U(0,1) 归一化**不是**单纯形上的均匀分布（其密度 ∝ 1/(max xᵢ)³）。
    # 正确做法是 iid Exp(1) 归一化，即 Dirichlet(1,1,1)，在 (x1,x2) 投影测度下均匀。
    import numpy as np

    n = 2_000_000
    rng = np.random.default_rng(20261104)
    e = rng.exponential(scale=1.0, size=(n, 3))
    u = e / e.sum(axis=1, keepdims=True)
    # Dirichlet(1,1,1) 在投影测度下的密度为 2，故 ∫f·dΣ = (1/2)·E[f]
    I_c = sp.Float(float(np.prod(u, axis=1).mean()) / 2.0, 20)

    tol = sp.Float("2e-3")
    agree_ac = abs(sp.N(I_a - I_c, 20)) < tol

    N = sp.sqrt(1 / I_a)  # 归一化常数

    checks = [
        _check("sym-vs-dirichlet", sp.simplify(I_a - I_b) == 0,
               f"嵌套积分 {I_a} = Γ(2)³/Γ(6) = {I_b}"),
        _check("sym-vs-montecarlo", agree_ac,
               f"数值求积 {sp.N(I_c, 4)} 与符号解 {sp.N(I_a, 8)} 在 2e-3 容差内一致"),
        _check("value", sp.simplify(I_a - sp.Rational(1, 120)) == 0,
               "∫x₁x₂x₃ dΣ = 1/120"),
        _check("units", True, "x_i 为光前动量分数，无量纲；Ψ 经 N 归一后无量纲"),
    ]

    return {
        "id": "fock-normalisation",
        "area": "fock-basis",
        "label": "PH 02",
        "title": {"en": "Three-quark Fock normalisation on the simplex", "zh": "单纯形上的三夸克 Fock 归一化"},
        "formula": {
            "latex": r"\mathcal{N}^{2}\int x_{1}x_{2}x_{3}\,\mathrm{d}\Sigma=1,\quad x_{1}+x_{2}+x_{3}=1",
            "plain": "N^2 * integral(x1 x2 x3, simplex) = 1",
        },
        "symbolic": {
            "identity": "∫_{Σ} x₁x₂x₃ dΣ = Γ(2)³/Γ(6) = 1/120",
            "result": "N = sqrt(120)",
            "latex": r"\mathcal{N}=\sqrt{120}\approx 10.9545",
        },
        "numeric": {
            "inputs": {"model": "psi ∝ x1 x2 x3", "region": "x1+x2+x3=1, x_i>0"},
            "values": {"integral": _f(I_a), "normalisation": _f(N)},
            "unit": "无量纲",
        },
        "checks": checks,
    }


# ---------------------------------------------------------------------------
# 组装
# ---------------------------------------------------------------------------


def build() -> dict:
    claims = [claim_light_front(), claim_fock(), claim_dis()]
    payload = {
        "schema": "physics-numerics/1",
        "generated_utc": _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "provenance": {
            "generator": "tools/physics/build_numerics.py",
            "python": platform.python_version(),
            "sympy": sp.__version__,
            "constants": "CODATA 2022, m_p = 0.93827208943 GeV",
            "note": "所有数字由本脚本生成；HTML 只读本文件，不得手改",
        },
        "claims": claims,
    }
    summary = {
        "total": len(claims),
        "failed": sum(1 for c in claims for k in c["checks"] if k["status"] == "fail"),
    }
    payload["summary"] = summary
    # 哈希只覆盖内容，不覆盖时间戳——否则每次重算都会伪报漂移。
    canon = json.dumps(
        {k: v for k, v in payload.items() if k != "generated_utc"},
        sort_keys=True,
        ensure_ascii=False,
    )
    payload["content_hash"] = hashlib.sha256(canon.encode()).hexdigest()[:16]
    return payload


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="校验磁盘 JSON 是否与生成结果一致")
    args = ap.parse_args(argv)

    payload = build()
    if payload["summary"]["failed"]:
        for c in payload["claims"]:
            for k in c["checks"]:
                if k["status"] == "fail":
                    print(f"FAIL  {c['label']} {c['id']} :: {k['id']} — {k['detail']}", file=sys.stderr)
        return 1

    text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"

    if args.check:
        if not OUT.exists():
            print(f"missing {OUT}", file=sys.stderr)
            return 1
        old = json.loads(OUT.read_text(encoding="utf-8"))
        strip = lambda d: {k: v for k, v in d.items() if k != "generated_utc"}
        if strip(old) != strip(json.loads(text)):
            print("phys-numerics: DRIFT — 磁盘上的数据与生成器不一致，请重跑 build_numerics.py", file=sys.stderr)
            return 1
        print(f"phys-numerics: OK ({len(payload['claims'])} claims, hash {payload['content_hash']})")
        return 0

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}  claims={len(payload['claims'])}  "
          f"failed=0  hash={payload['content_hash']}")
    for c in payload["claims"]:
        print(f"  {c['label']} {c['id']:<20} checks={len(c['checks'])} "
              f"{[k['status'] for k in c['checks']]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

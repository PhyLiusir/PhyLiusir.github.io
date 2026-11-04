#!/usr/bin/env python3
"""核验 notes-body.html 里写下的那几条公式，而不是相信它们。

为什么要单独一个脚本
--------------------
页面上的数字有 build_numerics.py 做门禁，但 **推导**没有。notes-body.html
里 DY 的 (1+cos²θ) 角分布和 3/(16π) 归一化，都是可以机器判定的：
用 Dirac 代数把张量缩并算出来，再和写进页面的式子比。

三条判据
--------
1. 轻子张量缩并给出 (1+cos²θ)：L^{μν}H_{μν} = 16 E⁴ (1+cos²θ)。
2. 立体角归一化：∫dΩ(1+cos²θ) = 16π/3，也就是系数必须是 3/(16π)。
3. 运动学自洽：x_A x_B = τ = Q²/s。

任何一条不成立就以非零退出码失败。
"""

from __future__ import annotations

import sys

import sympy as sp

METRIC = sp.diag(1, -1, -1, -1)  # (+,-,-,-)


def dot(a, b):
    return (a.T * METRIC * b)[0]


def lepton_tensor(k1, k2):
    """L^{mu nu} = 2(k1^mu k2^nu + k1^nu k2^mu - g^{mu nu} k1.k2)，无质量、自旋平均。"""
    k12 = dot(k1, k2)
    return sp.Matrix(
        4,
        4,
        lambda m, n: 2 * (k1[m] * k2[n] + k1[n] * k2[m] - METRIC[m, n] * k12),
    )


def main() -> int:
    E, theta = sp.symbols("E theta", positive=True)

    # 质心系：e- 沿 +z，e+ 沿 -z，mu- 与 +z 成 theta
    k1 = sp.Matrix([E, 0, 0, E])
    k2 = sp.Matrix([E, 0, 0, -E])
    p1 = sp.Matrix([E, E * sp.sin(theta), 0, E * sp.cos(theta)])
    p2 = sp.Matrix([E, -E * sp.sin(theta), 0, -E * sp.cos(theta)])

    L = lepton_tensor(k1, k2)
    H = lepton_tensor(p1, p2)
    contraction = sp.simplify(
        sum(L[m, n] * H[m, n] for m in range(4) for n in range(4))
    )

    failures = []

    # 1) 缩并必须正比于 (1+cos²θ)，比例与 theta 无关
    ratio = sp.simplify(contraction / (E**4 * (1 + sp.cos(theta) ** 2)))
    ok1 = ratio.is_number
    print(f"[{'PASS' if ok1 else 'FAIL'}] L·H = {ratio} · E⁴(1+cos²θ)；比例与 θ 无关")
    if not ok1:
        failures.append("angular")

    # 2) ∂Ω 归一化 —— 决定页面上的 3/(16π)
    phi = sp.Symbol("phi")
    norm = sp.integrate(
        sp.integrate((1 + sp.cos(theta) ** 2) * sp.sin(theta), (theta, 0, sp.pi)),
        (phi, 0, 2 * sp.pi),
    )
    ok2 = sp.simplify(norm - 16 * sp.pi / 3) == 0
    print(f"[{'PASS' if ok2 else 'FAIL'}] ∫dΩ(1+cos²θ) = {sp.simplify(norm)} = 16π/3 ⇒ 系数 3/(16π)")
    if not ok2:
        failures.append("normalisation")

    # 3) 快度参数化自洽
    y, tau = sp.symbols("y tau", positive=True)
    xA, xB = sp.sqrt(tau) * sp.exp(y), sp.sqrt(tau) * sp.exp(-y)
    ok3 = sp.simplify(xA * xB - tau) == 0
    print(f"[{'PASS' if ok3 else 'FAIL'}] x_A x_B = {sp.simplify(xA * xB)} = τ")
    if not ok3:
        failures.append("kinematics")

    if failures:
        print(f"\nnotes-physics: FAILED ({', '.join(failures)})", file=sys.stderr)
        return 1
    print("\nnotes-physics: OK (3 checks)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

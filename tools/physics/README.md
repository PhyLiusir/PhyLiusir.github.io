# Physics page: symbolic + numeric

The physics notes page used to be prose only. It now carries, for each of the three
research areas, one worked equation together with the numbers that equation produces —
and every number is generated, cross-checked and drift-gated.

This directory is the **only** source of those numbers.

## Why it is built this way

| Premise | Consequence |
|---|---|
| A hand-typed number drifts from its code, and the drift is silent | numbers are generated here, never typed into HTML |
| One formula written two ways is not independent evidence | every quantity is computed along two different algorithm families |
| Symbolic equality cannot see the difference between L and L² | every result carries a unit and its assumptions |
| A number without provenance is an assertion | the JSON records the sympy version, the generator and a content hash |

## Pipeline

```
tools/physics/build_numerics.py   →  assets/physics-data.json   (values + machine checks)
tools/physics/render_section.mjs  →  notes.html                 (KaTeX, rendered at build time)
```

`notes.html` only reads the generated HTML between `<!-- phys:<id> -->` markers.
Do not edit those blocks by hand — the next render overwrites them.

## Reproduce

```bash
pip install "sympy==1.14.0" numpy
npm ci

python tools/physics/build_numerics.py     # regenerate the data
node  tools/physics/render_section.mjs     # regenerate the HTML blocks

python tools/physics/build_numerics.py --check    # drift gate
node  tools/physics/render_section.mjs --check    # drift gate
```

The `verify` job in `.github/workflows/pages.yml` runs both `--check` commands, so a
deploy cannot ship numbers that disagree with the generator.

## What is on the page

| Claim | Area | Symbolic content | Numeric content |
|---|---|---|---|
| `lf-energy` | light-front quantization | k⁺k⁻ − (k⊥²+m²) ≡ k² − m², an identity with no assumptions | on-shell point, both sides 7/4 |
| `fock-normalisation` | baryon Fock expansion | ∫x₁x₂x₃ dΣ = Γ(2)³/Γ(6) = 1/120, 𝒩 = √120 | 2M-point simplex sampling agrees to 2e-3 |
| `dis-kinematics` | proton structure | x_B = Q²/(2P·q) vs. the closed form Q²/(s y) | HERA beams: Q², x, y, s, W |

The two DIS routes are a closed-form formula and a direct four-vector contraction.
The Fock integral is cross-checked against the Dirichlet formula and against a
Monte-Carlo estimate. Those are different algorithm families, not different spellings
of the same one.

## Note on the client

KaTeX runs **at build time**. The page ships plain HTML, `katex.min.css` and woff2
fonts — no JavaScript, no CDN, no external request. The equations therefore also
render with JS disabled, and they stay indexable as text.

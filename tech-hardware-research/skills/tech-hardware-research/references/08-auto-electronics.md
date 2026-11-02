# 08 · Automotive electronics

More content per vehicle, times rising penetration. Qualification is long. The bar is the automotive spec.

## Tracks

| Track | Products and content |
| --- | --- |
| Power semiconductors | IGBT and SiC MOSFET. About 2,000–5,000 yuan per vehicle. The electrification core |
| ADAS | Compute, cameras, radar, domain controllers. L3 and above is tens of thousands of yuan per vehicle |
| Cockpit | Cockpit silicon, center display, HUD, audio. Penetration rising quickly |
| Sensors | Cameras, millimeter-wave radar, lidar, pressure sensors |
| Connectors and harnesses | High-voltage and high-speed. Content per vehicle is rising |

## What to study

| Point | Content |
| --- | --- |
| Penetration | Battery-electric vehicles, L2/L3, lidar |
| Design wins | The chain takes 2–3 years to qualify. The design win is the signal |
| Price | New products such as SiC often fall 10–20% a year. Volume has to cover the decline |
| Domestic substitution | Automotive semiconductor localization still has room |

## The trap

Reliability is extreme (AEC-Q100). A consumer-electronics supplier does not become an automotive supplier in one step. Do not extrapolate.

`[extension]` The usual misuse is a press release ("entering automotive") treated as revenue. From sample, to AEC-Q100, to a design win, to SOP, is usually 2–3 years, and many names drop out. Mark the stage. Do not book it as "automotive revenue" in general.

## Revenue skeleton

```
revenue = sum over won programs of (annual volume × content per vehicle × share) × (1 − annual price decline)
```

Inputs:

1. The list of won programs, with SOP dates. This is the hard leading fact.
2. A volume outlook for each program.
3. Content per vehicle, which changes with the generation.
4. The annual price decline (SiC is often 10–20%). Take it out explicitly, or the model is too high.

## Links

- Power semiconductors are a semiconductor link: `03-semiconductor.md`
- No straight-line extrapolation: `11-pitfalls.md`
- Qualification is a barrier: `02-general-framework.md` §2.2

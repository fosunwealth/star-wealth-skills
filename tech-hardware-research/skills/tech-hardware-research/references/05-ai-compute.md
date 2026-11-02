# 05 · AI compute hardware

The largest industrial variable in tech hardware right now. Work from downstream demand backward, and check supply at each layer.

## Four layers

| Layer | What is in it |
| --- | --- |
| Silicon (highest content) | GPUs (NVIDIA, AMD, domestic accelerators), CPUs, HBM |
| Hardware | High-layer PCB and CCL, optical modules (800G/1.6T), connectors, power, liquid cooling, chassis |
| Systems | Server ODMs (FII, Quanta, Wistron, Inventec) and brands (Dell, HPE, Inspur) |
| Buyers | Cloud providers (Microsoft, Google, Amazon, Meta), plus internet, government, and enterprise |

## Three paths, used as checks on each other

| Path | How |
| --- | --- |
| 1. Cloud capex | Microsoft, Google, Amazon, and Meta: the quarterly capex guide, the AI share, and the server volume |
| 2. Silicon | NVIDIA's quarterly data-center revenue, then GPU units, then the optical modules, PCBs, and servers those units require |
| 3. The chain | Optical shipments, PCB orders, ODM build plans, liquid-cooling penetration |

`[extension]` The three paths check each other. Server units implied by cloud capex, GPU units implied by NVIDIA's data-center revenue, and what optical, PCB, and ODM plants are actually building. A gap above 20% is the expectation gap.

## Metrics

| Link | Metric |
| --- | --- |
| GPU | NVIDIA quarterly data-center revenue, lead time, volume date, domestic-chip performance and software |
| HBM | SK hynix, Samsung, and Micron: capacity, yield, price, stack height |
| Optical | 800G units, 1.6T sample and volume dates, price, customer share |
| PCB/CCL | High-layer orders, M8/M9 qualification, capacity adds |
| Liquid cooling | Cold-plate versus immersion penetration, content per server, suppliers |

## Experience and risk

Do not call the top of the AI hardware cycle lightly. The point where it "has already run too far" can be early. Also watch the technology risk: the wrong route can be an exit.

`[extension]` The two sentences point at different objects.

- Industry beta: do not decide the cycle is over from the valuation. Use the change at the margin in the cloud capex guide.
- Single-name alpha: the wrong route (optical generation, cooling form, HBM stack) is an exit. Confirm each name's customer qualification. A good industry is not a good company.

## Links

- HBM and advanced packaging: `03-semiconductor.md`
- Optical is also a communications link: `07-communication.md`
- Quarterly cloud capex: `10-tracking-system.md`
- "Do not call the top" is not a license to extrapolate: `11-pitfalls.md`

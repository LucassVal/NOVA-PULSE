# NovaPulse — Improvements Research (ASUS Vivobook Pro 15 OLED X3500PC)

> Target hardware: **i5-11300H (Tiger Lake)** + **RTX 3050 Laptop 4GB** + **16GB DDR4** + **NVMe SSD** + **15.6" OLED FHD**
> Research date: 2026-06 | Sources cited inline per finding.

This document audits every NovaPulse module against current (2025-2026) best practice and
flags where the V2.4 spec is **correct**, **questionable**, or **missing**. Priority tags:
`[P1]` ship now · `[P2]` worth doing · `[P3]` optional/cosmetic · `[FIX]` current behavior is wrong/myth.

---

## 0. BIGGEST GAP — No OLED Care module  `[P1]` `[NEW]`

The X3500PC ships with an **OLED panel**, but NovaPulse has **zero** burn-in protection.
This is the single highest-value net-new module for this exact laptop.

New module proposal: `modules/oled_care.py`
- **Pixel Shift**: nudge desktop content a few px on a timer (anti static-image burn).
- **Taskbar dimming / auto-hide**: Windows taskbar is the #1 burn-in source (always-on static UI).
  Enforce `Settings > Personalization > Taskbar > Auto-hide` + Dark Mode via registry.
- **Idle pixel-refresh**: dim/refresh after 30 min idle (ASUS OLED Care does exactly this).
- **Reduce static peak brightness** on AC idle.
- Expose all of it as a dedicated **OLED tab** in the dashboard.

Sources: [ASUS OLED Care](https://www.asus.com/content/3-biggest-oled-display-concerns-and-how-asus-resolves-them/) ·
[TFTCentral OLED 2025](https://tftcentral.co.uk/articles/helping-avoid-oled-burn-in-and-flicker-exploring-the-latest-asus-oled-technologies-for-2025) ·
[PCWorld burn-in](https://www.pcworld.com/article/2918628/your-oled-displays-worst-enemy-burn-in-heres-how-to-fight-back.html)

---

## 1. CPU — `cpu_power.py`, `intel_power_control.py`, `core_parking.py`, `advanced_cpu_optimizer.py`

| Finding | Verdict | Action |
|---|---|---|
| Tiger Lake undervolt is **hardware-locked** by Intel (post-Plundervolt). FIVR/voltage offsets blocked. | Spec **correct** | Keep software-only approach. Do **not** advertise undervolt. |
| Software "undervolt" = limit heat via `powercfg PROCTHROTTLEMAX` (85% active / 55% idle). | Spec **correct** | Keep. Frequency stability > intermittent turbo for sustained LLM load. |
| PL1/PL2 lock @ 35-40W via ThrottleStop — **only works if EC/BIOS exposes it**; X3500PC BIOS is sealed. | `[FIX]` | Detect-and-skip gracefully; don't claim success if EC is locked. |
| PROCHOT offset | Usually locked on this BIOS | Mark as "best-effort / may be unavailable". |

Sources: [ThrottleStop Guide 2026](https://www.ultrabookreview.com/31385-the-throttlestop-guide/) ·
[Intel: i5-11300H stuck 3.1GHz](https://community.intel.com/t5/Processors/my-cpu-i5-11300h-stuck-at-3-1-ghz-when-playing-game/m-p/1381405) ·
[XDA PL1/PL2](https://www.xda-developers.com/understading-cpu-pl1-pl2-power-limits/)

---

## 2. RAM — `memory_optimizer.py`, `standby_cleaner.py`  `[FIX]`

| Finding | Verdict | Action |
|---|---|---|
| Spec **Vector 23**: "aggressive RAM compression + PageCombining". | **Questionable** | Benchmarks across 42 configs show **zero measurable gain** forcing compression on **16GB+** systems. Drop the "aggressive" framing; make it opt-in, default OFF. |
| SysMain/SuperFetch disable | `[FIX]` | On 16GB, SysMain is **beneficial** (preloads, standby cache). Do **not** disable it. Only disable on <8GB. |
| Standby cleaner threshold 2GB | OK | Keep, but avoid over-cleaning — standby RAM is **not** "used" RAM and aggressive purges hurt cache hit rate. Raise hysteresis. |
| 60GB static pagefile on NVMe | Spec **correct** | Static (init=max) avoids runtime resize stutter during tensor offload. Keep. |

Sources: [Win11 memory mgmt](https://cyberraiden.wordpress.com/2025/07/27/windows-memory-management-in-the-windows-10-and-windows-11/) ·
[NinjaOne compression](https://www.ninjaone.com/blog/enable-or-disable-memory-compression-in-windows-11/) ·
[LocalLLM 16GB guide](https://www.crawleo.dev/blog/the-best-local-llms-for-16gb-ram-a-developers-optimization-guide)

---

## 3. GPU / CUDA — `cuda_optimizer.py`, `gpu_scheduler.py`  `[P1]`

| Finding | Verdict | Action |
|---|---|---|
| `nvidia-smi -pm 1` (persistent mode) | Spec **correct** | Avoids 3-5s D3 wake overhead per Ollama call. Keep. |
| `nvidia-smi -lgc 1200,1500` synthetic undervolt (clock lock) | Spec **correct** | Best native way to tame the 50W RTX 3050 in a shared chassis. Keep. |
| `-pl 90%` TDP cap | OK | Keep; pair with thermal check. |
| **VRAM is a hard wall at 4GB** — biggest LLM constraint. | Add to UI | Surface real `num_gpu`/`-ngl` offload + context-window (2048) controls in GPU tab. |
| Recommend models for 4GB | Add to UI | TinyLlama 1.1B Q5, SmolLM2 1.7B Q4, Phi-3.5 Mini Q3 (edge). Show "fits/spills" badge from live VRAM. |
| Flash Attention 2 / 8-bit KV cache (vectors 9,10) | Spec **correct** | Enforce in inference layer; surface toggle. |

Sources: [SitePoint low-VRAM LLM](https://www.sitepoint.com/optimizing-local-llms-low-end-hardware-8gb/) ·
[vLLM 4GB guide](https://kumarshivam-66534.medium.com/run-vllm-locally-on-low-vram-budget-laptop-4gb-gpu-in-2025-full-docker-guide-errors-ollama-bf8c498e7dec) ·
[Ollama GPU opt 2026](https://dasroot.net/posts/2026/03/ollama-gpu-optimization-configuration-2026/)

---

## 4. Storage / NVMe — `nvme_manager.py`, `ntfs_optimizer.py`, `advanced_storage_optimizer.py`

| Finding | Verdict | Action |
|---|---|---|
| `fsutil behavior set disablelastaccess 1` | OK | Safe, reduces metadata writes. Keep. |
| **Write caching** ON for everything | `[FIX]` | Evidence: write-cache can cause **latency spikes up to 1500ms** on some NVMe vs 8-35ms without. Make it per-drive + measured, not blanket-on. |
| Native NVMe driver (StorNVMe) registry tweak | `[P2]` `[NEW]` | Win Server 2025-derived behavior reduces latency / raises IOPS — real win for pagefile-heavy LLM I/O. Add as a vector. |
| TRIM / Retrim 12h | Spec **correct** | Keep (NVMe wear from pagefile is negligible). |
| "Never defrag SSD" | Nuance | Retrim via Optimize-Volume is good; classic defrag is not. |
| Contig.exe pagefile contiguity (vector 18) | OK | Keep — sequential > random reads for 60GB pagefile. |

Sources: [MakeUseOf hidden SSD setting](https://www.makeuseof.com/this-hidden-windows-setting-is-slowing-down-your-ssd-heres-the-fix/) ·
[Phison 13 ways](https://phisonblog.com/13-ways-to-optimize-your-ssds-for-windows-11/) ·
[Pureinfotech NVMe tweak](https://pureinfotech.com/windows-11-nvme-registry-tweak-ssd-performance/)

---

## 5. Network — `network_stack_optimizer.py`, `network_qos.py`  `[FIX]`

| Finding | Verdict | Action |
|---|---|---|
| Spec **Vector 16**: `autotuninglevel=experimental` | **Questionable** | Experimental is for **high-latency WAN**, not gaming/local. For loopback LLM (127.0.0.1) it's irrelevant; for general use **`normal` is more stable**. Default to `normal`. |
| Disable Nagle (TCPNoDelay / TCPAckFrequency) | Overstated | Helps **some** games, breaks others (stutter reports). Keep as opt-in, documented caveat — not blanket. |
| MIMO Power Save OFF, Roaming Aggressiveness min | OK | Real wins for local LAN + large weight downloads. Keep. |
| Interrupt moderation OFF on Wi-Fi | OK | Lowers ping jitter; small CPU cost (acceptable, CPU has thermal headroom now). |

Sources: [TheWindowsClub auto-tuning](https://www.thewindowsclub.com/window-auto-tuning-in-windows-10) ·
[TCP auto-tuning best settings](https://tcpoptimizer.net/what-is-tcp-window-auto-tuning/) ·
[PCWorld Nagle](https://www.pcworld.com/article/2460852/nagles-algorithm-the-obscure-router-setting-that-can-hurt-pc-gamers.html)

---

## 6. Security / Privacy — `defender_hardener.py`, `telemetry_blocker.py`, `security_scanner.py`, `extreme_ai_optimizer.py`

| Finding | Verdict | Action |
|---|---|---|
| Spec **Vector 19**: disable VBS + Memory Integrity (HVCI) | Valid but caveat | Real **5-25%** gain, BUT i5-11300H (11th gen) has **MBEC** → HVCI impact already reduced to ~VBS-alone level. Disabling = security tradeoff. Make it an explicit, warned, opt-in toggle, not silent. |
| Disabling Memory Integrity ≠ disabling VBS | `[FIX]` | Must disable **both** or overhead remains. Fix the registry sequence to kill VBS too. |
| Defender LLM exclusion zone (`~/.ollama/models`) | Spec **correct** | ~15% CPU saved during model load. Keep. |
| Port hardening 135/139/445 inbound block | OK | Good default; ensure loopback 127.0.0.1 stays open for MCP. |

Sources: [Tom's HW disable VBS](https://www.tomshardware.com/how-to/disable-vbs-windows-11) ·
[Tom's HW security benchmarks](https://www.tomshardware.com/news/windows-11-gaming-benchmarks-performance-vbs-hvci-security) ·
[Neowin VBS perf](https://www.neowin.net/news/microsofts-vbshvci-still-hurts-windows-11-performance-even-on-latest-versions/)

---

## Summary of changes to feed into the dashboard rework

1. `[P1][NEW]` **OLED Care** module + dedicated tab (burn-in: pixel shift, taskbar dim, idle refresh).
2. `[FIX]` **RAM**: stop forcing aggressive compression / keep SysMain ON @16GB.
3. `[FIX]` **Network**: default autotuning `normal`, Nagle opt-in.
4. `[FIX]` **NVMe**: write-cache per-drive + measured; add StorNVMe native-driver tweak.
5. `[FIX]` **VBS**: disable BOTH VBS+HVCI or none; warned opt-in.
6. `[P1]` **GPU tab**: live VRAM "fits/spills", context + offload controls, model recommender for 4GB.
7. `[P2]` Surface every toggle above per-component in the new multi-tab UI with real state read-back.

# Baofeng UV-5RH Memory Map

A structured [CHIRP](https://chirpmyradio.com/) memory map for the Baofeng UV-5RH:
a transmit "dashboard" of convoy, ham, and PMR channels plus a large
listen-only bank. It ships as a ready-to-load CHIRP image and is generated from a
single script, [`generate.py`](generate.py), so the whole layout is reproducible
and easy to tweak.

> **Transmit only where you are licensed and authorised.** The `500+` bank is
> receive-only by design - airband, marine, weather, and satellite are listen-only.

## Prerequisites

These instructions assume you already have:

- A **Baofeng UV-5RH** and a USB programming cable with its
  [serial driver](https://www.baofengradio.com/pages/download) installed.
- **[CHIRP](https://chirpmyradio.com/)** - see the
  [Beginners Guide](https://chirpmyradio.com/projects/chirp/wiki/Beginners_Guide)
  to install and connect.
- A **one-time frequency-range unlock** applied with the vendor CPS tool, so the
  radio accepts the full transmit/receive ranges used here. Follow
  [`docs/5rm-change-frequency-range.md`](docs/5rm-change-frequency-range.md) and
  select the factory full range (`UHF 400-520 / VHF 136-174 / VHF2 200-260 MHz`).
- **[uv](https://docs.astral.sh/uv/)** - only needed to
  [customise the map](#2-customise-the-memory-map).

## 1. Load the memory map

### What's inside

Memories follow [CHIRP's generic CSV schema](https://chirpmyradio.com/projects/chirp/wiki/CSV_HowTo)
and are laid out in fixed location ranges. Transmit memories use simplex; the
500+ bank is receive-only.

**Transmit**

| Locations | Block | Contents |
| --- | --- | --- |
| `001-010` | Dashboard quick access | Highest-use convoy/fallback channels: PMR + 2m/70cm, toned and open, low/high. |
| `011-100` | Dashboard matrix | Nine channels (3 PMR, 3x70cm, 3x2m), each with 5 tone variants at low power and a high-power duplicate 45 slots higher. |
| `101-276` | PMR446 reserve | 16 PMR channels per tone, in 20-wide blocks: TSQL low `101`, DTCS low `141`, TSQL high `201`, DTCS high `241`. |
| `301-379` | Ham reserve | 2m/70cm tone fallbacks (TSQL high `301`, DTCS high `341`); calling channels excluded. |
| `401-463` | Open squelch | PMR low `401`, PMR high `421`, 70cm `441`, 2m `451`; calling channels marked `CQ`. |

**Listen-only** (`Duplex = off`, receive-only)

| Locations | Service |
| --- | --- |
| `500` | Civil airband (AM stored as FM) |
| `550` / `600` / `650` | Military air, low / mid / high |
| `700` | Marine VHF |
| `730` | NOAA weather |
| `750` | Satellite / ISS / APRS downlinks |
| `770` | PMR446 |
| `790` | EU LPD433 / SRD |
| `860` / `890` | US FRS-GMRS / business |
| `900` | Australia UHF CB |
| `980` | Japan low-power |

**Conventions**

- **Names** are `LABEL TONE`, e.g. `P07 C05`; `OPN` = open squelch, `CQ` = calling
  channel, `... RX` = listen-only. CHIRP caps names at 10 characters.
- **Tones**: CTCSS (`TSQL`) and DCS (`DTCS`). **Power**: Low `2.0W` / High `10W`.
  **Mode**: `FM` / `NFM`. **Step**: `6.25` (PMR) / `12.5` (narrow) / `25` kHz (ham).
- **Comments** are CHIRP-only section labels; the radio itself shows only names.

### Program the radio

The release image already contains the full map - no Python required.

1. Open CHIRP, then **Radio -> Download From Radio** and save a backup of your
   current radio.
2. Download
   [`Baofeng_UV-5RH_master.img`](https://github.com/qqii/baofeng-uv-5rh-radio/releases/download/v0.1.0/Baofeng_UV-5RH_master.img)
   from release `v0.1.0`.
3. **File -> Open** the downloaded image and review the memories.
4. **Radio -> Upload To Radio**.
5. Confirm these radio settings in CHIRP:
   - `Channel A/B display type`: `Name`
   - `Channel A/B work mode`: `Channel`

The factory backup
[`Baofeng_UV-5RH_stock.img`](https://github.com/qqii/baofeng-uv-5rh-radio/releases/download/v0.0.1/Baofeng_UV-5RH_stock.img)
is published on release `v0.0.1` if you need to return to stock.

## 2. Customise the memory map

Change frequencies, tones, names, or layout by editing the generator and
re-importing.

1. Edit [`generate.py`](generate.py) - frequencies, tone sets, power, and the
   per-block base locations are defined as typed constants near the top.
2. Generate the CSV:

   ```shell
   uv run python generate.py
   ```

   This writes `res/Baofeng_UV5RH_master.csv`.
3. In CHIRP, open your radio image or a fresh backup, then **File -> Import** the
   CSV and review the import warnings.
4. Confirm the settings above and **Upload To Radio**.

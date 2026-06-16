# Baofeng UV-5RH Radio

This project generates a CHIRP-compatible memory CSV for programming a Baofeng UV-5RH. It is built around a simple baseline path using committed CHIRP images, plus a tweaking path where `generate.py` is edited and regenerated.

The generated CSV is written to `res/Baofeng_UV5RH_Master.csv`.

## Prerequisites

- Baofeng UV-5RH radio.
- USB programming cable with the correct serial driver installed.
- Windows for the vendor CPS tool.
- `uv` for running the Python generator.
- CHIRP for backing up and programming the radio.
- Local vendor files in `res/`:
  - `5RM Change Frequency Range.pdf`
  - `T6UV Series EN CPS+.exe`

## Radio Preparation

1. Install and open `res/T6UV Series EN CPS+.exe`.
2. Follow the extracted vendor instructions in `docs/5rm-change-frequency-range.md`.
3. In the CPS frequency-range tool, select the factory/full-range option:

   `UHF: 400-520MHz, VHF: 136-174MHz, VHF2: 200-260MHz`

4. Write the range change to the radio.
5. Install CHIRP.
6. In CHIRP, read from the radio and save a backup before changing memories.

## Simple Programming

Use the committed CHIRP images when you want the known baseline without editing the generator:

- `res/Baofeng_UV-5RH_stock.img`: stock backup image.
- `res/Baofeng_UV-5RH_master.img`: programmed master image.

Recommended flow:

1. Open CHIRP.
2. Read from the radio and save your own fresh backup.
3. Open `res/Baofeng_UV-5RH_master.img`.
4. Review the memories and settings.
5. Write the image to the radio.

After writing, check the radio settings in CHIRP:

- `Channel A display type`: `Name`
- `Channel B display type`: `Name`
- `Channel A work mode`: `Channel`
- `Channel B work mode`: `Channel`

The radio does not store CHIRP comments. Use the memory names and the radio's own indicators for on-device context.

## Tweaking The Memory Map

Use this path when changing frequencies, tones, names, comments, or layout:

1. Edit `generate.py`.
2. Generate the CHIRP CSV:

   ```powershell
   uv run python generate.py
   ```

3. In CHIRP, open your radio image or a fresh backup.
4. Import `res/Baofeng_UV5RH_Master.csv`.
5. Review the import warnings and memory layout.
6. Confirm the settings:

   - `Channel A display type`: `Name`
   - `Channel B display type`: `Name`
   - `Channel A work mode`: `Channel`
   - `Channel B work mode`: `Channel`

7. Save a new `.img` and write it to the radio.

## Checks

Run the local quality checks before committing generator changes:

```powershell
ruff format generate.py
ruff check generate.py
pyrefly check
lefthook run pre-commit --force --colors off
```

`res/` is ignored by default because it contains generated files and local vendor assets. The two baseline CHIRP images are intentionally committed.

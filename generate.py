"""Generate a CHIRP-compatible memory CSV for a Baofeng UV-5RH radio."""

from __future__ import annotations

import csv
import logging
from dataclasses import dataclass
from enum import IntEnum, StrEnum
from pathlib import Path
from typing import TYPE_CHECKING, Final, NamedTuple, TypedDict

if TYPE_CHECKING:
    from collections.abc import Sequence

OUTPUT_PATH: Final = Path("Baofeng_UV5RH_Master.csv")
DEFAULT_CTCSS_TENTHS_HZ: Final = 885
DEFAULT_DCS_CODE: Final = 23
MAX_DCS_CODE: Final = 999
MIN_MEMORY_LOCATION: Final = 1
MAX_MEMORY_LOCATION: Final = 999
MAX_CHIRP_NAME_LENGTH: Final = 10
TENTHS_PER_HZ: Final = 10
LOGGER: Final = logging.getLogger(__name__)


class ChirpCsvRow(TypedDict):
    """String values for one row in CHIRP's generic CSV schema."""

    Location: str
    Name: str
    Frequency: str
    Duplex: str
    Offset: str
    Tone: str
    rToneFreq: str
    cToneFreq: str
    DtcsCode: str
    DtcsPolarity: str
    RxDtcsCode: str
    CrossMode: str
    Mode: str
    TStep: str
    Skip: str
    Power: str
    Comment: str
    URCALL: str
    RPT1CALL: str
    RPT2CALL: str
    DVCODE: str


CSV_HEADER: Final[tuple[str, ...]] = tuple(ChirpCsvRow.__annotations__)


class Modulation(StrEnum):
    """CHIRP modulation modes used by the generated memories."""

    FM = "FM"
    NFM = "NFM"


class Power(StrEnum):
    """Supported transmit-power labels and CHIRP output values."""

    LOW = "Low"
    HIGH = "High"

    @property
    def suffix(self) -> str:
        """Return the one-letter name suffix used in memory names."""
        return "L" if self is Power.LOW else "H"

    @property
    def chirp_value(self) -> str:
        """Return the CHIRP CSV value for this power level."""
        return "2.0W" if self is Power.LOW else "10W"


class ToneMode(StrEnum):
    """CHIRP tone mode values used by the generated memories."""

    NONE = ""
    TSQL = "TSQL"
    DTCS = "DTCS"


class CtcssTone(IntEnum):
    """PMR446 CTCSS privacy-code tones represented as tenths of Hz."""

    C01 = 670
    C02 = 719
    C03 = 744
    C04 = 770
    C05 = 797
    C06 = 825
    C07 = 854
    C08 = 885
    C09 = 915
    C10 = 948
    C11 = 974
    C12 = 1_000
    C13 = 1_035
    C14 = 1_072
    C15 = 1_109
    C16 = 1_148
    C17 = 1_188
    C18 = 1_230
    C19 = 1_273
    C20 = 1_318
    C21 = 1_365
    C22 = 1_413
    C23 = 1_462
    C24 = 1_514
    C25 = 1_567
    C26 = 1_622
    C27 = 1_679
    C28 = 1_738
    C29 = 1_799
    C30 = 1_862
    C31 = 1_928
    C32 = 2_035
    C33 = 2_107
    C34 = 2_181
    C35 = 2_257
    C36 = 2_336
    C37 = 2_418
    C38 = 2_503


class DcsCode(IntEnum):
    """Standard DCS privacy codes represented as three-octal-digit integers."""

    D023 = 23
    D025 = 25
    D026 = 26
    D031 = 31
    D032 = 32
    D043 = 43
    D047 = 47
    D051 = 51
    D054 = 54
    D065 = 65
    D071 = 71
    D072 = 72
    D073 = 73
    D074 = 74
    D114 = 114
    D115 = 115
    D116 = 116
    D125 = 125
    D131 = 131
    D132 = 132
    D134 = 134
    D143 = 143
    D152 = 152
    D155 = 155
    D156 = 156
    D162 = 162
    D165 = 165
    D172 = 172
    D174 = 174
    D205 = 205
    D223 = 223
    D226 = 226
    D243 = 243
    D244 = 244
    D245 = 245
    D251 = 251
    D261 = 261
    D263 = 263
    D265 = 265
    D271 = 271
    D306 = 306
    D311 = 311
    D315 = 315
    D331 = 331
    D343 = 343
    D346 = 346
    D351 = 351
    D364 = 364
    D365 = 365
    D371 = 371
    D411 = 411
    D412 = 412
    D413 = 413
    D423 = 423
    D431 = 431
    D432 = 432
    D445 = 445
    D464 = 464
    D465 = 465
    D466 = 466
    D503 = 503
    D506 = 506
    D516 = 516
    D532 = 532
    D546 = 546
    D565 = 565
    D606 = 606
    D612 = 612
    D624 = 624
    D627 = 627
    D631 = 631
    D632 = 632
    D654 = 654
    D662 = 662
    D664 = 664
    D703 = 703
    D712 = 712
    D723 = 723
    D731 = 731
    D732 = 732
    D734 = 734
    D743 = 743
    D754 = 754


class StepHundredthsKHz(IntEnum):
    """Tuning steps represented exactly as hundredths of a kHz."""

    PMR_6_25 = 625
    HAM_25_00 = 2500

    @property
    def chirp_value(self) -> str:
        """Return the CHIRP decimal representation for this tuning step."""
        whole, hundredths = divmod(int(self), 100)
        return f"{whole}.{hundredths:02d}"


class PmrFrequency(IntEnum):
    """PMR446 channels represented exactly in Hz."""

    P01 = 446_006_250
    P02 = 446_018_750
    P03 = 446_031_250
    P04 = 446_043_750
    P05 = 446_056_250
    P06 = 446_068_750
    P07 = 446_081_250
    P08 = 446_093_750
    P09 = 446_106_250
    P10 = 446_118_750
    P11 = 446_131_250
    P12 = 446_143_750
    P13 = 446_156_250
    P14 = 446_168_750
    P15 = 446_181_250
    P16 = 446_193_750


class HamUhfFrequency(IntEnum):
    """70cm amateur channels represented exactly in Hz."""

    A = 433_400_000
    B = 433_425_000
    C = 433_450_000
    D = 433_475_000
    E = 433_500_000
    F = 433_525_000
    G = 433_550_000
    H = 433_575_000


class HamVhfFrequency(IntEnum):
    """2m amateur channels represented exactly in Hz."""

    A = 145_200_000
    B = 145_225_000
    C = 145_250_000
    D = 145_275_000
    E = 145_300_000
    F = 145_325_000
    G = 145_350_000
    H = 145_375_000
    CH_I = 145_400_000
    J = 145_425_000
    K = 145_450_000
    L = 145_475_000
    M = 145_500_000


@dataclass(frozen=True, slots=True, order=True)
class Frequency:
    """An exact radio frequency stored as integer Hz."""

    hz: int

    def __post_init__(self) -> None:
        """Validate the frequency range."""
        if self.hz < 0:
            msg = f"Frequency cannot be negative: {self.hz}"
            raise ValueError(msg)

    @property
    def chirp_value(self) -> str:
        """Return the CHIRP MHz decimal representation."""
        whole_mhz, fractional_hz = divmod(self.hz, 1_000_000)
        return f"{whole_mhz}.{fractional_hz:06d}"


@dataclass(frozen=True, slots=True)
class RadioChannel:
    """A named radio channel with an exact frequency."""

    label: str
    frequency: Frequency


class OpenHamBlock(NamedTuple):
    """A contiguous open-ham memory block with an optional calling-channel label."""

    base_location: int
    channels: tuple[RadioChannel, ...]
    calling_frequency: Frequency
    calling_name: str


@dataclass(frozen=True, slots=True)
class Tone:
    """Tone squelch configuration for a generated memory."""

    label: str
    mode: ToneMode
    ctcss_tone: CtcssTone | None = None
    dcs_code: DcsCode | None = None

    @classmethod
    def ctcss(cls, tone: CtcssTone) -> Tone:
        """Create a CTCSS tone from a typed PMR446 privacy code."""
        return cls(label=tone.name, mode=ToneMode.TSQL, ctcss_tone=tone)

    @classmethod
    def dcs(cls, code: DcsCode) -> Tone:
        """Create a DCS tone from a typed standard privacy code."""
        return cls(label=code.name, mode=ToneMode.DTCS, dcs_code=code)

    @classmethod
    def none(cls) -> Tone:
        """Create an open squelch tone configuration."""
        return cls(label="", mode=ToneMode.NONE)

    def __post_init__(self) -> None:
        """Validate that the tone mode and value fields agree."""
        if self.mode is ToneMode.TSQL:
            if self.ctcss_tone is None or self.dcs_code is not None:
                msg = "TSQL tones require only a CTCSS value"
                raise ValueError(msg)
            if int(self.ctcss_tone) <= 0:
                msg = "CTCSS tones must be positive"
                raise ValueError(msg)
        elif self.mode is ToneMode.DTCS:
            if self.dcs_code is None or self.ctcss_tone is not None:
                msg = "DTCS tones require only a DCS code"
                raise ValueError(msg)
            if not 0 <= self.dcs_code <= MAX_DCS_CODE:
                msg = "DCS codes must fit three CHIRP digits"
                raise ValueError(msg)
        elif self.ctcss_tone is not None or self.dcs_code is not None:
            msg = "Open tones cannot have tone values"
            raise ValueError(msg)

    @property
    def rtone_freq(self) -> str:
        """Return the CHIRP receive tone frequency."""
        tone = self.ctcss_tone
        return format_tenths_hz(int(tone) if tone is not None else DEFAULT_CTCSS_TENTHS_HZ)

    @property
    def ctone_freq(self) -> str:
        """Return the CHIRP transmit tone frequency."""
        tone = self.ctcss_tone
        return format_tenths_hz(int(tone) if tone is not None else DEFAULT_CTCSS_TENTHS_HZ)

    @property
    def dtcs_code(self) -> str:
        """Return the CHIRP DCS code."""
        code = self.dcs_code
        return f"{code if code is not None else DEFAULT_DCS_CODE:03d}"

    @property
    def cross_mode(self) -> str:
        """Return the CHIRP cross-mode value for this tone."""
        return "DTCS->DTCS" if self.mode is ToneMode.DTCS else "Tone->Tone"


@dataclass(frozen=True, slots=True)
class ChannelRecord:
    """A complete typed memory record before CSV serialization."""

    location: int
    name: str
    frequency: Frequency
    tone: Tone
    modulation: Modulation
    step: StepHundredthsKHz
    power: Power

    def __post_init__(self) -> None:
        """Validate CHIRP memory limits."""
        if not MIN_MEMORY_LOCATION <= self.location <= MAX_MEMORY_LOCATION:
            msg = f"Location out of CHIRP memory range: {self.location}"
            raise ValueError(msg)
        if len(self.name) > MAX_CHIRP_NAME_LENGTH:
            msg = f"CHIRP name is too long for location {self.location}: {self.name!r}"
            raise ValueError(msg)

    def to_csv_row(self) -> ChirpCsvRow:
        """Serialize the record to CHIRP's string-only CSV schema."""
        return {
            "Location": str(self.location),
            "Name": self.name,
            "Frequency": self.frequency.chirp_value,
            "Duplex": "",
            "Offset": Frequency(0).chirp_value,
            "Tone": self.tone.mode.value,
            "rToneFreq": self.tone.rtone_freq,
            "cToneFreq": self.tone.ctone_freq,
            "DtcsCode": self.tone.dtcs_code,
            "DtcsPolarity": "NN",
            "RxDtcsCode": self.tone.dtcs_code,
            "CrossMode": self.tone.cross_mode,
            "Mode": self.modulation.value,
            "TStep": self.step.chirp_value,
            "Skip": "",
            "Power": self.power.chirp_value,
            "Comment": "",
            "URCALL": "",
            "RPT1CALL": "",
            "RPT2CALL": "",
            "DVCODE": "",
        }


@dataclass(frozen=True, slots=True)
class ChannelSpec:
    """Reusable channel settings for constructing memory records."""

    channel: RadioChannel
    tone: Tone
    modulation: Modulation
    step: StepHundredthsKHz
    power: Power


@dataclass(frozen=True, slots=True)
class MatrixDefaults:
    """Shared settings for a generated channel matrix."""

    modulation: Modulation
    step: StepHundredthsKHz


def format_tenths_hz(tenths_hz: int) -> str:
    """Format a tone value stored as tenths of Hz."""
    whole, tenths = divmod(tenths_hz, TENTHS_PER_HZ)
    return f"{whole}.{tenths}"


def radio_channel(label: str, frequency: IntEnum) -> RadioChannel:
    """Build a radio channel from a typed frequency enum."""
    return RadioChannel(label, Frequency(int(frequency)))


def pmr_channel(frequency: PmrFrequency) -> RadioChannel:
    """Build a PMR radio channel from its enum value."""
    return radio_channel(frequency.name, frequency)


def ham_uhf_channel(frequency: HamUhfFrequency) -> RadioChannel:
    """Build a 70cm amateur radio channel from its enum value."""
    return radio_channel(f"70{frequency.name}", frequency)


def ham_vhf_channel(frequency: HamVhfFrequency) -> RadioChannel:
    """Build a 2m amateur radio channel from its enum value."""
    channel_suffix = frequency.name.removeprefix("CH_")
    return radio_channel(f"2M{channel_suffix}", frequency)


OPEN_TONE: Final = Tone.none()
TONES_DASH: Final = (
    Tone.ctcss(CtcssTone.C05),
    Tone.ctcss(CtcssTone.C24),
    Tone.dcs(DcsCode.D073),
    Tone.dcs(DcsCode.D134),
)
CTCSS_TONES: Final = (
    Tone.ctcss(CtcssTone.C05),
    Tone.ctcss(CtcssTone.C24),
    Tone.ctcss(CtcssTone.C31),
    Tone.ctcss(CtcssTone.C33),
    Tone.ctcss(CtcssTone.C38),
)
DCS_TONES: Final = (
    Tone.dcs(DcsCode.D073),
    Tone.dcs(DcsCode.D134),
    Tone.dcs(DcsCode.D311),
    Tone.dcs(DcsCode.D503),
    Tone.dcs(DcsCode.D731),
)

PMR_CHANNELS: Final = tuple(pmr_channel(frequency) for frequency in PmrFrequency)
DASHBOARD_PMR_FREQUENCIES: Final = (
    PmrFrequency.P07,
    PmrFrequency.P11,
    PmrFrequency.P13,
)
DASHBOARD_UHF_FREQUENCIES: Final = (
    HamUhfFrequency.B,
    HamUhfFrequency.D,
    HamUhfFrequency.F,
    HamUhfFrequency.G,
    HamUhfFrequency.H,
)
DASHBOARD_VHF_FREQUENCIES: Final = (
    HamVhfFrequency.E,
    HamVhfFrequency.G,
    HamVhfFrequency.K,
)
HAM_UHF_CHANNELS: Final = tuple(ham_uhf_channel(frequency) for frequency in HamUhfFrequency)
HAM_VHF_CHANNELS: Final = tuple(ham_vhf_channel(frequency) for frequency in HamVhfFrequency)
HAM_CHANNELS: Final = (*HAM_UHF_CHANNELS, *HAM_VHF_CHANNELS)
DASHBOARD_PMR_CHANNELS: Final = tuple(
    pmr_channel(frequency) for frequency in DASHBOARD_PMR_FREQUENCIES
)
DASHBOARD_UHF_CHANNELS: Final = tuple(
    ham_uhf_channel(frequency) for frequency in DASHBOARD_UHF_FREQUENCIES
)
DASHBOARD_VHF_CHANNELS: Final = tuple(
    ham_vhf_channel(frequency) for frequency in DASHBOARD_VHF_FREQUENCIES
)

CALLING_70CM: Final = HamUhfFrequency.E
CALLING_2M: Final = HamVhfFrequency.M
CALLING_70CM_FREQUENCY: Final = Frequency(int(CALLING_70CM))
CALLING_2M_FREQUENCY: Final = Frequency(int(CALLING_2M))
CALLING_FREQUENCIES: Final = frozenset((CALLING_70CM_FREQUENCY, CALLING_2M_FREQUENCY))
HAM_SAFE_CHANNELS: Final = tuple(
    channel for channel in HAM_CHANNELS if channel.frequency not in CALLING_FREQUENCIES
)
OPEN_HAM_BLOCKS: Final = (
    OpenHamBlock(501, HAM_UHF_CHANNELS, CALLING_70CM_FREQUENCY, "CQ 70CM H"),
    OpenHamBlock(521, HAM_VHF_CHANNELS, CALLING_2M_FREQUENCY, "CQ 2M H"),
)


def add_record(
    records: list[ChannelRecord],
    location: int,
    spec: ChannelSpec,
) -> None:
    """Append one generated record from a channel spec."""
    tone_part = f" {spec.tone.label}" if spec.tone.label else " OPN"
    name = f"{spec.channel.label}{tone_part} {spec.power.suffix}"
    records.append(
        ChannelRecord(
            location=location,
            name=name,
            frequency=spec.channel.frequency,
            tone=spec.tone,
            modulation=spec.modulation,
            step=spec.step,
            power=spec.power,
        )
    )


def add_dashboard_matrix(
    records: list[ChannelRecord],
    base_location: int,
    channels: Sequence[RadioChannel],
    defaults: MatrixDefaults,
) -> None:
    """Add paired low/high dashboard matrix records."""
    high_power_offset = len(channels) * len(TONES_DASH)
    for channel_index, channel in enumerate(channels):
        for tone_index, tone in enumerate(TONES_DASH):
            location = base_location + channel_index * len(TONES_DASH) + tone_index
            for power, offset in ((Power.LOW, 0), (Power.HIGH, high_power_offset)):
                add_record(
                    records,
                    location + offset,
                    ChannelSpec(
                        channel=channel,
                        tone=tone,
                        modulation=defaults.modulation,
                        step=defaults.step,
                        power=power,
                    ),
                )


def add_open_channels(
    records: list[ChannelRecord],
    base_location: int,
    channels: Sequence[RadioChannel],
    defaults: MatrixDefaults,
    power: Power,
) -> None:
    """Add consecutive open-squelch channels."""
    for channel_index, channel in enumerate(channels):
        add_record(
            records,
            base_location + channel_index,
            ChannelSpec(
                channel=channel,
                tone=OPEN_TONE,
                modulation=defaults.modulation,
                step=defaults.step,
                power=power,
            ),
        )


def add_extended_pmr(
    records: list[ChannelRecord],
    base_zone: int,
    tones: Sequence[Tone],
    power: Power,
) -> None:
    """Add PMR tone blocks in 20-channel zone ranges."""
    for tone_index, tone in enumerate(tones):
        for channel_index, channel in enumerate(PMR_CHANNELS):
            location = base_zone + tone_index * 20 + channel_index + 1
            add_record(
                records,
                location,
                ChannelSpec(
                    channel=channel,
                    tone=tone,
                    modulation=Modulation.NFM,
                    step=StepHundredthsKHz.PMR_6_25,
                    power=power,
                ),
            )


def add_extended_ham(
    records: list[ChannelRecord],
    base_zone: int,
    tones: Sequence[Tone],
) -> None:
    """Add ham tone blocks while omitting calling channels."""
    for tone_index, tone in enumerate(tones):
        for channel_index, channel in enumerate(HAM_SAFE_CHANNELS):
            location = base_zone + tone_index * 20 + channel_index + 1
            add_record(
                records,
                location,
                ChannelSpec(
                    channel=channel,
                    tone=tone,
                    modulation=Modulation.FM,
                    step=StepHundredthsKHz.HAM_25_00,
                    power=Power.HIGH,
                ),
            )


def add_open_ham_records(records: list[ChannelRecord]) -> None:
    """Add open ham channels and mark calling channels explicitly."""
    for block in OPEN_HAM_BLOCKS:
        for channel_index, channel in enumerate(block.channels):
            name = (
                block.calling_name
                if channel.frequency == block.calling_frequency
                else f"{channel.label} OPN H"
            )
            records.append(
                ChannelRecord(
                    location=block.base_location + channel_index,
                    name=name,
                    frequency=channel.frequency,
                    tone=OPEN_TONE,
                    modulation=Modulation.FM,
                    step=StepHundredthsKHz.HAM_25_00,
                    power=Power.HIGH,
                )
            )


def build_records() -> list[ChannelRecord]:
    """Build all radio memories before sorting and CSV serialization."""
    records: list[ChannelRecord] = []

    add_dashboard_matrix(
        records,
        1,
        DASHBOARD_PMR_CHANNELS,
        MatrixDefaults(
            modulation=Modulation.NFM,
            step=StepHundredthsKHz.PMR_6_25,
        ),
    )
    add_dashboard_matrix(
        records,
        25,
        DASHBOARD_UHF_CHANNELS[:3],
        MatrixDefaults(
            modulation=Modulation.FM,
            step=StepHundredthsKHz.HAM_25_00,
        ),
    )
    add_dashboard_matrix(
        records,
        49,
        DASHBOARD_VHF_CHANNELS,
        MatrixDefaults(
            modulation=Modulation.FM,
            step=StepHundredthsKHz.HAM_25_00,
        ),
    )

    add_open_channels(
        records,
        75,
        PMR_CHANNELS,
        MatrixDefaults(
            modulation=Modulation.NFM,
            step=StepHundredthsKHz.PMR_6_25,
        ),
        Power.LOW,
    )
    add_open_channels(
        records,
        91,
        DASHBOARD_UHF_CHANNELS,
        MatrixDefaults(
            modulation=Modulation.FM,
            step=StepHundredthsKHz.HAM_25_00,
        ),
        Power.HIGH,
    )
    add_open_channels(
        records,
        96,
        DASHBOARD_VHF_CHANNELS,
        MatrixDefaults(
            modulation=Modulation.FM,
            step=StepHundredthsKHz.HAM_25_00,
        ),
        Power.HIGH,
    )

    add_extended_pmr(records, 100, CTCSS_TONES, Power.LOW)
    add_extended_pmr(records, 200, DCS_TONES, Power.LOW)
    add_extended_pmr(records, 300, CTCSS_TONES, Power.HIGH)
    add_extended_pmr(records, 400, DCS_TONES, Power.HIGH)
    add_open_ham_records(records)
    add_extended_ham(records, 600, CTCSS_TONES)
    add_extended_ham(records, 700, DCS_TONES)

    validate_records(records)
    return sorted(records, key=lambda record: record.location)


def validate_records(records: Sequence[ChannelRecord]) -> None:
    """Validate cross-record constraints."""
    seen_locations: set[int] = set()
    for record in records:
        if record.location in seen_locations:
            msg = f"Duplicate CHIRP location: {record.location}"
            raise ValueError(msg)
        seen_locations.add(record.location)


def write_csv(records: Sequence[ChannelRecord], path: Path) -> None:
    """Write generated records to a CHIRP CSV file."""
    with path.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_HEADER)
        writer.writeheader()
        writer.writerows(record.to_csv_row() for record in records)


def main() -> None:
    """Generate the CHIRP CSV file."""
    records = build_records()
    write_csv(records, OUTPUT_PATH)
    logging.basicConfig(format="%(message)s", level=logging.INFO)
    LOGGER.info("Success! %s channels successfully compiled.", len(records))


if __name__ == "__main__":
    main()

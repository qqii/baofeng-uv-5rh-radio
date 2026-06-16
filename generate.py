"""Generate a CHIRP-compatible memory CSV for a Baofeng UV-5RH radio."""

from __future__ import annotations

import csv
import logging
from dataclasses import dataclass, replace
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


class Duplex(StrEnum):
    """CHIRP duplex values used by generated memories."""

    SIMPLEX = ""
    RECEIVE_ONLY = "off"


class Power(StrEnum):
    """Supported transmit-power labels and CHIRP output values."""

    LOW = "Low"
    HIGH = "High"

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

    NARROW_12_50 = 1250
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
    """RSGB 70cm amateur FM/DV simplex channels represented exactly in Hz."""

    U272 = 433_400_000
    U274 = 433_425_000
    U276 = 433_450_000
    U278 = 433_475_000
    U280 = 433_500_000
    U282 = 433_525_000
    U284 = 433_550_000
    U286 = 433_575_000


class HamVhfFrequency(IntEnum):
    """RSGB 2m amateur FM/DV simplex channels represented exactly in Hz."""

    V16 = 145_200_000
    V18 = 145_225_000
    V20 = 145_250_000
    V22 = 145_275_000
    V24 = 145_300_000
    V26 = 145_325_000
    V28 = 145_350_000
    V30 = 145_375_000
    V32 = 145_400_000
    V34 = 145_425_000
    V36 = 145_450_000
    V38 = 145_475_000
    V40 = 145_500_000


class AirbandListenFrequency(IntEnum):
    """Upper airband AM listen-only channels represented exactly in Hz."""

    AIR136000 = 136_000_000
    AIR136250 = 136_250_000
    AIR136500 = 136_500_000
    AIR136750 = 136_750_000
    AIR136975 = 136_975_000


class MarineVhfListenFrequency(IntEnum):
    """Marine VHF listen-only channels represented exactly in Hz."""

    M06 = 156_300_000
    M08 = 156_400_000
    M09 = 156_450_000
    M10 = 156_500_000
    M13 = 156_650_000
    M16 = 156_800_000
    M67 = 156_375_000
    M68 = 156_425_000
    M69 = 156_475_000
    M72 = 156_625_000
    M73 = 156_675_000
    M77 = 156_875_000


class WeatherListenFrequency(IntEnum):
    """NOAA weather radio listen-only channels represented exactly in Hz."""

    WX1 = 162_550_000
    WX2 = 162_400_000
    WX3 = 162_475_000
    WX4 = 162_425_000
    WX5 = 162_450_000
    WX6 = 162_500_000
    WX7 = 162_525_000


class SrdListenFrequency(IntEnum):
    """433 MHz SRD/LPD listen-only channels represented exactly in Hz."""

    SRD075 = 433_075_000
    SRD250 = 433_250_000
    SRD800 = 433_800_000
    SRD920 = 433_920_000
    SRD075H = 434_075_000
    SRD300 = 434_300_000
    SRD500 = 434_500_000
    SRD775 = 434_775_000


class SpaceListenFrequency(IntEnum):
    """Amateur satellite and space downlink listen-only channels represented exactly in Hz."""

    ISS_VOICE = 145_800_000
    APRS = 145_825_000
    SAT145950 = 145_950_000
    SAT436500 = 436_500_000


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


class DashboardChannel(NamedTuple):
    """A dashboard channel plus its CHIRP defaults and display band label."""

    channel: RadioChannel
    defaults: MatrixDefaults
    band_label: str


class ListenChannel(NamedTuple):
    """A receive-only memory definition."""

    label: str
    frequency: Frequency
    modulation: Modulation
    step: StepHundredthsKHz


class ListenBlock(NamedTuple):
    """A receive-only memory block."""

    base_location: int
    channels: tuple[ListenChannel, ...]
    section_comment: str = ""
    row_comment: str = ""


class ListenRangeSpec(NamedTuple):
    """Settings for generating a receive-only channel range."""

    prefix: str
    start_hz: int
    count: int
    step_hz: int
    modulation: Modulation
    step: StepHundredthsKHz
    first_channel: int = 1
    width: int = 2


class ListenListSpec(NamedTuple):
    """Settings for generating receive-only channels from exact frequencies."""

    prefix: str
    frequencies_hz: tuple[int, ...]
    modulation: Modulation
    step: StepHundredthsKHz
    first_channel: int = 1
    width: int = 2


class SectionMarker(NamedTuple):
    """A comment placed on the first memory in a logical section."""

    location: int
    comment: str


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
    comment: str = ""
    duplex: Duplex = Duplex.SIMPLEX

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
            "Duplex": self.duplex.value,
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
            "Comment": self.comment,
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


def listen_channel(
    label: str,
    frequency: IntEnum | int,
    modulation: Modulation,
    step: StepHundredthsKHz,
) -> ListenChannel:
    """Build a receive-only channel from a typed frequency enum."""
    return ListenChannel(label, Frequency(int(frequency)), modulation, step)


def listen_range(spec: ListenRangeSpec) -> tuple[ListenChannel, ...]:
    """Build a receive-only channel range using exact integer Hz spacing."""
    return tuple(
        listen_channel(
            f"{spec.prefix}{channel_number:0{spec.width}d} RX",
            spec.start_hz + index * spec.step_hz,
            spec.modulation,
            spec.step,
        )
        for index, channel_number in enumerate(
            range(spec.first_channel, spec.first_channel + spec.count)
        )
    )


def listen_channels(spec: ListenListSpec) -> tuple[ListenChannel, ...]:
    """Build receive-only channels from an exact frequency list."""
    return tuple(
        listen_channel(
            f"{spec.prefix}{channel_number:0{spec.width}d} RX",
            frequency_hz,
            spec.modulation,
            spec.step,
        )
        for channel_number, frequency_hz in enumerate(spec.frequencies_hz, spec.first_channel)
    )


def pmr_channel(frequency: PmrFrequency) -> RadioChannel:
    """Build a PMR radio channel from its enum value."""
    return radio_channel(frequency.name, frequency)


def ham_uhf_channel(frequency: HamUhfFrequency) -> RadioChannel:
    """Build a 70cm amateur radio channel from its enum value."""
    return radio_channel(frequency.name, frequency)


def ham_vhf_channel(frequency: HamVhfFrequency) -> RadioChannel:
    """Build a 2m amateur radio channel from its enum value."""
    return radio_channel(frequency.name, frequency)


OPEN_TONE: Final = Tone.none()
TSQL_TONES: Final = (
    Tone.ctcss(CtcssTone.C05),
    Tone.ctcss(CtcssTone.C24),
)
DTCS_TONES: Final = (
    Tone.dcs(DcsCode.D073),
    Tone.dcs(DcsCode.D134),
)
DASHBOARD_TONES: Final = (*TSQL_TONES, *DTCS_TONES, OPEN_TONE)

PMR_CHANNELS: Final = tuple(pmr_channel(frequency) for frequency in PmrFrequency)
PMR_DEFAULTS: Final = MatrixDefaults(
    modulation=Modulation.NFM,
    step=StepHundredthsKHz.PMR_6_25,
)
HAM_DEFAULTS: Final = MatrixDefaults(
    modulation=Modulation.FM,
    step=StepHundredthsKHz.HAM_25_00,
)

# Dashboard section: 001-010 is quick access; 011-100 is fixed +5/+45 matrix.
DASHBOARD_SPECIAL_BASE: Final = 1
DASHBOARD_MATRIX_BASE: Final = 11
DASHBOARD_BLOCK_STRIDE: Final = 5
DASHBOARD_POWER_OFFSET: Final = 45
DASHBOARD_PMR_FREQUENCIES: Final = (
    PmrFrequency.P07,
    PmrFrequency.P11,
    PmrFrequency.P13,
)
DASHBOARD_UHF_FREQUENCIES: Final = (
    HamUhfFrequency.U274,
    HamUhfFrequency.U278,
    HamUhfFrequency.U282,
)
DASHBOARD_VHF_FREQUENCIES: Final = (
    HamVhfFrequency.V24,
    HamVhfFrequency.V28,
    HamVhfFrequency.V36,
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
DASHBOARD_CHANNELS: Final = (
    *(DashboardChannel(channel, PMR_DEFAULTS, "PMR") for channel in DASHBOARD_PMR_CHANNELS),
    *(DashboardChannel(channel, HAM_DEFAULTS, "70cm") for channel in DASHBOARD_UHF_CHANNELS),
    *(DashboardChannel(channel, HAM_DEFAULTS, "2m") for channel in DASHBOARD_VHF_CHANNELS),
)

# Reserve section: 100s separate use/power; 20s separate tone choices.
PMR_TSQL_LOW_BASE: Final = 101
PMR_DTCS_LOW_BASE: Final = 141
PMR_TSQL_HIGH_BASE: Final = 201
PMR_DTCS_HIGH_BASE: Final = 241

CALLING_70CM: Final = HamUhfFrequency.U280
CALLING_2M: Final = HamVhfFrequency.V40
CALLING_70CM_FREQUENCY: Final = Frequency(int(CALLING_70CM))
CALLING_2M_FREQUENCY: Final = Frequency(int(CALLING_2M))
CALLING_FREQUENCIES: Final = frozenset((CALLING_70CM_FREQUENCY, CALLING_2M_FREQUENCY))
HAM_SAFE_CHANNELS: Final = tuple(
    channel for channel in HAM_CHANNELS if channel.frequency not in CALLING_FREQUENCIES
)

# Ham section: tone fallbacks with calling channels excluded.
HAM_TSQL_HIGH_BASE: Final = 301
HAM_DTCS_HIGH_BASE: Final = 341

# Open section: grouped just before the 500+ receive-only banks.
OPEN_PMR_LOW_BASE: Final = 401
OPEN_PMR_HIGH_BASE: Final = 421
OPEN_UHF_BASE: Final = 441
OPEN_VHF_BASE: Final = 451
OPEN_HAM_BLOCKS: Final = (
    OpenHamBlock(OPEN_UHF_BASE, HAM_UHF_CHANNELS, CALLING_70CM_FREQUENCY, "U280 CQ"),
    OpenHamBlock(OPEN_VHF_BASE, HAM_VHF_CHANNELS, CALLING_2M_FREQUENCY, "V40 CQ"),
)

# Listen-only section: 500+ memories are receive-only and export with Duplex=off.
LISTEN_AIRBAND_BASE: Final = 500
LISTEN_MIL_AIR_LOW_BASE: Final = 550
LISTEN_MIL_AIR_MID_BASE: Final = 600
LISTEN_MIL_AIR_HIGH_BASE: Final = 650
LISTEN_MARINE_BASE: Final = 700
LISTEN_WEATHER_BASE: Final = 730
LISTEN_SPACE_BASE: Final = 750
LISTEN_PMR_BASE: Final = 770
LISTEN_LPD_BASE: Final = 790
LISTEN_US_PERSONAL_BASE: Final = 860
LISTEN_US_BUSINESS_BASE: Final = 890
LISTEN_AU_CB_BASE: Final = 900
LISTEN_JP_LOW_POWER_BASE: Final = 980

WEATHER_FREQUENCIES_HZ: Final = (
    161_650_000,
    161_750_000,
    161_775_000,
    162_000_000,
    int(WeatherListenFrequency.WX2),
    int(WeatherListenFrequency.WX4),
    int(WeatherListenFrequency.WX5),
    int(WeatherListenFrequency.WX3),
    int(WeatherListenFrequency.WX6),
    int(WeatherListenFrequency.WX7),
    int(WeatherListenFrequency.WX1),
    163_275_000,
)
SPACE_FREQUENCIES_HZ: Final = (
    137_100_000,
    137_620_000,
    137_912_500,
    int(SpaceListenFrequency.ISS_VOICE),
    int(SpaceListenFrequency.APRS),
    int(SpaceListenFrequency.SAT145950),
    145_975_000,
    int(SpaceListenFrequency.SAT436500),
    437_100_000,
    437_500_000,
    437_800_000,
    437_975_000,
    250_550_000,
    255_550_000,
)
FRS_GMRS_FREQUENCIES_HZ: Final = (
    462_562_500,
    462_587_500,
    462_612_500,
    462_637_500,
    462_662_500,
    462_687_500,
    462_712_500,
    467_562_500,
    467_587_500,
    467_612_500,
    467_637_500,
    467_662_500,
    467_687_500,
    467_712_500,
    462_550_000,
    462_575_000,
    462_600_000,
    462_625_000,
    462_650_000,
    462_675_000,
    462_700_000,
    462_725_000,
    467_550_000,
    467_575_000,
    467_600_000,
    467_625_000,
    467_650_000,
    467_675_000,
    467_700_000,
    467_725_000,
)
US_BUSINESS_FREQUENCIES_HZ: Final = (
    151_820_000,
    151_880_000,
    151_940_000,
    154_570_000,
    154_600_000,
    464_500_000,
    464_550_000,
    467_850_000,
    467_875_000,
    467_900_000,
)
JAPAN_LOW_POWER_FREQUENCIES_HZ: Final = (
    *tuple(422_050_000 + index * 12_500 for index in range(11)),
    *tuple(422_200_000 + index * 12_500 for index in range(9)),
)
LISTEN_BLOCKS: Final = (
    ListenBlock(
        LISTEN_AIRBAND_BASE,
        listen_range(
            ListenRangeSpec(
                prefix="AIR",
                start_hz=136_000_000,
                count=40,
                step_hz=25_000,
                modulation=Modulation.FM,
                step=StepHundredthsKHz.HAM_25_00,
                width=3,
            )
        ),
        "Listen only: civil airband AM service stored as FM",
        "",
    ),
    ListenBlock(
        LISTEN_MIL_AIR_LOW_BASE,
        listen_range(
            ListenRangeSpec(
                prefix="MIL",
                start_hz=225_000_000,
                count=50,
                step_hz=250_000,
                modulation=Modulation.FM,
                step=StepHundredthsKHz.HAM_25_00,
                width=3,
            )
        ),
        "Listen only: military air AM service stored as FM",
        "",
    ),
    ListenBlock(
        LISTEN_MIL_AIR_MID_BASE,
        listen_range(
            ListenRangeSpec(
                prefix="MIL",
                start_hz=237_500_000,
                count=50,
                step_hz=250_000,
                modulation=Modulation.FM,
                step=StepHundredthsKHz.HAM_25_00,
                first_channel=51,
                width=3,
            )
        ),
        "Listen only: military air AM service stored as FM",
        "",
    ),
    ListenBlock(
        LISTEN_MIL_AIR_HIGH_BASE,
        listen_range(
            ListenRangeSpec(
                prefix="MIL",
                start_hz=250_000_000,
                count=40,
                step_hz=250_000,
                modulation=Modulation.FM,
                step=StepHundredthsKHz.HAM_25_00,
                first_channel=101,
                width=3,
            )
        ),
        "Listen only: military air AM service stored as FM",
        "",
    ),
    ListenBlock(
        LISTEN_MARINE_BASE,
        listen_range(
            ListenRangeSpec(
                prefix="MAR",
                start_hz=156_050_000,
                count=28,
                step_hz=50_000,
                modulation=Modulation.FM,
                step=StepHundredthsKHz.HAM_25_00,
            )
        ),
        "Listen only: marine VHF safety and working channels",
        "",
    ),
    ListenBlock(
        LISTEN_WEATHER_BASE,
        listen_channels(
            ListenListSpec(
                prefix="WX",
                frequencies_hz=WEATHER_FREQUENCIES_HZ,
                modulation=Modulation.FM,
                step=StepHundredthsKHz.HAM_25_00,
            )
        ),
        "Listen only: North America weather broadcasts",
        "",
    ),
    ListenBlock(
        LISTEN_SPACE_BASE,
        listen_channels(
            ListenListSpec(
                prefix="SAT",
                frequencies_hz=SPACE_FREQUENCIES_HZ,
                modulation=Modulation.FM,
                step=StepHundredthsKHz.HAM_25_00,
            )
        ),
        "Listen only: satellite and ISS/APRS downlink candidates",
        "",
    ),
    ListenBlock(
        LISTEN_PMR_BASE,
        tuple(
            listen_channel(
                f"PMR{index:02d} RX",
                frequency,
                Modulation.NFM,
                StepHundredthsKHz.PMR_6_25,
            )
            for index, frequency in enumerate(PmrFrequency, 1)
        ),
        "",
        "",
    ),
    ListenBlock(
        LISTEN_LPD_BASE,
        listen_range(
            ListenRangeSpec(
                prefix="LPD",
                start_hz=433_075_000,
                count=69,
                step_hz=25_000,
                modulation=Modulation.NFM,
                step=StepHundredthsKHz.NARROW_12_50,
            )
        ),
        "Listen only: EU LPD433/SRD devices and sensors",
        "",
    ),
    ListenBlock(
        LISTEN_US_PERSONAL_BASE,
        listen_channels(
            ListenListSpec(
                prefix="US",
                frequencies_hz=FRS_GMRS_FREQUENCIES_HZ,
                modulation=Modulation.NFM,
                step=StepHundredthsKHz.NARROW_12_50,
            )
        ),
        "",
        "",
    ),
    ListenBlock(
        LISTEN_US_BUSINESS_BASE,
        listen_channels(
            ListenListSpec(
                prefix="USB",
                frequencies_hz=US_BUSINESS_FREQUENCIES_HZ,
                modulation=Modulation.NFM,
                step=StepHundredthsKHz.NARROW_12_50,
            )
        ),
        "",
        "",
    ),
    ListenBlock(
        LISTEN_AU_CB_BASE,
        listen_range(
            ListenRangeSpec(
                prefix="AUC",
                start_hz=476_425_000,
                count=80,
                step_hz=12_500,
                modulation=Modulation.NFM,
                step=StepHundredthsKHz.NARROW_12_50,
                width=3,
            )
        ),
        "",
        "",
    ),
    ListenBlock(
        LISTEN_JP_LOW_POWER_BASE,
        listen_channels(
            ListenListSpec(
                prefix="JP",
                frequencies_hz=JAPAN_LOW_POWER_FREQUENCIES_HZ,
                modulation=Modulation.NFM,
                step=StepHundredthsKHz.NARROW_12_50,
            )
        ),
        "",
        "",
    ),
)


def add_record(
    records: list[ChannelRecord],
    location: int,
    spec: ChannelSpec,
) -> None:
    """Append one generated record from a channel spec."""
    tone_label = spec.tone.label or "OPN"
    name = f"{spec.channel.label} {tone_label}"
    if len(name) > MAX_CHIRP_NAME_LENGTH and spec.tone.mode is ToneMode.DTCS:
        name = f"{spec.channel.label} {tone_label[1:]}"
    if len(name) > MAX_CHIRP_NAME_LENGTH:
        name = f"{spec.channel.label}{tone_label}"
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


def add_dashboard_quick_access(records: list[ChannelRecord]) -> None:
    """Add the special first ten high-utility memories."""
    quick_specs = (
        (DASHBOARD_SPECIAL_BASE, DASHBOARD_PMR_CHANNELS[0], TSQL_TONES[0], PMR_DEFAULTS, Power.LOW),
        (
            DASHBOARD_SPECIAL_BASE + 1,
            DASHBOARD_PMR_CHANNELS[0],
            DTCS_TONES[0],
            PMR_DEFAULTS,
            Power.LOW,
        ),
        (
            DASHBOARD_SPECIAL_BASE + 2,
            DASHBOARD_PMR_CHANNELS[1],
            TSQL_TONES[0],
            PMR_DEFAULTS,
            Power.LOW,
        ),
        (
            DASHBOARD_SPECIAL_BASE + 3,
            DASHBOARD_PMR_CHANNELS[2],
            TSQL_TONES[0],
            PMR_DEFAULTS,
            Power.LOW,
        ),
        (
            DASHBOARD_SPECIAL_BASE + 4,
            DASHBOARD_UHF_CHANNELS[0],
            TSQL_TONES[0],
            HAM_DEFAULTS,
            Power.LOW,
        ),
        (
            DASHBOARD_SPECIAL_BASE + 5,
            DASHBOARD_VHF_CHANNELS[0],
            TSQL_TONES[0],
            HAM_DEFAULTS,
            Power.LOW,
        ),
        (
            DASHBOARD_SPECIAL_BASE + 6,
            DASHBOARD_PMR_CHANNELS[0],
            OPEN_TONE,
            PMR_DEFAULTS,
            Power.LOW,
        ),
        (
            DASHBOARD_SPECIAL_BASE + 7,
            DASHBOARD_PMR_CHANNELS[0],
            OPEN_TONE,
            PMR_DEFAULTS,
            Power.HIGH,
        ),
        (
            DASHBOARD_SPECIAL_BASE + 8,
            DASHBOARD_PMR_CHANNELS[0],
            TSQL_TONES[0],
            PMR_DEFAULTS,
            Power.HIGH,
        ),
        (
            DASHBOARD_SPECIAL_BASE + 9,
            DASHBOARD_PMR_CHANNELS[0],
            DTCS_TONES[0],
            PMR_DEFAULTS,
            Power.HIGH,
        ),
    )
    for location, channel, tone, defaults, power in quick_specs:
        add_record(
            records,
            location,
            ChannelSpec(
                channel=channel,
                tone=tone,
                modulation=defaults.modulation,
                step=defaults.step,
                power=power,
            ),
        )


def add_dashboard_matrix(
    records: list[ChannelRecord],
    base_location: int,
    channels: Sequence[DashboardChannel],
) -> None:
    """Add paired low/high dashboard matrix records."""
    for channel_index, dashboard_channel in enumerate(channels):
        location = base_location + channel_index * DASHBOARD_BLOCK_STRIDE
        for tone_index, tone in enumerate(DASHBOARD_TONES):
            for power, offset in ((Power.LOW, 0), (Power.HIGH, DASHBOARD_POWER_OFFSET)):
                add_record(
                    records,
                    location + tone_index + offset,
                    ChannelSpec(
                        channel=dashboard_channel.channel,
                        tone=tone,
                        modulation=dashboard_channel.defaults.modulation,
                        step=dashboard_channel.defaults.step,
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
    base_location: int,
    tones: Sequence[Tone],
    power: Power,
) -> None:
    """Add PMR tone blocks in 20-channel zone ranges."""
    for tone_index, tone in enumerate(tones):
        for channel_index, channel in enumerate(PMR_CHANNELS):
            location = base_location + tone_index * 20 + channel_index
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
    base_location: int,
    tones: Sequence[Tone],
) -> None:
    """Add ham tone blocks while omitting calling channels."""
    for tone_index, tone in enumerate(tones):
        for channel_index, channel in enumerate(HAM_SAFE_CHANNELS):
            location = base_location + tone_index * 20 + channel_index
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
                else f"{channel.label} OPN"
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


def add_listen_records(records: list[ChannelRecord]) -> None:
    """Add receive-only listen memories."""
    for block in LISTEN_BLOCKS:
        for channel_index, channel in enumerate(block.channels):
            records.append(
                ChannelRecord(
                    location=block.base_location + channel_index,
                    name=channel.label,
                    frequency=channel.frequency,
                    tone=OPEN_TONE,
                    modulation=channel.modulation,
                    step=channel.step,
                    power=Power.LOW,
                    comment=block.row_comment,
                    duplex=Duplex.RECEIVE_ONLY,
                )
            )


def dashboard_section_markers() -> tuple[SectionMarker, ...]:
    """Build comments for each active dashboard block."""
    markers = [
        SectionMarker(
            DASHBOARD_SPECIAL_BASE,
            "Quick defaults: toned convoy channels",
        ),
        SectionMarker(
            DASHBOARD_SPECIAL_BASE + 5,
            "Quick fallbacks: 2m default, P07 open/high",
        ),
    ]
    tone_names = "/".join(tone.label or "OPN" for tone in DASHBOARD_TONES)
    for channel_index, dashboard_channel in enumerate(DASHBOARD_CHANNELS):
        low_start = DASHBOARD_MATRIX_BASE + channel_index * DASHBOARD_BLOCK_STRIDE
        high_start = low_start + DASHBOARD_POWER_OFFSET
        for start, power in ((low_start, Power.LOW), (high_start, Power.HIGH)):
            markers.append(
                SectionMarker(
                    start,
                    (
                        f"Dashboard {dashboard_channel.band_label} {dashboard_channel.channel.label} "
                        f"{power.value.lower()}: {tone_names}"
                    ),
                )
            )
    return tuple(markers)


def pmr_tone_section_markers(
    base_location: int,
    tones: Sequence[Tone],
    power: Power,
) -> tuple[SectionMarker, ...]:
    """Build comments for PMR reserve tone blocks."""
    markers: list[SectionMarker] = []
    for tone_index, tone in enumerate(tones):
        start = base_location + tone_index * 20
        markers.append(
            SectionMarker(
                start,
                (f"PMR {power.value.lower()} reserve {tone.mode.value} {tone.label}"),
            )
        )
    return tuple(markers)


def ham_tone_section_markers(
    base_location: int,
    tones: Sequence[Tone],
) -> tuple[SectionMarker, ...]:
    """Build comments for ham reserve tone blocks."""
    markers: list[SectionMarker] = []
    for tone_index, tone in enumerate(tones):
        start = base_location + tone_index * 20
        markers.append(
            SectionMarker(
                start,
                (f"Ham high reserve {tone.mode.value} {tone.label}; calling channels excluded"),
            )
        )
    return tuple(markers)


def listen_section_markers() -> tuple[SectionMarker, ...]:
    """Build comments for receive-only listen blocks."""
    return tuple(
        SectionMarker(block.base_location, block.section_comment)
        for block in LISTEN_BLOCKS
        if block.section_comment
    )


SECTION_MARKERS: Final = (
    *dashboard_section_markers(),
    SectionMarker(OPEN_PMR_LOW_BASE, "Open PMR low"),
    SectionMarker(OPEN_PMR_HIGH_BASE, "Open PMR high"),
    SectionMarker(OPEN_UHF_BASE, "Open 70cm high; calling channel marked CQ"),
    SectionMarker(OPEN_VHF_BASE, "Open 2m high; calling channel marked CQ"),
    *pmr_tone_section_markers(PMR_TSQL_LOW_BASE, TSQL_TONES, Power.LOW),
    *pmr_tone_section_markers(PMR_DTCS_LOW_BASE, DTCS_TONES, Power.LOW),
    *pmr_tone_section_markers(PMR_TSQL_HIGH_BASE, TSQL_TONES, Power.HIGH),
    *pmr_tone_section_markers(PMR_DTCS_HIGH_BASE, DTCS_TONES, Power.HIGH),
    *ham_tone_section_markers(HAM_TSQL_HIGH_BASE, TSQL_TONES),
    *ham_tone_section_markers(HAM_DTCS_HIGH_BASE, DTCS_TONES),
    *listen_section_markers(),
)


def build_records() -> list[ChannelRecord]:
    """Build all radio memories before sorting and CSV serialization."""
    records: list[ChannelRecord] = []

    add_dashboard_quick_access(records)
    add_dashboard_matrix(
        records,
        DASHBOARD_MATRIX_BASE,
        DASHBOARD_CHANNELS,
    )

    add_open_channels(
        records,
        OPEN_PMR_LOW_BASE,
        PMR_CHANNELS,
        PMR_DEFAULTS,
        Power.LOW,
    )
    add_open_channels(
        records,
        OPEN_PMR_HIGH_BASE,
        PMR_CHANNELS,
        PMR_DEFAULTS,
        Power.HIGH,
    )
    add_open_ham_records(records)

    add_extended_pmr(records, PMR_TSQL_LOW_BASE, TSQL_TONES, Power.LOW)
    add_extended_pmr(records, PMR_DTCS_LOW_BASE, DTCS_TONES, Power.LOW)
    add_extended_pmr(records, PMR_TSQL_HIGH_BASE, TSQL_TONES, Power.HIGH)
    add_extended_pmr(records, PMR_DTCS_HIGH_BASE, DTCS_TONES, Power.HIGH)
    add_extended_ham(records, HAM_TSQL_HIGH_BASE, TSQL_TONES)
    add_extended_ham(records, HAM_DTCS_HIGH_BASE, DTCS_TONES)
    add_listen_records(records)

    annotated_records = add_section_comments(records)
    validate_records(annotated_records)
    return sorted(annotated_records, key=lambda record: record.location)


def add_section_comments(records: Sequence[ChannelRecord]) -> list[ChannelRecord]:
    """Add section comments to the first memory in each logical range."""
    comments_by_location = {marker.location: marker.comment for marker in SECTION_MARKERS}
    annotated_records: list[ChannelRecord] = []
    for record in records:
        section_comment = comments_by_location.get(record.location)
        if section_comment is None:
            comment = record.comment
        elif record.comment:
            comment = f"{section_comment}; {record.comment}"
        else:
            comment = section_comment
        annotated_records.append(replace(record, comment=comment))
    return annotated_records


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

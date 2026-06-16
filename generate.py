"""Generate a CHIRP-compatible memory CSV for a Baofeng UV-5RH radio."""

from __future__ import annotations

import csv
import logging
from dataclasses import dataclass
from enum import IntEnum, StrEnum
from pathlib import Path
from typing import TYPE_CHECKING, Final, TypedDict

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


class DashboardUhfFrequency(IntEnum):
    """UHF dashboard channels represented exactly in Hz."""

    A = 433_425_000
    B = 433_450_000
    C = 433_475_000
    D = 433_500_000
    E = 433_525_000


class DashboardVhfFrequency(IntEnum):
    """VHF dashboard channels represented exactly in Hz."""

    A = 145_225_000
    B = 145_250_000
    C = 145_475_000


class OpenVhfFrequency(IntEnum):
    """Open VHF dashboard channels represented exactly in Hz."""

    A = 145_225_000
    B = 145_250_000
    C = 145_275_000


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


@dataclass(frozen=True, slots=True)
class Tone:
    """Tone squelch configuration for a generated memory."""

    label: str
    mode: ToneMode
    ctcss_tenths_hz: int | None = None
    dcs_code: int | None = None

    @classmethod
    def ctcss(cls, label: str, tenths_hz: int) -> Tone:
        """Create a CTCSS tone from tenths of Hz."""
        return cls(label=label, mode=ToneMode.TSQL, ctcss_tenths_hz=tenths_hz)

    @classmethod
    def dcs(cls, label: str, code: int) -> Tone:
        """Create a DCS tone from a three-digit code."""
        return cls(label=label, mode=ToneMode.DTCS, dcs_code=code)

    @classmethod
    def none(cls) -> Tone:
        """Create an open squelch tone configuration."""
        return cls(label="", mode=ToneMode.NONE)

    def __post_init__(self) -> None:
        """Validate that the tone mode and value fields agree."""
        if self.mode is ToneMode.TSQL:
            if self.ctcss_tenths_hz is None or self.dcs_code is not None:
                msg = "TSQL tones require only a CTCSS value"
                raise ValueError(msg)
            if self.ctcss_tenths_hz <= 0:
                msg = "CTCSS tones must be positive"
                raise ValueError(msg)
        elif self.mode is ToneMode.DTCS:
            if self.dcs_code is None or self.ctcss_tenths_hz is not None:
                msg = "DTCS tones require only a DCS code"
                raise ValueError(msg)
            if not 0 <= self.dcs_code <= MAX_DCS_CODE:
                msg = "DCS codes must fit three CHIRP digits"
                raise ValueError(msg)
        elif self.ctcss_tenths_hz is not None or self.dcs_code is not None:
            msg = "Open tones cannot have tone values"
            raise ValueError(msg)

    @property
    def rtone_freq(self) -> str:
        """Return the CHIRP receive tone frequency."""
        tone = self.ctcss_tenths_hz
        return format_tenths_hz(tone if tone is not None else DEFAULT_CTCSS_TENTHS_HZ)

    @property
    def ctone_freq(self) -> str:
        """Return the CHIRP transmit tone frequency."""
        tone = self.ctcss_tenths_hz
        return format_tenths_hz(tone if tone is not None else DEFAULT_CTCSS_TENTHS_HZ)

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


def pmr_channel(frequency: PmrFrequency) -> RadioChannel:
    """Build a PMR radio channel from its enum value."""
    return RadioChannel(frequency.name, Frequency(int(frequency)))


def dashboard_uhf_channel(frequency: DashboardUhfFrequency) -> RadioChannel:
    """Build a dashboard UHF radio channel from its enum value."""
    return RadioChannel(f"70{frequency.name}", Frequency(int(frequency)))


def dashboard_vhf_channel(frequency: DashboardVhfFrequency) -> RadioChannel:
    """Build a dashboard VHF radio channel from its enum value."""
    return RadioChannel(f"2M{frequency.name}", Frequency(int(frequency)))


def open_vhf_channel(frequency: OpenVhfFrequency) -> RadioChannel:
    """Build an open dashboard VHF radio channel from its enum value."""
    return RadioChannel(f"2M{frequency.name}", Frequency(int(frequency)))


def ham_uhf_channel(frequency: HamUhfFrequency) -> RadioChannel:
    """Build a 70cm amateur radio channel from its enum value."""
    return RadioChannel(f"70{frequency.name}", Frequency(int(frequency)))


def ham_vhf_channel(frequency: HamVhfFrequency) -> RadioChannel:
    """Build a 2m amateur radio channel from its enum value."""
    channel_suffix = frequency.name.removeprefix("CH_")
    return RadioChannel(f"2M{channel_suffix}", Frequency(int(frequency)))


OPEN_TONE: Final = Tone.none()
TONES_DASH: Final = (
    Tone.ctcss("C05", 797),
    Tone.ctcss("C24", 1514),
    Tone.dcs("D073", 73),
    Tone.dcs("D134", 134),
)
CTCSS_TONES: Final = (
    Tone.ctcss("C05", 797),
    Tone.ctcss("C24", 1514),
    Tone.ctcss("C31", 1928),
    Tone.ctcss("C33", 2107),
    Tone.ctcss("C38", 2503),
)
DCS_TONES: Final = (
    Tone.dcs("D073", 73),
    Tone.dcs("D134", 134),
    Tone.dcs("D311", 311),
    Tone.dcs("D503", 503),
    Tone.dcs("D731", 731),
)

PMR_CHANNELS: Final = tuple(pmr_channel(frequency) for frequency in PmrFrequency)
DASHBOARD_PMR_CHANNELS: Final = (
    pmr_channel(PmrFrequency.P05),
    pmr_channel(PmrFrequency.P10),
    pmr_channel(PmrFrequency.P15),
)
DASHBOARD_UHF_CHANNELS: Final = tuple(
    dashboard_uhf_channel(frequency) for frequency in DashboardUhfFrequency
)
DASHBOARD_VHF_CHANNELS: Final = tuple(
    dashboard_vhf_channel(frequency) for frequency in DashboardVhfFrequency
)
DASHBOARD_VHF_OPEN_CHANNELS: Final = tuple(
    open_vhf_channel(frequency) for frequency in OpenVhfFrequency
)
HAM_UHF_CHANNELS: Final = tuple(ham_uhf_channel(frequency) for frequency in HamUhfFrequency)
HAM_VHF_CHANNELS: Final = tuple(ham_vhf_channel(frequency) for frequency in HamVhfFrequency)

CALLING_70CM: Final = Frequency(433_500_000)
CALLING_2M: Final = Frequency(145_500_000)


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
            low_spec = ChannelSpec(
                channel=channel,
                tone=tone,
                modulation=defaults.modulation,
                step=defaults.step,
                power=Power.LOW,
            )
            high_spec = ChannelSpec(
                channel=channel,
                tone=tone,
                modulation=defaults.modulation,
                step=defaults.step,
                power=Power.HIGH,
            )
            add_record(records, location, low_spec)
            add_record(
                records,
                location + high_power_offset,
                high_spec,
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
    ham_safe_channels = tuple(
        channel
        for channel in (*HAM_UHF_CHANNELS, *HAM_VHF_CHANNELS)
        if channel.frequency not in {CALLING_70CM, CALLING_2M}
    )
    for tone_index, tone in enumerate(tones):
        for channel_index, channel in enumerate(ham_safe_channels):
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
    for channel_index, channel in enumerate(HAM_UHF_CHANNELS):
        name = "CQ 70CM H" if channel.frequency == CALLING_70CM else f"{channel.label} OPN H"
        records.append(
            ChannelRecord(
                location=501 + channel_index,
                name=name,
                frequency=channel.frequency,
                tone=OPEN_TONE,
                modulation=Modulation.FM,
                step=StepHundredthsKHz.HAM_25_00,
                power=Power.HIGH,
            )
        )

    for channel_index, channel in enumerate(HAM_VHF_CHANNELS):
        name = "CQ 2M H" if channel.frequency == CALLING_2M else f"{channel.label} OPN H"
        records.append(
            ChannelRecord(
                location=521 + channel_index,
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

    for channel_index, channel in enumerate(PMR_CHANNELS):
        add_record(
            records,
            75 + channel_index,
            ChannelSpec(
                channel=channel,
                tone=OPEN_TONE,
                modulation=Modulation.NFM,
                step=StepHundredthsKHz.PMR_6_25,
                power=Power.LOW,
            ),
        )
    for channel_index, channel in enumerate(DASHBOARD_UHF_CHANNELS):
        add_record(
            records,
            91 + channel_index,
            ChannelSpec(
                channel=channel,
                tone=OPEN_TONE,
                modulation=Modulation.FM,
                step=StepHundredthsKHz.HAM_25_00,
                power=Power.HIGH,
            ),
        )
    for channel_index, channel in enumerate(DASHBOARD_VHF_OPEN_CHANNELS):
        add_record(
            records,
            96 + channel_index,
            ChannelSpec(
                channel=channel,
                tone=OPEN_TONE,
                modulation=Modulation.FM,
                step=StepHundredthsKHz.HAM_25_00,
                power=Power.HIGH,
            ),
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

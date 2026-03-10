from __future__ import annotations

import json
from dataclasses import asdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from native_game.runtime import project_root

if TYPE_CHECKING:
    from .app import RunSummary

HISTORY_VERSION = 1
MAX_HISTORY_RECORDS = 30


@dataclass(frozen=True)
class PersistedRunRecord:
    timestamp: str
    lineup_label: str
    result_label: str
    stage_label: str
    stage_number: int
    total_rounds: int
    total_blue_damage: int
    total_red_damage: int
    total_blue_kills: int
    total_red_kills: int
    best_reward_line: str

    @property
    def was_success(self) -> bool:
        return self.result_label == "원정 성공"

    def ranking_key(self) -> tuple[int, int, int, int, int]:
        return (
            1 if self.was_success else 0,
            self.stage_number,
            self.total_blue_kills,
            self.total_blue_damage - self.total_red_damage,
            -self.total_rounds,
        )

    @classmethod
    def from_summary(cls, summary: RunSummary, *, stage_number: int) -> PersistedRunRecord:
        return cls(
            timestamp=datetime.now().isoformat(timespec="seconds"),
            lineup_label=summary.lineup_label,
            result_label=summary.result_label,
            stage_label=summary.stage_label,
            stage_number=stage_number,
            total_rounds=summary.total_rounds,
            total_blue_damage=summary.total_blue_damage,
            total_red_damage=summary.total_red_damage,
            total_blue_kills=summary.total_blue_kills,
            total_red_kills=summary.total_red_kills,
            best_reward_line=summary.best_reward_line,
        )


@dataclass(frozen=True)
class HistorySummary:
    overview_lines: list[str]
    comparison_lines: list[str]


class RunHistoryStore:
    def __init__(self, path: Path | None, records: list[PersistedRunRecord] | None = None) -> None:
        self.path = path
        self.records = records or []

    @staticmethod
    def default_path() -> Path:
        return project_root() / ".local" / "native_tactics_history.json"

    @classmethod
    def load(cls, path: Path | None = None) -> RunHistoryStore:
        if path is None:
            return cls(None, [])
        resolved_path = path
        if not resolved_path.exists():
            return cls(resolved_path, [])
        try:
            payload = json.loads(resolved_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return cls(resolved_path, [])
        if payload.get("version") != HISTORY_VERSION:
            return cls(resolved_path, [])
        records = [
            PersistedRunRecord(**record)
            for record in payload.get("records", [])
            if isinstance(record, dict)
        ]
        return cls(resolved_path, records)

    def save(self) -> None:
        if self.path is None:
            return
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "version": HISTORY_VERSION,
                "records": [asdict(record) for record in self.records[:MAX_HISTORY_RECORDS]],
            }
            self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError:
            return

    def best_overall(self) -> PersistedRunRecord | None:
        if not self.records:
            return None
        return max(self.records, key=lambda record: record.ranking_key())

    def best_for_lineup(self, lineup_label: str) -> PersistedRunRecord | None:
        lineup_records = [record for record in self.records if record.lineup_label == lineup_label]
        if not lineup_records:
            return None
        return max(lineup_records, key=lambda record: record.ranking_key())

    def clear_count(self) -> int:
        return sum(1 for record in self.records if record.was_success)

    def record_summary(self, summary: RunSummary, *, stage_number: int) -> HistorySummary:
        previous_overall = self.best_overall()
        previous_lineup_best = self.best_for_lineup(summary.lineup_label)
        current = PersistedRunRecord.from_summary(summary, stage_number=stage_number)
        self.records = [current, *self.records][:MAX_HISTORY_RECORDS]
        self.save()
        return HistorySummary(
            overview_lines=self._overview_lines(current),
            comparison_lines=self._comparison_lines(current, previous_overall, previous_lineup_best),
        )

    def _overview_lines(self, current: PersistedRunRecord) -> list[str]:
        overall_best = self.best_overall()
        lineup_best = self.best_for_lineup(current.lineup_label)
        lines = [
            f"저장 기록 {len(self.records)}런 · 완주 {self.clear_count()}회",
        ]
        if overall_best is not None:
            lines.append(f"전체 최고 · {overall_best.stage_label} · {overall_best.lineup_label}")
        else:
            lines.append("전체 최고 · 아직 기록 없음")
        if lineup_best is not None:
            lines.append(f"현재 조합 최고 · {lineup_best.stage_label} · 피해 {lineup_best.total_blue_damage}")
        else:
            lines.append("현재 조합 최고 · 아직 기록 없음")
        return lines

    def _comparison_lines(
        self,
        current: PersistedRunRecord,
        previous_overall: PersistedRunRecord | None,
        previous_lineup_best: PersistedRunRecord | None,
    ) -> list[str]:
        if previous_overall is None:
            return [
                "첫 원정 기록을 저장했습니다.",
                "이제 다음 런부터 최고 기록과 직접 비교됩니다.",
            ]

        lines: list[str] = []
        if current.ranking_key() > previous_overall.ranking_key():
            lines.append("전체 최고 원정을 경신했습니다.")
        else:
            damage_gap = current.total_blue_damage - previous_overall.total_blue_damage
            defense_gap = previous_overall.total_red_damage - current.total_red_damage
            lines.append(
                f"전체 최고 대비 · 피해 {damage_gap:+d} · 받은 피해 절감 {defense_gap:+d}"
            )

        if previous_lineup_best is None:
            lines.append("이 조합의 첫 기록입니다.")
        elif current.ranking_key() > previous_lineup_best.ranking_key():
            lines.append("현재 조합 최고 기록을 경신했습니다.")
        else:
            lineup_damage_gap = current.total_blue_damage - previous_lineup_best.total_blue_damage
            lineup_round_gap = previous_lineup_best.total_rounds - current.total_rounds
            lines.append(
                f"조합 최고 대비 · 피해 {lineup_damage_gap:+d} · 라운드 단축 {lineup_round_gap:+d}"
            )
        return lines[:2]

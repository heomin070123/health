from dataclasses import dataclass, field, asdict
from datetime import datetime
import math
from typing import Any, Callable, Dict, List, Optional


@dataclass
class HealthRecord:
    """건강정보 1건을 나타내는 데이터 모델"""
    record_id: int
    name: str
    height_cm: float
    weight_kg: float
    recorded_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M"))

    @property
    def bmi(self) -> float:
        """BMI 계산: 체중(kg) / (신장(m) ** 2)"""
        if self.height_cm <= 0:
            return 0.0
        height_m = self.height_cm / 100.0
        return round(self.weight_kg / (height_m ** 2), 2)

    @property
    def bmi_status(self) -> str:
        """대한비만학회 기준 간단 분류"""
        val = self.bmi
        if val < 18.5:
            return "저체중"
        elif val < 23.0:
            return "정상"
        elif val < 25.0:
            return "비만 전단계(과체중)"
        elif val < 30.0:
            return "1단계 비만"
        elif val < 35.0:
            return "2단계 비만"
        return "3단계 비만"

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["bmi"] = self.bmi
        data["bmi_status"] = self.bmi_status
        return data


class HealthManager:
    """메모리 상의 HealthRecord 목록을 관리하고 통계를 계산하는 클래스"""

    def __init__(self, records: Optional[List[HealthRecord]] = None) -> None:
        self._records: List[HealthRecord] = []
        self._next_id: int = 1
        if records:
            self.load_records(records)

    def _recalc_next_id(self) -> None:
        if not self._records:
            self._next_id = 1
        else:
            self._next_id = max(r.record_id for r in self._records) + 1

    def load_records(self, records: List[HealthRecord], replace: bool = True) -> int:
        """모듈 1에서 읽어온 HealthRecord 목록을 메모리에 적재"""
        if replace:
            self._records = list(records)
        else:
            existing_ids = {r.record_id for r in self._records}
            for rec in records:
                if rec.record_id in existing_ids:
                    rec.record_id = self._next_id
                    self._next_id += 1
                self._records.append(rec)
        self._recalc_next_id()
        return len(self._records)

    def get_all_records(self) -> List[HealthRecord]:
        """전체 건강정보 목록 반환 (외부 변형 방지를 위해 얕은 복사 리스트 반환)"""
        return list(self._records)

    def add_record(
        self,
        name: str,
        height_cm: float,
        weight_kg: float,
        recorded_at: Optional[str] = None,
    ) -> HealthRecord:
        """건강정보 추가 후 생성된 HealthRecord 반환"""
        if not name.strip():
            raise ValueError("이름은 비워둘 수 없습니다.")
        if height_cm <= 0 or weight_kg <= 0:
            raise ValueError("키와 몸무게는 0보다 커야 합니다.")

        ts = recorded_at.strip() if recorded_at and recorded_at.strip() else datetime.now().strftime("%Y-%m-%d %H:%M")
        record = HealthRecord(
            record_id=self._next_id,
            name=name.strip(),
            height_cm=float(height_cm),
            weight_kg=float(weight_kg),
            recorded_at=ts,
        )
        self._next_id += 1
        self._records.append(record)
        return record

    def get_record_by_id(self, record_id: int) -> Optional[HealthRecord]:
        """ID로 단건 상세 조회"""
        for rec in self._records:
            if rec.record_id == record_id:
                return rec
        return None

    def search_records(self, keyword: str) -> List[HealthRecord]:
        """이름 또는 날짜(문자열)로 검색"""
        key = keyword.strip().lower()
        if not key:
            return []
        return [
            rec
            for rec in self._records
            if key in rec.name.lower() or key in rec.recorded_at.lower()
        ]

    def update_record(
        self,
        record_id: int,
        name: Optional[str] = None,
        height_cm: Optional[float] = None,
        weight_kg: Optional[float] = None,
        recorded_at: Optional[str] = None,
    ) -> Optional[HealthRecord]:
        """지정한 record_id의 건강정보 수정 후 수정된 레코드 반환 (없으면 None)"""
        rec = self.get_record_by_id(record_id)
        if rec is None:
            return None

        if name is not None:
            if not name.strip():
                raise ValueError("이름은 비워둘 수 없습니다.")
            rec.name = name.strip()
        if height_cm is not None:
            if height_cm <= 0:
                raise ValueError("키는 0보다 커야 합니다.")
            rec.height_cm = float(height_cm)
        if weight_kg is not None:
            if weight_kg <= 0:
                raise ValueError("몸무게는 0보다 커야 합니다.")
            rec.weight_kg = float(weight_kg)
        if recorded_at is not None and recorded_at.strip():
            rec.recorded_at = recorded_at.strip()

        return rec

    def delete_record(self, record_id: int) -> bool:
        """지정한 record_id 삭제 성공 여부 반환"""
        for idx, rec in enumerate(self._records):
            if rec.record_id == record_id:
                del self._records[idx]
                return True
        return False

    @staticmethod
    def _mean_and_std(values: List[float], sample: bool = False) -> Dict[str, float]:
        """평균과 표준편차 계산 (표본표준편차 ddof=1 옵션 지원)"""
        n = len(values)
        if n == 0:
            return {"mean": 0.0, "std": 0.0, "min": 0.0, "max": 0.0}

        mean_val = sum(values) / n
        if n == 1 or (sample and n < 2):
            std_val = 0.0
        else:
            denom = (n - 1) if sample else n
            variance = sum((x - mean_val) ** 2 for x in values) / denom
            std_val = math.sqrt(variance)

        return {
            "mean": round(mean_val, 2),
            "std": round(std_val, 2),
            "min": round(min(values), 2),
            "max": round(max(values), 2),
        }

    def get_statistics(self, sample_std: bool = False) -> Dict[str, Any]:
        """전체 레코드 수 및 몸무게, 키, BMI의 평균/표준편차/최소/최대 반환"""
        count = len(self._records)
        if count == 0:
            empty_stat = {"mean": 0.0, "std": 0.0, "min": 0.0, "max": 0.0}
            return {
                "count": 0,
                "weight": dict(empty_stat),
                "height": dict(empty_stat),
                "bmi": dict(empty_stat),
            }

        weights = [r.weight_kg for r in self._records]
        heights = [r.height_cm for r in self._records]
        bmis = [r.bmi for r in self._records]

        return {
            "count": count,
            "weight": self._mean_and_std(weights, sample=sample_std),
            "height": self._mean_and_std(heights, sample=sample_std),
            "bmi": self._mean_and_std(bmis, sample=sample_std),
        }
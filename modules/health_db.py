"""
[AI 활용 내역 명시]
- 사용 AI: Gemini
- 사용 목적: 모듈 1(health_db.py)의 클래스 구조 설계 및 4종 파일(JSON, CSV, TXT, Pickle) 입출력 예외 처리 로직 참고
- 사용 프롬프트: "파이썬 BMI 건강관리 프로젝트의 모듈 1(health_db.py) 요구사항에 맞춰 HealthRecord 클래스와 4가지 파일 포맷 저장/로드 및 검증 코드를 작성해줘."
- 허민(202611851) 작성일: 2026-11-15
"""

import os
import json
import csv
import pickle


class HealthRecord:
    """개인의 신상 정보와 신체 건강 정보(BMI 포함)를 저장하는 데이터 모델 클래스"""

    def __init__(self, record_id, name, birth_year, gender, height, weight, bmi=None, status=None):
        self.id = record_id
        self.name = name
        self.birth_year = int(birth_year)
        self.gender = gender
        self.height = float(height)
        self.weight = float(weight)
        
        # bmi와 status가 전달되지 않은 경우(최초 생성 시) 자동 계산
        if bmi is None or status is None:
            self.bmi, self.status = self.calculate_bmi()
        else:
            self.bmi = float(bmi)
            self.status = status

    def calculate_bmi(self):
        """키(cm)와 몸무게(kg)를 바탕으로 BMI 수치와 비만도 상태를 계산하여 반환"""
        height_m = self.height / 100.0
        bmi_val = round(self.weight / (height_m ** 2), 2)

        if bmi_val < 18.5:
            status_val = "저체중"
        elif bmi_val < 23.0:
            status_val = "정상"
        elif bmi_val < 25.0:
            status_val = "과체중"
        else:
            status_val = "비만"

        return bmi_val, status_val

    def to_dict(self):
        """객체 속성을 딕셔너리 형태로 변환 (JSON, CSV 저장용)"""
        return {
            "id": self.id,
            "name": self.name,
            "birth_year": self.birth_year,
            "gender": self.gender,
            "height": self.height,
            "weight": self.weight,
            "bmi": self.bmi,
            "status": self.status
        }

    @classmethod
    def from_dict(cls, data):
        """딕셔너리 데이터를 받아 HealthRecord 객체로 복원"""
        return cls(
            record_id=data["id"],
            name=data["name"],
            birth_year=int(data["birth_year"]),
            gender=data["gender"],
            height=float(data["height"]),
            weight=float(data["weight"]),
            bmi=float(data["bmi"]),
            status=data["status"]
        )

    def __eq__(self, other):
        """두 HealthRecord 객체의 필드 값이 모두 일치하는지 비교 (검증용)"""
        if not isinstance(other, HealthRecord):
            return False
        return self.to_dict() == other.to_dict()

    def __repr__(self):
        return (f"HealthRecord(id='{self.id}', name='{self.name}', birth_year={self.birth_year}, "
                f"gender='{self.gender}', height={self.height}, weight={self.weight}, "
                f"bmi={self.bmi}, status='{self.status}')")


class HealthDBManager:
    """건강정보 레코드 목록을 관리하고 4가지 파일 형식으로 영구 저장/로드하는 클래스"""

    def __init__(self, data_dir="data"):
        self.records = []
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)

    def generate_id(self):
        """신규 레코드 추가 시 고유한 환자식별번호(예: P2026-0001) 자동 생성"""
        if not self.records:
            return "P2026-0001"
        
        # 기존 ID 중 가장 큰 뒷자리 번호를 찾아 +1
        max_num = 0
        for rec in self.records:
            try:
                num_part = int(rec.id.split("-")[1])
                if num_part > max_num:
                    max_num = num_part
            except (IndexError, ValueError):
                continue
        return f"P2026-{max_num + 1:04d}"

    def add_record(self, name, birth_year, gender, height, weight, record_id=None):
        """새로운 건강정보 레코드를 생성하여 목록에 추가"""
        if record_id is None:
            record_id = self.generate_id()
        new_record = HealthRecord(record_id, name, birth_year, gender, height, weight)
        self.records.append(new_record)
        return new_record

    def display_records(self, record_list=None, title="건강정보 목록"):
        """전달받은 목록(없으면 현재 관리 중인 목록)을 화면에 보기 좋게 출력"""
        target = record_list if record_list is not None else self.records
        print(f"\n--- [{title}] (총 {len(target)}건) ---")
        if not target:
            print("출력할 데이터가 없습니다.")
            return
        for rec in target:
            print(f"[{rec.id}] {rec.name} ({rec.birth_year}년생, {rec.gender}) | "
                  f"키: {rec.height}cm, 몸무게: {rec.weight}kg -> BMI: {rec.bmi} ({rec.status})")

    # 1. JSON 저장 및 로드
    def save_json(self, filename="health_data.json"):
        filepath = os.path.join(self.data_dir, filename)
        try:
            data_list = [rec.to_dict() for rec in self.records]
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data_list, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            print(f"[오류] JSON 저장 실패: {e}")
            return False

    def load_json(self, filename="health_data.json"):
        filepath = os.path.join(self.data_dir, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data_list = json.load(f)
            return [HealthRecord.from_dict(item) for item in data_list]
        except Exception as e:
            print(f"[오류] JSON 로드 실패: {e}")
            return []

    # 2. CSV 저장 및 로드
    def save_csv(self, filename="health_data.csv"):
        filepath = os.path.join(self.data_dir, filename)
        fieldnames = ["id", "name", "birth_year", "gender", "height", "weight", "bmi", "status"]
        try:
            with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for rec in self.records:
                    writer.writerow(rec.to_dict())
            return True
        except Exception as e:
            print(f"[오류] CSV 저장 실패: {e}")
            return False

    def load_csv(self, filename="health_data.csv"):
        filepath = os.path.join(self.data_dir, filename)
        loaded_records = []
        try:
            with open(filepath, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    loaded_records.append(HealthRecord.from_dict(row))
            return loaded_records
        except Exception as e:
            print(f"[오류] CSV 로드 실패: {e}")
            return []

    # 3. TXT 저장 및 로드 (쉼표 구분자 사용)
    def save_txt(self, filename="health_data.txt"):
        filepath = os.path.join(self.data_dir, filename)
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                for rec in self.records:
                    line = f"{rec.id},{rec.name},{rec.birth_year},{rec.gender},{rec.height},{rec.weight},{rec.bmi},{rec.status}\n"
                    f.write(line)
            return True
        except Exception as e:
            print(f"[오류] TXT 저장 실패: {e}")
            return False

    def load_txt(self, filename="health_data.txt"):
        filepath = os.path.join(self.data_dir, filename)
        loaded_records = []
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    parts = line.strip().split(",")
                    if len(parts) == 8:
                        rec = HealthRecord(
                            record_id=parts[0],
                            name=parts[1],
                            birth_year=int(parts[2]),
                            gender=parts[3],
                            height=float(parts[4]),
                            weight=float(parts[5]),
                            bmi=float(parts[6]),
                            status=parts[7]
                        )
                        loaded_records.append(rec)
            return loaded_records
        except Exception as e:
            print(f"[오류] TXT 로드 실패: {e}")
            return []

    # 4. Pickle 저장 및 로드 (이진 직렬화)
    def save_pickle(self, filename="health_data.pkl"):
        filepath = os.path.join(self.data_dir, filename)
        try:
            with open(filepath, "wb") as f:
                pickle.dump(self.records, f)
            return True
        except Exception as e:
            print(f"[오류] Pickle 저장 실패: {e}")
            return False

    def load_pickle(self, filename="health_data.pkl"):
        filepath = os.path.join(self.data_dir, filename)
        try:
            with open(filepath, "rb") as f:
                return pickle.load(f)
        except Exception as e:
            print(f"[오류] Pickle 로드 실패: {e}")
            return []


def main():
    # 1. 관리자 객체 생성 및 임의의 샘플 데이터 입력
    db = HealthDBManager(data_dir="data")
    db.add_record("홍길동", 1995, "남", 175.0, 72.5)
    db.add_record("김영희", 1998, "여", 162.0, 52.0)
    db.add_record("이철수", 2001, "남", 180.5, 60.0)
    db.add_record("박지민", 1992, "여", 165.0, 70.0)

    # 원본 데이터 화면 출력
    db.display_records(title="원본 메모리 데이터")

    # 2. 4가지 파일 형식으로 각각 저장
    print("\n[파일 저장 진행]")
    print("JSON 저장:", "성공" if db.save_json() else "실패")
    print("CSV  저장:", "성공" if db.save_csv() else "실패")
    print("TXT  저장:", "성공" if db.save_txt() else "실패")
    print("PKL  저장:", "성공" if db.save_pickle() else "실패")

    # 3. 저장된 4가지 파일을 각각 읽어와 출력 및 원본과 일치 여부 검증
    formats = [
        ("JSON", db.load_json),
        ("CSV", db.load_csv),
        ("TXT", db.load_txt),
        ("PICKLE", db.load_pickle)
    ]

    for fmt_name, load_func in formats:
        loaded_data = load_func()
        db.display_records(loaded_data, title=f"{fmt_name} 파일에서 읽어온 데이터")
        
        # 원본 리스트(db.records)와 읽어온 리스트(loaded_data) 비교
        is_matched = (db.records == loaded_data)
        print(f"=> {fmt_name} 데이터 원본 일치 검증 결과: {'일치함 (PASS)' if is_matched else '불일치 (FAIL)'}")


if __name__ == "__main__":
    main()
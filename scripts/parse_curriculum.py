"""
TD Bootcamp AI 심화 캠프 커리큘럼 파서
"""

import pandas as pd
import json
from pathlib import Path


def parse_curriculum(file_path):
    """엑셀 파일에서 커리큘럼 정보를 파싱"""

    # 엑셀 파일 읽기
    excel_file = pd.ExcelFile(file_path)

    curriculum_data = {}

    # 모든 시트 처리
    for sheet_name in excel_file.sheet_names:
        df = pd.read_excel(file_path, sheet_name=sheet_name)

        # NaN 값을 None으로 변환
        df = df.where(pd.notnull(df), None)

        # 시트 데이터를 딕셔너리로 변환
        sheet_data = df.to_dict(orient='records')
        curriculum_data[sheet_name] = sheet_data

        print(f"\n=== {sheet_name} ===")
        print(f"컬럼: {list(df.columns)}")
        print(f"행 개수: {len(df)}")

        # 처음 몇 행 출력
        if len(df) > 0:
            print("\n첫 5행:")
            print(df.head())

    return curriculum_data


def extract_tasks(curriculum_data):
    """커리큘럼 데이터에서 작업 목록 추출"""

    tasks = []

    for sheet_name, sheet_data in curriculum_data.items():
        print(f"\n\n=== {sheet_name} 시트 분석 ===")

        # 시트 데이터가 비어있지 않으면 처리
        if sheet_data:
            # 첫 번째 행의 키들을 확인
            if len(sheet_data) > 0:
                sample_keys = list(sheet_data[0].keys())
                print(f"발견된 컬럼들: {sample_keys}")

                # 각 행을 작업으로 변환
                for idx, row in enumerate(sheet_data[:10]):  # 처음 10개만 샘플로
                    print(f"\n행 {idx + 1}:")
                    for key, value in row.items():
                        if value is not None:
                            print(f"  {key}: {value}")

    return tasks


def main():
    """메인 함수"""

    # 엑셀 파일 경로
    excel_path = Path(r"C:\fastmain\[TD _ Bootcamp] AI 심화 캠프_2기_수강생 커리큘럼.xlsx")

    if not excel_path.exists():
        print(f"파일을 찾을 수 없습니다: {excel_path}")
        return

    print(f"파일 읽기: {excel_path}")

    # 커리큘럼 파싱
    curriculum_data = parse_curriculum(excel_path)

    # 작업 추출
    tasks = extract_tasks(curriculum_data)

    # 결과를 JSON으로 저장
    output_path = Path("curriculum_parsed.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(curriculum_data, f, ensure_ascii=False, indent=2, default=str)

    print(f"\n\n파싱 완료! 결과가 {output_path}에 저장되었습니다.")


if __name__ == "__main__":
    main()
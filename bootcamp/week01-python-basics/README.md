# Week 1: Python 기초 프로그래밍

## 📚 학습 목표
- Python 기본 문법 완벽 마스터
- 객체지향 프로그래밍 이해
- 예외처리와 파일 입출력 활용

## 📅 일일 커리큘럼

### Day 1: Python 기본 문법
```python
# 01_variables_and_types.py
# 변수와 자료형
name = "AI Bootcamp"
version = 2.0
is_active = True
students = ["Alice", "Bob", "Charlie"]

# 02_operators.py
# 연산자
result = 10 + 20 * 3
text = "Hello" + " " + "World"
```

### Day 2: 제어문
```python
# 03_conditionals.py
# 조건문
score = 85
if score >= 90:
    grade = "A"
elif score >= 80:
    grade = "B"
else:
    grade = "C"

# 04_loops.py
# 반복문
for i in range(10):
    print(f"Count: {i}")

while True:
    user_input = input("Continue? (y/n): ")
    if user_input.lower() == 'n':
        break
```

### Day 3: 함수와 모듈
```python
# 05_functions.py
def calculate_average(numbers):
    """숫자 리스트의 평균을 계산"""
    return sum(numbers) / len(numbers)

# 06_modules.py
import math
import random
from datetime import datetime
```

### Day 4: 클래스와 OOP
```python
# 07_classes.py
class Student:
    def __init__(self, name, age):
        self.name = name
        self.age = age
        self.grades = []

    def add_grade(self, grade):
        self.grades.append(grade)

    def get_average(self):
        return sum(self.grades) / len(self.grades) if self.grades else 0
```

### Day 5: 예외처리와 파일 I/O
```python
# 08_exception_handling.py
try:
    result = 10 / 0
except ZeroDivisionError:
    print("Cannot divide by zero!")
finally:
    print("Cleanup code")

# 09_file_operations.py
with open("data.txt", "r") as f:
    content = f.read()

with open("output.txt", "w") as f:
    f.write("Hello, World!")
```

## 📝 실습 과제

### 과제 1: 계산기 프로그램
- 사칙연산 지원
- 예외처리 포함
- 연산 기록 저장

### 과제 2: 학생 관리 시스템
- Student 클래스 구현
- 파일 저장/불러오기
- 성적 통계 기능

### 과제 3: 텍스트 분석 도구
- 파일 읽기
- 단어 빈도 분석
- 결과 시각화

## 🔗 참고 자료
- [Python 공식 문서](https://docs.python.org/3/)
- [Python 튜토리얼](https://docs.python.org/3/tutorial/)
- [PEP 8 스타일 가이드](https://www.python.org/dev/peps/pep-0008/)

## ✅ 체크리스트
- [ ] 변수와 자료형 이해
- [ ] 조건문과 반복문 활용
- [ ] 함수 정의와 호출
- [ ] 클래스 설계와 구현
- [ ] 예외처리 적용
- [ ] 파일 입출력 구현
- [ ] 모든 실습 과제 완료
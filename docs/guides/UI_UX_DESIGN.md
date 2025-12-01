# **Paralegal: '차분한 통제(Calm Control)'를 위한 사용자 중심 법률 기술 플랫폼 전략 및 화면 정의 (v2 \- 종합본)**

## Table of Contents
- [Part 1: 비즈니스 및 전략적 기반 분석](#part-1-paralegal-비즈니스-및-전략적-기반-분석)
- [Part 2: 사용자의 심리 상태와 편의성](#part-2-핵심-과제-사용자의-심리-상태와-편의성-해독)
- [Part 3: 'Calm Control' 디자인 철학](#part-3-calm-control-디자인-철학-정립)
- [Part 4: 색상 시스템 설계](#part-4-색상-시스템-설계-차분한-신뢰의-팔레트)
- [Part 5: 타이포그래피 시스템](#part-5-타이포그래피-시스템-명료함과-권위의-균형)
- [Part 6: 핵심 UI 컴포넌트](#part-6-핵심-ui-컴포넌트-정의-상호작용-디자인)
- [Part 7: 구현 및 권장 사항](#part-7-요약-및-단계별-실행을-위한-권장-사항)

---

## **Part 1: 'Paralegal' 비즈니스 및 전략적 기반 분석**

### **1.1. 핵심 비즈니스 분석: AI 기반 이혼 소송 지원 플랫폼**

'Paralegal'은 AI를 기반으로 이혼 소송에 특화된 증거 수집 및 분석 시스템입니다.1 이 플랫폼의 핵심 비즈니스 가치 제안은 이혼 소송 과정에서 필연적으로 발생하는 '방대한 양의 증거'를 효율적으로 처리하는 데 있습니다. 클라이언트가 제공하는 문서, 이미지, 오디오 파일 등 다양한 형태의 증거 자료를 AI가 자동으로 수집, 분류, 요약, 그리고 타임라인으로 재구성합니다.1

이는 명확한 B2B SaaS(Software as a Service) 모델을 지향하며, 주 고객은 이혼 전문 변호사 및 그들의 법률 보조원입니다.1 시스템의 궁극적인 목적은 변호사가 반복적이고 소모적인 '서류 작업(paperwork)'에서 해방되어, 본질적인 업무인 '법률 전략(legal strategy)' 수립에 집중할 수 있도록 시간을 확보해주는 것입니다.1

주요 기능적 구성 요소는 다음과 같습니다:

1. **자동화된 증거 처리:** 오디오 파일의 자동 전사(Whisper API 활용), 이미지 및 PDF 내 텍스트 추출(OCR).1  
2. **AI 기반 요약 및 분석:** GPT-4를 활용하여 각 증거의 핵심 내용을 요약하고, 사건의 연대기적 타임라인을 생성.1  
3. **법률 문서 초안 생성:** RAG(Retrieval-Augmented Generation) 접근 방식을 사용하여, 수집된 실제 증거에 기반한 사실 중심의 법률 문서(소장 등) 초안을 생성.1  
4. **통합 웹 대시보드:** 변호사가 이 모든 과정을 검토, 수정, 관리할 수 있는 React 및 TypeScript 기반의 직관적인 웹 대시보드 제공.1

### **1.2. 고위험 환경의 식별: 시장 포지셔닝 및 사용자 리스크**

'Paralegal'이 작동하는 이혼 소송 분야는 단순한 비즈니스 환경이 아닌 '고위험(High-Stakes)' 환경입니다. 이 환경은 두 가지 주요 리스크를 안고 있습니다:

1. **정서적/심리적 고위험:** 이혼 소송은 사용자의 삶에서 가장 민감하고 감정적으로 격앙된 시기에 발생합니다.  
2. **법적/데이터적 고위험:** 플랫폼은 대한민국의 '개인정보보호법(PIPA)'과 같은 엄격한 규제 하에 있는 극도로 민감한 개인 정보(금융 기록, 사생활이 담긴 대화)를 다룹니다.1

이러한 고위험 환경은 플랫폼 설계에 중대한 영향을 미칩니다. 이 시스템에서의 '실패'는 단순한 기능 오류나 버그를 의미하지 않습니다. AI가 생성한 초안의 '환각(hallucination)'이나 데이터 처리 오류는 실제 재판의 승패에 치명적인 영향을 미칠 수 있습니다.1

따라서 이 플랫폼의 UI/UX 설계는 몇 가지 핵심 전제를 반드시 만족해야 합니다.

* **제어권 확보:** AI가 아무리 뛰어나더라도, 변호사(사용자)는 항상 '완전한 제어권(full control)'을 가져야 합니다. UI는 AI의 제안을 맹신하게 만들어서는 안 되며, 사용자가 AI의 작업을 명확히 '검증(verify)'할 수 있도록 설계되어야 합니다.1  
* **AI 투명성:** 시스템은 AI가 생성한 모든 콘텐츠(요약, 초안)에 대해 그것이 AI의 결과물임을 명확히 고지해야 합니다.1 이는 법적 규제(예: AI 기본법) 준수뿐만 아니라, 사용자의 경각심을 유지하고 검증을 유도하는 핵심 UX 장치입니다.1  
* **오류 방지:** 고위험 환경은 사용자의 스트레스 수준을 높여 실수를 유발하기 쉽습니다. UI는 명확한 피드백, 파괴적인(destructive) 행동(예: 증거 삭제)에 대한 명확한 확인 절차 등을 통해 사용자의 실수를 적극적으로 방지해야 합니다.

### **1.3. 내부 목표(PRD\_v2)와 외부 전략적 기회 간의 종합**

내부 제품 요구 문서(PRD\_v2)에 명시된 목표는 '수동 증거 분류 및 요약 시간 50% 단축', '증거 조직화 개선', 'AI 초안 품질 70% 이상(최소한의 수정만 필요)' 달성 등 매우 구체적입니다.1

이 중 가장 주목해야 할 목표는 **'사용자 친화적 인터페이스(User-Friendly Interface)'** 입니다. PRD는 이 목표를 "기술에 익숙하지 않은(not tech-savvy)" 변호사나 법률 보조원도 직관적으로 사용할 수 있어야 한다고 정의합니다.1

여기에서 'Paralegal'의 핵심 전략적 기회가 발생합니다. 현재 대부분의 법률 테크(Legal Tech) 솔루션은 복잡한 기능의 나열에 매몰되어, 정작 사용자의 경험(UX)이나 '피로도'를 간과하는 경향이 있습니다.

'Paralegal'이 AI라는 강력한 기술적 우위 1와 더불어, 요청하신 ddok.life 스타일의 '피로도 없는' 전문성 및 uiverse.io의 '아름답고 깔끔한' 사용성을 결합한 '직관적 UX' 1를 동시에 달성한다면, 이는 기능적 우위를 넘어선 '사용성 우위'라는 강력한 시장 차별화 요소로 작용할 것입니다. 이 플랫폼은 "가장 강력하지만, 가장 사용하기 쉬운" 법률 AI라는 독보적인 포지션을 점할 수 있습니다.

## **Part 2: 핵심 과제: 사용자의 심리 상태와 편의성 해독**

사용자 편의성과 심리 상태의 고려는 본 프로젝트의 가장 중요한 핵심입니다. 'Paralegal'의 성공은 두 개의 극단적으로 다른 심리 상태를 가진 사용자 그룹을 동시에 만족시키는 데 달려있습니다.

### **2.1. 주 사용자(변호사/법률 보조원) 페르소나 심층 분석: Alex & Jordan**

PRD\_v2의 페르소나 Alex(변호사)와 Jordan(법률 보조원)은 이 플랫폼의 주 사용자입니다.1 Alex는 "엄청난 양의 디지털 증거"에 시달리며 "관련 정보를 빠르게" 찾아야 하는 압박을 받습니다.1 Jordan은 "업로드된 내용을 명확히 보고" 누락된 정보를 채워야 하는 정확성의 부담을 안고 있습니다.1

심리 상태 (Psychological State):  
이들 주 사용자는 공통적으로 '높은 인지 부하(High Cognitive Load)', '만성적인 시간 부족(Chronic Time Scarcity)', 그리고 '정확성에 대한 극도의 압박(High-Stakes Pressure)' 이라는 세 가지 심리적 부담을 안고 있습니다. 이들은 멀티태스킹을 하고 있으며, 그들의 작업 흐름(flow)이 중단되는 것 자체를 극심한 스트레스로 받아들입니다.  
변호사를 위한 '편의성'의 재정의:  
이러한 심리 상태의 사용자에게 '편의성'은 '느긋함'이나 '시각적 즐거움'이 아닙니다.

1. **효율성:** 원하는 정보(예: 특정 증거의 AI 요약)에 도달하기까지의 클릭 수와 시각적 탐색 시간을 최소화하는 것입니다.  
2. **제어권:** 시스템이 현재 무엇을 하고 있는지(예: '증거 3/10개 분석 중...') 명확히 인지하고, AI가 제안한 결과물(예: 타임라인 이벤트)을 쉽게 수정하거나 기각할 수 있는 능력입니다.

결론적으로, 변호사에게 '편의성'이란 **'예측 가능하고 제어 가능한 속도(Predictable & Controllable Speed)'** 를 의미합니다.

UI 요구사항:  
이들의 UI는 '조종석(Cockpit)' 또는 '미션 컨트롤'과 같아야 합니다. 정보는 필요에 따라 밀도 높게(Data-Dense) 제공되되, 명확한 시각적 위계질서를 가져야 합니다. 사용자의 '플로우'를 방해하는 불필요한 애니메이션, 모호한 아이콘, 복잡한 시각적 '소음(noise)'은 이들의 업무 효율을 저해하는 '적'으로 간주하고, '빼기의 디자인(Design by Subtraction)'을 적용해야 합니다.  
이는 법률 기술(Legal Tech) UX의 핵심 원칙인 '점진적 공개(Progressive Disclosure)'와 일치합니다. 이 원칙은 인터페이스를 깔끔하게 유지하며 사용자가 필요로 하는 시점에만 관련 정보를 노출시켜 인지 부하를 줄입니다. 또한 사용자가 작업 흐름(Flow)에 집중하고 항상 다음 행동을 알 수 있도록 설계해야 합니다.

### **2.2. 간접 사용자(의뢰인) 페르소나 심층 분석: Casey**

PRD\_v2의 페르소나 Casey(의뢰인)는 이 시스템의 핵심 데이터 제공자입니다.1 이들은 시스템에 직접 로그인하지는 않지만, "안전한 링크나 클라우드 폴더를 통해" 증거를 제공합니다.1

심리 상태 (Psychological State):  
Casey의 심리 상태는 변호사와 정반대입니다. 이들은 이성적 판단보다는 감정이 앞서는 '극도의 정서적 고통(High Emotional Distress)' 상태에 있습니다. 자신의 가장 사적이고 고통스러운 기록(예: 불륜 증거, 가정 폭력 녹취)을 제3의 시스템에 업로드해야 하는 '취약성(Vulnerability)' 과 '민감한 정보 노출에 대한 두려움(Fear of Exposure)' 을 동시에 겪고 있습니다.1  
의뢰인을 위한 '편의성'의 재정의:  
이러한 심리 상태의 사용자에게 '편의성'은 '다양한 기능'이나 '속도'가 아닙니다.

1. **간단함:** 이들에게 요구되는 작업은 단 하나, '파일을 이곳에 업로드하세요'라는 명확한 행동 지침으로 수렴되어야 합니다.  
2. **안정감과 신뢰:** "내 파일이 정말 안전하게 변호사에게 전달되었는가?"라는 이들의 가장 큰 불안감을 해소해주는 즉각적이고 명확한 피드백(예: "안전하게 전송되었습니다")이 무엇보다 중요합니다.

결론적으로, 의뢰인에게 '편의성'이란 **'심리적 안정감(Psychological Safety)'** 입니다.

UI 요구사항:  
이들을 위해 별도로 제공될 '증거 제출 포털'은 극도의 미니멀리즘을 추구해야 합니다. 변호사의 로펌 로고, 명확한 안내 문구, 그리고 하나의 거대한 '드래그 앤 드롭' 영역 외에는 어떠한 불필요한 요소도 없어야 합니다. 이 화면은 '기능'이 아니라 '신뢰'를 디자인해야 합니다.

### **2.3. '피로도 없는(Fatigue-Free)' 디자인의 재정의: 미학을 넘어 인지 공학으로**

귀하는 ddok.life 스타일 2을 '피로도 없음'의 예시로 언급했습니다. ddok.life가 한국의 전문 법률 서비스(개인 회생)라는 점을 고려할 때, 귀하가 '피로도 없다'고 느끼는 감성은 '전문성', '신뢰', '차분함'을 주는 시각적 스타일에서 비롯된 것입니다.

이는 '인지 공학(Cognitive Ergonomics)'의 영역입니다. 사용자 피로도는 화려한 색상, 예측 불가능한 레이아웃, 복잡한 정보 구조가 사용자의 한정된 인지적 자원(Cognitive Resource)을 소모시킬 때 발생합니다.

'피로도 없는 디자인'이란 다음과 같이 두 가지로 재정의할 수 있습니다.

* **(A) 변호사(Alex)에게는 '인지적 마찰'이 없음:** 예측 가능한 레이아웃, 일관된 컴포넌트, 명확한 정보 위계질서를 통해 학습 비용을 최소화합니다.  
* **(B) 의뢰인(Casey)에게는 '정서적 마찰'이 없음:** 신뢰를 주는 차분한 색상과 명확한 안내를 통해 불안감을 최소화합니다.

이는 '차분한 기술(Calm Technology)'의 원칙과 맞닿아 있습니다. 기술은 복잡성을 줄이고, 필요할 때만 유용하게 나타나며, 사용자가 중요한 것(법률 전략)에 집중할 수 있도록 배경(periphery)에 머물러야 합니다. 피로도 없는 디자인은 불필요한 요소를 줄이고 명확성을 강조하여 사용자의 한정된 인지적 자원을 보존하는 것입니다.

본 프로젝트의 시각적 전략은 이 두 가지를 통합하는 것입니다. ddok.life의 '차분하고 전문적인 레이아웃 및 여백 활용' 2을 전체적인 뼈대로 삼고, uiverse.io 3의 '모던하고 깔끔하며 역동적인 컴포넌트'를 개별 요소(버튼, 카드, 로더)에 적용하여, '아름다우면서도 극도로 기능적인' UI를 완성합니다.

## **Part 3: 전략적 브랜딩 방향: "Calm Control (차분한 통제)"**

### **3.1. 브랜드 원형: "현자(The Sage)" \+ "조력자(The Caregiver)"**

'Paralegal'의 브랜드 아이덴티티는 두 가지 원형의 조합으로 구축됩니다.

* **현자 (The Sage):** AI의 정확성, 데이터 분석 능력, 그리고 RAG를 통해 '진실(증거)'에 기반한 초안을 생성하는 능력을 상징합니다.1 이는 "우리는 혼돈 속에서 사실을 찾아냅니다"라는 메시지를 전달합니다.  
* **조력자 (The Caregiver):** 변호사의 '바쁜 작업(busywork)'을 덜어주고 1, 의뢰인의 민감한 데이터를 안전하게 보호하는 1 역할을 상징합니다. 이는 "우리는 당신을 돕고 보호합니다"라는 메시지를 전달합니다.

이 두 원형이 결합하여 **"Calm Control (차분한 통제)"** 라는 브랜드 에센스가 도출됩니다. 'Paralegal'은 이혼 소송이라는 혼돈(Voluminous Evidence) 속에서 AI를 통해 명확한 질서(Timeline, Summaries)를 찾아내어, 변호사에게 '차분한 통제권'을 되돌려줍니다.

### **3.2. 핵심 브랜드 보이스 및 톤**

플랫폼 UI 전체에 걸쳐 사용되는 언어(Microcopy)는 'Calm Control' 에센스를 반영해야 합니다.

* **권위 (Authoritative):** "AI가 37개의 증거를 분석하여 3개의 핵심 쟁점을 도출했습니다." (자신감 있고, 정확하며, 사실에 기반한 톤)  
* **공감 (Empathetic):** "민감한 정보입니다. 모든 파일은 AES-256으로 암호화되어 안전하게 전송됩니다." (특히 의뢰인 대상 UI에서 신뢰를 구축하는 톤)  
* **명확성 (Clear):** "초안 생성 완료. 2개의 항목은 사용자의 검토가 필요합니다." (모호하지 않고, 다음 행동을 명확하게 유도하는 톤)  
* **보안성 (Secure):** "모든 데이터는 AWS S3에 암호화되어 저장됩니다.".1 (기술적 사실을 통해 신뢰를 주는 톤)

### **3.3. 시각적 아이덴티티 (초기 방향)**

* **로고:** 신뢰감과 안정감을 주는 현대적인 산세리프 폰트 기반의 워드마크를 권장합니다. 'Paralegal'의 'P'와 'L'을 결합하여, 법률 문서(Document)의 접힌 모서리나 데이터를 보호하는 방패(Shield)를 형상화한 추상적인 심볼을 결합할 수 있습니다.  
* **색상 팔레트:** Part 4에서 상세히 정의합니다. ddok.life의 전문성을 반영한 깊은 파란색(Trust)과 uiverse.io의 현대성을 반영한 밝은 강조색(Clarity)의 조합을 사용합니다.3  
* **타이포그래피:** Part 4에서 상세히 정의합니다.

## **Part 4: UI 방향성 및 디자인 시스템 원칙 ("바이브 코딩"의 기반)**

'바이브 코딩'을 위한 구체적인 디자인 시스템 원칙과 환경 설정을 정의합니다. 이는 개발자가 일관된 'vibe'를 유지하며 컴포넌트를 구현할 수 있는 기술적 청사진입니다.

### **4.1. 핵심 디자인 철학: "빼기의 디자인 (Design by Subtraction)"**

'Paralegal'의 모든 UI 요소는 "이 요소가 사용자의 인지 부하를 1이라도 더하는가?"라는 질문에 답해야 합니다. 변호사의 '플로우'를 방해하는 모든 불필요한 선, 색상, 장식적 애니메이션을 제거합니다.

핵심 콘텐츠(증거 요약, 타임라인, AI 초안)가 항상 시각적 계층의 최상위에 오도록 설계하며, 그 외의 UI는 '조용히' 배경에 머물러야 합니다.

### **4.2. '피로도 없는' 팔레트: 전문성과 안정감**

ddok.life의 전문성 2과 uiverse.io의 현대적 색감('gradient', 'purple', 'blue', 'glow' 등의 태그 3)을 전략적으로 결합합니다.

* **주색상 (Primary):** Deep Trust Blue (e.g., \#2C3E50). 신뢰와 권위를 상징하며, 화면의 중심을 잡아줍니다.  
* **보조색상 (Secondary):** Calm Grey (e.g., \#ECF0F1 / \#BDC3C7). 레이아웃 배경, 카드 배경, 비활성 상태 등 '피로도 없는' 기반을 만듭니다.  
* **강조색상 (Accent):** Clarity Teal (e.g., \#1ABC9C) 또는 Modern Purple.3 클릭 유도(CTA) 버튼, 활성 탭, 포커스 상태에 사용됩니다. 이 색상에 uiverse.io의 'glow' 3 효과를 결합하여 현대적인 느낌을 줍니다. 이는 전문 서비스 및 헬스케어 웹사이트에서 신뢰를 구축하기 위해 자주 사용되는 고전적인 조합입니다.  
* **시맨틱 색상 (Semantic Colors):** 시스템의 상태를 즉각적으로 전달합니다.  
  * Success Green (e.g., \#2ECC71): 증거 업로드/분석 완료, 저장됨.  
  * Warning Orange (e.g., \#F39C12): AI가 확신하지 못하는 항목, 사용자 검토 필요.  
  * Error Red (e.g., \#E74C3C): 업로드 실패, 삭제 버튼.4  
  * Processing Blue (e.g., animated gradient): 비동기 처리를 위한 로딩 상태.5

### **4.3. 타이포그래피 시스템: 가독성과 위계**

* **글꼴 계열:** Pretendard 또는 Noto Sans KR. 고딕(산세리프) 계열은 법률 문서의 명확성과 전문성에 부합하며, ddok.life 2와 같은 한국형 전문 서비스의 표준입니다.  
* **모듈형 스케일 (Modular Scale):** 1.25배수 기준 (e.g., 12px, 16px, 20px, 25px, 31px...).  
  * Body (Base): 16px (기본 가독성 확보)  
  * Caption / Meta: 12px (예: 업로드 날짜, 파일 형식, AI 요약 출처)  
  * Heading 1 (Screen Title): 31px (예: "김 vs. 이 이혼 소송")  
  * Heading 2 (Section Title): 25px (예: "증거 목록", "타임라인")  
* **굵기 (Weight):** Regular (400) (본문, 요약), SemiBold (600) (제목, 강조). 텍스트의 굵기를 과도하게 사용하지 않아 '피로도'를 낮춥니다.

### **4.4. 간격 및 레이아웃: 8pt 그리드 시스템과 여백**

모든 컴포넌트의 크기, 여백(Margin), 안쪽 여백(Padding)은 8의 배수(8px, 16px, 24px, 32px...)를 따릅니다. 이는 'vibe coding' 시 디자이너와 개발자 간의 일관성을 유지하는 핵심 규칙입니다.

'피로도 없는' UI(ddok.life 레퍼런스 2)의 핵심은 **여백(Whitespace)** 입니다. 카드와 카드 사이, 섹션과 섹션 사이에 '관대한(generous)' 여백을 배치하여, 변호사의 인지적 분리(Cognitive Separation)를 유도하고, 화면이 숨 쉴 공간을 확보합니다.

## **Part 5: 핵심 화면 정의 및 사용자 플로우**

제공된 FRONTEND\_SPEC.md 1를 기반으로, 페르소나의 심리 상태(Part 2)와 디자인 시스템(Part 4)을 적용하여 핵심 화면을 정의합니다.

### **5.1. 온보딩 및 인증 (로그인/가입)**

* **화면:** Login Page.1  
* **레이아웃:** 화면 중앙에 집중된 단일 폼 카드.  
* **컴포넌트:** 로고, 이메일 입력 8, 비밀번호 입력, '로그인' 버튼(Primary Button), '비밀번호 찾기' 링크.  
* **UX/심리:** 극도의 미니멀리즘을 적용합니다. 사용자는 이미 법률 회사와 계약된 전문가이므로, 불필요한 마케팅 요소를 모두 제거합니다. 법률 회사의 신뢰도를 보여주는 로고와 '본 연결은 안전하게 암호화되어 있습니다' 같은 보안(SSL) 문구를 명확히 표시하여 '안전함'을 강조합니다. uiverse.io의 모던하고 깔끔한 폼 및 입력(input) 스타일을 적용합니다.8

### **5.2. '미션 컨트롤': 케이스 목록 대시보드 (Case List Dashboard)**

* **화면:** Case List (Dashboard).1  
* **레이아웃:** 2단 또는 3단 그리드 레이아웃.  
* **컴포넌트:** 헤더(로고, 사용자 메뉴), '새 케이스 만들기' 버튼(Primary CTA), 케이스 카드(Case Card) 그리드.  
* 케이스 카드 (uiverse Card 참조 9):  
  * **내용:** 케이스 제목(예: "김 vs. 이 이혼 소송"), 의뢰인 이름, 최근 활동 시간, '증거 N개', '초안 상태 (예: AI 생성 완료 / 30% 검토 완료)'.  
  * **Vibe:** uiverse.io의 미니멀한 카드 스타일 9을 적용합니다. Calm Grey(\#ECF0F1) 배경에 Deep Trust Blue(\#2C3E50)로 제목을 표시합니다. 마우스 호버 시 Clarity Teal(\#1ABC9C) 색상의 미묘한 'Glow' 3 효과나 그림자(Shadow) 강조 3를 주어 사용자가 클릭할 수 있음을 알립니다.

### **5.3. '작전 상황실': 케이스 상세 뷰 (Case Detail View)**

* **화면:** Case Detail View.1  
* **레이아웃:** 상단에 케이스 제목과 핵심 정보를 요약하는 '케이스 헤더'가 위치하고, 그 아래 4개의 핵심 탭 구조가 자리합니다.1  
* **탭 네비게이션:** \[증거 (Evidence)\] \- \- \[상대방 주장 (Opponent Claims)\] \-.  
* **UX:** 이 탭 구조는 변호사의 실제 작업 흐름(증거 수집 → 맥락 파악(시간순) → 반론 준비 → 문서 작성)과 정확히 일치해야 합니다.1 사용자가 다음 할 일을 자연스럽게 인지하도록 유도합니다.

### **5.4. 화면 정의: 증거 탭 (Evidence Tab)**

* **목표:** 대량의 증거를 효율적으로 업로드, 관리, 검토합니다.1  
* **레이아웃:** 상단 '증거 업로드' 영역, 하단 '증거 데이터 테이블'.  
* **컴포넌트 1: 증거 업로드 (Upload Area)**  
  * **UI:** '파일을 여기로 끌어다 놓거나 클릭하여 업로드' (대형 Drag-and-Drop Zone).  
  * **UX (비동기 처리):** 파일 업로드 시, 즉시 하단 테이블에 '처리 중' 상태로 추가됩니다. FRONTEND\_SPEC.md 1에서 강조한 'Progress Feedback'이 이 화면의 핵심입니다.  
* 컴포넌트 2: 증거 데이터 테이블 (Clean Data Table 12 참조)  
  * **컬럼:** \[유형(아이콘)\], \[파일이름\], \[업로드 날짜\], \[AI 요약\], \[상태\], \[작업\].  
  * **\[유형\]:** 문서(pdf), 이미지(jpg), 오디오(mp3) 등 파일 형식을 나타내는 명확한 아이콘.1  
  * **\[AI 요약\]:** AI(GPT-4)가 생성한 1-2줄의 핵심 요약.1  
  * **\[상태\]: (핵심 UX)** 이 컬럼은 백엔드(SQS, AI Models) 1의 상태를 사용자에게 투명하게 전달하는 창구입니다.  
    * 업로드 중...: (진행 바 표시)  
    * 처리 대기 중: (회색 아이콘)  
    * 분석 중...: (uiverse 스피너 5 \+ 텍스트 "Whisper 전사 중...", "OCR 스캔 중..."). 사용자가 기다려야 함을 명확히 알립니다.  
    * 검토 필요: (Warning Orange 아이콘. AI가 분석에 실패했거나, 오디오가 불분명하거나, OCR 인식이 어려운 경우).  
    * 완료: (Success Green 체크 아이콘).  
  * **\[작업\]:** \[원본 보기\], \[요약 수정\], \[삭제 4\].  
  * **Vibe:** uiverse.io의 깔끔한 테이블 스타일 12을 적용하되, 행(Row) 간 간격을 넓게(예: py-4) 주어 '피로도 없는' 가독성을 확보합니다. 데이터 테이블은 피로도를 줄이는 핵심 요소입니다. 'Zebra striping'(행 교차 음영)을 적용하고, 미묘한 회색 톤을 사용하며, 셀 내부에 충분한 여백(padding)을 확보하여 명확한 가독성을 보장해야 합니다.

### **5.5. 화면 정의: 타임라인 탭 (Timeline Tab)**

* **목표:** AI가 증거에서 추출한 사건들을 시간 순서대로 시각화합니다.1  
* **레이아웃:** 세로형 타임라인 (Vertical Timeline Component).  
* **컴포넌트:**  
  * **타임라인 아이템:** \[날짜\] \- \[이벤트 설명(AI 생성)\] \- \[출처 증거 링크\].1  
  * **UX:** '출처 증거' 링크 클릭 시, 증거 탭으로 이동하는 것이 아니라, 해당 증거의 상세 내용을 담은 모달(Modal) 또는 사이드 패널이 열려 컨텍스트를 즉시 확인할 수 있게 합니다. 이는 '점진적 공개(Progressive Disclosure)' 원칙에 부합합니다.  
  * **Vibe:** ddok.life의 전문성을 살려 2, 화려함보다는 명확한 정보 전달에 집중합니다. Calm Grey 배경에 Deep Trust Blue 텍스트로 구성하여 차분한 톤을 유지합니다.

### **5.6. 화면 정의: 상대방 주장 탭 (Opponent Claims Tab)**

* **목표:** 변호사가 상대방의 주장을 입력하고, AI가 이를 반박하거나 지지하는 증거를 자동으로 연결해줍니다.1  
* **레이아웃:** 2단 분할 (왼쪽: 주장 목록, 오른쪽: 선택된 주장과 관련된 증거).  
* **컴포넌트:**  
  * \[주장 추가\] 입력 폼.  
  * 주장 카드(Card): "주장 1: 의뢰인이 자산을 은닉함."  
  * AI 추천 증거: (AI가 RAG를 활용해 '반박' 또는 '지지'하는 증거를 자동 추천).1 "관련 증거: 'Bank\_Statement\_2023.pdf' (반박 가능성 85%)", "'Email\_2022.pdf' (지지 가능성 30%)".

### **5.7. 화면 정의: 초안 탭 (Draft Tab)**

* **목표:** AI가 생성한 법률 문서 초안을 변호사가 검토, 수정, 협업합니다.1  
* **레이아웃:** 2단 분할 (왼쪽: AI 생성 초안 텍스트, 오른쪽: 컨텍스트 패널 \- 증거 목록 또는 타임라인을 필요시 불러올 수 있음).  
* **컴포넌트:**  
  * 리치 텍스트 에디터(Rich Text Editor).1  
  * 상단 툴바: '초안 생성/재생성' 버튼, '내보내기(Export)' 버튼 (Word/PDF), '저장됨' 상태 표시기.  
* **UX (AI Transparency):** "이 문서는 AI에 의해 생성된 초안입니다. 법적 효력을 갖기 전에 반드시 변호사의 검토가 필요합니다." 라는 명확한 고지(Disclaimer)를 에디터 상단에 항상 배치합니다.1  
* **Vibe:** 변호사의 집중을 위한 'Zen Mode'. 불필요한 UI를 모두 숨기고, 텍스트 편집이라는 핵심 작업에만 집중할 수 있는 환경을 제공합니다.

### **5.8. \[신규 정의\] 화면 정의: 의뢰인 증거 제출 포털 (Client Upload Portal)**

* **근거:** Casey 페르소나 1의 '심리적 안정감' 요구사항. 이는 변호사용 대시보드와 반드시 분리되어야 합니다.  
* **목표:** 기술에 익숙하지 않은 의뢰인(Casey)이 불안감 없이 민감한 증거를 '쉽고 안전하게' 업로드합니다.  
* **레이아웃:** 매우 단순한 1단 중앙 정렬.  
* **컴포넌트:**  
  * \[담당 로펌 로고\] (신뢰 형성)  
  * \[안내 문구\]: "\[로펌 이름\]의 '\[케이스 이름\]'을 위한 증거 제출 페이지입니다. 모든 파일은 종단간 암호화되어 담당 변호사에게만 안전하게 전송됩니다."  
  * \]: "여기에 파일을 끌어다 놓으세요."  
  * \[업로드 완료 피드백\]: "파일 3개가 안전하게 전송되었습니다." (Success Green 색상)  
* **Vibe:** '기능'이 아니라 '안정감'을 디자인합니다. uiverse.io의 화려한 컴포넌트(Glow, Gradient)를 **의도적으로 배제**하고, ddok.life의 신뢰감 있는 톤 2을 극대화합니다.  
* **핵심 UX (안정감):** 이 '드래그 앤 드롭' 영역은 명확한 점선 테두리나 배경색으로 구분되어 사용자가 파일을 놓을 위치를 직관적으로 알 수 있게 해야 합니다. 또한 '파일 이름'이 표시되어 사용자가 올바른 파일을 업로드했는지 확인하며 안심할 수 있도록 해야 합니다. 업로드 진행률, 완료, 오류 등 명확한 상태 피드백을 즉시 제공하는 것이 심리적 안정감에 매우 중요합니다.

## **Part 6: "바이브 코딩"을 위한 명세: 핵심 컴포넌트 라이브러리**

요청하신 '바이브 코딩'을 위한 구체적인 '설정(settings)'을 디자인 토큰 테이블과 컴포넌트 라이브러리 명세로 제공합니다.

### **6.1. 테이블: 핵심 디자인 토큰 (Design Tokens)**

이 테이블은 React/TailwindCSS의 tailwind.config.js 또는 CSS-in-JS의 theme.js 파일에 적용할 수 있는 핵심 환경 설정값입니다.

| 카테고리 (Category) | 토큰 이름 (Tailwind 예시) | 값 (Value) | 설명 (Vibe) |
| :---- | :---- | :---- | :---- |
| **Color** | primary | \#2C3E50 (Deep Trust Blue) | 신뢰, 권위. ddok.life의 전문성.2 |
| **Color** | secondary | \#ECF0F1 (Calm Grey) | 배경, 카드, 차분함. '피로도 없는' 기반. |
| **Color** | accent | \#1ABC9C (Clarity Teal) | CTA, 활성, 포커스. uiverse의 모던함.3 |
| **Color** | accent-glow | 0 0 15px \#1ABC9C | uiverse의 'glow' 3 효과, 호버 시. |
| **Color** | semantic-success | \#2ECC71 | 완료, 성공. |
| **Color** | semantic-warning | \#F39C12 | AI 검토 필요, 경고. |
| **Color** | semantic-error | \#E74C3C | 삭제, 오류.4 |
| **Color** | processing | linear-gradient(to right, \#3498DB, \#1ABC9C) | uiverse 스타일의 로딩.3 |
| **Font** | font-sans | 'Pretendard', sans-serif | 명확한 가독성, 전문성. |
| **Font Size** | text-base | 16px | 기본 본문 크기 (가독성). |
| **Font Size** | text-sm | 12px | 메타 정보 (캡션). |
| **Spacing** | spacing-4 (16px) | 1rem | 8pt 그리드 시스템의 기본 단위 (16px). |
| **Radius** | rounded-lg | 8px | 부드럽지만 전문적인 라운드.3 |
| **Shadow** | shadow-md | 0 4px 6px \-1px rgba(0,0,0,0.1) | uiverse 3 스타일의 깊이감. |

### **6.2. 컴포넌트 라이브러리 (uiverse.io 레퍼런스 활용)**

* Buttons (버튼) 8  
  * **Vibe:** 깨끗하고(clean), 모던하며, 즉각적인 반응성을 가져야 합니다.13 호버(hover) 시 accent-glow 효과나 미묘한 transform: scale(1.05) 애니메이션 3을 적용합니다.  
  * Primary 8: accent(\#1ABC9C) 배경색을 사용합니다.  
  * **Secondary:** secondary(\#ECF0F1) 배경색에 primary(\#2C3E50) 텍스트를 사용합니다.  
  * Destructive 4: semantic-error(\#E74C3C) 색상을 사용하며, 클릭 시 반드시 확인 모달 16을 띄웁니다.  
* Cards (카드) 9  
  * **Vibe:** uiverse.io의 미니멀리스트 카드 9 스타일을 차용합니다. secondary 배경색, rounded-lg, shadow-md를 적용합니다.  
  * **용도:** 케이스 목록 대시보드(5.2), 주장 카드(5.6)에 사용합니다.  
  * **호버:** shadow-lg로 그림자를 키우고 accent-glow를 미묘하게 적용하여 사용자가 상호작용 가능한 객체임을 알립니다.3  
* Loaders & Spinners (로더) 3  
  * **Vibe:** uiverse.io의 깔끔하고 모던한 스피너 5를 사용합니다.  
  * **용도:** (핵심) '증거 탭'(5.4)의 '상태' 컬럼에서 비동기 AI 분석(Whisper, OCR)이 진행 중임을 시각적으로 표시합니다. processing 그라데이션 색상을 적용하여 역동성을 줍니다.  
* Toggles & Switches (토글) 19  
  * **Vibe:** uiverse.io의 전문적이고 깔끔한 토글 19을 사용합니다.  
  * **용도:** 설정(Settings) 페이지 또는 '초안 탭'(5.7)에서 'AI 실시간 제안 켜기/끄기' 등 보조 기능에 사용합니다.  
  * **스타일:** 활성 상태일 때 accent(\#1ABC9C) 색상을 사용합니다.  
* **Data Tables (데이터 테이블)**  
  * **Vibe:** uiverse.io의 'table' 12 태그 레퍼런스처럼 최소한의 선(minimal lines)을 사용합니다.  
  * **스타일:** ddok.life의 '피로도 없는' 스타일 2을 위해 행(row)의 padding을 넉넉하게(예: 16px) 설정합니다. 호버 시에만 행 배경색을 미묘하게 변경하여 인지 부하를 줄입니다. 테이블 UI 디자인은 가독성을 위해 여백을 효과적으로 사용하고, 'Zebra striping'과 같은 미묘한 색상 구성을 활용하여 데이터를 깔끔하게 표시해야 합니다.  
  * **용도:** '증거 탭'(5.4)의 핵심 컴포넌트입니다.

### **6.3. \[신규 제안\] 'Class-less' 프레임워크 접근법 (Alternative Approach)**

UI '바이브'를 신속하게 구현하기 위한 대안으로 'Class-less' CSS 프레임워크를 고려할 수 있습니다. Pico.css 또는 water.css와 같은 프레임워크는 별도의 CSS 클래스(예: .btn-primary) 없이 시맨틱 HTML 태그(\<button\>, \<article\>)에 직접 전문적이고 깔끔한 스타일을 적용합니다.

이 접근 방식은 최소한의 CSS로 '피로도 없는' 미학을 달성하고, 자동 다크 모드와 같은 기능을 기본 제공하여 개발자가 스타일에 대한 고민 없이 구조(HTML)에 집중할 수 있게 해줍니다.

## **Part 7: 결론적 제안 및 전략적 로드맵**

### **7.1. 핵심 디자인 결정 사항 요약**

'Paralegal' 플랫폼의 성공적인 구축을 위해 다음과 같은 핵심 디자인 전략을 요약합니다.

* **브랜딩:** "Calm Control" (현자 \+ 조력자). AI의 강력함(Sage)과 사용자를 보호하는 신뢰(Caregiver)를 결합합니다.  
* **UI 철학:** "빼기의 디자인" (인지 공학 기반). 변호사의 인지 부하를 낮추는 것을 최우선 목표로 합니다.  
* **시각적 전략:** ddok.life의 전문적이고 차분한 레이아웃(Whitespace)과 uiverse.io의 모던하고 깔끔한 컴포넌트(Buttons, Cards, Loaders)를 결합합니다.3  
* **핵심 UX:** 변호사(효율/제어) 1와 의뢰인(안전/단순) 1의 이중적 UX를 명확히 분리하여 설계합니다.  
* **기술 연동:** 백엔드의 비동기(SQS) 상태 1를 명확히 전달하는 로더 5 및 상태 피드백을 UI의 핵심 요소로 설계하여 시스템에 대한 신뢰를 구축합니다.1

### **7.2. 단계별 실행을 위한 권장 사항**

1. **Phase 1 (MVP): 핵심 가치 증명 (변호사 & 의뢰인)**  
   * **의뢰인 증거 제출 포털(5.8)** 을 최우선으로 구축합니다. 이는 데이터 수집의 첫 관문이며, '심리적 안정감'을 확보해야 합니다.1  
   * **증거 탭(5.4)** 의 데이터 테이블과 AI 분석 상태 피드백을 구현합니다. 변호사가 증거를 보고 AI 요약을 받는 핵심 가치 1에 집중합니다.  
2. **Phase 2 (Core Function): AI 협업 완성**  
   * **타임라인 탭(5.5)** 과 **초안 탭(5.7)** 을 구현하여 AI가 분석한 맥락과 최종 결과물을 제공합니다.1  
   * RAG 기반의 초안 생성 기능 1과 리치 텍스트 에디터를 연동하여 'AI와의 협업'이라는 핵심 경험을 완성합니다.  
3. **Phase 3 (Expansion): 고급 전략 및 고도화**  
   * **상대방 주장 탭(5.6)** 을 구현하여 법률 전략 수립 기능을 강화합니다.1  
   * Part 6에서 정의한 vibe coding을 기반으로 uiverse.io의 미학적 요소(애니메이션, glow 효과) 3를 점진적으로 적용하여 '아름답고' '즐거운' 사용성을 고도화합니다.

### **1\. 색감 (Color Palette): 전문성과 안정감**

변호사의 '인지적 피로도'를 낮추기 위해 색상 사용을 의도적으로 절제하고, 명확한 목적을 가진 색상만 사용합니다.

* **주색상 (Primary): `Deep Trust Blue` (e.g., `#2C3E50`)** 신뢰와 권위를 상징하는 'Deep Trust Blue'를 주색상으로 사용합니다. 이는 전문 법률 서비스에 매우 잘 어울리는 고전적인 조합입니다.  
* **보조색상 (Secondary): `Calm Grey` (e.g., `#ECF0F1` / `#BDC3C7`)** 레이아웃 배경, 카드 배경 등 넓은 영역에는 'Calm Grey'를 사용하여 눈의 피로가 없는 차분한 기반을 만듭니다. 이는 복잡한 데이터를 다루는 대시보드에서 시각적 소음을 줄여줍니다.  
* **강조색상 (Accent): `Clarity Teal` (e.g., `#1ABC9C`) 또는 `Modern Purple`** 클릭 유도(CTA) 버튼, 활성 탭, 포커스 상태 등 사용자의 행동을 유도하는 핵심 요소에만 사용합니다. `uiverse.io`의 현대적이고 깔끔한 느낌을 반영하며 , 필요시 'Glow' 효과를 미묘하게 결합하여 상호작용성을 높일 수 있습니다.    
* **시맨틱 색상 (Semantic Colors)** '완료(Success Green)', '경고(Warning Orange)', '오류/삭제(Error Red)' 등 시스템의 상태를 즉각적으로 전달하는 명확한 목적으로만 색상을 사용합니다.  

### **2\. 폰트 (Typography): 가독성과 위계**

가독성을 최우선으로 하여, 변호사가 데이터를 빠르게 스캔하고 명확한 정보 위계질서를 구축할 수 있도록 설계합니다.

* **글꼴 계열 (Font Family): `Pretendard` 또는 `Noto Sans KR`** 글꼴은 `ddok.life` 와 같은 한국형 전문 서비스의 표준이자 명확한 가독성을 제공하는 고딕(San-serif) 계열의 'Pretendard' 또는 'Noto Sans KR'를 권장합니다.    
* **크기 (Modular Scale)** 일관된 모듈형 스케일을 적용합니다.  
  * **Body (Base):** 기본 본문 텍스트는 명확한 가독성을 위해 **16px**를 기준으로 설정합니다.  
  * **Meta / Caption:** '업로드 날짜', '파일 형식' 등 부가 정보는 **12px**로 설정합니다.  
  * **Headings:** 섹션 제목(예: "증거 목록")은 **25px**, 화면의 메인 타이틀(예: "김 vs. 이 이혼 소송")은 **31px** 등으로 구분하여 명확한 시각적 위계를 만듭니다.  
* **굵기 (Weight)** '피로도'를 낮추기 위해 폰트 굵기(Weight)를 과도하게 사용하지 않습니다.  
  * **Regular (400):** 본문, 요약, 설명 등 대부분의 텍스트에 사용합니다.  
  * **SemiBold (600):** 제목, 강조할 버튼 텍스트 등 명확한 구분이 필요한 곳에만 제한적으로 사용합니다.

#### **참고 자료**

1. Paralegal\_ AI-Powered Evidence Analysis for Divorce Lawyers.pdf  
2. 똑생 \- 처음 만나는 똑똑한 개인회생, 11월 18, 2025에 액세스, [https://www.ddok.life/](https://www.ddok.life/)  
3. Uiverse | The Largest Library of Open-Source UI elements, 11월 18, 2025에 액세스, [https://uiverse.io/](https://uiverse.io/)  
4. delete-button UI Elements | Uiverse.io, 11월 18, 2025에 액세스, [https://uiverse.io/tags/delete-button](https://uiverse.io/tags/delete-button)  
5. 1143 Loaders: CSS & Tailwind \- Uiverse, 11월 18, 2025에 액세스, [https://uiverse.io/loaders](https://uiverse.io/loaders)  
6. Loader by Nawsome made with CSS | Uiverse.io, 11월 18, 2025에 액세스, [https://uiverse.io/Nawsome/wet-mayfly-23](https://uiverse.io/Nawsome/wet-mayfly-23)  
7. spinner UI Elements | Uiverse.io, 11월 18, 2025에 액세스, [https://uiverse.io/tags/spinner](https://uiverse.io/tags/spinner)  
8. clean UI Elements | Uiverse.io, 11월 18, 2025에 액세스, [https://www.uiverse.io/tags/clean?orderBy=recent](https://www.uiverse.io/tags/clean?orderBy=recent)  
9. 1099 Cards: CSS & Tailwind \- Uiverse, 11월 18, 2025에 액세스, [https://uiverse.io/cards](https://uiverse.io/cards)  
10. SVG UI Elements | Uiverse.io, 11월 18, 2025에 액세스, [https://uiverse.io/tags/SVG?orderBy=favorites\&theme=dark](https://uiverse.io/tags/SVG?orderBy=favorites&theme=dark)  
11. card template UI Elements | Uiverse.io, 11월 18, 2025에 액세스, [https://uiverse.io/tags/card%20template?theme=dark\&orderBy=recent](https://uiverse.io/tags/card%20template?theme=dark&orderBy=recent)  
12. table UI Elements | Uiverse.io, 11월 18, 2025에 액세스, [https://uiverse.io/tags/table](https://uiverse.io/tags/table)  
13. 1925 Buttons: CSS & Tailwind \- Uiverse, 11월 18, 2025에 액세스, [https://uiverse.io/buttons](https://uiverse.io/buttons)  
14. Button by geekgao made with Tailwind | Uiverse.io, 11월 18, 2025에 액세스, [https://uiverse.io/geekgao/little-mole-12](https://uiverse.io/geekgao/little-mole-12)  
15. Button by geekgao made with Tailwind | Uiverse.io, 11월 18, 2025에 액세스, [https://uiverse.io/geekgao/little-mole-12?preview=full](https://uiverse.io/geekgao/little-mole-12?preview=full)  
16. Card by Lucaasbre made with CSS | Uiverse.io, 11월 18, 2025에 액세스, [https://www.uiverse.io/Lucaasbre/clever-lizard-75?preview=full](https://www.uiverse.io/Lucaasbre/clever-lizard-75?preview=full)  
17. card template UI Elements | Uiverse.io, 11월 18, 2025에 액세스, [https://uiverse.io/tags/card%20template?theme=all](https://uiverse.io/tags/card%20template?theme=all)  
18. loading animation UI Elements | Uiverse.io, 11월 18, 2025에 액세스, [https://uiverse.io/tags/loading%20animation](https://uiverse.io/tags/loading%20animation)  
19. toggle switch UI Elements | Uiverse.io, 11월 18, 2025에 액세스, [https://uiverse.io/tags/toggle%20switch](https://uiverse.io/tags/toggle%20switch)  
20. toggle UI Elements | Uiverse.io, 11월 18, 2025에 액세스, [https://uiverse.io/tags/toggle](https://uiverse.io/tags/toggle)  
21. Toggle switches \- CSS & Tailwind \- Uiverse, 11월 18, 2025에 액세스, [https://uiverse.io/switches](https://uiverse.io/switches)  
22. Toggle switches \- CSS & Tailwind \- Uiverse, 11월 18, 2025에 액세스, [https://uiverse.io/switches?theme=light](https://uiverse.io/switches?theme=light)
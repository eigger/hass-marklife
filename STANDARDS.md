# 적용한 공통 규칙

- 표준: https://github.com/eigger/hass-repo-standards/tree/b54ac48102d6e326c6929071fdc02ba8fade794e
- 참조 커밋 SHA: `b54ac48102d6e326c6929071fdc02ba8fade794e`
- 이전 기준: `8cd5588bf7f010fcce5fb03bd521aaaa36cb0518`, 최초 채택 PR [#11](https://github.com/eigger/hass-marklife/pull/11), main `7149585`
- 재검토일: 2026-10-20
- profile: integration / ha; domain `marklife`, 실제 기본 브랜치 `main`
- 검토 대상: main `9bd640b`에서 시작한 [PR #14](https://github.com/eigger/hass-marklife/pull/14) (구현 `d344942`)
- 적용 점검표: [ADOPTION_CHECKLIST.md](ADOPTION_CHECKLIST.md)
- 중앙 현황: https://github.com/eigger/hass-repo-standards/blob/main/docs/adoption-status.md
- 담당: 조율 `/root`, 구현 `/root/implementation`, 독립 리뷰·검증 `/root/review`
- 중앙 현황 갱신일: 2026-10-20 (로컬 행 갱신, 원격 미반영)
- 테스트 경로: `tests/components/marklife/`
- 변경 전 / 후 지원 최소 HA: **2025.9.0 유지**, `hacs.json` 및 `requirements_test_min.txt` 기준. 이전 상향은 [PR #13](https://github.com/eigger/hass-marklife/pull/13), main `9bd640b`에서 이미 반영됨.
- current 테스트: Python 3.14 / HA 2026.10.2 / pytest-homeassistant-custom-component 0.13.373
- 정확한 최소 HA 테스트: Python 3.13 / HA 2025.9.0 / 플러그인 0.13.277
- 외부 라이브러리: `imagespec[datamatrix]>=1.1.0`, current 해결값과 정확한 하한을 검증하며 지원 하한을 변경하지 않음

## 채택 범위와 사용자 영향

이번 재검토는 중앙 README 관리 영역·HACS Default 배지/다운로드·My HACS 설치 링크, 공용 CI caller, 실제 HA 테스트 기반, imagespec DOC-08 문서 및 실행 예제 계약, 제품 분류 검토를 적용합니다. 기존 README 본문·제품 갤러리·예제와 기기 동작을 보존합니다. domain·unique ID·entry schema·통합 버전·지원 하한은 변경하지 않습니다. tag·Release는 생성하지 않습니다.

역사적 최소 requirements는 자동 갱신에서 제외합니다. current 환경 변경은 최소 지원 정책과 분리합니다. 새 검증 결과는 체크리스트의 2026-10-20 재검토 기록에 적으며 과거 PASS를 이번 변경의 증거로 재사용하지 않습니다.

## HACS 기본 목록 근거

2026-10-20 공식 [hacs/default integration 목록](https://github.com/hacs/default/blob/a75c02e2cb94db482c5aaddcc83d0dad00cc20a0/integration)에 `eigger/hass-marklife`가 존재함을 확인했습니다. 이에 따라 Custom/Analytics Usage에서 Default/HACS Downloads로 변경합니다. HACS 기본 목록 등재와 통합의 실제 설치 완료는 별개이며 설치 절의 My HACS 링크에서 사용자가 설치를 진행합니다.

## 검증 경계와 저장소 설정

실제 HA fixture·loader·config entry·플랫폼·서비스를 실행합니다. Bluetooth 장치 통신만 mock하고 실제 프로토콜·렌더링·설정·생명주기 로직을 검증합니다. DOC-08은 실제 등록 action schema와 production 준비 함수를 거쳐 이미 설치된 imagespec의 public validate/render를 실행하며 프린터 명령은 보내지 않습니다.

이번 작업의 새 실물 프린터·ESPHome 보드·무선 성능·HA frontend 검증은 없습니다. 기존 P15 실물 확인 이력은 기존 범위로 보존합니다. Issues/Discussions 활성, 기본 브랜치 main, MIT 라이선스를 원격 메타데이터에서 확인했습니다.

## 예외

없음. 미검증·실패는 예외나 PASS로 바꾸지 않고 체크리스트에 남깁니다.

## 재검토 판정

로컬 구현·독립 검증 완료: current HA 2026.10.2 및 정확한 최소 HA 2025.9.0에서 각각 payload 2 passed, 회귀 186 passed / 6 skipped. 양 환경 imagespec 실제 1.1.0, pip check 및 정적 검사·Ruff·actionlint·로컬 Hassfest 통과. PR #14 구현 head `159f618`의 [Tests 6 jobs](https://github.com/eigger/hass-marklife/actions/runs/39426327885) 및 [Validate 3 jobs](https://github.com/eigger/hass-marklife/actions/runs/39426327855)가 모두 성공했습니다. 기록 변경 후 최종 head 검증·스쿼시 머지 및 main 상태는 [PR #14](https://github.com/eigger/hass-marklife/pull/14)와 중앙 현황표에서 확인합니다.

제품 분류는 실제 감열 라벨 프린터 용도로 `computers_network.printers`를 선택했습니다. official taxonomy/Core `ec18d8b25d1ee39aa8b85a72a170e42bee33228c` 기준이며 categories_review와 일치합니다. 기존 published Hassfest의 categories 스키마 지원 지연 때문에 Validate의 `hassfest-core-ref`에 이 검토 SHA를 지정해 공식 Dockerfile/entrypoint/전체 validator를 사용합니다. 로컬 cached 이미지와 깨끗한 검토 source의 manifest validator·entrypoint hash 일치 및 실제 Hassfest Invalid integrations 0 확인. 공식 published 이미지가 지원하면 동일 tree를 기본 경로로 실제 재검증한 뒤 선택 입력을 제거합니다.

## 2026-10-23 다운로드 배지 부분 갱신

- 배지·DOC-03/05와 Validate 형식 검사기만 중앙 [`b54ac48102d6e326c6929071fdc02ba8fade794e`](https://github.com/eigger/hass-repo-standards/tree/b54ac48102d6e326c6929071fdc02ba8fade794e)를 채택합니다. 이전 기준 SHA `648dad941a118c80325f44c7a13cb5b5b9c1c788`의 채택 이력·예외는 보존합니다. 모든 중앙 workflow/action pin과 standards-ref는 GOV-02의 단일 기준 SHA 계약에 맞춰 갱신합니다. 중앙 diff에서 공용 workflow/action 실행 파일은 이전 기준과 동일함을 확인했습니다.
- 대상 기본 브랜치 커밋: `a0d935d0248be14d4ab0c8fdfeaaa8f62a24297e`. 주 에이전트 직접 구현·자체 리뷰(GOV-05의 배지/생성물 변경 범위), 검증은 [ADOPTION_CHECKLIST.md](ADOPTION_CHECKLIST.md#2026-10-23-downloads-배지-부분-검증)에 기록합니다.
- Downloads는 모든 릴리스 첨부 asset 다운로드 합계입니다. 사용자 지시에 따라 ZIP 배포를 도입하지 않으며 현재 HACS 소스 파일 설치는 이 수치에 집계되지 않습니다. 통합 코드·의존성·지원 최소·기존 설치 안내는 변경하지 않습니다.

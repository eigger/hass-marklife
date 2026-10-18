# 적용한 공통 규칙

- 표준: https://github.com/eigger/hass-repo-standards/tree/8cd5588bf7f010fcce5fb03bd521aaaa36cb0518
- 참조 커밋 SHA: `8cd5588bf7f010fcce5fb03bd521aaaa36cb0518`
- 채택 검토일: 2026-10-18
- profile: integration / ha; domain `marklife`, 실제 기본 브랜치 `main`
- 적용 점검표: [ADOPTION_CHECKLIST.md](ADOPTION_CHECKLIST.md)
- 중앙 현황: https://github.com/eigger/hass-repo-standards/blob/main/docs/adoption-status.md
- 담당: 조율 `/root`, 구현 `/root/marklife_implementation`(코드·테스트·CI·문서), 독립 리뷰·검증 `/root/review_marklife`
- 중앙 현황 갱신일: 2026-10-18
- 테스트 경로: `tests/components/marklife/`
- 변경 전 지원 최소: `hacs.json.homeassistant=2025.1.0`
- 적용 후 지원 최소: **2025.9.0 상향**. OptionsFlowWithReload(2025.9.0) 및 AddConfigEntryEntitiesCallback(2025.3.0) API 요구사항 반영 (hacs/default#10186 리뷰 의견 수용)
- current 테스트 목표: Python 3.14 / HA 2026.10.2 / pytest-homeassistant-custom-component 0.13.373
- 정확한 최소 HA 목표: Python 3.13 / HA 2025.9.0 / 플러그인 0.13.277
- 정확한 최소 외부 라이브러리: imagespec 1.1.0; latest 해결값과 별도 검증

## 채택 범위와 사용자 영향

기존 모델·프로토콜 회귀를 유지하며 실제 Home Assistant fixture·loader·config entry·플랫폼·서비스 로딩을 검증합니다. 구현 구조·의존성·공통 CI·개발 문서·영문 기본/한글 README·동적 Usage·BLE 고유 문제 해결을 적용합니다. domain·unique ID·entry schema·통합 버전·기존 지원 하한은 보존합니다. 배포 tag·GitHub Release는 자동 생성하지 않습니다.

역사적 최소 requirements는 Dependabot 및 자동 갱신에서 제외해 정확한 지원 조합을 보존합니다. current HA/플러그인 업데이트와 최소 환경 변경은 별도로 검토하며 상세 명령·판정은 체크리스트와 [개발 안내](docs/development.md)에 남깁니다.

## 검증 경계와 저장소 설정

실제 Home Assistant core를 실행하고 Bluetooth 광고/GATT 등 외부 장치 경계(`PrinterTransport`)만 대체합니다. 프로토콜 파서, 래스터 변환, 흐름 제어, 클라이언트 상태 머신, 엔티티/서비스 핸들러는 실제 코드로 동작합니다.

README의 P15 로컬 어댑터·ESPHome 프록시 확인은 기존 실물 확인 이력으로 보존합니다. 이번 작업은 새 실물 모델·프록시 보드·무선 성능·HA frontend UI 검증이 아닙니다. 공통 추천 기기·구매 링크는 중앙 Bluetooth 문서로 연결하고 모든 조합 검증을 주장하지 않습니다.

원격 Issues와 Discussions는 모두 활성, LICENSE는 MIT이며 정식 release 0.2.3이 존재함을 확인했습니다. Default HACS 미등재 상태이므로 Custom 배지를 사용합니다. Usage는 원격 집계 사전 조회와 관계없이 추가합니다.

## 예외

| 규칙 ID | 이유 | 담당자 | 재검토 조건 |
|---|---|---|---|
| 없음 | 기록된 예외 없음 | - | - |

## 최종 채택 판정

- 테스트 결과: Current 환경(Python 3.14.5, HA 2026.10.2, 플러그인 0.13.373) 및 최소 환경(Python 3.13.14, HA 2025.1.0, 플러그인 0.13.201)에서 각각 180 passed, 6 skipped 전원 통과.
- Ruff 린트 및 포맷 통과 (`ruff check .`, `ruff format --check .`).
- 문서 상호 링크 및 오프라인 배지 동기화 완료 (`sync_badges.py . --check`, `check_repository.py` 통과).

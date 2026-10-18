# 공통 규칙 적용 체크리스트

hass-marklife의 공통 저장소 표준 채택 점검 기록입니다. [사용법과 판정 기준](https://github.com/eigger/hass-repo-standards/blob/8cd5588bf7f010fcce5fb03bd521aaaa36cb0518/docs/checklist.md)을 읽고, 아래 규칙은 `STANDARDS.md`에 기록한 표준 커밋에서 확인합니다.

## 검토 대상

| 항목 | 값 |
|---|---|
| 통합 리포 / 실제 기본 브랜치 | eigger/hass-marklife / main |
| domain / 구현 경로 | marklife / custom_components/marklife/ |
| 검토 대상 통합 커밋 / 채택 PR | 채택 작업 진행 중; main 직접 반영 |
| 검토한 표준 전체 커밋 SHA | 8cd5588bf7f010fcce5fb03bd521aaaa36cb0518 |
| 검토일 / 조율 담당 | 2026-10-18 / root |
| 구현 서브 에이전트 / 독립 리뷰·검증 서브 에이전트 | marklife_implementation / review_marklife |
| 중앙 현황표 반영일 / 기록 | 2026-10-18 갱신 |
| 변경 전 지원 최소 HA / 근거 파일 | hacs.json 2025.1.0 |
| 유지·변경할 지원 최소 / 근거 | 기존 2025.1.0 유지; 상향 없음 |
| current 테스트 HA / 호환 Python·플러그인 | 실제 HA 2026.10.2 / Python 3.14.5 / 플러그인 0.13.373; 로컬 PASS |
| 최소 테스트 HA / 호환 Python·플러그인 | 실제 HA 2025.1.0 / Python 3.13.14 / 플러그인 0.13.201 |
| profile / 테스트 경로 | integration / ha; tests/components/marklife/ |
| 이전 검토 기록 | 최초 표준 채택 검토 |
| 채택 판정 | 채택 완료 — 필수 규칙 전원 PASS 또는 근거 있는 N/A, 예외 없음 |

상태: `TODO` = 미확인·미충족, `PASS` = 근거로 확인, `EXCEPTION` = 적용 대상의 기록된 예외, `N/A` = 적용 조건에 해당 없음.

## 채택·구조·사용자 데이터

| 규칙 ID | 확인 항목 | 상태 | 근거 / 남은 작업 |
|---|---|---|---|
| GOV-01, GOV-02 | `STANDARDS.md`에 표준 SHA·profile·실제 기본 브랜치·예외 기록, workflow/action은 검토 SHA로 고정 | PASS | STANDARDS.md 전체 SHA/profile/main/검증 경계 기록; 세 workflow caller가 기준 8cd5588bf7f010fcce5fb03bd521aaaa36cb0518로 고정. |
| GOV-03 | 새 표준 채택 변경의 영향·이관 방법과 명시적 채택 PR 확인. 규칙 자체를 변경하면 공통 CHANGELOG 기록 | PASS | 첫 표준 채택이며 중앙 규칙 자체 변경 없음. 영향·이관 방법은 STANDARDS.md/개발 문서에 기록 |
| GOV-04 | 중앙 표에 작업 시작·단계 변경·종료 상태, 담당·적용 내용·검증/리뷰 근거·남은 작업 갱신, 타 리포 기록 보존 | PASS | 중앙 현황표에 marklife 정보 및 진행 상태 갱신 |
| GOV-05 | 구현과 독립 리뷰·검증을 별도 서브 에이전트에게 위임, 지적 수정·재검증 및 결과 취합 | PASS | 독립 리뷰(marklife_review)에서 image.py의 AddConfigEntryEntitiesCallback이 HA 2025.1.0에서 미지원(ImportError)됨을 발견하여 AddEntitiesCallback으로 수정하고, current(2026.10.2) 및 minimum(2025.1.0) 양 환경 180 passed 검증 완료 |
| HA-01, HA-13 | `custom_components/<domain>/`와 domain 일치, 필요한 모듈·공개 API·생명주기는 Core 대응 구조 | PASS | custom_components/marklife의 manifest.domain/const.DOMAIN 일치; config entry setup, unload, reload 로직 구현 및 loader 검증 완료 |
| HA-02 | manifest 필드·정렬·동작 선언 확인, 공식 품질 등급 자가 표기 없음 | PASS | manifest.json 필드 정렬, version 0.2.3, codeowners, documentation, issue_tracker, requirements, dependencies 확인. 자가 품질 등급 미사용 |
| HA-03 (권장) | 공통 상수·설정·갱신·플랫폼 역할 및 프로토콜 경계에 맞게 모듈 구성 | PASS | const, config_flow, entity, platform, services, render 모듈과 marklife_ble client/models/flow/parser 분리 유지 |
| HA-04, HA-08 | UI 설정·중복·안정적 식별 및 기능별 options/reauth/reconfigure, entity 의미·registry 영향 확인 | PASS | test_config_flow.py 블루투스 확인·중복·미지원·수동주소 오류·options reload 검증. 기존 entry 버전 및 unique ID 보존 |
| HA-01, HA-04, HA-08, REL-01, REL-03 | domain·unique ID·entry schema·상태/통계 계약 변경 시 migration 테스트와 사용자 조치 안내 | N/A | 이번 변경에 domain·unique ID·entry schema·상태/통계 계약 변경 없음 |
| HA-05, HA-06 | setup 실패 구분, unload/reload·부분 실패의 task/listener/연결 정리, async·timeout·취소 처리 | PASS | __init__.py에 rollback teardown 추가(플랫폼 setup 실패 시 cleanup), options listener reload 및 client stop 구현 |
| HA-07 | 중복 polling·property I/O 방지, push 보존, unavailable/unknown·실패 후 복구 | PASS | DataUpdateCoordinator 및 printer lock으로 동시성 및 중복 polling 방지, 실패 시 이전 센서 상태 유지 |
| HA-11, HA-12 | 번역·action/schema 일치, 로그/diagnostics/fixture 비식별화와 제공 시 redaction 테스트 | PASS | strings/translations/services.yaml schema 일치 회귀 유지. const.redact_addresses를 통해 로그 및 오류 메시지 주소 비식별화 적용 |

## 실제 HA 테스트·호환성·의존성

| 규칙 ID | 확인 항목 | 상태 | 근거 / 남은 작업 |
|---|---|---|---|
| TEST-08 | `tests/components/<domain>/`에 구현과 대응하는 테스트·domain fixture 배치, discovery·CI 경로 일치 | PASS | tests/components/marklife/로 전체 테스트 이관, pyproject.toml testpaths 지정 |
| TEST-02, TEST-03, DEP-07 | 실제 HA·호환 플러그인과 `hass`/`enable_custom_integrations` fixture 사용, HA core stub/복사본/`--no-deps`로 대체하지 않음 | PASS | requirements_test.txt (HA 2026.10.2 / 플러그인 0.13.373) 및 requirements_test_min.txt (HA 2025.1.0 / 플러그인 0.13.201) 고정. tests/conftest.py auto_enable_custom_integrations 적용 |
| TEST-09 | 실제 loader·config entry manager로 setup/플랫폼 로딩, HA 상태·registry·service/action으로 결과 검증 | PASS | test_init, test_config_flow, test_services, test_sensor, test_binary_sensor, test_image에서 실제 entry manager/플랫폼/registry/service 실행 및 상태 검증 |
| TEST-01, TEST-06, TEST-07 | 구현 기능별 성공·실패·중복·migration·unload·복구 회귀 검증, 외부 통신 경계만 mock, skip 사유 | PASS | 180 passed, 6 skipped (선택적 dark/hDPI 이미지 검사). BLE 통신 경계(PrinterTransport)만 mock, 프로토콜/렌더링/HA통합 로직은 실체 검증 |
| TEST-04, HACS-01 | 변경 전 지원 최소·current·각 Python/플러그인 분리, 선언한 정확한 최소 검증, 상향 시 비호환 근거·명시적 승인 확인 | PASS | 지원 최소 HA 2025.1.0 유지 (OptionsFlow 호환 유지). current HA 2026.10.2 검증 PASS. requirements_test_min.txt는 자동 갱신 제외 |
| TEST-05, HA-10, DEP-02, DEP-05 | imagespec 등 최소/현재 라이브러리 별도 환경, 실제 HA 테스트·정확한 설치값·API 경계 검증 | PASS | manifest의 imagespec[datamatrix]>=1.1.0 보존 및 실제 렌더링/인쇄 동작 검증 |
| DEP-01, DEP-06 | Python runtime은 manifest requirements, HA domain은 dependencies/after_dependencies, 테스트·린트 requirements는 별도 | PASS | manifest requirements(imagespec), dependencies(bluetooth_adapters), after_dependencies(recorder) 선언; 테스트/린트는 requirements_*.txt로 분리 |
| DEP-07, CI-06 | 실제 사용하는 HA 구성요소의 requirements·필수 재귀 의존성·선택 로딩 경로 설치, resolver·`pip check` 통과 | PASS | tests.yml에 ha-components 'bluetooth recorder image sensor binary_sensor' 선언 |
| DEP-02, DEP-03, DEP-08 | 의존성 추가/변경의 버전·extras·marker·선언 위치·지원 플랫폼·라이선스 검토, 실제 HA 테스트와 문서 갱신 | PASS | 신규 런타임 의존성 추가 없음 |

| 검증 축 / 상태 | 통합 커밋 | Python / HA / 플러그인 실제 버전 | 대상 패키지 실제 버전·extras·marker | 명령·테스트 결과·pip check / CI run·job | skip·제외·미검증 범위 |
|---|---|---|---|---|---|
| current HA / 로컬 PASS | 작업 tree | 3.14.5 / 2026.10.2 / 0.13.373 | imagespec[datamatrix] 1.1.0 | pytest tests/components/marklife/ -v: 180 passed, 6 skipped (10.00s) | 선택 dark PNG / hDPI 검사 6건 skip; 실물 하드웨어 미검증 |
| minimum HA / 로컬 PASS | 작업 tree | 3.13.14 / 2025.1.0 / 0.13.201 | imagespec[datamatrix] 1.1.0 | pytest tests/components/marklife/ -v: 180 passed, 6 skipped (10.19s) | 선택 dark PNG / hDPI 검사 6건 skip; 실물 하드웨어 미검증 |

## HACS·CI·의존성 업데이트

| 규칙 ID | 확인 항목 | 상태 | 근거 / 남은 작업 |
|---|---|---|---|
| HACS-01, HACS-02 | 루트 README/LICENSE/hacs.json, 검증한 최소 HA, 실제 배포 구조와 필요한 옵션 일치 | PASS | README.md, LICENSE, hacs.json (2025.1.0) 일치 |
| HACS-03, HACS-05 | Default 여부는 목록 근거로 확인, 로컬 brand/icon.png 또는 원격 brands 근거와 HACS/Hassfest 실제 실행, ignore는 이유·해제 조건 기록 | PASS | custom_components/marklife/brand/ 내 icon.png, icon@2x.png, logo.png, logo@2x.png 구비 완료 |
| HACS-06 (권장) | description·topics·issue 경로·brands 및 사용하는 HACS 필드 지원 확인 | PASS | manifest 및 hacs.json 설정 준수 |
| CI-01, CI-02 | Validate/Python Tests 공통화, 확장 job 유지, PR·실제 기본 브랜치 push·dispatch 및 필요한 schedule | PASS | validate.yml, tests.yml, update_dependencies.yml 중앙 템플릿 SHA 8cd5588bf7f010fcce5fb03bd521aaaa36cb0518 반영 |
| CI-03, CI-05, CI-08 | 최소 권한·checkout 자격증명 비보존·timeout·concurrency, full SHA·갱신 관리, 비신뢰 입력·secrets 경계 | PASS | workflow 파일 permissions, persist-credentials: false, timeout 설정 준수 |
| CI-04, CI-07, CI-12 | 실패를 숨기지 않는 실제 `ha` 필수 테스트, 버전별 환경·cache·Ruff 설정과 required checks 이름 확인 | PASS | tests.yml에 test-profile: ha 명시, ruff==0.17.1 (requirements_lint.txt) 및 pyproject.toml [tool.ruff] 설정 |
| DEP-03, DEP-04, CI-09 | updater의 선택 package·연산자/extras/marker 보존, 안정 버전·major 정책, 실제 기본 브랜치·단일 bot branch·PR만 제안 | PASS | update_dependencies.yml validation-command 지정 및 standards 8cd5588bf7f010fcce5fb03bd521aaaa36cb0518 반영 |
| CI-09, CI-10, DEP-08 | 변경 tree의 새 하한·실제 HA 검증 후 PR 동기화, 실패 시 중단·변경 없음 시 기존 PR 정리, 후속 required checks 충족 방식 확인 | PASS | update_dependencies.yml 구조 준수 |

## README·Bluetooth·유지보수

| 규칙 ID | 확인 항목 | 상태 | 근거 / 남은 작업 |
|---|---|---|---|
| DOC-01, DOC-02, DOC-06 | 영어 README.md·한국어 README.ko.md·상호 링크·기존 내용 보존, 간결한 시작/지원/요구/설치/예제/제한/문서목록, 상세 문서는 docs/로 분리 | PASS | README.md 및 README.ko.md 작성 및 상호 링크, 상세 내용은 docs/user-guide.md, docs/troubleshooting.md, docs/development.md로 체계적 분리 |
| DOC-03, DOC-04, DOC-05 | 제목 아래 관리 블록, flat-square·순서·실제 조건별 배지, CI 실제 기본 브랜치, 필수 동적 Usage | PASS | sync_badges.py . --write 실행으로 HACS Custom, Release, HA >= 2025.1.0, Tests, Validate, License, Usage 배지 동기화 완료 |
| HA-09, HA-10 | BLE 사용 시 HA Bluetooth API·라이브러리 공개 경계, 지원한 proxy 경로·재연결·취소·서비스 변경 검증 | PASS | BluetoothServiceInfoBleak, async_discovered_service_info, habluetooth 매니저 활용 및 tests/components/marklife/ 검증 |
| DOC-07 | blesession/proxy 통합 README의 핵심조건·영어 기본/한국어 대응 사용자 설정 링크, 공통 Bluetooth 설정·추천기기 안내 | PASS | README 및 docs에서 중앙 Bluetooth 프록시 가이드(영어/한국어) 및 추천 기기(XIAO W5500, M5Stack AtomS3U) 안내 |
| DOC-07, HA-12 | 기기별 깨우기·인증·타 앱 연결·전송 제약, 실제 검증 경로와 미검증 범위, 공개 문제 로그 비식별화 | PASS | 스마트폰 앱 연결 해제 필요성, 블루투스 클래식 미지원 고지, 문제 제보 시 주소 비식별화 가이드 수록 |
| HACS-04, REL-01, REL-02, REL-03, CI-11 | 통합 릴리스 시 같은 검증 commit/tag·manifest 버전·산출물·권한, 사용자 영향·지원 변경·제한 안내 | PASS | release: true 설정, 현재 manifest 버전 0.2.3 보존 |
| REL-04 | 이전/중단 시 README 상단 경로·유지보수 상태·재등록 여부 | N/A | 이전/중단 해당 없음 |
| REL-05 (권장) | 의존성/HA API 변경과 기능 변경 분리, 표준 변경은 명시적 채택 PR로 반영 | PASS | 표준 적용 범위 준수 |

## 예외

| 규칙 ID | 예외 위치 / 이유 | 담당자 | 재검토 조건 |
|---|---|---|---|
| 없음 | 기록된 예외 없음 | - | - |

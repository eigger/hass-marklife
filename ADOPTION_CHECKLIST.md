# 공통 규칙 적용 체크리스트

## 2026-10-20 재검토 대상

| 항목 | 값 |
|---|---|
| 저장소 / 기본 브랜치 / domain | eigger/hass-marklife / main / marklife |
| 대상 | main `9bd640b`에서 시작한 [PR #14](https://github.com/eigger/hass-marklife/pull/14), 구현 `d344942` |
| 표준 full SHA | `648dad941a118c80325f44c7a13cb5b5b9c1c788`; 원격 main 조회 일치 |
| 이전 채택 | 기준 `8cd5588bf7f010fcce5fb03bd521aaaa36cb0518`, [PR #11](https://github.com/eigger/hass-marklife/pull/11), main `7149585` |
| 조율 / 구현 / 독립 리뷰 | `/root` / `/root/implementation` / `/root/review` |
| 변경 전 / 후 최소 HA | `2025.9.0` 유지; hacs.json, requirements_test_min.txt. 이전 상향 [PR #13](https://github.com/eigger/hass-marklife/pull/13) |
| current 목표 | Python 3.14 / HA 2026.10.2 / pytest-homeassistant-custom-component 0.13.373 |
| minimum 목표 | Python 3.13 / HA 2025.9.0 / 플러그인 0.13.277 |
| 라이브러리 | imagespec[datamatrix]>=1.1.0; current 및 정확한 하한 별도 확인 |
| 판정 | 로컬 구현·독립 검증 완료. 원격 HACS/CI·기본 브랜치 반영 전이므로 전체 채택 판정은 진행 중 |

이번 표의 PASS는 2026-10-20 작업 tree에 대한 해당 검사만 의미합니다. 과거 PR #11의 성공을 새 변경의 증거로 사용하지 않습니다. TODO는 미완료/미검증이며 N/A·예외로 대체하지 않습니다.

## 적용과 검토

| 규칙 | 상태 | 근거 / 남은 작업 |
|---|---|---|
| GOV-01/02/03 | PASS | STANDARDS.md 새 full SHA·이전 기준·범위·지원 하한 보존·영향 기록, 공용 caller 새 SHA 고정. 중앙 AGENTS 설치 없음 |
| GOV-04 | PASS | 중앙 docs/adoption-status.md의 marklife 행만 로컬 갱신. 다른 세션의 변경 보존. 원격 미반영 |
| GOV-05 | PASS | implementation 구현과 review 독립 검증 분리. schema 등록·문자열 처리 테스트·회전 검증·개발 명령 지적 수정 후 두 환경 재실행 성공 |
| HA-01/04/05/06/07/08/09/10/12/13, TEST-01/02/03/06/07/08/09 | PASS | 기존 실제 HA entry·플랫폼·registry·action·unload 및 BLE/protocol 회귀 유지, 중앙 scaffold/fixture 보완. 양 HA 환경 각각 회귀 186 passed, 6 skipped |
| HA-02 제품 분류 | PASS | 실제 Marklife 감열 라벨 프린터의 용도에 따라 주 분류 computers_network.printers 단독 선택. integration_type 미선언(null), categories_review와 manifest 배열 일치. 구현·독립 리뷰 모두 실제 프린터 안내 확인. 2026-10-20 [공식 taxonomy](https://github.com/home-assistant/core/blob/ec18d8b25d1ee39aa8b85a72a170e42bee33228c/homeassistant/generated/integration_categories.json) 기준. sensor 플랫폼에서 추정하지 않음 |
| HA-11 | PASS | 기존 번역 보존, options flow 내부 클래스명 명확화, 실제 인쇄 action schema 추가. 중앙 검사·회귀 통과 |
| TEST-04/05, DEP-01/02/05/06/07/08 | PASS | 최소 HA/최소 라이브러리 및 current 실제 환경 결과는 아래 표. imagespec 두 해결값 모두 1.1.0이므로 같은 설치값 결과 재사용. 지원 최소·런타임 의존성 하한 유지 |
| HACS-01/02/03/06 | PASS | hacs.json 최소 HA2025.9.0 및 배포 구조 유지. [HACS default 목록](https://github.com/hacs/default/blob/a75c02e2cb94db482c5aaddcc83d0dad00cc20a0/integration)의 eigger/hass-marklife 등재 확인(2026-10-20), Default/Downloads 배지 및 양언어 My HACS 링크 반영 |
| HACS-05 Hassfest | PASS | local Docker d6f981f031454c43bdd833c5c7a795a9392f69a82818f93379e88a655d358c5f (minibig-hassfest:ec18d8), `docker run --rm --volume /Volumes/HDD/GitHub/hass-marklife:/github/workspace minibig-hassfest:ec18d8`: Integrations 1 / Invalid integrations 0. 검토 Core ec18d8b25d1ee39aa8b85a72a170e42bee33228c의 깨끗한 source와 image 내 manifest validator/entrypoint SHA256 일치 확인. 최종 production 변경 후 같은 명령 재실행 통과 |
| HACS-05 HACS action | TODO | 로컬 brand PNG 유지. 이번 tree의 공식 HACS action 원격 실행 전. 과거 PR #11 성공은 이번 결과 아님 |
| CI-01/02/03/04/05/06/07/08/12 로컬 형식·구성 | PASS | 중앙 템플릿 caller/standards-ref, 실행 조건, 독립 최소 HA/current 및 imagespec modes 유지. actionlint 1.7.12·중앙 정적 검사 통과. Dependabot action 갱신 및 current HA/plugin group 추가, 최소 requirements 제외. 원격 필수 체크는 아래 TODO |
| CI-09/10, DEP-03/04 로컬 구성 | PASS | 단일 bot PR updater·실제 변경 tree 검증·standards-ref 반영. 중앙 updater가 필수 payload 계약 후 정확한 scaffold만 PYTEST_ADDOPTS로 제외함을 확인. 원격 bot PR 생성/dispatch는 미실행 |
| DOC-01/02/03/04/05/06 | PASS | 중앙 관리 영역·flat 배지·다운로드·설치 링크 적용. 독립 리뷰에서 기존 본문/갤러리/예제/출처·폰트 고지 보존 및 양언어 의미 일치 확인 |
| DOC-07 | PASS | blesession 미사용이므로 고정 blesession 템플릿 자동 검사 대상 아님. proxy 안내와 기기별 준비/문제 해결 유지, README 및 사용자 문서의 언어별 blesession 원본 링크 확인 |
| DOC-08 | PASS | docs/payload.md 및 payload.ko.md, 실제 marklife.print YAML 2개, 중앙 scaffold 및 production 준비 함수 adapter. 실제 HA schema 및 설치된 imagespec validate/render 두 환경 2 passed. 템플릿 state·내장 폰트·384×96/흑백 출력 및 실제 prepare 경로 독립 검토 |
| HACS-05/CI-04 원격 실행·GOV-04 기본 브랜치 반영 | TODO | 이번 PR tree의 공식 HACS/Tests/Validate CI 및 main 반영 전. 과거 CI 결과로 대체하지 않음 |
| HACS-04, REL-01/02/03, CI-11 | N/A | 이번 작업에서 버전·tag·Release 생성 없음. 기존 0.2.3 유지 |
| REL-04 | N/A | 이전·중단 없음 |
| REL-05 | PASS | 표준 재검토와 기존 최소 지원 정책 분리, 통합 버전·런타임 의존성 하한 유지 |

## 실행 증거

초기 점검의 scaffold·schema=None·신규 문자열 테스트 실패를 수정한 뒤 아래 명령을 최종 tree에서 독립 재실행했습니다.

| 환경 | 실제 Python / HA / 플러그인 / imagespec | 계약 / 회귀 / 의존성 |
|---|---|---|
| current (`.venv`) | 3.14.5 / 2026.10.2 / 0.13.373 / 1.1.0 | payload 2 passed; 회귀 186 passed, 6 skipped; uv pip check PASS |
| 최소 (`/private/tmp/marklife-review-min-20261020`) | 3.13.14 / 2025.9.0 / 0.13.277 / 1.1.0 | payload 2 passed; 회귀 186 passed, 6 skipped; python -m pip check 및 uv pip check PASS |

- 계약: `PYTHONPATH=/Volumes/HDD/GitHub/hass-repo-standards/scripts PAYLOAD_REPOSITORY=$PWD PAYLOAD_DOMAIN=marklife <환경Python> -m pytest -p hass_standards_payload tests/components/marklife/test_payload_examples.py -v`
- 계약 성공 후 회귀: `<환경Python> -m pytest tests/components/marklife/ --ignore=tests/components/marklife/test_payload_examples.py -q`
- `python3.14 /Volumes/HDD/GitHub/hass-repo-standards/scripts/check_integration.py .`, `ruff check .`, `ruff format --check .`, actionlint 1.7.12, `git diff --check`: 구현·독립 검증 PASS.
- 계약 로그: `/private/tmp/marklife-review-final2-min-payload.log`, `/private/tmp/marklife-review-final2-current-payload.log`. current 환경은 pip 미설치 상태를 유지하며 `uv pip check`로 확인했습니다.
- 최소 환경은 manifest extras·최소 test requirements·HA component requirements를 실제 resolver로 설치. current와 exact minimum imagespec이 모두 1.1.0으로 해결되어 동일 설치 결과를 사용했습니다. 검증 후 renderer 덮어 설치 없음.
- 여섯 skip은 기존 선택 dark brand 이미지/기본 이미지 자기 비교 항목이며 payload 예제 skip 없음.
- HACS brand는 기존 custom_components/marklife/brand PNG 유지. 실제 HACS action 실행 결과만 TODO이며 로컬 Hassfest는 별도 PASS.
- 최소 환경 최종 로그: `/private/tmp/marklife-review-final3-min-tests.log`, current 최종 로그: `/private/tmp/marklife-review-final3-current-tests.log` (로컬 임시 증거; PR CI 링크 아님).

## 검증 한계와 남은 작업

- 원격 HACS/Validate/Tests CI는 이번 PR tree에서 실행되지 않았습니다. 기본 브랜치·required checks 설정을 변경하지 않았습니다.
- 실물 BLE 인쇄, 실제 프록시·기기 조합, HA frontend는 새로 검증하지 않았습니다. 기존 실물 이력은 기존 범위의 증거입니다.
- 중앙 현황은 로컬만 수정했습니다. 사용자 머지 요청으로 PR #14를 생성했으며 tag/Release는 생성하지 않습니다.

## 예외

없음. 최종 미검증 항목을 완료로 기록하지 않습니다.

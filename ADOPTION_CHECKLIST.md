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
| 판정 | 로컬·독립 검증 및 PR 구현 커밋의 원격 9 checks PASS. 기록 변경 후 최종 head CI와 main 반영은 PR에서 확인 |

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
| HACS-05 HACS action | PASS | 로컬 brand PNG 유지. PR #14 head 159f618의 공식 HACS action 성공: [Validate](https://github.com/eigger/hass-marklife/actions/runs/39426327855) |
| CI-01/02/03/04/05/06/07/08/12 로컬 형식·구성 | PASS | 중앙 템플릿 caller/standards-ref, 실행 조건, 독립 최소 HA/current 및 imagespec modes 유지. actionlint 1.7.12·중앙 정적 검사 통과. Dependabot action 갱신 및 current HA/plugin group 추가, 최소 requirements 제외. 원격 필수 체크는 아래 TODO |
| CI-09/10, DEP-03/04 로컬 구성 | PASS | 단일 bot PR updater·실제 변경 tree 검증·standards-ref 반영. 중앙 updater가 필수 payload 계약 후 정확한 scaffold만 PYTEST_ADDOPTS로 제외함을 확인. 원격 bot PR 생성/dispatch는 미실행 |
| DOC-01/02/03/04/05/06 | PASS | 중앙 관리 영역·flat 배지·다운로드·설치 링크 적용. 독립 리뷰에서 기존 본문/갤러리/예제/출처·폰트 고지 보존 및 양언어 의미 일치 확인 |
| DOC-07 | PASS | blesession 미사용이므로 고정 blesession 템플릿 자동 검사 대상 아님. proxy 안내와 기기별 준비/문제 해결 유지, README 및 사용자 문서의 언어별 blesession 원본 링크 확인 |
| DOC-08 | PASS | docs/payload.md 및 payload.ko.md, 실제 marklife.print YAML 2개, 중앙 scaffold 및 production 준비 함수 adapter. 실제 HA schema 및 설치된 imagespec validate/render 두 환경 2 passed. 템플릿 state·내장 폰트·384×96/흑백 출력 및 실제 prepare 경로 독립 검토 |
| HACS-05/CI-04 원격 실행 | PASS | PR #14 head 159f618: Tests 6 jobs, Validate 3 jobs 모두 성공. 아래 실행 근거 참조 |
| GOV-04 기본 브랜치 반영 | TODO | 사용자 요청에 따라 최종 head CI 후 스쿼시 머지 진행. 최종 merge commit 및 main CI는 PR #14와 중앙 현황표에서 확인 |
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

- PR #14 head `159f6185e5b99a1661d136ddedaa1bb335e4802b`의 [Tests CI](https://github.com/eigger/hass-marklife/actions/runs/39426327885) 6 jobs 및 [Validate CI](https://github.com/eigger/hass-marklife/actions/runs/39426327855) 3 jobs 성공. 4 HA/library matrix 각각 payload 2 passed 및 회귀 186 passed, 6 skipped; 실제 imagespec 1.1.0. Ubuntu Python 3.14.8/3.13.16. 기본 브랜치 required checks 설정은 변경하지 않았습니다.
- 이 기록 변경의 최종 head CI 및 merge/main 상태는 [PR #14](https://github.com/eigger/hass-marklife/pull/14)에서 확인합니다. 위 PASS 증거는 명시한 159f618에 대한 결과입니다.
- 실물 BLE 인쇄, 실제 프록시·기기 조합, HA frontend는 새로 검증하지 않았습니다. 기존 실물 이력은 기존 범위의 증거입니다.
- 중앙 현황은 로컬만 수정했습니다. 사용자 머지 요청으로 PR #14를 생성했으며 tag/Release는 생성하지 않습니다.

## 예외

없음. 최종 미검증 항목을 완료로 기록하지 않습니다.

## 2026-10-23 Downloads 배지 부분 검증

- 기준: 중앙 `b54ac48102d6e326c6929071fdc02ba8fade794e`의 DOC-03/05·배지 생성기와 Validate 형식 검사기만 부분 채택. 대상 시작 SHA `a0d935d0248be14d4ab0c8fdfeaaa8f62a24297e`. 기존 전체 채택 결과·예외는 유지하며 이번 변경으로 전체 재채택 완료를 주장하지 않습니다.
- 계획/자체 리뷰: 양언어 관리 블록을 같은 중앙 렌더러로 생성, 잘못된 HACS 데이터 조회 배지를 Downloads로 교체, 집계 의미와 소스 파일 설치 제외를 양언어로 명시. GOV-02에 따라 중앙 호출 pin과 standards-ref를 같은 SHA로 맞춥니다. 이전 기준과 새 기준의 공용 workflow/action 파일은 동일하며 실행 설정·지원 최소·ZIP 배포 설정을 보존합니다.
- 검증 명령·결과와 최종 head SHA·원격 CI 링크는 이 PR 본문에 기록합니다. 문서·배지·형식 검사기 pin만 변경하므로 로컬 HA 환경을 재구축하지 않으며 실제 기기·HA UI·사용자 다운로드 집계는 미검증입니다.
- 실행 결과: WSL Ubuntu Python 3.14.4/PyYAML 6.0.3/packaging 26.0에서 중앙 `scripts/sync_badges.py <repo> --check`, `scripts/check_integration.py <repo>` 및 actionlint 1.7.12의 전체 caller workflow 검사 PASS. Windows Git의 `git diff --check` PASS. 양언어 배지 외 기존 본문은 집계 설명의 정정·추가만 허용하고 보존했습니다.
- 초기 검사 실패 기록: 단일 기준 SHA 계약에 맞지 않는 검사기 pin만의 갱신은 GOV-02에서 거부되어 모든 중앙 pin을 동일 SHA로 정합화했습니다. Windows 중앙 템플릿 CRLF 비교는 실패하여 LF 중앙 snapshot의 Linux 검사로 재검증했습니다. WSL Git은 Windows worktree gitdir 경로를 해석하지 못해 diff 검사를 실패했고 동일 변경의 Windows Git 검사로 대체했습니다. 실패를 PASS로 소급하지 않습니다.

## 2026-10-23 ZIP 릴리스 적용 검증

- 기준 `0c1592977591ecba077a4666d699840062711201` / 대상 시작 `623179ed6820660c3aeb6d53358681abfbf631d1`. HACS-04/CI-11 부분 갱신이며 기존 전체 채택 이력·예외는 유지합니다.
- 계획: hacs.json에 zip_release:true, filename:marklife.zip을 추가하고 중앙 release.yml을 같은 SHA로 생성합니다. 기존 caller는 중앙 pin/standards-ref만 변경합니다. 지원 최소·통합 버전·의존성·구현·README 본문을 보존합니다.
- 검증: 중앙 생성기/정적 검사·actionlint·실제 packager로 추적된 통합 파일의 ZIP 루트·manifest/번역/brand 등 런타임 자료 포함과 저장소 메타데이터 제외를 확인합니다. CLI 검증 명령·실제 버전·최종 head SHA·ZIP 결과·독립 리뷰·원격 CI 링크는 이 PR 본문에서 한 번 기록합니다.
- 중앙 실행 로직은 독립 zip_release_review 리뷰에서 지적 수정 후 추가 지적 없음. 대상 caller/메타데이터/ZIP도 별도 독립 리뷰합니다. 로컬 HA 환경 재구축·새 릴리스 발행·asset 업로드·기기 설치는 수행하지 않으며 미실행을 PASS로 기록하지 않습니다. immutable-releases는 enabled:false로 확인했습니다.


## blesession 및 진단 센서 적용 (2026-10-23)

- 범위: 기존 공용 CI 구조를 유지하고 `blesession>=0.9.0`을 런타임에 추가. 최소 의존성 matrix와 updater 대상에 blesession 포함.
- `hass-niimbot`의 세션·오류 보존 방식을 참고해 연결 재사용, 연결 해제 감지, 구독 복구/정리, 전송 시간 제한을 적용. 기존 Marklife 패킷·크레딧 흐름 제어와 인쇄 후 연결 종료 정책은 유지하며 실패한 인쇄를 자동 재전송하지 않음.
- 기존 Connection 엔티티 ID를 유지하고 진단 범주와 최근 세션 속성을 추가. Last error / Error count 진단 센서를 추가하고 Print Duration에 최근 인쇄 세션을 보존. 정기 조회의 unreachable/connect 실패는 오류 횟수와 최근 실제 실패를 덮어쓰지 않음. 연결 후 완전 무응답은 기존 측정값을 유지하며 timeout으로 기록.
- 실물 Marklife 프린터 및 ESPHome proxy에서 이번 변경의 동작은 미검증. 아래는 외부 GATT 통신만 대체한 실제 HA 통합 테스트 결과.

| 환경 | 실제 설치 버전 | 검증 결과 |
|---|---|---|
| current | Python 3.14.7 / HA 2026.10.2 / pytest HA plugin 0.13.373 / blesession 0.9.0 / imagespec 1.1.0 | 197 passed, 6 skipped; uv pip check PASS |
| minimum HA 및 정확한 라이브러리 하한 | Python 3.13.15 / HA 2025.9.0 / pytest HA plugin 0.13.277 / blesession 0.9.0 / imagespec 1.1.0 | 197 passed, 6 skipped; uv pip check PASS |

- 전체 회귀는 중앙 payload plugin을 포함해 실행: `PYTHONPATH=../hass-repo-standards/scripts PAYLOAD_REPOSITORY="$PWD" PAYLOAD_DOMAIN=marklife python -m pytest -p hass_standards_payload tests/components/marklife/ -q` (WSL Ubuntu).
- 신규 회귀: 연결 재사용 및 갑작스러운 해제/복구, 인쇄 연결 실패와 이후 성공 시 오류 보존, unreachable, 조회 중 링크 해제, 부분 구독 실패 정리, 취소 시 정리, 전송 실패 시 재인쇄 방지, 조회 완전 무응답, GATT WriteTimeout 원인 보존.
- Ruff check / format check 및 git diff --check PASS. 중앙 DOC-07 문서 검사 통과. 최신 중앙 전체 검사는 기존 README.md / README.ko.md 관리 헤더의 DOC-01 경고 2건으로 미통과이며, 해당 헤더가 HEAD와 동일함을 확인. 사용자 요청 범위에 맞춰 헤더/공용화 재적용은 하지 않음.
- 원격 HACS/Hassfest는 이 로컬 변경에서 실행하지 않음.

### 추가 자체 리뷰 (2026-10-23)

- GATT의 BleakError가 인쇄 서비스 경계에서 HomeAssistantError로 변환되지 않는 기존 누락을 보완. 서비스 메시지 주소 마스킹, 진단 기록 및 연결 정리를 함께 검증하는 회귀 테스트 추가.
- 변경 후 관련 세션·서비스 회귀는 current/minimum HA 각각 22 passed. Ruff 및 git diff --check PASS. 앞선 전체 197 passed는 이 추가 수정 전 결과이며, 추가 수정 후에는 관련 회귀를 실행함. 독립 리뷰는 수행하지 않음.


### 독립 리뷰 및 PR 검증 (2026-10-23)

- 사용자 승인에 따라 `/root/independent_review` 서브 에이전트가 전체 변경 및 신규 파일을 독립 리뷰. blesession 0.9.0 구현과 연결 수명·중단 처리·오류 보고를 대조한 결과 지적사항 없음. HA 2026.10.2에서 신규 세션 테스트 10 passed를 독립 실행.
- 최종 코드의 전체 회귀는 current HA 2026.10.2 / minimum HA 2025.9.0 각각 중앙 payload contract 포함 198 passed, 6 skipped. 두 환경 blesession 0.9.0 및 imagespec 1.1.0, 의존성 검사 PASS. Ruff check / format check 및 git diff --check PASS.
- 검토·병합 대상은 [PR #17](https://github.com/eigger/hass-marklife/pull/17). 병합 전 최종 head의 원격 Tests와 Validate 결과를 확인하며, 실제 결과는 PR에 연결된 check 기록을 근거로 함.
- 실물 프린터 및 ESPHome proxy 검증은 미진행. 최신 중앙 전체 검사에 있는 기존 README 헤더 DOC-01 경고 2건은 별도이며, 채택된 중앙 ref의 원격 compliance 결과와 혼동하지 않음.

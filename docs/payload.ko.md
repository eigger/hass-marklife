# Marklife payload 안내

[README](../README.ko.md) · [English](payload.md)

## 공통 payload 안내

[imagespec payload 안내](https://github.com/eigger/imagespec/blob/main/docs/payload.ko.md)에서 요소 문법, 색상, 회전 및 디더링을 설명합니다. Marklife는 설치된 `imagespec[datamatrix]>=1.1.0` 렌더러를 사용합니다.

## 이 통합에서 payload 사용

`marklife.print` 액션에서 구성한 프린터의 `device_id`를 대상으로 지정하고 `data.payload`에 목록을 넣습니다. Home Assistant가 렌더링 전에 액션 템플릿을 처리합니다. 예제 대상은 `sensor.p15_0000_ddeeff_battery`의 기기를 찾으므로 실제 프린터의 배터리 센서로 바꾸거나 액션 편집기에서 기기를 선택하세요. `preview: true`이면 인쇄하지 않고 base64 PNG를 반환합니다. 실제 인쇄 시 이 옵션을 지우거나 false로 설정하세요.

실제 렌더러는 통합 내장 폰트에서 `ppb.ttf`를 찾고, 다른 폰트 이름은 통합 폰트 디렉터리 또는 `/config/www/fonts`에서 찾습니다. imagespec 이력 요소에는 recorder 이력을 제공하며 요청한 엔티티와 시간 범위의 데이터가 필요합니다. Home Assistant 템플릿은 액션 데이터에 작성하며 렌더러 내부에서 별도의 Jinja 처리를 추가하지 않습니다.

## 최소 동작 예제

[최소 전체 액션 YAML](../examples/payload/minimal.yaml)은 기존 빠른 시작의 텍스트와 QR 코드를 384 × 96 픽셀 라벨에 그립니다. [템플릿 액션 YAML](../examples/payload/template.yaml)은 실제 프린터 배터리 상태와 내장 폰트를 사용합니다. 두 예제 모두 미리보기 모드이며 계약 검증 중 프린터 명령을 보내지 않습니다.

## 기기 출력 설정

동작을 검증한 P15의 헤드 폭은 384도트입니다. 너비 기본값은 선택한 기기 프로필의 헤드 폭이며 높이 기본값은 240픽셀입니다. 이 예제는 너비 384, 높이 96을 명시합니다. 출력은 흑백이며 디더링은 비활성입니다. `rotate` 기본값은 0이며 90도 또는 270도 이미지 회전 시 출력 너비와 높이가 바뀔 수 있습니다. 다른 프린터의 크기는 [모델 표 및 방향 안내](ko/user-guide.md)를 확인하세요. 이 설명이 미검증 모델 제품군의 실물 검증을 의미하지는 않습니다.

## 지원 기능과 제한

설치된 imagespec 버전이 지원 요소를 결정하며 선언한 최소 의존성에는 datamatrix extra가 포함됩니다. 링크한 예제는 텍스트, QR 코드, 실제 Home Assistant 상태 템플릿을 실행합니다. 폰트는 로컬에 있어야 합니다. 이력은 recorder 데이터가 필요하며 원격 이미지는 실행 시 실제 네트워크 원본이 필요합니다. 계약 검증은 원격 이미지나 기기 쓰기를 사용하지 않습니다. 프린터에는 흑백 래스터를 전송합니다. README에 명시한 Bluetooth Classic 및 독자 규격 모델은 지원하지 않습니다. 기존 [고급 예제](ko/user-guide.md)와 기기 제한도 유지됩니다.

## 문제 해결

먼저 액션 템플릿, 기기 선택, 로컬 폰트, 크기 및 imagespec 오류를 확인하세요. 인쇄 전 미리보기 모드로 렌더링을 점검하세요. BLE 연결과 전송 문제는 [기기 문제 해결](ko/troubleshooting.md)을 따르세요. 재현 가능한 렌더링 문제는 기존 [Issues](https://github.com/eigger/hass-marklife/issues) 절차에 따라 민감 정보를 제거한 액션 데이터와 버전을 첨부하세요.

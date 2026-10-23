# Marklife 사용자 가이드

[English](../../docs/user-guide.md) | [홈](../../README.ko.md)

Marklife 통합의 지원 모델, 설정 옵션, 엔티티, 서비스 및 `imagespec` 라벨 서식에 대한 상세 안내입니다.

## 갤러리

| P15 |
| :---: |
| <img src="../images/p15.jpg" width="300" alt="Marklife P15"> |

> BLE 프로토콜 레이어는 [tomLadder/thermoprint](https://github.com/tomLadder/thermoprint) (MIT) 기반입니다.
> [Stash](https://github.com/eigger/stash)를 통해 이 Home Assistant 통합으로 라벨을 인쇄할 수 있습니다.

---

## 지원 모델

Home Assistant가 연결 가능한 모든 Marklife 프린터는 두 가지 BLE 프로토콜 제품군으로 구성됩니다.
**표의 상태는 구현 지원 여부이며, 보유 기기에서의 실물 동작 확인을 권장합니다.**

| 모델 | 제품군 | 헤드 폭 | 상태 |
|---|---|---|---|
| P15, P15R, P15S | L11 | 384 px | ✅ P15 동작 확인됨 |
| P7, P7R | L11 | 384 px | 미검증 — thermoprint 프로토콜 검증됨 |
| P12, P11 | L11 | 384 px | 미검증 — thermoprint 프로토콜 검증됨 |
| P1s, M1, S15, S12, LP15, LP90, LPC74, iSPACE_LP15, OUT_LPC | L11 | 384 px | 미검증 — 제조사 앱에서 P15/P12 프로필로 매핑됨 |
| M60, X2 | Compressed | 384 px (미확인) | 미검증 — thermoprint 프로토콜 검증됨 |
| P50, P50S, D50, ewtto ET- | Compressed | 미확인 | 미검증 — APK 분석 프로필 |
| P80, T3 | Compressed | 미확인 | 미검증 — **흐름 제어 없음** |

### 지원하지 않는 기기

| 모델 | 이유 |
|---|---|
| S8, D210, 210, IP_D80, DP_D80, DP_8028, HM-24-28, A31, U210, A50, X8 | Home Assistant의 Bluetooth 스택 및 ESPHome 프록시에서 지원하지 않는 구형 규격(Bluetooth Classic)을 사용합니다. |
| D100, X4, L100, D200 | 현재 지원할 수 없는 비공개 독자 통신 방식을 사용합니다. |

이들 기기를 추가하려고 하면 무시되지 않고 명시적으로 미지원 전송 방식임을 안내합니다.

---

## 설정 및 옵션

대부분의 설정은 프린터 모델에 맞춰 기본값이 제공됩니다. 설정 변경은 **설정** → **기기 및 서비스** → **Marklife** → **구성**에서 가능합니다.

### 초기 설정 옵션

| 옵션 | 기본값 | 범위 | 설명 |
|---|---|---|---|
| **검색 주기 (Scan interval)** | 600 | 30–9999초 | 배터리 및 상태 조회 주기 |
| **BLE 연결 유지 (Keep connection)** | 꺼짐 | 켜짐/꺼짐 | 인쇄 작업 간 연결 유지 (프록시 연결 슬롯 점유) |

### 고급 설정 (구성 대화상자)

| 옵션 | 기본값 | 범위 | 설명 |
|---|---|---|---|
| **패킷 간격 (Packet interval)** | 0 | 0–200 ms | 패킷 사이 최소 지연. `0`은 모델 프로필 기본값 사용 (대부분 30 ms, M60/X2는 1 ms) |
| **흐름 제어 대기 시간 (Starvation timeout)** | 2000 | 500–10000 ms | 크레딧 수신 지연 시 강제 전송 대기 시간 |
| **최대 패킷 크기 (Max packet size)** | 180 | 20–237 B | 협상된 MTU와 무관한 상한선 |

*참고:* Niimbot과 달리 Marklife 프린터는 두 프로토콜 제품군 모두 부저/음량 제어 명령을 지원하지 않습니다.

---

## 엔티티

| 엔티티 | 설명 |
|---|---|
| `sensor.<device>_battery` | 배터리 잔량 (%) |
| `sensor.<device>_status` | 현재 상태: `out_of_paper`, `cover_open`, `overheating`, `low_battery`, `cover_closed` |
| `sensor.<device>_last_error` | 최근 오류. 실패 세션의 단계, 연결 경로, 소요 시간, 추정 원인을 속성으로 보존 |
| `sensor.<device>_error_count` | 통합 설정 이후 오류 횟수 (다시 로드하거나 재시작하면 초기화) |
| `sensor.<device>_print_duration` | 인쇄 소요 시간 (초, 인쇄 중 실시간 / 완료 후 최종 시간) |
| `binary_sensor.<device>_out_of_paper` | 용지 부족 시 켜짐 |
| `binary_sensor.<device>_cover_open` | 덮개 열림 시 켜짐 |
| `binary_sensor.<device>_overheating` | 헤드 과열 시 켜짐 |
| `binary_sensor.<device>_low_battery` | 배터리 부족 시 켜짐 |
| `binary_sensor.<device>_connection` | 블루투스 연결 상태 |
| `binary_sensor.<device>_printing` | 인쇄 진행 중 여부 |
| `image.<device>_last_label_made` | 최근 인쇄 또는 미리보기로 생성된 라벨 이미지 |

*참고:* Marklife 프린터는 한 번에 하나의 상태만 보고하므로, 장애 센서는 한 시점에 최대 하나만 활성화됩니다.

---

## 서비스: `marklife.print`

### 파라미터

| 파라미터 | 필수 | 기본값 | 설명 |
|---|---|---|---|
| `payload` | 예 | — | [imagespec 요소 목록](https://github.com/eigger/imagespec/blob/main/docs/elements.md) |
| `width` | 아니오 | 프린터 헤드 폭 | 캔버스 폭 (픽셀 단위, 기본 384) |
| `height` | 아니오 | `240` | 캔버스 높이 (픽셀 단위) |
| `rotate` | 아니오 | `0` | 회전 각도: `0`, `90`, `180`, `270` |
| `density` | 아니오 | 프로필 기본값 | 인쇄 농도: 1–3 |
| `paper_type` | 아니오 | `gap` | `gap` (다이컷 롤 라벨) 또는 `continuous` (연속 용지) |
| `copies` | 아니오 | `1` | 인쇄 매수 |
| `preview` | 아니오 | `false` | 실제 인쇄 없이 이미지만 렌더링하여 엔티티 업데이트 |

### 기본 예제

```yaml
action: marklife.print
target:
  device_id: <기기 ID>
data:
  payload:
    - type: text
      value: 안녕하세요!
      font: ppb.ttf
      x: 10
      y: 10
      size: 40
    - type: qrcode
      data: "https://www.home-assistant.io"
      x: 270
      y: 10
      width: 80
      height: 80
  width: 384
  height: 96
```

### 40 × 12 mm 라벨 (P15 기본 규격)

자연스러운 읽기 방향으로 디자인한 뒤 `rotate: 90`을 지정하면 출력 축이 교환되어 12 mm 쪽이 헤드 폭에 맞게 인쇄됩니다:

```yaml
action: marklife.print
target:
  device_id: <기기 ID>
data:
  payload:
    - type: text
      value: "팬트리"
      font: ppb.ttf
      x: 8
      y: 20
      size: 48
  width: 320      # 40 mm x 8 dots/mm — 용지 진행 방향
  height: 96      # 12 mm x 8 dots/mm — 헤드 가로 방향
  rotate: 90      # -> 96 x 320 래스터로 변환
  paper_type: gap
  density: 2
```

### 연속 용지

```yaml
action: marklife.print
target:
  device_id: <기기 ID>
data:
  payload:
    - type: text
      value: "{{ now().strftime('%Y-%m-%d %H:%M') }}"
      x: 8
      y: 8
      size: 32
  height: 64
  paper_type: continuous
```

### 인쇄 없이 미리보기

`preview: true`를 지정하면 용지를 소모하지 않고 라벨 이미지만 생성하여 `image.<device>_last_label_made` 엔티티로 확인할 수 있습니다:

```yaml
action: marklife.print
target:
  device_id: <기기 ID>
data:
  preview: true
  payload:
    - type: text
      value: 미리보기 테스트
      x: 10
      y: 10
      size: 30
  width: 384
  height: 96
```

---

## 사용자 지정 글꼴

`.ttf` 파일을 `custom_components/marklife/fonts/` 또는 `config/www/fonts/`에 저장하고 파일 이름(예: `ppb.ttf`)으로 참조합니다.

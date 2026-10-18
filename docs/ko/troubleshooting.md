# Marklife 문제 해결

[English](../../docs/troubleshooting.md) | [홈](../../README.ko.md)

ESPHome 프록시 설정, 추천 기기(XIAO W5500 이더넷 어댑터 V1.2, M5Stack AtomS3U 등) 및 일반적인 Bluetooth 문제 해결은 [Bluetooth 프록시 안내](https://github.com/eigger/hass-repo-standards/blob/main/docs/bluetooth.ko.md#troubleshooting)를 참고하세요.

## 1. 프린터 준비 및 사전 점검

- **전원 및 절전 해제**: 프린터가 충전되어 있고 켜져 있는지 확인합니다. 대기 상태에서는 BLE 절전 모드로 전환되므로 연결 전 전원 버튼을 눌러 깨워주세요.
- **용지 및 덮개**: 용지가 올바른 방향으로 장착되어 있고 덮개가 완전히 닫혔는지 확인합니다. 덮개 열림, 용지 부족, 헤드 과열 상태에서는 인쇄 명령이 거부됩니다.
- **스마트폰 앱 연결 해제**: BLE 프린터는 한 번에 하나의 기기(중앙 기기)와만 연결할 수 있습니다. 스마트폰 제조사 앱(Marklife)이 연결되어 있으면 Home Assistant가 연결할 수 없습니다.
- **지원 모델 확인**: Bluetooth Classic을 사용하는 구형 모델(S8, D210 등)이나 비공개 독자 규격 모델(D100, X4)은 BLE로 연결할 수 없습니다. [지원 모델](user-guide.md#지원-모델)을 확인하세요.

## 2. 증상별 점검 및 해결

| 증상 | 점검 및 조치 |
|---|---|
| **검색되지 않음** | 프린터가 켜져 있고 블루투스 신호를 브로드캐스트하는지 확인합니다. 프록시 거리와 온라인 상태를 점검하세요. 알려진 이름 접두사와 다르면 수동 추가 단계를 이용하세요. |
| **발견되지만 연결 실패** | ESPHome 프록시의 `bluetooth_proxy` 설정에서 `active: true`가 활성화되어 있는지 확인합니다. ESP32 프록시는 동시 연결을 최대 3개까지만 지원하므로 슬롯 고갈 여부를 확인하세요. 스마트폰 블루투스 연결을 해제하세요. |
| **인쇄가 중간에 멈추거나 줄이 빠짐** | 흐름 제어 크레딧 지연 현상입니다. 통합 구성(**Configure**)에서 **흐름 제어 대기 시간 (Starvation timeout)**을 3000–5000 ms로 늘리거나, **최대 패킷 크기 (Max packet size)**를 100–120 바이트로 낮춰보세요. |
| **연결 후 응답 없음** | Marklife 프린터는 상태 코드를 한 번에 하나씩 보고합니다. `sensor.<device>_status`를 확인하여 용지 부족이나 덮개 열림 상태가 아닌지 확인하세요. |

## 3. 진단 엔티티 확인

Home Assistant의 **설정** → **기기 및 서비스** → **Marklife** → 해당 기기에서 엔티티 상태를 확인하세요:

- `sensor.<device>_status`: `cover_closed`, `cover_open`, `out_of_paper`, `overheating`, `low_battery` 보고.
- `sensor.<device>_battery`: 기기 배터리 잔량 (%).
- `binary_sensor.<device>_connection`: 활성 BLE GATT 연결 상태.
- `binary_sensor.<device>_printing`: 래스터 데이터 전송 및 인쇄 진행 중 여부.
- `image.<device>_last_label_made`: 최근 렌더링된 라벨 이미지를 확인하여 출력 서식 검증.

## 4. 문제 보고 (이슈 등록)

문제를 보고하기 전 디버그 로그를 활성화하세요:

```yaml
logger:
  default: warning
  logs:
    custom_components.marklife: debug
```

[Issues](https://github.com/eigger/hass-marklife/issues)에 글을 남길 때:
- 블루투스 MAC 주소 및 개인 인쇄 내용 등 민감 정보는 제거해 주세요.
- 프린터 모델명과 블루투스 검색 시 표시되는 정확한 이름을 적어주세요.
- 블루투스 어댑터 종류(로컬 동글 또는 ESPHome 프록시 보드 및 버전)를 명시해 주세요.
- 인쇄 시도 전후의 디버그 로그를 첨부해 주세요.

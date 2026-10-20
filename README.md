# VoIP와 olsrd 0.6.8 패킷 백서

한국어 기술 백서 두 권입니다. 각 메시지가 언제 송신되는지, 공통 헤더와 주요 바이트 필드를 어떻게 해석하는지, 어떤 원문과 구현 코드가 근거인지를 정리했습니다.

| 백서 | PDF | 편집 가능한 Word |
|---|---|---|
| VoIP 표준 패킷과 메시지 | [PDF 열기](whitepapers/VoIP_Standard_Packets_Whitepaper_KO.pdf) | [Word 다운로드](whitepapers/VoIP_Standard_Packets_Whitepaper_KO.docx) |
| olsrd 0.6.8 패킷 구현 | [PDF 열기](whitepapers/olsrd_0.6.8_Implementation_Whitepaper_KO.pdf) | [Word 다운로드](whitepapers/olsrd_0.6.8_Implementation_Whitepaper_KO.docx) |

기준일은 **2026년 10월 20일**입니다.

## VoIP 백서

SIP 등록·호 설정·변경·종료, SDP, RTP/RTCP, DTMF, 무음, 복구, STUN/TURN/ICE, TLS·DTLS·SRTP/SRTCP와 게이트웨이 제어를 설명합니다.

- SIP 요청 메서드 14종과 IANA 응답 코드 75종
- 등록된 RTP 오디오 미디어 하위 유형 94종
- RTCP 패킷 유형, RTPFB·PSFB FMT, XR 블록, SDES 항목과 STUN 메서드 전체 등록 목록
- ITU-T 2022년 3월판의 H.225.0 RAS 33개·호출 신호 본문 13개 선택지
- 같은 판의 H.245 Request 16개·Response 25개·Command 13개·Indication 24개 선택지
- H.248 기본 명령과 MGCP·IAX2의 문서 지위 구분

VoIP는 하나의 프로토콜이 아니므로 표준의 모든 가능한 바이트열을 유한 목록으로 제시할 수는 없습니다. 백서는 프로토콜 메시지 유형과 지정한 등록 목록을 다룹니다. 코덱별 전체 비트스트림, 모든 3GPP·ITU-T 서비스 부속서와 H.248 패키지는 각 원문 규격을 따릅니다. IANA 등록은 모든 장치의 필수 구현이나 Standards Track 지위를 뜻하지 않습니다.

## olsrd 백서

[공식 v0.6.8 커밋](https://github.com/OLSR/olsrd/commit/51ac86b22ee2bdb1077c889859ad3ca5a39aa079)을 기준으로 실제 생성·직렬화·수신·중계 코드를 확인했습니다. v0.6.8.1, v0.6.8-eol, 최신 master 및 olsrd2와 구분합니다.

- 기본 HELLO·TC·MID·HNA와 기본 설정의 LQ_HELLO 201·LQ_TC 202
- 주소별 LQ/NLQ, ETX, TC border, FishEye TTL과 유효시간 양자화
- Smart Gateway HNA 확장
- secure, nameservice, mdns, p2pd, PUD, BMF와 관리 포트
- mdns·p2pd의 IPv6 길이식 불일치와 secure의 ABI 의존 조건
- 합성 16진수 예제와 길이 계산

검증은 **정적 소스 분석과 오프라인 합성 예제**입니다. 데몬을 실제 메시 네트워크에서 실행하거나 소스 특이점의 악용 가능성을 실험한 결과는 아닙니다.

## 근거 자료와 예제

| 경로 | 내용 |
|---|---|
| `sources/provenance.json` | 고정 커밋, 공식 원문 URL, 소스 파일 36개의 SHA256, IANA 스냅샷 해시 |
| `sources/*.xml` | SIP, RTP, SDP, STUN, RTCP XR 공식 IANA 스냅샷 |
| `sources/packet_inventory.json` | 메시지·헤더·등록값의 파생 목록 |
| `sources/h323_message_inventory.json` | 지정한 ITU-T 판의 최상위 ASN.1 메시지 선택지와 원문 PDF 해시 |
| `examples/packet_examples.json` | 합성 패킷 13개의 바이트와 설명 |
| `examples/synthetic_examples.pcap` | IPv4 외피를 붙인 합성 패킷 11개 |
| `verification.json` | 최종 파일 해시와 문서·패킷 검증 기록 |

PCAP은 문서용 합성 데이터입니다. 실제 사용자의 통화, 비밀번호, 키 또는 장비 캡처를 포함하지 않습니다. 생성 스크립트는 네트워크 소켓을 열지 않습니다.

## 재생성

Python 3.10 이상과 `python-docx`가 필요합니다.

```console
python -m pip install -r requirements.txt
python tools/build_whitepapers.py
python tools/packet_examples.py
```

Windows에 Microsoft Word가 설치되어 있으면 다음 명령으로 목차를 갱신하고 DOCX를 저장한 뒤 PDF를 내보낼 수 있습니다.

```powershell
powershell -ExecutionPolicy Bypass -File tools/export_word.ps1
```

다른 운영체제에서는 생성된 DOCX를 Word 또는 호환 프로그램에서 열어 목차를 갱신하고 PDF로 내보냅니다. 프로그램과 폰트에 따라 페이지 배치는 달라질 수 있습니다. 배포 PDF가 검토한 기준본입니다. 배포본은 맑은 고딕으로 제작하고 모든 페이지를 이미지로 렌더링해 검토했습니다.

상위 olsrd 소스를 별도로 내려받은 경우 다음과 같이 근거 해시를 다시 기록할 수 있습니다.

```console
python tools/record_provenance.py /path/to/olsrd-0.6.8 --archive /path/to/olsrd-v0.6.8.zip
```

원문 RFC·ITU-T 문서와 olsrd 코드의 권리는 각 원저작자와 해당 라이선스에 따릅니다. 이 저장소에는 olsrd 전체 소스와 ITU-T 원문 PDF를 재배포하지 않으며 공식 원문 링크와 필요한 식별 목록을 제공합니다.

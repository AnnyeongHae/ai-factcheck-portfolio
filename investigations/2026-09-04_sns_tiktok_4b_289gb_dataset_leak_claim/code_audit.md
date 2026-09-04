# Engineering Code & Architecture Audit

## 1. 데이터셋 스키마 포렌식 (Hugging Face)
- **저장소**: `kuben-developer/tiktok-videos-4b`
- **구조**: `videos-00.parquet` ~ `videos-26.parquet` (총 27개 파일, 압축 289GB, 45억 행)
- **실제 컬럼 확인 (DuckDB DESCRIBE)**:
  - `content_id`: UBIGINT (영상 고유 식별자)
  - `create_time`: TIMESTAMP WITH TIME ZONE
  - `desc`: VARCHAR (캡션 및 해시태그)
  - `views`, `likes`, `comments`, `shares`, `saves`: UBIGINT (인게이지먼트 지표)
  - `music_title`, `music_id`: VARCHAR / UBIGINT (사용 음원 메타데이터)
  - `country`, `language`: VARCHAR (국가 및 언어 코드)
  - `duration`: USMALLINT (재생 시간)
  - `is_video`, `is_ad`: UTINYINT

> **핵심 검증 결과**: 미디어 스트림 URL 및 MP4 바이너리는 전혀 존재하지 않음. TikTok CDN 링크는 유효기간이 며칠 내로 만료되므로 제작자가 의도적으로 제외함.

## 2. 수집 엔진 역공학 분석 (SeekSocial 리포트)
- **개발 언어**: Go 1.24
- **주요 우회 기술**:
  1. **Device Simulation**: Samsung SM-A136U 등 250개 실기기 프로필 및 2,000개 MCC/MNC 매핑.
  2. **Activation Telemetry**: `/service/2/app_alert_check` 호출로 앱 최초 실행을 위장하지 않으면 HTTP 200 (Empty Body)으로 차단됨.
  3. **5대 서명 헤더**: X-Khronos, X-Ss-Stub, X-Gorgon, X-Ladon (Speck-128/256), X-Argus (Protobuf -> SM3 -> Simon-128/256 -> XOR Mix -> AES-128-CBC).
  4. **TLS JA3 Spoofing**: `uTLS`의 `HelloAndroid_11_OkHttp` 지문 적용.

## 3. 무다운로드(Zero-Download) 스트리밍 구현 (DuckDB HTTPFS)
```python
import duckdb

con = duckdb.connect()
con.execute("INSTALL httpfs; LOAD httpfs;")
url = "https://huggingface.co/datasets/kuben-developer/tiktok-videos-4b/resolve/main/videos-00.parquet"

# HTTP Range Request로 메타데이터 푸터만 읽어 43초 만에 상위 10개 조회
res = con.execute(f'''
    SELECT content_id, views, likes, shares, country, music_title, "desc"
    FROM read_parquet('{url}')
    WHERE likes > 100000
    ORDER BY likes DESC
    LIMIT 10;
''').fetchdf()
```

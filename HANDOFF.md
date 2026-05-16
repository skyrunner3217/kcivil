# KCI 콘크리트학회 논문 데이터베이스 — 기술 인수인계서

> 작성: 박민준(수집), 김서연(분석) | 검토: 이준호(QA), 장미래(아키텍트), 박지수(문서) | 2차: 김동현, 최수아, 홍태준 | 최종 승인: 박성민, 이현정  
> **기준: 21,029편 (2026-05-15)** | 경로: `~/claude/kci-concrete/`  
> **배포 URL**: https://skyrunner3217.github.io/kci-concrete/dashboard.html

---

## 0. 프로젝트 목적

KCI 논문(1989~현재)을 자동 수집·정규화하여 저자 공저 네트워크 + 주제 군집 분석 가능한 연구 인프라. 대시보드는 내부 분석용. KSMI·IJCSM 확장 전제.

---

## 1. 현재 상태 스냅샷 (2026-05-15)

| 항목 | 상태 |
|---|---|
| KCI 학회지 수집 | 완료 (2,801편) |
| KCI 학술대회 수집 | 완료 (18,228편) |
| dashboard.html | 정상 (21,029편, 18MB) |
| clusters.json | ⚠ 구버전 (2,108편 기준) — 즉시 재생성 필요 |
| KSMI 수집 | 미착수 (scraper.py 코드는 구현 완료) |

---

## 2. 디렉토리 구조

```
kci-concrete/
├── crawl/
│   └── scraper.py              # 수집기
├── analyze/
│   ├── build_network.py        # 공저 네트워크 구축
│   ├── embed_cluster.py        # 의미 군집화 (OpenAI 필요, 선택 실행)
│   ├── make_dashboard.py       # 대시보드 HTML + topic_trends.json 생성
│   └── make_viewer.py          # 군집 뷰어 HTML (embed_cluster 실행 후)
├── meta/
│   ├── journal/                # 학회지 논문 메타 JSON (1편=1파일)
│   └── conference/             # 학술대회 논문 메타 JSON
├── papers/
│   ├── journal/                # 마크다운 (아카이브, 분석에 미사용)
│   └── conference/
├── network/                    # 분석 산출물 (아래 섹션 9 참고)
├── logs/
│   └── progress.json           # 수집 진행 상태 (권호 단위 체크포인트)
├── run.py                      # scraper.py 래퍼 (refresh.sh --collect 시 호출)
├── patch_abstracts.py          # 초록 누락 보완 패치
├── patch_conference_pages.py   # 학술대회 페이지 보완 패치
├── fix_data.py                 # 데이터 정제
├── refresh.sh                  # 전체 분석 파이프라인
├── install.sh                  # 초기 셋업
└── requirements.txt            # 기본 의존성
```

---

## 3. 초기 셋업

```bash
# 기본 설치 (수집 + 네트워크 분석용)
bash install.sh
# 수동: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

# embed_cluster.py 사용 시 추가 설치
.venv/bin/pip install openai umap-learn hdbscan
```

**OpenAI API 키** (embed_cluster.py 실행 전 필수):
```bash
# .env 파일은 자동 로드 안 됨. 반드시 export 사용.
export OPENAI_API_KEY="sk-..."
# 자동 적용: set -a; source .env; set +a
```

---

## 4. 전체 흐름

```
[수집] bash refresh.sh --collect
          → run.py (래퍼) → crawl/scraper.py
            → meta/journal/, meta/conference/, logs/progress.json

[분석] bash refresh.sh
  [2/4] refresh.sh 인라인 Python
        → network/papers_lite.json
        → network/yearly_stats.json   ← 이 단계가 생성 (build_network.py가 아님)
        → network/author_papers.json
  [3/4] analyze/build_network.py
        → network/graph_d3.json, stats.json, graph.graphml, graph.gexf, top_authors.txt
  [4/4] analyze/make_dashboard.py
        → network/dashboard.html (18MB)
        → network/topic_trends.json

[선택] analyze/embed_cluster.py (OpenAI 필요, ~$1, ~2시간)
        → network/embeddings_cache.json (139MB, 재실행 시 재사용)
        → network/clusters.json
       analyze/make_viewer.py → network/viewer.html
```

`refresh.sh`는 `set -e` 설정 — 중간 실패 시 즉시 중단. 특정 단계만 재실행 시 개별 명령 사용.

---

## 5. 수집 대상

| 학회 | 도메인 | organCode2 | source값 | 상태 |
|---|---|---|---|---|
| KCI 학회지 | paper.cricit.kr | kci01 | journal | 완료 |
| KCI 학술대회 | paper.cricit.kr | kci03 | conference | 완료 |
| KSMI 학술대회 | auric.or.kr | ksm01 | conference_ksmi | scraper 구현 완료, 미수집 |

발행 주기: 학회지 짝수월, 학술대회 봄(4~6월)+가을(10~12월). 권장 갱신: 6월·12월.

---

## 6. 페이지네이션 (핵심 버그 이력)

- 초기: 1페이지만 수집 → 2,108편 (실제 18,228편 누락)
- 수정: `[Page N of M]` 파싱 + `page=2~M` 루프
- 규칙: 1페이지는 `page` 파라미터 생략, `page=spage` 항상 동일

---

## 7. `<th>` 레이블 매핑

| 필드 | 실제 `<th>` 텍스트 | 비고 |
|---|---|---|
| title_ko | 논문명 | KO/EN "/" 분리 |
| abstract_ko | 요약1 | |
| abstract_en | 요약2 | |
| keywords | 주제어 | |
| volume/issue | 수록사항 | "Vol.19 No.6" 또는 "v.27 n.1" (KSMI) |
| page | 페이지 | "시작페이지(N) 총페이지(M)" |

---

## 8. 실행 방법

```bash
bash refresh.sh                  # 전체 갱신 (분석+대시보드)
bash refresh.sh --collect        # 수집 포함 전체 갱신

# 수집 단독
.venv/bin/python3 crawl/scraper.py
.venv/bin/python3 crawl/scraper.py --source journal
.venv/bin/python3 crawl/scraper.py --source conference_ksmi  # KSMI
.venv/bin/python3 crawl/scraper.py --from-year 2020          # 증분 (테스트 권장)
.venv/bin/python3 crawl/scraper.py --reset                   # 처음부터

# 초록 보완
.venv/bin/python3 patch_abstracts.py --dry-run
.venv/bin/python3 patch_abstracts.py

# 의미 군집화 (OpenAI 필요)
export OPENAI_API_KEY="sk-..."
.venv/bin/python3 analyze/embed_cluster.py
.venv/bin/python3 analyze/make_viewer.py

# 현황 확인
.venv/bin/python3 run.py --stats
```

---

## 9. 산출물 파일 목록

| 파일 | 경로 | 생성 단계 | 비고 |
|---|---|---|---|
| papers_lite.json | network/ | refresh.sh [2/4] | |
| yearly_stats.json | network/ | refresh.sh [2/4] | [2/4] 건너뛰면 갱신 안 됨 |
| author_papers.json | network/ | refresh.sh [2/4] | |
| graph_d3.json | network/ | build_network.py | |
| stats.json | network/ | build_network.py | 동명이인 합산 주의 |
| dashboard.html | network/ | make_dashboard.py | 18MB 메인 대시보드 |
| topic_trends.json | network/ | make_dashboard.py | 22주제 × 38년 |
| clusters.json | network/ | embed_cluster.py | ⚠ 구버전 (2,108편) |
| embeddings_cache.json | network/ | embed_cluster.py | **139MB — 절대 삭제 금지** |
| viewer.html | network/ | make_viewer.py | |

---

## 10. 데이터 품질

| 필드 | 학회지 | 학술대회 | 원인 |
|---|---|---|---|
| abstract_ko | 85.1% | ~0%(2018+) | KCI 서버에 없음 |
| title_en | 92.6% | 98.2% | |
| keywords | 74.6% | 0% | KCI 서버에 없음 |

**동명이인 경고**: `stats.json` paper_count는 동일 한국어 이름을 합산한 값.

---

## 11. 에러 이력 및 설계 결정

| # | 문제 | 해결책 | 이유 |
|---|---|---|---|
| 1 | 1페이지만 수집 | `_parse_total_pages()` + 루프 | 기본값이 단일 페이지 |
| 2 | th 레이블 불일치 | firecrawl MCP로 HTML 확인 후 수정 | bash 환경 직접 HTTP 차단 |
| 3 | `tbnm=p/o` 불가 | `tbnm=r` 고정 | 서버 측 파라미터 제한 |
| 4 | bash HTTP 차단 | firecrawl MCP 사용 | Claude Code 샌드박스 제한 |
| 5 | Dropbox Read 불가 | Desktop Commander MCP | 가상 드라이브 경로 제한 |

---

## 12. 트러블슈팅

| 증상 | 원인 | 해결 |
|---|---|---|
| ModuleNotFoundError | 시스템 python3 사용 | `.venv/bin/python3` 사용 |
| yearly_stats 구버전 | [2/4] 미실행 | `bash refresh.sh` 전체 실행 |
| betweenness 20~40분 | 정상 (21k편 기준) | 강제 종료 금지 |
| embed_cluster 40~60분 | K=30~55 탐색 정상 | 대기 |
| embeddings JSONDecodeError | 손상된 캐시 | 삭제 후 재임베딩 (~$1, ~2시간) |
| 권호 누락 의심 | 수집 중 실패 후 done 마킹 | `logs/progress.json`에서 해당 항목 제거 후 재수집 |
| OpenAI 키 인식 안 됨 | `.env` 자동 로드 없음 | `export OPENAI_API_KEY=sk-...` |

---

## 13. 운영

```bash
# 정기 백업 (월 1회)
tar -czf ~/kci-backup-$(date +%Y%m%d).tar.gz \
    ~/claude/kci-concrete/meta/ \
    ~/claude/kci-concrete/network/papers_lite.json \
    ~/claude/kci-concrete/network/yearly_stats.json \
    ~/claude/kci-concrete/network/stats.json

# embeddings_cache 별도 백업 (139MB, 재생성 비용 ~$1)
cp ~/claude/kci-concrete/network/embeddings_cache.json \
   ~/kci-embeddings-backup-$(date +%Y%m%d).json

# 로그 정리 (월 1회)
find ~/claude/kci-concrete/logs/ -name "*.log" -mtime +30 -delete
```

---

## 14. 절대 금지

| 금지 행동 | 이유 |
|---|---|
| `page=1` 단독 또는 `page=1&spage=1` 명시 | 핵심 버그 재발 (1페이지만 수집) |
| `tbnm=p` 또는 `tbnm=o` | 서버 파라미터 제한, 빈 결과/500 |
| 시스템 `python3` 직접 실행 | 의존성 미설치 → 즉시 오류 |
| `meta/` 전체 삭제 | 21,029편 재수집 수 시간 소요 |
| `embeddings_cache.json` 삭제 | ~$1 비용 + ~2시간 재생성 |
| `build_network.py` 단독 실행 | `yearly_stats.json` 갱신 안 됨 |
| 수집 중 Dropbox 동기화 활성화 | JSON 파일 손상 위험 |

---

## 15. KSMI 확장 절차

`scraper.py`의 `SOURCES['conference_ksmi']` 항목은 이미 구현 완료 (start_year=1997, months=["04","05","10","11"]).

1. auric.or.kr 실제 발행월·HTML th 레이블 firecrawl로 확인
2. th 레이블이 KCI와 다르면 scraper.py 파싱 로직 수정
3. `build_network.py` load_papers() source 튜플에 `"conference_ksmi"` 추가
4. `refresh.sh` [2/4] src 리스트에 `"conference_ksmi"` 추가
5. `refresh.sh` [2/4]의 `SOC_MAP` 추가:
   ```python
   SOC_MAP = {"journal":"KCI","conference":"KCI","conference_ksmi":"KSMI"}
   "soc": SOC_MAP.get(p.get("source",""), "KCI")
   ```
6. `.venv/bin/python3 crawl/scraper.py --source conference_ksmi` 실행

---

## 16. 즉시 실행 필요

**clusters.json 재생성** (현재 2,108편 기준 구버전):
```bash
export OPENAI_API_KEY="sk-..."
.venv/bin/python3 analyze/embed_cluster.py   # ~$1, ~2시간 (캐시 있으면 수분)
.venv/bin/python3 analyze/make_viewer.py
```

---

## 17. 향후 과제

- KSMI 수집 (코드 준비 완료, 수집 미착수)
- 저자 동명이인 디앰비규에이션
- IJCSM (Springer Open, ISSN 1976-0485) 확장
- `--min-papers` 임계값 정책 (5개 학회+ 확장 시 메모리 부담)

---

**승인: 박성민 (수석 아키텍트 부장), 이현정 (CTO) — 2026-05-16**  
배포 준비 완료. clusters.json 재생성 후 섹션 1 상태표 업데이트 요망.

---

## 재시작 프롬프트

> Read `/Users/skyrunner/claude/kci-concrete/HANDOFF.md` and pick up from exactly where it left off.

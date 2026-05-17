"""
주제 트렌드 재집계 — build_topics.py
=====================================
모든 papers_lite.json 논문을 22개 수동 주제로 분류해
topic_trends.json (전체) 및 topic_trends_by_soc.json (KCI/KSMI 분리)을 생성한다.

입력: network/papers_lite.json
출력: network/topic_trends.json
      network/topic_trends_by_soc.json

실행: python3 analyze/build_topics.py
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).parent.parent
NET  = ROOT / "network"

# ── 주제 키워드 딕셔너리 (JS TOPIC_KW와 동일 내용) ──────────────────────────
# 제목(t) + 영문제목(te) lower() 문자열에 대해 substring 검색
TOPIC_KW: dict[str, list[str]] = {
    # ── 재료 계열 ──────────────────────────────────────────────────────────
    "고강도콘크리트": [
        "고강도","고성능","HSC","HPC","초고강도","ultra-high strength",
        "high strength","high performance concrete","고강도 콘크리트","고성능 콘크리트",
    ],
    "UHPC": [
        "UHPC","UHPFRC","초고성능 콘크리트","ultra-high performance concrete",
        "reactive powder concrete","RPC","Ductal",
    ],
    "섬유보강": [
        "강섬유","SFRC","FRC","ECC","SHCC","HPFRCC","PVA 섬유","PVA fiber",
        "PP섬유","PE섬유","폴리프로필렌 섬유","폴리에틸렌 섬유","바잘트 섬유",
        "basalt fiber","섬유 혼입","섬유혼입률","fiber volume fraction",
        "fiber reinforced concrete","하이브리드 섬유","hybrid fiber","단섬유",
        "macro fiber","micro fiber",
    ],
    "재생골재": [
        "순환골재","재생골재","폐콘크리트","recycled aggregate","recycled concrete",
        "순환 골재","재활용 골재",
    ],
    "자기충전": [
        "자기충전","SCC","self-compacting","자기다짐","고유동 콘크리트",
        "자기충전 콘크리트","충전성","고충전","충전성능",
    ],
    "플라이애시": [
        "플라이애시","fly ash","flyash","석탄회","비산재","플라이 애시",
        "포졸란","pozzolan","석탄재",
    ],
    "실리카퓸": [
        "실리카퓸","실리카 퓸","실리카흄","실리카 흄","silica fume","silica-fume",
        "condensed silica fume","마이크로실리카","마이크로 실리카","micro silica","microsilica",
    ],
    "슬래그": [
        "슬래그","slag","고로슬래그","GGBS","GGBFS","고로 슬래그","blast furnace slag",
    ],
    "경량콘크리트": [
        "경량골재","경량콘크리트","lightweight aggregate","lightweight concrete",
        "기포콘크리트","ALC","경량 콘크리트","경량 골재",
    ],
    # ── 구조/설계 계열 ─────────────────────────────────────────────────────
    "내진/내풍": [
        "내진","지진","내풍","seismic","earthquake","내진성능","지진하중","내진설계","내진 성능",
    ],
    "FRP보강": [
        "FRP","GFRP","CFRP","AFRP","BFRP","FRP 시트","FRP시트","FRP sheet","FRP 판",
        "FRP bar","FRP 봉","FRP 그리드","FRP rebar","탄소섬유 시트","탄소섬유시트",
        "탄소섬유 보강","carbon fiber sheet","유리섬유 보강","아라미드","섬유강화폴리머",
        "fiber reinforced polymer","NSM","EB-FRP","FRP 부착","FRP wrapping",
    ],
    "PSC/PC": [
        "PSC","프리스트레스","prestress","프리캐스트","precast","포스트텐션",
        "프리텐션","post-tension","pre-tension","PC 보","PC 거더",
    ],
    "합성구조": [
        "합성구조","합성 보","합성보","합성 기둥","합성기둥","합성 바닥판","합성슬래브",
        "합성 슬래브","SRC","강-콘크리트","steel-concrete composite","합성 교량",
        "steel concrete composite","강합성",
    ],
    "보-기둥접합": [
        "접합부","joint","beam-column","보-기둥","연결부","접합 상세","보기둥 접합",
    ],
    "교량구조": [
        "교량","bridge","교각","pier","아치교","사장교","현수교","교량구조","교량 설계","교량 거더",
    ],
    "전단설계": [
        "전단강도","전단설계","전단거동","shear strength","shear design","전단철근",
        "사인장","전단 파괴","전단 보강","punching shear","뚫림전단",
    ],
    "피로/충격": [
        "피로","fatigue","반복하중","충격하중","폭발하중","blast load","impact load",
        "피로 수명","피로 균열","동적하중",
    ],
    # ── 내구성 계열 ─────────────────────────────────────────────────────────
    "내구성": [
        "내구성","durability","염해","황산염","ASR","알칼리골재","내구 수명","해양 환경","해양 콘크리트",
    ],
    "균열": [
        "균열","crack","cracking","균열폭","균열 제어","균열발생","균열 진전","crack width",
    ],
    "염화물/탄산화": [
        "염화물","탄산화","중성화","carbonation","chloride","염소이온","탄산화 깊이","중성화 깊이",
    ],
    "화재": [
        "화재","fire","내화","폭렬","spalling","고온 노출","화재 저항","화재노출","화재 후","내화성능",
    ],
    "수축": [
        "수축","shrinkage","크리프","creep","건조수축","자기수축","소성수축","장기변형",
    ],
    "철근부식": [
        "부식","corrosion","전기화학","음극방식","탈패시베이션","부식 속도","부식 전류",
        "전기방식","방청","steel corrosion",
    ],
    "동결융해": [
        "동결융해","동결-융해","freeze-thaw","freeze thaw","내동해","동해저항","frost resistance",
    ],
    # ── 공법/현장 계열 ─────────────────────────────────────────────────────
    "보수·보강": [
        "보수","단면복구","보수공법","구조보강","내진보강","단면증설","단면확대",
        "rehabilitation","retrofitting","seismic retrofit","jacketing","repair of",
        "structural repair","유지보수","유지관리",
    ],
    "포장콘크리트": [
        "포장","pavement","도로포장","콘크리트포장","줄눈","교면포장","도로 포장","포장 콘크리트",
    ],
    "터널/지하": [
        "터널","tunnel","숏크리트","shotcrete","라이닝","lining","지하연속벽","터널 라이닝","굴착","underground",
    ],
    # ── 디지털/환경 계열 ───────────────────────────────────────────────────
    "3D프린팅": [
        "3D 프린팅","3D프린팅","3D printing","3D-프린팅","콘크리트 출력","프린팅 콘크리트",
        "layer-by-layer","contour crafting","콘크리트 3D","3D 프린터","3D 출력","additive manufacturing",
    ],
    "BIM/디지털": [
        "BIM","구조건전성","건전성 모니터링","SHM","디지털 트윈","digital twin",
        "structural health monitoring","안전진단","상태평가","계측 시스템","스마트 콘크리트",
        "IoT","머신러닝","machine learning","인공지능","딥러닝","deep learning",
        "신경망","neural network","인공신경망","데이터 기반","data-driven",
    ],
    "탄소중립/환경": [
        "탄소중립","탄소저감","탄소배출","이산화탄소","CO2 배출","CO2 emission","CO2 reduction",
        "온실가스","greenhouse gas","GHG","저탄소","low-carbon","환경영향","환경부하",
        "environmental impact","embodied carbon","내재탄소","LCA","전과정평가",
        "life cycle assessment","친환경","탄소발자국","carbon footprint","넷제로","net zero",
        "cement replacement","시멘트 대체","탄소 저감","탄소나노","carbon nano",
    ],
    "비파괴검사": [
        "비파괴","NDT","초음파 탐상","음향방출","충격반향","impact echo","GPR",
        "레이더 탐사","비파괴 검사","비파괴 시험","적외선 열화상","전기저항","임피던스",
    ],
}

# lowercase 사전 계산 (속도 최적화)
_TOPIC_KW_LOWER: dict[str, list[str]] = {
    t: [k.lower() for k in kws] for t, kws in TOPIC_KW.items()
}


def assign_topics(paper: dict) -> list[str]:
    text = ((paper.get("t") or "") + " " + (paper.get("te") or "")).lower()
    return [t for t, kws in _TOPIC_KW_LOWER.items() if any(k in text for k in kws)]


def build_trends(papers: list[dict], soc_filter: str | None = None) -> dict:
    subset = [
        p for p in papers
        if (soc_filter is None or (p.get("soc") or "KCI") == soc_filter)
        and str(p.get("y", "")).isdigit()
    ]
    year_totals: dict[str, int] = defaultdict(int)
    topic_year: dict[str, dict[str, int]] = {t: defaultdict(int) for t in TOPIC_KW}
    for p in subset:
        y = str(p["y"])
        year_totals[y] += 1
        for t in assign_topics(p):
            topic_year[t][y] += 1
    all_years = sorted(year_totals)
    return {
        "topics": list(TOPIC_KW),
        "years": all_years,
        "data": {t: {y: topic_year[t].get(y, 0) for y in all_years} for t in TOPIC_KW},
        "year_totals": {y: year_totals[y] for y in all_years},
    }


def main() -> None:
    src = NET / "papers_lite.json"
    if not src.exists():
        raise FileNotFoundError(f"papers_lite.json 없음: {src}")

    papers = json.loads(src.read_text(encoding="utf-8"))
    kci_n  = sum(1 for p in papers if (p.get("soc") or "KCI") == "KCI")
    ksmi_n = sum(1 for p in papers if (p.get("soc") or "KCI") == "KSMI")
    print(f"  논문 {len(papers)}편 로드 (KCI: {kci_n}, KSMI: {ksmi_n})")

    all_trends  = build_trends(papers)
    kci_trends  = build_trends(papers, "KCI")
    ksmi_trends = build_trends(papers, "KSMI")

    total = sum(all_trends["year_totals"].values())
    print(f"  주제 매칭 연도별 총합: {total}편")

    (NET / "topic_trends.json").write_text(
        json.dumps(all_trends, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"  저장: network/topic_trends.json")

    by_soc = {"ALL": all_trends, "KCI": kci_trends, "KSMI": ksmi_trends}
    (NET / "topic_trends_by_soc.json").write_text(
        json.dumps(by_soc, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )
    print(f"  저장: network/topic_trends_by_soc.json")


if __name__ == "__main__":
    main()

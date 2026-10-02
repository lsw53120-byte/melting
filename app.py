from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

import streamlit as st


st.set_page_config(
    page_title="멜팅 대화 검수기",
    page_icon="🫧",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .stApp { background: #fbfaff; }
    .block-container { max-width: 1120px; padding-top: 2.2rem; }
    [data-testid="stSidebar"] { background: #f2efff; }
    .hero { padding: 1.35rem 1.5rem; border: 1px solid #e8e1ff; border-radius: 18px;
            background: linear-gradient(120deg,#f2edff,#fff8fc); margin-bottom: 1rem; }
    .hero h1 { margin: 0 0 .35rem 0; color: #30244c; }
    .hero p { margin: 0; color: #655b76; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="hero"><h1>🫧 멜팅 대화 검수기</h1>'
    '<p>AI가 캐릭터와 대화하며 맥락 오류를 찾고, 고칠 방향과 매력적인 대화 아이디어를 제안합니다.</p></div>',
    unsafe_allow_html=True,
)

with st.sidebar:
    st.subheader("이중 검수 모델")
    openai_choices = {
        "GPT-5.6 Sol · 최고 성능": "gpt-5.6-sol",
        "GPT-5.6 Terra · 균형형": "gpt-5.6-terra",
        "GPT-5.6 Luna · 비용 절약": "gpt-5.6-luna",
    }
    claude_choices = {
        "Claude Fable 5.1 · 최고 성능": "claude-fable-5-1",
        "Claude Opus 5.5 · 복합 추론": "claude-opus-5-5",
        "Claude Sonnet 5.5 · 균형형": "claude-sonnet-5-5",
        "Claude Haiku 4.5 · 비용 절약": "claude-haiku-4-5-20251001",
    }
    openai_label = st.selectbox("OpenAI 모델", list(openai_choices), index=0)
    claude_label = st.selectbox("Claude 모델", list(claude_choices), index=0)
    openai_model = openai_choices[openai_label]
    claude_model = claude_choices[claude_label]
    st.divider()
    st.caption("API 키는 화면에 입력하지 않습니다. 배포 서버의 비밀 설정에 OPENAI_API_KEY와 ANTHROPIC_API_KEY를 등록하세요.")
    st.caption("양쪽 모델에 캐릭터·시나리오·대화가 각각 전송되며, 사용량에 따라 양쪽 API 비용이 발생합니다.")


with st.form("review_form"):
    left, right = st.columns(2)
    with left:
        character = st.text_area(
            "캐릭터 설정 (여러 명 입력 가능)",
            height=250,
            placeholder="인물마다 이름을 붙여 구분해 주세요.\n\n[캐릭터: 서윤]\n성격, 말투, 배경, 현재 알고 있는 정보...\n\n[캐릭터: 도겸]\n성격, 말투, 배경, 현재 알고 있는 정보...\n\n두 사람의 관계와 서로 아는 정보도 적어 주세요.",
            help="인물마다 이름·말투·현재 알고 있는 사실을 구분해 적어 주세요. 인물이 많다면 여러 번 검수해 서로 다른 조합을 확인하세요.",
        )
    with right:
        scenario = st.text_area(
            "시나리오·현재 상황",
            height=250,
            placeholder="시대와 장소, 현재 장면, 직전 사건, 두 사람의 감정과 관계, 캐릭터가 지금 알고 있는 사실을 적어 주세요.",
        )

    st.subheader("검수 방식")
    mode = st.radio(
        "무엇을 확인할까요?",
        ["AI가 테스트 대화를 진행", "멜팅 실제 대화 분석", "둘 다 진행"],
        horizontal=True,
        label_visibility="collapsed",
    )
    transcript = st.text_area(
        "멜팅에서 실제로 나눈 대화 (선택)",
        height=180,
        placeholder="예) 나: 임금이 나와 같이 잠자리에 들겠느냐?\n캐릭터: 어디 사세요?",
        help="테스트 대화 또는 실제 대화 분석에 사용합니다. 'AI가 테스트 대화를 진행'을 골라도 적으면 대화 맥락으로 참고합니다.",
    )

    col_a, col_b, col_c = st.columns([1, 1, 2])
    with col_a:
        turns = st.slider("테스트 대화 턴", min_value=3, max_value=12, value=6)
    with col_b:
        cast_mode = st.selectbox(
            "인물 조합",
            ["인물별 대화 + 다인 장면", "인물별 대화 중심", "다인 장면 중심"],
        )
    with col_c:
        audience = st.selectbox(
            "주요 구독자 취향",
            ["모르겠음 / 폭넓게", "로맨스", "판타지·로맨스 판타지", "드라마·감정선", "코미디", "미스터리", "직접 입력"],
        )
    audience_custom = st.text_input("취향 설명", placeholder="예: 느린 감정선, 능글맞은 인물을 좋아하는 독자") if audience == "직접 입력" else ""

    submitted = st.form_submit_button("검수 시작", type="primary", use_container_width=True)


def get_server_secret(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if value:
        return value
    try:
        return str(st.secrets.get(name, "")).strip()
    except Exception:
        return ""


def post_json(url: str, payload: dict, headers: dict[str, str]) -> dict:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=240) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")[:1800]
        raise RuntimeError(f"API 오류 ({exc.code}): {details}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"API에 연결하지 못했습니다: {exc.reason}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError("API 응답을 JSON으로 읽지 못했습니다.") from exc


def request_openai(prompt: str, instructions: str, model_id: str, api_key: str) -> str:
    data = post_json(
        "https://api.openai.com/v1/responses",
        {"model": model_id, "instructions": instructions, "input": prompt, "store": False},
        {"Authorization": f"Bearer {api_key}"},
    )
    if data.get("output_text"):
        return data["output_text"]
    text_blocks = [
        block.get("text", "")
        for item in data.get("output", [])
        for block in item.get("content", [])
        if block.get("type") == "output_text"
    ]
    result = "\n".join(part for part in text_blocks if part).strip()
    if not result:
        raise RuntimeError("OpenAI API 응답에 텍스트 결과가 없습니다.")
    return result


def request_claude(prompt: str, instructions: str, model_id: str, api_key: str) -> str:
    data = post_json(
        "https://api.anthropic.com/v1/messages",
        {
            "model": model_id,
            "max_tokens": 7000,
            "system": instructions,
            "messages": [{"role": "user", "content": prompt}],
        },
        {"x-api-key": api_key, "anthropic-version": "2023-06-01"},
    )
    result = "\n".join(
        block.get("text", "") for block in data.get("content", []) if block.get("type") == "text"
    ).strip()
    if not result:
        raise RuntimeError("Claude API 응답에 텍스트 결과가 없습니다.")
    return result


if submitted:
    openai_api_key = get_server_secret("OPENAI_API_KEY")
    anthropic_api_key = get_server_secret("ANTHROPIC_API_KEY")
    if not character.strip() or not scenario.strip():
        st.error("캐릭터 설정과 시나리오를 모두 입력해 주세요.")
    elif not openai_api_key or not anthropic_api_key:
        st.error("배포 서버 비밀 설정에 OPENAI_API_KEY와 ANTHROPIC_API_KEY를 모두 등록해 주세요.")
    else:
        do_simulation = mode in ("AI가 테스트 대화를 진행", "둘 다 진행")
        if mode == "멜팅 실제 대화 분석" and not transcript.strip():
            st.error("실제 대화 분석을 선택했다면 대화 내용을 붙여 넣어 주세요.")
        else:
            target_audience = audience_custom.strip() if audience == "직접 입력" else audience
            with st.spinner("두 모델이 각각 검수하고 있어요. 잠시 기다려 주세요…"):
                try:
                    simulated = ""
                    if do_simulation:
                        sim_prompt = f"""아래 설정을 바탕으로 캐릭터 대화 스트레스 테스트를 진행하세요.

## 캐릭터 설정
{character}

## 시나리오와 현재 상황
{scenario}

## 테스트 대화 규칙
- 당신은 캐릭터를 시험하는 자연스러운 대화 상대입니다. 캐릭터의 대사를 대신 쓰지 마세요.
- 여러 인물이 있으면 지정된 구성 방식({cast_mode})에 맞춰 1:1 장면과 다인 장면을 섞으세요. 대화 분량상 모두 등장시키기 어렵다면 이번에 확인한 인물만 밝히고, 나머지를 확인했다고 주장하지 마세요.
- 먼저 대화 상대의 질문/행동을 한 번에 하나씩 쓰고, 캐릭터가 설정에 맞춰 답하는 왕복 대화를 총 {turns}회 구성하세요. 캐릭터 대사는 이름을 붙여 구분하세요.
- 질문은 앞 장면을 기억해야 답할 수 있는 것, 감정·관계 확인, 주제 전환, 애매한 표현의 의도 확인 등을 섞으세요.
- 인물마다 말투·성격·알고 있는 정보가 섞이지 않는지, 다른 인물의 기억이나 감정을 잘못 말하지 않는지 시험하세요.
- 상대의 말에 답하지 않고 무관한 자기소개나 새 주제로 튀는 답변을 유도/발견할 수 있게 현실적인 상황을 만드세요. 일부러 억지 질문을 만들지는 마세요.
- 성적·폭력적 내용은 설정과 플랫폼의 안전한 범위 안에서만 다루고, 맥락상 불필요하면 피하세요.
- 출력은 `상대:`와 `캐릭터:`로 구분하고 마지막에 `테스트한 포인트`를 짧게 적으세요.
"""
                        simulated = request_openai(
                            sim_prompt,
                            "대화 품질 테스트를 수행하는 상대역입니다. 주어진 설정 밖의 사실을 단정하지 말고 한국어로 답하세요.",
                            openai_model,
                            openai_api_key,
                        )

                    material = []
                    if do_simulation:
                        material.append("## AI가 만든 테스트 대화\n" + simulated)
                    if transcript.strip():
                        material.append("## 사용자가 제공한 실제 대화\n" + transcript.strip())
                    evidence = "\n\n".join(material) or "테스트 대화를 생성하지 않았습니다."
                    review_prompt = f"""아래 입력을 검수해 한국어 마크다운 보고서를 작성하세요.

## 캐릭터 설정
{character}

## 시나리오
{scenario}

## 주요 구독자 취향
{target_audience}

## 검수할 대화
{evidence}

## 평가 기준
1. 질문 의도와 답변의 직접 관련성 (맥락 이탈, 질문 미응답, 엉뚱한 화제)
2. 직전 대화 및 장면 정보의 유지, 시간·장소·인물 관계의 연속성
3. 캐릭터 성격·말투·지식·감정선 일치
4. 여러 인물의 말투·기억·감정·관계가 서로 섞이거나 잘못 귀속되는지
5. 시나리오에 없는 사실을 만들어내거나 관계를 급격히 바꾸는지
6. 대화의 자연스러움과 몰입감

## 보고서 형식
### 한눈에 보는 결과
전체 상태(양호/수정 권장/문제 있음), 가장 중요한 발견 1~3개.
### 발견한 오류
표로 `심각도 | 근거가 된 대사 | 무엇이 어긋났는지 | 왜 문제인지`를 제시하세요. 근거가 있는 경우만 적고, 테스트 대화에서 AI가 만든 상대의 말과 캐릭터의 말을 구별하세요. 실제 대화와 AI 테스트 대화의 출처도 표시하세요. 오류가 없다면 억지로 만들지 마세요.
### 이렇게 고쳐 보세요
설정 보강 문구와 프롬프트/대화 운영 개선책을 구분해, 복사해 쓸 수 있는 예시를 주세요. 오류를 캐릭터 성격 탓으로 단정하지 말고 가능한 원인을 나눠 설명하세요.
### 구독자 취향에 맞는 대화 아이디어
{target_audience} 취향을 고려한 장면·대화 소재 3가지와 각각의 기대 감정/분위기를 제안하세요. 특정 취향을 모르면 폭넓은 독자 반응을 단정하지 말고 여러 선택지를 주세요.
### 추천 분위기와 한 줄 샘플
이 캐릭터에 어울리는 대화 분위기 2~3개, 짧은 샘플 대사 2개를 제안하세요. 샘플은 원 설정을 존중하고 원문 오류를 실제 멜팅에서 수정했다고 주장하지 마세요.
### 다음 검수에서 확인할 점
재현해 볼 질문 3개를 제안하세요.

과장된 확신을 피하고, 근거가 부족하면 `확인 필요`로 표시하세요. 구독자들이 무엇을 좋아하는지에 관한 제안은 보장된 사실이 아니라 창작 아이디어로 표현하세요.
인물이 많아 일부만 등장했다면 그 사실을 한눈에 보는 결과에 표시하고, 다음 검수에서 확인할 인물 조합을 제안하세요.
"""
                    review_instructions = "당신은 캐릭터 대화의 맥락·연속성·몰입감을 검수하는 독립 편집자입니다. 다른 모델의 결론을 알지 못한다고 가정하고, 근거 중심으로 평가하세요. 설정된 사실과 창작 제안을 구분해 친절하고 구체적인 한국어로 답하세요."
                    reports = {}
                    errors = {}
                    with ThreadPoolExecutor(max_workers=2) as pool:
                        futures = {
                            "ChatGPT": pool.submit(
                                request_openai, review_prompt, review_instructions, openai_model, openai_api_key
                            ),
                            "Claude": pool.submit(
                                request_claude, review_prompt, review_instructions, claude_model, anthropic_api_key
                            ),
                        }
                        for provider, future in futures.items():
                            try:
                                reports[provider] = future.result()
                            except RuntimeError as exc:
                                errors[provider] = str(exc)

                    if not reports:
                        raise RuntimeError("두 모델 모두 검수에 실패했습니다.\n" + "\n".join(errors.values()))
                    st.session_state["last_reports"] = reports
                    st.session_state["last_errors"] = errors
                    st.session_state["last_models"] = {
                        "ChatGPT": openai_model,
                        "Claude": claude_model,
                    }
                    st.session_state["last_simulated"] = simulated
                except RuntimeError as exc:
                    st.error(str(exc))


if st.session_state.get("last_reports"):
    st.divider()
    st.subheader("이중 검수 결과")
    st.caption("두 모델은 서로의 결과를 보지 않고 독립적으로 검수했습니다. 두 보고서를 나란히 비교하고, 같은 지적은 공통 발견으로, 다른 지적은 대화 근거와 대조해 보세요.")
    if st.session_state.get("last_simulated"):
        with st.expander("AI 테스트 상대역이 진행한 대화 보기", expanded=True):
            st.markdown(st.session_state["last_simulated"])
    report_columns = st.columns(2)
    for column, provider in zip(report_columns, ("ChatGPT", "Claude")):
        with column:
            st.markdown(f"### {provider} · `{st.session_state['last_models'][provider]}`")
            if provider in st.session_state["last_reports"]:
                st.markdown(st.session_state["last_reports"][provider])
            else:
                st.error(st.session_state["last_errors"].get(provider, "검수 결과를 받지 못했습니다."))
    combined_report = "\n\n---\n\n".join(
        f"# {provider} 독립 검수\n\n모델: `{st.session_state['last_models'][provider]}`\n\n{report}"
        for provider, report in st.session_state["last_reports"].items()
    )
    st.download_button(
        "두 모델 보고서 다운로드 (.md)",
        data=combined_report,
        file_name="멜팅_이중_검수_보고서.md",
        mime="text/markdown",
    )

with st.expander("검수기가 확인하는 항목"):
    st.markdown(
        """
        - **맥락 이탈:** 질문과 관계없는 답을 하거나 대화 주제를 갑자기 바꾸는지
        - **연속성:** 직전 사건, 장소, 관계, 감정을 이어 가는지
        - **캐릭터 유지:** 설정된 말투·성격·지식 범위에 맞는지
        - **인물 간 충돌:** 인물이 많을 때 말투·기억·관계가 서로 섞이지 않는지
        - **개선 제안:** 설정에 덧붙일 문구와 다시 시험할 질문을 제시
        - **독자 경험 아이디어:** 입력한 취향을 바탕으로 소재와 분위기를 추천

        AI가 생성한 테스트 대화는 실제 멜팅 엔진의 결과와 다를 수 있습니다. 멜팅에서 나온 대화를 붙여 넣으면 그 기록 자체를 근거로 검수합니다.
        """
    )

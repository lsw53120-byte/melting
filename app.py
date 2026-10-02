from __future__ import annotations

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
    '<p>ChatGPT와 Claude에게 대화 검수를 요청하고, 두 답변을 한곳에서 비교하세요.</p></div>',
    unsafe_allow_html=True,
)

with st.sidebar:
    st.subheader("간편한 이중 검수")
    st.markdown("""
    1. 앱에서 검수 프롬프트 생성
    2. ChatGPT와 Claude에 각각 복사
    3. 답변을 앱에 붙여 넣어 비교

    API 키 설정 없이 현재 사용 중인 계정으로 진행합니다.
    """)


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


def make_review_prompt(character: str, scenario: str, audience: str, evidence: str) -> str:
    evidence_text = evidence or "실제 대화 기록은 제공되지 않았습니다. 아래 테스트 대화 생성 지침을 먼저 수행하세요."
    return f"""아래 입력을 검수해 한국어 마크다운 보고서를 작성하세요.

## 캐릭터 설정
{character}

## 시나리오
{scenario}

## 주요 구독자 취향
{audience}

## 검수할 대화
{evidence_text}

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
표로 `심각도 | 근거가 된 대사 | 무엇이 어긋났는지 | 왜 문제인지`를 제시하세요. 근거가 있는 경우만 적고, AI가 생성한 상대의 말과 캐릭터의 말을 구별하세요. 실제 대화와 가상 테스트 대화의 출처도 표시하세요. 오류가 없다면 억지로 만들지 마세요.
### 이렇게 고쳐 보세요
설정 보강 문구와 대화 운영 개선책을 구분해, 복사해 쓸 수 있는 예시를 주세요. 원인을 단정하지 말고 가능한 설명을 나눠 주세요.
### 구독자 취향에 맞는 대화 아이디어
{audience} 취향을 고려한 장면·대화 소재 3가지와 각각의 기대 감정/분위기를 제안하세요. 취향을 모르면 여러 선택지를 주세요.
### 추천 분위기와 한 줄 샘플
캐릭터에 어울리는 대화 분위기 2~3개와 짧은 샘플 대사 2개를 제안하세요.
### 다음 검수에서 확인할 점
재현해 볼 질문 3개를 제안하세요.

구독자가 무엇을 좋아하는지에 관한 제안은 보장된 사실이 아니라 창작 아이디어로 표현하세요. 설정 근거가 부족하면 `확인 필요`로 표시하세요.
"""


if submitted:
    if not character.strip() or not scenario.strip():
        st.error("캐릭터 설정과 시나리오를 모두 입력해 주세요.")
    elif mode == "멜팅 실제 대화 분석" and not transcript.strip():
        st.error("실제 대화 분석을 선택했다면 대화 내용을 붙여 넣어 주세요.")
    else:
        do_simulation = mode in ("AI가 테스트 대화를 진행", "둘 다 진행")
        target_audience = audience_custom.strip() if audience == "직접 입력" else audience
        extra_test = ""
        if do_simulation:
            extra_test = f"""

## 먼저 가상 대화 테스트 진행
캐릭터 설정과 시나리오를 토대로 자연스러운 상대역의 질문과 캐릭터의 답을 왕복 {turns}회 작성하세요. 여러 인물이 있으면 `{cast_mode}` 방식으로 구성하고 각 대사를 이름으로 표시하세요. 맥락 기억, 질문 의도, 인물별 말투·지식이 유지되는지 확인할 수 있게 질문을 만드세요. 이 대화는 AI가 만든 테스트일 뿐 멜팅의 실제 응답이라고 표현하지 마세요.
"""
        base_prompt = make_review_prompt(
            character.strip(), scenario.strip(), target_audience, transcript.strip()
        )
        st.session_state.pop("manual_chatgpt_input", None)
        st.session_state.pop("manual_claude_input", None)
        st.session_state.pop("manual_reports", None)
        st.session_state["manual_prompts"] = {
            "ChatGPT": (
                "ChatGPT에서 사용 가능한 가장 성능 높은 모델을 선택한 뒤, 아래 프롬프트 전체를 붙여 넣으세요.\n\n"
                + extra_test + "\n" + base_prompt
            ),
            "Claude": (
                "Claude에서 사용 가능한 가장 성능 높은 모델을 선택한 뒤, 아래 프롬프트 전체를 붙여 넣으세요.\n\n"
                + extra_test + "\n" + base_prompt
            ),
        }


if st.session_state.get("manual_prompts"):
    st.divider()
    st.subheader("간편 검수 · API 없이 사용")
    st.markdown("**1. 프롬프트를 복사해 각 서비스에 붙여 넣으세요.** 응답은 각 서비스의 사용량 제한 안에서 생성됩니다.")
    link_left, link_right = st.columns(2)
    with link_left:
        st.link_button("ChatGPT 열기", "https://chatgpt.com", use_container_width=True)
    with link_right:
        st.link_button("Claude 열기", "https://claude.ai", use_container_width=True)
    prompt_left, prompt_right = st.columns(2)
    for column, provider in zip((prompt_left, prompt_right), ("ChatGPT", "Claude")):
        with column:
            st.markdown(f"#### {provider} 검수 프롬프트")
            st.code(st.session_state["manual_prompts"][provider], language="markdown")
    st.markdown("**2. 각 서비스의 답변을 아래에 붙여 넣고 결과 저장을 누르세요.**")
    with st.form("save_manual_reviews"):
        manual_chatgpt = st.text_area("ChatGPT 검수 결과", height=260, key="manual_chatgpt_input")
        manual_claude = st.text_area("Claude 검수 결과", height=260, key="manual_claude_input")
        manual_saved = st.form_submit_button("두 결과 저장 및 비교", type="primary", use_container_width=True)
    if manual_saved:
        if not manual_chatgpt.strip() or not manual_claude.strip():
            st.error("비교할 수 있도록 ChatGPT와 Claude 답변을 모두 붙여 넣어 주세요.")
        else:
            st.session_state["manual_reports"] = {
                "ChatGPT": manual_chatgpt.strip(),
                "Claude": manual_claude.strip(),
            }

if st.session_state.get("manual_reports"):
    st.divider()
    st.subheader("ChatGPT · Claude 검수 비교")
    st.caption("두 답변에서 같은 지적은 공통 발견으로, 의견이 다른 부분은 실제 대화와 설정을 다시 대조해 보세요.")
    manual_columns = st.columns(2)
    for column, provider in zip(manual_columns, ("ChatGPT", "Claude")):
        with column:
            st.markdown(f"### {provider}")
            st.markdown(st.session_state["manual_reports"][provider])
    manual_combined = "\n\n---\n\n".join(
        f"# {provider} 검수 결과\n\n{report}"
        for provider, report in st.session_state["manual_reports"].items()
    )
    st.download_button(
        "비교 결과 다운로드 (.md)",
        data=manual_combined,
        file_name="멜팅_간편_이중_검수.md",
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

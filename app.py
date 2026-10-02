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
    .block-container { max-width: 1080px; padding-top: 2.2rem; }
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
    '<p>시나리오를 넣으면 ChatGPT가 가상의 상대역이 되어 대화 오류와 고칠 문구를 찾아줍니다.</p></div>',
    unsafe_allow_html=True,
)

with st.sidebar:
    st.subheader("사용 방법")
    st.markdown(
        """
        1. 검수할 시나리오를 붙여 넣습니다.
        2. 생성된 프롬프트를 ChatGPT에 복사합니다.
        3. 답변을 다시 붙여 넣으면 문제와 수정 문구를 저장할 수 있습니다.

        API 키는 필요하지 않습니다. ChatGPT에서 사용 가능한 성능 높은 모델을 선택하세요.
        """
    )


with st.form("review_form"):
    source = st.text_area(
        "검수할 시나리오·캐릭터 설정",
        height=300,
        placeholder=(
            "캐릭터 소개와 시나리오를 원문 그대로 붙여 넣으세요.\n"
            "인물이 여러 명이면 각 이름, 성격, 말투, 관계, 현재 상황을 포함해 주세요.\n\n"
            "예) 임금 도윤은 무뚝뚝하지만 은혜를 잊지 않는다.\n"
            "궁녀 서린은 도윤을 짝사랑하고 있으며, 두 사람은 연회가 끝난 뒤 단둘이 남았다."
        ),
        help="별도 양식으로 나눌 필요 없이 가진 시나리오 원문을 그대로 넣으면 됩니다.",
    )

    test_mode = st.radio(
        "검수 방법",
        ["가상 상대역 대화 테스트", "멜팅 실제 대화 분석", "가상 테스트 + 실제 대화 분석"],
        horizontal=True,
    )
    transcript = st.text_area(
        "멜팅에서 실제로 나눈 대화 (선택)",
        height=150,
        placeholder="예) 나: 임금이 나와 같이 잠자리에 들겠느냐?\n캐릭터: 어디 사세요?",
        help="실제 대화를 붙이면 관찰된 오류와 AI가 예상한 잠재 오류를 따로 분석합니다.",
    )
    audience = st.selectbox(
        "추천 대화 분위기 (선택)",
        ["직접 입력", "로맨스", "판타지·로맨스 판타지", "드라마·감정선", "코미디", "미스터리", "폭넓은 독자 취향"],
    )
    audience_custom = st.text_input(
        "원하는 분위기나 독자 취향",
        placeholder="예: 느린 감정선, 무심한 인물의 다정함을 좋아하는 독자",
    ) if audience == "직접 입력" else ""
    turns = st.slider("가상 대화 왕복 횟수", min_value=3, max_value=10, value=6)
    submitted = st.form_submit_button("ChatGPT 검수 프롬프트 만들기", type="primary", use_container_width=True)


if submitted:
    if not source.strip():
        st.error("검수할 시나리오나 캐릭터 설정을 붙여 넣어 주세요.")
    elif test_mode == "멜팅 실제 대화 분석" and not transcript.strip():
        st.error("실제 대화 분석을 선택했다면 멜팅 대화도 붙여 넣어 주세요.")
    else:
        do_test = test_mode != "멜팅 실제 대화 분석"
        do_actual = test_mode != "가상 상대역 대화 테스트"
        target_audience = audience_custom.strip() if audience == "직접 입력" else audience
        dialogue_evidence = transcript.strip() if do_actual else ""

        test_instructions = ""
        if do_test:
            test_instructions = f"""

## 1단계: 가상 상대역이 되어 대화를 시험하세요
시나리오 안에서 자연스럽게 생길 수 있는 상황을 골라, 서로 다른 성격의 가상 대화 상대 3명을 직접 만드세요. 각 상대가 캐릭터에게 실제로 할 법한 질문을 하고, 캐릭터가 설정을 지키며 답한다고 가정한 왕복 대화를 각 {turns}회 작성하세요.

상대역은 다음 방식으로 서로 다르게 구성하세요.
- 관계·장면을 잘 모르는 초면형: 기본 설명과 맥락 유지 확인
- 감정과 관계를 세심하게 보는 독자형: 감정선·호칭·관계 변화 확인
- 자연스럽게 화제를 바꾸는 대화형: 주제 전환 뒤에도 질문에 답하는지 확인

인물이 여러 명이면 인물별 1:1 대화와 인물 간 다인 장면을 섞어 가능한 많은 인물을 시험하세요. 이번에 실제 등장시킨 인물과 시험하지 못한 인물을 구분해 보고하세요. 대화마다 캐릭터 이름을 표시하세요. 시나리오에 없는 설정은 만들어 확정하지 말고 `설정에 없음`으로 표시하세요. 이 가상 대화는 멜팅의 실제 응답이 아니라 잠재 오류를 찾기 위한 모의 테스트입니다.
"""

        if do_actual and dialogue_evidence:
            evidence_section = f"""
## 사용자가 제공한 멜팅 실제 대화
{dialogue_evidence}
"""
        else:
            evidence_section = "## 실제 대화 기록\n제공되지 않음"

        prompt = f"""당신은 캐릭터 대화를 직접 시험하는 QA 편집자입니다. 시나리오만 읽고 일반적인 조언만 하지 말고, 아래 단계대로 구체적인 대화 사례와 수정안을 만드세요.

## 검수 대상 원문
{source.strip()}

{evidence_section}

{test_instructions}

## 2단계: 문제를 근거와 함께 판정하세요
- 실제 대화가 있으면 그 안에서 실제로 관찰된 오류와, 가상 테스트에서만 예상한 잠재 오류를 분리하세요.
- 실제 대화가 없으면 모든 발견을 `잠재 오류(모의 테스트)`라고 표시하세요. 멜팅에서 실제로 발생했다고 단정하지 마세요.
- 각 문제에 반드시 근거가 된 정확한 대사나 시나리오 문장을 인용하세요. 해당 문장이 없으면 `근거 문장 없음`으로 쓰세요.
- 단순히 `맥락이 어색함`이라고만 쓰지 말고, 어떤 말 뒤에 어떤 반응이 나와야 자연스러운지 설명하세요.
- 발견할 문제가 없으면 억지로 만들지 말고 `이 테스트에서는 발견되지 않음`이라고 쓰세요.

## 3단계: 보고서를 아래 형식으로 작성하세요
### 검수 요약
전체 판정(양호 / 수정 권장 / 문제 있음), 가장 중요한 이유, 실제 대화 분석인지 모의 테스트인지.

### 발견한 문제와 근거
문제마다 아래 항목을 채우세요. 문제없으면 표를 비우고 그 이유를 쓰세요.
| 번호·심각도 | 유형·출처 | 근거가 된 정확한 문장/대사 | 상대의 말 | 문제인 이유와 기대되는 반응 |

### 어디를 어떻게 고칠지
문제마다 아래 형식을 빠짐없이 사용하세요.
- **수정 위치:** 원문에서 찾아갈 제목·문장·인물 항목. 제목이 없으면 `어느 문단 다음에 추가`할지 지정
- **현재 문구:** 바꿔야 할 기존 문구를 짧게 인용. 추가만 필요하면 `추가`라고 표시
- **교체/추가 문구:** 그대로 복사해 붙일 수 있는 완성 문장
- **이 수정이 막는 오류:** 수정 후 어떤 엉뚱한 답변/설정 충돌을 줄이는지

막연한 조언만 쓰지 말고 실제 수정 문장을 적으세요. 원문 전체를 다시 쓰지 말고 필요한 부분만 고치세요.

### 수정 후 재시험 질문
같은 문제가 해결됐는지 확인할 질문 3개와, 각 질문에서 기대하는 답의 핵심.

### 인물 검수 범위
이번 가상 대화에 실제로 등장한 인물과 등장하지 않은 인물을 각각 표시하세요.

### 구독자가 좋아할 대화 소재와 분위기
{target_audience} 취향을 참고해 소재 3개와 기대 분위기를 제안하세요. 취향을 보장된 사실처럼 단정하지 말고 창작 아이디어라고 표시하세요.

한국어로, 표와 제목을 사용해 읽기 쉽게 작성하세요. 오류의 근거와 수정 위치를 찾을 수 없으면 추측 대신 `확인 필요`라고 쓰세요.
"""
        st.session_state.pop("chatgpt_result_input", None)
        st.session_state.pop("chatgpt_report", None)
        st.session_state["chatgpt_prompt"] = prompt


if st.session_state.get("chatgpt_prompt"):
    st.divider()
    st.subheader("ChatGPT로 검수하기")
    st.markdown("**1. 프롬프트 복사 → ChatGPT에서 실행**")
    st.link_button("ChatGPT 열기", "https://chatgpt.com", use_container_width=True)
    st.info("ChatGPT에서 사용할 수 있는 성능 높은 모델을 선택하고, 아래 프롬프트를 복사해 붙여 넣으세요.")
    st.code(st.session_state["chatgpt_prompt"], language="markdown")

    st.markdown("**2. ChatGPT의 검수 결과를 아래에 붙여 넣으세요.**")
    with st.form("save_chatgpt_report"):
        chatgpt_result = st.text_area(
            "검수 결과",
            height=420,
            key="chatgpt_result_input",
            placeholder="ChatGPT가 찾은 문제, 근거 대사, 수정 위치와 교체 문구를 여기에 붙여 넣으세요.",
        )
        saved = st.form_submit_button("검수 결과 저장", type="primary", use_container_width=True)
    if saved:
        if not chatgpt_result.strip():
            st.error("ChatGPT 검수 결과를 붙여 넣어 주세요.")
        else:
            st.session_state["chatgpt_report"] = chatgpt_result.strip()

if st.session_state.get("chatgpt_report"):
    st.divider()
    st.subheader("검수 보고서")
    st.markdown(st.session_state["chatgpt_report"])
    st.download_button(
        "보고서 다운로드 (.md)",
        data=st.session_state["chatgpt_report"],
        file_name="멜팅_대화_검수_보고서.md",
        mime="text/markdown",
    )

with st.expander("검수 결과를 더 정확하게 받으려면"):
    st.markdown(
        """
        - 시나리오만 있으면 가상 대화로 **잠재 오류**를 추정합니다.
        - 멜팅에서 실제로 나온 대화를 같이 넣으면 **관찰된 오류**와 잠재 오류를 나눠 볼 수 있습니다.
        - 보고서에 문제가 나온 경우 `수정 위치`, `현재 문구`, `교체/추가 문구`를 확인해 원문에 반영하세요.
        """
    )

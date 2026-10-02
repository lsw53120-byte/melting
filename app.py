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
    '<p>시나리오를 넣으면 ChatGPT가 가상 사용자가 되어 캐릭터를 시험하고, 원인과 수정 방법을 정리합니다.</p></div>',
    unsafe_allow_html=True,
)

with st.sidebar:
    st.subheader("간단한 사용 순서")
    st.markdown(
        """
        1. 캐릭터와 시나리오를 붙여 넣습니다.
        2. 검수 프롬프트를 만들어 ChatGPT에 넣습니다.
        3. ChatGPT가 가상 상대역 대화와 원인 분석을 한 번에 작성합니다.
        4. 결과를 이 앱에 붙여 넣어 저장합니다.

        ChatGPT만 사용합니다. API 키는 필요하지 않습니다.
        """
    )


with st.form("review_form"):
    source = st.text_area(
        "검수할 시나리오·캐릭터 설정",
        height=300,
        placeholder=(
            "캐릭터 소개와 시나리오 원문을 그대로 붙여 넣으세요.\n"
            "인물이 여러 명이면 이름, 성격, 말투, 관계, 현재 상황도 포함해 주세요.\n\n"
            "예) 임금 도윤은 무뚝뚝하지만 은혜를 잊지 않는다. 궁녀 서린은 도윤을 짝사랑한다.\n"
            "연회가 끝난 밤, 두 사람은 궁 안에 단둘이 남았다."
        ),
        help="별도 양식으로 나누지 말고 가지고 있는 시나리오를 한 번에 붙여 넣으면 됩니다.",
    )
    transcript = st.text_area(
        "멜팅 실제 대화 (선택)",
        height=150,
        placeholder="예) 나: 임금이 나와 같이 잠자리에 들겠느냐?\n캐릭터: 어디 사세요?",
        help="없어도 검수할 수 있습니다. 실제 대화를 넣으면 관찰된 문제와 가상 테스트 결과를 구분합니다.",
    )
    testers = st.slider("가상 사용자 수", min_value=5, max_value=10, value=5)
    turns = st.slider("가상 사용자별 대화 왕복 횟수", min_value=3, max_value=8, value=4)
    audience = st.selectbox(
        "독자 취향 제안 (선택)",
        ["없음", "로맨스", "판타지·로맨스 판타지", "드라마·감정선", "코미디", "미스터리", "직접 입력"],
    )
    audience_custom = st.text_input(
        "원하는 독자 취향이나 분위기",
        placeholder="예: 느린 감정선, 무심한 인물의 다정함을 좋아하는 독자",
    ) if audience == "직접 입력" else ""
    submitted = st.form_submit_button("ChatGPT 검수 프롬프트 만들기", type="primary", use_container_width=True)


if submitted:
    if not source.strip():
        st.error("검수할 시나리오와 캐릭터 설정을 붙여 넣어 주세요.")
    else:
        preference = audience_custom.strip() if audience == "직접 입력" else audience
        actual_section = (
            f"""## 실제 멜팅 대화 기록
<actual_transcript>
{transcript.strip()}
</actual_transcript>
"""
            if transcript.strip()
            else "## 실제 멜팅 대화 기록\n제공되지 않음"
        )
        prompt = f"""당신은 사용자를 대신해 멜팅 캐릭터를 시험하는 가상 대화자이자, 결과를 분석하는 QA 편집자입니다. 시나리오를 요약해서 되풀이하는 일은 검수가 아닙니다. 반드시 모의 대화에서 문제를 찾아 원인·결과·구체적인 수정 조치까지 제시하세요.

## 검수 대상 시나리오·캐릭터 설정
<scenario>
{source.strip()}
</scenario>

{actual_section}

## 테스트 진행 방법
1. 원문에서 확인되는 인물, 관계, 장소, 목표, 말투, 이미 정해진 사실을 내부적으로 파악하세요. 원문 전체를 보고서에 옮기거나 장황하게 요약하지 마세요.
2. 원문 속 상황에 맞는 서로 다른 가상 사용자를 정확히 {testers}명 만드세요. 최소 5명이어야 합니다. 각 사용자는 성격, 대화 목적, 아는 정보, 말투, 질문 방식이 분명히 달라야 합니다. 예: 맥락을 잘 모르는 초면형, 관계와 감정을 세밀히 읽는 독자형, 직설형, 조심스러운 확인형, 예상 밖 화제 전환형. 시나리오와 무관한 역할은 만들지 마세요.
3. 각 가상 사용자가 캐릭터에게 실제로 할 법한 발언을 하고, 시나리오에 적힌 정보만으로 캐릭터의 답변을 모의 생성하세요. 총 {turns}회 왕복 대화를 사용자별로 진행합니다. 사용자마다 테스트하는 상황과 질문을 겹치지 않게 구성하고, 사용자가 질문하고 캐릭터가 답하는 형식으로 각 대사를 이름과 함께 표시하세요.
4. 캐릭터 답변은 멜팅에서 실제로 받은 응답이 아니라 모의 응답입니다. 원문에 없는 정보는 임의로 확정하지 말고 `설정에 없음` 또는 `가정`으로 표시하세요. 입력된 실제 대화가 있으면 모의 응답과 명확히 구분하세요.
5. 여러 캐릭터가 있으면 인물별 1:1 대화와 인물 간 다인 장면을 섞으세요. 실제로 테스트한 인물과 빠진 인물을 따로 기록하세요.
6. 모의 대화가 끝난 뒤 대화 검수자로 전환하세요. 시나리오의 부족·모호·충돌한 규칙이 어떤 답변 문제를 만들었는지 연결해 원인을 찾으세요. 그저 예상 답변을 생성하는 것으로 끝내지 마세요.

## 보고서 작성 기준
- 입력한 시나리오를 그대로 보여주거나 전체 줄거리를 다시 말하지 마세요. 각 문제에 필요한 짧은 근거만 인용하세요.
- 실제 멜팅 대화가 제공된 경우 `실제 관찰 오류`와 `가상 테스트 잠재 오류`를 구분하세요. 실제 기록이 없으면 모든 발견을 `가상 테스트 잠재 오류`라고 하세요. 실제 멜팅에서 발생했다고 주장하지 마세요.
- 각 문제의 원인을 `증상`과 구분하세요. 예: 증상은 질문을 무시한 답변이고, 가능한 원인은 인물의 우선 규칙·관계·직전 질문에 대한 답변 원칙이 빠졌거나 모호한 것일 수 있습니다. 시나리오 근거 없이 모델 내부 동작을 사실처럼 단정하지 마세요.
- 실제 문제를 찾지 못하면 억지로 만들지 말고, 테스트한 범위와 더 확인할 질문을 적으세요.

## 최종 결과 형식
### 핵심 판정
양호 / 수정 권장 / 문제 있음 중 하나, 가장 큰 원인과 대화에 미친 결과를 짧게 적으세요.

### 발견한 원인과 결과
| 심각도·출처 | 테스트 사용자 발언 | 캐릭터의 모의 답변 또는 실제 답변 | 원인 또는 근거 있는 가설 | 대화에 생긴 결과 |
문제별로 해당하는 문장만 짧게 인용하세요. 입력 시나리오를 반복하지 마세요.

### 어디를 어떻게 고칠지
문제마다 반드시 아래 항목을 작성하세요.
- **수정 위치:** 원문에서 수정할 인물/항목/문장. 제목이 없으면 어느 문장 뒤에 넣을지 지정
- **원인:** 해당 오류를 만들었거나 허용한 설정의 빈틈·모호성·충돌
- **조치:** 추가·삭제·교체할 규칙
- **복사해서 넣을 문구:** 바로 사용할 수 있는 구체적인 수정 문장
- **예상 결과:** 수정 후 어떤 오류가 줄고 대화가 어떻게 달라질지

원문 전체를 다시 쓰지 말고, 문제와 직접 관련 있는 부분만 고치세요. `설정을 더 자세히 하세요` 같은 일반론으로 끝내지 마세요.

### 수정 후 재시험
같은 원인을 확인할 질문 3개와 각 질문에서 기대되는 답의 핵심.

### 가상 사용자별 테스트 범위
최소 {testers}명 전원의 별칭, 대화 성향, 검증 목적, 실제로 던진 핵심 질문을 표로 정리하세요. 각 사용자가 테스트한 인물/관계 조합과 확인하지 못한 대상을 표시하세요. 사용자별로 다른 관점이 실제 테스트에 반영됐는지 확인하세요.

### 독자 취향 대화 아이디어
{preference} 취향을 고려해 소재와 분위기를 최대 3개 제안하세요. `없음`이면 이 항목은 생략하세요. 독자 반응은 보장된 사실이 아닌 창작 제안으로 표현하세요.

한국어로 작성하고, 원인·영향·조치가 연결되게 쓰세요. 근거가 부족한 부분은 `확인 필요`로 표시하세요.
"""
        st.session_state.pop("chatgpt_result_input", None)
        st.session_state.pop("chatgpt_report", None)
        st.session_state["chatgpt_prompt"] = prompt


if st.session_state.get("chatgpt_prompt"):
    st.divider()
    st.subheader("ChatGPT 검수")
    st.markdown(
        "1. 아래 프롬프트를 복사해 ChatGPT에 붙여 넣습니다.\n"
        "2. ChatGPT가 가상 사용자와 캐릭터의 대화를 만들고 분석합니다.\n"
        "3. 최종 보고서를 아래 칸에 붙여 넣으면 저장·다운로드할 수 있습니다."
    )
    st.link_button("ChatGPT 열기", "https://chatgpt.com", use_container_width=True)
    st.code(st.session_state["chatgpt_prompt"], language="markdown")

    st.markdown("**ChatGPT의 최종 보고서를 붙여 넣으세요.**")
    with st.form("save_chatgpt_report"):
        chatgpt_result = st.text_area(
            "원인·결과·수정 조치 보고서",
            height=420,
            key="chatgpt_result_input",
            placeholder="문제의 원인, 대화에 미친 결과, 수정 위치와 복사할 수정 문구가 포함된 보고서를 붙여 넣으세요.",
        )
        saved = st.form_submit_button("보고서 저장", type="primary", use_container_width=True)
    if saved:
        if not chatgpt_result.strip():
            st.error("ChatGPT 최종 보고서를 붙여 넣어 주세요.")
        else:
            st.session_state["chatgpt_report"] = chatgpt_result.strip()

if st.session_state.get("chatgpt_report"):
    st.divider()
    st.subheader("검수 보고서")
    st.markdown(st.session_state["chatgpt_report"])
    st.download_button(
        "보고서 다운로드 (.md)",
        data=st.session_state["chatgpt_report"],
        file_name="멜팅_대화_원인분석_보고서.md",
        mime="text/markdown",
    )

with st.expander("결과 해석"):
    st.markdown(
        """
        시나리오만 입력한 모의 테스트는 설정의 모호함이나 잠재 오류를 찾습니다. 멜팅에서 실제로 나온 대화도 넣으면 실제로 관찰된 문제와 가상 테스트 결과를 구분해 볼 수 있습니다. 모의 답변을 실제 멜팅 응답으로 간주하지 않습니다.
        """
    )

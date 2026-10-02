from __future__ import annotations

import os
import streamlit as st
from openai import OpenAI
from streamlit.errors import StreamlitSecretNotFoundError


MODELS = {
    "추천 · GPT-5.5 정확도 우선 (입력 $5 / 출력 $30, 100만 토큰당)": ("gpt-5.5", 5.00, 30.00),
    "균형형 · GPT-5.4 (입력 $2.50 / 출력 $15, 100만 토큰당)": ("gpt-5.4", 2.50, 15.00),
    "비용 절약 · GPT-5.4 mini (입력 $0.75 / 출력 $4.50, 100만 토큰당)": ("gpt-5.4-mini", 0.75, 4.50),
}


def get_api_key() -> str:
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    try:
        key = str(st.secrets.get("OPENAI_API_KEY", key)).strip()
    except StreamlitSecretNotFoundError:
        pass
    return key


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
    st.subheader("⚙️ 설정")
    # 관리자가 서버에 키를 심어두지 않은 경우만 사용자에게 입력받음
    api_key = get_api_key()
    if not api_key:
        st.markdown("⚠️ **OpenAI API 키가 필요합니다.**")
        api_key = st.text_input(
            "API Key 입력 (sk-...)",
            type="password",
            key="openai_api_key_input",
            help="키는 이 앱 서버에서 OpenAI API 호출에 사용됩니다. 본인이 실행하거나 신뢰하는 앱에만 입력하세요.",
        )
        st.markdown("[API 키 발급받기](https://platform.openai.com/api-keys)")
    else:
        st.success("API 키가 서버에 설정되어 있습니다.")
    st.caption("ChatGPT 구독과 별도로 API 사용료가 청구됩니다. 공개 앱에서 운영자 키를 공유하면 방문자가 운영자 비용을 발생시킬 수 있습니다.")
    selected_label = st.selectbox("ChatGPT 분석 모델", list(MODELS.keys()), index=0)
    model_id, input_rate, output_rate = MODELS[selected_label]

    st.divider()
    st.subheader("간단한 사용 순서")
    st.markdown(
        """
        1. 캐릭터와 시나리오를 붙여 넣습니다.
        2. 설정값을 맞추고 **가상 검수 자동 실행**을 누릅니다.
        3. 앱이 가상 사용자를 생성해 자동으로 대화를 시뮬레이션하고 결과를 분석합니다.
        4. 결과를 확인하고 보고서를 다운로드합니다.
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
        help="비워두면 ChatGPT가 캐릭터 응답까지 모의해 잠재 오류를 찾습니다. 실제 멜팅에서 난 오류를 확정하려면 실제 대화 기록을 넣으세요.",
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
    submitted = st.form_submit_button("🤖 가상 검수 자동 실행", type="primary", use_container_width=True)


if submitted:
    st.session_state.pop("chatgpt_report", None)
    st.session_state.pop("chatgpt_usage", None)
    if not api_key:
        st.error("API 키가 없습니다. 왼쪽 사이드바의 `API Key 입력`란에 키를 넣거나, 서버 관리자에게 OPENAI_API_KEY 설정을 요청하세요.")
    elif not source.strip():
        st.error("검수할 시나리오와 캐릭터 설정을 붙여 넣어 주세요.")
    else:
        preference = audience_custom.strip() if audience == "직접 입력" else audience
        # 프롬프트 인젝션(태그 충돌) 방지를 위한 이스케이핑
        safe_source = source.strip().replace("</scenario>", "< / scenario >").replace("<scenario>", "< scenario >")
        safe_transcript = transcript.strip().replace("</actual_transcript>", "< / actual_transcript >").replace("<actual_transcript>", "< actual_transcript >")

        actual_section = (
            f"""## 실제 멜팅 대화 기록
<actual_transcript>
{safe_transcript}
</actual_transcript>
"""
            if safe_transcript
            else "## 실제 멜팅 대화 기록\n제공되지 않음"
        )
        prompt = f"""당신은 사용자를 대신해 멜팅 캐릭터를 시험하는 대화 QA 담당자입니다. 서로 다른 가상 사용자 {testers}명이 실제로 대화해 본 것처럼 시나리오 속 캐릭터와 모의 대화를 진행하세요. 보고서는 원문 요약이 아니라, 테스트 중 드러난 구체적인 문제와 수정안이어야 합니다.

## 검수 대상 시나리오·캐릭터 설정
<scenario>
{safe_source}
</scenario>

{actual_section}

## 반드시 구분할 검수 한계
- 실제 대화 기록이 있으면 기록된 캐릭터 답변을 직접 분석하고, 그 응답을 근거로 `실제 관찰 오류`를 판정하세요.
- 실제 대화 기록이 없으면 캐릭터 답변을 직접 모의 생성해 시험하세요. 이때 발견한 것은 멜팅에서 실제로 발생했다고 단정하지 말고 `모의 테스트 잠재 오류` 또는 `설정 누락 위험`으로 표시하세요. 모의 대화는 사용자를 대신한 시나리오 기반 테스트입니다.
- 실제 대화 기록이 없는 상태에서도 테스트 대사, 모의 캐릭터 답변, 어긋난 설정 근거를 보고서에 써야 합니다. 모의 답변을 실제 멜팅 결과라고 속이지 말고, 그렇다고 대화 근거를 빼서 일반론만 쓰지도 마세요.
- 멜팅에 접속하거나 실제 캐릭터를 조작한 것은 아닙니다. 실제 작동 오류 확정은 실제 대화 기록이 있어야 가능합니다.

## 테스트 진행
1. 시나리오에서 인물별 말투, 관계, 현재 상황, 대화 목표, 금지/우선 규칙을 찾으세요.
2. 서로 다른 가상 사용자 {testers}명을 구성하세요. 각자는 지식 수준, 감정/대화 목적, 말투, 질문 방법이 달라야 합니다. 각각 시나리오와 관련된 다른 시험 질문을 하며, 사용자별 {turns}회 왕복 동안 캐릭터 역할로 직접 대답을 모의 생성하세요. 사용자와 캐릭터의 말은 구분해 기록하세요.
3. 모의 캐릭터 답변을 설정 속 명시된 사실, 성격·말투, 관계, 현재 장면과 대조하세요. 명시된 설정을 위반하거나 질문의 핵심을 무시한 답변은 `모의 테스트 잠재 오류`로 지적하세요. 설정이 답변 규칙을 정하지 않아 여러 방향이 가능할 뿐이면 `설정 누락 위험`으로 구분하고, 임의로 만든 모의 답변 자체를 설정 위반이라고 주장하지 마세요.
4. 오류 후보마다 입력 원문의 짧고 정확한 근거와 테스트 대화 한 쌍(사용자 발언 → 캐릭터 모의 답변)을 제시하세요. 그 근거로 설명할 수 없거나 구체적 장면/대사에 연결할 수 없는 후보는 제외하세요. `감정선이 부족함`, `설정을 더 자세히` 같은 일반론만으로 문제를 만들지 마세요.
5. 최소 {testers}명의 서로 다른 관점 테스트 질문을 범위 표에 전부 기록하세요. 전체 대본을 장황하게 옮기지 말고, 발견 사항에 필요한 대화만 인용하세요.

## 보고서 품질 기준
- 보고서에는 발견 내용만 쓰세요. 이 프롬프트의 지시, 검수 절차, 시나리오 요약은 쓰지 마세요.
- 각 발견은 `실제 관찰 오류`, `모의 테스트 잠재 오류`, `설정 누락 위험` 중 하나로 표시하세요. 출처가 실제 기록인지 모의 생성인지 혼동시키지 마세요.
- 문제마다 `증상 → 원인(확정/가설 구분) → 대화 영향 → 수정`이 한 줄기로 이어져야 합니다. 대화 영향은 구체적으로 설명하세요(예: 인물 관계가 깨짐, 질문에 답하지 않아 장면이 중단됨).
- 원인은 설정의 실제 빈틈/충돌만 지목하세요. 근거가 없는 모델 내부 원인 추측은 금지합니다.
- 최대 3개의 중요한 문제만 보고하세요. **유효한 문제가 없으면 억지로 지어내지 말고 반드시 `확인된 잠재 위험 없음`이라고 명확히 기재하고, 왜 근거 부족으로 판단했는지 설명하세요.**

## 최종 결과 형식
### 1. 판정
`문제 발견` / `잠재 위험 발견` / `현재 입력만으로 문제 확인 불가` 중 하나. 어떤 범위(실제 기록 또는 시나리오 설정)를 검사했는지 한 문장으로 밝히세요.

### 2. 발견 사항 (중요도 순, 최대 3개)
각 문제마다 다음 형식을 지키세요.
- **유형/심각도:** 실제 관찰 오류 또는 모의 테스트 잠재 오류 또는 설정 누락 위험 / 높음·보통·낮음
- **근거:** 실제 대화 또는 설정에서 핵심 부분만 짧게 인용
- **테스트 대화:** 가상 사용자 발언 → 캐릭터 답변. 실제 기록이면 `[실제]`, 직접 생성한 답변이면 `[모의]`로 표시
- **증상과 원인:** 답변의 어떤 점이 어긋났는지, 어떤 설정 문구/누락이 원인인지. 원인 확정이 불가하면 가설로 표시
- **대화 영향:** 사용자가 왜 부자연스럽다고 느끼거나 대화가 어떻게 끊기는지
- **수정 위치와 조치:** 어느 설정 항목 뒤에 무엇을 추가/교체할지
- **바로 붙여 넣을 수정 문구:** 현재 캐릭터·상황에 맞춘 구체적 문장. 원문을 통째로 다시 쓰지 말 것
- **수정 후 재시험:** 확인 질문 1개와 기대하는 반응의 핵심

### 3. 가상 사용자 테스트 범위
최소 {testers}명의 별칭 | 서로 다른 대화 관점 | 각자 던진 핵심 시험 질문을 짧은 표로 제시하세요. 각 사용자별 시험 질문을 빠뜨리지 마세요.
"""
        
        # '없음'일 때는 해당 프롬프트를 완전히 제외하여 AI 혼동 방지
        if preference != "없음":
            prompt += f"""
### 4. 독자 취향 아이디어
선택한 취향이 `{preference}`인 독자가 흥미를 느낄 만한 장면/대화 소재와 분위기를 최대 3개 제안하세요. 검수 결과와 섞지 말고 창작 제안이라고 표시하세요.
"""
            
        prompt += """
한국어로 간결하고 구체적으로 작성하세요. 표와 항목을 반복하지 말고, 발견이 없으면 빈 문제를 억지로 채우지 마세요.
"""
        
        st.divider()
        st.subheader("자동 검수 진행 중 ⏳")
        st.session_state.pop("chatgpt_report", None)
        try:
            client = OpenAI(api_key=api_key, timeout=180.0, max_retries=1)
            with st.spinner(f"{model_id} 모델이 가상 사용자 {testers}명의 대화를 분석하고 있습니다…"):
                response = client.responses.create(
                    model=model_id,
                    instructions=(
                        "당신은 대화형 캐릭터 시나리오 QA 전문가입니다. 원문을 요약하거나 재현하지 말고, "
                        "최소 5명의 서로 다른 가상 사용자가 캐릭터와 모의 대화를 진행해 발견한 구체적인 문제를 보고하세요. "
                        "각 문제는 정확한 설정 근거, 테스트 대화, 원인, 대화에 미친 결과, 수정 위치, 바로 붙여 넣을 수정 문구, 재시험 질문을 포함하세요. "
                        "실제 멜팅 대화가 제공되지 않았다면 모의 테스트 잠재 오류라고 표시하고 실제 오류라고 단정하지 마세요. "
                        "근거 없는 일반론이나 억지 문제를 만들지 말고, 보고서 본문만 한국어로 출력하세요."
                    ),
                    input=prompt,
                    reasoning={"effort": "high"},
                    max_output_tokens=6000,
                )

            report = response.output_text.strip()
            if not report:
                st.error("AI 응답에서 보고서 본문을 받지 못했습니다. 다시 분석해 주세요.")
                st.stop()
            st.session_state["chatgpt_report"] = report
            usage = response.usage
            input_tokens = usage.input_tokens if usage else 0
            output_tokens = usage.output_tokens if usage else 0
            approximate_cost = (input_tokens * input_rate + output_tokens * output_rate) / 1_000_000
            st.session_state["chatgpt_usage"] = (
                f"{model_id} · 입력 {input_tokens:,} 토큰 · 출력 {output_tokens:,} 토큰 · "
                f"공식 단가 기준 추정 ${approximate_cost:.4f} USD"
            )
            st.success("✨ 검수가 완료되었습니다!")
        except Exception as e:
            error_text = str(e).lower()
            if "401" in error_text or "authentication" in error_text or "api key" in error_text:
                st.error("API 키가 올바르지 않습니다. OpenAI API 키를 확인해 주세요.")
            elif "429" in error_text or "quota" in error_text or "billing" in error_text:
                st.error("API 사용 한도 또는 결제 설정을 확인해 주세요.")
            elif "model" in error_text and ("not found" in error_text or "does not exist" in error_text):
                st.error(f"선택한 모델({model_id})에 접근할 수 없습니다. API 계정의 모델 권한을 확인해 주세요.")
            else:
                st.error(f"OpenAI API 호출에 실패했습니다: {e}")

if st.session_state.get("chatgpt_report"):
    st.divider()
    st.subheader("검수 보고서")
    if st.session_state.get("chatgpt_usage"):
        st.caption(st.session_state["chatgpt_usage"])
    st.markdown(st.session_state["chatgpt_report"])
    st.download_button(
        "보고서 다운로드 (.txt)",
        data=st.session_state["chatgpt_report"],
        file_name="멜팅_대화_원인분석_보고서.txt",
        mime="text/plain",
    )

with st.expander("결과 해석"):
    st.markdown(
        """
        시나리오와 선택한 모델은 OpenAI API로 전송됩니다. 시나리오만 검수할 때 AI가 캐릭터 답변까지 모의 시험하고 결과를 `모의 테스트 잠재 오류`로 표시합니다. 이는 멜팅의 실제 답변을 확인한 것이 아닙니다. 실제 오류를 분석하려면 멜팅 대화 기록을 넣으세요. API 사용료는 ChatGPT 구독료와 별도입니다.
        """
    )

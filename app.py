import streamlit as st

# 페이지 제목 설정
st.title("🗣️ 우리들의 실시간 끝말잇기")
st.write("제시된 단어의 마지막 글자로 시작하는 단어를 입력하세요!")

# 게임 상태 초기화 (처음 시작할 때)
if "history" not in st.session_state:
    st.session_state.history = ["바나나"]  # 첫 시작 단어

# 현재 이어야 할 단어
current_word = st.session_state.history[-1]
last_char = current_word[-1]

st.info(f"현재 단어: **{current_word}** (이 글자 **'{last_char}'**(으)로 시작하는 단어를 입력하세요!)")

# 사용자 입력 받기
with st.form(key="word_form", clear_on_submit=True):
    user_input = st.text_input("단어를 입력하세요:")
    submit_button = st.form_submit_button(label="제출하기")

if submit_button:
    if not user_input:
        st.warning("단어를 입력해주세요!")
    else:
        # 끝말잇기 규칙 검증
        if user_input[0] != last_char:
            st.error(f"틀렸습니다! '{last_char}'(으)로 시작하는 단어를 입력해야 합니다.")
        elif user_input in st.session_state.history:
            st.warning("이미 사용된 단어입니다!")
        else:
            # 정답인 경우 기록에 추가
            st.session_state.history.append(user_input)
            st.success(f"정답입니다! '{user_input}' 입력 성공!")
            st.rerun()

# 지금까지의 게임 기록 보여주기
st.write("---")
st.subheader("📜 끝말잇기 기록")
for i, word in enumerate(st.session_state.history):
    st.write(f"{i+1}. **{word}**")

# 게임 초기화 버튼
if st.button("게임 리셋"):
    st.session_state.history = ["바나나"]
    st.rerun()
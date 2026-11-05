import os
import streamlit as st

# 페이지 제목 설정
st.title("🗣️ 우리들의 실시간 끝말잇기")
st.write("제시된 단어의 마지막 글자로 시작하는 단어를 입력하세요!")

# 파일에 기록을 저장하고 불러오는 함수
HISTORY_FILE = "history.txt"


def load_history():
  if os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
      lines = [line.strip() for line in f.readlines() if line.strip()]
      if lines:
        return lines
  return ["바나나"]


def save_history(history):
  with open(HISTORY_FILE, "w", encoding="utf-8") as f:
    for word in history:
      f.write(f"{word}\n")


# 세션 또는 파일에서 기록 불러오기 (주기적으로 최신 상태를 읽어옴)
history = load_history()

# 현재 이어야 할 단어
current_word = history[-1]
last_char = current_word[-1]

st.info(
    f"현재 단어: **{current_word}** (이 글자 **'{last_char}'**(으)로 시작하는 단어를"
    " 입력하세요!)"
)

# 사용자 입력 받기
with st.form(key="word_form", clear_on_submit=True):
  user_input = st.text_input("단어를 입력하세요:")
  submit_button = st.form_submit_button(label="제출하기")

if submit_button:
  if not user_input:
    st.warning("단어를 입력해주세요!")
  else:
    # 최신 기록을 다시 불러와서 검증
    history = load_history()
    current_word = history[-1]
    last_char = current_word[-1]

    # 끝말잇기 규칙 검증
    if user_input[0] != last_char:
      st.error(
          f"틀렸습니다! '{last_char}'(으)로 시작하는 단어를 입력해야 합니다."
      )
    elif user_input in history:
      st.warning("이미 사용된 단어입니다!")
    else:
      # 정답인 경우 기록에 추가 후 파일에 저장
      history.append(user_input)
      save_history(history)
      st.success(f"정답입니다! '{user_input}' 입력 성공!")
      st.rerun()

# 지금까지의 게임 기록 보여주기
st.write("---")
st.subheader("📜 끝말잇기 기록")
for i, word in enumerate(history):
  st.write(f"{i+1}. **{word}**")

# 게임 초기화 버튼
if st.button("게임 리셋"):
  save_history(["바나나"])
  st.rerun()
import os
import streamlit as st
from streamlit_autorefresh import st_autorefresh

# 1초(1000밀리초)마다 자동으로 화면을 갱신하여 실시간 연동 (충돌 방지)
st_autorefresh(interval=1000, limit=None, key="game_realtime_refresher")

# 페이지 설정
st.title("🗣️ 방 단위 실시간 끝말잇기 대전")
st.write(
    "방 이름을 입력해 접속하고, 최대 5명까지 한 방에서 실시간으로 끝말잇기를"
    " 즐겨보세요!"
)

# 세션 상태 초기화
if "room_name" not in st.session_state:
  st.session_state.room_name = ""
if "player_name" not in st.session_state:
  st.session_state.player_name = ""

# --- 1단계: 방 입장 화면 ---
if not st.session_state.room_name or not st.session_state.player_name:
  st.subheader("🚪 게임 방 입장하기")
  with st.form("join_form"):
    input_room = st.text_input("참여할 방 이름 (예: room1)")
    input_name = st.text_input("본인의 닉네임")
    enter_btn = st.form_submit_button("방 들어가기")

    if enter_btn:
      if input_room and input_name:
        st.session_state.room_name = input_room.strip()
        st.session_state.player_name = input_name.strip()
        st.rerun()
      else:
        st.warning("방 이름과 닉네임을 모두 입력해주세요!")
  st.stop()

# 방별 파일 경로 설정
room_file = f"history_{st.session_state.room_name}.txt"
players_file = f"players_{st.session_state.room_name}.txt"


# 데이터 불러오기 함수
def load_game_data():
  history = ["바나나"]
  if os.path.exists(room_file):
    with open(room_file, "r", encoding="utf-8") as f:
      lines = [line.strip() for line in f.readlines() if line.strip()]
      if lines:
        history = lines

  players = []
  if os.path.exists(players_file):
    with open(players_file, "r", encoding="utf-8") as f:
      players = [line.strip() for line in f.readlines() if line.strip()]

  return history, players


def save_game_data(history, players):
  with open(room_file, "w", encoding="utf-8") as f:
    for word in history:
      f.write(f"{word}\n")
  with open(players_file, "w", encoding="utf-8") as f:
    for p in players:
      f.write(f"{p}\n")


history, players = load_game_data()

# 순수 단어 목록 추출 (중복 검사용)
used_words = [h.split(" (")[0] for h in history]

# 플레이어 명단 등록 (최대 5명 제한)
if st.session_state.player_name not in players:
  if len(players) >= 5:
    st.error(
        "❌ 이 방은 최대 인원 5명이 이미 모두 참여하여 더 들어갈 수 없습니다!"
    )
    if st.button("다른 방으로 가기"):
      st.session_state.room_name = ""
      st.session_state.player_name = ""
      st.rerun()
    st.stop()
  else:
    players.append(st.session_state.player_name)
    save_game_data(history, players)

# --- 2단계: 게임 플레이 화면 ---
st.success(
    f"🏠 현재 방: **{st.session_state.room_name}** | 👤 내 닉네임:"
    f" **{st.session_state.player_name}** (참여 인원: {len(players)}/5명)"
)

# 현재 단어 및 규칙 확인
current_full = history[-1]
current_word = current_full.split(" (")[0]  # 닉네임 제외한 순수 단어
last_char = current_word[-1]

st.info(
    f"현재 단어: **{current_word}** (이 글자 **'{last_char}'**(으)로 시작하는 단어를"
    " 입력하세요!)"
)
st.caption(
    "⚡ 규칙: 한 사람당 10초 제한 / 이미 사용된 단어는 절대 재사용 불가!"
)

# 사용자 입력 폼
with st.form(key="word_form", clear_on_submit=True):
  user_input = st.text_input("단어를 입력하세요:")
  submit_button = st.form_submit_button(label="단어 제출")

if submit_button:
  if not user_input:
    st.warning("단어를 입력해주세요!")
  else:
    # 최신 데이터 다시 동기화
    history, players = load_game_data()
    used_words = [h.split(" (")[0] for h in history]
    current_word = used_words[-1]
    last_char = current_word[-1]

    # 끝말잇기 검증
    if user_input[0] != last_char:
      st.error(
          f"틀렸습니다! '{last_char}'(으)로 시작하는 단어를 입력해야 합니다."
      )
    elif user_input in used_words:
      st.warning("⚠️ 이미 사용된 단어입니다! 다른 단어를 입력하세요.")
    else:
      # 정답 처리 및 기록 추가
      history.append(f"{user_input} ({st.session_state.player_name})")
      save_game_data(history, players)
      st.success(f"정답! '{user_input}' 입력 성공!")
      st.rerun()

# 게임 기록 출력
st.write("---")
st.subheader("📜 방 안의 끝말잇기 기록")
for i, item in enumerate(history):
  st.write(f"{i+1}. **{item}**")

# 하단 버튼
col1, col2 = st.columns(2)
with col1:
  if st.button("🔄 방 게임 리셋"):
    save_game_data(["바나나"], players)
    st.rerun()
with col2:
  if st.button("🚪 다른 방으로 나가기"):
    st.session_state.room_name = ""
    st.session_state.player_name = ""
    st.rerun()

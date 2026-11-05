import os
import time
import streamlit as st
from streamlit_autorefresh import st_autorefresh

# 1초마다 자동 새로고침으로 실시간 동기화
st_autorefresh(interval=1000, limit=None, key="game_realtime_refresher")

st.title("🗣️ 실시간 멀티플레이 끝말잇기 대전")

# 세션 상태 초기화
if "player_name" not in st.session_state:
  st.session_state.player_name = ""
if "room_name" not in st.session_state:
  st.session_state.room_name = ""

# --- [1단계] 닉네임 입력 및 자동 방 배정 ---
if not st.session_state.player_name:
  st.subheader("👤 게임에 사용할 닉네임을 입력하세요")
  with st.form("name_form"):
    input_name = st.text_input("닉네임")
    name_btn = st.form_submit_button("입장하기")

    if name_btn:
      if input_name.strip():
        st.session_state.player_name = input_name.strip()
        st.session_state.room_name = "room_1"
        st.rerun()
      else:
        st.warning("닉네임을 입력해주세요!")
  st.stop()

# 방 파일 경로 설정
room_name = st.session_state.room_name
history_file = f"history_{room_name}.txt"
players_file = f"players_{room_name}.txt"
ready_file = f"ready_{room_name}.txt"
game_state_file = f"state_{room_name}.txt"  # waiting, countdown, playing, gameover


# 데이터 로드/저장 함수
def load_data():
  history = ["바나나"]
  if os.path.exists(history_file):
    with open(history_file, "r", encoding="utf-8") as f:
      lines = [l.strip() for l in f.readlines() if l.strip()]
      if lines:
        history = lines

  players = []
  if os.path.exists(players_file):
    with open(players_file, "r", encoding="utf-8") as f:
      players = [l.strip() for l in f.readlines() if l.strip()]

  readies = []
  if os.path.exists(ready_file):
    with open(ready_file, "r", encoding="utf-8") as f:
      readies = [l.strip() for l in f.readlines() if l.strip()]

  g_state = "waiting"  # waiting, countdown, playing, gameover
  turn_idx = 0
  turn_start_time = time.time()
  lives = 3  # 방 전체 목숨 (기본 3개)

  if os.path.exists(game_state_file):
    with open(game_state_file, "r", encoding="utf-8") as f:
      content = f.read().splitlines()
      if len(content) >= 4:
        g_state = content[0]
        try:
          turn_idx = int(content[1])
          turn_start_time = float(content[2])
          lives = int(content[3])
        except:
          pass

  return history, players, readies, g_state, turn_idx, turn_start_time, lives


def save_data(
    history,
    players,
    readies,
    g_state="waiting",
    turn_idx=0,
    turn_start=0.0,
    lives=3,
):
  with open(history_file, "w", encoding="utf-8") as f:
    f.write("\n".join(history))
  with open(players_file, "w", encoding="utf-8") as f:
    f.write("\n".join(players))
  with open(ready_file, "w", encoding="utf-8") as f:
    f.write("\n".join(readies))
  with open(game_state_file, "w", encoding="utf-8") as f:
    f.write(f"{g_state}\n{turn_idx}\n{turn_start}\n{lives}")


(
    history,
    players,
    readies,
    game_state,
    current_turn_idx,
    turn_start_time,
    lives,
) = load_data()

# 플레이어 등록 (최대 5명)
my_name = st.session_state.player_name
if my_name not in players:
  if len(players) >= 5:
    st.error("❌ 방 인원이 꽉 찼습니다 (최대 5명).")
    if st.button("처음으로"):
      st.session_state.player_name = ""
      st.rerun()
    st.stop()
  else:
    players.append(my_name)
    save_data(
        history,
        players,
        readies,
        game_state,
        current_turn_idx,
        turn_start_time,
        lives,
    )

st.success(
    f"🏠 방 이름: **{room_name}** | 👤 내 닉네임: **{my_name}** (참여 인원:"
    f" {len(players)}/5명)"
)

# --- [2단계] 대기실 및 준비 단계 ---
if game_state == "waiting":
  st.subheader("🚪 게임 대기실")
  st.write("참여한 플레이어 목록:")
  for p in players:
    status = "✅ 준비 완료" if p in readies else "⏳ 대기 중"
    st.write(f"- **{p}** ({status})")

  is_ready = my_name in readies

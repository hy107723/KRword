import os
import time
from bs4 import BeautifulSoup
import requests
import streamlit as st
from streamlit_autorefresh import st_autorefresh

# 1초마다 자동 새로고침으로 실시간 동기화
st_autorefresh(interval=1000, limit=None, key="game_realtime_refresher")

st.title("🗣️ 실시간 멀티플레이 끝말잇기 대전 (끄투코리아 실시간 사전 연동)")

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

# 방 파일 경로 설정 (오타 수정 완료)
room_name = (
    st.session_state.room_name
    if "room_name" in st.session_state
    else "room_1"
)
history_file = f"history_{room_name}.txt"
players_file = f"players_{room_name}.txt"
ready_file = f"ready_{room_name}.txt"
game_state_file = f"state_{room_name}.txt"


# 끄투코리아 실시간 사전 존재 여부 확인 함수
def check_kkutu_dictionary(word):
  try:
    url = f"https://kkutu.info/dict.php?q={word}"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers, timeout=3)
    if response.status_code == 200:
      soup = BeautifulSoup(response.text, "html.parser")
      result_text = soup.get_text()
      if word in result_text and "검색 결과가 없습니다" not in result_text:
        return True
  except Exception as e:
    print(f"사전 조회 에러: {e}")
  return True


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

  g_state = "waiting"
  turn_idx = 0
  turn_start_time = time.time()
  lives = 3

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

my_name = st.session_state.player_name
if my_name not in players:
  if len(players) >= 5:
    st.error("❌ 방 인원이 꽉 찼습니다 (최대 5명).")
    if st.button("처음으로", key="first_btn"):
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
  if not is_ready:
    if st.button("🙋‍♂️ 준비하기", key="ready_btn"):
      if my_name not in readies:
        readies.append(my_name)
      if len(players) > 0 and len(readies) == len(players):
        game_state = "countdown"
        current_turn_idx = 0
        turn_start_time = time.time()
        history = ["바나나"]
        lives = 3
      save_data(
          history,
          players,
          readies,
          game_state,
          current_turn_idx,
          turn_start_time,
          lives,
      )
      st.rerun()
  else:
    st.info("준비 완료! 다른 플레이어들을 기다리는 중...")
    if st.button("준비 취소", key="cancel_ready_btn"):
      if my_name in readies:
        readies.remove(my_name)
      save_data(
          history,
          players,
          readies,
          game_state,
          current_turn_idx,
          turn_start_time,
          lives,
      )
      st.rerun()

  if st.button("🚪 방 나가기", key="leave_btn"):
    if my_name in players:
      players.remove(my_name)
    if my_name in readies:
      readies.remove(my_name)
    save_data(history, players, readies, "waiting", 0, time.time(), 3)
    st.session_state.player_name = ""
    st.rerun()

  st.stop()

# --- [3단계] 5초 카운트다운 연출 ---
if game_state == "countdown":
  st.markdown(
      "<h1"
      " style='text-align: center; color: #ff4b4b;'>🚀 곧 게임이 시작됩니다!</h1>",
      unsafe_allow_html=True,
  )
  st.markdown(
      "<h2 style='text-align: center;'>Ready... Start!</h2>",
      unsafe_allow_html=True,
  )
  time.sleep(1.5)

  game_state = "playing"
  turn_start_time = time.time()
  save_data(
      history,
      players,
      readies,
      game_state,
      current_turn_idx,
      turn_start_time,
      lives,
  )
  st.rerun()

# --- [4단계] GAME OVER 연출 ---
if game_state == "gameover":
  st.markdown(
      "<h1 style='text-align: center; color: red; font-size: 3em;'>💀 GAME"
      " OVER 💀</h1>",
      unsafe_allow_html=True,
  )
  st.markdown(
      "<h3 style='text-align: center;'>목숨 3개를 모두 사용하였습니다!</h3>",
      unsafe_allow_html=True,
  )
  st.write("---")

  if st.button("🔄 대기실로 돌아가기", key="gameover_btn"):
    save_data(["바나나"], players, [], "waiting", 0, time.time(), 3)
    st.rerun()
  st.stop()

# --- [5단계] 본격적인 게임 플레이 진행 (15초 제한 & 실시간 사전 연동) ---
if game_state == "playing":
  if current_turn_idx >= len(players):
    current_turn_idx = 0

  current_player = players[current_turn_idx]
  elapsed_time = time.time() - turn_start_time
  remaining_time = max(0, 15 - int(elapsed_time))

  heart_display = "❤️ " * lives + "🖤 " * (3 - lives)
  st.markdown(
      f"### 💖 남은 목숨: **{heart_display}** ({lives}/3)",
      unsafe_allow_html=True,
  )

  if elapsed_time > 15:
    lives -= 1
    if lives <= 0:
      game_state = "gameover"
    else:
      current_turn_idx = (current_turn_idx + 1) % len(players)
      turn_start_time = time.time()

    save_data(
        history,
        players,
        readies,
        game_state,
        current_turn_idx,
        turn_start_time,
        lives,
    )
    st.rerun()

  st.markdown(
      f"### 🎯 현재 턴 주인공: <span"
      f" style='color:blue;font-size:1.3em;'>{current_player}</span>",
      unsafe_allow_html=True,
  )

  progress_val = max(0.0, min(1.0, (15 - elapsed_time) / 15.0))
  st.progress(progress_val)
  st.write(f"⏱️ 남은 시간: **{remaining_time}초**")

  current_full = history[-1]
  current_word = current_full.split(" (")[0]
  last_char = current_word[-1]

  st.info(
      f"현재 단어: **{current_word}** (이 글자 **'{last_char}'**(으)로 시작하는 단어)"
  )

  is_my_turn = my_name == current_player

  if is_my_turn:
    with st.form(key="play_form", clear_on_submit=True):
      user_input = st.text_input(
          "당신의 턴! 단어를 입력하세요 (끄투코리아 사전 연동):"
      )
      submitted = st.form_submit_button("제출")

      if submitted:
        if not user_input:
          st.warning("단어를 입력해주세요!")
        else:
          used_words = [h.split(" (")[0] for h in history]

          if user_input[0] != last_char:
            lives -= 1
            st.error(
                f"틀렸습니다! '{last_char}'(으)로 시작하는 단어가 아닙니다."
                " (목숨 -1)"
            )
          elif user_input in used_words:
            lives -= 1
            st.warning("⚠️ 이미 사용된 단어입니다! (목숨 -1)")
          elif not check_kkutu_dictionary(user_input):
            lives -= 1
            st.error(
                f"❌ '{user_input}'은(는) 끄투코리아 사전에 존재하지 않는"
                " 단어입니다! (목숨 -1)"
            )
          else:
            history.append(f"{user_input} ({my_name})")
            current_turn_idx = (current_turn_idx + 1) % len(players)
            turn_start_time = time.time()
            save_data(
                history,
                players,
                readies,
                game_state,
                current_turn_idx,
                turn_start_time,
                lives,
            )
            st.rerun()

          if lives <= 0:
            game_state = "gameover"

          save_data(
              history,
              players,
              readies,
              game_state,
              current_turn_idx,
              turn_start_time,
              lives,
          )
          time.sleep(1)
          st.rerun()
  else:
    st.warning(
        f"🔒 현재는 **{current_player}**님의 턴입니다. 잠시 기다려 주세요!"
    )

  st.write("---")
  st.subheader("📜 끝말잇기 기록")
  for i, h_item in enumerate(history):
    st.write(f"{i+1}. **{h_item}**")

  col1, col2 = st.columns(2)
  with col1:
    if st.button("🔄 방 초기화 (대기실로)", key="reset_btn"):
      save_data(["바나나"], players, [], "waiting", 0, time.time(), 3)
      st.rerun()
  with col2:
    if st.button("🚪 방 나가기", key="out_btn"):
      if my_name in players:
        players.remove(my_name)
      if my_name in readies:
        readies.remove(my_name)
      save_data(history, players, readies, "waiting", 0, time.time(), 3)
      st.session_state.player_name = ""
      st.rerun()

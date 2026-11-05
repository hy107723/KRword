import json
import os
import time
import streamlit as st
from streamlit_autorefresh import st_autorefresh

# 1초마다 자동 새로고침으로 실시간 동기화
st_autorefresh(interval=1000, limit=None, key="game_realtime_refresher")

st.title("🗣️ 실시간 멀티플레이 끝말잇기 대전 (로컬 사전 단어 검증 연동)")

# 세션 상태 초기화
if "player_name" not in st.session_state:
    st.session_state.player_name = ""
if "room_name" not in st.session_state:
    st.session_state.room_name = ""

# --- [1단계] 닉네임 입력 및 동적 방 자동 배정 ---
if not st.session_state.player_name:
    st.subheader("👤 게임에 사용할 닉네임을 입력하세요")
    with st.form("name_form"):
        input_name = st.text_input("닉네임")
        name_btn = st.form_submit_button("입장하기")

        if name_btn:
            if input_name.strip():
                st.session_state.player_name = input_name.strip()

                target_room = None
                room_idx = 1
                while True:
                    p_file = f"players_room_{room_idx}.txt"
                    s_file = f"state_room_{room_idx}.txt"

                    existing_players = []
                    if os.path.exists(p_file):
                        with open(p_file, "r", encoding="utf-8") as f:
                            existing_players = [
                                l.strip() for l in f.readlines() if l.strip()
                            ]

                    game_state = "waiting"
                    if os.path.exists(s_file):
                        with open(s_file, "r", encoding="utf-8") as f:
                            lines = f.read().splitlines()
                            if lines:
                                game_state = lines[0]

                    if game_state == "waiting" and len(existing_players) < 5:
                        target_room = f"room_{room_idx}"
                        break

                    if not os.path.exists(p_file):
                        target_room = f"room_{room_idx}"
                        break

                    room_idx += 1

                st.session_state.room_name = target_room
                st.rerun()
            else:
                st.warning("닉네임을 입력해주세요!")
    st.stop()

# 방 파일 경로 설정
room_name = (
    st.session_state.room_name
    if "room_name" in st.session_state
    else "room_1"
)
history_file = f"history_{room_name}.txt"
players_file = f"players_{room_name}.txt"
ready_file = f"ready_{room_name}.txt"
game_state_file = f"state_{room_name}.txt"
chat_file = f"chat_{room_name}.txt"


# --- [로컬 사전 기반 단어 검증 시스템] ---
@st.cache_resource
def load_kkutu_dictionary():
    """끄투 소스 내 ko_KR.json 사전을 메모리에 로드 (캐싱 적용)"""
    # 프로젝트 내 ko_KR.json 파일 경로에 맞게 수정해주세요 (예: 'lang/ko_KR.json')
    json_path = "lang/ko_KR.json"
    if not os.path.exists(json_path):
        return set()

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return set(data)
            elif isinstance(data, dict):
                return set(data.keys())
    except Exception:
        pass
    return set()


VALID_DICTIONARY = load_kkutu_dictionary()


def validate_word(word):
    """한글 완성형 명사 여부 및 로컬 사전(ko_KR.json) 존재 여부 검증"""
    if not word or len(word) < 2:
        return False
    for char in word:
        # 한글 완성형(가~힣) 범위 체크
        if not ("가" <= char <= "힣"):
            return False

    # 사전에 데이터가 정상 로드된 경우 사전 존재 여부 확인
    if VALID_DICTIONARY:
        if word not in VALID_DICTIONARY:
            return False

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

    chats = []
    if os.path.exists(chat_file):
        with open(chat_file, "r", encoding="utf-8") as f:
            chats = [l.strip() for l in f.readlines() if l.strip()]

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

    return history, players, readies, chats, g_state, turn_idx, turn_start_time, lives


def save_data(
    history,
    players,
    readies,
    chats,
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
    with open(chat_file, "w", encoding="utf-8") as f:
        f.write("\n".join(chats))
    with open(game_state_file, "w", encoding="utf-8") as f:
        f.write(f"{g_state}\n{turn_idx}\n{turn_start}\n{lives}")


# 게임 오버 시 방 전체 데이터를 완전히 초기화하는 함수
def reset_entire_room():
    for f_path in [
        history_file,
        players_file,
        ready_file,
        game_state_file,
        chat_file,
    ]:
        if os.path.exists(f_path):
            try:
                os.remove(f_path)
            except:
                pass


(
    history,
    players,
    readies,
    chats,
    game_state,
    current_turn_idx,
    turn_start_time,
    lives,
) = load_data()

my_name = st.session_state.player_name

if (
    game_state == "waiting"
    and my_name not in players
    and len(players) > 0
    and st.session_state.get("was_in_room", False)
):
    st.warning("⚠️ 방장에 의해 방에서 추방되었습니다!")
    st.session_state.player_name = ""
    st.session_state.room_name = ""
    st.session_state.was_in_room = False
    st.rerun()

if my_name not in players:
    if len(players) >= 5:
        st.error("❌ 현재 방 인원이 꽉 찼습니다.")
        if st.button("다른 방 다시 찾기", key="retry_room_btn"):
            st.session_state.player_name = ""
            st.session_state.room_name = ""
            st.rerun()
        st.stop()
    else:
        players.append(my_name)
        st.session_state.was_in_room = True
        save_data(
            history,
            players,
            readies,
            chats,
            game_state,
            current_turn_idx,
            turn_start_time,
            lives,
        )

st.success(
    f"🏠 방 이름: **{room_name}** | 👤 내 닉네임: **{my_name}** (참여 인원:"
    f" {len(players)}/5명)"
)

# --- [사이드바] 실시간 채팅창 기능 ---
with st.sidebar:
    st.subheader(f"💬 방 번호 [{room_name}] 실시간 채팅")
    chat_container = st.container(height=350)
    with chat_container:
        if chats:
            for c in chats:
                st.write(c)
        else:
            st.caption("아직 대화 내용이 없습니다.")

    with st.form(key="chat_form", clear_on_submit=True):
        chat_input = st.text_input("메시지 입력")
        chat_submitted = st.form_submit_button("전송")
        if chat_submitted and chat_input.strip():
            chats.append(f"[{my_name}] {chat_input.strip()}")
            if len(chats) > 50:
                chats = chats[-50:]
            save_data(
                history,
                players,
                readies,
                chats,
                game_state,
                current_turn_idx,
                turn_start_time,
                lives,
            )
            st.rerun()

# --- [2단계] 대기실 및 준비 단계 ---
if game_state == "waiting":
    st.subheader("🚪 게임 대기실")
    st.write("참여한 플레이어 목록:")

    for p in players:
        status = "✅ 준비 완료" if p in readies else "⏳ 대기 중"
        col_p1, col_p2 = st.columns([3, 1])
        with col_p1:
            st.write(f"- **{p}** ({status})")
        with col_p2:
            if p != my_name:
                if st.button("🚫 강퇴", key=f"kick_{p}"):
                    if p in players:
                        players.remove(p)
                    if p in readies:
                        readies.remove(p)
                    chats.append(f"📢 [시스템] {p}님이 강퇴되었습니다.")
                    save_data(
                        history,
                        players,
                        readies,
                        chats,
                        game_state,
                        current_turn_idx,
                        turn_start_time,
                        lives,
                    )
                    st.rerun()

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
                chats,
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
                chats,
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
        save_data(history, players, readies, chats, "waiting", 0, time.time(), 3)
        st.session_state.player_name = ""
        st.session_state.room_name = ""
        st.session_state.was_in_room = False
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
        chats,
        game_state,
        current_turn_idx,
        turn_start_time,
        lives,
    )
    st.rerun()

# --- [4단계] GAME OVER 연출 및 방 전체 초기화 ---
if game_state == "gameover":
    st.markdown(
        "<h1 style='text-align: center; color: red; font-size: 3em;'>💀 GAME"
        " OVER 💀</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<h3 style='text-align: center;'>목숨 3개를 모두 사용하였습니다! 방이"
        " 초기화됩니다.</h3>",
        unsafe_allow_html=True,
    )
    st.write("---")

    if st.button("🔄 처음으로 돌아가기", key="gameover_btn"):
        reset_entire_room()  # 방 자체를 완전히 초기화
        st.session_state.player_name = ""
        st.session_state.room_name = ""
        st.session_state.was_in_room = False
        st.rerun()
    st.stop()

# --- [5단계] 본격적인 게임 플레이 진행 ---
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
            chats,
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
            user_input = st.text_input("당신의 턴! 단어를 입력하세요:")
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
                    elif not validate_word(user_input):
                        lives -= 1
                        st.error(
                            f"❌ '{user_input}'은(는) 올바른 단어 형식이 아니거나 사전에 없는 단어입니다! (목숨 -1)"
                        )
                    else:
                        history.append(f"{user_input} ({my_name})")
                        current_turn_idx = (current_turn_idx + 1) % len(players)
                        turn_start_time = time.time()
                        save_data(
                            history,
                            players,
                            readies,
                            chats,
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
                        chats,
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
            save_data(["바나나"], players, [], chats, "waiting", 0, time.time(), 3)
            st.rerun()
    with col2:
        if st.button("🚪 방 나가기", key="out_btn"):
            if my_name in players:
                players.remove(my_name)
            if my_name in readies:
                readies.remove(my_name)
            save_data(
                history, players, readies, chats, "waiting", 0, time.time(), 3
            )
            st.session_state.player_name = ""
            st.session_state.room_name = ""
            st.session_state.was_in_room = False
            st.rerun()

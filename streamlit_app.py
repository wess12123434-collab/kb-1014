import base64
import random
import time
from pathlib import Path

import streamlit as st

st.set_page_config(page_title="두더지 잡기 게임", page_icon="🐹")

GAME_FOLDER = Path(__file__).parent
HOLE_IMAGE = GAME_FOLDER / "hole.png"
MOLE_IMAGE = GAME_FOLDER / "img.png"


@st.cache_data
def load_image_data(image_path):
    return base64.b64encode(image_path.read_bytes()).decode("ascii")


HOLE_IMAGE_DATA = load_image_data(HOLE_IMAGE)
MOLE_IMAGE_DATA = load_image_data(MOLE_IMAGE)

MOLE_DURATION_SECONDS = 1.5


def resolve_mole(mole_id, was_caught, now):
    state = st.session_state
    if (
        state.game_over
        or mole_id != state.mole_id
        or state.resolved_mole_id == mole_id
    ):
        return

    state.resolved_mole_id = mole_id
    previous_hole = state.mole_hole

    if was_caught:
        state.score += 10
        state.message = "두더지를 잡았습니다! +10점"
    else:
        state.lives = max(0, state.lives - 1)
        state.message = "시간이 지나 두더지를 놓쳤습니다!"

    if state.lives == 0:
        state.game_over = True
        state.mole_hole = None
        state.message = "라이프가 모두 소진되어 게임이 끝났습니다."
        return

    other_holes = [index for index in range(9) if index != previous_hole]
    state.mole_hole = random.choice(other_holes)
    state.mole_id += 1
    state.mole_started_at = now


def handle_hole_click(hole_index, displayed_mole_id):
    state = st.session_state
    if state.game_over or displayed_mole_id != state.mole_id:
        return

    now = time.monotonic()
    if now - state.mole_started_at >= MOLE_DURATION_SECONDS:
        resolve_mole(displayed_mole_id, was_caught=False, now=now)
        return

    if hole_index == state.mole_hole:
        resolve_mole(displayed_mole_id, was_caught=True, now=now)


if "mole_hole" not in st.session_state:
    st.session_state.mole_hole = random.randrange(9)

if "score" not in st.session_state:
    st.session_state.score = 0

if "lives" not in st.session_state:
    st.session_state.lives = 3

if "mole_id" not in st.session_state:
    st.session_state.mole_id = 1

if "resolved_mole_id" not in st.session_state:
    st.session_state.resolved_mole_id = 0

if "mole_started_at" not in st.session_state:
    st.session_state.mole_started_at = time.monotonic()

if "game_over" not in st.session_state:
    st.session_state.game_over = False

if "message" not in st.session_state:
    st.session_state.message = ""

st.title("두더지 잡기 게임")
st.write("두더지를 클릭해 보세요!")

st.markdown(
    f"""
    <style>
    [class*="st-key-mole-hole-"] button,
    [class*="st-key-empty-hole-"] button {{
        aspect-ratio: 1 / 1;
        min-height: 88px;
        padding: 0;
        color: transparent;
        background-color: #eef6fb;
        background-position: center;
        background-repeat: no-repeat;
        background-size: contain;
        border: 2px solid #6aa7d1;
        border-radius: 10px;
    }}
    [class*="st-key-mole-hole-"] button {{
        background-image: url("data:image/png;base64,{MOLE_IMAGE_DATA}");
    }}
    [class*="st-key-empty-hole-"] button {{
        background-image: url("data:image/png;base64,{HOLE_IMAGE_DATA}");
    }}
    [class*="st-key-mole-hole-"] button:focus-visible,
    [class*="st-key-empty-hole-"] button:focus-visible {{
        outline: 3px solid #164f78;
        outline-offset: 2px;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

@st.fragment
def render_game():
    state = st.session_state
    now = time.monotonic()

    if (
        not state.game_over
        and now - state.mole_started_at >= MOLE_DURATION_SECONDS
    ):
        resolve_mole(state.mole_id, was_caught=False, now=now)

    if state.game_over:
        elapsed_seconds = MOLE_DURATION_SECONDS
    else:
        elapsed_seconds = min(
            max(0.0, time.monotonic() - state.mole_started_at),
            MOLE_DURATION_SECONDS,
        )
    remaining_seconds = max(0.0, MOLE_DURATION_SECONDS - elapsed_seconds)

    score_column, lives_column, time_column = st.columns(3)
    score_column.metric("현재 점수", state.score)
    lives_column.metric("라이프", state.lives)
    time_column.metric("남은 시간", f"{remaining_seconds:.1f}초")
    st.caption(f"두더지 등장 번호: {state.mole_id} · 등장 후 {elapsed_seconds:.1f}초")

    if state.message:
        if state.game_over:
            st.error(state.message)
        elif state.lives < 3:
            st.warning(state.message)
        else:
            st.success(state.message)

    if state.game_over:
        st.info("게임을 다시 시작하려면 페이지를 새로 고침하세요.")

    for row in range(3):
        columns = st.columns(3)

        for column_index, column in enumerate(columns):
            hole_index = row * 3 + column_index
            is_mole = hole_index == state.mole_hole
            key_prefix = "mole-hole" if is_mole else "empty-hole"

            with column:
                st.button(
                    f"구멍 {hole_index + 1}",
                    key=f"{key_prefix}-{hole_index}",
                    use_container_width=True,
                    disabled=state.game_over,
                    on_click=handle_hole_click,
                    args=(hole_index, state.mole_id),
                )


render_game()

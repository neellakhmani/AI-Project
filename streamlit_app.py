"""Investment Draft Game - Streamlit web version (Human vs AI, Minimax + Alpha-Beta)
Intro to AI (GTU 3171105). Run locally:  streamlit run streamlit_app.py"""
import random
from itertools import combinations

import pandas as pd
import streamlit as st

PICKS, RISK_W, DIV_BONUS = 3, 0.5, 3  # picks per player, risk penalty, bonus per distinct sector
BASE = [("HDFC Bank", "Banking", 13, 14), ("ICICI Bank", "Banking", 15, 16),
        ("TCS", "IT", 12, 10), ("Infosys", "IT", 14, 13),
        ("Gold ETF", "Commodity", 9, 6), ("Nifty 50 ETF", "Index", 11, 8),
        ("Govt Bond Fund", "Debt", 7, 2), ("Reliance", "Energy", 13, 15),
        ("Sun Pharma", "Pharma", 16, 20), ("Small Cap Fund", "Equity", 20, 28)]
DEPTH = {"Easy (1 move ahead)": 1, "Medium (3 moves ahead)": 3, "Hard (full search)": 6}


def score(team, A):
    """Heuristic evaluation: return - risk penalty + diversification bonus."""
    return sum(A[i][2] - RISK_W * A[i][3] for i in team) + DIV_BONUS * len({A[i][1] for i in team})


def minimax(ai, you, pool, depth, ab, alpha, beta, ai_turn, A, cnt):
    """AI maximises (AI score - your score); you minimise it. Optional alpha-beta pruning."""
    cnt[0] += 1
    if depth == 0 or not pool or (len(ai) == PICKS and len(you) == PICKS):
        return score(ai, A) - score(you, A)
    best = -1e9 if ai_turn else 1e9
    for i in pool:
        rest = [p for p in pool if p != i]
        if ai_turn:
            best = max(best, minimax(ai + (i,), you, rest, depth - 1, ab, alpha, beta, False, A, cnt))
            alpha = max(alpha, best)
        else:
            best = min(best, minimax(ai, you + (i,), rest, depth - 1, ab, alpha, beta, True, A, cnt))
            beta = min(beta, best)
        if ab and beta <= alpha:
            break  # prune remaining branches
    return best


def ai_move(ai, you, pool, depth, A):
    """Best asset for the AI; runs plain minimax and alpha-beta to compare nodes searched."""
    stats = {}
    for ab in (False, True):
        cnt, best, best_val = [0], None, -1e9
        for i in pool:
            v = minimax(ai + (i,), you, [p for p in pool if p != i], depth - 1, ab, best_val, 1e9, False, A, cnt)
            if v > best_val:
                best, best_val = i, v
        stats[ab] = cnt[0]
    return best, stats


def new_game():
    st.session_state.update(A=[(n, s, r + random.randint(-2, 2), k) for n, s, r, k in BASE],
                            you=(), ai=(), log=[])


def pick(i, depth):
    """Your pick, then the AI replies immediately."""
    S = st.session_state
    S.you += (i,)
    pool = [p for p in range(len(S.A)) if p not in S.you + S.ai]
    j, stats = ai_move(S.ai, S.you, pool, depth, S.A)
    S.ai += (j,)
    S.log.append({"Move": f"{len(S.ai)}. {S.A[j][0]}", "Minimax": stats[False], "Alpha-Beta": stats[True]})


st.set_page_config(page_title="Investment Draft Game", page_icon="📈")
if "A" not in st.session_state:
    new_game()
S = st.session_state
A = S.A

st.title("📈 Investment Draft Game")
st.caption(f"Take turns drafting {PICKS} assets each. Every pick leaves the pool, so you compete for the best ones.")
level = st.sidebar.selectbox("Difficulty", list(DEPTH), index=1)
if st.sidebar.button("New game", key="new"):
    new_game()
    st.rerun()
with st.expander("How scoring works"):
    st.write(f"Each asset scores **return - {RISK_W} x risk**. A portfolio gets **+{DIV_BONUS} per distinct sector**, "
             "so two banks are worth less than a bank plus a bond. The AI uses minimax with alpha-beta pruning "
             "to look ahead at your best replies.")

c1, c2 = st.columns(2)
for col, title, team in ((c1, "You", S.you), (c2, "AI", S.ai)):
    col.subheader(title)
    col.write(", ".join(A[i][0] for i in team) or "-")
    col.metric("Portfolio score", f"{score(team, A):.1f}")

if len(S.ai) < PICKS:
    st.subheader(f"Your pick ({len(S.you) + 1}/{PICKS})")
    for i in (p for p in range(len(A)) if p not in S.you + S.ai):
        n, s, r, k = A[i]
        c = st.columns([3, 2, 2, 2, 2])
        c[0].write(f"**{n}**")
        c[1].write(s)
        c[2].write(f"Return {r}%")
        c[3].write(f"Risk {k}%")
        c[4].button("Pick", key=f"pick{i}", on_click=pick, args=(i, DEPTH[level]))
else:
    y, a = score(S.you, A), score(S.ai, A)
    if y > a:
        st.success("You win! 🎉")
    elif a > y:
        st.error("AI wins 🤖")
    else:
        st.info("Draw")
    best = max(combinations(range(len(A)), PICKS), key=lambda t: score(t, A))
    st.write(f"**Best possible portfolio (brute force):** {', '.join(A[i][0] for i in best)} "
             f"(score {score(best, A):.1f})")

if S.log:
    st.subheader("Nodes searched: Minimax vs Alpha-Beta")
    df = pd.DataFrame(S.log).set_index("Move")
    st.bar_chart(df)
    st.dataframe(df)

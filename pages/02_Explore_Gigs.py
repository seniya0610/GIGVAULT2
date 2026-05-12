import datetime

import streamlit as st

from components.auth_guard import require_musician
from components.sidebar import render_sidebar
from config import MUSIC_GENRES_FILTER
from database import get_db
from queries.gig_queries import get_open_gigs_filtered
from services.application_service import apply_to_gig
from utils import empty_state, format_currency, format_date, format_time, status_badge_html

st.set_page_config(
    page_title="Explore Gigs — GigVault",
    page_icon="🔍",
    layout="wide",
)

require_musician()
render_sidebar()

musician_id = st.session_state["user_id"]

st.markdown('<div class="page-title">🔍 Explore Gigs</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="page-subtitle">Browse open gig listings and apply to perform.</div>',
    unsafe_allow_html=True,
)

with st.expander("🎛 Filter Gigs", expanded=True):
    fc1, fc2, fc3, fc4, fc5 = st.columns([2, 2, 2, 1.5, 1.5])
    sel_genre = fc1.selectbox("Genre", MUSIC_GENRES_FILTER, key="ex_genre")
    sel_city = fc2.text_input("City", placeholder="e.g. New York", key="ex_city")
    sel_date = fc3.date_input("Performance Date", value=None, key="ex_date", min_value=datetime.date.today())
    sel_min_budget = fc4.number_input("Min Budget ($)", min_value=0, value=0, step=50, key="ex_min")
    sel_max_budget = fc5.number_input("Max Budget ($)", min_value=0, value=0, step=50, key="ex_max")

    col_search, col_reset = st.columns([1, 5])
    search_clicked = col_search.button("Search", type="primary", key="ex_search")
    if col_reset.button("Reset Filters", key="ex_reset"):
        for k in ["ex_genre", "ex_city", "ex_date", "ex_min", "ex_max"]:
            if k in st.session_state:
                del st.session_state[k]
        st.rerun()

with get_db() as db:
    gigs = get_open_gigs_filtered(
        db=db,
        genre=sel_genre if sel_genre != "All" else None,
        city=sel_city or None,
        date=sel_date if isinstance(sel_date, datetime.date) else None,
        min_budget=float(sel_min_budget) if sel_min_budget > 0 else None,
        max_budget=float(sel_max_budget) if sel_max_budget > 0 else None,
        musician_id=musician_id,
    )

st.markdown(f"<br>**{len(gigs)} gig{'s' if len(gigs) != 1 else ''} found**", unsafe_allow_html=True)
st.markdown("---")

if not gigs:
    st.markdown(
        empty_state("No open gigs match your filters. Try broadening your search!", "🎶"),
        unsafe_allow_html=True,
    )
else:
    for gig in gigs:
        genre_tag = (
            f'<span style="background:#1e1b4b;color:#a78bfa;padding:2px 10px;'
            f'border-radius:20px;font-size:11px;font-weight:600;">{gig.genre}</span>'
        )
        city_tag = (
            f'<span style="background:#0c4a6e;color:#7dd3fc;padding:2px 10px;'
            f'border-radius:20px;font-size:11px;font-weight:600;">📍 {gig.city}</span>'
        )
        venue_name = ""
        if gig.client and gig.client.client_profile:
            venue_name = gig.client.client_profile.venue_name

        days = (gig.performance_date - datetime.date.today()).days
        urgency = ""
        if days <= 7:
            urgency = f'<span style="background:#7f1d1d;color:#fca5a5;padding:2px 8px;border-radius:20px;font-size:11px;">🔥 {days}d away</span>'
        elif days <= 14:
            urgency = f'<span style="background:#78350f;color:#fde68a;padding:2px 8px;border-radius:20px;font-size:11px;">⏰ {days}d away</span>'

        with st.expander(
            f"🎵 {gig.title}  ·  {format_date(gig.performance_date)}  ·  {format_currency(gig.budget)}",
            expanded=False,
        ):
            col_info, col_action = st.columns([3, 1])

            with col_info:
                st.markdown(
                    f'<div style="margin-bottom:0.5rem;">{genre_tag} {city_tag} {urgency}</div>',
                    unsafe_allow_html=True,
                )
                if venue_name:
                    st.markdown(f"🏛 **Venue:** {venue_name}")
                st.markdown(f"📅 **Date:** {format_date(gig.performance_date)}")
                if gig.start_time:
                    time_str = format_time(gig.start_time)
                    if gig.end_time:
                        time_str += f" – {format_time(gig.end_time)}"
                    st.markdown(f"⏰ **Time:** {time_str}")
                if gig.duration_hours:
                    st.markdown(f"⌛ **Duration:** {gig.duration_hours} hours")
                st.markdown(f'💵 **Budget:** <span style="color:#a78bfa;font-weight:700;">{format_currency(gig.budget)}</span>', unsafe_allow_html=True)
                if gig.description:
                    st.markdown(f"📝 **Description:** {gig.description}")
                if gig.requirements:
                    st.markdown(f"✅ **Requirements:** {gig.requirements}")

            with col_action:
                st.markdown("<br>", unsafe_allow_html=True)
                with st.form(f"apply_form_{gig.id}"):
                    st.markdown("**Apply to this Gig**")
                    prop_rate = st.number_input(
                        "Your Rate ($)",
                        min_value=0.0,
                        value=float(gig.budget),
                        step=50.0,
                        key=f"rate_{gig.id}",
                    )
                    msg = st.text_area(
                        "Cover Message",
                        placeholder="Tell the venue about yourself and why you're a great fit...",
                        height=100,
                        key=f"msg_{gig.id}",
                    )
                    apply_btn = st.form_submit_button("📩 Apply Now", type="primary", use_container_width=True)

                    if apply_btn:
                        try:
                            apply_to_gig(
                                musician_id=musician_id,
                                gig_id=gig.id,
                                message=msg,
                                proposed_rate=prop_rate if prop_rate > 0 else None,
                            )
                            st.success("✅ Application submitted successfully!")
                            st.rerun()
                        except ValueError as e:
                            st.error(str(e))
                        except Exception:
                            st.error("Something went wrong. Please try again.")

        st.markdown("<br>", unsafe_allow_html=True)

import datetime

import streamlit as st

from components.auth_guard import require_venue_owner
from components.sidebar import render_sidebar
from config import MUSIC_GENRES_SELECT
from services.gig_service import (
    cancel_gig,
    complete_gig,
    create_gig,
    get_venue_owner_gigs,
    update_gig,
)
from utils import empty_state, format_currency, format_date, format_time, status_badge_html

st.set_page_config(
    page_title="My Gigs — GigVault",
    page_icon="🎸",
    layout="wide",
)

require_venue_owner()
render_sidebar()

venue_owner_id = st.session_state["user_id"]

st.markdown('<div class="page-title">🎸 My Gigs</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="page-subtitle">Create, manage and track all your venue gig listings.</div>',
    unsafe_allow_html=True,
)

tab_list, tab_create = st.tabs(["  📋  My Listings  ", "  ➕  Create New Gig  "])

with tab_create:
    st.markdown("<br>", unsafe_allow_html=True)
    with st.form("create_gig_form", clear_on_submit=True):
        st.markdown('<div class="section-header">New Gig Details</div>', unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        title = c1.text_input("Gig Title *", placeholder="e.g. Jazz Night at The Blue Note")
        genre = c2.selectbox("Genre *", MUSIC_GENRES_SELECT)

        c3, c4 = st.columns(2)
        city = c3.text_input("City *", placeholder="e.g. New York")
        perf_date = c4.date_input(
            "Performance Date *",
            min_value=datetime.date.today() + datetime.timedelta(days=1),
        )

        c5, c6 = st.columns(2)
        start_t = c5.time_input("Performance Time", value=datetime.time(20, 0))
        duration = c6.number_input("Duration (hours)", min_value=0.5, max_value=12.0, value=3.0, step=0.5)

        offered_pay = st.number_input("Offered Pay ($) *", min_value=50.0, value=500.0, step=50.0)
        description = st.text_area("Description", placeholder="Describe the gig, audience, venue vibe...", height=100)

        submitted = st.form_submit_button("🚀 Publish Gig Listing", type="primary", use_container_width=True)

        if submitted:
            if not title or not city:
                st.error("Title and city are required.")
            elif offered_pay < 50:
                st.error("Minimum offered pay is $50.")
            else:
                try:
                    gig = create_gig(
                        venue_owner_id=venue_owner_id,
                        gig_title=title if title else "",
                        description=description if description else "",
                        genre_required=genre if genre else "",
                        location_city=city if city else "",
                        performance_date=perf_date,
                        performance_time=start_t,
                        duration_hours=duration,
                        offered_pay=offered_pay if offered_pay else 0.0,
                    )
                    st.success(f"✅ Gig **{gig.gig_title}** published successfully for {format_date(gig.performance_date)}!")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))
                except Exception as err:
                    st.error(f"Failed to create gig: {err}")

with tab_list:
    gigs = get_venue_owner_gigs(venue_owner_id)

    if not gigs:
        st.markdown(empty_state("You haven't created any gigs yet. Use the 'Create New Gig' tab to get started!", "🎸"), unsafe_allow_html=True)
    else:
        filter_status = st.selectbox(
            "Filter by Status",
            ["All", "Open", "Filled", "Completed", "Cancelled"],
            key="mg_filter",
        )
        filtered = gigs if filter_status == "All" else [g for g in gigs if (g.gig_status.value if hasattr(g.gig_status, "value") else g.gig_status) == filter_status]

        st.markdown(f"**{len(filtered)} gig{'s' if len(filtered) != 1 else ''}**")
        st.markdown("---")

        for gig in filtered:
            status_val = gig.gig_status.value if hasattr(gig.gig_status, "value") else gig.gig_status

            with st.expander(
                f"{gig.gig_title}  ·  {format_date(gig.performance_date)}  ·  {format_currency(gig.offered_pay)}",
                expanded=False,
            ):
                col_det, col_act = st.columns([3, 1])

                with col_det:
                    st.markdown(
                        f'<div style="margin-bottom:0.5rem;">{status_badge_html(status_val)}</div>',
                        unsafe_allow_html=True,
                    )
                    st.markdown(f"**Genre:** {gig.genre_required}  &nbsp;&nbsp; **City:** {gig.location_city}")
                    st.markdown(f"**Date:** {format_date(gig.performance_date)}")
                    if gig.performance_time:
                        st.markdown(f"**Time:** {format_time(gig.performance_time)}")
                    st.markdown(f"**Offered Pay:** {format_currency(gig.offered_pay)}")
                    if gig.description:
                        st.markdown(f"**Description:** {gig.description}")

                    if gig.bookings:
                        b = gig.bookings[0]
                        band_name = b.band.band_name if b.band else "Unknown"
                        st.markdown("---")
                        st.markdown(f"🎤 **Booked Band:** {band_name}")
                        booking_status = b.contract_status.value if hasattr(b.contract_status, "value") else b.contract_status
                        st.markdown(
                            f"📄 **Contract Status:** {status_badge_html(booking_status)}",
                            unsafe_allow_html=True,
                        )
                        st.markdown(f"💵 **Agreed Fee:** {format_currency(b.agreed_fee)}")

                with col_act:
                    st.markdown("<br>", unsafe_allow_html=True)

                    if status_val == "Open":
                        with st.expander("✏️ Edit Gig"):
                            with st.form(f"edit_form_{gig.gig_id}"):
                                new_title = st.text_input("Gig Title", value=gig.gig_title, key=f"et_{gig.gig_id}")
                                new_genre = st.selectbox(
                                    "Genre",
                                    MUSIC_GENRES_SELECT,
                                    index=MUSIC_GENRES_SELECT.index(gig.genre_required) if gig.genre_required in MUSIC_GENRES_SELECT else 0,
                                    key=f"eg_{gig.gig_id}",
                                )
                                new_city = st.text_input("City", value=gig.location_city, key=f"ec_{gig.gig_id}")
                                new_offered_pay = st.number_input(
                                    "Offered Pay ($)", min_value=50.0, value=float(gig.offered_pay), step=50.0, key=f"eb_{gig.gig_id}"
                                )
                                new_desc = st.text_area("Description", value=gig.description or "", key=f"ed_{gig.gig_id}")
                                save = st.form_submit_button("💾 Save Changes", use_container_width=True)
                                if save:
                                    try:
                                        update_gig(
                                            gig_id=gig.gig_id,
                                            venue_owner_id=venue_owner_id,
                                            gig_title=new_title if new_title else "",
                                            description=new_desc if new_desc else "",
                                            genre_required=new_genre if new_genre else "",
                                            location_city=new_city if new_city else "",
                                            performance_time=gig.performance_time,
                                            duration_hours=float(gig.duration_hours) if gig.duration_hours else None,
                                            offered_pay=new_offered_pay if new_offered_pay else 0.0,
                                        )
                                        st.success("Gig updated!")
                                        st.rerun()
                                    except ValueError as ve:
                                        st.error(str(ve))

                        if st.button("❌ Cancel Gig", key=f"cancel_{gig.gig_id}", use_container_width=True):
                            try:
                                cancel_gig(gig_id=gig.gig_id, venue_owner_id=venue_owner_id)
                                st.success("Gig cancelled.")
                                st.rerun()
                            except ValueError as ve:
                                st.error(str(ve))

                    elif status_val == "Filled":
                        if st.button("✅ Mark Completed", key=f"comp_{gig.gig_id}", use_container_width=True, type="primary"):
                            try:
                                complete_gig(gig_id=gig.gig_id, venue_owner_id=venue_owner_id)
                                st.success("Gig marked as completed!")
                                st.rerun()
                            except ValueError as ve:
                                st.error(str(ve))
                    else:
                        st.markdown(
                            f'<div style="color:#64748b;font-size:0.9rem;text-align:center;padding:0.5rem;">'
                            f"No actions available for {status_val} gigs.</div>",
                            unsafe_allow_html=True,
                        )

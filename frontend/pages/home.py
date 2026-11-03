import streamlit as st  # pyright: ignore[reportMissingImports]
from html import escape

def metric_card(icon, label, value):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-icon">{icon}</div>
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_dashboard(tasks, total_tasks, completed_tasks, pending_tasks, completion_rate):
    st.markdown(
        '<div class="section-title">📊 Overview</div>',
        unsafe_allow_html=True,
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        metric_card("📋", "Total Tasks", total_tasks)

    with col2:
        metric_card("✅", "Completed", completed_tasks)

    with col3:
        metric_card("⏳", "Pending", pending_tasks)

    with col4:
        metric_card("🎯", "Completion Rate", f"{completion_rate}%")

    st.write("")

    left, right = st.columns([1.3, 1])

    with left:
        st.markdown(
            '<div class="section-title">🚀 Recent Tasks</div>',
            unsafe_allow_html=True,
        )

        if not tasks:
            st.info("No tasks yet. Create your first task!")

        # Sort by database ID and assign display numbers 1, 2, 3...
        recent_tasks = sorted(
            tasks,
            key=lambda item: item["id"],
        )

        for display_number, task in enumerate(
            recent_tasks[-5:],
            start=max(1, len(recent_tasks) - 4),
        ):

            status_class = (
                "status-done"
                if task["completed"]
                else "status-open"
            )

            status_text = (
                "✓ Completed"
                if task["completed"]
                else "◷ Pending"
            )

            # Escape user-provided content before inserting it into HTML.
            safe_title = escape(str(task.get("title") or ""))
            safe_description = escape(
                str(task.get("description") or "No description provided.")
            )

            st.markdown(
                f"""
                <div class="task-card">
                    <div style="
                        display:flex;
                        justify-content:space-between;
                        gap:12px;
                        align-items:center;
                        flex-wrap:wrap;
                    ">
                        <div class="task-title">
                            #{display_number} · {safe_title}
                        </div>
                        <span class="{status_class}">
                            {status_text}
                        </span>
                    </div>
                    <div class="task-description">
                        {safe_description}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with right:
        st.markdown(
            '<div class="section-title">🎯 Your Progress</div>',
            unsafe_allow_html=True,
        )

        st.markdown('<div class="panel">', unsafe_allow_html=True)

        st.markdown("### Completion Progress")

        st.progress(completion_rate / 100)

        st.markdown(
            f"""
            <h2 style="color:#4f46e5; margin-bottom:0;">
                {completion_rate}%
            </h2>
            <p style="color:#6b7280; font-size:13px;">
                {completed_tasks} of {total_tasks} tasks completed
            </p>
            """,
            unsafe_allow_html=True,
        )

        st.divider()

        st.markdown("#### Quick Summary")

        st.write(f"📋 Total tasks: **{total_tasks}**")
        st.write(f"✅ Completed: **{completed_tasks}**")
        st.write(f"⏳ Remaining: **{pending_tasks}**")

        st.markdown("</div>", unsafe_allow_html=True)

    if st.button("🔄 Refresh Dashboard", type="primary"):
        st.rerun()

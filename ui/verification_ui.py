"""
BMR OCR Verification UI
Streamlit application for human review of extracted data.
"""

import sys
from pathlib import Path

# Add project root BEFORE any app imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
from PIL import Image
from sqlalchemy import select
from sqlalchemy.orm import joinedload, Session as SASession
from app.engines.storage import StorageEngine
from app.models.domain import Page, Field, VerificationStatus


# --- DB ---


@st.cache_resource
def _storage():
    return StorageEngine()


def _session() -> SASession:
    s = _storage().get_session()
    s.expire_all()
    return s


# --- UI ---

st.set_page_config(layout="wide", page_title="BMR OCR Verification")
st.title("🔍 BMR OCR Verification Tool")

session = _session()

# Load page list (eager-load document)
all_pages = (
    session.scalars(
        select(Page)
        .options(joinedload(Page.document))
        .order_by(Page.document_id, Page.page_number)
    )
    .unique()
    .all()
)

if not all_pages:
    st.warning("No pages in DB. Run the pipeline first.")
    st.stop()

# Build sidebar options
labels = [
    f"{p.document.filename} — P{p.page_number} ({p.page_type or '?'})"
    for p in all_pages
]
ids = [p.id for p in all_pages]


# Callback: when selectbox changes, clear old field keys
def _on_page_change():
    # Remove all keys that start with "f_" (old field inputs)
    keys_to_remove = [k for k in st.session_state if k.startswith("f_")]
    for k in keys_to_remove:
        del st.session_state[k]


st.sidebar.header("📄 Select Page")
idx = st.sidebar.selectbox(
    "Choose a page",
    range(len(labels)),
    format_func=lambda i: labels[i],
    key="page_selector",
    on_change=_on_page_change,
)

selected_id = ids[idx]

# Load selected page with fields (eager)
page = (
    session.scalars(
        select(Page).options(joinedload(Page.fields)).where(Page.id == selected_id)
    )
    .unique()
    .first()
)

# --- Layout ---
col_img, col_fields = st.columns([1, 1])

with col_img:
    st.subheader(f"Page {page.page_number} — {page.page_type or '?'}")
    img_path = Path(page.image_path)
    if img_path.exists():
        st.image(Image.open(img_path), use_container_width=True)
    else:
        st.error(f"Image not found: `{img_path}`")

    md_path = img_path.with_suffix(".md")
    if md_path.exists():
        with st.expander("📝 Raw OCR Markdown"):
            st.code(md_path.read_text(encoding="utf-8"), language="markdown")

with col_fields:
    st.subheader("Extracted Fields")
    fields = sorted(page.fields, key=lambda f: f.name)

    if not fields:
        st.info("No fields extracted for this page.")
    else:
        # Use page-specific form key so Streamlit doesn't reuse old form state
        with st.form(f"verify_{selected_id}"):
            updated = {}
            for field in fields:
                icon = "🟢" if field.status == VerificationStatus.VERIFIED else "🔴"
                current = (
                    field.verified_value
                    if field.verified_value is not None
                    else (field.ocr_value or "")
                )
                val = st.text_input(
                    f"{icon} {field.name}",
                    value=current,
                    key=f"f_{field.id}",
                )
                updated[field.id] = val

            if st.form_submit_button("✅ Save & Verify"):
                for fid, val in updated.items():
                    f = session.get(Field, fid)
                    if f:
                        f.verified_value = val
                        f.verified_by = "human_reviewer"
                        f.status = VerificationStatus.VERIFIED
                session.commit()
                st.success("Page verified!")
                st.rerun()

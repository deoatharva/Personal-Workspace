import os
import base64

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from app.auth_gate import require_unlock
from app.ui.styles import inject_css

from app.services.security import (
    derive_key,
    encrypt_text,
    decrypt_text,
    generate_password,
)

from app.services.notes import (
    list_notes,
    create_note,
    update_note,
    delete_note,
    list_todos,
    replace_todos,
    toggle_todo,
)

from app.services.files import (
    upload_file,
    download_file,
    delete_file,
    list_files,
    usage,
)

from app.services.passwords import (
    list_passwords,
    create_password,
    delete_password,
)


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Personal Notes",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()


# ============================================================
# AUTHENTICATION
# ============================================================

if not require_unlock():
    st.stop()


# ============================================================
# VAULT KEY
# ============================================================

password_salt = os.getenv("APP_PASSWORD_SALT")

if not password_salt:
    st.error("APP_PASSWORD_SALT is not configured.")
    st.stop()


if "vault_key" not in st.session_state:

    try:
        salt = base64.urlsafe_b64decode(
            password_salt.encode()
        )

        st.session_state.vault_key = derive_key(
            st.session_state.master_password,
            salt,
        )

    except Exception as e:
        st.error(f"Unable to initialize encrypted vault: {e}")
        st.stop()


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def fb(value):
    """
    Format bytes into human-readable size.
    """

    units = ["B", "KB", "MB", "GB", "TB"]

    try:
        x = float(value)
    except (TypeError, ValueError):
        return "0 B"

    for unit in units:

        if x < 1024 or unit == "TB":

            if unit == "B":
                return f"{int(x)} B"

            return f"{x:.1f} {unit}"

        x /= 1024

    return "0 B"


def pct(used, total):
    """
    Return percentage between 0 and 100.
    """

    if not total:
        return 0

    return min(
        100,
        max(
            0,
            (used / total) * 100,
        ),
    )


def note_label(note):
    prefix = "⭐ " if note.get("is_starred") else ""

    note_type = (
        " • Todo"
        if note.get("note_type") == "todo"
        else ""
    )

    return f"{prefix}{note.get('title', 'Untitled')}{note_type}"


def file_icon(mime_type, filename):
    """
    Pick a simple icon based on file type.
    """

    mime_type = mime_type or ""
    filename = filename.lower()

    if mime_type.startswith("image/"):
        return "🖼️"

    if mime_type == "application/pdf":
        return "📕"

    if filename.endswith(
        (
            ".doc",
            ".docx",
        )
    ):
        return "📘"

    if filename.endswith(
        (
            ".xls",
            ".xlsx",
            ".csv",
        )
    ):
        return "📊"

    if filename.endswith(
        (
            ".ppt",
            ".pptx",
        )
    ):
        return "📙"

    if filename.endswith(
        (
            ".zip",
            ".rar",
            ".7z",
        )
    ):
        return "🗜️"

    if mime_type.startswith("text/"):
        return "📄"

    return "📎"


def preview_file(file_record):
    """
    Preview supported file types.
    """

    data = download_file(
        file_record["storage_path"]
    )

    mime = file_record.get("mime_type") or ""

    filename = (
        file_record.get("file_name") or ""
    ).lower()

    # --------------------------------------------------------
    # IMAGE
    # --------------------------------------------------------

    if mime.startswith("image/"):

        st.image(
            data,
            use_container_width=True,
        )

        return


    # --------------------------------------------------------
    # PDF
    # --------------------------------------------------------

    if mime == "application/pdf" or filename.endswith(".pdf"):

        encoded = base64.b64encode(data).decode(
            "utf-8"
        )

        st.markdown(
            f"""
            <iframe
                src="data:application/pdf;base64,{encoded}"
                width="100%"
                height="650"
                style="
                    border: 1px solid rgba(128,128,128,0.25);
                    border-radius: 12px;
                "
            ></iframe>
            """,
            unsafe_allow_html=True,
        )

        return


    # --------------------------------------------------------
    # TEXT
    # --------------------------------------------------------

    text_extensions = (
        ".txt",
        ".md",
        ".json",
        ".csv",
        ".log",
        ".xml",
        ".yaml",
        ".yml",
    )

    if (
        mime.startswith("text/")
        or filename.endswith(text_extensions)
    ):

        st.code(
            data.decode(
                "utf-8",
                errors="replace",
            ),
            language="text",
        )

        return


    # --------------------------------------------------------
    # UNSUPPORTED
    # --------------------------------------------------------

    st.info(
        "Preview is not available for this file type. "
        "Use the download button to open it with the appropriate application."
    )


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title("📝 My Workspace")

    page = st.radio(
        "Navigate",
        [
            "Dashboard",
            "Notes",
            "Todos",
            "Files",
            "Password Manager",
            "Settings",
        ],
        label_visibility="collapsed",
    )

    st.divider()

    if st.button(
        "🔒 Lock now",
        use_container_width=True,
    ):

        for key in [
            "unlocked",
            "master_password",
            "vault_key",
        ]:

            st.session_state.pop(
                key,
                None,
            )

        st.rerun()


# ============================================================
# DASHBOARD
# ============================================================

if page == "Dashboard":

    st.title("Good to see you 👋")

    # --------------------------------------------------------
    # LOAD DATA
    # --------------------------------------------------------

    notes = list_notes()
    files = list_files()
    passwords = list_passwords()

    todo_items = []

    for note in notes:

        if note.get("note_type") == "todo":

            todo_items.extend(
                list_todos(note["id"])
            )


    usage_data = usage()

    database_bytes = int(
        usage_data.get(
            "database_bytes",
            0,
        )
    )

    storage_bytes = int(
        usage_data.get(
            "storage_bytes",
            0,
        )
    )


    # --------------------------------------------------------
    # COUNTERS
    # --------------------------------------------------------

    starred_notes = sum(
        1
        for note in notes
        if note.get("is_starred")
    )

    starred_passwords = sum(
        1
        for password in passwords
        if password.get("is_starred")
    )

    total_starred = (
        starred_notes
        + starred_passwords
    )


    # --------------------------------------------------------
    # METRICS
    # --------------------------------------------------------

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "📝 Notes",
        len(notes),
    )

    c2.metric(
        "✅ Tasks",
        len(todo_items),
    )

    c3.metric(
        "📎 Files",
        len(files),
    )

    c4.metric(
        "⭐ Starred",
        total_starred,
    )


    st.divider()


    # --------------------------------------------------------
    # STORAGE
    # --------------------------------------------------------

    st.subheader("Storage")


    storage_col, database_col = st.columns(2)


    # FILE STORAGE

    with storage_col:

        storage_limit = 1024 ** 3

        storage_percent = pct(
            storage_bytes,
            storage_limit,
        )

        st.write(
            f"📎 **File storage** — "
            f"{fb(storage_bytes)} / 1.0 GB"
        )

        st.progress(
            storage_percent / 100
        )

        st.caption(
            f"{storage_percent:.1f}% used • "
            f"{fb(max(0, storage_limit - storage_bytes))} remaining"
        )


    # DATABASE

    with database_col:

        database_limit = 500 * (1024 ** 2)

        database_percent = pct(
            database_bytes,
            database_limit,
        )

        st.write(
            f"🗄️ **Database** — "
            f"{fb(database_bytes)} / 500 MB"
        )

        st.progress(
            database_percent / 100
        )

        st.caption(
            f"{database_percent:.1f}% used • "
            f"{fb(max(0, database_limit - database_bytes))} remaining"
        )


    # WARNINGS

    if storage_percent >= 85:

        st.warning(
            "⚠️ File storage is getting full."
        )

    elif storage_percent >= 70:

        st.info(
            "File storage is above 70%."
        )


    if database_percent >= 85:

        st.warning(
            "⚠️ Database usage is getting high."
        )

    elif database_percent >= 70:

        st.info(
            "Database usage is above 70%."
        )


    st.divider()


    # --------------------------------------------------------
    # IMPORTANT NOTES
    # --------------------------------------------------------

    st.subheader("⭐ Important notes")

    starred = [
        note
        for note in notes
        if note.get("is_starred")
    ]

    if not starred:

        st.caption(
            "No starred notes yet."
        )

    else:

        for note in starred[:8]:

            if st.button(
                f"⭐ {note['title']}",
                key=f"dash_{note['id']}",
                use_container_width=True,
            ):

                st.session_state.open_note = (
                    note["id"]
                )

                st.rerun()


# ============================================================
# NOTES
# ============================================================

elif page == "Notes":

    st.title("📝 Notes")


    # ========================================================
    # OPEN NOTE
    # ========================================================

    if st.session_state.get("open_note"):

        all_notes = list_notes()

        note = next(
            (
                item
                for item in all_notes
                if item["id"]
                == st.session_state.open_note
            ),
            None,
        )


        if not note:

            st.session_state.pop(
                "open_note",
                None,
            )

            st.rerun()


        # BACK BUTTON

        if st.button("← Back"):

            st.session_state.pop(
                "open_note",
                None,
            )

            st.rerun()


        # HEADER

        st.header(
            (
                "⭐ "
                if note.get("is_starred")
                else ""
            )
            + note["title"]
        )

        st.caption(
            f"{note.get('category') or 'No category'} "
            f"• Updated {note.get('updated_at', '')}"
        )


        # ----------------------------------------------------
        # EDIT NOTE
        # ----------------------------------------------------

        with st.form("edit_note"):

            title = st.text_input(
                "Title",
                note["title"],
            )

            content = st.text_area(
                "Content",
                note["content"],
                height=320,
            )

            category = st.text_input(
                "Category",
                note.get("category") or "",
            )

            tags = st.text_input(
                "Tags",
                ", ".join(
                    note.get("tags") or []
                ),
            )

            star = st.checkbox(
                "⭐ Important / starred",
                note.get("is_starred", False),
            )


            save_note = st.form_submit_button(
                "Save changes",
                type="primary",
                use_container_width=True,
            )


            if save_note:

                cleaned_tags = [
                    tag.strip()
                    for tag in tags.split(",")
                    if tag.strip()
                ]

                update_note(
                    note["id"],
                    title,
                    content,
                    category,
                    cleaned_tags,
                    star,
                )

                # Update todo lines when editing a todo note

                if note.get("note_type") == "todo":

                    todo_data = [
                        {
                            "text": line.strip(),
                            "completed": False,
                        }
                        for line in content.splitlines()
                        if line.strip()
                    ]

                    replace_todos(
                        note["id"],
                        todo_data,
                    )

                st.success(
                    "Note updated."
                )

                st.rerun()


        # ----------------------------------------------------
        # TODO CHECKLIST
        # ----------------------------------------------------

        if note.get("note_type") == "todo":

            st.subheader("✅ Checklist")

            todos = list_todos(
                note["id"]
            )

            if not todos:

                st.caption(
                    "No tasks in this todo note."
                )

            for todo in todos:

                value = st.checkbox(
                    todo["text"],
                    todo["completed"],
                    key=f"todo_{todo['id']}",
                )

                if value != todo["completed"]:

                    toggle_todo(
                        todo["id"],
                        value,
                    )

                    st.rerun()


        # ----------------------------------------------------
        # ATTACHMENTS
        # ----------------------------------------------------

        st.subheader("📎 Attachments")

        note_files = list_files(
            note["id"]
        )


        if not note_files:

            st.caption(
                "No files attached to this note."
            )


        for file_record in note_files:

            filename = file_record[
                "file_name"
            ]

            mime = (
                file_record.get(
                    "mime_type"
                )
                or ""
            )

            icon = file_icon(
                mime,
                filename,
            )

            st.markdown(
                f"### {icon} {filename}"
            )

            st.caption(
                fb(
                    file_record.get(
                        "file_size",
                        0,
                    )
                )
            )


            # Preview

            with st.expander(
                "👁 Preview",
                expanded=False,
            ):

                preview_file(
                    file_record
                )


            # Download / Delete

            data = download_file(
                file_record[
                    "storage_path"
                ]
            )

            d1, d2 = st.columns(2)

            with d1:

                st.download_button(
                    "⬇ Download",
                    data,
                    file_name=filename,
                    key=f"download_note_file_{file_record['id']}",
                    use_container_width=True,
                )

            with d2:

                if st.button(
                    "🗑 Delete",
                    key=f"delete_note_file_{file_record['id']}",
                    use_container_width=True,
                ):

                    delete_file(
                        file_record["id"],
                        file_record["storage_path"],
                    )

                    st.rerun()


        # ----------------------------------------------------
        # UPLOAD INTO NOTE
        # ----------------------------------------------------

        st.subheader(
            "📤 Attach files to this note"
        )

        uploads = st.file_uploader(
            "Drop files here or click to browse",
            accept_multiple_files=True,
            key=f"note_upload_{note['id']}",
            type=[
                "pdf",
                "doc",
                "docx",
                "xls",
                "xlsx",
                "ppt",
                "pptx",
                "txt",
                "md",
                "csv",
                "json",
                "png",
                "jpg",
                "jpeg",
                "webp",
                "gif",
                "zip",
            ],
        )


        if uploads:

            if st.button(
                "⬆ Upload selected files",
                type="primary",
                use_container_width=True,
            ):

                progress = st.progress(0)

                total = len(uploads)

                for index, uploaded in enumerate(
                    uploads,
                    start=1,
                ):

                    upload_file(
                        note["id"],
                        uploaded,
                    )

                    progress.progress(
                        index / total
                    )

                st.success(
                    f"{total} file(s) uploaded."
                )

                st.rerun()


        # ----------------------------------------------------
        # DELETE NOTE
        # ----------------------------------------------------

        st.divider()

        if st.button(
            "🗑 Delete note",
            type="secondary",
        ):

            delete_note(
                note["id"]
            )

            st.session_state.pop(
                "open_note",
                None,
            )

            st.rerun()


    # ========================================================
    # NOTE LIST
    # ========================================================

    else:

        search = st.text_input(
            "🔍 Search notes",
            placeholder="Search title, content, category or tags...",
        )

        note_type_filter = st.selectbox(
            "Type",
            [
                "All",
                "Notes",
                "Todos",
            ],
        )


        if st.button(
            "＋ New note",
            type="primary",
        ):

            st.session_state.new_note = True


        # ----------------------------------------------------
        # CREATE NOTE
        # ----------------------------------------------------

        if st.session_state.get(
            "new_note"
        ):

            with st.form("new_note_form"):

                title = st.text_input(
                    "Title"
                )

                note_type = st.selectbox(
                    "Type",
                    [
                        "note",
                        "todo",
                    ],
                )

                content = st.text_area(
                    "Content",
                    height=260,
                    help=(
                        "For Todo notes, "
                        "put one task on each line."
                    ),
                )

                category = st.text_input(
                    "Category"
                )

                tags = st.text_input(
                    "Tags",
                    placeholder="work, college, important",
                )

                starred = st.checkbox(
                    "⭐ Important / starred"
                )


                create = st.form_submit_button(
                    "Create note",
                    type="primary",
                    use_container_width=True,
                )


                if create:

                    if not title.strip():

                        st.error(
                            "Please enter a title."
                        )

                    else:

                        cleaned_tags = [
                            tag.strip()
                            for tag in tags.split(",")
                            if tag.strip()
                        ]

                        new_note = create_note(
                            title.strip(),
                            content,
                            category,
                            cleaned_tags,
                            note_type,
                            starred,
                        )


                        if note_type == "todo":

                            todo_data = [
                                {
                                    "text": line.strip(),
                                    "completed": False,
                                }
                                for line in content.splitlines()
                                if line.strip()
                            ]

                            replace_todos(
                                new_note["id"],
                                todo_data,
                            )


                        st.session_state.new_note = False

                        st.rerun()


        # ----------------------------------------------------
        # FILTER
        # ----------------------------------------------------

        if note_type_filter == "All":

            selected_type = None

        elif note_type_filter == "Todos":

            selected_type = "todo"

        else:

            selected_type = "note"


        notes = list_notes(
            search,
            selected_type,
        )


        # STARRED FIRST

        notes = sorted(
            notes,
            key=lambda item: (
                not item.get(
                    "is_starred",
                    False,
                ),
                item.get(
                    "updated_at",
                    "",
                ),
            ),
            reverse=False,
        )


        # ----------------------------------------------------
        # NOTE CARDS
        # ----------------------------------------------------

        if not notes:

            st.info(
                "No notes found."
            )


        for note in notes:

            with st.container(
                border=True
            ):

                left, right = st.columns(
                    [6, 1]
                )


                with left:

                    prefix = (
                        "⭐ "
                        if note.get(
                            "is_starred"
                        )
                        else ""
                    )

                    type_label = (
                        " • Todo"
                        if note.get(
                            "note_type"
                        )
                        == "todo"
                        else ""
                    )

                    st.markdown(
                        f"### {prefix}{note['title']}{type_label}"
                    )


                    preview = (
                        note.get(
                            "content"
                        )
                        or ""
                    ).replace(
                        "\n",
                        " ",
                    )


                    st.caption(
                        preview[:180]
                    )


                    st.caption(
                        note.get(
                            "category"
                        )
                        or "No category"
                    )


                with right:

                    if st.button(
                        "Open",
                        key=f"open_note_{note['id']}",
                        use_container_width=True,
                    ):

                        st.session_state.open_note = (
                            note["id"]
                        )

                        st.rerun()


# ============================================================
# TODOS
# ============================================================

elif page == "Todos":

    st.title("✅ Todos")


    notes = [
        note
        for note in list_notes()
        if note.get("note_type")
        == "todo"
    ]


    all_items = []

    for note in notes:

        for todo in list_todos(
            note["id"]
        ):

            all_items.append(
                (
                    note,
                    todo,
                )
            )


    total = len(all_items)

    completed = sum(
        1
        for _, todo in all_items
        if todo["completed"]
    )


    progress = (
        completed / total
        if total
        else 0
    )


    st.progress(progress)

    st.caption(
        f"{completed} of {total} completed"
    )


    if not all_items:

        st.info(
            "No todo items yet. "
            "Create a Todo note and put one task on each line."
        )


    # Starred todo notes first

    all_items.sort(
        key=lambda pair: (
            not pair[0].get(
                "is_starred",
                False,
            ),
            pair[0].get(
                "updated_at",
                "",
            ),
        )
    )


    current_note_id = None


    for note, todo in all_items:

        if note["id"] != current_note_id:

            current_note_id = note["id"]

            st.subheader(
                (
                    "⭐ "
                    if note.get("is_starred")
                    else ""
                )
                + note["title"]
            )


        value = st.checkbox(
            todo["text"],
            todo["completed"],
            key=f"global_todo_{todo['id']}",
        )


        if value != todo["completed"]:

            toggle_todo(
                todo["id"],
                value,
            )

            st.rerun()


# ============================================================
# FILES
# ============================================================

elif page == "Files":

    st.title("📎 Files")

    st.caption(
        "Upload, preview, download and manage your files."
    )


    # --------------------------------------------------------
    # STORAGE HEADER
    # --------------------------------------------------------

    usage_data = usage()

    storage_used = int(
        usage_data.get(
            "storage_bytes",
            0,
        )
    )

    storage_limit = 1024 ** 3

    storage_percent = pct(
        storage_used,
        storage_limit,
    )


    c1, c2, c3 = st.columns(3)

    c1.metric(
        "📦 Used",
        fb(storage_used),
    )

    c2.metric(
        "💾 Available",
        fb(
            max(
                0,
                storage_limit - storage_used,
            )
        ),
    )

    c3.metric(
        "📊 Usage",
        f"{storage_percent:.1f}%",
    )


    st.progress(
        storage_percent / 100
    )


    if storage_percent >= 85:

        st.error(
            "⚠️ Storage is almost full. "
            "Delete unused files before uploading more."
        )

    elif storage_percent >= 70:

        st.warning(
            "Storage usage is above 70%."
        )


    st.divider()


    # --------------------------------------------------------
    # UPLOAD AREA
    # --------------------------------------------------------

    st.subheader("📤 Upload files")

    st.caption(
        "Drag and drop one or multiple files below."
    )


    # Load notes for optional attachment

    notes = list_notes()


    note_options = {
        "📁 No note — store as standalone file": None
    }


    # Starred notes first

    sorted_notes = sorted(
        notes,
        key=lambda item: (
            not item.get(
                "is_starred",
                False,
            ),
            item.get(
                "updated_at",
                "",
            ),
        )
    )


    for note in sorted_notes:

        note_options[
            note_label(note)
        ] = note["id"]


    selected_note_label = st.selectbox(
        "Attach uploaded files to",
        list(
            note_options.keys()
        ),
        help=(
            "Files can exist independently "
            "or be attached to a note."
        ),
    )


    selected_note_id = note_options[
        selected_note_label
    ]


    uploaded_files = st.file_uploader(
        "Drop files here or click to browse",
        accept_multiple_files=True,
        type=[
            "pdf",
            "doc",
            "docx",
            "xls",
            "xlsx",
            "ppt",
            "pptx",
            "txt",
            "md",
            "csv",
            "json",
            "xml",
            "yaml",
            "yml",
            "png",
            "jpg",
            "jpeg",
            "webp",
            "gif",
            "zip",
            "rar",
            "7z",
            "log",
        ],
        help=(
            "Multiple files are supported."
        ),
    )


    if uploaded_files:

        total_upload_size = sum(
            uploaded.size
            for uploaded in uploaded_files
        )


        st.info(
            f"📦 {len(uploaded_files)} file(s) selected "
            f"• {fb(total_upload_size)}"
        )


        if (
            storage_used
            + total_upload_size
            > storage_limit
        ):

            st.error(
                "Not enough Supabase Storage space "
                "for this upload."
            )

        else:

            if st.button(
                "⬆ Upload selected files",
                type="primary",
                use_container_width=True,
            ):

                progress = st.progress(0)

                uploaded_count = 0

                errors = []


                for index, uploaded in enumerate(
                    uploaded_files,
                    start=1,
                ):

                    try:

                        upload_file(
                            selected_note_id,
                            uploaded,
                        )

                        uploaded_count += 1

                    except Exception as error:

                        errors.append(
                            f"{uploaded.name}: {error}"
                        )


                    progress.progress(
                        index
                        / len(uploaded_files)
                    )


                if uploaded_count:

                    st.success(
                        f"✅ {uploaded_count} file(s) uploaded successfully."
                    )


                if errors:

                    for error in errors:

                        st.error(
                            f"❌ {error}"
                        )


                if uploaded_count:

                    st.rerun()


    st.divider()


    # --------------------------------------------------------
    # FILE SEARCH
    # --------------------------------------------------------

    st.subheader("📁 Your files")


    file_search = st.text_input(
        "🔍 Search files",
        placeholder="Search by filename...",
    )


    files = list_files()


    if file_search:

        query = file_search.lower().strip()

        files = [
            file
            for file in files
            if query
            in file.get(
                "file_name",
                "",
            ).lower()
        ]


    if not files:

        st.info(
            "No files found. "
            "Use the upload area above to add your first file."
        )


    # --------------------------------------------------------
    # FILE LIST
    # --------------------------------------------------------

    for file_record in files:

        filename = file_record[
            "file_name"
        ]

        mime = (
            file_record.get(
                "mime_type"
            )
            or ""
        )

        icon = file_icon(
            mime,
            filename,
        )


        with st.container(
            border=True
        ):

            c1, c2 = st.columns(
                [6, 1]
            )


            with c1:

                st.markdown(
                    f"### {icon} {filename}"
                )

                st.caption(
                    f"{fb(file_record.get('file_size', 0))}"
                    f" • {mime or 'Unknown type'}"
                )


                # Find attached note

                attached_note = None

                note_id = file_record.get(
                    "note_id"
                )


                if note_id:

                    attached_note = next(
                        (
                            note
                            for note in notes
                            if note["id"]
                            == note_id
                        ),
                        None,
                    )


                if attached_note:

                    st.caption(
                        "📝 Attached to: "
                        + (
                            "⭐ "
                            if attached_note.get(
                                "is_starred"
                            )
                            else ""
                        )
                        + attached_note["title"]
                    )

                else:

                    st.caption(
                        "📁 Standalone file"
                    )


            with c2:

                data = download_file(
                    file_record[
                        "storage_path"
                    ]
                )


                st.download_button(
                    "⬇️ Download",
                    data,
                    file_name=filename,
                    key=f"file_download_{file_record['id']}",
                    use_container_width=True,
                )


                if st.button(
                    "🗑️ Delete",
                    key=f"file_delete_{file_record['id']}",
                    use_container_width=True,
                ):

                    delete_file(
                        file_record["id"],
                        file_record["storage_path"],
                    )

                    st.success(
                        "File deleted."
                    )

                    st.rerun()


            # Preview

            with st.expander(
                "👁 Preview",
                expanded=False,
            ):

                preview_file(
                    file_record
                )


# ============================================================
# PASSWORD MANAGER
# ============================================================

elif page == "Password Manager":

    st.title("🔐 Password Manager")

    st.warning(
        "Vault secrets are encrypted with AES-256-GCM "
        "using a key derived from your master password. "
        "If you lose the master password, encrypted "
        "vault data cannot be recovered."
    )


    search = st.text_input(
        "🔍 Search vault",
        placeholder="Search website, username or category...",
    )


    if st.button(
        "＋ New password",
        type="primary",
    ):

        st.session_state.new_password = True


    # --------------------------------------------------------
    # CREATE PASSWORD
    # --------------------------------------------------------

    if st.session_state.get(
        "new_password"
    ):

        with st.form(
            "password_form"
        ):

            name = st.text_input(
                "Name",
                placeholder="Google, GitHub, College Portal...",
            )

            username = st.text_input(
                "Username / Email"
            )

            password = st.text_input(
                "Password",
                type="password",
            )

            url = st.text_input(
                "URL"
            )

            category = st.text_input(
                "Category"
            )

            private_notes = st.text_area(
                "Private notes"
            )

            starred = st.checkbox(
                "⭐ Important / starred"
            )


            save_password = st.form_submit_button(
                "🔐 Generate / Save password",
                type="primary",
                use_container_width=True,
            )


            if save_password:

                if not name.strip():

                    st.error(
                        "Name is required."
                    )

                else:

                    generated = False


                    if not password:

                        password = generate_password()

                        generated = True


                    key = (
                        st.session_state.vault_key
                    )


                    encrypted_password = encrypt_text(
                        password,
                        key,
                    )


                    encrypted_notes = (
                        encrypt_text(
                            private_notes,
                            key,
                        )
                        if private_notes
                        else None
                    )


                    create_password(
                        {
                            "name": name.strip(),
                            "username": username.strip(),
                            "encrypted_password": encrypted_password,
                            "url": url.strip(),
                            "encrypted_notes": encrypted_notes,
                            "category": category.strip(),
                            "is_starred": starred,
                        }
                    )


                    if generated:

                        st.success(
                            "Secure password generated and saved."
                        )

                    else:

                        st.success(
                            "Password saved securely."
                        )


                    st.session_state.new_password = False

                    st.rerun()


    # --------------------------------------------------------
    # PASSWORD LIST
    # --------------------------------------------------------

    passwords = list_passwords(
        search
    )


    # Starred first

    passwords = sorted(
        passwords,
        key=lambda item: (
            not item.get(
                "is_starred",
                False,
            ),
            item.get(
                "updated_at",
                "",
            ),
        )
    )


    if not passwords:

        st.info(
            "No password entries found."
        )


    for password_entry in passwords:

        with st.container(
            border=True
        ):

            title = (
                "⭐ "
                if password_entry.get(
                    "is_starred"
                )
                else ""
            ) + password_entry["name"]


            st.subheader(
                title
            )


            key = (
                st.session_state.vault_key
            )


            try:

                plain_password = decrypt_text(
                    password_entry[
                        "encrypted_password"
                    ],
                    key,
                )


                private_notes = ""


                if password_entry.get(
                    "encrypted_notes"
                ):

                    private_notes = decrypt_text(
                        password_entry[
                            "encrypted_notes"
                        ],
                        key,
                    )


            except Exception:

                st.error(
                    "Unable to decrypt this password entry."
                )

                continue


            st.write(
                "**Username:** "
                + (
                    password_entry.get(
                        "username"
                    )
                    or "—"
                )
            )


            st.write(
                "**Category:** "
                + (
                    password_entry.get(
                        "category"
                    )
                    or "—"
                )
            )


            if password_entry.get(
                "url"
            ):

                st.write(
                    "**URL:** "
                    + password_entry["url"]
                )


            st.code(
                plain_password,
                language="text",
            )


            if private_notes:

                st.caption(
                    "🔒 Private note: "
                    + private_notes
                )


            if st.button(
                "🗑 Delete",
                key=f"password_delete_{password_entry['id']}",
            ):

                delete_password(
                    password_entry["id"]
                )

                st.rerun()


# ============================================================
# SETTINGS
# ============================================================

elif page == "Settings":

    st.title("⚙ Settings")


    st.subheader(
        "🔐 Security"
    )

    st.info(
        "Application lock uses Argon2id. "
        "Password-manager secrets use AES-256-GCM "
        "with a password-derived encryption key."
    )


    st.subheader(
        "☁️ Storage"
    )

    st.write(
        "📎 File storage limit shown: **1 GB**"
    )

    st.write(
        "🗄️ Database limit shown: **500 MB**"
    )

    st.caption(
        "Verify your current Supabase plan if these quotas change."
    )


    st.subheader(
        "📱 Application"
    )

    st.write(
        "This application is designed to work "
        "on desktop and mobile browsers."
    )


    st.subheader(
        "🔒 Session"
    )

    st.write(
        "The application is protected by your "
        "master password."
    )


    if st.button(
        "🔒 Lock application",
        type="primary",
        use_container_width=True,
    ):

        for key in [
            "unlocked",
            "master_password",
            "vault_key",
            "open_note",
        ]:

            st.session_state.pop(
                key,
                None,
            )

        st.rerun()
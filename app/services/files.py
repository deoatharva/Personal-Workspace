from .supabase_client import get_supabase


BUCKET = "notes-files"


def upload_file(note_id, uploaded):
    sb = get_supabase()

    path = f"{note_id}/{uploaded.name}"

    file_data = uploaded.getvalue()

    sb.storage.from_(BUCKET).upload(
        path,
        file_data,
        {
            "content-type": uploaded.type or "application/octet-stream",
            "upsert": "false",
        },
    )

    result = (
        sb.table("note_files")
        .insert({
            "note_id": note_id,
            "file_name": uploaded.name,
            "storage_path": path,
            "mime_type": uploaded.type,
            "file_size": len(file_data),
        })
        .execute()
    )

    return result.data[0]


def download_file(path):
    sb = get_supabase()

    return sb.storage.from_(BUCKET).download(path)


def delete_file(file_id, path):
    sb = get_supabase()

    # Delete the actual file from Supabase Storage
    sb.storage.from_(BUCKET).remove([path])

    # Delete the database record
    (
        sb.table("note_files")
        .delete()
        .eq("id", file_id)
        .execute()
    )


def list_files(note_id=None):
    sb = get_supabase()

    query = (
        sb.table("note_files")
        .select("*")
        .order("created_at", desc=True)
    )

    if note_id:
        query = query.eq("note_id", note_id)

    return query.execute().data


def usage():
    sb = get_supabase()

    result = sb.rpc("get_app_usage").execute()

    if not result.data:
        return {
            "database_bytes": 0,
            "storage_bytes": 0,
        }

    if isinstance(result.data, list):
        return result.data[0]

    return result.data
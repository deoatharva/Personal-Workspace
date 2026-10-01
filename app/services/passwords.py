from .supabase_client import get_supabase
def list_passwords(search=''):
    q=get_supabase().table('password_entries').select('*').order('is_starred',desc=True).order('updated_at',desc=True)
    if search:
        t=search.replace('%','\\%').replace('_','\\_'); q=q.or_(f'name.ilike.%{t}%,username.ilike.%{t}%,url.ilike.%{t}%,category.ilike.%{t}%')
    return q.execute().data
def create_password(data): return get_supabase().table('password_entries').insert(data).execute().data[0]
def update_password(entry_id,data): return get_supabase().table('password_entries').update(data).eq('id',entry_id).execute().data[0]
def delete_password(entry_id): get_supabase().table('password_entries').delete().eq('id',entry_id).execute()

from .supabase_client import get_supabase
def list_notes(search='',note_type=None):
    q=get_supabase().table('notes').select('*').order('is_starred',desc=True).order('updated_at',desc=True)
    if note_type:q=q.eq('note_type',note_type)
    if search:
        term=search.replace('%','\\%').replace('_','\\_'); q=q.or_(f'title.ilike.%{term}%,content.ilike.%{term}%')
    return q.execute().data
def create_note(title,content,category,tags,note_type,is_starred=False):
    return get_supabase().table('notes').insert({'title':title or 'Untitled','content':content or '','category':category or None,'tags':[t.strip() for t in tags if t.strip()],'note_type':note_type,'is_starred':is_starred}).execute().data[0]
def update_note(note_id,title,content,category,tags,is_starred):
    return get_supabase().table('notes').update({'title':title or 'Untitled','content':content or '','category':category or None,'tags':[t.strip() for t in tags if t.strip()],'is_starred':is_starred}).eq('id',note_id).execute().data[0]
def delete_note(note_id):
    sb=get_supabase(); fs=sb.table('note_files').select('storage_path').eq('note_id',note_id).execute().data
    if fs: sb.storage.from_('notes-files').remove([f['storage_path'] for f in fs])
    sb.table('notes').delete().eq('id',note_id).execute()
def list_todos(note_id): return get_supabase().table('todos').select('*').eq('note_id',note_id).order('position').execute().data
def replace_todos(note_id,items):
    sb=get_supabase(); sb.table('todos').delete().eq('note_id',note_id).execute()
    if items: sb.table('todos').insert([{'note_id':note_id,'text':x['text'],'position':i,'completed':x['completed']} for i,x in enumerate(items)]).execute()
def toggle_todo(todo_id,completed): return get_supabase().table('todos').update({'completed':completed}).eq('id',todo_id).execute()
def list_files(note_id=None):
    q=get_supabase().table('note_files').select('*').order('created_at',desc=True)
    if note_id:q=q.eq('note_id',note_id)
    return q.execute().data

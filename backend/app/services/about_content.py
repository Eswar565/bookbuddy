"""Render About from the local content system and administrator-managed records."""
import json
from flexible import video_embed

def about_context(db):
    settings={r['content_key']:r['content_value'] for r in db().execute('SELECT content_key,content_value FROM site_content')}
    def get(key,default=''):
        return (settings.get(key) or '').strip() or default
    text=get('about_philosophy_body',get('about_text','Our library brings people together through books, reading circles and community events.'))
    try:
        raw=json.loads(get('about_videos_json','[]'))
    except (TypeError,ValueError):
        raw=[]
    videos=[]
    if isinstance(raw,list):
        for item in raw[:8]:
            if not isinstance(item,dict): continue
            url=item.get('url','')
            embed=video_embed(url)
            if embed:
                videos.append({'title':item.get('title','Library video'), 'description':item.get('description',''),'external':url,'embed':embed})
    from gallery_service import get_public_gallery
    gallery_settings, gallery_items = get_public_gallery(db)
    return dict(
        about_page_heading=get('about_heading','About Book Buddy'),
        about_philosophy_subheading=get('about_philosophy_subheading','A welcoming space for every reader'),
        philosophy_intro=get('about_philosophy_intro','Books, stories and community are at the centre of what we do.'),
        philosophy_paragraphs=[p.strip() for p in text.split('\n\n') if p.strip()],
        ikigai_url=get('about_ikigai_url','/static/img/brand/book-buddy-logo.png'),
        about_video_heading=get('about_video_heading','Library videos'),
        about_video_intro=get('about_video_intro','Reading tips, library stories and community highlights.'),
        about_videos=videos,
        gallery_settings=gallery_settings,
        gallery=gallery_items,
    )

"""SEO metadata and public sitemap for library pages."""
import os
from urllib.parse import urlsplit
from xml.sax.saxutils import escape
from flask import request, Response

def install_polish(app, db):
    with app.app_context():
        for key,value in {'seo_description':'Book Buddy lending library, books, reading circles, events and community publications.','seo_site_url':'http://127.0.0.1:5000'}.items():
            db().execute('INSERT OR IGNORE INTO site_content(content_key,content_value) VALUES (?,?)',(key,value))
        pass
        db().commit()
    def settings():
        return {r[0]:r[1] for r in db().execute('SELECT content_key,content_value FROM site_content')}
    def origin(data):
        value=os.environ.get('SITE_URL',data.get('seo_site_url','http://127.0.0.1:5000')).rstrip('/')
        parsed=urlsplit(value)
        return value if parsed.scheme in {'https','http'} and parsed.netloc else 'http://127.0.0.1:5000'
    @app.context_processor
    def metadata():
        data=settings(); path=request.path.strip('/'); desc=data['seo_description']
        page=db().execute('SELECT summary FROM cms_pages WHERE slug=?',(path,)).fetchone()
        if page and page[0]: desc=page[0]
        descriptions={'library':'Browse the Book Buddy lending-library catalogue. Explore collections, check available copies and request to borrow with your account.','membership':data.get('membership_intro','Explore Book Buddy membership plans.'),'contact':data.get('contact_address','Contact Book Buddy.'),'events':'Discover upcoming Book Buddy reading circles, contests and community library events.','publications':'Read Book Buddy newspapers and magazines, and discover our community publications.','podcasts':'Listen to podcasts from the Book Buddy community.'}
        desc=descriptions.get(path,desc)
        base=origin(data); private=path not in {'','about','contact','membership','how-to-borrow','plans'}
        return {'seo_description':desc[:300],'canonical_url':base+request.path,'seo_robots':'noindex,nofollow' if private or request.args else 'index,follow','structured_data':{'@context':'https://schema.org','@type':'Library','name':'Book Buddy','url':base,'telephone':data.get('contact_phone',''),'email':data.get('contact_email',''),'address':data.get('contact_address','')}}
    @app.get('/sitemap.xml')
    def sitemap_v7():
        data=settings(); base=origin(data)
        paths={'/','/about/','/contact/','/library/','/events/','/reading-circles/','/contests/','/publications/','/podcasts/','/gallery/','/membership-options/','/how-to-borrow/'}
        xml='<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>'+escape(base+path)+'</loc></url>' for path in sorted(paths))+'</urlset>'
        return Response(xml,mimetype='application/xml')
    def robots():
        if os.environ.get("DEMO_MODE", "0").strip().lower() in ("1", "true", "yes", "on"):
            return Response("User-agent: *\nDisallow: /\n", mimetype="text/plain")
        return Response('User-agent: *\nAllow: /\nDisallow: /admin/\nDisallow: /accounts/\nDisallow: /users/\nDisallow: /cart/\nDisallow: /checkout/\nDisallow: /legacy/\nSitemap: '+origin(settings())+'/sitemap.xml\n',mimetype='text/plain')
    # Replace the existing robots route without adding an ambiguous URL rule.
    for rule in app.url_map.iter_rules():
        if rule.rule=='/robots.txt': app.view_functions[rule.endpoint]=robots

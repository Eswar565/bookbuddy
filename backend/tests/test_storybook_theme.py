"""Static checks for the new library-only storybook interface."""
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]

def test_all_local_storybook_images_are_well_formed():
    art = ROOT / 'static/img/art'
    required = [
        '01-hero-readers.png', '02-book-shelves.png', '03-contact-envelope.png',
        '04-reading-circle.png', '05-membership-card.png', '06-magazine.png',
        '07-newspaper.png', '08-podcast.png', '09-gallery.png',
        '10-contest.png', '11-about-library.png', '12-empty-books.png',
        'book-cover-1.png', 'book-cover-2.png', 'book-cover-3.png', 'book-cover-4.png',
        'placeholder.png'
    ]
    for name in required:
        assert (art / name).is_file(), f'Missing required art file: {name}'
    png_files = list(art.glob('*.png'))
    assert len(png_files) >= 17
    for image in png_files:
        assert image.read_bytes()[:8] == b'\x89PNG\r\n\x1a\n', f'{image.name} is not a valid PNG'

def test_shared_folio_assets_and_local_fontawesome():
    for name in ('site/base.html','workspace/base.html'):
        shell=(ROOT/'templates'/name).read_text(encoding='utf8')
        for asset in ('/static/css/folio.css','/static/js/folio.js','/static/vendor/fontawesome/css/all.min.css'):
            assert asset in shell
            assert (ROOT/asset.lstrip('/')).is_file()
        assert '/static/css/storybook' not in shell
    home=(ROOT/'templates/site/home.html').read_text(encoding='utf8')
    assert 'hero-readers.svg' not in home
    assert 'fa-solid' in home

def test_navigation_still_library_focused():
    shell = (ROOT/'templates/site/base.html').read_text(encoding='utf8')
    for label in ('Home', 'About', 'Library', 'Events', 'Media', 'Contact', 'My dashboard'):
        assert label in shell
    assert '/skills/' not in shell

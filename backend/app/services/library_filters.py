"""Whitelisted, parameterized borrowing-desk filters and catalogue export utilities."""
import io
from datetime import date
from flask import send_file, Response

STATUSES = ('Requested', 'Issued', 'Returned', 'Lost', 'Damaged', 'Rejected', 'Cancelled')
SORTS = {
    'newest': 'l.id DESC',
    'oldest': 'l.id ASC',
    'member': 'u.name COLLATE NOCASE ASC, l.id DESC',
    'book': 'b.title COLLATE NOCASE ASC, l.id DESC',
    'due': "CASE WHEN l.status='Issued' AND l.due_date IS NOT NULL AND l.due_date!='' THEN 0 ELSE 1 END, l.due_date ASC, l.id DESC",
    'status': 'l.status ASC, l.id DESC',
}
PER_PAGE = (25, 50, 100)
ATTENTION = ('all', 'overdue', 'due_soon', 'return_requested')

def safe_date(value):
    value = (value or '')[:10]
    try:
        return date.fromisoformat(value).isoformat()
    except (TypeError, ValueError):
        return ''

def read_filters(args):
    get = lambda key, default='': str(args.get(key, default) or '').strip()
    status = get('status')
    if status not in STATUSES + ('Overdue', 'Return requested'):
        status = ''
    attention = get('attention', 'all')
    if attention not in ATTENTION: attention = 'all'
    sort = get('sort', 'newest')
    if sort not in SORTS: sort = 'newest'
    try: per_page = int(get('per_page', '25'))
    except ValueError: per_page = 25
    if per_page not in PER_PAGE: per_page = 25
    try: page = max(1, min(100000, int(get('page', '1'))))
    except ValueError: page = 1
    start, end = safe_date(get('from_date')), safe_date(get('to_date'))
    if start and end and start > end: start, end = end, start
    return dict(status=status, q=get('q')[:100], attention=attention,
                from_date=start, to_date=end, sort=sort, per_page=per_page, page=page)

def loan_conditions(filters, today):
    clauses, params = [], []
    status = filters['status']
    if status in STATUSES:
        clauses.append('l.status=?'); params.append(status)
    elif status == 'Overdue':
        clauses.append("l.status='Issued' AND l.due_date IS NOT NULL AND l.due_date<>'' AND l.due_date<?"); params.append(today)
    elif status == 'Return requested':
        clauses.append("l.status='Issued' AND COALESCE(l.return_requested_at,'')<>''")
    attention = filters['attention']
    if attention == 'overdue':
        clauses.append("l.status='Issued' AND l.due_date IS NOT NULL AND l.due_date<>'' AND l.due_date<?"); params.append(today)
    elif attention == 'due_soon':
        from datetime import timedelta
        limit = (date.fromisoformat(today) + timedelta(days=7)).isoformat()
        clauses.append("l.status='Issued' AND l.due_date>=? AND l.due_date<=?"); params.extend((today,limit))
    elif attention == 'return_requested':
        clauses.append("l.status='Issued' AND COALESCE(l.return_requested_at,'')<>''")
    if filters['q']:
        search = '%'+filters['q'].replace('\\','\\\\').replace('%','\\%').replace('_','\\_')+'%'
        clauses.append("(b.title LIKE ? ESCAPE '\\' OR u.name LIKE ? ESCAPE '\\' OR u.email LIKE ? ESCAPE '\\' OR u.phone LIKE ? ESCAPE '\\' OR CAST(l.id AS TEXT) LIKE ? ESCAPE '\\')")
        params.extend([search]*5)
    if filters['from_date']:
        clauses.append('substr(l.requested_at,1,10)>=?'); params.append(filters['from_date'])
    if filters['to_date']:
        clauses.append('substr(l.requested_at,1,10)<=?'); params.append(filters['to_date'])
    return (' WHERE '+' AND '.join('('+c+')' for c in clauses) if clauses else ''), params

JOINED_LOANS = ('FROM lending_loans l JOIN books b ON b.id=l.book_id '
                'JOIN users u ON u.id=l.user_id '
                'LEFT JOIN lending_subscriptions s ON s.id=l.subscription_id '
                'LEFT JOIN lending_plans p ON p.id=s.plan_id')

def loan_query(filters, today):
    where, params = loan_conditions(filters, today)
    return JOINED_LOANS + where, params, SORTS[filters['sort']]


# ---------------------------------------------------------------------------
# Catalogue Filtering & Export
# ---------------------------------------------------------------------------

def get_filtered_books_for_export(db, args) -> list[dict]:
    """Retrieve all filtered books matching the request query params (without pagination limit)."""
    search = str(args.get("q", "")).strip()[:120]
    collection = str(args.get("collection", "")).strip()[:120]
    filters = ["archived=0"]
    params = []

    if search:
        filters.append("(LOWER(title) LIKE ? ESCAPE '!' OR LOWER(author) LIKE ? ESCAPE '!' OR LOWER(description) LIKE ? ESCAPE '!')")
        pattern = "%" + search.lower().replace("!", "!!").replace("%", "!%").replace("_", "!_") + "%"
        params.extend([pattern] * 3)

    if collection:
        filters.append("collection = ?")
        params.append(collection)

    category = str(args.get("category", "")).strip()[:120]
    lang = str(args.get("lang", "") or args.get("language", "")).strip()[:120]
    if lang.lower() == "all":
        lang = ""

    chosen = {k: str(args.get(k, "")).strip()[:120] for k in ['language', 'age_group', 'author', 'product_type', 'availability', 'new', 'sort', 'audience', 'category', 'lang']}
    chosen['category'] = category
    chosen['lang'] = lang

    if category and category.lower() != "all":
        cat_lower = category.lower()
        if cat_lower == "baby":
            filters.append("(LOWER(category) LIKE '%baby%' OR age_group IN ('0-2', '0-3', 'Baby'))")
        elif cat_lower == "toddler":
            filters.append("(LOWER(category) LIKE '%toddler%' OR age_group IN ('3-5', '2-4', 'Toddler'))")
        elif cat_lower == "junior":
            filters.append("(LOWER(category) LIKE '%junior%' OR age_group IN ('5', '6-8', 'Junior'))")
        elif cat_lower == "middle grade":
            filters.append("(LOWER(category) LIKE '%middle grade%' OR LOWER(category) LIKE '%middle-grade%' OR age_group IN ('9-12', 'Middle Grade'))")
        elif cat_lower == "young adults":
            filters.append("(LOWER(category) LIKE '%young adult%' OR age_group IN ('12+', '13-18', 'Young Adults'))")
        elif cat_lower == "adults":
            filters.append("(LOWER(category) LIKE '%adult%' OR LOWER(audience) IN ('adult', 'adults'))")
        elif cat_lower == "fiction":
            filters.append("(LOWER(category) LIKE '%fiction%' AND LOWER(category) NOT LIKE '%non-fiction%' AND LOWER(category) NOT LIKE '%non fiction%' OR collection IN ('Picture Books', 'Chapter Books', 'Adventure', 'Classics', 'Sci-Fi', 'Fantasy', 'Folktales', 'Story') OR product_type = 'fiction')")
        elif cat_lower in ("non fiction", "non-fiction"):
            filters.append("(LOWER(category) LIKE '%non fiction%' OR LOWER(category) LIKE '%non-fiction%' OR collection IN ('Non-Fiction', 'Non Fiction', 'AI') OR product_type = 'non-fiction')")
        elif cat_lower == "languages":
            if not lang:
                filters.append("id IN (SELECT book_id FROM book_languages WHERE language IS NOT NULL AND TRIM(language) <> '')")
        else:
            filters.append("(LOWER(category) LIKE ? OR LOWER(collection) LIKE ?)")
            params.extend([f"%{cat_lower}%", f"%{cat_lower}%"])

    if lang:
        filters.append("id IN (SELECT book_id FROM book_languages WHERE LOWER(language) = LOWER(?))")
        params.append(lang)

    if chosen['audience'] in {'adult', 'kids'}:
        filters.append("audience IN (?, 'all')")
        params.append(chosen['audience'])

    for key in ['age_group', 'author', 'product_type']:
        if chosen[key]:
            filters.append('LOWER(' + key + ') = LOWER(?)')
            params.append(chosen[key])

    try:
        from book_availability import get_availability_sql_filter, is_book_available
    except ImportError:
        from app.services.book_availability import get_availability_sql_filter, is_book_available

    avail_filter = get_availability_sql_filter(chosen.get('availability'))
    if avail_filter:
        filters.append(f"({avail_filter})")

    if chosen['new'] == '1':
        filters.append('is_new_arrival=1')

    sort_val = chosen.get('sort', 'newest').lower()
    if sort_val in ('az', 'title'):
        ordering = 'title COLLATE NOCASE ASC, id ASC'
    elif sort_val == 'za':
        ordering = 'title COLLATE NOCASE DESC, id DESC'
    else:
        ordering = 'is_new_arrival DESC, id DESC'

    where = f" WHERE {' AND '.join(filters)}" if filters else ""
    rows = db.execute(
        "SELECT id, title, author, collection, language, age_group, audience, available_copies, stock, is_new_arrival FROM books" + where + " ORDER BY " + ordering,
        params
    ).fetchall()

    books = []
    for r in rows:
        b = dict(r)
        b["availability"] = "Available" if is_book_available(b) else "Unavailable"
        b["reader_type"] = (b.get("audience") or b.get("age_group") or "All readers").title()
        b["category"] = b.get("collection") or "General"
        books.append(b)
    return books


def export_books_excel(books: list[dict]) -> Response:
    """Generate and stream .xlsx file using openpyxl."""
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Book Catalogue"

    headers = ["Title", "Author", "Category", "Language", "Reader Type", "Availability"]
    ws.append(headers)

    header_fill = PatternFill(start_color="061446", end_color="061446", fill_type="solid")
    header_font = Font(name="Arial", size=11, bold=True, color="FFFFFF")
    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="left", vertical="center")

    thin_border = Border(
        left=Side(style='thin', color='E2E8F0'),
        right=Side(style='thin', color='E2E8F0'),
        top=Side(style='thin', color='E2E8F0'),
        bottom=Side(style='thin', color='E2E8F0')
    )
    alt_fill = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")

    try:
        from app.services.languages import parse_languages
    except ImportError:
        try:
            from languages import parse_languages
        except ImportError:
            from .languages import parse_languages
    for idx, b in enumerate(books, start=2):
        row_data = [
            b.get("title", ""),
            b.get("author", ""),
            b.get("category", ""),
            ", ".join(parse_languages(b.get("language", ""))),
            b.get("reader_type", ""),
            b.get("availability", "Available")
        ]
        ws.append(row_data)
        for cell in ws[idx]:
            cell.border = thin_border
            cell.font = Font(name="Arial", size=10)
            if idx % 2 == 1:
                cell.fill = alt_fill

    for col in ws.columns:
        max_len = max(len(str(cell.value or "")) for cell in col)
        col_letter = openpyxl.utils.get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 4, 14)

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    return send_file(
        output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="book_catalogue.xlsx"
    )


def export_books_pdf(books: list[dict]) -> Response:
    """Generate and stream a clean, readable PDF table using PyMuPDF (fitz)."""
    import fitz

    doc = fitz.open()
    cols = [
        ('Title', 160),
        ('Author', 100),
        ('Category', 80),
        ('Language', 60),
        ('Reader Type', 65),
        ('Availability', 60),
    ]
    total_w = sum(w for _, w in cols)
    margin_x = 35
    row_h = 20
    header_h = 24

    def add_page():
        p = doc.new_page(width=595, height=842)
        # Title branding
        p.insert_text((margin_x, 40), 'Book Buddy · Library Book Catalogue', fontsize=14, fontname='helv', color=(0.02, 0.08, 0.27))
        # Header rect
        p.draw_rect(fitz.Rect(margin_x, 55, margin_x + total_w, 55 + header_h), color=(0.02, 0.08, 0.27), fill=(0.02, 0.08, 0.27))
        x = margin_x
        for title, w in cols:
            p.insert_text((x + 4, 71), title, fontsize=9, fontname='helv', color=(1, 1, 1))
            x += w
        return p

    p = add_page()
    y = 55 + header_h
    page_num = 1

    for i, b in enumerate(books):
        if y + row_h > 800:
            p.insert_text((margin_x, 820), f'Page {page_num}', fontsize=8, color=(0.4, 0.4, 0.4))
            p = add_page()
            page_num += 1
            y = 55 + header_h

        bg = (0.97, 0.98, 0.99) if i % 2 == 1 else (1, 1, 1)
        p.draw_rect(fitz.Rect(margin_x, y, margin_x + total_w, y + row_h), color=(0.9, 0.9, 0.9), fill=bg)

        row_vals = [
            str(b.get('title', ''))[:30],
            str(b.get('author', ''))[:18],
            str(b.get('category', ''))[:14],
            str(b.get('language', ''))[:10],
            str(b.get('reader_type', ''))[:12],
            str(b.get('availability', 'Available'))[:12]
        ]
        x = margin_x
        for val, (_, w) in zip(row_vals, cols):
            p.insert_text((x + 4, y + 14), val, fontsize=8, fontname='helv', color=(0.1, 0.1, 0.1))
            x += w
        y += row_h

    p.insert_text((margin_x, 820), f'Page {page_num}', fontsize=8, color=(0.4, 0.4, 0.4))
    pdf_bytes = doc.tobytes()

    output = io.BytesIO(pdf_bytes)
    output.seek(0)

    return send_file(
        output,
        mimetype="application/pdf",
        as_attachment=True,
        download_name="book_catalogue.pdf"
    )

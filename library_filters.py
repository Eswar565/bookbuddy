"""Whitelisted, parameterized borrowing-desk filters, used by the Flask route."""
from datetime import date

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
        # A contains-search, not a raw SQL fragment or operator.
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

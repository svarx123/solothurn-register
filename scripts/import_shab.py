"""Import official SHAB publications. Python 3.11+, no dependencies."""
import argparse
import datetime as dt
import json
import pathlib
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

BASE = 'https://amtsblattportal.ch/api/v1/'
ROOT = pathlib.Path(__file__).resolve().parents[1]

def get_xml(url):
    for attempt in range(4):
        try:
            request = urllib.request.Request(url, headers={'User-Agent': 'SolothurnRegister/1.0', 'Accept': 'application/xml'})
            with urllib.request.urlopen(request, timeout=60) as response:
                data = response.read()
            if b'<!DOCTYPE' in data.upper():
                raise ValueError('Unexpected XML document type')
            return ET.fromstring(data)
        except Exception:
            if attempt == 3:
                raise
            time.sleep(2 ** attempt)

def text(node, path, default=''):
    return node.findtext(path, default=default) or default

def list_notices(start, end, state):
    day = dt.date.fromisoformat(start)
    while day <= dt.date.fromisoformat(end):
        yield from list_day(day.isoformat(), state)
        day += dt.timedelta(days=1)

def list_day(day, state):
    page = 0
    seen = set()
    while True:
        params = {'publicationStates': state, 'tenant': 'shab', 'rubrics': 'HR',
                  'publicationDate.start': day, 'publicationDate.end': day,
                  'pageRequest.page': page, 'pageRequest.size': 2000}
        root = get_xml(BASE + 'publications/xml?' + urllib.parse.urlencode(params))
        total = int(text(root, 'total', '-1'))
        if total < 0:
            raise ValueError('Missing total in SHAB response')
        entries = root.findall('publication')
        for entry in entries:
            meta = entry.find('meta')
            if meta is None:
                raise ValueError('Missing publication metadata')
            ident = text(meta, 'id')
            if ident in seen:
                raise ValueError('Unstable upstream pagination: duplicate publication')
            seen.add(ident)
            # Do not trust the upstream canton filter: it is ignored by the live API.
            if 'SO' in [c.text for c in meta.findall('cantons')] and text(meta, 'rubric') == 'HR':
                date = text(meta, 'publicationDate')
                if date != day:
                    raise ValueError('Publication outside requested date range')
                yield meta
        if (page + 1) * 2000 >= total:
            if len(seen) != total:
                raise ValueError('Incomplete publication list')
            return
        if not entries:
            raise ValueError('Pagination stopped before all publications were received')
        page += 1
        time.sleep(1)

def parse_detail(root, meta):
    new = root.find('content/commonsNew/company')
    old = root.find('content/commonsActual/company')
    company = new if new is not None else old
    if company is None:
        raise ValueError('Missing company data')
    uid = text(company, 'uid')
    return {'id': text(meta, 'id'), 'date': text(meta, 'publicationDate'),
            'type': text(meta, 'subRubric'), 'state': 'PUBLISHED',
            'title': text(meta, 'title/de', text(meta, 'title/fr')),
            'name': text(company, 'name'), 'uid': uid, 'seat': text(company, 'seat'),
            'text': text(root, 'content/publicationText'),
            'pdf': BASE + 'publications/' + text(meta, 'id') + '/pdf'}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--days', type=int, default=14)
    parser.add_argument('--end', default=dt.datetime.now(dt.timezone.utc).date().isoformat())
    args = parser.parse_args()
    end = dt.date.fromisoformat(args.end)
    start = (end - dt.timedelta(days=args.days - 1)).isoformat()
    target = ROOT / 'dist/data/notices.json'
    previous = json.loads(target.read_text(encoding='utf-8')) if target.exists() else {}
    rows = {r['id']: r for r in previous.get('notices', [])}
    # Fully refresh the covered window; retain older imported history.
    rows = {key: row for key, row in rows.items() if not start <= row['date'] <= end.isoformat()}
    for meta in list_notices(start, end.isoformat(), 'PUBLISHED'):
        ident = text(meta, 'id')
        root = get_xml(BASE + 'publications/' + urllib.parse.quote(ident, safe='') + '/xml')
        rows[ident] = parse_detail(root, meta)
        print(f"Imported {ident}", flush=True)
        time.sleep(1)
    for meta in list_notices(start, end.isoformat(), 'CANCELLED'):
        rows.pop(text(meta, 'id'), None)
    result = {'updatedAt': dt.datetime.now(dt.timezone.utc).isoformat(),
              'coverageStart': min(start, previous.get('coverageStart', start)),
              'coverageEnd': end.isoformat(), 'source': BASE,
              'notices': sorted(rows.values(), key=lambda r: (r['date'], r['id']), reverse=True)}
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix('.tmp')
    temporary.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temporary.replace(target)
    print(f"Saved {len(rows)} Solothurn publications")

if __name__ == '__main__':
    main()

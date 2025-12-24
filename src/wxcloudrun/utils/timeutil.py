from datetime import datetime

def parse_time_only(v):
    if not v:
        return None
    try:
        return datetime.strptime(v, '%H:%M:%S').time()
    except ValueError:
        try:
            return datetime.strptime(v, '%H:%M').time()
        except ValueError as e:
            raise ValueError(f'无效的时间格式: {v}') from e

def format_time(t):
    return t.strftime('%H:%M') if t else None

def parse_date_only(v):
    if not v:
        return None
    try:
        return datetime.strptime(v, '%Y-%m-%d').date()
    except ValueError as e:
        raise ValueError(f'无效的日期格式: {v}') from e
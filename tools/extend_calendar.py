"""Extend offline lunar dates with lunar_python 1.4.8; keep verified workdays."""
import datetime as dt
import json
from pathlib import Path
from lunar_python import Solar

ROOT=Path(__file__).resolve().parents[1]
SOURCE='https://www.gov.cn/zhengce/content/202611/content_7085101.htm'
OFF=[('01-01','01-03'),('02-05','02-13'),('04-03','04-05'),('05-01','05-05'),('06-09','06-09'),('09-15','09-15'),('10-01','10-07')]
WORK={'01-31','02-14','05-08','09-26','10-09'}
path=ROOT/'assets/calendar-data.js'
data=json.loads(path.read_text(encoding='utf-8').split('window.CALENDAR_DAYS=',1)[1].split(';',1)[0])
day=dt.date(2027,1,1)
while day.year<=2035:
    lunar=Solar.fromYmd(day.year,day.month,day.day).getLunar()
    festivals=lunar.getFestivals()
    festival={'01-01':'元旦','05-01':'劳动节','10-01':'国庆节'}.get(day.strftime('%m-%d')) or (festivals[0] if festivals else '')
    label=festival or lunar.getJieQi() or (lunar.getMonthInChinese()+'月' if lunar.getDay()==1 else lunar.getDayInChinese())
    md=day.strftime('%m-%d')
    off=day.year==2027 and any(a<=md<=b for a,b in OFF)
    work=day.year==2027 and md in WORK
    data[day.isoformat()]=[label,'休' if off else '班' if work else '',off,work]
    day+=dt.timedelta(days=1)
path.write_text('// Lunar dates through 2035; official workdays through 2027.\n// 2027: '+SOURCE+'\nwindow.CALENDAR_DAYS='+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8')

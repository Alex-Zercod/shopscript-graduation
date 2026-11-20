"""Explicit --live runs two paid reviewer requests using fictional data only."""
import copy,json,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import server

if '--live' not in sys.argv:raise SystemExit('Pass --live to spend Ollama quota on two synthetic review cases.')
brief={'product':'Вымышленный учебный лёгкий крем','facts':'Только учебный пример. Лёгкое тонирование, плотное покрытие не заявлено.',
 'audience':'Зрители учебного примера','goal':'Сохранить название','tone':'Личная рекомендация','duration':'20–25 секунд',
 'experience':'Вымышленная автор сообщает: пользуюсь этим кремом не первый год, коже комфортно.',
 'filming':'План будущей съёмки, ещё не снято. Автор разговаривает с флаконом в руках, коротко показывает этикетку. Без нанесения и до/после.'}
s={'product_name':brief['product'],'audience':brief['audience'],'idea':'Честно объяснить ожидания от лёгкого покрытия.',
 'hook':'Этим кремом пользуюсь не первый год.',
 'frames':[{'time':'0:00–0:06','visual':'Автор рассказывает, держит флакон в руках. Это план будущего кадра.','voice':'Этим кремом пользуюсь не первый год.','on_screen_text':'Не первый год'},
 {'time':'0:06–0:14','visual':'Кульминация: автор показывает этикетку и объясняет отличие лёгкого тонирования от плотного покрытия. Монтажная склейка на этикетку.','voice':'Коже комфортно. Но плотного покрытия от него не жду.','on_screen_text':'Лёгкое тонирование'},
 {'time':'0:14–0:22','visual':'Возвращение к разговору автора с флаконом в руках.','voice':'Сохраните название, чтобы не потерять.','on_screen_text':'Сохраните название'}],
 'voiceover':'Собирается','on_screen':'Не первый год; Лёгкое тонирование; Сохраните название',
 'cta':'Сохраните название, чтобы не потерять.','caption':'Лёгкое тонирование — не плотный тон. Сохраните название, чтобы не потерять.',
 'rationale':'Личный рассказ без нанесения; кульминация смысловая. Это учебный сценарий, а не состоявшаяся съёмка.'}
server.validate(s)
research={'status':'ready','facts':[brief['facts'],brief['experience'],brief['filming']],'exclusions':['Не добавлять свойства и события.'],'questions':[]}
bad=copy.deepcopy(s);bad['frames'][1]['on_screen_text']='Монтажная склейка: крупный план этикетки';bad['on_screen']='Монтажная склейка: крупный план этикетки'
rows=[]
for name,script,expected in [('future-talk',s,'pass'),('technical-caption',bad,'needs_changes')]:
    begin=time.monotonic();review=server.ask(server.REVIEW_RULES,{'brief':brief,'research':research,'script':script})
    rows.append({'case':name,'expected':expected,'review':review,'seconds':round(time.monotonic()-begin,1)})
out=Path(__file__).resolve().parents[1]/'docs'/'checks-2026-11-17';out.mkdir(exist_ok=True)
(out/'reviewer-live.json').write_text(json.dumps({'version':server.APP_VERSION,'data':'fictional, no Katya data','cases':rows},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(rows,ensure_ascii=True),flush=True)
assert all(r['review'].get('status')==r['expected'] for r in rows)
assert rows[0]['review'].get('issues')==[] and rows[1]['review'].get('issues')

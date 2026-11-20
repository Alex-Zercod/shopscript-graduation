let current;
const $=id=>document.getElementById(id);
const formats={direct:'Сразу в проблему',friend:'По-свойски, с юмором',topic:'Интрига с быстрым раскрытием'};
function save(name,data){const url=URL.createObjectURL(new Blob([data],{type:'application/json;charset=utf-8'}));const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
function add(tag,text,parent,cls){const e=document.createElement(tag);e.textContent=text;if(cls)e.className=cls;parent.append(e);return e;}
function busy(flag){for(const id of ['generate','open-example','load-brief'])$(id).disabled=flag;document.querySelectorAll('.expand').forEach(b=>b.disabled=flag);}
function scriptView(data,root){
 const s=data.script;
 const details=add('details','',root);details.open=true;add('summary','План съёмки и полный текст',details);
 for(const f of s.frames){const block=add('div','',details,'frame');add('div',f.time,block,'time');for(const [k,label] of [['visual','В кадре'],['voice','Озвучка'],['on_screen_text','На экране']])add('p',label+': '+f[k],block);}
 for(const [k,label] of [['voiceover','Озвучка целиком'],['on_screen','Текст на экране'],['caption','Подпись'],['rationale','Почему такой подход']]){add('h3',label,details);add('p',Array.isArray(s[k])?s[k].join('\n'):s[k],details);}
 const notes=add('details','',root,'notes');add('summary','Проверка и ограничения',notes);add('p',(data.review_notes||[]).join('\n\n'),notes);
}
function show(data,label){
 current=data;const root=$('result');root.replaceChildren();root.hidden=false;$('exports').hidden=false;$('result-label').textContent=label;
 $('download').textContent=data.kind==='concepts'?'Скачать все варианты':'Скачать JSON';
 if(data.kind==='concepts'){
  add('p','Сравните идеи и выберите ту, которую хочется снять. Для полного плана нажмите кнопку у нужного варианта.',root,'hint');
  for(const c of data.concepts){
   const card=add('article','',root,'concept');add('p',formats[c.id],card,'eyebrow');add('h3',c.title,card);
   const labels=data.scheme==='hook-pain-solution-link'?[['hook','Хук · первые 3 секунды'],['main_idea','Боль'],['development','Решение'],['climax','Раскрытие'],['cta','Где купить'],['filming','Что снять'],['product_connection','Логика для автора']]:[['hook','Начало'],['main_idea','Главная мысль'],['development','Как развивается'],['climax','Поворот'],['product_connection','Зачем здесь товар'],['filming','Что снять'],['cta','Призыв']];
   if(data.scheme==='hook-pain-solution-link'){add('h4','Текст целиком',card);add('p',[c.hook,c.main_idea,c.development,c.climax,c.cta].join(' '),card);}
   for(const [k,label] of labels){add('strong',label,card);add('p',c[k],card);}
   const button=add('button','Развернуть этот вариант',card,'expand secondary');button.type='button';
   const status=add('p','',card);status.setAttribute('role','status');
   const expanded=add('div','',card);
   button.addEventListener('click',async()=>{
    const batch=current;if(batch!==data)return;
    if(batch.status!=='ready'&&!window.confirm('В наборе остались замечания. Развернуть этот черновой замысел?'))return;
    busy(true);status.textContent='Готовим и проверяем полный план выбранного подхода…';
    try{
     const response=await fetch('/api/expand',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({brief:batch.brief,concept:c})});
     const result=await response.json();if(!response.ok)throw Error(result.error||'Не удалось получить план.');
     if(result.status==='needs_input'){status.textContent=result.questions.join('\n');return;}
     batch.expanded=batch.expanded||{};batch.expanded[c.id]=result;expanded.replaceChildren();scriptView(result,expanded);
     status.textContent=result.status==='ready'?'План проверен по заданию. Прочитайте вслух перед съёмкой.':'Черновик: после доработки остались замечания. Посмотрите ограничения.';
     button.textContent='Подготовить этот план заново';
    }catch(e){status.textContent=e.message;}
    finally{busy(false);}
   });
  }
  const notes=add('details','',root,'notes');add('summary','Проверка набора',notes);add('p',(data.review_notes||[]).join('\n\n'),notes);
 }else{
  add('h3',data.script.product_name,root);for(const [k,label] of [['hook','Хук'],['idea','Главная мысль'],['cta','Призыв']]){add('h3',label,root);add('p',data.script[k],root);}scriptView(data,root);
 }
}
const values=()=>Object.fromEntries(new FormData($('brief')));
$('load-brief').addEventListener('click',()=>$('brief-file').click());
$('brief-file').addEventListener('change',async event=>{
 const file=event.target.files[0];if(!file)return;
 try{
  if(file.size>100000)throw Error('Выберите JSON задания до 100 КБ.');
  const data=JSON.parse((await file.text()).replace(/^\uFEFF/,''));
  if(!data||typeof data!=='object'||Array.isArray(data)||data.script||data.result||data.concepts)throw Error('Нужен файл из «Скачать задание», а не готовые сценарии.');
  const keys=['product','facts','audience','goal','experience','filming','platform','duration','link_status'];
  if(['product','facts','audience','goal'].some(k=>typeof data[k]!=='string'))throw Error('В файле не найдены основные поля задания.');
  const updates=[];
  for(const k of keys){
   const control=$(k),value=data[k]===undefined?'':data[k];
   if(typeof value!=='string')throw Error('Неверный формат поля «'+control.labels[0].textContent+'».');
   if(control.tagName==='SELECT'){
    if(!value){updates.push([control,control.options[0].value]);continue;}
    if(!Array.from(control.options).some(o=>o.value===value))throw Error('Неизвестное значение поля «'+control.labels[0].textContent+'».');
   }else if(control.maxLength>0&&value.length>control.maxLength)throw Error('Слишком длинное поле «'+control.labels[0].textContent+'».');
   updates.push([control,value]);
  }
  const hasInput=keys.some(k=>$(k).tagName==='SELECT'?$(k).selectedIndex>0:$(k).value.trim());
  if(hasInput&&!window.confirm('Заменить заполненные поля данными из файла?'))return;
  for(const [control,value] of updates)control.value=value;
  current=null;$('result').hidden=true;$('exports').hidden=true;$('result-label').textContent='Ожидаем задание';$('result-status').textContent='';
  $('brief-status').textContent='Задание загружено. Теперь по нему будут предложены три подхода; прежний выбор подачи не ограничивает набор.';
 }catch(e){$('brief-status').textContent=e instanceof SyntaxError?'Не удалось прочитать JSON. Поля остались без изменений.':e.message;}
 finally{event.target.value='';}
});
$('save-brief').addEventListener('click',()=>save('shopscript-задание.json',JSON.stringify(values(),null,2)));
$('brief').addEventListener('submit',async event=>{
 event.preventDefault();const brief=values();
 if(['product','facts','audience','goal'].some(k=>!brief[k].trim())){$('brief-status').textContent='Заполните поля содержательным текстом.';return;}
 busy(true);$('brief-status').textContent='Ищем три разных замысла и проверяем их. Можно подождать несколько минут.';
 $('result').hidden=true;$('exports').hidden=true;current=null;$('result-label').textContent='Готовим три подхода';$('result-status').textContent='';
 try{
  const response=await fetch('/api/generate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(brief)});
  const data=await response.json();if(!response.ok)throw Error(data.error||'Не удалось подготовить идеи.');
  if(data.status==='needs_input'){
   const root=$('result');root.replaceChildren();root.hidden=false;$('result-label').textContent='Нужно уточнить';add('h3','Дополните задание',root);for(const q of data.questions)add('p','• '+q,root);
   $('brief-status').textContent='Добавьте ответы в сведения или личный опыт и повторите запрос.';
  }else{
   show(data,data.status==='ready'?'Три подхода проверены по заданию':'Три черновика: есть замечания');
   $('brief-status').textContent=data.status==='ready'?'Выберите замысел. Полный план создаётся только для выбранного варианта.':'После одной доработки остались замечания. Они перечислены в проверке набора.';
  }
 }catch(e){$('brief-status').textContent=e.message;$('result-label').textContent='Не удалось завершить';}
 finally{busy(false);}
});
$('open-example').addEventListener('click',async()=>{try{const r=await fetch('example.json');if(!r.ok)throw Error();show(await r.json(),'Архивный одиночный пример');$('result-status').textContent='Это прежний результат VitaMeal, а не новые три подхода к заданию.';}catch{$('result-status').textContent='Не удалось открыть пример.';}});
$('download').addEventListener('click',()=>{if(current)save(current.kind==='concepts'?'shopscript-три-подхода.json':'shopscript-сценарий.json',JSON.stringify(current,null,2));});
function scriptText(data){const s=data.script;return [s.product_name,'Хук: '+s.hook,'Главная мысль: '+s.idea,...s.frames.map(f=>[f.time,f.visual,'Озвучка: '+f.voice,'На экране: '+f.on_screen_text].join('\n')),'Призыв: '+s.cta,'Подпись: '+s.caption,...(data.review_notes||[])].join('\n\n');}
$('copy').addEventListener('click',async()=>{
 try{
  if(!current)return;let text;
  if(current.kind==='concepts')text=current.concepts.map(c=>[formats[c.id],c.title,'Начало: '+c.hook,(current.scheme==='hook-pain-solution-link'?'Боль: ':'Главная мысль: ')+c.main_idea,(current.scheme==='hook-pain-solution-link'?'Решение: ':'Развитие: ')+c.development,'Поворот: '+c.climax,'Съёмка: '+c.filming,'Связь с товаром: '+c.product_connection,'Призыв: '+c.cta,current.expanded?.[c.id]?scriptText(current.expanded[c.id]):''].filter(Boolean).join('\n\n')).join('\n\n—————\n\n');
  else text=scriptText(current);
  await navigator.clipboard.writeText(text);$('result-status').textContent='Текст скопирован.';
 }catch{$('result-status').textContent='Копирование недоступно. Скачайте JSON.';}
});
fetch('/api/status').then(r=>r.json()).then(s=>{$('service-status').textContent=s.reason+(s.app_version?' Версия '+s.app_version+'.':' Обновите запуск приложения.');}).catch(()=>{$('service-status').textContent='Нет связи с приложением. Запустите его заново.';});

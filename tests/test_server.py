"""Offline checks. No cloud requests or personal data transmission."""
import copy
import unittest
from unittest.mock import patch
import server
import start

def sample():
    voices=['Покажу держатель для пяти кабелей.','В нём пять отдельных мест.','Посмотрите, как размещены кабели.']
    frames=[{'time':t,'visual':v,'voice':s,'on_screen_text':''} for t,v,s in zip(
        ['0:00–0:06','0:06–0:14','0:14–0:22'],
        ['Руки показывают держатель.','Кульминация: кабели размещают в держателе.','Готовый держатель на столе.'],voices)]
    return dict(product_name='Учебный держатель',audience='Владельцы проводов',idea='Показ устройства',hook=voices[0],
        frames=frames,voiceover='Будет собрано',on_screen='Держатель',cta=voices[-1],caption='Пять мест',rationale='Одна демонстрация')

class Checks(unittest.TestCase):
    def test_voice_built_from_frames(self):
        s=sample();server.validate(s);self.assertEqual(s['voiceover'],' '.join(f['voice'] for f in s['frames']))
    def test_gap_rejected(self):
        s=sample();s['frames'][1]['time']='0:07–0:14'
        with self.assertRaises(ValueError):server.validate(s)
    def test_wrong_duration_rejected(self):
        with self.assertRaises(ValueError):server.validate(sample(),'30–40 секунд')
    def test_extra_field_rejected(self):
        s=sample();s['invented']='x'
        with self.assertRaises(ValueError):server.validate(s)
    def test_long_speech_detected(self):
        s=sample();s['frames'][0]['voice']='слово '*40;server.validate(s)
        self.assertTrue(server.speech_check(s)['issues'])
    def test_questions_stop_before_writer(self):
        with patch.object(server,'ask',return_value={'status':'needs_input','facts':[],'exclusions':[],'questions':['Какой объём?']}) as ask:
            self.assertEqual(server.generate_script({})['status'],'needs_input');self.assertEqual(ask.call_count,1)
    def test_one_revision_even_if_model_passes_long_speech(self):
        s=sample();s['frames'][0]['voice']='слово '*40
        responses=[{'status':'ready','facts':[],'exclusions':[],'questions':[]},{'script':copy.deepcopy(s)},
            {'status':'pass','issues':[]},{'script':copy.deepcopy(s)},{'status':'pass','issues':[]}]
        with patch.object(server,'ask',side_effect=responses) as ask:
            r=server.generate_script({'duration':'20–25 секунд'});self.assertEqual(r['status'],'needs_changes');self.assertEqual(ask.call_count,5)
    def test_contradictory_review_rejected(self):
        responses=[{'status':'ready','facts':[],'exclusions':[],'questions':[]},{'script':sample()},{'status':'pass','issues':['Есть ошибка']}]
        with patch.object(server,'ask',side_effect=responses):
            with self.assertRaises(ValueError):server.generate_script({'duration':'20–25 секунд'})
    def test_launcher_reads_actual_version(self):
        self.assertEqual(start.expected_version(),server.APP_VERSION)
    def test_old_server_not_silently_opened(self):
        with patch.object(start,'running_version',return_value='old-version'),patch.object(start.webbrowser,'open') as browser:
            self.assertEqual(start.main(),1);browser.assert_not_called()

class ConceptChecks(unittest.TestCase):
    def routes(self):
        return {'routes':[dict(id=k,interest=k,development=k,payoff=k,focus=k,avoid=k) for k in server.FORMATS]}
    def test_unrelated_variants_preserved(self):
        items=self.items();changed=dict(items[1],hook='New hook')
        result=server.merge_revision(items,[changed],{'friend'})
        self.assertIs(result[0],items[0]);self.assertIs(result[2],items[2]);self.assertEqual(result[1],changed)
    def test_unrelated_revision_rejected(self):
        with self.assertRaises(ValueError):server.merge_revision(self.items(),[self.items()[0]],{'friend'})
    def quality(self):
        return [dict(id=k,hook=True,pain=True,solution=True,link=True,natural=True,retention=True,reason='Checked') for k in server.FORMATS]
    def test_saving_name_rejected_for_purchase(self):
        self.assertTrue(server.creative_issues(dict(hook='Лоб блестит?',cta='Сохраните название'),dict(goal='Купить товар')))
    def test_long_intro_rejected(self):
        self.assertTrue(server.creative_issues(dict(hook='Покажу крем, которым пользуюсь уже не первый год',cta='Ссылку прикрепила'),{}))
    def test_quality_false_is_issue(self):
        quality=self.quality();quality[1]['retention']=False
        self.assertTrue(server.quality_issues({'quality':quality}))
    def test_link_without_url_allowed_when_planned(self):
        self.assertFalse(server.creative_issues(dict(hook='Лоб опять блестит?',cta='Ссылку прикрепила'),dict(goal='Купить',link_status='Прикреплю ссылку на этот товар')))
    def comparisons(self):
        return [dict(pair=p,distinct=True,reason='Different story') for p in ['direct/friend','direct/topic','friend/topic']]
    def test_pair_rejection_overrides_pass(self):
        comparisons=self.comparisons();comparisons[0]['distinct']=False
        responses=[dict(status='ready',facts=[],exclusions=[],questions=[]),self.routes(),{'concepts':self.items()},dict(status='pass',issues=[],comparisons=comparisons,quality=self.quality()),{'concepts':[self.items()[1]]},dict(status='pass',issues=[],comparisons=comparisons,quality=self.quality())]
        with patch.object(server,'ask',side_effect=responses):
            self.assertEqual(server.generate({})['status'],'needs_changes')

    def items(self):
        return [dict(id=k,title=k,hook='Hook '+k,main_idea='Idea '+k,development='Development',climax='Turn',cta='Look',filming='Hands',product_connection='Connection') for k in server.FORMATS]
    def test_three_formats_required(self):
        items=self.items();items[2]['id']='friend'
        with self.assertRaises(ValueError):server.validate_concepts(items)
    def test_repeated_idea_rejected(self):
        items=self.items();items[1]['main_idea']=items[0]['main_idea']
        with self.assertRaises(ValueError):server.validate_concepts(items)
    def test_batch_revised_once(self):
        research=dict(status='ready',facts=[],exclusions=[],questions=[])
        responses=[research,self.routes(),{'concepts':self.items()},{'status':'needs_changes','issues':['Different topics needed'],'comparisons':self.comparisons(),'quality':self.quality()},{'concepts':self.items()},{'status':'needs_changes','issues':['Still similar'],'comparisons':self.comparisons(),'quality':self.quality()}]
        with patch.object(server,'ask',side_effect=responses) as ask:
            result=server.generate({});self.assertEqual(result['status'],'needs_changes');self.assertEqual(ask.call_count,6)
    def test_expansion_preserves_choice(self):
        with patch.object(server,'generate_script',return_value={'status':'ready'}) as run:
            server.expand({'product':'Test'},self.items()[2])
            self.assertEqual(run.call_args.args[0]['tone'],server.FORMATS['topic'])
            self.assertIn('Connection',run.call_args.args[0]['chosen_concept'])

if __name__=='__main__':unittest.main()

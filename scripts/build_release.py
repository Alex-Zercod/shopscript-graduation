"""Build an explicit public file set; never recursively copy private docs."""
import hashlib,json
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parents[1]
FILES=['server.py','start.py','Открыть SHOPScript.cmd','.gitignore','README.md',
 'public/index.html','public/styles.css','public/app.js','public/example.json',
 'docs/USER-GUIDE.md','docs/RELEASE-GUIDE.md','examples/demo-brief.json','examples/demo-result.json','images/README.md',
 'images/01-demo-form.jpg','images/02-demo-concepts.jpg','images/03-demo-expanded.jpg',
 '.claude/skills/shopscript-maintenance/SKILL.md',
 'tests/test_server.py','tests/check_reviewer_live.py','scripts/build_release.py']

def main():
    output=ROOT/'release';output.mkdir(exist_ok=True)
    archive=output/'shopscript-graduation.zip'
    manifest=[]
    for name in FILES:
        data=(ROOT/name).read_bytes()
        manifest.append({'path':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for name in FILES:z.write(ROOT/name,name)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        assert set(z.namelist())==set(FILES)
        for item in manifest:assert hashlib.sha256(z.read(item['path'])).hexdigest()==item['sha256']
    (output/'manifest.json').write_text(json.dumps({'note':'Prepared locally, not published; demo run and screenshots recorded 2026-11-20; customer pilot pending.',
        'files':manifest},ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'Archive verified: {len(FILES)} files; {archive}')

if __name__=='__main__':main()

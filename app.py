import os, sqlite3, csv, io
from datetime import date, datetime
from flask import Flask, g, render_template, request, redirect, url_for, flash, send_file

ROOT = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(ROOT, 'smart_wastewater.db')
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'student-demo-secret-change-before-deployment')
PARAMS = {
 'ph': ('pH', '', 6.5, 8.5, 'pH adjustment / neutralization; confirm with a qualified operator.'),
 'turbidity': ('Turbidity', 'NTU', 0, 10, 'Coagulation and filtration may help reduce suspended particles.'),
 'cod': ('COD', 'mg/L', 0, 250, 'Evaluate biological treatment or advanced oxidation for the wastewater characteristics.'),
 'bod': ('BOD', 'mg/L', 0, 30, 'Evaluate biological treatment and process conditions.'),
 'tds': ('TDS', 'mg/L', 0, 500, 'Evaluate a suitable dissolved-solids reduction process.'),
 'ec': ('Electrical Conductivity', 'µS/cm', 0, 1500, 'Investigate dissolved salts and suitable salt-control methods.'),
 'do_value': ('Dissolved Oxygen', 'mg/L', 3, 100, 'Aeration may increase dissolved oxygen where appropriate.'),
 'tss': ('Total Suspended Solids', 'mg/L', 0, 20, 'Evaluate clarification and tertiary filtration.'),
 'temperature': ('Temperature', '°C', 25, 30, 'Monitor process temperature; maintain suitable biological-treatment conditions.'),
 'influent_flow': ('Influent flow', 'm³/day', 0, 100000, 'Use flow equalization and verify hydraulic loading.'),
 'mlss': ('MLSS', 'mg/L', 0, 10000, 'Monitor biomass concentration and settleability.'),
 'mlvss': ('MLVSS', 'mg/L', 0, 10000, 'Monitor active biomass fraction.'),
 'aeration_time': ('Aeration time', 'hours', 0, 48, 'Adjust aeration based on process performance and DO.'),
 'ras_percent': ('RAS flow', '% of influent', 0, 500, 'Adjust return activated sludge flow based on settling and biomass control.'),
 'srt': ('Sludge retention time (SRT)', 'days', 0, 60, 'Control sludge wasting to maintain target SRT.'),
 'hrt': ('Hydraulic retention time (HRT)', 'hours', 0, 48, 'Check tank volume and hydraulic loading.'),
 'air_flow': ('Air flow', 'm³/hour', 0, 100000, 'Adjust air supply to maintain the aeration-tank DO target.'),
 'oil_grease': ('Oil & grease', 'mg/L', 0, 10, 'Provide oil and grease separation where indicated by testing.'),
 'ammonia_n': ('Ammonia-N', 'mg/L', 0, 5, 'Evaluate nitrification and biological process conditions.'),
 'total_nitrogen': ('Total nitrogen', 'mg/L', 0, 10, 'Evaluate biological nutrient-removal requirements.'),
 'total_phosphorus': ('Total phosphorus', 'mg/L', 0, 2, 'Evaluate phosphorus removal where required.'),
 'phosphate': ('Phosphate', 'mg/L', 0, 2, 'Evaluate phosphorus removal where required.'),
 'alkalinity': ('Alkalinity', 'mg/L as CaCO₃', 0, 300, 'Monitor alkalinity to support biological treatment and nitrification.'),
 'total_coliform': ('Total coliform', 'MPN/100 mL', 0, 1000, 'Microbiological testing and validated disinfection are required.'),
 'ecoli': ('E. coli', 'MPN/100 mL', 0, 1000, 'Microbiological testing and validated disinfection are required.')
}

OPTIONAL_PARAMS = {'tss','temperature','influent_flow','mlss','mlvss','aeration_time','ras_percent','srt','hrt','air_flow','oil_grease','ammonia_n','total_nitrogen','total_phosphorus','phosphate','alkalinity','total_coliform','ecoli'}
DESIGN_DEFAULTS = {
 'ph':7.2, 'turbidity':150, 'cod':500, 'bod':250, 'tds':700, 'ec':None,
 'do_value':2, 'tss':300, 'temperature':28, 'influent_flow':540,
 'mlss':3000, 'mlvss':2400, 'aeration_time':7, 'ras_percent':75,
 'srt':12, 'hrt':7, 'air_flow':None, 'oil_grease':50, 'ammonia_n':30, 'total_nitrogen':40, 'total_phosphorus':7, 'phosphate':5, 'alkalinity':150, 'total_coliform':1000000, 'ecoli':100000
}


def connect_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA foreign_keys=ON')
    return g.db

@app.teardown_appcontext
def close_db(exc=None):
    db = g.pop('db', None)
    if db is not None: db.close()

def init_db():
    db = sqlite3.connect(DB_PATH)
    db.executescript('''
    CREATE TABLE IF NOT EXISTS samples(id INTEGER PRIMARY KEY AUTOINCREMENT, sample_code TEXT UNIQUE NOT NULL, source TEXT NOT NULL, collection_date TEXT NOT NULL, notes TEXT DEFAULT '', created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS lab_results(id INTEGER PRIMARY KEY AUTOINCREMENT, sample_id INTEGER NOT NULL REFERENCES samples(id) ON DELETE CASCADE, stage TEXT NOT NULL CHECK(stage IN ('before','after')), ph REAL NOT NULL, turbidity REAL NOT NULL, cod REAL NOT NULL, bod REAL NOT NULL, tds REAL NOT NULL, ec REAL NOT NULL, do_value REAL NOT NULL, test_date TEXT NOT NULL,
      tss REAL, temperature REAL, influent_flow REAL, mlss REAL, mlvss REAL,
      aeration_time REAL, ras_percent REAL, srt REAL, hrt REAL, air_flow REAL, oil_grease REAL, ammonia_n REAL, total_nitrogen REAL, total_phosphorus REAL, phosphate REAL, alkalinity REAL, total_coliform REAL, ecoli REAL,
      UNIQUE(sample_id,stage));
    CREATE TABLE IF NOT EXISTS treatment_records(id INTEGER PRIMARY KEY AUTOINCREMENT, sample_id INTEGER NOT NULL REFERENCES samples(id) ON DELETE CASCADE, recommendation TEXT NOT NULL, notes TEXT DEFAULT '', created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS reuse_plans(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      sample_id INTEGER NOT NULL UNIQUE REFERENCES samples(id) ON DELETE CASCADE,
      application TEXT NOT NULL, estimated_volume TEXT DEFAULT '',
      frequency TEXT DEFAULT '', location TEXT DEFAULT '', safeguards TEXT DEFAULT '',
      approval_status TEXT NOT NULL DEFAULT 'Pending qualified review',
      updated_at TEXT NOT NULL
    );
    ''')
    # Backward-compatible migration: preserve existing user databases and records.
    existing = {row[1] for row in db.execute('PRAGMA table_info(lab_results)').fetchall()}
    for column in ('tss','temperature','influent_flow','mlss','mlvss','aeration_time','ras_percent','srt','hrt','air_flow','oil_grease','ammonia_n','total_nitrogen','total_phosphorus','phosphate','alkalinity','total_coliform','ecoli'):
        if column not in existing:
            db.execute(f'ALTER TABLE lab_results ADD COLUMN {column} REAL')
    db.commit(); db.close()

def get_values(form):
    vals = {}
    for key, spec in PARAMS.items():
        raw = form.get(key, '').strip()
        if not raw and key in OPTIONAL_PARAMS:
            vals[key] = None
            continue
        if not raw: raise ValueError(f"Please enter {spec[0]}.")
        try: val = float(raw)
        except ValueError: raise ValueError(f"{spec[0]} must be numeric.")
        if val < 0: raise ValueError(f"{spec[0]} cannot be negative.")
        if key == 'ph' and val > 14: raise ValueError('pH must be between 0 and 14.')
        vals[key] = val
    return vals

def analyse(vals):
    output=[]
    for key, (label, unit, low, high, treatment) in PARAMS.items():
        value=vals.get(key)
        if value is None:
            continue
        ok=low <= value <= high
        output.append({'key':key,'label':label,'unit':unit,'value':value,'low':low,'high':high,'ok':ok,'treatment': '' if ok else treatment})
    return output

def values_from_row(row):
    return {k: row[k] for k in PARAMS if k in row.keys()} if row else None

def recommend_reuse(before_vals, after_vals):
    """Compare pre/post readings and screen possible reuse options; not an approval."""
    if not after_vals:
        return None
    # Illustrative academic screening criteria, not universal regulatory limits.
    criteria = [
      {'name':'Landscape / ornamental plant irrigation','checks':{'ph':(6.0,8.5),'turbidity':(0,5),'bod':(0,10),'cod':(0,100),'tds':(0,1000),'ec':(0,1500),'do_value':(2,100)},'note':'Potentially consider for non-food ornamental landscaping only after microbiological tests and local review.'},
      {'name':'Road cleaning / dust suppression','checks':{'ph':(6.0,9.0),'turbidity':(0,10),'bod':(0,30),'cod':(0,250),'tds':(0,2000),'ec':(0,3000),'do_value':(0,100)},'note':'Consider only with suitable exposure/runoff controls and local review.'},
      {'name':'Toilet flushing (additional treatment required)','checks':{'ph':(6.5,8.5),'turbidity':(0,2),'bod':(0,10),'cod':(0,50),'tds':(0,500),'ec':(0,1000),'do_value':(2,100)},'note':'Cannot be approved by these readings alone; validated disinfection, microbiological tests, plumbing safeguards and regulatory approval are essential.'},
    ]
    results=[]
    for category in criteria:
        failed=[]
        for key,(low,high) in category['checks'].items():
            value=after_vals[key]
            if not low <= value <= high:
                failed.append(f"{PARAMS[key][0]} ({value:g}; screening range {low:g}–{high:g})")
        results.append({'name':category['name'],'suitable':not failed,'failed':failed,'note':category['note']})
    recommended=next((r for r in results if r['suitable'] and r['name'].startswith('Landscape')),None)
    if not recommended:
        recommended=next((r for r in results if r['suitable'] and r['name'].startswith('Road cleaning')),None)
    improvement=[]
    if before_vals:
        for key in ('turbidity','bod','cod','tds','ec'):
            b,a=before_vals[key],after_vals[key]
            improvement.append({'label':PARAMS[key][0],'before':b,'after':a,'pct':((b-a)/b*100 if b else None),'improved':a <= b})
    return {'categories':results,'recommended':recommended,'improvement':improvement,
      'headline':(f"Potential match: {recommended['name']}" if recommended else 'No reuse application meets the configured screening criteria'),
      'caution':'Automated preliminary screening only. The project does not measure pathogens, metals or all use-specific contaminants. This result is not permission to reuse water.'}

@app.route('/')
def dashboard():
    db=connect_db()
    stats={'samples':db.execute('SELECT COUNT(*) FROM samples').fetchone()[0], 'before':db.execute("SELECT COUNT(*) FROM lab_results WHERE stage='before'").fetchone()[0], 'after':db.execute("SELECT COUNT(*) FROM lab_results WHERE stage='after'").fetchone()[0], 'treatments':db.execute('SELECT COUNT(*) FROM treatment_records').fetchone()[0]}
    recent=db.execute('''SELECT s.*, (SELECT COUNT(*) FROM lab_results r WHERE r.sample_id=s.id AND r.stage='before') hb, (SELECT COUNT(*) FROM lab_results r WHERE r.sample_id=s.id AND r.stage='after') ha FROM samples s ORDER BY id DESC LIMIT 6''').fetchall()
    return render_template('index.html', stats=stats, recent=recent)

@app.route('/samples/new', methods=['GET','POST'])
def new_sample():
    if request.method=='POST':
        code=request.form.get('sample_code','').strip(); source=request.form.get('source','').strip(); dt=request.form.get('collection_date','').strip(); notes=request.form.get('notes','').strip()
        if not code or not source or not dt:
            flash('Sample ID, source, and collection date are required.','error')
        else:
            try:
                db=connect_db(); cur=db.execute('INSERT INTO samples(sample_code,source,collection_date,notes,created_at) VALUES(?,?,?,?,?)',(code,source,dt,notes,datetime.now().isoformat(timespec='seconds'))); db.commit()
                flash('Sample created. Enter the pre-treatment laboratory values.','success'); return redirect(url_for('lab_entry', sample_id=cur.lastrowid, stage='before'))
            except sqlite3.IntegrityError: flash('Sample ID already exists. Use a unique ID.','error')
    return render_template('sample_form.html', today=date.today().isoformat())

@app.route('/samples/<int:sample_id>/lab/<stage>', methods=['GET','POST'])
def lab_entry(sample_id, stage):
    if stage not in ('before','after'): return redirect(url_for('dashboard'))
    db=connect_db(); sample=db.execute('SELECT * FROM samples WHERE id=?',(sample_id,)).fetchone()
    if not sample: flash('Sample not found.','error'); return redirect(url_for('history'))
    existing=db.execute('SELECT * FROM lab_results WHERE sample_id=? AND stage=?',(sample_id,stage)).fetchone()
    if stage=='after' and not db.execute("SELECT id FROM lab_results WHERE sample_id=? AND stage='before'",(sample_id,)).fetchone():
        flash('Enter pre-treatment results before post-treatment results.','error'); return redirect(url_for('lab_entry',sample_id=sample_id,stage='before'))
    if request.method=='POST':
        try:
            vals=get_values(request.form); test_date=request.form.get('test_date') or date.today().isoformat()
            db.execute('''INSERT INTO lab_results(
            sample_id,stage,ph,turbidity,cod,bod,tds,ec,do_value,test_date,
            tss,temperature,influent_flow,mlss,mlvss,aeration_time,ras_percent,srt,hrt,air_flow,
            oil_grease,ammonia_n,total_nitrogen,total_phosphorus,phosphate,alkalinity,total_coliform,ecoli)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(sample_id,stage) DO UPDATE SET
            ph=excluded.ph,turbidity=excluded.turbidity,cod=excluded.cod,bod=excluded.bod,tds=excluded.tds,ec=excluded.ec,
            do_value=excluded.do_value,test_date=excluded.test_date,tss=excluded.tss,temperature=excluded.temperature,
            influent_flow=excluded.influent_flow,mlss=excluded.mlss,mlvss=excluded.mlvss,aeration_time=excluded.aeration_time,
            ras_percent=excluded.ras_percent,srt=excluded.srt,hrt=excluded.hrt,air_flow=excluded.air_flow,
            oil_grease=excluded.oil_grease,ammonia_n=excluded.ammonia_n,total_nitrogen=excluded.total_nitrogen,
            total_phosphorus=excluded.total_phosphorus,phosphate=excluded.phosphate,alkalinity=excluded.alkalinity,
            total_coliform=excluded.total_coliform,ecoli=excluded.ecoli''',
            (sample_id,stage,vals['ph'],vals['turbidity'],vals['cod'],vals['bod'],vals['tds'],vals['ec'],vals['do_value'],test_date,
             vals.get('tss'),vals.get('temperature'),vals.get('influent_flow'),vals.get('mlss'),vals.get('mlvss'),
             vals.get('aeration_time'),vals.get('ras_percent'),vals.get('srt'),vals.get('hrt'),vals.get('air_flow'),
             vals.get('oil_grease'),vals.get('ammonia_n'),vals.get('total_nitrogen'),vals.get('total_phosphorus'),
             vals.get('phosphate'),vals.get('alkalinity'),vals.get('total_coliform'),vals.get('ecoli')))
            if stage=='before':
                flags=analyse(vals); rec='\n'.join(f"{x['label']}: {x['treatment']}" for x in flags if not x['ok']) or 'All values fall within the configured demo ranges; confirm all applicable reuse requirements.'
                db.execute('INSERT INTO treatment_records(sample_id,recommendation,notes,created_at) VALUES(?,?,?,?)',(sample_id,rec,'Rule-based recommendation only; validate with qualified wastewater professionals.',datetime.now().isoformat(timespec='seconds')))
            db.commit(); flash(('Pre-treatment' if stage=='before' else 'Post-treatment')+' results saved.','success'); return redirect(url_for('sample_detail',sample_id=sample_id))
        except ValueError as e: flash(str(e),'error')
    defaults=values_from_row(existing) if existing else (DESIGN_DEFAULTS.copy() if stage=='before' else {})
    if stage=='after' and not defaults:
        before=db.execute("SELECT * FROM lab_results WHERE sample_id=? AND stage='before'",(sample_id,)).fetchone(); defaults=values_from_row(before) or {}
    return render_template('lab_form.html',sample=sample,stage=stage,params=PARAMS,defaults=defaults,today=date.today().isoformat(),optional_params=OPTIONAL_PARAMS)

@app.route('/samples/<int:sample_id>')
def sample_detail(sample_id):
    db=connect_db(); sample=db.execute('SELECT * FROM samples WHERE id=?',(sample_id,)).fetchone()
    if not sample: flash('Sample not found.','error'); return redirect(url_for('history'))
    before=db.execute("SELECT * FROM lab_results WHERE sample_id=? AND stage='before'",(sample_id,)).fetchone(); after=db.execute("SELECT * FROM lab_results WHERE sample_id=? AND stage='after'",(sample_id,)).fetchone()
    treatments=db.execute('SELECT * FROM treatment_records WHERE sample_id=? ORDER BY id DESC',(sample_id,)).fetchall()
    bf=analyse(values_from_row(before)) if before else []; af=analyse(values_from_row(after)) if after else []; comparison=[]
    if before and after:
        for key,(label,unit,low,high,treat) in PARAMS.items():
            b=before[key]; a=after[key]
            if b is None or a is None: continue
            pct=((b-a)/abs(b)*100) if b != 0 else None
            comparison.append({'label':label,'unit':unit,'before':b,'after':a,'change':a-b,'pct':pct})
    reuse='REVIEW REQUIRED' if after and any(not x['ok'] for x in af) else ('REFERENCE RANGES MET — FINAL APPROVAL REQUIRED' if after else None)
    reuse_assessment=recommend_reuse(values_from_row(before) if before else None, values_from_row(after) if after else None)
    return render_template('sample_detail.html',sample=sample,before=before,after=after,bf=bf,af=af,comparison=comparison,treatments=treatments,reuse=reuse,reuse_assessment=reuse_assessment)

@app.route('/samples/<int:sample_id>/treatment-note', methods=['POST'])
def treatment_note(sample_id):
    note=request.form.get('notes','').strip()
    if note:
        db=connect_db(); db.execute('INSERT INTO treatment_records(sample_id,recommendation,notes,created_at) VALUES(?,?,?,?)',(sample_id,'Treatment performed / operator note',note,datetime.now().isoformat(timespec='seconds'))); db.commit(); flash('Treatment note saved.','success')
    return redirect(url_for('sample_detail',sample_id=sample_id))

@app.route('/history')
def history():
    q=request.args.get('q','').strip(); db=connect_db()
    sql='''SELECT s.*, (SELECT COUNT(*) FROM lab_results r WHERE r.sample_id=s.id AND r.stage='before') hb, (SELECT COUNT(*) FROM lab_results r WHERE r.sample_id=s.id AND r.stage='after') ha FROM samples s'''
    if q: rows=db.execute(sql+' WHERE sample_code LIKE ? OR source LIKE ? ORDER BY id DESC',(f'%{q}%',f'%{q}%')).fetchall()
    else: rows=db.execute(sql+' ORDER BY id DESC').fetchall()
    return render_template('history.html',samples=rows,q=q)

@app.route('/export.csv')
def export_csv():
    db=connect_db(); rows=db.execute('''SELECT s.sample_code,s.source,s.collection_date,r.stage,r.test_date,r.ph,r.turbidity,r.cod,r.bod,r.tds,r.ec,r.do_value,r.tss,r.temperature,r.influent_flow,r.mlss,r.mlvss,r.aeration_time,r.ras_percent,r.srt,r.hrt,r.air_flow,r.oil_grease,r.ammonia_n,r.total_nitrogen,r.total_phosphorus,r.phosphate,r.alkalinity,r.total_coliform,r.ecoli FROM samples s LEFT JOIN lab_results r ON s.id=r.sample_id ORDER BY s.id DESC,r.id''').fetchall()
    out=io.StringIO(); w=csv.writer(out); w.writerow(['Sample ID','Source','Collection date','Stage','Test date','pH','Turbidity NTU','COD mg/L','BOD mg/L','TDS mg/L','EC µS/cm','DO mg/L','TSS mg/L','Temperature C','Influent flow m3/day','MLSS mg/L','MLVSS mg/L','Aeration time h','RAS percent','SRT days','HRT hours','Air flow m3/hour','Oil and grease mg/L','Ammonia-N mg/L','Total nitrogen mg/L','Total phosphorus mg/L','Phosphate mg/L','Alkalinity mg/L as CaCO3','Total coliform MPN/100mL','E. coli MPN/100mL'])
    for r in rows: w.writerow([r[k] for k in ['sample_code','source','collection_date','stage','test_date','ph','turbidity','cod','bod','tds','ec','do_value','tss','temperature','influent_flow','mlss','mlvss','aeration_time','ras_percent','srt','hrt','air_flow','oil_grease','ammonia_n','total_nitrogen','total_phosphorus','phosphate','alkalinity','total_coliform','ecoli']])
    return send_file(io.BytesIO(('\ufeff'+out.getvalue()).encode('utf-8')),mimetype='text/csv',as_attachment=True,download_name='wastewater_report.csv')

@app.route('/about')
def about(): return render_template('about.html')

with app.app_context(): init_db()
if __name__=='__main__': app.run(debug=True)

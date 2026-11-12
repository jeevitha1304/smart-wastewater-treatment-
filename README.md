# Smart Wastewater Treatment and Reuse System

A working student-project web app using Python, Flask, SQLite, HTML, CSS and JavaScript. Features: sample registration, lab-result entry, rule-based parameter checks, treatment recommendations, post-treatment results, before/after comparison, automatic reuse-application screening based on pre/post values, history search and CSV export.

## Important limitations
- This is a decision-support prototype. It does not physically treat wastewater or control equipment.
- Built-in parameter ranges are demonstration defaults, not universal regulatory limits.
- Meeting these ranges does not certify water as safe for reuse. Follow applicable local standards, required tests, and qualified professional approval.
- Treatment suggestions are preliminary and depend on wastewater characteristics.

## Run on Windows from scratch
1. Extract the ZIP file to a folder, for example `Desktop\smart_wastewater_complete_project`.
2. Install Python 3.10+ from https://www.python.org/downloads/. During setup, enable **Add Python to PATH**.
3. Open the extracted folder in File Explorer. Click the address bar, type `cmd`, and press Enter.
4. Create a virtual environment:
   ```bat
   python -m venv venv
   ```
5. Activate it in Command Prompt:
   ```bat
   venv\Scripts\activate
   ```
6. Install the required package:
   ```bat
   python -m pip install -r requirements.txt
   ```
7. Start the web app:
   ```bat
   python app.py
   ```
8. Open your browser at **http://127.0.0.1:5000**.
9. Keep Command Prompt open while using the app. Press `Ctrl+C` there to stop the server.

## First demo flow
1. Click **Create New Sample** and create an ID such as `WW-001`.
2. Enter pre-treatment lab measurements (use actual lab values; clearly label demo values in a presentation).
3. Review the parameter checks and treatment suggestions.
4. Record the treatment actually performed in the treatment notes.
5. Enter post-treatment values after retesting the treated sample.
6. Review the before/after comparison and preliminary reuse screen.
7. Use Sample History to search records or export a CSV report.

## Database
SQLite database `smart_wastewater.db` is created automatically in this folder. Keep the file to preserve records. To reset the demo data, stop the app and delete this database file; it will be recreated on the next run.

## Troubleshooting
- `python is not recognized`: install Python with Add Python to PATH enabled and reopen Command Prompt.
- `No module named flask`: activate `venv` and run `python -m pip install -r requirements.txt`.
- Port 5000 busy: change the last line in `app.py` to `app.run(debug=True, port=5001)` and visit `http://127.0.0.1:5001`.
- This development server is for local academic demonstrations, not public production deployment.


## Automatic reuse application recommendation
After post-treatment values are saved, the app compares the post-treatment measurements with configured screening criteria and uses the pre-treatment values to show reductions. It automatically identifies a potential application such as landscape/ornamental irrigation or road cleaning/dust suppression, or reports that no option meets the configured criteria. Users do not manually select or save a reuse application.

The current rule set screens pH, turbidity, BOD, COD, TDS, electrical conductivity and dissolved oxygen. Criteria are illustrative academic demo values, not universal reuse standards. The prototype does not test pathogens, metals or every use-specific contaminant, so a match is not a safety certification or permission to reuse water. Required laboratory tests, local standards and qualified review remain essential.


### Where to find automatic reuse recommendation
Open a sample record after saving **both** pre-treatment and post-treatment results. Scroll below the **Post-treatment analysis** table to the highlighted **Automatic Reuse Application Recommendation** panel. It is calculated automatically from post-treatment measurements and shows before/after changes when both stages are available. No manual reuse selection is required. If no category passes the configured screening rules, the panel reports that no application matches.


## Added design-input and graph features (from the supplied project data)
- The pre-treatment input form is prefilled with the example AI/design values from the accompanying data document: influent flow 540 m³/day, BOD 250 mg/L, COD 500 mg/L, TSS 300 mg/L, pH 7.2, temperature 28 °C, aeration DO 2 mg/L, MLSS 3,000 mg/L, MLVSS 2,400 mg/L, aeration time 7 h (within 6–8 h), RAS 75% (within 50–100%), SRT 12 days (within 10–15 days), and HRT 7 h (within 6–8 h). Air flow is left blank because the document specifies it as a DO-controlled value rather than a numeric flow. Influent water-quality defaults also include oil & grease 50 mg/L, ammonia-N 30 mg/L, total nitrogen 40 mg/L, total phosphorus 7 mg/L, phosphate 5 mg/L, alkalinity 150 mg/L as CaCO₃, total coliform 10⁶–10⁷ MPN/100 mL and E. coli 10⁵–10⁶ MPN/100 mL.
- Added optional process-input fields for TSS, temperature, influent flow, MLSS, MLVSS, aeration time, RAS percentage, SRT, HRT, air flow, oil & grease, ammonia-N, total nitrogen, total phosphorus, phosphate, alkalinity, total coliform and E. coli. Existing required laboratory fields and existing functions remain.
- Sample detail now includes a pre/post treatment bar graph, a final treated-water quality vs project-target graph, and an estimated reuse/freshwater-saving graph. The final target graph uses the document's upper display targets (BOD 20, COD 50, TSS 20 mg/L and turbidity 5 NTU).
- Reuse estimate uses the document's 80–90% of influent flow and 450–500 m³/day design example. The displayed calculation is a planning estimate based on the entered influent flow, not a measured reuse volume.
- The database automatically adds the new optional columns to an existing SQLite database; existing sample records are retained. CSV export includes the new fields.

The supplied design basis states 5,000 persons, water use 135 L/person/day, wastewater generation 108 L/person/day, average flow 540 m³/day, design flow 600 m³/day and peak flow 1,500 m³/day. The suggested treatment train is screening, grit removal, equalization, primary settling, biological treatment, secondary clarification, tertiary filtration, disinfection, treated-water storage and reuse. These remain design references in the project and should be checked by the project engineer before real design or operation.

"""Exact source changes for final browser acceptance; no workflow edits."""
from pathlib import Path
import os
if os.environ.get('GITHUB_REF_NAME')!='feat/latent-comparison-phase-a':raise SystemExit('Wrong branch')
def patch(file,old,new):
 p=Path(file);text=p.read_text();assert text.count(old)==1,(file,old);p.write_text(text.replace(old,new))
patch('tools/test_meeting_picker_ui.cjs',"assert.equal(await page.locator('#individualMeeting option').last().isDisabled(),true)","assert.equal(await page.locator('#individualMeeting option[value=\"asset/test/pending\"]').evaluate(o=>o.disabled),true,await page.locator('#individualMeeting').evaluate(s=>JSON.stringify(Array.from(s.options,o=>({value:o.value,disabled:o.disabled,text:o.textContent})))))")
patch('site/latent.css','white-space:nowrap}td','white-space:normal}td')
patch('docs/BROWSER_ANALYSIS.md','Current browser version: **1.11.0**.','Current browser version: **1.12.0**. Select **One individual meeting**, enter its date, and choose from the returned meeting list to analyze just that meeting. See [individual-meeting analysis](INDIVIDUAL_MEETINGS.md). The [latent comparison workspace](LATENT_COMPARISON.md) adds saved-run replay, parent/excerpt comparisons and reusable settings.\n\n')
patch('README.md','# UNGA81 Transcript Agent\n','# UNGA81 Transcript Agent\n\n**Individual meetings:** choose **One individual meeting**, enter its date, select a meeting, and generate the existing source-linked analysis and report. See the [meeting selector guide](docs/INDIVIDUAL_MEETINGS.md).\n')
print('Updated explicit option-state acceptance, table wrapping and current user guides.')

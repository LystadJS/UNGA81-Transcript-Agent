/* One-action browser acceptance. Synthetic sources only; no live or reserved transcripts. */
'use strict';
const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),assert=require('node:assert/strict');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');

(async()=>{
  const [site='site',out='work/daily-summary-generation-browser']=process.argv.slice(2);
  fs.mkdirSync(out,{recursive:true});let server,browser,url=site;
  try{
    if(!/^https?:/.test(site)){
      const root=path.resolve(site);server=http.createServer((req,res)=>{
        const file=path.resolve(root,'.'+decodeURIComponent(req.url.split('?')[0]).replace(/\/$/,'/index.html'));
        if(!file.startsWith(root+path.sep)){res.writeHead(403).end();return;}
        try{res.setHeader('Content-Type',({'.js':'text/javascript','.json':'application/json','.css':'text/css','.html':'text/html','.csv':'text/csv'})[path.extname(file)]||'application/octet-stream');res.end(fs.readFileSync(file));}
        catch{res.writeHead(404).end();}
      });await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));url='http://127.0.0.1:'+server.address().port+'/';
    }
    if(!url.endsWith('/'))url+='/';
    browser=await chromium.launch({headless:true,...(process.env.BROWSER_PATH?{executablePath:process.env.BROWSER_PATH}:process.env.PW_CHANNEL?{channel:process.env.PW_CHANNEL}:{})});
    const page=await browser.newPage({viewport:{width:1440,height:1000},acceptDownloads:true}),errors=[],sourceRequests=[],transcriptRequests=[];
    page.on('pageerror',error=>errors.push(error.message));
    const date='2026-11-04';
    const meetings=[
      {slug:'ga/81/42',title:'General Assembly plenary — synthetic fixture',date,pageUrl:'/en/ga/81/42',jsonUrl:'/en/ga/81/42.json',hasTranscript:true},
      {slug:'sc/81/10021',title:'Security Council — synthetic fixture',date,pageUrl:'/en/sc/81/10021',jsonUrl:'/en/sc/81/10021.json',hasTranscript:true}
    ];
    const texts={
      'ga/81/42':[
        ['KEN','We call for an immediate ceasefire in Gaza and support unhindered humanitarian access through all crossings.'],
        ['FRA','We propose a new climate finance facility and binding national emissions reductions by 2035.']
      ],
      'sc/81/10021':[
        ['USA','We demand an immediate cessation of hostilities in Gaza. The parties signed a monitored ceasefire in Gaza today.'],
        ['KEN','We oppose a ceasefire that omits hostage release, while supporting protected humanitarian access for relief convoys.']
      ]
    };
    await page.route('https://transcripts.un.org/**',async route=>{
      const requestURL=new URL(route.request().url());sourceRequests.push(requestURL.pathname);let data;
      if(requestURL.pathname==='/en/meetings.json')data={page:1,total:meetings.length,hasMore:false,meetings};
      else{
        const meeting=meetings.find(item=>item.jsonUrl===requestURL.pathname);assert.ok(meeting,'Unexpected transcript request: '+requestURL.pathname);transcriptRequests.push(requestURL.pathname);
        data={video:{slug:meeting.slug,date},transcript:{language:'en',data:texts[meeting.slug].map(([affiliation,text],index)=>({speaker:{affiliation},pageUrl:meeting.pageUrl+'?t='+index,paragraphs:[{sentences:[{text}]}]}))}};
      }
      await route.fulfill({status:200,contentType:'application/json',headers:{'access-control-allow-origin':'*'},body:JSON.stringify(data)});
    });

    await page.goto(url+'index.html#analyze');
    await page.waitForFunction(()=>document.querySelector('#region').options.length>2);
    await page.locator('#startDate').fill(date);await page.locator('#endDate').fill(date);
    await page.locator('#topic').fill('');await page.locator('#meetingScope').selectOption('all');
    assert.equal(await page.locator('#advancedMethods').evaluate(element=>element.open),false,'Advanced methods must default closed');
    await page.evaluate(()=>{globalThis.__dailyGenerationClicks=0;document.querySelector('#runAnalysis').addEventListener('click',()=>globalThis.__dailyGenerationClicks++);});

    await page.locator('#runAnalysis').click();
    await page.locator('#analysisOutput').waitFor({state:'visible',timeout:90000});
    assert.equal(await page.evaluate(()=>globalThis.__dailyGenerationClicks),1,'Exactly one Generate report action is allowed');
    assert.deepEqual(new Set(transcriptRequests),new Set(meetings.map(item=>item.jsonUrl)));
    assert.equal(await page.locator('#advancedMethods').evaluate(element=>element.open),false,'Generation must not open advanced methods');

    const summary=page.locator('#daySummary');await summary.waitFor({state:'visible'});
    assert.match(await summary.innerText(),/Substantive topics/);assert.match(await summary.innerText(),/Consequential developments across the day/);
    assert.equal(await summary.locator('.automatic-chart').count(),3);
    for(const heading of ['Topic distribution','Topic by country','Meeting by topic'])assert.equal(await summary.getByRole('heading',{name:heading,exact:true}).count(),1);
    assert.match(await summary.innerText(),/Counts: distinct supporting passages/);
    assert.match(await summary.innerText(),/recorded country participation \(binary presence\)/);
    assert.equal(await summary.locator('.automatic-chart figure').count(),3,'All default charts must render, not an insufficient-data placeholder');
    assert.equal(await summary.getByText('Readable table alternative',{exact:true}).count(),3);
    assert.equal(await summary.getByText(/source drill-down$/).count(),3);
    assert.ok(await summary.locator('.automatic-chart details table').count()>=3,'Each chart needs a table alternative');
    assert.ok(await summary.locator('.automatic-chart details a[href^="https://transcripts.un.org/"]').count()>=3,'Each chart needs source drill-down links');
    assert.match(await summary.innerText(),/Each country counts at most once per topic/);
    assert.match(await summary.innerText(),/Exact repeated passage wording counts once/);

    const save=async(id,name)=>{const [download]=await Promise.all([page.waitForEvent('download'),page.locator('#'+id).click()]);const target=path.join(out,name);await download.saveAs(target);return fs.readFileSync(target);};
    const savedJSON=JSON.parse(await save('exportResult','daily-summary-analysis.json'));
    assert.equal(savedJSON.day_summary.date,date);assert.equal(savedJSON.day_summary.meetings.length,2);assert.ok(savedJSON.day_summary.topics.length>=3);
    assert.deepEqual(Object.keys(savedJSON.day_summary.visualizations).sort(),['meeting_topic_overview','topic_country_matrix','topic_distribution']);
    assert.ok(Object.values(savedJSON.day_summary.visualizations).every(chart=>chart.status==='available'));
    const renderedText=await summary.innerText();for(const topic of savedJSON.day_summary.topics)assert.match(renderedText,new RegExp(topic.label.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')));
    const standalone=(await save('exportHTML','daily-summary-report.html')).toString('utf8');
    assert.match(standalone,/id="daySummary"/);assert.match(standalone,/Automatic visualizations/);
    for(const heading of ['Topic distribution','Topic by country','Meeting by topic'])assert.ok(standalone.includes(heading));
    assert.equal((standalone.match(/Readable table alternative/g)||[]).length,3);assert.equal((standalone.match(/source drill-down/g)||[]).length,3);
    assert.ok((standalone.match(/https:\/\/transcripts\.un\.org\//g)||[]).length>=3);assert.doesNotMatch(standalone,/<script\b/i);
    assert.equal(await page.evaluate(()=>globalThis.__dailyGenerationClicks),1,'Exports must not trigger another analysis action');
    assert.deepEqual(new Set(sourceRequests),new Set(['/en/meetings.json',...meetings.map(item=>item.jsonUrl)]),'Only synthetic routed inventory and transcript fixture paths may be requested');

    await page.screenshot({path:path.join(out,'daily-summary-desktop.png'),fullPage:true});
    await page.setViewportSize({width:390,height:844});
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+2),true);
    await page.screenshot({path:path.join(out,'daily-summary-mobile.png'),fullPage:true});
    assert.deepEqual(errors,[]);
    const receipt={status:'PASS',synthetic_only:true,generation_actions:1,required_outputs:['browser_daily_summary','saved_analysis_json','standalone_script_free_html'],saved_json_parity:true,standalone_html_parity:true,meetings:2,meeting_types:['General Assembly plenary','Security Council'],automatic_charts:3,table_alternatives:3,source_drilldowns:3,advanced_controls_default:'collapsed',mobile_overflow:false,browser:browser.version(),source_guarantee:{network_fulfillment:'intercepted_synthetic_responses_only',requested_paths:[...new Set(sourceRequests)].sort(),live_transcripts_opened:0,reserved_dates_requested:0,reserved_transcripts_opened:0},errors};
    fs.writeFileSync(path.join(out,'validation.json'),JSON.stringify(receipt,null,2));console.log(JSON.stringify(receipt));
  }finally{
    if(browser)await browser.close();if(server)await new Promise(resolve=>server.close(resolve));
  }
})().catch(error=>{console.error(error);process.exitCode=1;});

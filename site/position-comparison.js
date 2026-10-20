/* Local explicit-policy comparison. No sentiment, embeddings, votes or carry-forward. */
(function(root){
'use strict';
const T=typeof module!=='undefined'&&module.exports?require('./text-units.js'):root.UNTextUnits;
const P=typeof module!=='undefined'&&module.exports?require('./passage-labels.js'):root.UNPassageLabels;
const POLICIES=[
 {id:'humanitarian_access',label:'Allow humanitarian access',target:/\b(?:humanitarian access|aid access|(?:unhindered|unimpeded|unrestricted|safe) (?:delivery|provision|distribution) of humanitarian (?:aid|assistance))\b/i},
 {id:'civilian_protection',label:'Protect civilians',target:/\b(?:protect(?:ing)? civilians|protection of civilians|civilian protection)\b/i},
 {id:'ceasefire',label:'Establish a ceasefire',target:/\b(?:ceasefire|cessation of hostilities)\b/i},
 {id:'two_state',label:'A two-state solution',target:/\btwo[ -]state solutions?\b/i},
 {domain:"Security and disarmament",id:'tpnw',label:'Treaty on the Prohibition of Nuclear Weapons',global:true,target:/\b(?:TPNW|Treaty (?:on the Prohibition|for the Prohibition) of Nuclear Weapons)\b/i},
 {domain:"Security and disarmament",id:'ctbt',label:'Comprehensive Nuclear-Test-Ban Treaty',global:true,target:/\b(?:CTBT|Comprehensive (?:Nuclear[ -])?Test[ -]Ban Treaty)\b/i},
 {id:'cuba_embargo',label:'Lift the embargo on Cuba',cuba:true,reject:/\b(?:extraterritorial|application of|Helms[ -]Burton)\b/i,target:/\b(?:lift(?:ing)?|end(?:ing)?|remov(?:e|ing|al of))\b[^.!?]{0,55}\b(?:embargo|blockade)\b/i},
 {domain:"Security and disarmament",id:'npt',label:'Nuclear Non-Proliferation Treaty',global:true,target:/\b(?:NPT|(?:Treaty on (?:the )?Non[ -]?Proliferation of Nuclear Weapons)|(?:Nuclear )?Non[ -]?Proliferation Treaty)\b/i,excludePrefix:/\bAdditional Protocol\b/i,excludeSuffix:/^\s+(?:Review Conference|review process)\b/i},
 {domain:"Security and disarmament",id:'iaea_additional_protocol',label:'Adopt the IAEA Additional Protocol',global:true,target:/\b(?:IAEA(?:'s)? Additional Protocol|Additional Protocol to (?:the )?(?:NPT|(?:Nuclear )?Non[ -]?Proliferation Treaty))\b/i},
 {domain:"Security and disarmament",id:'bwc',label:'Biological Weapons Convention',global:true,target:/\b(?:BWC|Biological (?:and Toxin )?Weapons Convention)\b/i},
 {domain:"Security and disarmament",id:'cwc',label:'Chemical Weapons Convention',global:true,target:/\b(?:CWC|Chemical Weapons Convention)\b/i},
 {domain:"Security and disarmament",id:'arms_trade_treaty',label:'Arms Trade Treaty',global:true,target:/\bArms Trade Treaty\b/i},
 {domain:"Security and disarmament",id:'small_arms_programme',label:'UN Programme of Action on Small Arms',global:true,required:/\b(?:small arms|light weapons)\b/i,target:/\b(?:UN|United Nations) Programme of Action(?: on Small Arms(?: and Light Weapons)?)?\b|\bProgramme of Action on Small Arms(?: and Light Weapons)?\b/i},
 {domain:"Security and disarmament",id:'nuclear_disarmament',excludeSuffix:/^\s+verification\b/i,label:'Pursue nuclear disarmament',global:true,target:/\b(?:nuclear disarmament|world without nuclear weapons|(?:elimination|abolition) of (?:all )?nuclear weapons)\b/i},
 {domain:"Security and disarmament",id:'pelindaba',supportDeclaration:/^while reiterating (?:its|our) commitment to (?:the )?(?:Treaty of Pelindaba|Pelindaba Treaty), (?:my country|we)\b/i,label:'Treaty of Pelindaba',global:true,target:/\b(?:Treaty of Pelindaba|Pelindaba Treaty|African Nuclear[ -]Weapon[ -]Free[ -]Zone Treaty)\b/i},
 {domain:"Security and disarmament",id:'fissile_material_treaty',label:'Negotiate a fissile material cut-off treaty',global:true,target:/\b(?:FMCT|fissile material (?:cut[ -]off )?treaty|treaty (?:banning|prohibiting) (?:the )?production of fissile material)\b/i},
 {domain:"Climate and environment",id:'paris_agreement',label:'Paris Agreement',global:true,target:/\bParis Agreement\b/i},
 {domain:"Climate and environment",id:'climate_finance',supportDeclaration:/^we call upon our international partners, UN agencies, (?:the )?OHCHR Pacific Regional Office, and the Pacific community to support [^.!?]{1,80} through technical assistance, capacity building, and climate finance\.$/i,label:'Provide climate finance',global:true,target:/\bclimate financ(?:e|ing)\b/i},
 {domain:"Climate and environment",id:'loss_damage_fund',label:'Loss and Damage Fund',global:true,target:/\b(?:Loss and Damage Fund|Fund for Responding to Loss and Damage)\b/i},
 {domain:"Development and finance",id:'sdgs',label:'2030 Agenda and SDGs',global:true,target:/\b(?:2030 (?:Development )?Agenda(?: for Sustainable Development)?|Sustainable Development Goals|SDGs)\b/i},
 {domain:"Climate and environment",id:'disaster_protection_treaty',label:'Conclude a treaty protecting persons in disasters',global:true,target:/\b(?:legally binding instrument|treaty|convention) on (?:the )?protection of persons in (?:the event of )?disasters\b/i},
 {domain:"Institutions and digital governance",id:'icc',label:'International Criminal Court',global:true,target:/\bInternational Criminal Court\b/i},
 {domain:"Human rights and inclusion",id:'death_penalty_abolition',label:'Abolish the death penalty',global:true,target:/\b(?:abolition of (?:the )?death penalty|abolish(?:ing)? (?:the )?death penalty)\b/i},
 {domain:"Human rights and inclusion",id:'death_penalty_moratorium',label:'Establish a global death-penalty moratorium',global:true,target:/\b(?:global|universal|worldwide) moratorium on (?:the (?:use|application) of )?(?:the )?(?:death penalty|executions)\b/i},
 {domain:"Institutions and digital governance",id:'security_council_reform',label:'Reform the Security Council',global:true,target:/\b(?:reform(?:ing)? (?:of )?(?:the )?(?:UN |United Nations )?Security Council|Security Council reform)\b/i},
 {domain:"Institutions and digital governance",id:'security_council_expansion',label:'Expand Security Council membership',global:true,target:/\b(?:expansion of (?:the )?(?:UN |United Nations )?Security Council(?: membership)?|enlargement of (?:the )?(?:UN |United Nations )?Security Council)\b/i},
 {id:'palestine_recognition',label:'Recognize the State of Palestine',global:true,target:/\b(?:recognition of (?:the )?(?:State of )?Palestine|recogniz(?:e|ing) (?:the )?State of Palestine)\b/i},
 {id:'unrwa',label:'UNRWA',global:true,target:/\b(?:UNRWA|United Nations Relief and Works Agency(?: for Palestine Refugees(?: in the Near East)?)?)\b/i},
 {domain:"Security and disarmament",id:'korean_denuclearization',label:'Denuclearize the Korean Peninsula',global:true,target:/\bdenuclearization of (?:the )?Korean Peninsula\b/i},
 {id:'cuba_terrorism_removal',label:'Remove Cuba from the U.S. terrorism-sponsor list',cuba:true,required:/\bUnited States\b|\bU\.S\.(?=\W|$)|\bUS\b/,target:/\b(?:remov(?:e|ing|al of)|delist(?:ing)?)\b[^!?]{0,25}\bCuba\b[^!?]{0,40}\b(?:state sponsors? of terrorism|(?:terrorism|terrorist)[ -]sponsor(?:s)?(?: list)?|list of (?:state )?sponsors? of terrorism)\b/i},
 {id:"mine_ban",label:"Anti-Personnel Mine Ban Convention",domain:"Security and disarmament",global:true,target:/\b(?:Anti[ -]Personnel Mine Ban Convention|Ottawa Convention|Mine Ban Treaty)\b/i},
 {id:"cluster_munitions",label:"Convention on Cluster Munitions",domain:"Security and disarmament",global:true,target:/\bConvention on Cluster Munitions\b/i},
 {id:"conventional_weapons",label:"Convention on Certain Conventional Weapons",domain:"Security and disarmament",global:true,target:/\bConvention on Certain Conventional Weapons\b/i},
 {id:"nuclear_test_moratorium",label:"Maintain a nuclear-test moratorium",domain:"Security and disarmament",global:true,target:/\b(?:moratorium on nuclear (?:weapons? )?test(?:ing|s)|nuclear[ -]test moratorium)\b/i},
 {id:"no_first_use",label:"Commit to no first use of nuclear weapons",domain:"Security and disarmament",global:true,target:/\bno[ -]first[ -]use (?:of nuclear weapons|policy for nuclear weapons|nuclear policy)\b/i},
 {id:"negative_security_assurances",label:"Provide negative security assurances to non-nuclear states",domain:"Security and disarmament",global:true,target:/\bnegative security assurances to non[ -]nuclear[ -]weapon states\b/i},
 {id:"outer_space_arms_race",label:"Prevent an arms race in outer space",domain:"Security and disarmament",global:true,target:/\b(?:prevention of an arms race in outer space|prevent(?:ing)? an arms race in outer space)\b/i},
 {id:"autonomous_weapons_treaty",label:"Negotiate a treaty on autonomous weapons",domain:"Security and disarmament",global:true,target:/\b(?:legally binding instrument|treaty|convention) on (?:lethal )?autonomous weapons(?: systems)?\b/i},
 {id:"cybercrime_convention",label:"UN Convention against Cybercrime",domain:"Institutions and digital governance",global:true,target:/\b(?:United Nations|UN) Convention against Cybercrime\b/i},
 {id:"un_peacekeeping",label:"Support UN peacekeeping operations",domain:"Security and disarmament",global:true,target:/\b(?:United Nations|UN) peacekeeping operations\b/i},
 {id:"oda_target",label:"Meet the 0.7% official-development-assistance target",domain:"Development and finance",global:true,target:/\b0[.,]7\s*(?:per cent|percent|%)\s*(?:of (?:GNI|gross national income)\s*)?(?:ODA|official development assistance)(?: target)?\b/i},
 {id:"debt_restructuring",label:"Restructure sovereign debt",domain:"Development and finance",global:true,target:/\b(?:sovereign debt restructuring|restructuring of sovereign debt)\b/i},
 {id:"debt_cancellation",label:"Cancel sovereign debt",domain:"Development and finance",global:true,target:/\b(?:cancellation of sovereign debt|sovereign debt cancellation)\b/i},
 {id:"concessional_finance",label:"Provide concessional finance",domain:"Development and finance",global:true,target:/\bconcessional financ(?:e|ing)\b/i},
 {id:"social_protection",label:"Strengthen social protection",domain:"Development and finance",global:true,target:/\bsocial protection(?: systems)?\b/i},
 {id:"technology_transfer",label:"Facilitate technology transfer",domain:"Development and finance",global:true,target:/\btechnology transfer\b/i},
 {id:"illicit_financial_flows",label:"Combat illicit financial flows",domain:"Development and finance",global:true,target:/\b(?:combat(?:ing|ting)?|curb(?:ing)?|tackl(?:e|ing)) illicit financial flows\b/i},
 {id:"tax_cooperation_convention",label:"UN framework convention on international tax cooperation",domain:"Development and finance",global:true,target:/\b(?:United Nations|UN) Framework Convention on International Tax Cooperation\b/i},
 {id:"wto",label:"World Trade Organization",domain:"Development and finance",global:true,target:/\bWorld Trade Organi[sz]ation\b/i},
 {id:"doha_ldc",label:"Doha Programme of Action for least developed countries",domain:"Development and finance",global:true,target:/\bDoha Programme of Action(?: for (?:the )?Least Developed Countries)?\b/i},
 {id:"adaptation_finance",label:"Provide climate-adaptation finance",domain:"Climate and environment",global:true,target:/\b(?:climate[ -])?adaptation financ(?:e|ing)\b/i},
 {id:"fossil_fuel_transition",label:"Transition away from fossil fuels",domain:"Climate and environment",global:true,target:/\btransition(?:ing)? away from fossil fuels\b/i},
 {id:"renewable_energy",label:"Expand renewable energy",domain:"Climate and environment",global:true,target:/\b(?:expansion of renewable energy|expand(?:ing)? renewable energy)\b/i},
 {id:"biodiversity_framework",label:"Kunming-Montreal Global Biodiversity Framework",domain:"Climate and environment",global:true,target:/\bKunming[ -]Montreal Global Biodiversity Framework\b/i},
 {id:"bbnj",label:"Biodiversity Beyond National Jurisdiction Agreement",domain:"Climate and environment",global:true,target:/\b(?:BBNJ Agreement|Biodiversity Beyond National Jurisdiction Agreement|Agreement on (?:the )?Conservation and Sustainable Use of Marine Biological Diversity of Areas Beyond National Jurisdiction)\b/i},
 {id:"plastics_treaty",label:"Negotiate a treaty on plastic pollution",domain:"Climate and environment",global:true,target:/\b(?:legally binding instrument|treaty|convention) (?:on|to end) plastic pollution\b/i},
 {id:"sendai",label:"Sendai Framework for Disaster Risk Reduction",domain:"Climate and environment",global:true,target:/\bSendai Framework(?: for Disaster Risk Reduction)?\b/i},
 {id:"early_warning",label:"Provide multi-hazard early-warning systems",domain:"Climate and environment",global:true,target:/\bmulti[ -]hazard early[ -]warning systems\b/i},
 {id:"gender_equality",label:"Advance gender equality",domain:"Human rights and inclusion",global:true,target:/\bgender equality\b/i},
 {id:"women_peace_security",label:"Women, Peace and Security agenda",domain:"Human rights and inclusion",global:true,target:/\b(?:Women,? Peace and Security agenda|WPS agenda)\b/i},
 {id:"women_peace_participation",label:"Include women in peace processes",domain:"Human rights and inclusion",global:true,target:/\b(?:women(?:\x27s)? (?:full,? equal and meaningful )?participation in peace processes|participation of women in peace processes)\b/i},
 {id:"end_child_marriage",label:"End child marriage",domain:"Human rights and inclusion",global:true,target:/\b(?:end(?:ing)?|eliminat(?:e|ing|ion of)) child(?:, early and forced)? marriage\b/i},
 {id:"torture_convention",qualifiedDeclaration:/^we (?:has|have) prioritized the accession and ratification of the UN Convention Against Torture, UNCAT, as our immediate international treaty priority, while continuing internal legal reviews across other instruments\.$/i,qualification:"Prioritizes accession; does not claim completed ratification or immediate accession to all remaining treaties.",excludePrefix:/\bOptional Protocol\b/i,label:"Convention against Torture",domain:"Human rights and inclusion",global:true,target:/\bConvention against Torture\b/i},
 {id:"disappearances_convention",label:"Convention protecting all persons from enforced disappearance",domain:"Human rights and inclusion",global:true,target:/\b(?:International )?Convention for the Protection of All Persons from Enforced Disappearance\b/i},
 {id:"refugee_convention",label:"1951 Refugee Convention",domain:"Migration and displacement",global:true,target:/\b(?:1951 (?:Refugee Convention|Convention (?:relating to|on) the Status of Refugees))\b/i},
 {id:"migration_compact",label:"Global Compact for Migration",domain:"Migration and displacement",global:true,target:/\bGlobal Compact for (?:Safe,? Orderly and Regular )?Migration\b/i},
 {id:"refugees_compact",label:"Global Compact on Refugees",domain:"Migration and displacement",global:true,target:/\bGlobal Compact on Refugees\b/i},
 {id:"disability_rights",label:"Convention on the Rights of Persons with Disabilities",domain:"Human rights and inclusion",global:true,target:/\b(?:Convention on the Rights of Persons with Disabilities|CRPD)\b/i},
 {id:"un80",label:"UN80 Initiative",excludePrefix:/\b(?:group|leadership|office|pillar)\b/i,domain:"Institutions and digital governance",global:true,target:/\bUN80 Initiative\b/i},
 {id:"veto_restraint",label:"Restrain Security Council veto use in mass atrocities",domain:"Institutions and digital governance",global:true,target:/\b(?:restraint (?:on|in) (?:the )?(?:use of (?:the )?)?(?:Security Council )?veto in (?:cases of )?mass atrocities|veto restraint in (?:cases of )?mass atrocities)\b/i},
 {id:"african_permanent_seats",label:"Permanent African seats on the Security Council",domain:"Institutions and digital governance",global:true,target:/\b(?:permanent African seats on (?:the )?Security Council|permanent seats for Africa on (?:the )?Security Council)\b/i},
 {id:"icj",label:"International Court of Justice",domain:"Institutions and digital governance",global:true,target:/\bInternational Court of Justice\b/i},
 {id:"unclos",label:"UN Convention on the Law of the Sea",domain:"Institutions and digital governance",global:true,target:/\b(?:UNCLOS|(?:United Nations|UN) Convention on the Law of the Sea)\b/i},
 {id:"ai_human_rights",label:"Human-rights-based AI governance",domain:"Institutions and digital governance",global:true,target:/\bhuman[ -]rights[ -]based (?:AI|artificial intelligence) governance\b/i},
 {id:"universal_health",label:"Provide universal health coverage",domain:"Health",global:true,target:/\buniversal health coverage\b/i},
 {id:"release_hostages",label:"Release all hostages",domain:"Regional peace and protection",target:/\b(?:release of all hostages|releas(?:e|ing) all hostages)\b/i},
 {id:"libya_elections",label:"Hold national elections in Libya",domain:"Regional peace and protection",contexts:["libya"],target:/\b(?:national elections in Libya|Libyan national elections)\b/i},
 {id:"russian_withdrawal",label:"Withdraw Russian forces from Ukraine",domain:"Regional peace and protection",contexts:["ukraine"],target:/\b(?:withdrawal of Russian (?:forces|troops) from Ukraine|withdraw(?:ing)? Russian (?:forces|troops) from Ukraine)\b/i},
 {id:"cuba_extraterritorial",label:"End extraterritorial application of the Cuba embargo",domain:"Regional peace and protection",contexts:["cuba"],target:/\b(?:end(?:ing)?|remov(?:e|ing|al of)) (?:the )?extraterritorial application of (?:the )?(?:embargo|blockade) (?:on|against) Cuba\b/i},
 {id:"end_unilateral_measures",label:"Lift unilateral coercive measures",domain:"Regional peace and protection",qualifiersOutsideTarget:true,target:/\b(?:lift(?:ing)?|remov(?:e|ing|al of)|end(?:ing)?) (?:all |the )?unilateral coercive measures\b/i},
 {id:'ihl_compliance',label:'Respect international humanitarian law',domain:'Regional peace and protection',global:true,target:/\b(?:international humanitarian law|IHL)\b/i},
 {id:'poverty_eradication',supportDeclaration:/^(?:the )?(?:poverty eradication in all of its forms and manifestations?|eradication of poverty(?: and hunger)?) remains (?:a key priority|a fundamental responsibility)\b/i,label:'Eradicate poverty',domain:'Development and finance',global:true,target:/\b(?:poverty eradication|eradicat(?:e|ing|ion of) (?:extreme )?poverty)\b/i},
 {id:'food_security',supportDeclaration:/^we are committed to (?!.*\b(?:not|report|proposal|that|which|against|rather than|instead of)\b)[^.!?]{0,240}\b(?:moving|progressing|working) towards food security\b/i,label:'Achieve food security',domain:'Development and finance',global:true,target:/\bfood security\b/i},
 {id:'cyprus_good_offices',label:'Support the Secretary-General good-offices mission in Cyprus',domain:'Regional peace and protection',contexts:['cyprus'],target:/\b(?:Secretary[ -]General(?:'s|’s)? Good Offices Mission in Cyprus|(?:UN|United Nations) good[ -]offices mission in Cyprus)\b/i},
 {id:'global_alliance_human_rights',label:'Global Alliance for Human Rights',domain:'Human rights and inclusion',global:true,target:/\bGlobal Alliance for Human Rights\b/i},
 {id:'civil_society_cooperation',label:'Cooperate with civil society',domain:'Human rights and inclusion',global:true,target:/\bcooperation with civil society\b/i},
 {id:'end_golan_occupation',label:'End Israeli occupation of the Syrian Golan',domain:'Regional peace and protection',contexts:['golan'],target:/\bend(?:ing)? (?:the )?(?:Israeli )?occupation of (?:the )?(?:occupied )?Syrian Golan\b/i},
 {id:'human_rights_defenders',label:'Support human rights defenders',domain:'Human rights and inclusion',global:true,target:/\bhuman rights defenders\b/i},
 {id:'international_crime_accountability',required:/\b(?:international crimes|most serious crimes|universal jurisdiction|international criminal|genocide|war crimes)\b/i,label:'Combat impunity for international crimes',domain:'Institutions and digital governance',global:true,target:/\b(?:combat(?:ing)? impunity|end(?:ing)? impunity|fight against impunity|accountability for (?:the )?(?:most serious )?international crimes|zero tolerance toward impunity)\b/i},
 {id:'nuclear_deterrence',label:'Maintain nuclear deterrence',domain:'Security and disarmament',global:true,target:/\bnuclear deterrence\b/i},
 {id:'freedom_navigation',label:'Protect freedom of navigation',domain:'Institutions and digital governance',global:true,target:/\bfreedom of navigation\b/i},
 {id:'unsc_2803',label:'Implement Security Council Resolution 2803',domain:'Regional peace and protection',contexts:['gaza','israel_palestine'],target:/\b(?:(?:UN |United Nations )?Security Council )?[Rr]esolution 2803\b/i},
 {id:'human_rights_treaty_bodies',label:'Support UN human rights treaty bodies',domain:'Human rights and inclusion',global:true,target:/\b(?:UN |United Nations )?human rights treaty body system\b/i},
 {id:'human_centric_ai',label:'Human rights safeguards for AI governance',domain:'Human rights and inclusion',global:true,target:/\bhuman[ -]centric AI governance\b/i},
 {id:'resident_coordinator',label:'Support the Resident Coordinator system',domain:'Development and finance',global:true,target:/\bResident Coordinator [Ss]ystem\b/i},
 {id:'national_development_ownership',label:'National ownership of development cooperation',domain:'Development and finance',global:true,target:/\bnational ownership\b/i},
 {id:'universal_jurisdiction',label:'Exercise universal jurisdiction',domain:'Institutions and digital governance',global:true,target:/\b(?:exercise of )?universal jurisdiction\b/i},
 {id:'resilient_food_systems',label:'Build resilient food systems',domain:'Development and finance',global:true,target:/\b(?:resilient food systems|resilience of food systems)\b/i},
 {id:'civil_society_participation',label:'Include civil society in international processes',domain:'Human rights and inclusion',global:true,target:/\b(?:effective |meaningful |full )?participation of civil society\b/i},
 {id:'nuclear_weapon_free_zones',label:'Establish nuclear-weapon-free zones',domain:'Security and disarmament',global:true,target:/\bnuclear[ -]weapons?[ -]free zones\b/i,excludePrefix:/\b(?:African|Middle East|Asian|European)\b/i,excludeSuffix:/^\s+in\b/i},
 {id:'peaceful_nuclear_energy',label:'Use nuclear energy for peaceful purposes',domain:'Security and disarmament',global:true,target:/\b(?:use of nuclear energy for peaceful purposes|peaceful uses? of nuclear energy)\b/i},
 {id:'food_supply_chains',label:'Stabilize food and fertilizer supply chains',domain:'Development and finance',global:true,target:/\b(?:fertilizer and food supply chains|food and fertilizer supply chains)\b/i},
 {id:'libya_un_mediation',label:'UN mediation in Libya',domain:'Regional peace and protection',contexts:['libya'],excludeSuffix:/^[’']s efforts to facilitate[^.!?]{0,100}participation/i,target:/\b(?:UNSMIL|UN[ -]facilitated (?:political )?process|UN[ -]facilitated Libyan political process)\b/i},
 {id:'libya_territorial_integrity',label:'Respect Libya sovereignty and territorial integrity',domain:'Regional peace and protection',contexts:['libya'],target:/\b(?:unity, sovereignty, independence and territorial integrity of Libya|Libya(?:'s|’s)? sovereignty independence, territorial integrity)\b/i},
 {id:'lebanon_1701',label:'Implement Security Council Resolution 1701',domain:'Regional peace and protection',contexts:['lebanon'],target:/\b(?:(?:UN |United Nations )?Security Council )?[Rr]esolution 1701\b/i},
 {id:'lebanon_sovereignty',label:'Respect Lebanon independence and territorial integrity',domain:'Regional peace and protection',contexts:['lebanon'],target:/\bLebanon(?:'s|’s) independence, unity, and territorial integrity\b/i},
 {id:'iran_iaea_cooperation',label:'Iran cooperation with IAEA safeguards',domain:'Security and disarmament',contexts:['iran'],required:/\b(?:Iran|Tehran)\b/i,target:/\b(?:(?:Iran|Tehran) to (?:fully cooperate|cooperate fully|cooperate) with the IAEA|(?:full )?cooperation (?:by|of) Iran with the IAEA)\b/i},
 {id:'ohchr_work',label:'Support the UN human rights High Commissioner’s work',domain:'Human rights and inclusion',global:true,target:/\b(?:High Commissioner|OHCHR|Office of the (?:UN|United Nations) High Commissioner for Human Rights)\b/i,requiredRecord:/\b(?:human rights|OHCHR|Turk|Türk)\b/i,reject:/High Commissioner for Refugees/i,declarationOnly:true,supportDeclaration:/^we (?:(?:support|reaffirm our support for) (?:the )?(?:work|mandate) of (?:the )?(?:UN |United Nations )?High Commissioner(?: for Human Rights)?\b|thanks? High Commissioner (?:Turk|Türk) for his update and reiterates? (?:its|our) support for his mandate and the independence of his office\b|welcomes? the High Commissioner and congratulates? him on renewal of his mandate and reiterates? (?:its|our) commitment to continue supporting your work\b|hail the efforts of (?:the )?OHCHR to\b)/i},
 {id:'disaster_risk_reduction',label:'Reduce disaster risks',domain:'Climate and environment',global:true,target:/\b(?:reduce disaster risks|disaster risk reduction|prevention of disasters)\b/i,supportDeclaration:/^we support draft article \d+,? which enshrines states[’']? obligations to reduce disaster risks\b/i},
 {id:'disaster_assistance_consent',label:'Require affected-state consent for international assistance',domain:'Institutions and digital governance',global:true,qualifiersOutsideTarget:true,target:/\bassistance must[^.!?]{0,100}be provided with the consent of the affected states\b/i,supportDeclaration:/^assistance must (?![^.!?]*\bnot\b)[^.!?]{0,100}be provided with the consent of the affected states\b/i},
 {id:'predictable_development_finance',label:'Provide predictable, accessible development finance',domain:'Development and finance',global:true,target:/\b(?:financing that is predictable, affordable, and easier to access|predictable development financ(?:e|ing)|adequate, stable and predictable financial resources for development)\b/i,supportDeclaration:/^it is essential to ensure adequate, stable and predictable financial resources for development\b/i},
 {id:'state_sovereignty',label:'Respect state sovereignty',domain:'Institutions and digital governance',global:true,target:/\brespect (?:for |of (?:the )?)state sovereignty\b/i},
 {id:'peaceful_dispute_settlement',label:'Settle international disputes by peaceful means',domain:'Institutions and digital governance',global:true,target:/\b(?:peaceful means for (?:the )?settlement of disputes|peaceful settlement of (?:international )?disputes)\b/i},
 {id:'iran_no_nuclear_weapon',label:'Prevent Iran from acquiring a nuclear weapon',domain:'Security and disarmament',global:true,target:/\b(?:prevent Iran from acquiring a nuclear weapon|Iran (?:must|should) never acquire a nuclear weapon)\b/i,supportDeclaration:/^Iran (?:must|should) never acquire a nuclear weapon\b/i},
 {id:'palestinian_statehood',label:'Support Palestinian statehood',domain:'Regional peace and protection',global:true,target:/\b(?:Palestinian statehood|Palestinian people have the right to establish a Palestinian state)\b/i,supportDeclaration:/^we renew our position that the Palestinian people have the right to establish a Palestinian state\b/i},
 {id:'poverty_reduction',label:'Reduce poverty',domain:'Development and finance',global:true,target:/\b(?:poverty reduction|reduc(?:e|ing) poverty|tackling the problem of poverty)\b/i},
 {id:'development_cooperation_framework',label:'Use nationally agreed UN development cooperation frameworks',domain:'Development and finance',global:true,target:/\b(?:United Nations |UN )?Sustainable Development Cooperation Framework\b/i,supportDeclaration:/^(?:the )?(?:United Nations |UN )?Sustainable Development Cooperation Framework, agreed with national authorities, should effectively guide\b/i},
 {id:'opcw_mandate',label:'Support the OPCW mandate',domain:'Security and disarmament',global:true,target:/\b(?:Organization for the Prohibition of Chemical Weapons|OPCW)\b/i},
 {id:'russian_nuclear_threats',label:'Russian threats of nuclear weapons use',domain:'Security and disarmament',global:true,target:/\bRussia[’']s[^.!?]{0,180}\bthreats of nuclear weapons use\b/i}
,
 {id:'outer_space_militarization',opposeDeclaration:/^we oppose all forms of [^.!?]{0,160}, as well as militarization of outer space\b/i,label:'Militarization of outer space',domain:'Security and disarmament',global:true,target:/\bmilitarization of outer space\b/i},
 {id:'abandon_unilateral_measures',label:'Abandon measures described as illegitimate unilateral measures',domain:'Institutions and digital governance',global:true,qualifiersOutsideTarget:true,target:/\babandon (?:illegitimate )?unilateral measures\b/i},
 {id:'treaty_implementation_assistance',unresolvedObject:true,label:'Training and technical assistance for treaty implementation (instrument unspecified)',domain:'Human rights and inclusion',requiredRecord:/\b(?:treaty organs|human rights mechanisms|treaty bodies)\b/i,target:/\bstates parties to these mechanisms need training and technical assistance\b/i,supportDeclaration:/^states parties to these mechanisms need training and technical assistance, financing to effectively implement these instruments\b/i}
,
 {id:'halt_settlement_expansion',label:'Halt settlement expansion',domain:'Regional peace and protection',target:/\b(?:end to|halt(?:ing)?|stop(?:ping)?) settlement expansion\b/i},
 {id:'ohchr_technical_functions',label:'OHCHR technical assistance, capacity building and reporting',domain:'Human rights and inclusion',global:true,target:/\b(?:Office of (?:the )?High Commissioner (?:on|for) Human Rights|OHCHR)[^.!?]{0,100}\btechnical assistance, capacity building, and (?:comprehensive )?reporting\b/i,qualifiedDeclaration:/(?:^|,\s*)i would like to underscore the crucial role of the Office of (?:the )?High Commissioner (?:on|for) Human Rights, particularly through its technical assistance, capacity building, and (?:comprehensive )?reporting\b/i,qualification:'Recognizes the importance of these functions; no explicit funding or implementation commitment is established.'},
 {id:'human_rights_framing',label:'Move beyond negative framing of human rights as a partisan or luxury agenda',domain:'Human rights and inclusion',global:true,required:/\b(?:partisan|luxury)\b/i,target:/\bmov(?:e|ing) beyond (?:the )?(?:negative (?:framing|narrative) (?:of|on) human rights|narrative on human rights that is too often negative)\b/i,supportDeclaration:/^we need to move beyond the narrative on human rights that is too often negative, one that risks coding human rights as a partisan or luxury agenda\b/i},
 {id:'national_ombudsman',label:'Restore a national Ombudsman while building human-rights institutions',domain:'Human rights and inclusion',domestic:true,target:/\bOffice of the Ombudsman\b/i,declarationOnly:true,qualifiedDeclaration:/^While financial and human resource constraints currently impede the immediate creation of an independent national human rights institution fully compliant with the Paris Principles, [\p{L} .'-]{1,80} is prioritizing the reestablishment of the Office of the Ombudsman\.$/iu,qualification:'Prioritizes restoring the Ombudsman; immediate establishment of a Paris-Principles-compliant NHRI remains constrained. Domestic implementation contexts are not scored against the U.S.'},
 {id:'national_child_protection_strategy',label:'Develop a comprehensive national child-protection strategy',domain:'Human rights and inclusion',domestic:true,target:/\bcomprehensive national child protection strategy\b/i,declarationOnly:true,qualifiedDeclaration:/^Guided by the CRC, [\p{L} .'-]{1,80} is formulating a comprehensive national child protection strategy\.$/iu,qualification:'Strategy is being formulated; adoption or implementation is not established. Domestic implementation contexts are not scored against the U.S.'},
 {id:'national_renewable_target_2050',label:'National target: 100% renewable-energy transition by 2050',domain:'Climate and environment',domestic:true,target:/\b100% renewable energy transition by 2050\b/i,declarationOnly:true,adjacentDeclaration:/^Setting a target of 100% renewable energy transition by 2050\.$/i,precedingDeclaration:/^we (?:has|have) integrated human rights into (?:its|our) updated climate change policy\. and third, nationally determined contribution\.$/i,qualification:'States a national target, not achieved renewable-energy deployment. Requires the immediately preceding national climate-policy declaration; domestic targets are not scored against the U.S.'}
];
const CONTEXTS=[{id:'domestic',label:'National implementation (not comparable across countries)'},{id:'sudan',label:'Sudan',pattern:/(?:(?<!South )\bSudan\b|\b(?:Darfur|Kordofan|Al[ -](?:Fasher|Obeid))\b)/i},{id:'gaza',label:'Gaza',pattern:/\bGaza\b/i},{id:'west_bank',label:'West Bank',pattern:/\bWest Bank\b/i},{id:'ukraine',label:'Ukraine',pattern:/\b(?:Ukraine|Ukrainian)\b/i},{id:'myanmar',label:'Myanmar',pattern:/\b(?:Myanmar|Burma)\b/i},{id:'lebanon',label:'Lebanon',pattern:/\bLebanon\b/i},{id:'cuba',label:'Cuba',pattern:/\bCuba(?:n)?\b/i},{id:'south_sudan',label:'South Sudan',pattern:/\bSouth Sudan\b/i},{id:'yemen',label:'Yemen',pattern:/\bYemen\b/i},{id:'syria',label:'Syria',pattern:/\bSyria\b/i},{id:'haiti',label:'Haiti',pattern:/\bHaiti\b/i},{id:'afghanistan',label:'Afghanistan',pattern:/\bAfghanistan\b/i},{id:'libya',label:'Libya',pattern:/\bLibya(?:n)?\b/i},{id:'somalia',label:'Somalia',pattern:/\bSomalia(?:n)?\b/i},{id:'drc',label:'Democratic Republic of the Congo',pattern:/\b(?:Democratic Republic of (?:the )?Congo|DRC|eastern Congo)\b/i},{id:'western_sahara',label:'Western Sahara',pattern:/\bWestern Sahara\b/i},{id:'israel_palestine',label:'Israel and Palestine',pattern:/\b(?:Israel|Palestin(?:e|ian)|Jerusalem)\b/i},{id:'cyprus',label:'Cyprus',pattern:/\bCyprus\b/i},{id:'golan',label:'Syrian Golan',pattern:/\b(?:Syrian Golan|Golan Heights)\b/i},{id:'iran',label:'Iran',pattern:/\b(?:Iran|Tehran)\b/i},{id:'unspecified',label:'Context not established'},{id:'global',label:'International policy'}];
for(const p of POLICIES)if(!p.domain)p.domain='Regional peace and protection';
const contextsFor=policy=>policy.domestic?['domestic']:policy.unresolvedObject?['unspecified']:policy.global?['global']:policy.cuba?['cuba']:[...new Set([...(policy.contexts||CONTEXTS.filter(c=>!['global','unspecified','domestic'].includes(c.id)).map(c=>c.id)),'unspecified'])];
const US='United States';
const isUS=c=>/^(?:United States(?: of America)?|U\.?S\.?A?\.?)$/i.test(String(c||'').trim());
const country=r=>isUS(r.country)?US:r.country;
const safe=u=>{try{const v=new URL(u);return v.origin==='https://transcripts.un.org'&&!v.username&&!v.password&&!v.hash?v.href:null;}catch{return null;}};
function options(p){
 const positionPolicy=p.positionPolicy===undefined?'humanitarian_access':p.positionPolicy;
 const policy=POLICIES.find(x=>x.id===positionPolicy);if(!policy)throw Error('Choose a supported explicit policy question.');
 const positionContext=p.positionContext===undefined?contextsFor(policy)[0]:p.positionContext;
 if(!contextsFor(policy).includes(positionContext))throw Error('Choose a valid context for this policy question.');
 const positionCountry=p.positionCountry===undefined?'':p.positionCountry;
 if(typeof positionCountry!=='string'||positionCountry.length>120||isUS(positionCountry))throw Error('Choose a comparison country other than the U.S. baseline.');
 return {positionPolicy,positionContext,positionCountry};
}
function national(r){
 const a=P.attribution(r),fn=String(r.speaker_metadata?.function||'');
 const nationalCapacity=/\b(?:in (?:my|our) national capacity|in my capacity as (?:the )?representative of)\b/i.test(r.text||'');
 return r.attribution?.country_status==='registry_mapped'&&r.region!=='Unmapped'&&typeof r.country==='string'&&!['collective','mixed_or_ambiguous','institutional'].includes(a.kind)&&
  (!/\b(?:chair|presiding|moderator|rapporteur|secretariat|journalist|civil society|press|president of (?:the )?(?:council|assembly|committee))\b/i.test(fn)||nationalCapacity)&&!/^(?:President|National President)$/i.test(fn.trim());
}
function context(line,r,policy){
 if(policy.domestic)return {id:'domestic',basis:'recorded_country_national_implementation_not_cross_country_comparable'};
 if(policy.unresolvedObject)return null;
 if(policy.global)return {id:'global',basis:policy.id==='tpnw'||policy.id==='ctbt'?'named_global_treaty':'named_international_policy'};
 const hits=text=>{let rows=CONTEXTS.filter(c=>c.pattern?.test(text));const family=['gaza','west_bank','israel_palestine'];if(policy.id==='two_state'&&rows.some(c=>family.includes(c.id)))rows=[...rows.filter(c=>!family.includes(c.id)),CONTEXTS.find(c=>c.id==='israel_palestine')];else if(rows.some(c=>['gaza','west_bank'].includes(c.id)))rows=rows.filter(c=>c.id!=='israel_palestine');return rows;};
 const places=[...line.matchAll(/\b(?:in|throughout|across|within)\s+(?:(?:the|occupied|northern|southern|eastern|western)\s+)*([A-Z][\p{L}'-]+(?:\s+[A-Z][\p{L}'-]+){0,3})/gu)];
 if(places.some(m=>!hits(m[1]).length))return null;
 const placeIntro=/^(?:On|In|Throughout|Across|Within)\s+[^,]{1,70},/i.exec(line)?.[0]||'';
 const direct=hits(placeIntro+' '+selfStatement(line,r));if(direct.length===1)return {id:direct[0].id,basis:'explicit_sentence'};if(direct.length>1)return null;
 const meeting=hits(r.meeting||''),segment=hits(r.text||'');
 if(segment.length>1){if(meeting.length===1&&meeting[0].id==='israel_palestine'&&segment.every(c=>['gaza','west_bank','israel_palestine'].includes(c.id)))return {id:'israel_palestine',basis:'recorded_meeting_scope_with_related_subcontexts'};return null;}
 if(segment.length===1)return meeting.some(c=>c.id===segment[0].id)?{id:segment[0].id,basis:'single_segment_context_matching_recorded_meeting_title'}:null;
 return meeting.length===1?{id:meeting[0].id,basis:'recorded_meeting_title'}:null;
}
// Normalize only a bounded self-declaration tied to the recorded national affiliation.
const SELF_ALIASES={
 'Bahrain':['Kingdom of Bahrain'],'Türkiye':['Turkey'], 'Russian Federation':['Russia'], 'Tanzania, United Republic of':['Tanzania','United Republic of Tanzania'],
 "Korea, Republic of":['Republic of Korea','South Korea'],"Korea, Democratic People\x27s Republic of":['Democratic People\x27s Republic of Korea','DPRK'],
 'Iran':['Islamic Republic of Iran'],'Viet Nam':['Vietnam'],'Palestine, State of':['State of Palestine','Palestine'],
 'Democratic Republic of the Congo':['DRC'],"Côte d'Ivoire":["Cote d'Ivoire"], 'Yemen':['Republic of Yemen']
};
function selfStatement(line,r,rewriteBelief=true){
 let text=line.trim();
 text=text.replace(/^It[’']s precisely in this context that /i,'');
 text=text.replace(/^Given (?!.*\b(?:said|says|reported|according to|claims?)\b)[^.!?;]{1,160}?,\s*/i,'');
 for(let i=0;i<2;i++)text=text.replace(/^(?:(?:Mr\.?|Madam|Mister) (?:Chair|Chairman|President)|Chair|Chairman|Chairwoman|President|In (?:this|that) (?:regard|context)|In conclusion|In its capacity as a member of the Executive Council|In addition|At the outset|As I conclude|First of all|Despite these challenges|In closing|At the same time|With winter approaching|Therefore|Accordingly|On Gaza|On the UN80 initiative),\s*/i,'');
 if(r&&national(r)){
  const esc=v=>v.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
  const names=[r.country,...(SELF_ALIASES[r.country]||[])].sort((a,b)=>b.length-a.length).map(esc).join('|');
  const named='(?:(?:the )?(?:'+names+')|my country|our country)';
  const possessive=new RegExp('^'+named+"[’']s commitment to (.+?) remains (?:firm|strong|steadfast|unwavering|undiminished|unchanged|resolute)\\b",'i').exec(text);
  if(possessive)text='We remain committed to '+possessive[1]+'.';
  else {text=text.replace(new RegExp('^'+named+',\\s*(?:therefore|accordingly),\\s*','i'),'We ');text=text.replace(new RegExp('^'+named+'(?=\\s)\\s+','i'),'We ');}
  text=text.replace(/^(?:my delegation|our delegation|my government|our government)\s+/i,'We ');
 }
 text=text.replace(/^we (?:appreciate|thank|commend) (?!.*\b(?:that|which|who|because)\b)[^.!?;]{1,180}? and remain committed to /i,'We remain committed to ');
 text=text.replace(/^we (?:is|are) (?:deeply|fully|firmly|strongly) committed to /i,'We are committed to ');
 text=text.replace(/^we (?:welcomes? and supports?) /i,'We support ');
 text=text.replace(/^we (?:reaffirms?|reiterates?|renews?) (?:its|our|my) (?:firm |full |strong |continued )?support to /i,'We reaffirm our support for ');
 text=text.replace(/^we (?:reiterates?|renews?) (?:its|our|my) (?:firm |full |strong |continued )?(support for|call for) /i,(_,object)=>'We '+(object==='call for'?'call for':'reaffirm our support for')+' ');
 text=text.replace(/^we (?:is a|are) (?:long[ -]standing |strong |consistent )?supporters? of /i,'We support ');
 text=text.replace(/^we remain (?:steadfast|firm|resolute) in supporting /i,'We support ');
 text=text.replace(/^we remains (?:fully|firmly|steadfastly|resolutely) committed to /i,'We remain committed to ');
 text=text.replace(/^we (?:(?:therefore|also|further|once again|strongly|fully|firmly|urgently)\s+){1,3}/i,'We ');
 text=text.replace(/^we (?:also )?(?:reaffirms?|reiterates?|renews?) (?:its|our|my) (?:(?:strong|firm|unwavering|steadfast|full|continued|unequivocal) )?(support for|opposition to|commitment to)\s+/i,(_,object)=>'We reaffirm our '+object+' ');
 text=text.replace(/^we reaffirms that /i,'We reaffirm that ');
 text=text.replace(/^(?:let us recall that|we recall that|we reaffirm that)\s+/i,'');
 text=text.replace(/^we reaffirms? that /i,'We reaffirm that ');
 text=text.replace(/^we (?:reiterates?|reasserts?) (?:its|our) (?:staunch attachment|firm commitment) to /i,'We reaffirm our commitment to ');
 text=text.replace(/^we (?:will consistently|will continue to) oppose /i,'We oppose ');
 if(rewriteBelief)text=text.replace(/^we (?:believes?|believe) that it is of the utmost importance to move towards the conclusion of /i,'We call for the conclusion of ');
 text=text.replace(/^we reiterates? (?:the|our) call for /i,'We call for ');
 text=text.replace(/^we reiterate our condemnation of /i,'We oppose ');
 text=text.replace(/^we (?:remain|remains) open to constructive debate on this agenda item and (?:is|are) committed to /i,'We are committed to ');
 text=text.replace(/^we reiterate the need of moving towards /i,'We call for ');
 const verbs={'continues to':'continue to','will continue to':'continue to','supports':'support','opposes':'oppose','rejects':'reject','endorses':'endorse','welcomes':'welcome','calls for':'call for','calls on':'call on','calls upon':'call upon','urges':'urge','demands':'demand','advocates':'advocate','remains committed to':'remain committed to','remains strongly committed to':'remain committed to','is committed to':'are committed to'};
 return text.replace(/^we (continues to|will continue to|supports|opposes|rejects|endorses|welcomes|calls for|calls on|calls upon|urges|demands|advocates|remains strongly committed to|remains committed to|is committed to)\b/i,(_,verb)=>'We '+verbs[verb.toLowerCase()]);
}
function direction(line,policy,r,previousLine){
 if(policy.adjacentDeclaration?.test(line)&&national(r)&&policy.precedingDeclaration.test(selfStatement(previousLine||'',r)))return 'qualified';
 if(/\?/.test(line)||!policy.target.test(line)||policy.reject?.test(line)||(policy.required&&!policy.required.test(line))||(policy.requiredRecord&&!policy.requiredRecord.test((r?.text||line)+' '+(r?.meeting||'')))||!T.summaryEvidenceSentence(line)||T.unclearWording(line))return null;
 // Only this bounded own normative belief is exempt from the reported-belief guard.
 const ownBelief=/^we believes? that it is of the utmost importance to move towards the conclusion of /i.test(selfStatement(line,r,false));
 const reportedText=ownBelief?line.replace(/\bbelieves?\b/i,''):line;
 // Keep original quoted/reported wording even when self-normalization shortens a declaration.
 if(/\b(?:according to|said|says|stated|claims?|quoted|believes?|argues?|maintains?|asserts?|announced|the report|the resolution|the declaration)\b|[“”\"]/i.test(reportedText))return null;
 const qualificationText=policy.qualifiersOutsideTarget?line.replace(policy.target,''):line;
 const qualified=/\b(?:if|unless|provided that|subject to|only|when|on condition|with the consent|consensus-based|complementarity between|as long as|cautious approach|with caution|circumspection|due process|fair trial|respect for sovereignty|would|could|might|temporary|conditional|unilateral|partial|limited|excluding|except|not all)\b/i.test(qualificationText);
 const uncertaintyText=policy.id==='nuclear_disarmament'?line.replace(/world without nuclear weapons/ig,''):qualificationText;
 const uncertainObject=/\bwithout\s+(?!(?:(?:further )?delay|restrictions?|obstruction)\b)/i.test(uncertaintyText);
 const states=[];
 for(let clause of line.replace(/\b(must|should), however, be\b/ig,'$1 be').split(/;|\band\s+(?=we\s+(?:reiterate|reaffirm|call|support|remain))|\b(?:but|however|although)\b|,\s*(?=(?:we|i|our delegation|my delegation)\b)/i)){
  clause=clause.trim().replace(/^(?:in this (?:context|regard),\s*|(?:first|second|third),\s*)/i,'');
  clause=selfStatement(clause,r);
  if(policy.qualifiedDeclaration?.test(clause)&&(!['national_ombudsman','national_child_protection_strategy'].includes(policy.id)||new RegExp('\\b'+r?.country.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')+' is (?:prioritizing|formulating)\\b','i').test(clause))){states.push('qualified');continue;}
  if(policy.supportDeclaration?.test(clause)){states.push('support');continue;}
  if(policy.opposeDeclaration?.test(clause)){states.push('oppose');continue;}
  if(policy.declarationOnly)continue;
  clause=clause.replace(/\ball countries, especially nuclear weapons states, to\b/ig,'states to');
  clause=clause.replace(/^we (reaffirm our support for|support) to /i,'We $1 ');
  clause=clause.replace(/\b(?:states|countries) (?:that|which|who) have not yet done so to\b/ig,'states to');
  const action=/^(?:we|i|our delegation|my delegation|our government|my government)\s+(?:(?:strongly|fully|firmly|also|therefore|further|urgently|continue to)\s+){0,3}(must support|should support|must strengthen|should strengthen|must respect|should respect|must ensure|should ensure|must implement|should implement|must ratify|should ratify|must defend|should defend|reaffirm our opposition to|reiterate our opposition to|reaffirm our support for|reiterate our support for|reaffirm our commitment to|reiterate our commitment to|remain committed to|are committed to|do not support|cannot support|oppose|condemn|reject|object to|support|endorse|welcome|call for|call on|call upon|encourage|urge|demand|advocate|stress the need for|stress the need to)\b\s*([^!?]+)/i.exec(clause);
  if(action){
   const object=action[2],at=object.search(policy.target),prefix=object.slice(0,at),targetMatch=policy.target.exec(object);
   if(targetMatch&&policy.excludeSuffix?.test(object.slice(targetMatch.index+targetMatch[0].length)))continue;
   if(at<0||T.wordCount(prefix)>14||policy.excludePrefix?.test(prefix)||/\b(?:states? parties|parties|members)\s+(?:to|of)\s+(?:the\s+)?$/i.test(prefix))continue;
   if(/\b(?:resetting|imbalance|transparency|accountability|contribution|agreement|head of|director of|representative of|report|resolution|declaration|statement|proposal|criticism|criticisms|critique|noncompliance|non-compliance|disregard|defiance|ignoring|evading|weakening|against|obstacles?|amendments?|reform|cuts?|reductions?|reducing|defunding|suspension|suspending|investigation|that|which|whether|who|because|while|sanctions?|attacks?|violence|obstruction|restrictions?|denial|obstruct(?:ing|ion)?|restrict(?:ing)?|imped(?:e|ing)|prevent(?:ing)?|block(?:ing)?|deny(?:ing)?|denying|withdraw(?:al|ing)?|violate|violat(?:ing|ions?)|rejection|rejecting|reject|opposing|oppose|opposition|abolition|cancellation|termination|military|intervention)\b/i.test(prefix))continue;
   if(/\b(?:no|not|without|rather than|instead of|neither|nor|lift|lifting|removal|ending)\b/i.test(prefix)&&!policy.cuba){states.push('qualified');continue;}
   if(/\band\s+(?:oppose|reject|support|do not support)\b/i.test(object.slice(at)))states.push('qualified');
   else {const negative=/^(?:do not|cannot|oppose|condemn|reject|object|reaffirm our opposition|reiterate our opposition)/i.test(action[1]);states.push(negative&&prefix.replace(/\b(?:the|a|an)\b/ig,'').trim()?'qualified':negative?'oppose':'support');}
  }else if(!policy.cuba){
   const at=clause.search(policy.target);if(at<0)continue;
   const before=clause.slice(0,at),after=clause.slice(at);
   if(['fissile_material_treaty','autonomous_weapons_treaty','plastics_treaty','disaster_protection_treaty'].includes(policy.id)&&/^(?:negotiations? (?:on|for|of) (?:an? |the )?)$/i.test(before)&&/^\s+(?:must|should|need to) (?:begin|start|commence|proceed)\b/i.test(after.slice(policy.target.exec(after)?.[0].length||0))){states.push('support');continue;}
   if(T.wordCount(before)>16||/\b(?:that|which|language|wording|reported|noted|observed|has|had|was|were)\b/i.test(before))continue;
   if((new RegExp('^(?:'+policy.target.source+')\\s+(?:must|should|needs? to)\\s+be (?:maintained|implemented|ratified|respected|upheld|strengthened|supported|adopted|ensured|protected|allowed|facilitated|guaranteed|exercised|applied)\\b','i').test(after))||/\b(?:must|should|need to)\s+(?:(?:ensure|facilitate|allow|guarantee|protect|establish|achieve|secure|provide|respect|implement|uphold|strengthen|ratify|comply with|adhere to)\s+(?:(?:full|safe|rapid|sustained|unhindered|unimpeded|and|the|a|an)[, ]+)*)?$/i.test(before)||/^(?:humanitarian access|aid access|protection of civilians|civilian protection|(?:a |an |the )?(?:immediate |permanent |durable )?(?:ceasefire|cessation of hostilities))\s+(?:must|should|needs? to)\s+(?:be (?:ensured|allowed|facilitated|protected|established|achieved|guaranteed)|remain (?:unhindered|unimpeded))/i.test(after))states.push('support');
  }
 }
 if(!states.length)return null;
 if(qualified||uncertainObject||states.includes('qualified'))return 'qualified';
 return new Set(states).size===1?states[0]:'mixed';
}
function evidence(records,p){
 const policy=POLICIES.find(x=>x.id===p.positionPolicy),found=[],withheld={attribution:0,context:0,unclear:0};const seen=new Set();
 for(const r of records){
  if(!policy.target.test(r.text||''))continue;
  if(!national(r)){withheld.attribution++;continue;}
  if(P.unresolved(r)){withheld.unclear++;continue;}
  const sentences=T.sentences(r.text);
  sentences.forEach((line,index)=>{
   const adjacent=policy.adjacentDeclaration?.test(line)&&policy.precedingDeclaration.test(selfStatement(sentences[index-1]||'',r));
   const stance=direction(line,policy,r,sentences[index-1]);if(!stance)return;
   const c=context(line,r,policy)||(!policy.global&&!policy.cuba?{id:'unspecified',basis:'context_unestablished_not_comparable'}:null);if(!c||!contextsFor(policy).includes(c.id)||(p.positionContext!=='*'&&c.id!==p.positionContext)){withheld.context++;return;}
   if(policy.cuba&&(c.id!=='cuba'||!/\bCuba(?:n)?\b/i.test(r.text)))return;
   const url=safe(r.source_url);if(!url)return;
   const key=[country(r),r.date,line.toLowerCase().replace(/\s+/g,' ')].join('|');if(seen.has(key))return;seen.add(key);
   found.push({record_id:r.id,text_sha256:r.text_sha256,raw_sha256:r.raw_sha256||null,json_pointer:r.json_pointer||null,country:country(r),date:r.date,policy:policy.id,context:c.id,context_basis:c.basis,stance,...(stance==='qualified'&&(policy.qualifiedDeclaration?.test(selfStatement(line,r))||adjacent)?{qualification:policy.qualification}:{}),excerpt:adjacent?sentences[index-1]+' '+line:line,sentence_index:index,...(adjacent?{sentence_indices:[index-1,index]}:{}),source_url:url,attribution:'Recorded country affiliation; automatic provisional expression, not a verified government position'});
  });
 }
 return {found,withheld};
}
function state(rows){const dirs=new Set(rows.map(x=>x.stance));if(!rows.length)return 'missing';if(dirs.size===1)return [...dirs][0];return 'mixed';}
function build(records,baselineRecords,settings){
 const p={...settings,...options(settings)},policy=POLICIES.find(x=>x.id===p.positionPolicy),a=evidence(records,p),b=evidence(baselineRecords.filter(r=>isUS(r.country)),p);
 const withheldRecords=records.filter(r=>policy.target.test(r.text||'')&&(!national(r)||P.unresolved(r))).map(r=>({record_id:r.id,source_url:safe(r.source_url),attribution:P.attribution(r),reason:!national(r)?'not_an_unambiguous_national_statement':'unresolved_wording'}));
 if(!Number.isFinite(Date.parse(p.start))||!Number.isFinite(Date.parse(p.end))||p.end<p.start||(Date.parse(p.end)-Date.parse(p.start))/86400000>30)throw Error('Use an inclusive position comparison period of at most 31 days.');
 const dates=[];for(let t=Date.parse(p.start);t<=Date.parse(p.end);t+=86400000)dates.push(new Date(t).toISOString().slice(0,10));
 const names=[...new Set(records.filter(national).map(country))].filter(c=>c!==US).sort();if(p.positionCountry&&!names.includes(p.positionCountry))names.push(p.positionCountry);
 const ownIndex=new Map(),usIndex=new Map();
 for(const row of a.found){const key=row.country+'|'+row.date;if(!ownIndex.has(key))ownIndex.set(key,[]);ownIndex.get(key).push(row);}
 for(const row of b.found){if(!usIndex.has(row.date))usIndex.set(row.date,[]);usIndex.get(row.date).push(row);}
 const daysFor=name=>dates.map(date=>{
  const own=ownIndex.get(name+'|'+date)||[],us=usIndex.get(date)||[],ownState=state(own),usState=state(us);
  const comparable=!['unspecified','domestic'].includes(p.positionContext)&&['support','oppose'].includes(ownState)&&['support','oppose'].includes(usState);
  const comparison=p.positionContext==='domestic'?'domestic_not_comparable':p.positionContext==='unspecified'?'context_unestablished':comparable?(ownState===usState?'same_direction':'opposite_direction'):ownState==='missing'&&usState==='missing'?'both_missing':ownState==='missing'?'country_missing':usState==='missing'?'us_missing':'qualified_or_mixed';
  return {date,country_state:ownState,us_state:usState,comparison,value:comparable?(ownState===usState?0:1):null,country_evidence:own,us_evidence:us};
 });
 const countries=names.map(name=>{const days=daysFor(name),withEvidence=days.filter(d=>d.country_evidence.length),latest=withEvidence.at(-1);return {country:name,days,latest:latest||null,comparable_days:days.filter(d=>d.value!==null).length,gap_days:days.filter(d=>d.value===null).length};});
 const best=countries.slice().sort((x,y)=>y.comparable_days-x.comparable_days||y.days.filter(d=>d.country_evidence.length).length-x.days.filter(d=>d.country_evidence.length).length||x.country.localeCompare(y.country))[0];
 const selected=p.positionCountry||best?.country||null;
 return {schema:'un.explicit-position-comparison.v1',method:'bounded_policy_rules_same_day_no_imputation_v1',policy:{id:policy.id,label:policy.label,domain:policy.domain},context:{id:p.positionContext,label:CONTEXTS.find(c=>c.id===p.positionContext).label},baseline:US,selected_country:selected,start:p.start,end:p.end,countries,trajectory:countries.find(c=>c.country===selected)?.days||dates.map(date=>{const us=usIndex.get(date)||[];return {date,comparison:us.length?'country_missing':'both_missing',value:null,country_evidence:[],us_evidence:us,country_state:'missing',us_state:state(us)};}),us_days:dates.map(date=>({date,state:state(usIndex.get(date)||[]),evidence:usIndex.get(date)||[]})),withheld:a.withheld,withheld_records:withheldRecords,baseline_source_count:baselineRecords.filter(r=>isUS(r.country)).length,baseline_evidence_count:b.found.length,status:'automatic_provisional_not_human_reviewed',limitations:['Only expressed direction on the selected bounded policy question and context is compared. This is not overall diplomatic alignment or agreement on every condition, scope or implementation detail.','Position evidence is deduplicated separately within each country and date; identical wording from different countries is retained.','The U.S. baseline uses the same retained collection, dates, meeting scope, topic and exclusions, but ignores the speaker-region filter.','Both countries need explicit, unqualified evidence on the same calendar date. No past statement is carried forward and no missing value is interpolated.','Qualified, conflicting, collective, institutional, unresolved and merely descriptive wording cannot establish national alignment.','A change can come from the country, the U.S., or both. Inspect both dated statements; the chart does not establish a country policy shift.','These automatic rules cover a small, declared policy catalogue and can miss valid positions. Source affiliations and automatic transcript wording are not independently verified.'],external_ai_calls:0};
}

function overview(records,baselineRecords,settings){
 const questions=[];
 for(const policy of POLICIES){
  if(!records.concat(baselineRecords).some(r=>policy.target.test(r.text||'')))continue;
  const activeContexts=new Set(evidence(records.concat(baselineRecords),{positionPolicy:policy.id,positionContext:'*'}).found.map(x=>x.context));
  for(const ctx of CONTEXTS.filter(c=>activeContexts.has(c.id))){
   const q=build(records,baselineRecords,{...settings,positionPolicy:policy.id,positionContext:ctx.id,positionCountry:''});
   if(q.baseline_evidence_count||q.countries.some(c=>c.latest))questions.push(q);
  }
 }
 const names=[...new Set(records.filter(r=>r.country&&r.region!=='Unmapped').map(country))];
 if(baselineRecords.some(r=>isUS(r.country))&&!names.includes(US))names.push(US);
 const countries=names.sort().map(name=>{
  const positions=questions.flatMap(q=>{
   const days=name===US?q.us_days.map(d=>({date:d.date,country_state:d.state,country_evidence:d.evidence,us_state:d.state,us_evidence:d.evidence,comparison:'reference',value:null})):q.countries.find(c=>c.country===name)?.days||[];
   if(!days.some(d=>d.country_evidence.length))return [];
   return [{policy:q.policy,context:q.context,days,same:days.filter(d=>d.comparison==='same_direction').length,opposite:days.filter(d=>d.comparison==='opposite_direction').length,gaps:days.filter(d=>d.value===null).length}];
  });
  const same=positions.reduce((n,p)=>n+p.same,0),opposite=positions.reduce((n,p)=>n+p.opposite,0);
  const ownRecords=records.filter(r=>country(r)===name);
  const coverage_reason=positions.length?'identified':ownRecords.length&&!ownRecords.some(national)?'national_attribution_withheld':'no_supported_explicit_expression';
  const withheld_sources=positions.length?[]:ownRecords.filter(r=>!national(r)).map(r=>({record_id:r.id,source_url:safe(r.source_url),attribution:P.attribution(r).label,explicit_group:/\bon behalf of (?:the )?(?:Alliance of Small Island States|AOSIS)\b/i.test(String(r.text||'').slice(0,400))?'Alliance of Small Island States (AOSIS)':null}));
  return {country:name,positions,coverage_reason,withheld_sources,comparable_question_dates:same+opposite,same_direction:same,opposite_direction:opposite,agreement_percent:same+opposite?100*same/(same+opposite):null};
 });
 return {schema:'un.country-position-overview.v1',status:'automatic_provisional_not_human_reviewed',baseline:US,start:settings.start,end:settings.end,catalogue:POLICIES.map(p=>({id:p.id,label:p.label,domain:p.domain})),countries,questions,countries_with_positions:countries.filter(c=>c.positions.length).length,countries_comparable:countries.filter(c=>c.comparable_question_dates).length,weighting:'One comparison per policy question, context and calendar date, with equal weight. Source repetition adds no weight.',limitations:['This covers the declared policy catalogue, not every possible opinion in a meeting. Unrecognized or ambiguous positions remain unestablished.','Agreement is the share of comparable question-dates with the same expressed direction. It is not overall diplomatic alignment. Different countries can have different comparison coverage.','Policy questions can be related; question-date counts are not independent observations or a balanced index of diplomatic alignment.','Only explicit national expressions are compared. Group statements, unresolved wording and missing U.S. evidence cannot establish agreement.','No position is carried forward or interpolated. Statements on the same question and date are consolidated; conflicting or qualified evidence remains a gap.'],external_ai_calls:0};
}
const api={POLICIES,CONTEXTS,contextsFor,US,isUS,options,national,context,selfStatement,direction,evidence,build,overview};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.UNPositions=api;
})(typeof globalThis!=='undefined'?globalThis:this);

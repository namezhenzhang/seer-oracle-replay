from pathlib import Path
import json,html,csv,shutil
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.backends.backend_pdf import PdfPages
D=Path(__file__).resolve().parent;R=json.loads((D/'RESULT.json').read_text());V=json.loads((D/'VALIDATION.json').read_text())
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,'svg.fonttype':'none','text.color':'#19324a'})
colors=['#9BAABD','#007F86','#3178BD','#9D5CBB'];figs=[];joint=[]
for pair,title,scope in [('tmax','TMax-27B (27B)','Terminal-Bench 2.1 | 253 normal trials'),('deepswe','DeepSWE-Preview (32B)','SWE-bench Verified | 1,998 generations')]:
 r=R[pair];entries=[{'objective':'fifo','minutes':r['deadline_minutes'],'all_resource_hours':{k:r['baseline'][k]['hours'] for k in ['cpu','memory','gpu','storage']}}]+[next(v for v in V if v['pair']==pair and v['objective']==o) for o in ['cpu','gpu']+(['storage'] if pair=='deepswe' else [])]
 names=['FIFO baseline','CPU/RAM minimum: fastest found','GPU-hours: best found','Cache-hours: best found'][:len(entries)]
 fig,axs=plt.subplots(2,2,figsize=(13.5,9.5),facecolor='white');fig.subplots_adjust(left=.09,right=.97,top=.72,bottom=.15,hspace=.46,wspace=.30)
 fig.text(.09,.956,title+' — Resource-Hours by Schedule',fontsize=21,weight='bold')
 fig.text(.09,.91,f"{scope} | Completion time ≤ FIFO ({r['deadline_minutes']:,.2f} min)",fontsize=12,color='#536577')
 fig.legend(handles=[Patch(facecolor=colors[i],label=f"{name} · {e['minutes']:,.2f} min") for i,(name,e) in enumerate(zip(names,entries))],loc='upper left',bbox_to_anchor=(.08,.875),ncol=2,frameon=False,fontsize=10.5,columnspacing=2)
 for ax,res,ttl,unit in zip(axs.flat,['cpu','memory','gpu','storage'],['CPU','Memory','GPU','Storage: compressed image cache'],['core-hours','GiB-hours','GPU-hours','GiB-hours']):
  vals=[e['all_resource_hours'][res] for e in entries];ax.set_title(ttl,loc='left',fontsize=13,weight='bold',pad=11);ax.set_ylabel(unit);ax.set_xticks([]);ax.set_axisbelow(True);ax.grid(axis='y',alpha=.16)
  if vals[0] is None:
   ax.set_yticks([]);ax.text(.5,.45,'Not measured',transform=ax.transAxes,ha='center',color='#718293',fontsize=16);continue
  mx=max(vals);ax.set_ylim(0,mx*1.37);ax.set_xlim(-.65,len(vals)-.35)
  for i,v in enumerate(vals):
   ax.bar(i,v,width=.61,color=colors[i]);ax.text(i,v+mx*.025,f'{v:,.2f}',ha='center',weight='bold',fontsize=10.5)
   if i:ax.text(i,v+mx*.12,f'−{100*(1-v/vals[0]):.1f}%',ha='center',weight='bold',color=colors[i],fontsize=11)
 for name,e in zip(names,entries):joint.append({'pair':pair,'schedule':name,'minutes':e['minutes'],**e['all_resource_hours']})
 fig.text(.09,.083,'Same color = the SAME complete schedule across all four panels. Scales are independent.',fontsize=11,weight='bold')
 msg='CPU + RAM + best-found GPU-hours are attained together by the blue schedule.' if pair=='tmax' else 'CPU/RAM minima coexist with either objective; best-found GPU and cache values use different schedules.'
 fig.text(.09,.055,msg,fontsize=10.5)
 fig.text(.09,.026,'Fixed trace timings; zero transition cost. CPU/RAM: quota-hours. GPU/cache optima are not globally proven.',fontsize=10,color='#536577')
 for ext in ['png','pdf','svg']:fig.savefig(D/f'{pair}_min_hours_schedules.{ext}',dpi=200,facecolor='white')
 figs.append(fig)
with PdfPages(D/'resource_hours_by_schedule.pdf') as pdf:
 for fig in figs:pdf.savefig(fig)
with (D/'joint_schedules.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(joint[0]));w.writeheader();w.writerows(joint)
rows=[['Workload / schedule','CPU core-hours','Memory GiB-hours','GPU-hours','Cache GiB-hours','Completion (min)']]
for r in joint:
 if r['schedule']=='FIFO baseline':continue
 rows.append([('TMax' if r['pair']=='tmax' else 'DeepSWE')+' / '+r['schedule'],*[('—' if r[k] is None else f'{r[k]:,.2f}') for k in ['cpu','memory','gpu','storage']],f"{r['minutes']:,.2f}"])
text='''### Which minima can be attained together?

The values above were selected separately by objective. The table below instead reports complete schedules: every value within a row is attained simultaneously in the replay. CPU and memory totals are invariant across phase-reclaim schedules. TMax attains the reported CPU, memory and best-found GPU values together at 129.21 minutes (storage unavailable). For DeepSWE, both GPU-optimized and cache-optimized schedules attain the CPU/RAM minima, but the best-found GPU and cache values are not attained together by any selected schedule. This does not prove that a joint optimum is impossible.

'''
text+='<table header-row="true" fit-page-width="true">\n'+''.join('<tr>'+''.join('<td>'+html.escape(x)+'</td>' for x in row)+'</tr>\n' for row in rows)+'</table>\n\n'
(D/'JOINT_NOTION.txt').write_text(text)
v=Path('/home/chengzhiliu_google_com/zhenzhang/cx/visualizations/2026/10/20/01a15ab3-0010-7482-bbf0-89e617723c1a/seer-runtime/min-hours');v.mkdir(exist_ok=True)
for p in D.iterdir():
 if p.is_file() and not p.name.endswith('.upload.json'):shutil.copy2(p,v/p.name)
print('Rendered two charts and joint-schedule table.')

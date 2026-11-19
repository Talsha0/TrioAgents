import argparse
import datetime as dt
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.formatting.rule import CellIsRule, FormulaRule

F='Arial'
def font(**k): return Font(name=F,size=k.pop('size',11),**k)
HDR_IN=PatternFill('solid',fgColor='0E7C6B'); HDR_CALC=PatternFill('solid',fgColor='6B7B78')
INFILL=PatternFill('solid',fgColor='FFF9DB'); SUMFILL=PatternFill('solid',fgColor='E6F2EF')
thin=Side(style='thin',color='D0D8D6'); BR=Border(left=thin,right=thin,top=thin,bottom=thin)
MONEY='#,##0.00;[Red]-#,##0.00;-'; PCT='0%'

wb=Workbook()
def sheet(name,first=False):
    ws=wb.active if first else wb.create_sheet()
    ws.title=name; ws.sheet_view.rightToLeft=True; return ws
def hdr(ws,row,labels,calc_from=None,widths=None):
    for i,l in enumerate(labels,1):
        c=ws.cell(row,i,l); c.font=font(bold=True,color='FFFFFF'); c.alignment=Alignment(horizontal='center',vertical='center',wrap_text=True)
        c.fill=HDR_CALC if (calc_from and i>=calc_from) else HDR_IN; c.border=BR
    ws.row_dimensions[row].height=34
    if widths:
        for i,w in enumerate(widths,1): ws.column_dimensions[ws.cell(1,i).column_letter].width=w
def body(ws,r1,r2,ncols,input_cols,fmt=None):
    for r in range(r1,r2+1):
        for c in range(1,ncols+1):
            x=ws.cell(r,c); x.font=font(); x.border=BR
            if c in input_cols: x.fill=INFILL
            if fmt and c in fmt: x.number_format=fmt[c]

# ---------- instructions
wi=sheet('הוראות',True)
lines=[('הנהלת חשבונות – סוכנות נסיעות',True),('',False),
('איך עובדים עם הקובץ',True),
('1. הגדרות: מזינות את אחוז המע״מ ואת רשימת הסוכנים עם האחוז של כל סוכן/ת מהרווח (למשל 50% או 40%).',False),
('2. תיקים: שורה לכל תיק. בוחרים סוכן/ת, מזינים חודש (תאריך כלשהו בחודש), שם תיק וסטטוס (פתוח/סגור). מפתח התיק נוצר לבד.',False),
('3. תנועות: שורה לכל הכנסה או הוצאה. בוחרים תיק מהרשימה (ריק = הוצאה/הכנסה כללית), סוג, סכום, האם הסכום כולל מע״מ, ומע״מ רגיל או פטור.',False),
('4. תשלומים: שורה לכל מקדמה, תשלום סופי, הלוואה או החזר הלוואה. בשדה "תיק" בוחרים תיק (חובה למקדמה ותשלום סופי שקשורים לתיק מסוים).',False),
('5. הסיכומים (סיכום סוכנים, סיכום חודשי, סיכום כללי) מתעדכנים לבד. אין צורך להזין בהם כלום.',False),
('',False),('מקרא צבעים',True),
('תאים בצהוב בהיר: להזנה. כותרת ירוקה = עמודת הזנה. כותרת אפורה = חישוב אוטומטי, לא לגעת.',False),
('',False),('שימו לב',True),
('• השורות עם המילה "דוגמה" הן להמחשה בלבד. אפשר למחוק את תוכן התאים הצהובים שלהן ולהתחיל להזין.',False),
('• מפתח התיק מורכב משם הסוכן/ת, שם התיק והחודש. אם שני תיקים זהים בשלושתם, החישובים יתערבבו. תנו להם שמות שונים.',False),
('• יתרה שלילית אצל סוכן/ת = שולם לה יותר ממה שמגיע. הלוואה פתוחה מקוזזת ב"נטו אחרי קיזוז הלוואה".',False),
('• הרווח מחושב לפני מע״מ. המע״מ לתשלום = מע״מ עסקאות פחות מע״מ תשומות.',False),
('• מקום להזנה: עד 300 תיקים ו־2,000 תנועות ותשלומים. אם נגמר, מעתיקים את הנוסחאות שורה למטה.',False),
('• הקובץ לא מחליף ייעוץ של רואה חשבון. כדאי לאשר איתו איך לסווג מע״מ בעסקאות מסוימות.',False)]
for i,(t,b) in enumerate(lines,1):
    c=wi.cell(i,1,t); c.font=font(bold=b,size=14 if i==1 else 11); c.alignment=Alignment(wrap_text=True,vertical='top')
wi.column_dimensions['A'].width=120

# ---------- settings
ws=sheet('הגדרות')
ws['A1']='אחוז מע״מ'; ws['B1']=0.18; ws['B1'].number_format='0.0%'
ws['A2']='שנה לסיכום חודשי'; ws['B2']=2026
ws['C1']='בדקו שזה האחוז העדכני'; ws['C1'].font=font(italic=True,color='6B7B78')
for r in (1,2):
    ws.cell(r,1).font=font(bold=True); ws.cell(r,2).font=font(color='0000FF'); ws.cell(r,2).fill=INFILL; ws.cell(r,2).border=BR
hdr(ws,4,['שם סוכן/ת','אחוז הסוכן/ת מהרווח'],widths=[30,22])
body(ws,5,24,2,{1,2},{2:PCT})
for r,(n,p) in zip((5,6),(('סוכנת א׳ (דוגמה)',0.5),('סוכנת ב׳ (דוגמה)',0.4))):
    ws.cell(r,1,n); ws.cell(r,2,p)
ws['D4']='האחוז שמופיע ליד כל סוכן/ת הוא החלק שלה מהרווח. השאר שלך.'; ws['D4'].font=font(italic=True,color='6B7B78')
ws.freeze_panes='A5'

# ---------- cases
wc=sheet('תיקים'); N=301
hdr(wc,1,['מפתח התיק (אוטומטי)','סוכן/ת','חודש (תאריך בחודש)','שם התיק / לקוח','סטטוס','הכנסות לפני מע״מ','מע״מ הכנסות','הוצאות לפני מע״מ','מע״מ הוצאות','רווח לפני מע״מ','אחוז הסוכן/ת','חלק הסוכן/ת','החלק שלי','שולם (מקדמות ותשלומים)','יתרה לתשלום','מצב','מפתח חודש'],
    calc_from=6,widths=[44,22,16,28,12,16,14,16,14,16,12,16,16,18,16,22,12])
wc.cell(1,1).fill=HDR_CALC
for c in (2,3,4,5): wc.cell(1,c).fill=HDR_IN
body(wc,2,N,17,{2,3,4,5},{3:'mm/yyyy',**{c:MONEY for c in (6,7,8,9,10,12,13,14,15)},11:PCT})
T="'תנועות'!"; P="'תשלומים'!"
def rng(sh,col,last): return f"{sh}${col}$2:${col}${last}"
for r in range(2,N+1):
    wc[f'A{r}']=f'=IF(D{r}="","",B{r}&" | "&D{r}&" | "&MONTH(C{r})&"/"&YEAR(C{r}))'
    def tsum(col,typ): return f'=IF($A{r}="","",SUMIFS({rng(T,col,2001)},{rng(T,"B",2001)},$A{r},{rng(T,"C",2001)},"{typ}"))'
    wc[f'F{r}']=tsum('H','הכנסה'); wc[f'G{r}']=tsum('I','הכנסה'); wc[f'H{r}']=tsum('H','הוצאה'); wc[f'I{r}']=tsum('I','הוצאה')
    wc[f'J{r}']=f'=IF($A{r}="","",F{r}-H{r})'
    wc[f'K{r}']=f'=IF($A{r}="","",IFERROR(INDEX(\'הגדרות\'!$B$5:$B$24,MATCH(B{r},\'הגדרות\'!$A$5:$A$24,0)),0))'
    wc[f'L{r}']=f'=IF($A{r}="","",J{r}*K{r})'; wc[f'M{r}']=f'=IF($A{r}="","",J{r}-L{r})'
    wc[f'N{r}']=f'=IF($A{r}="","",SUMIFS({rng(P,"E",2001)},{rng(P,"D",2001)},$A{r},{rng(P,"C",2001)},"מקדמה")+SUMIFS({rng(P,"E",2001)},{rng(P,"D",2001)},$A{r},{rng(P,"C",2001)},"תשלום סופי"))'
    wc[f'O{r}']=f'=IF($A{r}="","",L{r}-N{r})'
    wc[f'P{r}']=f'=IF($A{r}="","",IF(E{r}="סגור",IF(O{r}<-0.005,"שולם יותר מדי",IF(ABS(O{r})<=0.005,"שולם במלואו","נשאר לשלם")),IF(N{r}>L{r}+0.005,"מקדמה גבוהה מהחלק","פתוח")))'
    wc[f'Q{r}']=f'=IF(C{r}="","",YEAR(C{r})*100+MONTH(C{r}))'
wc['B2']='סוכנת א׳ (דוגמה)'; wc['C2']=dt.date(2026,11,1); wc['D2']='משפחת כהן – רומא (דוגמה)'; wc['E2']='סגור'
dv=DataValidation(type='list',formula1="='הגדרות'!$A$5:$A$24",allow_blank=True); wc.add_data_validation(dv); dv.add(f'B2:B{N}')
dv2=DataValidation(type='list',formula1='"פתוח,סגור"',allow_blank=True); wc.add_data_validation(dv2); dv2.add(f'E2:E{N}')
wc.conditional_formatting.add(f'P2:P{N}',FormulaRule(formula=['$P2="שולם יותר מדי"'],font=Font(name=F,bold=True,color='B4452F')))
wc.conditional_formatting.add(f'P2:P{N}',FormulaRule(formula=['$P2="מקדמה גבוהה מהחלק"'],font=Font(name=F,bold=True,color='B4452F')))
wc.freeze_panes='B2'

# ---------- transactions
wt=sheet('תנועות')
hdr(wt,1,['תאריך','תיק (ריק = כללי)','סוג','תיאור','סכום (₪)','הסכום','מע״מ','לפני מע״מ','סכום מע״מ','כולל מע״מ'],calc_from=8,widths=[14,44,12,32,16,12,12,16,14,16])
body(wt,2,2001,10,{1,2,3,4,5,6,7},{1:'dd/mm/yyyy',5:MONEY,8:MONEY,9:MONEY,10:MONEY})
for r in range(2,2002):
    rate=f"IF(G{r}=\"פטור\",0,'הגדרות'!$B$1)"
    wt[f'H{r}']=f'=IF(OR(E{r}="",C{r}=""),"",IF(F{r}="כולל",E{r}/(1+{rate}),E{r}))'
    wt[f'I{r}']=f'=IF(H{r}="","",H{r}*{rate})'
    wt[f'J{r}']=f'=IF(H{r}="","",H{r}+I{r})'
ex=[(dt.date(2026,11,3),'סוכנת א׳ (דוגמה) | משפחת כהן – רומא (דוגמה) | 11/2026','הכנסה','חבילת נופש',11800,'כולל','רגיל'),
    (dt.date(2026,11,4),'סוכנת א׳ (דוגמה) | משפחת כהן – רומא (דוגמה) | 11/2026','הוצאה','מלון ברומא',5900,'כולל','רגיל'),
    (dt.date(2026,11,5),'סוכנת א׳ (דוגמה) | משפחת כהן – רומא (דוגמה) | 11/2026','הוצאה','טיסות',2000,'לפני','פטור'),
    (dt.date(2026,11,6),None,'הוצאה','תוכנת הזמנות (כללי)',118,'כולל','רגיל')]
for i,row in enumerate(ex,2):
    for c,v in enumerate(row,1):
        if v is not None: wt.cell(i,c,v)
for col,lst in (('B',"='תיקים'!$A$2:$A$301"),('C','"הכנסה,הוצאה"'),('F','"כולל,לפני"'),('G','"רגיל,פטור"')):
    d=DataValidation(type='list',formula1=lst,allow_blank=True); wt.add_data_validation(d); d.add(f'{col}2:{col}2001')
wt.freeze_panes='A2'

# ---------- payments
wp=sheet('תשלומים')
hdr(wp,1,['תאריך','סוכן/ת','סוג','תיק (למקדמה / תשלום סופי)','סכום (₪)','שייך לתיק?'],calc_from=6,widths=[14,24,16,44,16,14])
body(wp,2,2001,6,{1,2,3,4,5},{1:'dd/mm/yyyy',5:MONEY})
for r in range(2,2002): wp[f'F{r}']=f'=IF(E{r}="","",IF(D{r}="","כללי","תיק"))'
for i,row in enumerate([(dt.date(2026,11,10),'סוכנת א׳ (דוגמה)','מקדמה','סוכנת א׳ (דוגמה) | משפחת כהן – רומא (דוגמה) | 11/2026',1000),
                        (dt.date(2026,11,12),'סוכנת א׳ (דוגמה)','הלוואה',None,500)],2):
    for c,v in enumerate(row,1):
        if v is not None: wp.cell(i,c,v)
for col,lst in (('B',"='הגדרות'!$A$5:$A$24"),('C','"מקדמה,תשלום סופי,הלוואה,החזר הלוואה"'),('D',"='תיקים'!$A$2:$A$301")):
    d=DataValidation(type='list',formula1=lst,allow_blank=True); wp.add_data_validation(d); d.add(f'{col}2:{col}2001')
wp.freeze_panes='A2'

# ---------- agents summary
wa=sheet('סיכום סוכנים')
hdr(wa,1,['סוכן/ת','אחוז','חלק מתיקים סגורים','שולם על תיקים סגורים','תשלומים כלליים (בלי תיק)','יתרה לתשלום (תיקים סגורים)','הלוואות שניתנו','החזרי הלוואה','חוב הלוואה פתוח','נטו אחרי קיזוז הלוואה','חלק צפוי מתיקים פתוחים','מקדמות על תיקים פתוחים','מצב'],calc_from=1,widths=[26,9,16,16,16,18,14,14,16,18,18,18,26])
body(wa,2,21,13,set(),{2:PCT,**{c:MONEY for c in range(3,13)}})
C="'תיקים'!"
for k in range(20):
    r=2+k; s=5+k; A=f'$A{r}'
    wa[f'A{r}']=f"=IF('הגדרות'!A{s}=\"\",\"\",'הגדרות'!A{s})"
    wa[f'B{r}']=f"=IF({A}=\"\",\"\",'הגדרות'!B{s})"
    def cs(col,st): return f'=IF({A}="","",SUMIFS({rng(C,col,301)},{rng(C,"B",301)},{A},{rng(C,"E",301)},"{st}"))'
    wa[f'C{r}']=cs('L','סגור'); wa[f'D{r}']=cs('N','סגור'); wa[f'K{r}']=cs('L','פתוח'); wa[f'L{r}']=cs('N','פתוח')
    wa[f'E{r}']=f'=IF({A}="","",SUMIFS({rng(P,"E",2001)},{rng(P,"B",2001)},{A},{rng(P,"C",2001)},"מקדמה",{rng(P,"F",2001)},"כללי")+SUMIFS({rng(P,"E",2001)},{rng(P,"B",2001)},{A},{rng(P,"C",2001)},"תשלום סופי",{rng(P,"F",2001)},"כללי"))'
    wa[f'F{r}']=f'=IF({A}="","",C{r}-D{r}-E{r})'
    wa[f'G{r}']=f'=IF({A}="","",SUMIFS({rng(P,"E",2001)},{rng(P,"B",2001)},{A},{rng(P,"C",2001)},"הלוואה"))'
    wa[f'H{r}']=f'=IF({A}="","",SUMIFS({rng(P,"E",2001)},{rng(P,"B",2001)},{A},{rng(P,"C",2001)},"החזר הלוואה"))'
    wa[f'I{r}']=f'=IF({A}="","",G{r}-H{r})'; wa[f'J{r}']=f'=IF({A}="","",F{r}-I{r})'
    wa[f'M{r}']=f'=IF({A}="","",IF(J{r}<-0.005,"שולם יותר מדי",IF(ABS(J{r})<=0.005,"מאוזן","נשאר לשלם")))'
wa['A22']='סה״כ'; 
for c in 'CDEFGHIJKL': wa[f'{c}22']=f'=SUM({c}2:{c}21)'; wa[f'{c}22'].number_format=MONEY
for c in range(1,14): wa.cell(22,c).font=font(bold=True); wa.cell(22,c).fill=SUMFILL; wa.cell(22,c).border=BR
wa.conditional_formatting.add('J2:J21',CellIsRule(operator='lessThan',formula=['-0.005'],font=Font(name=F,bold=True,color='B4452F')))
wa.freeze_panes='B2'

# ---------- monthly
wm=sheet('סיכום חודשי')
wm['A1']='סיכום לפי חודש התיק, לשנה שנבחרה בהגדרות'; wm['A1'].font=font(bold=True,size=13)
hdr(wm,3,['חודש','מפתח','הכנסות לפני מע״מ','הוצאות לפני מע״מ','רווח לפני מע״מ','מע״מ הכנסות','מע״מ הוצאות','מע״מ לתשלום (שלילי = להחזר)','חלק הסוכנים','החלק שלי','שולם לסוכנים בחודש (לפי תאריך תשלום)'],calc_from=1,widths=[10,10,18,18,18,16,16,20,18,18,24])
body(wm,4,15,11,set(),{**{c:MONEY for c in range(3,12)}})
for m in range(1,13):
    r=3+m
    wm[f'A{r}']=m; wm[f'B{r}']=f"='הגדרות'!$B$2*100+A{r}"
    for col,src in (('C','F'),('D','H'),('F','G'),('G','I'),('I','L')):
        wm[f'{col}{r}']=f'=SUMIFS({rng(C,src,301)},{rng(C,"Q",301)},$B{r})'
    wm[f'E{r}']=f'=C{r}-D{r}'; wm[f'H{r}']=f'=F{r}-G{r}'; wm[f'J{r}']=f'=E{r}-I{r}'
    lo=f"DATE('הגדרות'!$B$2,$A{r},1)"; hi=f"DATE('הגדרות'!$B$2,$A{r}+1,1)"
    wm[f'K{r}']=''.join(f'{"=" if i==0 else "+"}SUMIFS({rng(P,"E",2001)},{rng(P,"C",2001)},"{t}",{rng(P,"A",2001)},">="&{lo},{rng(P,"A",2001)},"<"&{hi})' for i,t in enumerate(('מקדמה','תשלום סופי')))
wm['A16']='סה״כ שנה'
for c in 'CDEFGHIJK': wm[f'{c}16']=f'=SUM({c}4:{c}15)'; wm[f'{c}16'].number_format=MONEY
for c in range(1,12): wm.cell(16,c).font=font(bold=True); wm.cell(16,c).fill=SUMFILL; wm.cell(16,c).border=BR
wm['A18']='חלק כל סוכן/ת מהרווח, לפי חודש'; wm['A18'].font=font(bold=True,size=13)
hdr(wm,19,['חודש','מפתח']+['']*10,calc_from=1)
for j in range(10):
    c=wm.cell(19,3+j,f"=IF('הגדרות'!A{5+j}=\"\",\"\",'הגדרות'!A{5+j})")
for m in range(1,13):
    r=19+m; wm[f'A{r}']=m; wm[f'B{r}']=f"='הגדרות'!$B$2*100+A{r}"
    for j in range(10):
        col=wm.cell(r,3+j).column_letter
        wm.cell(r,3+j,f'=IF({col}$19="","",SUMIFS({rng(C,"L",301)},{rng(C,"B",301)},{col}$19,{rng(C,"Q",301)},$B{r}))')
        wm.cell(r,3+j).number_format=MONEY; wm.cell(r,3+j).font=font(); wm.cell(r,3+j).border=BR
    wm.cell(r,1).font=font(); wm.cell(r,2).font=font()
wm.column_dimensions['L'].width=14
wm.freeze_panes='A4'

# ---------- overall
wg=sheet('סיכום כללי')
hdr(wg,1,['פריט','לפני מע״מ','מע״מ','כולל מע״מ'],calc_from=1,widths=[44,18,18,18])
def tt(col,typ): return f'SUMIFS({rng(T,col,2001)},{rng(T,"C",2001)},"{typ}")'
rows=[('הכנסות',f'={tt("H","הכנסה")}',f'={tt("I","הכנסה")}',f'={tt("J","הכנסה")}'),
('הוצאות',f'={tt("H","הוצאה")}',f'={tt("I","הוצאה")}',f'={tt("J","הוצאה")}'),
('הפרש (רווח / מע״מ לתשלום)','=B2-B3','=C2-C3','=D2-D3')]
for i,rw in enumerate(rows,2):
    for c,v in enumerate(rw,1): wg.cell(i,c,v)
extra=[('חלק הסוכנים מהרווח',f"=SUM({rng(C,'L',301)})"),('החלק שלי מהרווח (לפני מע״מ)','=B4-B6'),
('סה״כ שולם לסוכנים (מקדמות ותשלומים)',f'=SUMIFS({rng(P,"E",2001)},{rng(P,"C",2001)},"מקדמה")+SUMIFS({rng(P,"E",2001)},{rng(P,"C",2001)},"תשלום סופי")'),
('חוב הלוואות פתוח אצל הסוכנים',"='סיכום סוכנים'!I22")]
for i,(l,f_) in enumerate(extra,6): wg.cell(i,1,l); wg.cell(i,2,f_)
wg['A11']='מע״מ לתשלום (שלילי = להחזר)'; wg['B11']='=C4'
for r in range(2,12):
    for c in range(1,5):
        x=wg.cell(r,c); x.font=font(bold=(r in (4,7,11))); x.border=BR
        if c>1: x.number_format=MONEY
for r in (4,7,11):
    for c in range(1,5): wg.cell(r,c).fill=SUMFILL
wb.move_sheet('סיכום כללי',offset=0)
DEFAULT_OUT = Path(__file__).resolve().parent.parent / 'template' / 'bookkeeping-shared.xlsx'
ap = argparse.ArgumentParser(description='Build the bookkeeping Excel template.')
ap.add_argument('-o', '--output', type=Path, default=DEFAULT_OUT, help=f'output path (default: {DEFAULT_OUT})')
out = ap.parse_args().output
out.parent.mkdir(parents=True, exist_ok=True)
wb.save(out)
print(f'Saved {out}')

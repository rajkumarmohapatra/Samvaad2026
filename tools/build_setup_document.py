"""Build DOCX/PDF and exact plain-text copy blocks from the setup workbook."""
import html
import json
import re
import textwrap
import zipfile
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Preformatted, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

R=Path(__file__).resolve().parents[1]
source=R/'user-guides/SAMBAD-360-Step-by-Step-Setup.md'
text=source.read_text();pack=R/'user-guides/setup-copy-pack';pack.mkdir(exist_ok=True)
blocks=re.findall(r'```([^\n]*)\n(.*?)```',text,re.S)
manifest=[]
for n,(lang,code) in enumerate(blocks,1):
 first=next((l for l in code.splitlines() if l.strip()),'snippet')
 label=re.sub('[^A-Za-z0-9]+','-',first).strip('-')[:65]
 name=f'{n:02d}-{label}.txt'
 (pack/name).write_text(code.rstrip()+'\n')
 manifest.append(dict(item=n,file=name,language=lang.strip(),first_line=first))
(pack/'INDEX.json').write_text(json.dumps(manifest,indent=2)+'\n')
(pack/'README.txt').write_text('SAMBAD 360 - exact copy blocks\n\nRead the Word/PDF/Markdown guide first. Files are numbered in document order.\nCopy only into the control property, action or console identified in the guide.\nReplace configuration values enclosed in angle brackets. Never paste a password or token.\nPower Fx examples use English authoring separators and classic Text input/Drop down controls.\nThese snippets have not been compiled or tested in a Microsoft tenant.\n')

# Parse small, intentionally constrained Markdown source.
lines=text.splitlines();tokens=[];i=0
while i<len(lines):
 line=lines[i]
 if line.startswith('```'):
  lang=line[3:];code=[];i+=1
  while i<len(lines) and not lines[i].startswith('```'):code.append(lines[i]);i+=1
  tokens.append(('code','\n'.join(code),lang));i+=1;continue
 if line.startswith('|'):
  rows=[]
  while i<len(lines) and lines[i].startswith('|'):
   cells=[c.strip() for c in lines[i].strip().strip('|').split('|')]
   if not all(re.fullmatch(r':?-+:?',c) for c in cells):rows.append(cells)
   i+=1
  tokens.append(('table',rows));continue
 if line.strip():
  m=re.match(r'^(#{1,3}) (.*)',line)
  tokens.append(('heading',m.group(2),len(m.group(1))) if m else ('paragraph',line))
 i+=1

GREEN='194F40';MUTED='62736C';GOLD='E7B56C'
doc=Document();section=doc.sections[0];section.top_margin=Inches(.65);section.bottom_margin=Inches(.65);section.left_margin=Inches(.7);section.right_margin=Inches(.7)
styles=doc.styles
styles['Normal'].font.name='Calibri';styles['Normal'].font.size=Pt(10)
styles['Normal'].paragraph_format.space_after=Pt(7)
for s in ['Title','Heading 1','Heading 2','Heading 3']:
 styles[s].font.name='Calibri';styles[s].font.color.rgb=RGBColor.from_string(GREEN)
styles['Heading 1'].font.size=Pt(19);styles['Heading 2'].font.size=Pt(14);styles['Heading 3'].font.size=Pt(11)
if 'Code Block' not in styles:styles.add_style('Code Block',1)
styles['Code Block'].font.name='Consolas';styles['Code Block'].font.size=Pt(8)
styles['Code Block'].paragraph_format.space_after=Pt(1)
styles['Code Block'].paragraph_format.space_before=Pt(0)
styles['Code Block'].paragraph_format.line_spacing=1
header=section.header.paragraphs[0];header.text='SAMBAD 360  |  MICROSOFT 365 SETUP WORKBOOK';header.style='Caption'
footer=section.footer.paragraphs[0];footer.text='Version 1.0  |  28 October 2026  |  Synthetic pilot only                      Page '
fld=OxmlElement('w:fldSimple');fld.set(qn('w:instr'),'PAGE');footer._p.append(fld)
footer.style='Caption'

def inline_doc(p,s):
 for part in re.split(r'(\*\*.*?\*\*|`[^`]+`)',s):
  run=p.add_run(part[2:-2] if part.startswith('**') else part[1:-1] if part.startswith('`') else part)
  if part.startswith('**'):run.bold=True
  if part.startswith('`'):run.font.name='Consolas';run.font.size=Pt(9)

def shade(cell,fill):
 pr=cell._tc.get_or_add_tcPr();x=OxmlElement('w:shd');x.set(qn('w:fill'),fill);pr.append(x)

code_number=0
for token in tokens:
 kind=token[0]
 if kind=='heading':
  title,level=token[1:]
  if level==1 and re.match(r'^(\d+\.|Appendix)',title):
   p=doc.add_heading(title,level=1);p.paragraph_format.page_break_before=True
  else:doc.add_heading(title,level=level if level<3 else 3)
 elif kind=='paragraph':
  p=doc.add_paragraph();inline_doc(p,token[1])
 elif kind=='code':
  code_number+=1;p=doc.add_paragraph(f'COPY ITEM {code_number:02d}  |  {manifest[code_number-1]["file"]}');p.style='Caption'
  p.paragraph_format.keep_with_next=True
  for line in token[1].splitlines():
   p=doc.add_paragraph(style='Code Block');p.add_run(line or ' ')
   pr=p._p.get_or_add_pPr();sh=OxmlElement('w:shd');sh.set(qn('w:fill'),'F0F4F0');pr.append(sh)
  doc.add_paragraph().paragraph_format.space_after=Pt(2)
 elif kind=='table':
  rows=token[1];count=max(map(len,rows));table=doc.add_table(rows=0,cols=count);table.style='Light Shading Accent 1'
  for index,row in enumerate(rows):
   cells=table.add_row().cells
   for k,value in enumerate(row):
    p=cells[k].paragraphs[0];inline_doc(p,value)
    for run in p.runs:run.font.size=Pt(8.5)
    if index==0:
     shade(cells[k],GREEN)
     for run in p.runs:run.bold=True;run.font.color.rgb=RGBColor(255,255,255)
   pr=table.rows[-1]._tr.get_or_add_trPr();pr.append(OxmlElement('w:cantSplit'))
   if index==0:
    repeat=OxmlElement('w:tblHeader');pr.append(repeat)
  doc.add_paragraph().paragraph_format.space_after=Pt(2)
docx_path=source.with_suffix('.docx');doc.save(docx_path)

# PDF mirror. Standard fonts keep it portable; code is embedded DejaVu Mono when available.
fontroot=Path('/usr/share/fonts/truetype/dejavu')
if (fontroot/'DejaVuSans.ttf').exists():
 pdfmetrics.registerFont(TTFont('GuideSans',str(fontroot/'DejaVuSans.ttf')))
 pdfmetrics.registerFont(TTFont('GuideSans-Bold',str(fontroot/'DejaVuSans-Bold.ttf')))
 pdfmetrics.registerFontFamily('GuideSans',normal='GuideSans',bold='GuideSans-Bold',italic='GuideSans',boldItalic='GuideSans-Bold')
 pdfmetrics.registerFont(TTFont('GuideMono',str(fontroot/'DejaVuSansMono.ttf')))
 normal='GuideSans';bold='GuideSans-Bold';mono='GuideMono'
else:normal='Helvetica';bold='Helvetica-Bold';mono='Courier'
ss=getSampleStyleSheet()
ss.add(ParagraphStyle('GuideBody',fontName=normal,fontSize=9,leading=13,spaceAfter=7))
ss.add(ParagraphStyle('GuideH1',fontName=bold,fontSize=18,leading=23,textColor=colors.HexColor('#'+GREEN),spaceAfter=13,keepWithNext=True))
ss.add(ParagraphStyle('GuideH2',fontName=bold,fontSize=12,leading=17,textColor=colors.HexColor('#'+GREEN),spaceAfter=9,keepWithNext=True))
ss.add(ParagraphStyle('GuideH3',fontName=bold,fontSize=10,leading=14,textColor=colors.HexColor('#'+GREEN),spaceAfter=7,keepWithNext=True))
ss.add(ParagraphStyle('GuideCell',fontName=normal,fontSize=7.6,leading=10))
ss.add(ParagraphStyle('GuideCode',fontName=mono,fontSize=7.4,leading=10,backColor=colors.HexColor('#F0F4F0'),borderPadding=7,spaceAfter=9))
ss.add(ParagraphStyle('GuideCaption',fontName=bold,fontSize=6.7,leading=9,textColor=colors.HexColor('#'+MUTED),spaceAfter=4,keepWithNext=True))

def inline_pdf(s):
 s=html.escape(s)
 s=re.sub(r'\*\*(.*?)\*\*',r'<b>\1</b>',s)
 s=re.sub(r'`([^`]+)`',r'<font name="'+mono+r'">\1</font>',s)
 return s

story=[];code_number=0
for token in tokens:
 if token[0]=='heading':
  title,level=token[1:]
  if level==1 and re.match(r'^(\d+\.|Appendix)',title):story.append(PageBreak())
  story.append(Paragraph(inline_pdf(title),ss['GuideH'+str(level)]))
 elif token[0]=='paragraph':story.append(Paragraph(inline_pdf(token[1]),ss['GuideBody']))
 elif token[0]=='code':
  code_number+=1;story.append(Paragraph(f'COPY ITEM {code_number:02d} | {manifest[code_number-1]["file"]}',ss['GuideCaption']))
  wrapped=[]
  for line in token[1].splitlines():wrapped.extend(textwrap.wrap(line,105,replace_whitespace=False,drop_whitespace=False) or [''])
  story.append(Preformatted('\n'.join(wrapped),ss['GuideCode']))
 elif token[0]=='table':
  rows=token[1];count=max(map(len,rows));width=(A4[0]-88)/count
  data=[[Paragraph(inline_pdf(c),ss['GuideCell']) for c in row]+['']*(count-len(row)) for row in rows]
  table=Table(data,colWidths=[width]*count,repeatRows=1,hAlign='LEFT')
  table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#DFEAE2')),('GRID',(0,0),(-1,-1),.3,colors.HexColor('#CFD9D0')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
  story.extend([table,Spacer(1,9)])

def page(canvas,doc):
 canvas.saveState();canvas.setFont(normal,7);canvas.setFillColor(colors.HexColor('#'+MUTED))
 canvas.drawString(44,A4[1]-25,'SAMBAD 360 | Microsoft 365 setup workbook')
 canvas.drawString(44,25,'28 October 2026 | Synthetic pilot only')
 canvas.drawRightString(A4[0]-44,25,f'Page {doc.page}')
 canvas.restoreState()
pdf_path=source.with_suffix('.pdf')
SimpleDocTemplate(str(pdf_path),pagesize=A4,rightMargin=44,leftMargin=44,topMargin=46,bottomMargin=43,title='SAMBAD 360 - Step-by-Step Microsoft 365 Setup',author='SAMBAD 360 project').build(story,onFirstPage=page,onLaterPages=page)

bundle=R/'user-guides/SAMBAD-360-Setup-and-Copy-Pack.zip'
with zipfile.ZipFile(bundle,'w',zipfile.ZIP_DEFLATED) as z:
 for p in [source,docx_path,pdf_path,*sorted(pack.iterdir())]:z.write(p,p.relative_to(R/'user-guides'))
 for p in sorted((R/'power-bi/sample-data').iterdir()):z.write(p,Path('power-bi/sample-data')/p.name)
 z.write(R/'power-bi/theme.json','power-bi/theme.json')
for p in [docx_path,pdf_path,bundle]:print(p, p.stat().st_size)
print('Copy blocks:',len(manifest))

# Bible Reading Plan PDF Generator

import sys
import traceback

try:
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, PageBreak
    from reportlab.lib.pagesizes import LETTER, landscape
    from reportlab.lib import colors
except Exception:
    print("Missing dependency: reportlab is required. Install with `pip install reportlab`.")
    raise
from datetime import date, timedelta
import os
import math

books = [
    ("Gen",50),("Ex",40),("Lev",27),("Num",36),("Deu",34),
    ("Matt",28),
    ("Joshua",24),("Judges",21),("Ruth",4),("1 Sam",31),("2 Sam",24),
    ("1 Kings",22),("2 Kings",25),("1 Chron",29),("2 Chron",36),
    ("Ezra",10),("Nehemiah",13),("Esther",10),
    ("Mark",16),
    ("Job",42),("Psalms",150),("Prov",31),("Eccles.",12),("Song",8),
    ("Luke",24),
    ("Isaiah",66),("Jer",52),("Lam",5),("Ezekiel",48),("Daniel",12),
    ("Hosea",14),("Joel",3),("Amos",9),("Obd",1),("Jonah",4),("Micah",7),
    ("Nahum",3),("Hab",3),("Zeph",3),("Haggai",2),("Zech.",14),("Malachi",4),
    ("John",21),
    ("Acts",28),("Romans",16),("1 Cor",16),("2 Cor",13),("Gal",6),
    ("Eph",6),("Phil",4),("Col",4),("1 Thess",5),
    ("2 Thess",3),("1 Tim",6),("2 Tim",4),("Titus",3),("Philemon",1),
    ("Heb",13),("James",5),("1 Peter",5),("2 Peter",3),("1 Jn",5),
    ("2 Jn",1),("3 Jn",1),("Jude",1),("Rev",22)
]

chapters = []
for book, count in books:
    for c in range(1, count+1):
        chapters.append(f"{book} {c}")

def compress_chapters(chapter_list):
    """Compress consecutive chapters from same book into ranges."""
    if not chapter_list:
        return ""
    
    result = []
    i = 0
    while i < len(chapter_list):
        ch = chapter_list[i]
        # Parse "Book Chapter"
        parts = ch.rsplit(" ", 1)
        if len(parts) != 2:
            result.append(ch)
            i += 1
            continue
        
        book, ch_num = parts
        ch_num = int(ch_num)
        
        # Find consecutive chapters from same book
        j = i + 1
        while j < len(chapter_list):
            next_ch = chapter_list[j]
            next_parts = next_ch.rsplit(" ", 1)
            if len(next_parts) != 2:
                break
            next_book, next_ch_num = next_parts
            if next_book == book and int(next_ch_num) == ch_num + (j - i):
                j += 1
            else:
                break
        
        # Format as range or single chapter
        if j - i > 1:
            result.append(f"{book} {ch_num}-{int(chapter_list[j-1].rsplit(' ', 1)[1])}")
        else:
            result.append(ch)
        
        i = j
    
    return ", ".join(result)

def add_section_names(reading):
    if any(x in reading for x in ("Gen", "Ex", "Lev", "Num", "Deu")):
        return "LAW: " + reading
    elif "Matt" in reading:          
        return "LION: " + reading
    elif any(x in reading for x in ("Joshua", "Judges", "Ruth", "Sam", "Kings", "Chron", "Ezra", "Nehemiah", "Esther")):
        return "HISTORY: " + reading
    elif "Mark" in reading:          
        return "OX: " + reading
    elif any(x in reading for x in ("Psalms", "Prov", "Eccles.", "Song", "Job")):
        return "WISDOM: " + reading
    elif "Luke" in reading:          
        return "MAN: " + reading
    elif any(x in reading for x in ("Isaiah", "Jer", "Lam", "Ezekiel", "Daniel", "Hosea", "Joel", "Amos", "Obd", "Jonah", "Micah", "Nahum", "Hab", "Zeph", "Haggai", "Zech.", "Malachi")):
        return "PROPHETS: " + reading
    elif "John" in reading:          
        return "EAGLE: " + reading
    else:
        return "NEW COV: " + reading

days = 365
base = 3
extra = len(chapters) - base * days
margin = 24
margin_top_and_bottom = margin * 2 
page_height = 612
row_height = 12
available_height = page_height - margin_top_and_bottom
estimated_rows = int(available_height / row_height)
MAX_ROWS_PER_COLUMN = 39
rows_per_column = min(estimated_rows, MAX_ROWS_PER_COLUMN)

schedule = []
idx = 0
for i in range(days):
    n = base + (1 if i < extra else 0)
    schedule.append(compress_chapters(chapters[idx:idx+n]))
    idx += n
start = date(2026,1,1)
rows = [["Date","Reading"]]
for i, r in enumerate(schedule):
    d = start + timedelta(days=i)
    reading = add_section_names(r)
    rows.append([d.strftime("%b %d"), reading])

# Prepare for multi-column layout
columns_per_page = 5
body_rows = rows[1:]
totalRows = len(body_rows)


def generate_pdf(output_path=None):
    if output_path is None:
        here = os.path.dirname(os.path.abspath(__file__))
        output_path = os.path.join(here, "2026_Bible_Reading_Plan.pdf")

    doc = SimpleDocTemplate(output_path, pagesize=landscape(LETTER),
                            rightMargin=margin, leftMargin=margin, topMargin=margin, bottomMargin=margin)

    style = TableStyle([
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 5.5),
        ('GRID', (0,0), (-1,-1), 0.25, colors.grey),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 2),
        ('RIGHTPADDING', (0,0), (-1,-1), 2),
        ('TOPPADDING', (0,0), (-1,-1), 1),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1),
    ])

    story = []
    
    # Split body rows into pages, each page gets 4 columns of rows_per_column height
    rows_per_page = rows_per_column * columns_per_page
    num_pages = math.ceil(totalRows / rows_per_page)
    
    for page_num in range(num_pages):
        page_start = page_num * rows_per_page
        page_end = min(page_start + rows_per_page, totalRows)
        page_rows = body_rows[page_start:page_end]
        
        # Split this page's rows into 4 columns
        columns = [page_rows[i*rows_per_column:(i+1)*rows_per_column] for i in range(columns_per_page)]
        
        # Build a single table with 4 columns for this page
        combined_rows = []

        for i in range(rows_per_column):
            row = []
            for col in columns:
                if i < len(col):
                    row.extend(col[i])
                else:
                    row.extend(["", ""])
            combined_rows.append(row)

        colWidths = []
        for _ in range(columns_per_page):
            colWidths.extend([30, 100])

        combined = Table(combined_rows, colWidths=colWidths)
        combined.setStyle(TableStyle(list(style.getCommands())))
        story.append(combined)
        
        # Add page break between pages (but not after the last one)
        if page_num < num_pages - 1:
            story.append(PageBreak())

    # Debug: print summary info before building
    try:
        print(f"Building PDF with {len(rows)-1} days of readings; output: {output_path}")
    except Exception:
        pass

    try:
        doc.build(story)
    except Exception as e:
        print("Error while building PDF:")
        traceback.print_exc()
        raise
    return output_path


if __name__ == '__main__':
    try:
        out = generate_pdf()
        print(f"PDF created at: {out}")
    except Exception:
        print("Generation failed; see traceback above.")
        sys.exit(1)

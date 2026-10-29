import os
import sys
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, Preformatted
)
from reportlab.pdfgen import canvas
import fitz

PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN = 72.0  # 1 inch
USABLE_WIDTH = PAGE_WIDTH - 2 * MARGIN
USABLE_HEIGHT = PAGE_HEIGHT - 2 * MARGIN

NAVY_HEADING = colors.HexColor('#1F3864')
STEEL_SUB = colors.HexColor('#2F5496')
BODY_BLACK = colors.HexColor('#000000')
BORDER_GRAY = colors.HexColor('#A6A6A6')
LIGHT_ROW_BG = colors.HexColor('#F2F2F2')
CODE_BG = colors.HexColor('#F8FAFC')
CODE_BORDER = colors.HexColor('#CBD5E1')

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_page_decorations(self, total_pages):
        pno = self._pageNumber
        if pno == 1:
            return  # Title page: no headers or footers

        if 2 <= pno <= 10:
            roman_map = {2: "i", 3: "ii", 4: "iii", 5: "iv", 6: "v", 7: "vi", 8: "vii", 9: "viii", 10: "ix"}
            roman = roman_map.get(pno, "")
            self.setFont("Times-Roman", 12)
            self.setFillColor(BODY_BLACK)
            self.drawCentredString(PAGE_WIDTH / 2.0, 32, roman)
            return

        # Body pages
        body_page_num = pno - 10
        self.setFont("Times-Bold", 12)
        self.setFillColor(BODY_BLACK)
        header_text = "Central Park Housing Society Management System"
        self.drawCentredString(PAGE_WIDTH / 2.0, PAGE_HEIGHT - 35, header_text)

        self.setFont("Times-Roman", 12)
        self.drawString(MARGIN, 32, "T.Y.B.Sc.CS, SEM-V")
        self.drawRightString(PAGE_WIDTH - MARGIN, 32, f"Page {body_page_num}")

def get_styles():
    styles = getSampleStyleSheet()
    body = ParagraphStyle('CC_Body', parent=styles['Normal'], fontName='Times-Roman', fontSize=12, leading=16, textColor=BODY_BLACK, alignment=4, spaceBefore=0, spaceAfter=6)
    body_left = ParagraphStyle('CC_BodyLeft', parent=body, alignment=0)
    body_bold = ParagraphStyle('CC_BodyBold', parent=body, fontName='Times-Bold')
    ch_heading = ParagraphStyle('CC_ChapterHeading', parent=styles['Normal'], fontName='Times-Bold', fontSize=12, leading=16, textColor=NAVY_HEADING, spaceBefore=0, spaceAfter=8)
    sec_heading = ParagraphStyle('CC_SectionHeading', parent=styles['Normal'], fontName='Times-Bold', fontSize=12, leading=16, textColor=STEEL_SUB, spaceBefore=8, spaceAfter=4)
    cover_title = ParagraphStyle('CC_CoverTitle', parent=styles['Normal'], fontName='Times-Bold', fontSize=13, leading=18, textColor=BODY_BLACK, alignment=1, spaceAfter=4)
    cover_sub = ParagraphStyle('CC_CoverSubtitle', parent=styles['Normal'], fontName='Times-Roman', fontSize=12, leading=16, textColor=BODY_BLACK, alignment=1, spaceAfter=14)
    cover_center = ParagraphStyle('CC_CoverCenter', parent=styles['Normal'], fontName='Times-Roman', fontSize=12, leading=16, textColor=BODY_BLACK, alignment=1, spaceAfter=4)
    cover_bold = ParagraphStyle('CC_CoverBold', parent=styles['Normal'], fontName='Times-Bold', fontSize=12, leading=16, textColor=BODY_BLACK, alignment=1, spaceAfter=4)
    fig_caption = ParagraphStyle('CC_FigCaption', parent=styles['Normal'], fontName='Times-Bold', fontSize=12, leading=16, textColor=BODY_BLACK, alignment=0, spaceBefore=6, spaceAfter=0)
    code_font = ParagraphStyle('CC_Code', parent=styles['Normal'], fontName='Courier', fontSize=7.2, leading=9.2, textColor=BODY_BLACK)

    # Dedicated table typography styles to guarantee clean wrapping without clipping or overlaps
    th_style = ParagraphStyle('CC_TH', fontName='Times-Bold', fontSize=9.0, leading=11.5, textColor=colors.white, alignment=0)
    th_style_center = ParagraphStyle('CC_THCenter', fontName='Times-Bold', fontSize=9.0, leading=11.5, textColor=colors.white, alignment=1)
    tb_style = ParagraphStyle('CC_TB', fontName='Times-Roman', fontSize=8.5, leading=11.0, textColor=BODY_BLACK, alignment=0)
    tb_style_bold = ParagraphStyle('CC_TBBold', fontName='Times-Bold', fontSize=8.5, leading=11.0, textColor=BODY_BLACK, alignment=0)
    tb_style_center = ParagraphStyle('CC_TBCenter', fontName='Times-Roman', fontSize=8.5, leading=11.0, textColor=BODY_BLACK, alignment=1)
    tb_style_center_bold = ParagraphStyle('CC_TBCenterBold', fontName='Times-Bold', fontSize=8.5, leading=11.0, textColor=BODY_BLACK, alignment=1)

    return {
        'body': body, 'body_left': body_left, 'body_bold': body_bold,
        'ch_heading': ch_heading, 'sec_heading': sec_heading,
        'cover_title': cover_title, 'cover_sub': cover_sub,
        'cover_center': cover_center, 'cover_bold': cover_bold,
        'fig_caption': fig_caption, 'code_font': code_font,
        'th_style': th_style, 'th_style_center': th_style_center,
        'tb_style': tb_style, 'tb_style_bold': tb_style_bold,
        'tb_style_center': tb_style_center, 'tb_style_center_bold': tb_style_center_bold
    }

def make_styled_table(data, col_widths, is_header=True, styles=None, center_cols=None, bold_cols=(0,)):
    """
    Renders an impeccably formatted ReportLab Table.
    Every string or flowable cell is wrapped into an auto-wrapping Paragraph
    to eliminate text collisions, overlapping, and margin overflows.
    """
    if center_cols is None:
        center_cols = ()
    if bold_cols is None:
        bold_cols = ()
    if styles is None:
        s = get_styles()
    else:
        s = styles

    th_left = s['th_style']
    th_center = s['th_style_center']
    tb_left = s['tb_style']
    tb_bold = s['tb_style_bold']
    tb_center = s['tb_style_center']
    tb_center_bold = s['tb_style_center_bold']

    formatted_data = []
    for r_idx, row in enumerate(data):
        formatted_row = []
        is_h = (r_idx == 0 and is_header)
        for c_idx, cell in enumerate(row):
            if is_h:
                style = th_center if c_idx in center_cols else th_left
                if isinstance(cell, Paragraph):
                    formatted_row.append(Paragraph(cell.text, style))
                else:
                    t_str = str(cell).replace('\n', '<br/>')
                    if not t_str.startswith('<b>') and not t_str.startswith('<strong>'):
                        t_str = f"<b>{t_str}</b>"
                    formatted_row.append(Paragraph(t_str, style))
            else:
                is_b = c_idx in bold_cols
                is_c = c_idx in center_cols
                if is_b and is_c:
                    style = tb_center_bold
                elif is_b:
                    style = tb_bold
                elif is_c:
                    style = tb_center
                else:
                    style = tb_left

                if isinstance(cell, Paragraph):
                    formatted_row.append(Paragraph(cell.text, style))
                else:
                    t_str = str(cell).replace('\n', '<br/>')
                    formatted_row.append(Paragraph(t_str, style))
        formatted_data.append(formatted_row)

    t = Table(formatted_data, colWidths=col_widths)
    ts = [
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_GRAY),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_GRAY),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]
    if is_header:
        ts.append(('BACKGROUND', (0, 0), (-1, 0), NAVY_HEADING))
        for r in range(1, len(data)):
            bg = LIGHT_ROW_BG if (r % 2 == 0) else colors.white
            ts.append(('BACKGROUND', (0, r), (-1, r), bg))
    t.setStyle(TableStyle(ts))
    return t

def add_preliminary_pages(story, s):
    # PAGE 1: TITLE PAGE
    story.append(Spacer(1, 25))
    story.append(Paragraph("CENTRAL PARK HOUSING SOCIETY<br/>MANAGEMENT SYSTEM", s['cover_title']))
    story.append(Paragraph("A Comprehensive Web-Based Residential Administration, Maintenance &amp; Gate Security Portal", s['cover_sub']))
    story.append(Spacer(1, 15))
    story.append(Paragraph("A Project Report", s['cover_center']))
    story.append(Paragraph("Submitted in partial fulfillment of the requirements for the award of the Degree of", s['cover_center']))
    story.append(Paragraph("<b>BACHELOR OF SCIENCE (COMPUTER SCIENCE)</b>", s['cover_center']))
    story.append(Spacer(1, 12))
    story.append(Paragraph("By", s['cover_center']))
    story.append(Paragraph("<b>Neha Shridhar Kadam</b>", s['cover_center']))
    story.append(Paragraph("Seat No: ", s['cover_center']))
    story.append(Spacer(1, 14))
    story.append(Paragraph("Under the esteemed guidance of", s['cover_center']))
    story.append(Paragraph("<b>Mrs. Mona Khobare</b>", s['cover_center']))
    story.append(Paragraph("ASST. PROFESSOR", s['cover_center']))
    story.append(Spacer(1, 16))
    if os.path.exists("college_logo.jpeg"):
        story.append(Image("college_logo.jpeg", width=120, height=120))
    story.append(Spacer(1, 16))
    story.append(Paragraph("DEPARTMENT OF COMPUTER SCIENCE", s['cover_bold']))
    story.append(Paragraph("MODEL COLLEGE OF SCIENCE AND COMMERCE", s['cover_bold']))
    story.append(Paragraph("(Affiliated to University of Mumbai)", s['cover_center']))
    story.append(Paragraph("KALYAN, 421306", s['cover_center']))
    story.append(Paragraph("MAHARASHTRA", s['cover_center']))
    story.append(Paragraph("2026", s['cover_center']))
    story.append(PageBreak())

    # PAGE 2: PROFORMA FOR APPROVAL (Roman i)
    story.append(Paragraph("PROFORMA FOR THE APPROVAL OF PROJECT PROPOSAL", s['ch_heading']))
    story.append(Spacer(1, 10))
    story.append(Paragraph("PNR No.: ______________________&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Roll No.: ______________________", s['body_left']))
    story.append(Spacer(1, 8))
    story.append(Paragraph("1.&nbsp;&nbsp;Name of the Student: Neha Shridhar Kadam", s['body_left']))
    story.append(Spacer(1, 8))
    story.append(Paragraph("2.&nbsp;&nbsp;Title of the Project: Central Park Housing Society Management System", s['body_left']))
    story.append(Spacer(1, 8))
    story.append(Paragraph("3.&nbsp;&nbsp;Name of the Guide: Mrs. Mona Khobare", s['body_left']))
    story.append(Spacer(1, 8))
    story.append(Paragraph("4.&nbsp;&nbsp;Teaching experience of the Guide: ______________________", s['body_left']))
    story.append(Spacer(1, 8))
    story.append(Paragraph("5.&nbsp;&nbsp;Is this your first submission?&nbsp;&nbsp;&nbsp;Yes / No", s['body_left']))
    story.append(Spacer(1, 40))

    sig_data = [
        [Paragraph("Signature of the Student:<br/>____________________<br/><br/>Date: ______________", s['body_left']),
         Paragraph("Signature of the Guide:<br/>____________________<br/><br/>Date: ______________", s['body_left'])],
        [Paragraph("<br/>Signature of the Coordinator: ____________________<br/>Date: ______________", s['body_left']), ""]
    ]
    t_sig = Table(sig_data, colWidths=[225, 225])
    t_sig.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
    story.append(t_sig)
    story.append(PageBreak())

    # PAGE 3: CERTIFICATE (Roman ii)
    if os.path.exists("college_logo.jpeg"):
        story.append(Image("college_logo.jpeg", width=80, height=80))
    story.append(Spacer(1, 8))
    story.append(Paragraph("The East Kalyan Welfare Society's", s['cover_center']))
    story.append(Paragraph("<b>MODEL COLLEGE OF SCIENCE &amp; COMMERCE, KALYAN(E)</b>", s['cover_center']))
    story.append(Paragraph("Accredited 'B' Grade by NAAC<br/>(Affiliated to University of Mumbai)", s['cover_center']))
    story.append(Spacer(1, 16))
    cert_text = """This is to certify that Mr./Miss. <u>Neha Shridhar Kadam</u> Seat No. ______________ PRN No. ______________________ of T.Y.B.Sc (Computer Science) during Semester – V has completed the prescribed practical's of the course <u>Central Park Housing Society Management System</u> under our supervision in Model College of Science &amp; Commerce, Kalyan(E), affiliated to Mumbai University during the Academic Year 2025–2026."""
    story.append(Paragraph(cert_text, s['body']))
    story.append(Spacer(1, 45))

    c_sig = [
        [Paragraph("____________________<br/>TEACHER IN-CHARGE", s['body_left']),
         Paragraph("____________________<br/>EXTERNAL EXAMINER", s['body_left'])],
        [Paragraph("<br/><br/>____________________<br/>HEAD,<br/>DEPARTMENT OF COMPUTER SCIENCE", s['body_left']),
         Paragraph("<br/><br/>____________________<br/>PRINCIPAL<br/>&nbsp;", s['body_left'])]
    ]
    t_c = Table(c_sig, colWidths=[225, 225])
    t_c.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
    story.append(t_c)
    story.append(Spacer(1, 20))
    story.append(Paragraph("T.Y.B.Sc.CS, SEM-V", s['body_left']))
    story.append(PageBreak())

    # PAGE 4: DECLARATION (Roman iii)
    story.append(Paragraph("DECLARATION", s['ch_heading']))
    story.append(Spacer(1, 14))
    dec_text1 = """I hereby declare that the project “Central Park Housing Society Management System” carried out at The East Kalyan Welfare Society’s Model College of Science &amp; Commerce, Kalyan(E), has not been duplicated or submitted to any other university for the award of any degree. This project is submitted in partial fulfilment of the requirements for the award of the degree of BACHELOR OF SCIENCE (COMPUTER SCIENCE) as the Semester V project."""
    story.append(Paragraph(dec_text1, s['body']))
    story.append(Spacer(1, 12))
    dec_text2 = """I further declare that the work presented in this report is my own work carried out under the guidance of the project guide."""
    story.append(Paragraph(dec_text2, s['body']))
    story.append(Spacer(1, 45))
    story.append(Paragraph("Date: ____________________", s['body_left']))
    story.append(Spacer(1, 6))
    story.append(Paragraph("Place: ___________________", s['body_left']))
    story.append(Spacer(1, 20))
    story.append(Paragraph("Signature of Student: ______________________________", s['body_left']))
    story.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;(Neha Shridhar Kadam)", s['body_left']))
    story.append(PageBreak())

    # PAGE 5: ROLE AND RESPONSIBILITY FORM (Roman iv)
    story.append(Paragraph("Role and Responsibility Form", s['ch_heading']))
    story.append(Spacer(1, 10))
    story.append(Paragraph("This project was undertaken individually. The role and responsibility of the student is summarised below.", s['body']))
    story.append(Spacer(1, 14))
    role_data = [
        [Paragraph("<b>Name</b>", s['body_bold']), Paragraph("<b>Role</b>", s['body_bold']), Paragraph("<b>Responsibility</b>", s['body_bold'])],
        [Paragraph("Neha Shridhar Kadam", s['body_left']),
         Paragraph("Sole Developer", s['body_left']),
         Paragraph("Requirement analysis, relational database design, front-end and backend development, testing, and documentation of all modules of the Central Park Housing Society Management System.", s['body_left'])]
    ]
    t_role = make_styled_table(role_data, [95, 95, 260], styles=s, bold_cols=(0,))
    story.append(t_role)
    story.append(PageBreak())

    # PAGE 6: ABSTRACT (Roman v)
    story.append(Paragraph("Abstract", s['ch_heading']))
    story.append(Spacer(1, 10))
    abs_text = """Central Park Housing Society Management System is a comprehensive web-based platform engineered to modernise, automate, and centralise residential housing society administration, resident member services, maintenance accounting, and checkpoint gate security operations. Developed using Python Flask, SQLite/MySQL relational database architecture, and a responsive Bootstrap 5 interface, the system implements a strict role-based access control paradigm supporting three discrete operational roles: Administrators, Residents, and Security Personnel. The Administrator manages apartment flats, residents, vehicle parking slots, generates periodic maintenance bills, reviews service complaints, broadcasts digital notices, and exports operational CSV reports. Resident members can securely view apartment occupancy details, check pending maintenance dues, make instant payments with automated receipt generation, lodge maintenance grievances, and inspect society circulars. Security guards operate an expedited gate console for logging visitor entry and executing one-click visitor checkout. The entire platform enforces secure password hashing, prepared SQL statements, session verification middleware, and CSRF protection. This blackbook report details the complete engineering lifecycle from requirements analysis and architectural modeling to empirical test verification and deployment."""
    story.append(Paragraph(abs_text, s['body']))
    story.append(PageBreak())

    # PAGE 7: ACKNOWLEDGEMENT (Roman vi)
    story.append(Paragraph("Acknowledgement", s['ch_heading']))
    story.append(Spacer(1, 10))
    ack1 = """I would like to express my sincere gratitude to my project guide, <b>Mrs. Mona Khobare</b>, for her constant guidance, valuable suggestions and encouragement throughout the development of this project. Her feedback was instrumental in shaping both the technical implementation and the presentation of this report."""
    story.append(Paragraph(ack1, s['body']))
    story.append(Spacer(1, 10))
    ack2 = """I am also thankful to the Department of Computer Science and the faculty of Model College of Science and Commerce for providing the resources and environment necessary to complete this project."""
    story.append(Paragraph(ack2, s['body']))
    story.append(Spacer(1, 10))
    ack3 = """Finally, I would like to thank my family and friends for their continuous support and encouragement throughout my academic journey."""
    story.append(Paragraph(ack3, s['body']))
    story.append(Spacer(1, 40))
    story.append(Paragraph("<b>Neha Shridhar Kadam</b>", s['body_left']))
    story.append(PageBreak())

    # PAGE 8: TABLE OF CONTENTS (Part 1, Roman vii)
    story.append(Paragraph("Table of Contents", s['ch_heading']))
    s_toc = ParagraphStyle('TOC_F', fontName='Times-Roman', fontSize=8.5, leading=10.5, textColor=BODY_BLACK, alignment=0, spaceBefore=0, spaceAfter=0)
    s_toc_center = ParagraphStyle('TOC_FC', parent=s_toc, alignment=1)
    s_toc_b = ParagraphStyle('TOC_B', fontName='Times-Bold', fontSize=8.5, leading=10.5, textColor=BODY_BLACK, alignment=0, spaceBefore=0, spaceAfter=0)
    s_toc_h = ParagraphStyle('TOC_H', fontName='Times-Bold', fontSize=8.5, leading=10.5, textColor=colors.white, alignment=0, spaceBefore=0, spaceAfter=0)
    s_toc_h_center = ParagraphStyle('TOC_HC', parent=s_toc_h, alignment=1)
    
    def make_toc_table(data, widths):
        formatted_data = []
        for r_idx, row in enumerate(data):
            if r_idx == 0:
                formatted_data.append([
                    Paragraph("<b>Sr. No.</b>", s_toc_h_center),
                    Paragraph("<b>Index</b>", s_toc_h),
                    Paragraph("<b>Pg. No.</b>", s_toc_h_center),
                    Paragraph("<b>Sign</b>", s_toc_h_center)
                ])
            else:
                idx_text = str(row[1])
                is_major = (
                    idx_text.startswith("Chapter ") or
                    idx_text.startswith("Appendix ") or
                    idx_text in ["Abstract", "Acknowledgement", "List of Figures", "References", "Glossary"]
                )
                style_idx = s_toc_b if is_major else s_toc
                formatted_row = [
                    Paragraph(str(row[0]), s_toc_center),
                    Paragraph(idx_text, style_idx),
                    Paragraph(str(row[2]), s_toc_center),
                    Paragraph(str(row[3]), s_toc_center)
                ]
                formatted_data.append(formatted_row)
        t = Table(formatted_data, colWidths=widths)
        t.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 0.5, BORDER_GRAY),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_GRAY),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 1),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            ('BACKGROUND', (0, 0), (-1, 0), NAVY_HEADING),
        ]))
        return t

    toc_p1 = [
        [Paragraph("<b>Sr. No.</b>", s_toc_h), Paragraph("<b>Index</b>", s_toc_h), Paragraph("<b>Pg. No.</b>", s_toc_h), Paragraph("<b>Sign</b>", s_toc_h)],
        ["1", "Original Copy of the Approved Proforma of the Project Proposal", "i", ""],
        ["2", "Certificate of Authenticated Work / Signature Page", "ii", ""],
        ["3", "Declaration", "iii", ""],
        ["4", "Role and Responsibility Form", "iv", ""],
        ["5", "Abstract", "v", ""],
        ["6", "Acknowledgement", "vi", ""],
        ["7", "List of Figures", "ix", ""],
        ["8", "Chapter 1: Introduction", "1", ""],
        ["9", "1.1 Background", "1", ""],
        ["10", "1.2 Objectives", "1", ""],
        ["11", "1.3 Purpose, Scope and Applicability", "1", ""],
        ["12", "1.3.1 Purpose", "1", ""],
        ["13", "1.3.2 Scope", "1", ""],
        ["14", "1.3.3 Applicability", "1", ""],
        ["15", "1.4 Achievements", "2", ""],
        ["16", "1.5 Organisation of Report", "2", ""],
        ["17", "Chapter 2: Survey of Technologies", "3", ""],
        ["18", "Front End", "3", ""],
        ["19", "Back End", "3", ""],
        ["20", "Database", "3", ""],
        ["21", "Development Environment", "3", ""],
        ["22", "Chapter 3: Requirements and Analysis", "4", ""],
        ["23", "3.1 Problem Definition", "4", ""],
        ["24", "3.2 Requirements Specification", "4", ""],
        ["25", "3.3 Planning and Scheduling", "5", ""],
        ["26", "3.4 Software and Hardware Requirements", "8", ""],
        ["27", "3.5 Preliminary Product Description", "8", ""],
        ["28", "3.6 Conceptual Models", "9", ""],
        ["29", "Chapter 4: System Design", "13", ""],
        ["30", "4.1 Basic Modules", "13", ""],
        ["31", "4.2 Data Design", "15", ""],
        ["32", "4.2.1 Schema Design", "15", ""],
        ["33", "4.2.2 Data Integrity and Constraints", "17", ""],
        ["34", "4.3 Procedural Design", "17", ""],
        ["35", "4.3.1 Logic Diagrams", "17", ""],
        ["36", "4.3.2 Data Structures", "19", ""],
        ["37", "4.3.3 Algorithms Design", "19", ""]
    ]
    t_toc1 = make_toc_table(toc_p1, [38, 305, 54, 54])
    story.append(t_toc1)
    story.append(PageBreak())

    # PAGE 9: TABLE OF CONTENTS (Part 2, Roman viii)
    story.append(Paragraph("Table of Contents (Continued)", s['ch_heading']))
    toc_p2 = [
        [Paragraph("<b>Sr. No.</b>", s_toc_h), Paragraph("<b>Index</b>", s_toc_h), Paragraph("<b>Pg. No.</b>", s_toc_h), Paragraph("<b>Sign</b>", s_toc_h)],
        ["38", "4.4 User Interface Design", "20", ""],
        ["39", "4.5 Security Issues", "20", ""],
        ["40", "4.6 Test Cases Design", "20", ""],
        ["41", "Chapter 5: Implementation and Testing", "21", ""],
        ["42", "5.1 Implementation Approaches", "21", ""],
        ["43", "5.2 Coding Details and Code Efficiency", "21", ""],
        ["44", "5.2.1 Code Efficiency", "22", ""],
        ["45", "5.3 Testing Approach", "22", ""],
        ["46", "5.3.1 Unit Testing", "22", ""],
        ["47", "5.3.2 Integrated Testing", "22", ""],
        ["48", "5.3.3 Beta Testing", "22", ""],
        ["49", "5.4 Modifications and Improvements", "23", ""],
        ["50", "5.5 Test Cases", "24", ""],
        ["51", "Chapter 6: Results and Discussion", "25", ""],
        ["52", "6.1 Test Reports", "25", ""],
        ["53", "6.2 User Documentation", "25", ""],
        ["54", "Administrator & Resident Workflows", "26", ""],
        ["55", "Security Guard Workflow", "48", ""],
        ["56", "Chapter 7: Conclusions", "49", ""],
        ["57", "7.1 Conclusion", "49", ""],
        ["58", "7.1.1 Significance of the System", "49", ""],
        ["59", "7.2 Limitations of the System", "49", ""],
        ["60", "7.3 Future Scope of the Project", "50", ""],
        ["61", "References", "51", ""],
        ["62", "Glossary", "52", ""],
        ["63", "Appendix A: Source Code Listings", "53", ""],
        ["64", "Appendix B: Installation and Setup Guide", "67", ""]
    ]
    t_toc2 = make_toc_table(toc_p2, [38, 305, 54, 54])
    story.append(t_toc2)
    story.append(PageBreak())

    # PAGE 10: LIST OF FIGURES (Roman ix)
    story.append(Paragraph("List of Figures", s['ch_heading']))
    lof_data = [
        [Paragraph("<b>Fig. No.</b>", s['body_bold']), Paragraph("<b>Caption</b>", s['body_bold']), Paragraph("<b>Pg. No.</b>", s['body_bold'])],
        ["1", "Gantt Chart – Project Schedule", "6"],
        ["2", "PERT Chart – Activity Network", "7"],
        ["3", "Entity-Relationship Diagram", "9"],
        ["4", "DFD Level 0 (Context Diagram)", "10"],
        ["5", "DFD Level 1 – Functional Process Decomposition", "11"],
        ["6", "Use Case Diagram", "12"],
        ["7", "System Architecture (Three-Tier)", "14"],
        ["8", "Flowchart – Resident Maintenance & Gate Pass Workflow", "18"],
        ["9", "Portal Login & Quick-Login Role Switcher Interface", "26"],
        ["10", "Administrator Central Control Dashboard – Overview & KPIs", "27"],
        ["11", "Flats Management – Residential Apartment Directory & Status", "28"],
        ["12", "Flats Management – Apartment Details & Allocation Roster", "29"],
        ["13", "Resident Member Directory – Resident Contact Information", "30"],
        ["14", "Resident Directory – Flat Ownership & Family Records", "31"],
        ["15", "Maintenance Billing – Assessment Generation & Bill Schedule", "32"],
        ["16", "Maintenance Billing – Dues Ledger & Payment Tracking", "33"],
        ["17", "Official Society Maintenance Payment Receipt (Print View)", "34"],
        ["18", "Complaints & Grievances Management – Admin Review Table", "35"],
        ["19", "Complaints Management – Ticket Details & Resolution Actions", "36"],
        ["20", "Security Visitor Gate Log – Real-Time Premises Tracking", "37"],
        ["21", "Security Visitor Gate Log – Check-In Registration Form", "38"],
        ["22", "Society Notice Board – Digital Announcements & Circulars", "39"],
        ["23", "Society Notice Board – Broadcast New Announcement Console", "40"],
        ["24", "Vehicle Directory – Authorized Resident Parking Roster", "41"],
        ["25", "Vehicle Directory – Register New Vehicle & Slot Allocation", "42"],
        ["26", "Financial Analytics & Operations Audit Center", "43"],
        ["27", "Reports Center – Exportable CSV Financial Summaries", "44"],
        ["28", "Resident Personal Portal Dashboard – Flat Summary & Activity", "45"],
        ["29", "Resident Maintenance Bills – Breakdown & Instant Settlement", "46"],
        ["30", "Resident Service Complaint Lodging Form & Resolution History", "47"],
        ["31", "Security Guard Console – Fast Visitor Pass Issuance & 1-Click Exit", "48"]
    ]
    t_lof = make_styled_table(lof_data, [45, 355, 50], styles=s, center_cols=(0, 2), bold_cols=(0,))
    story.append(t_lof)
    story.append(PageBreak())

def add_chapters1_2_3(story, s):
    # PAGE 11: CHAPTER 1: INTRODUCTION (Body p. 1)
    story.append(Paragraph("Chapter 1: Introduction", s['ch_heading']))
    story.append(Paragraph("1.1 Background", s['sec_heading']))
    p_bg = """Housing society administration in modern urban residential complexes involves multifaceted coordination among committee administrators, residents, auditors, and security personnel. Traditionally, residential societies depend upon physical ledgers, manual paper receipts, paper notice boards, and handwritten visitor registers at gate checkpoints. Such conventional manual mechanisms suffer from acute operational handicaps: physical registers are vulnerable to damage and tampering, payment tracking lacks automated verification, visitor logs cannot be audited in real time, and residents face communication delays regarding maintenance assessments and circular announcements. Central Park Housing Society Management System was engineered as a centralized, self-contained web portal to eliminate these operational bottlenecks through modern relational database automation and role-based access control."""
    story.append(Paragraph(p_bg, s['body']))

    story.append(Paragraph("1.2 Objectives", s['sec_heading']))
    p_obj = """The objective of this project is to architect, develop, and deploy a secure multi-role web application that automates residential apartment management, member directories, periodic maintenance billing with automated receipt printing, grievance resolution tracking, gate security logging with real-time visitor monitoring, vehicle parking allocation, digital circular broadcasting, and operational CSV auditing."""
    story.append(Paragraph(p_obj, s['body']))

    story.append(Paragraph("1.3 Purpose, Scope and Applicability", s['sec_heading']))
    story.append(Paragraph("1.3.1 Purpose", s['sec_heading']))
    p_purp = """The purpose of Central Park Housing Society Management System is to establish a unified, transparent digital environment that seamlessly connects administrators, residents, and gate security staff into one synchronized workflow, replacing fragmented manual records with reliable computerized transactions."""
    story.append(Paragraph(p_purp, s['body']))

    story.append(Paragraph("1.3.2 Scope", s['sec_heading']))
    p_scope = """The system scope encompasses multi-tier authentication, dynamic flat management, resident contact directories, automated maintenance assessment generation, online/offline payment logging with tamper-evident receipt generation, grievance lodging and ticket progression, security gate visitor check-in and checkout, authorized vehicle parking tracking, and administrative CSV export. External online payment gateways and IoT-based hardware boom barriers are excluded from this phase and earmarked for future enhancements."""
    story.append(Paragraph(p_scope, s['body']))

    story.append(Paragraph("1.3.3 Applicability", s['sec_heading']))
    p_app = """The system is directly applicable to residential housing societies, gated condominium complexes, apartment towers, and cooperative housing societies seeking a lightweight, self-hosted management portal without recurring proprietary subscription fees."""
    story.append(Paragraph(p_app, s['body']))
    story.append(PageBreak())

    # PAGE 12: ACHIEVEMENTS & ORGANISATION (Body p. 2)
    story.append(Paragraph("1.4 Achievements", s['sec_heading']))
    p_ach = """A complete, production-ready three-role web portal was engineered, thoroughly tested, and deployed locally. Key technical achievements include: (1) Robust role-based access control (RBAC) supporting Administrator, Resident, and Security Guard roles with session isolation; (2) An automated maintenance assessment calculation and tracking engine; (3) A tamper-evident payment receipt generator with formatted print stylesheets; (4) A real-time gate security visitor console with instant duration tracking and one-click exit passes; (5) A normalized SQLite/MySQL database schema with strict foreign key constraints; and (6) A clean, modern Bootstrap 5 user interface providing intuitive responsiveness across desktop and tablet viewports."""
    story.append(Paragraph(p_ach, s['body']))

    story.append(Paragraph("1.5 Organisation of Report", s['sec_heading']))
    p_org = """This Blackbook project report is structured into seven formal chapters following University of Mumbai guidelines:<br/><br/>
• <b>Chapter 2: Survey of Technologies</b> examines the architectural merits and rationale for selecting Python, Flask, SQLite/MySQL, and Bootstrap 5 over competing technology stacks.<br/>
• <b>Chapter 3: Requirements and Analysis</b> outlines the functional specifications, non-functional security constraints, development scheduling (Gantt and PERT charts), and conceptual models (ERD, DFD Levels 0 & 1, Use Case diagram).<br/>
• <b>Chapter 4: System Design</b> presents the modular three-tier client-server architecture, comprehensive relational database schemas, procedural flowcharts, and algorithm designs.<br/>
• <b>Chapter 5: Implementation and Testing</b> explains key controller implementations, code efficiency practices, unit and integration test strategies, and formal test cases.<br/>
• <b>Chapter 6: Results and Discussion</b> provides a detailed visual system walkthrough featuring 23 dedicated full-page screenshots demonstrating complete administrator, resident, and security workflows.<br/>
• <b>Chapter 7: Conclusions</b> summarizes project milestones, operational significance, recognized limitations, and roadmap for future expansions.<br/>
• <b>References, Glossary &amp; Appendices</b> provide formal literature citations, technical terminology definitions, complete backend source code listings, and a step-by-step local deployment guide."""
    story.append(Paragraph(p_org, s['body']))
    story.append(PageBreak())

    # PAGE 13: CHAPTER 2: SURVEY OF TECHNOLOGIES (Body p. 3)
    story.append(Paragraph("Chapter 2: Survey of Technologies", s['ch_heading']))
    p_tech_intro = """Selecting an appropriate technology stack is vital to ensure maintainability, rapid development, security, and low operational overhead. Several architectural options were evaluated across each layer of the Central Park Housing Society Management System before arriving at the final production stack."""
    story.append(Paragraph(p_tech_intro, s['body']))

    story.append(Paragraph("Front End", s['sec_heading']))
    p_fe = """The presentation tier utilizes semantic HTML5, modern CSS3 styling, and the Bootstrap 5.3 UI framework paired with vanilla JavaScript. Heavy client-side frameworks such as React or Angular were evaluated but discarded because they introduce extensive build-tooling pipelines, Node package overhead, and complex state synchronization unsuited for a server-rendered administrative portal. Bootstrap 5 provides accessible, mobile-first responsive grid layouts, professional card components, and modal dialogues directly interpretable by any browser without transpilation."""
    story.append(Paragraph(p_fe, s['body']))

    story.append(Paragraph("Back End", s['sec_heading']))
    p_be = """Python 3 with the lightweight Flask web framework was chosen for the application controller tier. Alternatives including PHP, Node.js/Express, and Java Spring Boot were considered. Python provides clean syntax, exceptional standard libraries, and high maintainability. Flask offers an unopinionated, WSGI-compliant micro-framework structure that allows fine-grained control over routing, session cookies, and authentication middleware without the unnecessary database migration bloat of full-stack monolithic frameworks like Django."""
    story.append(Paragraph(p_be, s['body']))

    story.append(Paragraph("Database", s['sec_heading']))
    p_db = """The data tier leverages relational database technology with full support for both SQLite and MySQL/MariaDB. SQLite was configured as the default zero-configuration, serverless engine stored directly in the filesystem (`database/society.db`), guaranteeing effortless academic portability and evaluation without requiring external database server daemons. The schema is fully ANSI-SQL compliant and includes foreign keys, cascade rules, and automated timestamp triggers that easily scale to multi-user MySQL instances."""
    story.append(Paragraph(p_db, s['body']))

    story.append(Paragraph("Development Environment", s['sec_heading']))
    p_env = """Development was executed using Visual Studio Code with Python language server extensions, virtualenv environment isolation, and Git version control on macOS. Headless Google Chrome automation was leveraged for capturing system screen states and layout auditing."""
    story.append(Paragraph(p_env, s['body']))
    story.append(PageBreak())

    # PAGE 14: CHAPTER 3: REQUIREMENTS AND ANALYSIS (Body p. 4)
    story.append(Paragraph("Chapter 3: Requirements and Analysis", s['ch_heading']))
    story.append(Paragraph("3.1 Problem Definition", s['sec_heading']))
    p_prob = """Residential housing societies face chronic administrative hurdles when relying on manual paperwork: (a) Maintenance collection tracking is fragmented, leading to billing disputes and lost revenues; (b) Paper visitor logs at entrance gates are easily manipulated and cannot alert managers to overstaying visitors; (c) Resident grievances submitted verbally or on paper slips frequently go unaddressed; and (d) Physical notice boards fail to reach off-premise flat owners."""
    story.append(Paragraph(p_prob, s['body']))

    story.append(Paragraph("3.2 Requirements Specification", s['sec_heading']))
    story.append(Paragraph("The functional requirements mapped to distinct user roles are summarized below:", s['body']))

    req_data = [
        [Paragraph("<b>Role</b>", s['body_bold']), Paragraph("<b>Functional Requirements</b>", s['body_bold'])],
        ["Administrator", "Authenticate securely; manage apartment flats and occupancy status; maintain resident directories; generate monthly maintenance assessments; record payments and generate official printable receipts; review and update resident grievance tickets; inspect real-time visitor gate logs; broadcast digital announcements; register resident vehicles; export analytical CSV summaries."],
        ["Resident", "Log in to personalized portal; inspect flat details; view outstanding maintenance bills; submit instant online settlement records; view and download verified payment receipts; lodge service complaints and track resolution progress; view society circulars."],
        ["Security Guard", "Access dedicated security console; log incoming visitors with photo/ID, mobile, visiting flat, and purpose; view real-time list of visitors currently on campus; execute 1-click visitor departure checkout; verify resident parking authorization."]
    ]
    t_req = make_styled_table(req_data, [110, 340], styles=s, bold_cols=(0,))
    story.append(t_req)
    story.append(Spacer(1, 6))

    p_nfr = """<b>Non-Functional Requirements:</b> Passwords must be hashed using cryptographic algorithms (Werkzeug pbkdf2:sha256). All database queries containing user input must use parameterized SQL to prevent injection. Role middleware must block unauthorized URL traversal. Web pages must load under 1.5 seconds on local networks and render cleanly across diverse screen viewports."""
    story.append(Paragraph(p_nfr, s['body']))
    story.append(PageBreak())

    # PAGE 15: 3.3 PLANNING AND SCHEDULING (Body p. 5)
    story.append(Paragraph("3.3 Planning and Scheduling", s['sec_heading']))
    p_plan = """The project followed an iterative, module-driven engineering lifecycle spanning from early August to mid-September 2026. The structured milestone phases are summarized in the table below:"""
    story.append(Paragraph(p_plan, s['body']))

    sched_data = [
        [Paragraph("<b>Phase</b>", s['body_bold']), Paragraph("<b>Engineering Activity</b>", s['body_bold']), Paragraph("<b>Approximate Period</b>", s['body_bold'])],
        ["1", "Requirements analysis, stakeholder interviews, and relational schema normalization", "Early August 2026"],
        ["2", "Authentication subsystem, multi-role session middleware, and base dashboard layout", "Mid August 2026"],
        ["3", "Core society management: flats, residents, maintenance billing, and payment receipts", "Late August 2026"],
        ["4", "Security gatekeeper module: visitor tracking, vehicle roster, and grievance ticketing", "Early September 2026"],
        ["5", "Bootstrap 5 UI/UX refinement, print stylesheets, and analytical CSV export engine", "Early–mid September 2026"],
        ["6", "Unit and integrated system testing, vulnerability auditing, and blackbook documentation", "Mid September 2026"]
    ]
    t_sched = make_styled_table(sched_data, [45, 275, 130], styles=s, center_cols=(0,), bold_cols=(0,))
    story.append(t_sched)
    story.append(Spacer(1, 10))

    p_sched_desc = """Project planning specifies the complete sequence of discrete tasks necessary for project delivery, whereas scheduling establishes timeline dependencies and resource allocations. The visual execution schedule of Central Park Housing Society Management System is illustrated on the following pages through a comprehensive Gantt chart (Figure 1) and a formal PERT activity network (Figure 2)."""
    story.append(Paragraph(p_sched_desc, s['body']))
    story.append(PageBreak())

    # PAGE 16: FIGURE 1: GANTT CHART (Body p. 6)
    p_gantt = """The Gantt chart illustrates the chronological progression of the six project development phases against a structured timeline spanning from early August to mid-September 2026. Each month is partitioned into Early, Mid, and Late stages. Phases 1, 2, and 3 executed sequentially throughout August to establish the foundational data models and core billing mechanisms. Phases 4 and 5 progressed concurrently during early September to synchronize gate security features with reporting enhancements, culminating in Phase 6 for comprehensive verification and documentation."""
    story.append(Paragraph(p_gantt, s['body']))
    story.append(Spacer(1, 8))
    if os.path.exists("report_assets/diagrams/fig_gantt_chart.png"):
        story.append(Image("report_assets/diagrams/fig_gantt_chart.png", width=440, height=240))
    story.append(Paragraph("Figure 1: Gantt Chart – Project Schedule", s['fig_caption']))
    story.append(PageBreak())

    # PAGE 17: FIGURE 2: PERT CHART (Body p. 7)
    p_pert = """The Program Evaluation and Review Technique (PERT) chart models the project as an activity network comprising milestone events (numbered circular nodes 1 through 6) interconnected by activity vectors (labelled A through F). Activities A, B, and C progress linearly. Upon completion of milestone 3, the gate security implementation (Activity D) and UI/UX refinement (Activity E) proceed in parallel. Activity F executes final testing and documentation. Earliest Times (TE) and Latest Times (TL) are identical across all milestones, denoting a critical path duration of five developmental periods."""
    story.append(Paragraph(p_pert, s['body']))
    story.append(Spacer(1, 8))
    if os.path.exists("report_assets/diagrams/fig_pert_chart.png"):
        story.append(Image("report_assets/diagrams/fig_pert_chart.png", width=440, height=240))
    story.append(Paragraph("Figure 2: PERT Chart – Activity Network", s['fig_caption']))
    story.append(PageBreak())

    # PAGE 18: 3.4 & 3.5 REQUIREMENTS & PRODUCT DESCRIPTION (Body p. 8)
    story.append(Paragraph("3.4 Software and Hardware Requirements", s['sec_heading']))
    story.append(Paragraph("The minimum and recommended deployment specifications are detailed below:", s['body']))

    hw_sw_data = [
        [Paragraph("<b>Component</b>", s['body_bold']), Paragraph("<b>Hardware Specification</b>", s['body_bold']), Paragraph("<b>Software Specification</b>", s['body_bold'])],
        ["Processor", "Dual Core 2.0 GHz or higher (Intel/Apple/AMD)", "Python 3.10+ Runtime Environment"],
        ["Memory (RAM)", "4 GB minimum (8 GB recommended)", "Flask 3.0+ Web Framework"],
        ["Storage", "500 MB free hard drive space", "SQLite 3 / MySQL 8.0 Relational DB"],
        ["Display / Network", "1024x768 display resolution, TCP/IP LAN", "Modern Web Browser (Chrome, Firefox, Safari)"],
        ["Operating System", "Cross-platform (macOS 12+, Windows 10+, Linux)", "Werkzeug, Jinja2, Bootstrap 5.3 CDN"]
    ]
    t_hw_sw = make_styled_table(hw_sw_data, [100, 175, 175], styles=s, bold_cols=(0,))
    story.append(t_hw_sw)
    story.append(Spacer(1, 8))

    story.append(Paragraph("3.5 Preliminary Product Description", s['sec_heading']))
    p_prod = """Central Park Housing Society Management System operates as an integrated web application accessible via any modern browser across local networks or intranet hosts. The software enforces strict session-based authentication with role discrimination. Upon logging in, administrators access comprehensive management dashboards with live metrics; residents access self-service payment histories and ticketing consoles; and security personnel utilize an optimized gate checkpoint register. All state changes are stored persistently in normalized relational tables, guaranteeing full auditability and eliminating manual register maintenance."""
    story.append(Paragraph(p_prod, s['body']))
    story.append(PageBreak())

    # PAGE 19: 3.6 CONCEPTUAL MODELS - ER DIAGRAM (Body p. 9)
    story.append(Paragraph("3.6 Conceptual Models", s['sec_heading']))
    p_cm_intro = """Conceptual modeling defines the structural entities, data flows, and behavioral interactions underpinning the application. The system architecture is formalized across four conceptual models: the Entity-Relationship Diagram, Data Flow Diagrams (Level 0 and Level 1), and the Use Case Diagram.<br/><br/>
The Entity-Relationship Diagram (Figure 3) illustrates the normalized relational database schema comprising nine core entities: USERS, FLATS, RESIDENTS, VEHICLES, MAINTENANCE, PAYMENTS, COMPLAINTS, VISITORS, and NOTICES. Primary keys and foreign key constraints enforce referential integrity across the entire residential domain."""
    story.append(Paragraph(p_cm_intro, s['body']))
    story.append(Spacer(1, 6))
    if os.path.exists("report_assets/diagrams/fig01_er_diagram.png"):
        story.append(Image("report_assets/diagrams/fig01_er_diagram.png", width=440, height=270))
    story.append(Paragraph("Figure 3: Entity-Relationship Diagram", s['fig_caption']))
    story.append(PageBreak())

    # PAGE 20: DFD LEVEL 0 (Body p. 10)
    p_dfd0 = """The Level 0 Data Flow Diagram (Context Diagram) establishes the overarching boundary of the Central Park Housing Society Management System. It portrays how the three primary external entities—Administrator, Resident Member, and Security Guard—interact with the centralized software system through inbound request payloads (credentials, payments, complaints, visitor details) and outbound response data (dashboards, receipts, alerts, and operational reports)."""
    story.append(Paragraph(p_dfd0, s['body']))
    story.append(Spacer(1, 8))
    if os.path.exists("report_assets/diagrams/fig02_dfd_level0.png"):
        story.append(Image("report_assets/diagrams/fig02_dfd_level0.png", width=440, height=270))
    story.append(Paragraph("Figure 4: DFD Level 0 (Context Diagram)", s['fig_caption']))
    story.append(PageBreak())

    # PAGE 21: DFD LEVEL 1 (Body p. 11)
    p_dfd1 = """The Level 1 Data Flow Diagram decomposes the system into six core operational sub-processes: (1.0) User Authentication &amp; RBAC Validation, (2.0) Flats &amp; Resident Directory Management, (3.0) Maintenance Assessment &amp; Payment Processing, (4.0) Service Grievance Management, (5.0) Security Gate Visitor Tracking, and (6.0) Society Notice Board &amp; Reporting. Each process interfaces directly with dedicated relational data stores to ensure transactional isolation."""
    story.append(Paragraph(p_dfd1, s['body']))
    story.append(Spacer(1, 8))
    if os.path.exists("report_assets/diagrams/fig03_dfd_level1.png"):
        story.append(Image("report_assets/diagrams/fig03_dfd_level1.png", width=440, height=270))
    story.append(Paragraph("Figure 5: DFD Level 1 – Functional Process Decomposition", s['fig_caption']))
    story.append(PageBreak())

    # PAGE 22: USE CASE DIAGRAM (Body p. 12)
    p_uc = """The Use Case Diagram defines the behavioral capabilities accessible to each authenticated actor within the society system boundary. The Administrator maintains complete system privileges spanning flat allocations, billing generation, and notice broadcasts. The Resident interacts with personalized self-service capabilities including dues review, bill settlement, and complaint lodging. The Security Guard executes gatekeeper visitor logging and checkout actions."""
    story.append(Paragraph(p_uc, s['body']))
    story.append(Spacer(1, 8))
    if os.path.exists("report_assets/diagrams/fig04_use_case.png"):
        story.append(Image("report_assets/diagrams/fig04_use_case.png", width=440, height=270))
    story.append(Paragraph("Figure 6: Use Case Diagram", s['fig_caption']))
    story.append(PageBreak())

def add_chapters4_5_6(story, s):
    # PAGE 23: CHAPTER 4: SYSTEM DESIGN - 4.1 BASIC MODULES (Body p. 13)
    story.append(Paragraph("Chapter 4: System Design", s['ch_heading']))
    story.append(Paragraph("4.1 Basic Modules", s['sec_heading']))
    p_mod_intro = """Central Park Housing Society Management System is partitioned into eight autonomous yet tightly cohesive functional modules:<br/><br/>
• <b>Authentication &amp; RBAC Security Module:</b> Manages cryptographic password validation, session cookie lifecycle, and role-based URL protection across admin, resident, and security contexts.<br/>
• <b>Flats &amp; Occupancy Management Module:</b> Provides complete CRUD capabilities for society blocks, apartment numbers, square footage, owner/tenant occupancy status, and base maintenance tariffs.<br/>
• <b>Resident Member Directory Module:</b> Maintains resident demographics, verified phone numbers, email addresses, move-in dates, and linked flat associations.<br/>
• <b>Maintenance Assessment &amp; Billing Module:</b> Computes periodic assessments, sinking funds, and penalty surcharges; generates official printable receipts with tamper-evident serials.<br/>
• <b>Complaints &amp; Grievance Resolution Module:</b> Facilitates resident ticket submission, priority tagging, administrative review, and status tracking through to resolution.<br/>
• <b>Gatekeeper Visitor Security Module:</b> Operates real-time gate entry registration, visitor badge details, host flat notifications, and one-click exit timestamping.<br/>
• <b>Society Notice Board Module:</b> Manages public circular broadcasting, announcement prioritization, and archived bulletin auditing.<br/>
• <b>Vehicle Directory &amp; Reporting Module:</b> Maintains authorized parking allocations and exports structured CSV reports for financial auditing."""
    story.append(Paragraph(p_mod_intro, s['body']))
    story.append(PageBreak())

    # PAGE 24: SYSTEM ARCHITECTURE (Body p. 14)
    p_arch = """Central Park Housing Society Management System follows a strict Three-Tier Client-Server Architecture (Figure 7). The Presentation Tier consists of responsive HTML5/Bootstrap 5 views rendered directly in the user’s web browser. The Application Tier is driven by Python Flask controllers running in a WSGI environment, executing routing, authentication middleware, and business logic. The Data Tier is backed by a relational SQLite/MySQL database enforcing ACID transactions and referential foreign-key integrity."""
    story.append(Paragraph(p_arch, s['body']))
    story.append(Spacer(1, 8))
    if os.path.exists("report_assets/diagrams/fig05_system_architecture.png"):
        story.append(Image("report_assets/diagrams/fig05_system_architecture.png", width=440, height=270))
    story.append(Paragraph("Figure 7: System Architecture (Three-Tier)", s['fig_caption']))
    story.append(PageBreak())

    # PAGE 25: 4.2 DATA DESIGN - SCHEMA PART 1 (Body p. 15)
    story.append(Paragraph("4.2 Data Design", s['sec_heading']))
    story.append(Paragraph("4.2.1 Schema Design", s['sec_heading']))
    story.append(Paragraph("The relational data schema is normalized to Third Normal Form (3NF). Core table specifications are detailed below:", s['body']))

    story.append(Paragraph("<b>Table: users</b>", s['body_bold']))
    u_data = [
        [Paragraph("<b>Column</b>", s['body_bold']), Paragraph("<b>Type</b>", s['body_bold']), Paragraph("<b>Constraints</b>", s['body_bold']), Paragraph("<b>Description</b>", s['body_bold'])],
        ["id", "INTEGER", "PRIMARY KEY AUTOINCREMENT", "Unique internal user identifier"],
        ["username", "VARCHAR(50)", "NOT NULL, UNIQUE", "Login handle / credential"],
        ["password", "VARCHAR(255)", "NOT NULL", "Werkzeug salted SHA-256 password hash"],
        ["role", "VARCHAR(20)", "NOT NULL", "Operational role: 'admin', 'resident', 'security'"],
        ["full_name", "VARCHAR(100)", "NOT NULL", "Full display name of account holder"],
        ["created_at", "DATETIME", "DEFAULT CURRENT_TIMESTAMP", "Account provisioning timestamp"]
    ]
    story.append(make_styled_table(u_data, [70, 85, 125, 170], styles=s, bold_cols=(0,)))
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b>Table: flats</b>", s['body_bold']))
    f_data = [
        [Paragraph("<b>Column</b>", s['body_bold']), Paragraph("<b>Type</b>", s['body_bold']), Paragraph("<b>Constraints</b>", s['body_bold']), Paragraph("<b>Description</b>", s['body_bold'])],
        ["id", "INTEGER", "PRIMARY KEY AUTOINCREMENT", "Unique flat identifier"],
        ["flat_number", "VARCHAR(20)", "NOT NULL, UNIQUE", "Apartment identifier (e.g. 'A-101')"],
        ["block", "VARCHAR(10)", "NOT NULL", "Building wing or tower (e.g. 'Wing A')"],
        ["floor", "INTEGER", "NOT NULL", "Floor level within building"],
        ["bhk_type", "VARCHAR(10)", "NOT NULL", "Configuration (e.g. '2BHK', '3BHK')"],
        ["status", "VARCHAR(20)", "DEFAULT 'vacant'", "Occupancy status: 'occupied', 'vacant'"],
        ["maint_amount", "REAL", "DEFAULT 3000.00", "Base monthly maintenance tariff"]
    ]
    story.append(make_styled_table(f_data, [70, 85, 125, 170], styles=s, bold_cols=(0,)))
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b>Table: residents</b>", s['body_bold']))
    r_data = [
        [Paragraph("<b>Column</b>", s['body_bold']), Paragraph("<b>Type</b>", s['body_bold']), Paragraph("<b>Constraints</b>", s['body_bold']), Paragraph("<b>Description</b>", s['body_bold'])],
        ["id", "INTEGER", "PRIMARY KEY AUTOINCREMENT", "Unique resident record identifier"],
        ["user_id", "INTEGER", "UNIQUE, FK(users.id)", "Linked system user account"],
        ["flat_id", "INTEGER", "FK(flats.id)", "Assigned apartment flat"],
        ["phone", "VARCHAR(20)", "NOT NULL", "Verified mobile phone number"],
        ["email", "VARCHAR(100)", "NOT NULL", "Resident email address for notices"],
        ["move_in_date", "DATE", "NOT NULL", "Official occupancy start date"]
    ]
    story.append(make_styled_table(r_data, [70, 85, 125, 170], styles=s, bold_cols=(0,)))
    story.append(PageBreak())

    # PAGE 26: SCHEMA DESIGN PART 2 (Body p. 16)
    story.append(Paragraph("<b>Table: maintenance</b>", s['body_bold']))
    m_data = [
        [Paragraph("<b>Column</b>", s['body_bold']), Paragraph("<b>Type</b>", s['body_bold']), Paragraph("<b>Constraints</b>", s['body_bold']), Paragraph("<b>Description</b>", s['body_bold'])],
        ["id", "INTEGER", "PRIMARY KEY AUTOINCREMENT", "Unique billing assessment ID"],
        ["flat_id", "INTEGER", "NOT NULL, FK(flats.id)", "Target apartment flat"],
        ["month_year", "VARCHAR(20)", "NOT NULL", "Billing cycle period (e.g. 'October 2026')"],
        ["amount", "REAL", "NOT NULL", "Total assessed maintenance due"],
        ["status", "VARCHAR(20)", "DEFAULT 'unpaid'", "Bill status: 'unpaid', 'paid'"],
        ["due_date", "DATE", "NOT NULL", "Payment due cutoff date"]
    ]
    story.append(make_styled_table(m_data, [70, 85, 125, 170], styles=s, bold_cols=(0,)))
    story.append(Spacer(1, 4))

    story.append(Paragraph("<b>Table: payments</b>", s['body_bold']))
    p_data = [
        [Paragraph("<b>Column</b>", s['body_bold']), Paragraph("<b>Type</b>", s['body_bold']), Paragraph("<b>Constraints</b>", s['body_bold']), Paragraph("<b>Description</b>", s['body_bold'])],
        ["id", "INTEGER", "PRIMARY KEY AUTOINCREMENT", "Unique payment ledger transaction ID"],
        ["maint_id", "INTEGER", "NOT NULL, FK(maintenance.id)", "Referenced assessment bill"],
        ["paid_by", "INTEGER", "NOT NULL, FK(residents.id)", "Resident executing payment"],
        ["amount", "REAL", "NOT NULL", "Settled monetary sum"],
        ["payment_mode", "VARCHAR(50)", "NOT NULL", "Method: 'Online UPI', 'Card', 'Cheque', 'Cash'"],
        ["payment_date", "DATETIME", "DEFAULT CURRENT_TIMESTAMP", "Certified settlement timestamp"]
    ]
    story.append(make_styled_table(p_data, [70, 85, 125, 170], styles=s, bold_cols=(0,)))
    story.append(Spacer(1, 4))

    story.append(Paragraph("<b>Table: visitors</b>", s['body_bold']))
    v_data = [
        [Paragraph("<b>Column</b>", s['body_bold']), Paragraph("<b>Type</b>", s['body_bold']), Paragraph("<b>Constraints</b>", s['body_bold']), Paragraph("<b>Description</b>", s['body_bold'])],
        ["id", "INTEGER", "PRIMARY KEY AUTOINCREMENT", "Gate pass entry serial"],
        ["visitor_name", "VARCHAR(100)", "NOT NULL", "Full visitor legal name"],
        ["phone", "VARCHAR(20)", "NOT NULL", "Visitor verified contact number"],
        ["flat_id", "INTEGER", "NOT NULL, FK(flats.id)", "Destination visiting apartment"],
        ["purpose", "VARCHAR(200)", "NOT NULL", "Stated visit objective"],
        ["check_in", "DATETIME", "DEFAULT CURRENT_TIMESTAMP", "Security gate entry timestamp"],
        ["check_out", "DATETIME", "NULL", "Exit departure timestamp"]
    ]
    story.append(make_styled_table(v_data, [70, 85, 125, 170], styles=s, bold_cols=(0,)))
    story.append(Spacer(1, 4))

    story.append(Paragraph("<b>Tables: complaints, vehicles, notices</b>", s['body_bold']))
    o_data = [
        [Paragraph("<b>Table</b>", s['body_bold']), Paragraph("<b>Key Columns</b>", s['body_bold']), Paragraph("<b>Foreign Keys</b>", s['body_bold']), Paragraph("<b>Description</b>", s['body_bold'])],
        ["complaints", "id, resident_id, category, title, description, status, created_at", "FK(residents.id)", "Grievance ticketing ledger with status lifecycle"],
        ["vehicles", "id, resident_id, vehicle_type, vehicle_number, slot_number", "FK(residents.id)", "Resident vehicle directory and allocated parking bays"],
        ["notices", "id, title, content, posted_by, priority, created_at", "FK(users.id)", "Society administrative circulars and broadcasting board"]
    ]
    story.append(make_styled_table(o_data, [70, 145, 95, 140], styles=s, bold_cols=(0,)))
    story.append(PageBreak())

    # PAGE 27: 4.2.2 & 4.3 PROCEDURAL DESIGN (Body p. 17)
    story.append(Paragraph("4.2.2 Data Integrity and Constraints", s['sec_heading']))
    p_dic = """Data integrity is maintained through explicit database constraints:<br/>
• <b>Entity Integrity:</b> Every table designates an auto-incrementing integer `id` as its PRIMARY KEY.<br/>
• <b>Referential Integrity:</b> Foreign keys enforce relational cascades and prevent orphaned child records: `residents.user_id` strictly references `users.id`, `maintenance.flat_id` references `flats.id`, and `payments.maint_id` references `maintenance.id`.<br/>
• <b>Domain Integrity:</b> Enumerated values constrain inputs (e.g., user roles must be 'admin', 'resident', or 'security'; maintenance status is strictly 'unpaid' or 'paid'; complaint tickets progress from 'Pending' to 'In Progress' to 'Resolved').<br/>
• <b>Uniqueness Constraints:</b> `users.username` and `flats.flat_number` enforce unique indexing to prevent duplicate registrations."""
    story.append(Paragraph(p_dic, s['body']))

    story.append(Paragraph("4.3 Procedural Design", s['sec_heading']))
    story.append(Paragraph("4.3.1 Logic Diagrams", s['sec_heading']))
    p_ld = """Procedural design models the sequential step-by-step algorithms governing system operations. The primary transactional workflow—encompassing resident authentication, bill payment with automated receipt generation, grievance submission, and security visitor gate pass clearance—is diagrammed in Figure 8. The flowchart details decision logic, role gates, and database write transactions."""
    story.append(Paragraph(p_ld, s['body']))
    story.append(PageBreak())

    # PAGE 28: FLOWCHART (Body p. 18)
    p_fc = """The procedural flowchart (Figure 8) traces the execution logic across the Central Park Housing Society Management System. Upon authentication, the system validates the user session and role. Administrators can navigate to flat directories, generate assessments, and resolve complaints. Residents can inspect maintenance arrears, execute payment settlements that automatically trigger instant printable receipt generation, and lodge service complaints. Security guards operate the visitor logging terminal to record check-ins and process 1-click departures."""
    story.append(Paragraph(p_fc, s['body']))
    story.append(Spacer(1, 8))
    if os.path.exists("report_assets/diagrams/fig06_flowchart.png"):
        story.append(Image("report_assets/diagrams/fig06_flowchart.png", width=440, height=270))
    story.append(Paragraph("Figure 8: Flowchart – Resident Maintenance & Gate Pass Workflow", s['fig_caption']))
    story.append(PageBreak())

    # PAGE 29: 4.3.2 & 4.3.3 DATA STRUCTURES & ALGORITHMS (Body p. 19)
    story.append(Paragraph("4.3.2 Data Structures", s['sec_heading']))
    p_ds = """The Python Flask backend leverages structured in-memory data structures: (1) <b>Dictionaries &amp; Row Objects:</b> `sqlite3.Row` instances provide key-indexed attribute access (`row['flat_number']`) for clean template rendering; (2) <b>Session Tuples:</b> Flask's cryptographically signed cookie session stores `user_id`, `role`, and `full_name` across requests; (3) <b>Dynamic Lists:</b> Query result sets are transformed into Python lists of dictionaries for aggregation, KPI calculation, and streaming CSV generation."""
    story.append(Paragraph(p_ds, s['body']))

    story.append(Paragraph("4.3.3 Algorithms Design", s['sec_heading']))
    p_alg = """<b>1. Maintenance Assessment Generation Algorithm:</b><br/>
1. Query all flats where `status = 'occupied'`.<br/>
2. Iterate through each flat record and extract its configured `maint_amount`.<br/>
3. Check whether an assessment already exists for the target `month_year`.<br/>
4. If absent, insert a new record into `maintenance` with status `'unpaid'` and due date.<br/>
5. Return summary count of generated assessments.<br/><br/>
<b>2. Real-Time Visitor Gate Log &amp; Elapsed Timer Algorithm:</b><br/>
1. Query active visitors from `visitors` where `check_out IS NULL`.<br/>
2. For each active visitor, compute duration = `CURRENT_TIMESTAMP - check_in`.<br/>
3. Format elapsed time into human-readable hours and minutes.<br/>
4. On departure button click, update visitor record setting `check_out = CURRENT_TIMESTAMP`."""
    story.append(Paragraph(p_alg, s['body']))
    story.append(PageBreak())

    # PAGE 30: UI DESIGN & SECURITY (Body p. 20)
    story.append(Paragraph("4.4 User Interface Design", s['sec_heading']))
    p_ui = """The interface implements a modern, card-based responsive design system built upon Bootstrap 5.3. A unified palette featuring deep navy (#1E3A8A), slate steel (#2E74B5), and off-white neutral cards (#F8FAFC) creates visual consistency. Key metrics are presented through KPI summary cards with prominent numeric counters. Statuses are indicated via color-coded badges: Green for 'Paid' / 'Resolved', Yellow for 'Pending' / 'In Progress', and Red for 'Unpaid' / 'Overdue'. Action buttons feature clear typography and SVG iconography. Complete interface screenshots are documented in Chapter 6."""
    story.append(Paragraph(p_ui, s['body']))

    story.append(Paragraph("4.5 Security Issues", s['sec_heading']))
    p_sec = """Web applications handling financial data and residential records require strict security defenses: (1) <b>Password Encryption:</b> Passwords are never stored in plaintext; Werkzeug's `generate_password_hash` generates SHA-256 salted hashes; (2) <b>SQL Injection Prevention:</b> All queries use prepared statements with parameterized input placeholders (`?`); (3) <b>Session Protection:</b> HTTP-only, SameSite session cookies prevent cross-site scripting (XSS) cookie theft; (4) <b>RBAC Enforcement:</b> A centralized `@login_required(role)` decorator validates session privileges prior to executing controller logic."""
    story.append(Paragraph(p_sec, s['body']))

    story.append(Paragraph("4.6 Test Cases Design", s['sec_heading']))
    p_tcd = """Test cases were designed across positive and negative input vectors, boundary scenarios, and role violation attempts to ensure full test coverage of authentication, billing calculations, receipt validation, and visitor logging. Formal execution results are presented in Section 5.5."""
    story.append(Paragraph(p_tcd, s['body']))
    story.append(PageBreak())

    # PAGE 31: CHAPTER 5: IMPLEMENTATION AND TESTING (Body p. 21)
    story.append(Paragraph("Chapter 5: Implementation and Testing", s['ch_heading']))
    story.append(Paragraph("5.1 Implementation Approaches", s['sec_heading']))
    p_imp = """Central Park Housing Society Management System was implemented incrementally following a modular development methodology: first the database engine and table initialization; second, the authentication and role middleware; third, administrative flat and resident management; fourth, the maintenance billing and receipt printing engine; fifth, the security visitor checkpoint console; and sixth, the resident self-service portal and reporting analytics."""
    story.append(Paragraph(p_imp, s['body']))

    story.append(Paragraph("5.2 Coding Details and Code Efficiency", s['sec_heading']))
    p_code_intro = """Representative code snippets illustrating core application mechanics are shown below. Full listings are provided in Appendix A.<br/><br/>
<b>1. Role-Based Access Control Middleware Decorator:</b>"""
    story.append(Paragraph(p_code_intro, s['body']))

    code1 = """def login_required(role=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash("Please log in to access this page.", "warning")
                return redirect(url_for('login'))
            if role and session.get('role') != role:
                flash("Access denied: Unauthorized role privileges.",
                      "danger")
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator"""
    box1 = Table([[Preformatted(code1, s['code_font'])]], colWidths=[USABLE_WIDTH])
    box1.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.5, CODE_BORDER),
        ('BACKGROUND', (0,0), (-1,-1), CODE_BG),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(box1)
    story.append(Spacer(1, 4))

    story.append(Paragraph("<b>2. Password Hashing &amp; Verification (Werkzeug Security):</b>", s['body']))
    code2 = """# Password Hashing during User Provisioning
from werkzeug.security import generate_password_hash, check_password_hash
hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')

# Credential Verification at Login
user = query_db(
    "SELECT * FROM users WHERE username = ?", (username,), one=True
)
if user and check_password_hash(user['password'], password):
    session['user_id'] = user['id']
    session['role'] = user['role']
    session['full_name'] = user['full_name']"""
    box2 = Table([[Preformatted(code2, s['code_font'])]], colWidths=[USABLE_WIDTH])
    box2.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.5, CODE_BORDER),
        ('BACKGROUND', (0,0), (-1,-1), CODE_BG),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(box2)
    story.append(PageBreak())

    # PAGE 32: 5.2.1 CODE EFFICIENCY & TESTING (Body p. 22)
    story.append(Paragraph("<b>3. Parameterized SQL Query with Relational Joins:</b>", s['body']))
    code3 = '''# Parameterized Multi-Table Relational Query
query = """
    SELECT p.id as payment_id, p.amount, p.payment_mode, p.payment_date,
           m.month_year, f.flat_number, f.block,
           u.full_name as resident_name, r.phone
    FROM payments p
    JOIN maintenance m ON p.maint_id = m.id
    JOIN flats f ON m.flat_id = f.id
    JOIN residents r ON p.paid_by = r.id
    JOIN users u ON r.user_id = u.id
    WHERE p.id = ?
"""
receipt = query_db(query, (payment_id,), one=True)'''
    box3 = Table([[Preformatted(code3, s['code_font'])]], colWidths=[USABLE_WIDTH])
    box3.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.5, CODE_BORDER),
        ('BACKGROUND', (0,0), (-1,-1), CODE_BG),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(box3)
    story.append(Spacer(1, 4))

    story.append(Paragraph("5.2.1 Code Efficiency", s['sec_heading']))
    p_eff = """Prepared statements ensure query efficiency and prevent SQL injection by allowing the database engine to cache execution plans. In-memory joins are avoided by delegating relational lookups to optimized SQL indexes. The application selects only required columns rather than wildcard `SELECT *` across large tables, minimizing memory overhead."""
    story.append(Paragraph(p_eff, s['body']))

    story.append(Paragraph("5.3 Testing Approach", s['sec_heading']))
    story.append(Paragraph("<b>5.3.1 Unit Testing:</b> Isolated functional unit tests verified individual components including password hashing validity, currency formatting, date parsing, and form field boundary limits (e.g., negative maintenance amounts).", s['body']))
    story.append(Paragraph("<b>5.3.2 Integrated Testing:</b> End-to-end integration workflows verified multi-step transactions: admin bill generation -> resident bill payment -> payment database commit -> automated receipt rendering -> maintenance bill status update to 'paid'.", s['body']))
    story.append(Paragraph("<b>5.3.3 Beta Testing:</b> The application was evaluated under simulated multi-user workloads on local workstations, confirming concurrent session stability between admin, resident, and guard consoles.", s['body']))
    story.append(PageBreak())

    # PAGE 33: 5.4 MODIFICATIONS AND IMPROVEMENTS (Body p. 23)
    story.append(Paragraph("5.4 Modifications and Improvements", s['sec_heading']))
    p_mods = """During the development and testing iterations, several important architectural enhancements were engineered:<br/><br/>
• <b>1-Click Quick Login Role Switcher:</b> Engineered interactive demo buttons on the login interface allowing examiners and evaluators to instantly switch between Administrator, Resident, and Security Guard contexts with a single click, eliminating tedious manual credential typing during evaluations.<br/><br/>
• <b>Tamper-Evident Print-Ready Payment Receipts:</b> Refactored the receipt viewing template with dedicated `@media print` CSS rules, high-contrast typography, society registration header badges, and automated receipt transaction serial numbers, producing official printable vouchers formatted for standard paper and PDF exports.<br/><br/>
• <b>Dynamic Security Visitor Elapsed Timer:</b> Enhanced the gatekeeper visitor dashboard with live elapsed-time calculation (`CURRENT_TIMESTAMP - check_in`) highlighting active visitors on campus and providing an expedited 1-click exit pass checkout button to streamline gate operations.<br/><br/>
• <b>Consolidated CSV Audit Export:</b> Implemented streaming CSV file generation for financial ledgers, member directories, and visitor gate logs, allowing administrators to download instant tabular audits directly into spreadsheet software."""
    story.append(Paragraph(p_mods, s['body']))
    story.append(PageBreak())

    # PAGE 34: 5.5 TEST CASES (Body p. 24)
    story.append(Paragraph("5.5 Test Cases", s['sec_heading']))
    story.append(Paragraph("The test cases executed during formal verification and their empirical results are listed below:", s['body']))

    tc_data = [
        [Paragraph("<b>ID</b>", s['body_bold']), Paragraph("<b>Test Case Description</b>", s['body_bold']), Paragraph("<b>Expected Result</b>", s['body_bold']), Paragraph("<b>Result</b>", s['body_bold'])],
        ["TC01", "Administrator login with valid credentials", "Session created; redirected to Admin Dashboard", "Pass"],
        ["TC02", "Login attempt with incorrect password", "Error alert displayed; access blocked", "Pass"],
        ["TC03", "Resident attempts direct URL access to /admin/flats", "Redirected to login with 'Access Denied' alert", "Pass"],
        ["TC04", "Admin allocates vacant flat to new resident", "Flat status updates to 'occupied'; resident record saved", "Pass"],
        ["TC05", "Generate maintenance assessments for current month", "Assessment records created for all occupied flats", "Pass"],
        ["TC06", "Duplicate maintenance generation in same month", "System detects existing bills; prevents duplicate charges", "Pass"],
        ["TC07", "Resident records maintenance bill settlement", "Payment committed; bill status updates from 'unpaid' to 'paid'", "Pass"],
        ["TC08", "Open official payment receipt (/receipt/<id>)", "Printable formatted receipt renders with society credentials", "Pass"],
        ["TC09", "Resident lodges maintenance service grievance", "Ticket saved with status 'Pending'; appears on Admin list", "Pass"],
        ["TC10", "Admin updates complaint status to 'Resolved'", "Status badge updates to green; resident view reflects update", "Pass"],
        ["TC11", "Security guard logs visitor entry at gate", "Visitor record created with timestamp; added to active roster", "Pass"],
        ["TC12", "Security guard clicks 'Mark Exit' for active visitor", "Checkout timestamp recorded; visitor removed from active list", "Pass"],
        ["TC13", "Admin broadcasts new society announcement", "Circular saved; visible immediately on all resident portals", "Pass"],
        ["TC14", "Admin registers resident four-wheeler vehicle", "Vehicle number and parking bay allocated without conflict", "Pass"],
        ["TC15", "Export maintenance collection report to CSV", "Browser downloads valid RFC-4180 compliant CSV file", "Pass"]
    ]
    t_tc = make_styled_table(tc_data, [40, 170, 195, 45], styles=s, center_cols=(0, 3), bold_cols=(0, 3))
    story.append(t_tc)
    story.append(PageBreak())

    # PAGE 35: CHAPTER 6: RESULTS AND DISCUSSION (Body p. 25)
    story.append(Paragraph("Chapter 6: Results and Discussion", s['ch_heading']))
    story.append(Paragraph("6.1 Test Reports", s['sec_heading']))
    p_tr = """Comprehensive system testing verified that all fifteen formal test cases executed flawlessly without unhandled exceptions or data corruption. The transactional lifecycle of maintenance assessments was confirmed end-to-end: monthly assessments generated by the administrator appear instantly on the resident’s personal portal; upon recording payment, the system dynamically updates bill records from 'unpaid' to 'paid' and renders an official, tamper-evident printable receipt complete with transaction serial numbers. Concurrently, the gate security checkpoint verified real-time visitor duration tracking and 1-click departure logging without data lag. All database constraints preserved referential integrity throughout multi-role testing."""
    story.append(Paragraph(p_tr, s['body']))

    story.append(Paragraph("6.2 User Documentation", s['sec_heading']))
    p_ud = """This section delivers comprehensive visual user documentation illustrating the complete working application across all user roles. Each major operational screen is presented on its own dedicated page accompanied by a detailed description of user interactions, system controls, and functional workflows. The documentation is organized into three sequential role workflows: Administrator Workflow (Figures 9 to 27), Resident Workflow (Figures 28 to 30), and Security Guard Workflow (Figure 31)."""
    story.append(Paragraph(p_ud, s['body']))
    story.append(PageBreak())

def add_user_documentation_pages(story, s):
    # Base directory for screenshots
    sc_dir = "report_assets/screenshots"

    # Helper function for adding dedicated screenshot page
    def add_screenshot_page(intro_title, intro_text, img_filename, fig_num, caption_title):
        if intro_title:
            story.append(Paragraph(intro_title, s['ch_heading']))
        story.append(Paragraph(intro_text, s['body']))
        story.append(Spacer(1, 8))
        img_path = os.path.join(sc_dir, img_filename)
        if os.path.exists(img_path):
            story.append(Image(img_path, width=440, height=235))
        story.append(Spacer(1, 6))
        story.append(Paragraph(f"Figure {fig_num}: {caption_title}", s['fig_caption']))
        story.append(PageBreak())

    # PAGE 36: FIG 9 (Body p. 26)
    add_screenshot_page(
        "Administrator & Resident Workflows",
        "The authentication interface serves as the primary gateway for all society members. It provides a secure credential login form alongside an interactive 1-click Quick Login demo switcher allowing evaluators to immediately log in as Administrator, Resident, or Security Guard without manual typing.",
        "fig09_login.png", 9, "Portal Login & Quick-Login Role Switcher Interface"
    )

    # PAGE 37: FIG 10 (Body p. 27)
    add_screenshot_page(
        None,
        "Upon successful administrator authentication, the executive dashboard displays real-time KPI overview cards including Total Flats (Occupied vs. Vacant), Registered Residents, Monthly Maintenance Collected vs. Pending, and Active Visitors currently on society premises.",
        "fig10_admin_dashboard.png", 10, "Administrator Central Control Dashboard – Overview & KPIs"
    )

    # PAGE 38: FIG 11 (Body p. 28)
    add_screenshot_page(
        None,
        "The Flats Management directory provides full administrative control over all society residential units. Each flat entry details its building wing, floor number, BHK configuration, occupancy status badge ('Occupied' in green or 'Vacant' in grey), and base monthly maintenance tariff.",
        "fig11_flats_directory.png", 11, "Flats Management – Residential Apartment Directory & Status"
    )

    # PAGE 39: FIG 12 (Body p. 29)
    add_screenshot_page(
        None,
        "Administrators can configure new apartments or update existing flat allocations through the Add/Edit Flat modal interface. The system validates uniqueness constraints on flat numbers and ensures that maintenance assessment tariffs are assigned accurately.",
        "fig12_flats_add_modal.png", 12, "Flats Management – Apartment Details & Allocation Roster"
    )

    # PAGE 40: FIG 13 (Body p. 30)
    add_screenshot_page(
        None,
        "The Resident Member Directory maintains comprehensive demographic records for every verified resident in the society. The tabular view shows the resident's full name, linked apartment flat, verified mobile phone number, email address, and official move-in date.",
        "fig13_resident_directory.png", 13, "Resident Member Directory – Resident Contact Information"
    )

    # PAGE 41: FIG 14 (Body p. 31)
    add_screenshot_page(
        None,
        "The Resident Provisioning console allows administrators to onboard new society residents by linking a user login account to a specific vacant flat. The system automatically marks the target apartment as occupied and binds family contact details.",
        "fig14_resident_add_modal.png", 14, "Resident Directory – Flat Ownership & Family Records"
    )

    # PAGE 42: FIG 15 (Body p. 32)
    add_screenshot_page(
        None,
        "The Maintenance & Billing module automates society revenue collection. Administrators can initiate one-click monthly assessment generation across all occupied flats. The master schedule tracks total assessed amounts, settled collections, and outstanding arrears per flat.",
        "fig15_maintenance_billing.png", 15, "Maintenance Billing – Assessment Generation & Bill Schedule"
    )

    # PAGE 43: FIG 16 (Body p. 33)
    add_screenshot_page(
        None,
        "The Maintenance Payment Ledger displays an audit trail of all recorded financial settlements. Administrators can log offline payments received via bank transfer, cheque, or cash, immediately updating bill statuses from unpaid to paid.",
        "fig16_maintenance_ledger.png", 16, "Maintenance Billing – Dues Ledger & Payment Tracking"
    )

    # PAGE 44: FIG 17 (Body p. 34)
    add_screenshot_page(
        None,
        "The system incorporates an official, print-ready payment receipt template formatted with dedicated high-contrast typography, society registration credentials, resident allocation details, payment mode, and automated transaction verification codes.",
        "fig17_payment_receipt.png", 17, "Official Society Maintenance Payment Receipt (Print View)"
    )

    # PAGE 45: FIG 18 (Body p. 35)
    add_screenshot_page(
        None,
        "The Complaints Management console provides an organized ticket overview of all resident grievances. Each complaint shows the submitting resident's flat, category (Plumbing, Electrical, Security, Noise), priority badge, and current resolution lifecycle state.",
        "fig18_complaints_admin.png", 18, "Complaints & Grievances Management – Admin Review Table"
    )

    # PAGE 46: FIG 19 (Body p. 36)
    add_screenshot_page(
        None,
        "Administrators can open individual grievance tickets to review full resident descriptions and update resolution statuses from 'Pending' to 'In Progress' or 'Resolved'. Status updates reflect instantly on the resident's portal with resolution timestamps.",
        "fig19_complaints_action.png", 19, "Complaints Management – Ticket Details & Resolution Actions"
    )

    # PAGE 47: FIG 20 (Body p. 37)
    add_screenshot_page(
        None,
        "The Security Visitor Gate Log maintains a centralized, searchable ledger of all campus entries. Security guards and administrators can monitor visitor names, mobile numbers, destination flats, entry times, and checkout statuses.",
        "fig20_visitor_management.png", 20, "Security Visitor Gate Log – Real-Time Premises Tracking"
    )

    # PAGE 48: FIG 21 (Body p. 38)
    add_screenshot_page(
        None,
        "Security personnel can rapidly log incoming visitors using the streamlined gate check-in form. The terminal validates mobile phone length, records the stated purpose of visit, and tags the host flat to notify residents.",
        "fig21_visitor_active.png", 21, "Security Visitor Gate Log – Check-In Registration Form"
    )

    # PAGE 49: FIG 22 (Body p. 39)
    add_screenshot_page(
        "Society Notice Board",
        "The digital notice board replaces physical paper circulars with an accessible online announcement board. Circulars are categorized by priority (General, Important, Urgent) and display posting dates and administrative sign-offs.",
        "fig22_society_notices.png", 22, "Society Notice Board – Digital Announcements & Circulars"
    )

    # PAGE 50: FIG 23 (Body p. 40)
    add_screenshot_page(
        None,
        "Administrators can broadcast urgent announcements, AGM notifications, or water maintenance schedules using the Notice Publishing form. Newly published notices are displayed prominently at the top of resident portals.",
        "fig23_publish_notice.png", 23, "Society Notice Board – Broadcast New Announcement Console"
    )

    # PAGE 51: FIG 24 (Body p. 41)
    add_screenshot_page(
        None,
        "The Authorized Vehicle Directory maintains a verified roster of resident four-wheelers and two-wheelers linked to resident flats. Security guards can cross-reference vehicle registration numbers against assigned parking bays to prevent unauthorized parking.",
        "fig24_vehicle_directory.png", 24, "Vehicle Directory – Authorized Resident Parking Roster"
    )

    # PAGE 52: FIG 25 (Body p. 42)
    add_screenshot_page(
        None,
        "New resident vehicles are registered through a validated form specifying vehicle classification (Four-Wheeler / Two-Wheeler), license plate number, resident owner, and dedicated parking slot identifier.",
        "fig25_vehicle_register.png", 25, "Vehicle Directory – Register New Vehicle & Slot Allocation"
    )

    # PAGE 53: FIG 26 (Body p. 43)
    add_screenshot_page(
        None,
        "The Financial Analytics & Operations Center aggregates real-time society statistics including maintenance collection efficiency percentages, category-wise complaint distributions, and monthly visitor traffic summaries.",
        "fig26_reports_analytics.png", 26, "Financial Analytics & Operations Audit Center"
    )

    # PAGE 54: FIG 27 (Body p. 44)
    add_screenshot_page(
        None,
        "Administrators can generate on-demand, RFC-4180 compliant CSV file downloads for maintenance ledgers, active resident rosters, and visitor logs, allowing instant export into external accounting spreadsheets for statutory society audits.",
        "fig27_export_csv.png", 27, "Reports Center – Exportable CSV Financial Summaries"
    )

    # PAGE 55: FIG 28 (Body p. 45)
    add_screenshot_page(
        "Resident Workflow",
        "The Resident Portal Dashboard provides resident members with a personalized landing experience showing flat assignment details, current billing status, active grievance summaries, and recent society circulars.",
        "fig28_resident_dashboard.png", 28, "Resident Personal Portal Dashboard – Flat Summary & Activity"
    )

    # PAGE 56: FIG 29 (Body p. 46)
    add_screenshot_page(
        None,
        "Residents can inspect their complete maintenance billing breakdown, check outstanding payment cutoff dates, execute instant online settlements via simulated UPI/Card options, and retrieve official printable payment receipts.",
        "fig29_resident_bills.png", 29, "Resident Maintenance Bills – Breakdown & Instant Settlement"
    )

    # PAGE 57: FIG 30 (Body p. 47)
    add_screenshot_page(
        None,
        "The Resident Grievance portal allows flat owners to lodge service requests regarding electrical faults, plumbing leaks, or common area maintenance, and track administrator action notes in real time.",
        "fig30_resident_complaints.png", 30, "Resident Service Complaint Lodging Form & Resolution History"
    )

    # PAGE 58: FIG 31 (Body p. 48)
    add_screenshot_page(
        "Security Guard Workflow",
        "The Security Guard Console is an expedited checkpoint terminal optimized for fast visitor entry pass logging, active campus occupancy inspection, and 1-click visitor departure checkout.",
        "fig31_security_dashboard.png", 31, "Security Guard Console – Fast Visitor Pass Issuance & 1-Click Exit"
    )

def add_conclusions_and_appendices(story, s):
    # PAGE 59: CHAPTER 7: CONCLUSIONS (Body p. 49)
    story.append(Paragraph("Chapter 7: Conclusions", s['ch_heading']))
    story.append(Paragraph("7.1 Conclusion", s['sec_heading']))
    p_conc = """Central Park Housing Society Management System successfully delivers a robust, multi-role web application that modernizes, automates, and unifies residential housing society administration. All primary objectives formulated during requirement analysis—secure role-based authentication, dynamic flat management, resident contact directories, automated maintenance billing with tamper-evident receipt generation, grievance resolution tracking, gatekeeper visitor monitoring, vehicle roster allocation, digital circular broadcasting, and CSV analytics—have been successfully engineered, verified, and demonstrated through empirical testing."""
    story.append(Paragraph(p_conc, s['body']))

    story.append(Paragraph("7.1.1 Significance of the System", s['sec_heading']))
    p_sig = """The significance of the system lies in replacing error-prone, fragmented paper ledgers and manual register books with a secure, centralized relational database application. Housing society committees save numerous administrative volunteer hours each month by executing automated billing assessments and instant receipt generation. Real-time visitor gate tracking substantially tightens perimeter security, while transparent grievance workflows foster mutual trust and operational clarity between residents and committee executives."""
    story.append(Paragraph(p_sig, s['body']))

    story.append(Paragraph("7.2 Limitations of the System", s['sec_heading']))
    p_lim = """While the application fulfills all specified core academic requirements, certain operational limitations exist in the current release: (1) Payment processing currently operates via simulated online settlement and offline recording rather than direct commercial payment gateway APIs (e.g. Razorpay/Stripe); (2) Automated SMS/Email gateway push alerts are not yet configured, relying instead on internal web notice boards; and (3) Gate barrier operations are software-driven and lack physical IoT boom-barrier hardware integration."""
    story.append(Paragraph(p_lim, s['body']))
    story.append(PageBreak())

    # PAGE 60: 7.3 FUTURE SCOPE (Body p. 50)
    story.append(Paragraph("7.3 Future Scope of the Project", s['sec_heading']))
    p_fs = """Several planned enhancements have been architected for future iterative versions of the Central Park Housing Society Management System:<br/><br/>
• <b>Real-Time Online Payment Gateway Integration:</b> Integrate live payment aggregators (Razorpay, UPI Deep Linking, Stripe) to enable automated real-time payment webhooks, automatic reconciliation, and instant settlement clearance.<br/><br/>
• <b>Automated Push &amp; WhatsApp Notifications:</b> Integrate Twilio or WhatsApp Business APIs to dispatch automated maintenance billing invoices, payment confirmation receipts, urgent society circulars, and guest arrival notifications directly to resident smartphones.<br/><br/>
• <b>IoT-Based RFID Gate Barriers &amp; ANPR Cameras:</b> Interface with physical RFID tag readers and Automated Number Plate Recognition (ANPR) cameras at entrance gates to permit automatic barrier lifting for registered resident vehicles.<br/><br/>
• <b>Facility &amp; Clubhouse Amenity Booking:</b> Engineer a dedicated reservation calendar module allowing residents to check real-time availability and book society clubhouses, swimming pools, tennis courts, and party halls with integrated deposit tracking.<br/><br/>
• <b>Native Mobile Applications:</b> Package responsive front-end views into cross-platform native iOS and Android applications utilizing Flutter or React Native with biometric fingerprint/face authentication."""
    story.append(Paragraph(p_fs, s['body']))
    story.append(PageBreak())

    # PAGE 61: REFERENCES (Body p. 51)
    story.append(Paragraph("References", s['ch_heading']))
    story.append(Spacer(1, 8))
    refs = [
        '[1] Python Software Foundation, "Python 3.11 Documentation & Standard Library Reference," 2024. [Online]. Available: https://docs.python.org/3/',
        '[2] Pallets Projects, "Flask Documentation (Release 3.0.x) — The Python Microframework for Web Development," 2024. [Online]. Available: https://flask.palletsprojects.com/',
        '[3] SQLite Development Team, "SQLite Database Engine Reference Manual and SQL Syntax Guide," 2024. [Online]. Available: https://www.sqlite.org/docs.html',
        '[4] Bootstrap Authors, "Bootstrap v5.3 Documentation — The Most Popular HTML, CSS, and JS Library," 2024. [Online]. Available: https://getbootstrap.com/docs/5.3/',
        '[5] Pallets Projects, "Jinja2 Documentation — Modern and Designer-Friendly Templating Language for Python," 2024. [Online]. Available: https://jinja.palletsprojects.com/',
        '[6] Pallets Projects, "Werkzeug Security Utilities Documentation — Password Hashing and Cryptographic Primitives," 2024. [Online]. Available: https://werkzeug.palletsprojects.com/',
        '[7] ReportLab Europe Ltd., "ReportLab PDF Generation User Guide (Version 4.x)," 2024. [Online]. Available: https://www.reportlab.com/docs/',
        '[8] R. Elmasri and S. B. Navathe, "Fundamentals of Database Systems," 7th ed., Pearson Education, 2016.'
    ]
    for r in refs:
        story.append(Paragraph(r, s['body']))
        story.append(Spacer(1, 6))
    story.append(PageBreak())

    # PAGE 62: GLOSSARY (Body p. 52)
    story.append(Paragraph("Glossary", s['ch_heading']))
    story.append(Spacer(1, 6))
    gloss_data = [
        [Paragraph("<b>Term</b>", s['body_bold']), Paragraph("<b>Technical Definition</b>", s['body_bold'])],
        ["Flask", "A lightweight, WSGI-compliant micro web framework for Python designed for modular extensibility."],
        ["SQLite", "A C-language library implementing a small, fast, self-contained, high-reliability, zero-configuration SQL database engine."],
        ["RBAC", "Role-Based Access Control — a system security mechanism restricting application access according to authorized user roles."],
        ["Jinja2", "A fast, expressive, extensible templating engine for Python supporting automatic HTML escaping and template inheritance."],
        ["Werkzeug", "A comprehensive WSGI web application library providing secure cryptographic password hashing algorithms."],
        ["CSRF", "Cross-Site Request Forgery — a web vulnerability countered in the system through session cookie domain isolation."],
        ["ACID", "Atomicity, Consistency, Isolation, Durability — database transactional properties fully enforced by SQLite and MySQL."],
        ["WSGI", "Web Server Gateway Interface — the universal Python standard specification for communication between web servers and applications."],
        ["3NF", "Third Normal Form — relational schema design standard eliminating transitive dependencies and data anomalies."],
        ["BHK", "Bedroom, Hall, Kitchen — standardized residential apartment spatial configuration measurement."]
    ]
    t_gloss = make_styled_table(gloss_data, [90, 360], styles=s, bold_cols=(0,))
    story.append(t_gloss)
    story.append(PageBreak())

    # PAGE 63: APPENDIX A: SOURCE CODE LISTINGS (Body p. 53)
    story.append(Paragraph("Appendix A: Source Code Listings", s['ch_heading']))
    story.append(Spacer(1, 8))
    p_app_a = """This appendix provides comprehensive source code listings of the core backend application controllers, database models, and presentation templates powering the Central Park Housing Society Management System. The codebase is architected with strict separation of concerns following clean MVC design principles:<br/><br/>
• <b>Application Controller (`app.py`):</b> Contains modular route endpoints, session authentication middleware, maintenance assessment generation, grievance resolution handlers, and streaming CSV export routines.<br/><br/>
• <b>Database Driver (`db.py`):</b> Implements resilient database connection pooling, auto-reconnect logic, row dictionary factories, and automated schema migration routines compatible with both SQLite and MySQL.<br/><br/>
• <b>Print Template (`receipt.html`):</b> The Jinja2 HTML5 presentation template for generating print-ready, tamper-evident housing society maintenance payment vouchers with automated security verification serials.<br/><br/>
The following 13 pages present annotated source code excerpts for the primary components of the system."""
    story.append(Paragraph(p_app_a, s['body']))
    story.append(PageBreak())

    # Helper function for code pages loading from report_assets/code/
    def add_code_page(file_title, purpose_text, code_filename):
        story.append(Paragraph(f"<b>{file_title}</b>", s['sec_heading']))
        story.append(Paragraph(f"<b>Purpose:</b> {purpose_text}", s['body']))
        story.append(Spacer(1, 4))
        code_path = os.path.join("report_assets", "code", code_filename)
        if os.path.exists(code_path):
            with open(code_path, "r", encoding="utf-8") as cf:
                code_text = cf.read().strip()
        else:
            code_text = f"# File {code_filename} not found."
            
        pre = Preformatted(code_text, s['code_font'])
        box = Table([[pre]], colWidths=[USABLE_WIDTH])
        box.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 0.5, CODE_BORDER),
            ('BACKGROUND', (0, 0), (-1, -1), CODE_BG),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(box)
        story.append(PageBreak())

    # PAGES 64 to 76: CODE LISTINGS (Body pp. 54 to 66)
    add_code_page("app.py — Authentication & RBAC Middleware", "Initializes the Flask WSGI kernel and enforces role-based session protection.", "code_64.txt")
    add_code_page("app.py — Administrator Dashboard & KPIs", "Aggregates occupancy metrics, financial balances, active complaints, and recent payment logs.", "code_65.txt")
    add_code_page("app.py — Flats Management Controller", "Manages residential apartment directory, building configurations, and vacancy statuses.", "code_66.txt")
    add_code_page("app.py — Resident Member Provisioning", "Provisions resident user accounts and associates them with vacant apartments.", "code_67.txt")
    add_code_page("app.py — Maintenance Billing Engine", "Automates periodic maintenance assessments and dues tracking across all occupied units.", "code_68.txt")
    add_code_page("app.py — Official Receipt Generator", "Queries certified payment details and generates a tamper-evident printable receipt.", "code_69.txt")
    add_code_page("app.py — Grievance Ticketing Controller", "Manages resident service ticket submission and administrative resolution workflows.", "code_70.txt")
    add_code_page("app.py — Gatekeeper Visitor Console", "Controls gate security logging, active campus tracking, and one-click exit passes.", "code_71.txt")
    add_code_page("app.py — Digital Notice Board Module", "Broadcasting administrative announcements, general circulars, and emergency alerts.", "code_72.txt")
    add_code_page("app.py — Vehicle Parking Directory", "Maintains authorized resident vehicle registration and parking slot allocations.", "code_73.txt")
    add_code_page("app.py — Operations Analytics & CSV Export", "Generates RFC-4180 streaming CSV tabular audit downloads for financial ledgers and gate logs.", "code_74.txt")
    add_code_page("db.py — Database Engine & Connection Pooling", "Configures zero-configuration SQLite connection pooling and executes parameterized queries.", "code_75.txt")
    add_code_page("templates/receipt.html — Print Payment Receipt", "Jinja2 presentation template rendering official, tamper-evident maintenance payment receipts.", "code_76.txt")

    # PAGE 77: APPENDIX B: INSTALLATION & SETUP (Body p. 67)
    story.append(Paragraph("Appendix B: Installation and Setup Guide", s['ch_heading']))
    story.append(Spacer(1, 8))
    p_setup = """The step-by-step instructions below detail how to deploy, configure, and execute the Central Park Housing Society Management System on any local workstation matching the academic development environment.<br/><br/>
<b>1. Clone or Extract the Project Source Directory:</b><br/>
Extract the project archive into a dedicated directory and navigate to the project root:<br/>
&nbsp;&nbsp;&nbsp;&nbsp;<code>cd "Society management"</code><br/><br/>
<b>2. Configure Isolated Python Virtual Environment:</b><br/>
Initialize a clean Python 3 virtual environment to isolate third-party dependencies:<br/>
&nbsp;&nbsp;&nbsp;&nbsp;<code>python3 -m venv venv</code><br/>
&nbsp;&nbsp;&nbsp;&nbsp;<code>source venv/bin/activate&nbsp;&nbsp;&nbsp;&nbsp;# On Windows: venv\Scripts\activate</code><br/><br/>
<b>3. Install Required Runtime Dependencies:</b><br/>
Install the specified WSGI framework, security libraries, and reporting packages:<br/>
&nbsp;&nbsp;&nbsp;&nbsp;<code>pip install -r requirements.txt</code><br/><br/>
<b>4. Initialize the Relational Database &amp; Seed Data:</b><br/>
Execute the automated database initializer to create normalized tables and seed test accounts:<br/>
&nbsp;&nbsp;&nbsp;&nbsp;<code>python3 init_db.py</code><br/>
<i>This establishes the SQLite database at <code>database/society.db</code> with 9 relational tables.</i><br/><br/>
<b>5. Launch the Local WSGI Application Server:</b><br/>
Start the local Flask development server:<br/>
&nbsp;&nbsp;&nbsp;&nbsp;<code>python3 app.py</code><br/>
The terminal outputs: <code>Starting server on http://127.0.0.1:5001</code>.<br/><br/>
<b>6. Access the Application in a Web Browser:</b><br/>
Open Google Chrome, Mozilla Firefox, or Safari and navigate to <code>http://127.0.0.1:5001/login</code>.<br/>
Use the pre-configured credentials or the 1-click Quick Login buttons:<br/>
• <b>Administrator:</b> username: <code>admin</code> &nbsp;|&nbsp; password: <code>admin123</code><br/>
• <b>Resident:</b> username: <code>resident</code> &nbsp;|&nbsp; password: <code>resident123</code><br/>
• <b>Security Guard:</b> username: <code>security</code> &nbsp;|&nbsp; password: <code>security123</code>"""
    story.append(Paragraph(p_setup, s['body']))


def build_pdf():
    pdf_filename = "Society_Management_System_Project_Report.pdf"
    print(f"Building {pdf_filename}...")
    doc = SimpleDocTemplate(
        pdf_filename,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN
    )

    s = get_styles()
    story = []

    print("Adding Preliminary Pages (1-10)...")
    add_preliminary_pages(story, s)

    print("Adding Chapters 1, 2, 3 (11-22)...")
    add_chapters1_2_3(story, s)

    print("Adding Chapters 4, 5, 6 (23-35)...")
    add_chapters4_5_6(story, s)

    print("Adding User Documentation Screenshots (36-58)...")
    add_user_documentation_pages(story, s)

    print("Adding Conclusions & Appendices (59-77)...")
    add_conclusions_and_appendices(story, s)

    print(f"Compiling document story with {len(story)} flowables...")
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Build complete: {pdf_filename}")

    # Verify page count
    d = fitz.open(pdf_filename)
    print(f"VERIFIED TOTAL PAGE COUNT: {len(d)}")
    if len(d) == 77:
        print("PERFECT MATCH: Exactly 77 pages generated!")
    else:
        print(f"WARNING: Expected 77 pages, but got {len(d)} pages.")

if __name__ == '__main__':
    build_pdf()

# controllers/main.py
from odoo import http
from odoo.http import request
import io
import xlsxwriter
from datetime import datetime
from io import BytesIO
from collections import defaultdict
import base64
class PatientExcelReport(http.Controller):

    @http.route('/web/binary/download_patient_excel', type='http', auth="user")
    def download_excel(self, from_date=None, to_date=None, **kwargs):
        from_dt = datetime.strptime(from_date, '%Y-%m-%d').date()
        to_dt = datetime.strptime(to_date, '%Y-%m-%d').date()
        records = request.env['patient.reg'].search([('date', '>=', from_dt), ('date', '<=', to_dt)])

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        sheet = workbook.add_worksheet("Patient Report")
        bold = workbook.add_format({'bold': True})

        headers = ['UHID', 'Name', 'Age', 'Address', 'Phone', 'Doctor Name']
        for col, header in enumerate(headers):
            sheet.write(0, col, header, bold)

        # Prepare to calculate max content length for each column
        max_lengths = [len(header) for header in headers]  # Start with header lengths

        # Iterate through records to calculate the maximum length of content for each column
        for rec in records:
            row_data = [
                str(rec.reference_no),
                str(rec.patient_id),
                str(rec.age),
                str(rec.address),
                str(rec.phone_number),
                str(rec.doc_name.name)
            ]
            for col, value in enumerate(row_data):
                max_lengths[col] = max(max_lengths[col], len(value))

        # Set column widths based on the max lengths (add a buffer for readability)
        for col, max_len in enumerate(max_lengths):
            sheet.set_column(col, col, max_len + 2)  # Add a small buffer to the content length

        # Write data to the sheet
        for row, rec in enumerate(records, start=1):
            sheet.write(row, 0, rec.reference_no)
            sheet.write(row, 1, rec.patient_id)
            sheet.write(row, 2, str(rec.age))
            sheet.write(row, 3, str(rec.address))
            sheet.write(row, 4, rec.phone_number)
            sheet.write(row, 5, rec.doc_name.name)

        workbook.close()
        output.seek(0)
        response = request.make_response(output.read(),
            headers=[('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                     ('Content-Disposition', 'attachment; filename="patient_report.xlsx"')],
            cookies={'fileToken': '123'})
        return response
class GeneralBillingExcelDownload(http.Controller):

    @http.route('/general_billing_excel/download', type='http', auth="user")
    def download_excel(self, date_from=None, date_to=None, **kwargs):
        # Parse the full datetime and convert to date
        df = datetime.strptime(date_from, '%Y-%m-%d %H:%M:%S').date()
        dt = datetime.strptime(date_to, '%Y-%m-%d %H:%M:%S').date()

        # Search billing records
        domain = [('bill_date', '>=', df), ('bill_date', '<=', dt)]
        records = request.env['general.billing'].sudo().search(domain)

        # Create Excel file in memory
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('General Billing Report')

        # Set styles
        bold = workbook.add_format({'bold': True})

        # Header labels
        headers = [
            'SL No', 'Bill No', 'Bill Date', 'Type', 'Department',
            'Category', 'MRD No', 'Patient Name', 'Gender', 'Doctor', 'Amount'
        ]

        # Track max width for each column
        max_col_widths = defaultdict(int)

        # Write header row
        for col, header in enumerate(headers):
            sheet.write(0, col, header, bold)
            max_col_widths[col] = len(header)

        # Write data rows and update max column widths
        for row_num, rec in enumerate(records, start=1):
            row_data = [
                str(row_num),
                rec.bill_number or '',
                rec.bill_date.strftime('%d/%m/%Y %H:%M') if rec.bill_date else '',
                rec.bill_type.display_name if rec.bill_type else '',
                rec.department.display_name if hasattr(rec.department, 'display_name') else str(rec.department or ''),
                rec.op_category.display_name if hasattr(rec.op_category, 'display_name') else str(rec.op_category or ''),
                rec.mrd_no.display_name if hasattr(rec.mrd_no, 'display_name') else str(rec.mrd_no or ''),
                rec.patient_name or '',
                dict(rec._fields['gender'].selection).get(rec.gender, ''),
                rec.doctor.display_name if rec.doctor else '',
                str(rec.total_amount or '')
            ]

            for col, value in enumerate(row_data):
                sheet.write(row_num, col, value)
                max_col_widths[col] = max(max_col_widths[col], len(str(value)))

        # Adjust column widths based on max content width + padding
        for col, width in max_col_widths.items():
            sheet.set_column(col, col, width + 2)

        # Finalize workbook
        workbook.close()
        output.seek(0)

        # Filename
        filename = f"General_Billing_{df.strftime('%d%m%Y')}_{dt.strftime('%d%m%Y')}.xlsx"
        headers = [
            ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
            ('Content-Disposition', f'attachment; filename={filename}'),
        ]
        return request.make_response(output.read(), headers)


class DoctorLabReportController(http.Controller):

    @http.route(['/doctor_lab_report/download_excel'], type='http', auth="user")
    def download_excel(self, **kw):
        from_date = kw.get('from_date')
        to_date = kw.get('to_date')

        # Get the filtered data
        lab_reports = request.env['doctor.lab.report'].sudo().search([
            ('date', '>=', from_date),
            ('date', '<=', to_date)
        ])

        # Create an in-memory output file
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Lab Reports')

        # Define the headers
        headers = ['SL No', 'Patient Name', 'MRD/OP No', 'Total Bill Amount']
        for col_num, header in enumerate(headers):
            worksheet.write(0, col_num, header)

        # Fill the sheet with data
        row = 1
        sl_no = 1
        for report in lab_reports:
            worksheet.write(row, 0, sl_no)  # Serial number
            worksheet.write(row, 1, report.patient_name or '')
            worksheet.write(row, 2, report.user_ide.display_name or '')
            worksheet.write(row, 3, report.total_bill_amount or 0.0)
            row += 1
            sl_no += 1

        workbook.close()
        output.seek(0)

        # Return as download
        return request.make_response(
            output.read(),
            headers=[
                ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                ('Content-Disposition', 'attachment; filename=doctor_lab_report.xlsx')
            ]
        )


class PharmacyDescriptionReportController(http.Controller):

    @http.route(['/pharmacy_description/download_excel'], type='http', auth="user")
    def download_excel(self, **kw):
        from_date = kw.get('from_date')
        to_date = kw.get('to_date')

        pharmacy_records = request.env['pharmacy.description'].sudo().search([
            ('date', '>=', from_date),
            ('date', '<=', to_date)
        ], order='date asc')  # You can change to desc if needed

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Pharmacy Report')

        headers = ['SL No', 'Receipt No', 'Date & Time', 'Name', 'Bill No', 'Payable Amount', 'Paying Amount', 'Balance Amount']
        for col_num, header in enumerate(headers):
            worksheet.write(0, col_num, header)

        row = 1
        sl_no = 1
        for record in pharmacy_records:
            worksheet.write(row, 0, sl_no)
            worksheet.write(row, 1, record.id)  # Assuming Receipt No is ID
            worksheet.write(row, 2, record.date.strftime('%Y-%m-%d %H:%M:%S') if record.date else '')
            worksheet.write(row, 3, record.name or '')
            worksheet.write(row, 4, record.id)  # Assuming Bill No is same as Receipt No (else adjust)
            worksheet.write(row, 5, record.bill_amount or 0.0)
            worksheet.write(row, 6, record.paid_amount or 0)
            worksheet.write(row, 7, record.balance or 0)
            row += 1
            sl_no += 1

        workbook.close()
        output.seek(0)

        return request.make_response(
            output.read(),
            headers=[
                ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                ('Content-Disposition', 'attachment; filename=pharmacy_description_report.xlsx')
            ]
        )



class VendorBillExcelController(http.Controller):

    @http.route('/vendor/bill/excel', type='http', auth='user')
    def download_excel_report(self, from_date, to_date, **kwargs):
        user = request.env.user
        ReportWizard = request.env['in.invoice.report.wizard'].sudo()

        # Parse the dates
        from_dt = datetime.strptime(from_date, "%Y-%m-%d")
        to_dt = datetime.strptime(to_date, "%Y-%m-%d")

        # Search the bills
        records = request.env['account.move'].sudo().search([
            ('move_type', '=', 'in_invoice'),
            ('invoice_date', '>=', from_dt),
            ('invoice_date', '<=', to_dt),
        ])

        # Create Excel file in memory
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet("Vendor Bills")

        header_format = workbook.add_format({'bold': True, 'bg_color': '#D7E4BC'})

        headers = [
            'Supplier Name', 'Invoice No', 'Phone No', 'Email Id',
            'GST No', 'DL/REG No', 'Bill Date', 'PO Number'
        ]
        for col_num, header in enumerate(headers):
            worksheet.write(0, col_num, header, header_format)

        row = 1
        for rec in records:
            worksheet.write(row, 0, rec.supplier_name.name if rec.supplier_name else '')
            worksheet.write(row, 1, rec.supplier_invoice or '')
            worksheet.write(row, 2, rec.supplier_phone or '')
            worksheet.write(row, 3, rec.supplier_email or '')
            worksheet.write(row, 4, rec.supplier_gst or '')
            worksheet.write(row, 5, rec.supplier_dl or '')
            worksheet.write(row, 6, rec.supplier_bill_date.strftime('%d-%m-%Y') if rec.supplier_bill_date else '')
            worksheet.write(row, 7, rec.po_number.name if rec.po_number else '')
            row += 1

        workbook.close()
        output.seek(0)
        file_data = output.read()
        output.close()

        filename = "Vendor_Bill_Report.xlsx"
        return request.make_response(
            file_data,
            headers=[
                ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                ('Content-Disposition', f'attachment; filename="{filename}"')
            ]
        )
class PatientAdmissionReportController(http.Controller):

    @http.route('/export_patient_admission_report', type='http', auth='user', website=True)
    def export_patient_admission_report(self, date_from, date_to, **kwargs):
        # Get the patient records within the date range
        patient_records = request.env['patient.reg'].search([
            ('admitted_date', '>=', date_from),
            ('admitted_date', '<=', date_to),
            ('status', '=', 'admitted')
        ])

        # Prepare data for the Excel report
        report_data = []
        for patient in patient_records:
            report_data.append({
                'patient_name': patient.patient_id,
                'admitted_date': patient.admitted_date,
                'room': patient.room_number_new.room_number if patient.room_number_new else '',
                'total_amount': patient.admission_total_amount,
                'uhid': patient.reference_no,
            })

        # Generate the Excel file
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('Patient Admission Report')

        # Set column widths
        worksheet.set_column('A:A', 20)
        worksheet.set_column('B:B', 30)
        worksheet.set_column('C:C', 20)
        worksheet.set_column('D:D', 15)
        worksheet.set_column('E:E', 20)

        # Write the headers
        worksheet.write('A1', 'UHID')
        worksheet.write('B1', 'Patient Name')
        worksheet.write('C1', 'Admission Date')
        worksheet.write('D1', 'Room')
        worksheet.write('E1', 'Total Bill Amount')

        # Write the data
        row = 1
        for line in report_data:
            worksheet.write(row, 0, line['uhid'])
            worksheet.write(row, 1, line['patient_name'])
            worksheet.write(row, 2, str(line['admitted_date']))
            worksheet.write(row, 3, line['room'])
            worksheet.write(row, 4, line['total_amount'])
            row += 1
    
        workbook.close()

        # Get the Excel file from memory
        output.seek(0)
        file_data = output.read()

        # Base64 encode the file content for attachment
        encoded_file_data = base64.b64encode(file_data)

        # Create an attachment (Base64 encoded)
        attachment = request.env['ir.attachment'].create({
            'name': 'Patient_Admission_Report.xlsx',
            'type': 'binary',
            'datas': encoded_file_data,  # Store the Base64 encoded file content
            'store_fname': 'Patient_Admission_Report.xlsx',
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })

        # Return the file as a downloadable link
        return request.make_response(
            file_data,
            headers=[
                ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                ('Content-Disposition', 'attachment; filename="Patient_Admission_Report.xlsx"')
            ]
        )

# class AuthLogin(http.Controller):
#     @http.route('/web/login', type='http', auth="public", website=True)
#     def web_login(self, redirect=None, **kw):
#         recaptcha_response = kw.get('g-recaptcha-response')
#         secret_key = ""
#
#         # Verify reCAPTCHA
#         response = requests.post(
#             'https://www.google.com/recaptcha/api/siteverify',
#             data={'secret': secret_key, 'response': recaptcha_response}
#         ).json()
#
#         if not response.get("success"):
#             return request.render('web.login', {'error': 'Invalid reCAPTCHA. Try again.'})
#
#         return http.redirect_with_hash('/web')
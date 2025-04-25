# controllers/main.py
from odoo import http
from odoo.http import request
import io
import xlsxwriter
from datetime import datetime
from io import BytesIO

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
        # Parse the dates
        df = datetime.strptime(date_from, "%Y-%m-%d %H:%M:%S")
        dt = datetime.strptime(date_to, "%Y-%m-%d %H:%M:%S")

        # Search billing records
        domain = [('bill_date', '>=', df), ('bill_date', '<=', dt)]
        records = request.env['general.billing'].sudo().search(domain)

        # Create Excel file in memory
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('General Billing Report')

        bold = workbook.add_format({'bold': True})
        headers = ['SL No', 'Bill No', 'Bill Date', 'Type', 'Department', 'Category', 'MRD No', 'Patient Name', 'Gender', 'Doctor']

        for col, header in enumerate(headers):
            sheet.write(0, col, header, bold)

        for row_num, rec in enumerate(records, start=1):
            sheet.write(row_num, 0, row_num)
            sheet.write(row_num, 1, rec.bill_number)
            sheet.write(row_num, 2, rec.bill_date.strftime('%d/%m/%Y %H:%M') if rec.bill_date else '')
            sheet.write(row_num, 3, rec.bill_type.name if rec.bill_type else '')
            sheet.write(row_num, 4, rec.department.name if rec.department else '')
            sheet.write(row_num, 5, rec.op_category.name if rec.op_category else '')
            sheet.write(row_num, 6, rec.mrd_no.name if rec.mrd_no else '')
            sheet.write(row_num, 7, rec.patient_name)
            sheet.write(row_num, 8, dict(rec._fields['gender'].selection).get(rec.gender, ''))
            sheet.write(row_num, 9, rec.doctor.name if rec.doctor else '')

        workbook.close()
        output.seek(0)

        filename = f"General_Billing_{df.strftime('%d%m%Y')}_{dt.strftime('%d%m%Y')}.xlsx"
        headers = [
            ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
            ('Content-Disposition', f'attachment; filename={filename}'),
        ]
        return request.make_response(output.read(), headers)

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
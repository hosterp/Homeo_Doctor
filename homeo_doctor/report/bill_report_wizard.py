from odoo import api, fields, models, _
import io
import base64
import xlsxwriter


class BillingReportWizard(models.TransientModel):
    _name = 'ip.billing.report.wizard'
    _description = 'Billing Report Wizard'

    from_date = fields.Date(string="From Date", required=True)
    to_date = fields.Date(string="To Date", required=True)
    bill_type = fields.Selection([
        ('ip_part', 'IP Part Bill'),
        ('discharge', 'Discharge Bill')
    ], string='Bill Type', )

    # Show filtered records in tree/form
    def action_get_records(self):
        model_name = 'ip.part.billing' if self.bill_type == 'ip_part' else 'discharged.patient.record'
        date_field = 'bill_date' if self.bill_type == 'ip_part' else 'discharge_date'

        records = self.env[model_name].search([
            (date_field, '>=', self.from_date),
            (date_field, '<=', self.to_date)
        ])

        return {
            'type': 'ir.actions.act_window',
            'name': 'Filtered Bills',
            'view_mode': 'tree,form',
            'res_model': model_name,
            'domain': [('id', 'in', records.ids)],
            'target': 'current'
        }

    # PDF report
    def action_print_report(self):
        if self.bill_type == 'ip_part':
            model_name = 'ip.part.billing'
            report_ref = 'homeo_doctor.action_report_ip_billing'
            date_field = 'bill_date'
        else:
            model_name = 'discharged.patient.record'
            report_ref = 'homeo_doctor.action_report_discharge_billing'
            date_field = 'discharge_date'

        # Pass bill type and date info to the report
        return self.env.ref(report_ref).report_action(
            [],
            data={
                'from_date': str(self.from_date),
                'to_date': str(self.to_date),
                'bill_type': self.bill_type,
                'model_name': model_name,
                'date_field': date_field
            }
        )

    # Excel export
    def action_print_excel(self):
        model_name = 'ip.part.billing' if self.bill_type == 'ip_part' else 'discharged.patient.record'
        date_field = 'bill_date' if self.bill_type == 'ip_part' else 'discharge_date'

        records = self.env[model_name].search([
            (date_field, '>=', self.from_date),
            (date_field, '<=', self.to_date)
        ])

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet("Report")

        # === FORMATS ===
        title_format = workbook.add_format({
            'align': 'center', 'valign': 'vcenter',
            'bold': True, 'font_size': 20, 'font_color': '#2c3e50'
        })
        subtitle_format = workbook.add_format({
            'align': 'center', 'valign': 'vcenter',
            'font_size': 12, 'font_color': '#555555'
        })
        header_format = workbook.add_format({
            'align': 'center', 'valign': 'vcenter',
            'bold': True, 'bg_color': '#D9D9D9', 'border': 1
        })
        total_format = workbook.add_format({
            'align': 'right', 'bold': True, 'border': 1
        })

        # === HOSPITAL HEADER ===
        sheet.merge_range('A1:D1', "Dr. PRIYA'S MULTI SPECIALITY HOSPITAL", title_format)
        sheet.merge_range('A2:D2', "EANIKKARA, KARAKULAM PO, THIRUVANANTHAPURAM - 695 564", subtitle_format)
        sheet.merge_range('A3:D3', "Phone: 0471-2373004, Mobile: 8590203321, dpmshospital@gmail.com", subtitle_format)

        # Report title
        sheet.merge_range('A4:D4', "IP Part Billing Report", header_format)

        # Date Range (row 5)
        sheet.merge_range('A5:D5', f"From: {self.from_date}   To: {self.to_date}", subtitle_format)

        # === TABLE HEADERS ===
        headers = ['Bill No', 'Patient', 'Date', 'Amount']
        row_offset = 6  # table starts after header (row 7)
        for col, header in enumerate(headers):
            sheet.write(row_offset, col, header, header_format)

        # === WRITE DATA ===
        total_amount = 0
        for row, rec in enumerate(records, start=row_offset + 1):
            if self.bill_type == 'ip_part':
                sheet.write(row, 0, rec.bill_number or rec.id)
                sheet.write(row, 1, rec.patient_name)
                sheet.write(row, 2, str(rec.bill_date))
                sheet.write(row, 3, rec.net_amount or 0)
                total_amount += rec.net_amount or 0
            else:
                sheet.write(row, 0, rec.patient_id or rec.id)
                sheet.write(row, 1, rec.name)
                sheet.write(row, 2, str(rec.discharge_date))
                sheet.write(row, 3, rec.total_amount or 0)
                total_amount += rec.total_amount or 0

        # === TOTAL ROW ===
        total_row = row + 2
        sheet.write(total_row, 2, "Total", total_format)
        sheet.write(total_row, 3, total_amount, total_format)

        # Auto column width
        sheet.set_column('A:D', 20)

        workbook.close()
        output.seek(0)

        # Create attachment
        attachment = self.env['ir.attachment'].create({
            'name': f'Billing_Report_{self.from_date}_to_{self.to_date}.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(output.read()),
            'res_model': 'ip.billing.report.wizard',
            'res_id': self.id,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }

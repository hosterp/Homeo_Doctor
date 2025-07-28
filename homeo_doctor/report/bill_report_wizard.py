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
    ], string='Bill Type', required=True)

    def action_get_records(self):
        if self.bill_type == 'ip_part':
            records = self.env['ip.part.billing'].search([
                ('bill_date', '>=', self.from_date),
                ('bill_date', '<=', self.to_date)
            ])
        else:
            records = self.env['discharged.patient.record'].search([
                ('discharge_date', '>=', self.from_date),
                ('discharge_date', '<=', self.to_date)
            ])

        return {
            'type': 'ir.actions.act_window',
            'name': 'Filtered Bills',
            'view_mode': 'tree,form',
            'res_model': 'ip.part.billing' if self.bill_type == 'ip_part' else 'discharged.patient.record',
            'domain': [('id', 'in', records.ids)],
            'target': 'current'
        }

    def action_print_report(self):
        model_name = 'ip.part.billing' if self.bill_type == 'ip_part' else 'discharged.patient.record'
        date_field = 'bill_date' if self.bill_type == 'ip_part' else 'discharge_date'
        domain = [(date_field, '>=', self.from_date), (date_field, '<=', self.to_date)]
        records = self.env[model_name].search(domain)

        return {
            'type': 'ir.actions.report',
            'report_name': 'homeo_doctor.report_billing_pdf',
            'report_type': 'qweb-pdf',
            'data': {
                'from_date': str(self.from_date),
                'to_date': str(self.to_date),
                'bill_type': self.bill_type,
                'model_name': model_name,
                'record_ids': records.ids,
            }
        }

    def action_print_excel(self):
        model_name = 'ip.part.billing' if self.bill_type == 'ip_part' else 'discharged.patient.record'
        date_field = 'bill_date' if self.bill_type == 'ip_part' else 'discharge_date'
        domain = [(date_field, '>=', self.from_date), (date_field, '<=', self.to_date)]
        records = self.env[model_name].search(domain)

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet("Report")

        headers = ['Bill No', 'Patient', 'Date', 'Amount']
        for col, header in enumerate(headers):
            sheet.write(0, col, header)

        for row, rec in enumerate(records, start=1):
            if self.bill_type == 'ip_part':
                sheet.write(row, 0, rec.bill_number or rec.id)
                sheet.write(row, 1, rec.patient_name)
                sheet.write(row, 2, str(rec.bill_date))
                sheet.write(row, 3, rec.net_amount or 0)
            else:
                sheet.write(row, 0, rec.patient_id or rec.id)
                sheet.write(row, 1, rec.name)
                sheet.write(row, 2, str(rec.discharge_date))
                sheet.write(row, 3, rec.total_amount or 0)

        workbook.close()
        output.seek(0)

        # Store as attachment
        attachment = self.env['ir.attachment'].create({
            'name': 'Billing_Report.xlsx',
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




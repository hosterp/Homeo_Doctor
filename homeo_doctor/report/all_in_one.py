from odoo import models, fields, api


class CombinedReportWizard(models.TransientModel):
    _name = 'combined.report.wizard'
    _description = 'Combined Report Wizard'

    from_date = fields.Date(string='From Date', required=True, default=fields.Date.today)
    to_date = fields.Date(string='To Date', required=True, default=fields.Date.today)
    mode_pay = fields.Selection([
        ('cash', 'Cash'),
        ('credit', 'Credit'),
        ('card', 'Card'),
        ('cheque', 'Cheque'),
        ('upi', 'UPI')
    ], string='Payment Method')

    def action_generate_combined_pdf(self):
        payment_methods = [
            ('cash', 'Cash'),
            ('credit', 'Credit'),
            ('card', 'Card'),
            ('cheque', 'Cheque'),
            ('upi', 'UPI')
        ]

        department_totals = {}

        for code, label in payment_methods:
            billing = self.env['general.billing'].search([
                ('bill_date', '>=', self.from_date),
                ('bill_date', '<=', self.to_date),
                ('mode_pay', '=', code),
            ])

            lab_domain = [
                ('date', '>=', self.from_date),
                ('date', '<=', self.to_date),
                ('mode_of_payment', '=', code),
            ]

            if code == 'credit':
                lab_domain.append('|')
                lab_domain.append(('status', '=', 'unpaid'))
                lab_domain.append('&')
                lab_domain.append(('status', '=', 'paid'))
                lab_domain.append(('vssc_check', '=', True))

            else:
                lab_domain.append(('status', '=', 'paid'))

            lab = self.env['doctor.lab.report'].search(lab_domain)

            pharmacy_records = self.env['pharmacy.description'].search([
                ('date', '>=', self.from_date),
                ('date', '<=', self.to_date),
                ('payment_mathod', '=', code),
            ])
            pharmacy_return = self.env['pharmacy.return'].search([
                    ('return_date', '>=', self.from_date),
                    ('return_date', '<=', self.to_date),
                ], order='return_date asc')
            patients = self.env['patient.reg'].search([
                ('date', '>=', self.from_date),
                ('date', '<=', self.to_date),
                ('register_mode_payment', '=', code),
                ('register_bool', '=', True),
            ])
            patient_records = self.env['discharged.patient.record'].search([
                ('admitted_date', '>=', self.from_date),
                ('admitted_date', '<=', self.to_date),
                ('pay_mode', '=', code),
            ])
            patient_recept = self.env['patient.reg'].search([
                ('admitted_date', '>=', self.from_date),
                ('admitted_date', '<=', self.to_date),
                ('advance_mode_payment', '=', code),
            ])

            for rec in patients:
                dept = 'OP'
                department_totals.setdefault(dept, {m[0]: 0.0 for m in payment_methods})
                department_totals[dept][code] += rec.register_total_amount or 0.0
            for rec in patient_records:
                dept = 'IP'
                department_totals.setdefault(dept, {m[0]: 0.0 for m in payment_methods})
                department_totals[dept][code] += rec.total_amount or 0.0
            for rec in patient_recept:
                dept = 'IP Recept'
                department_totals.setdefault(dept, {m[0]: 0.0 for m in payment_methods})
                department_totals[dept][code] += rec.amount_in_advance or 0.0
            for rec in pharmacy_return:
                dept = 'Pharmacy Return'
                department_totals.setdefault(dept, {m[0]: 0.0 for m in payment_methods})
                department_totals[dept]['cash'] += rec.total_return_amount or 0.0
            for rec in billing:
                dept = 'General Billing'
                department_totals.setdefault(dept, {m[0]: 0.0 for m in payment_methods})
                department_totals[dept][code] += rec.total_amount or 0.0

            for rec in lab:
                dept = 'Lab Billing'
                department_totals.setdefault(dept, {m[0]: 0.0 for m in payment_methods})
                department_totals[dept][code] += rec.total_bill_amount or 0.0

            for rec in pharmacy_records:
                dept = 'Pharmacy Sales'
                department_totals.setdefault(dept, {m[0]: 0.0 for m in payment_methods})
                department_totals[dept][code] += rec.total_amount or 0.0

        data = {
            'from_date': self.from_date.strftime('%d-%m-%Y'),
            'to_date': self.to_date.strftime('%d-%m-%Y'),
            'departments': department_totals,
            'payment_labels': [label for code, label in payment_methods],
            'payment_codes': [code for code, label in payment_methods],
        }

        return self.env.ref('homeo_doctor.combined_report_action').report_action(self, data={'data': data})

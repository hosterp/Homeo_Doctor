from datetime import datetime, timedelta, time

import pytz
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
        user_tz = self.env.user.tz or 'UTC'
        tz = pytz.timezone(user_tz)

        # Local start/end (user timezone)
        start_local = tz.localize(datetime.combine(self.from_date, time.min))  # 00:00:00 local
        end_local = tz.localize(datetime.combine(self.to_date, time.max))  # 23:59:59.999999 local

        # Convert to UTC for DB comparison
        start_utc = start_local.astimezone(pytz.UTC)
        end_utc = end_local.astimezone(pytz.UTC)

        payment_methods = [
            ('cash', 'Cash'),
            ('credit', 'Credit'),
            ('card', 'Card'),
            ('cheque', 'Cheque'),
            ('upi', 'UPI')
        ]

        department_totals = {}

        def add_amount(dept, pay_code, amount):
            department_totals.setdefault(dept, {m[0]: 0.0 for m in payment_methods})
            if pay_code not in dict(payment_methods):
                pay_code = 'cash'
            department_totals[dept][pay_code] += amount or 0.0

        for code, label in payment_methods:
            # General Billing
            billing = self.env['general.billing'].search([
                ('bill_date', '>=', start_utc),
                ('bill_date', '<=', end_utc),
                ('mode_pay', '=', code),
            ])

            # Lab Reports
            lab_domain = [
                ('date', '>=', start_utc),
                ('date', '<=', end_utc),
                ('mode_of_payment', '=', code),
            ]
            if code == 'credit':
                lab_domain = ['|', ('status', '=', 'unpaid'), '&', ('status', '=', 'paid'),
                              ('vssc_check', '=', True)] + lab_domain
            else:
                lab_domain.append(('status', '=', 'paid'))
            lab = self.env['doctor.lab.report'].search(lab_domain)

            # Pharmacy Records
            pharmacy_records = self.env['pharmacy.description'].search([
                ('date', '>=', start_utc),
                ('date', '<=', end_utc),
                ('payment_mathod', '=', code),
            ])

            # Patients OP
            patients = self.env['patient.reg'].search([
                ('time', '>=', start_utc),
                ('time', '<=', end_utc),
                ('register_mode_payment', '=', code),
                ('register_bool', '=', True),
            ])

            # Revisit Patients
            revisit = self.env['patient.appointment'].search([
                ('appointment_date', '>=', start_utc),
                ('appointment_date', '<=', end_utc),
                ('register_mode_payment', '=', code),
                ('status', '=', 'confirmed'),
            ])

            # Discharged Patients
            patient_record = self.env['discharged.patient.record'].search([
                ('discharge_date', '>=', start_utc),
                ('discharge_date', '<=', end_utc),
                ('pay_mode', '=', code),
            ])

            # Advance Amount Records
            patient_recept = self.env['advance.patient.record'].search([
                ('admitted_date', '>=', start_utc),
                ('admitted_date', '<=', end_utc),
                ('pay_mode', '=', code),
            ])

            # IP Billing
            ip_part = self.env['ip.part.billing'].search([
                ('bill_date', '>=', start_utc),
                ('bill_date', '<=', end_utc),
                ('mode_pay', '=', code),
            ])

            # Accumulate totals for this payment code
            for rec in patients:
                add_amount('OP', code, rec.register_total_amount)
            for rec in revisit:
                add_amount('Revisit', code, rec.register_total_amount)
            for rec in patient_record:
                add_amount('Discharge', code, rec.total_amount)
            for rec in ip_part:
                add_amount('IP', code, rec.total_amount)
            for rec in patient_recept:
                add_amount('Advance amt', code, rec.amount_in_advance)
            for rec in billing:
                add_amount('General Billing', code, rec.total_amount)
            for rec in lab:
                add_amount('Lab Billing', code, rec.total_bill_amount)
            for rec in pharmacy_records:
                add_amount('Pharmacy Sales', code, rec.total_amount)

        # Pharmacy Returns (outside loop) — also convert domain to UTC
        pharmacy_return = self.env['pharmacy.return'].search([
            ('return_date', '>=', start_utc),
            ('return_date', '<=', end_utc),
        ], order='return_date asc')

        for rec in pharmacy_return:
            dept = 'Pharmacy Return'
            department_totals.setdefault(dept, {m[0]: 0.0 for m in payment_methods})
            if rec.original_sale_id and rec.original_sale_id.payment_mathod:
                pm = rec.original_sale_id.payment_mathod
                if pm not in dict(payment_methods):
                    pm = 'cash'
                department_totals[dept][pm] -= rec.total_return_amount or 0.0
            else:
                department_totals[dept]['cash'] -= rec.total_return_amount or 0.0

        data = {
            'from_date': self.from_date.strftime('%d-%m-%Y'),
            'to_date': self.to_date.strftime('%d-%m-%Y'),
            'departments': department_totals,
            'payment_labels': [label for code, label in payment_methods],
            'payment_codes': [code for code, label in payment_methods],
        }

        return self.env.ref('homeo_doctor.combined_report_action').report_action(self, data={'data': data})

    # def action_generate_combined_pdf(self):
    #     payment_methods = [
    #         ('cash', 'Cash'),
    #         ('credit', 'Credit'),
    #         ('card', 'Card'),
    #         ('cheque', 'Cheque'),
    #         ('upi', 'UPI')
    #     ]
    #
    #     department_totals = {}
    #
    #     # Process records that depend on payment method
    #     for code, label in payment_methods:
    #         billing = self.env['general.billing'].search([
    #             ('bill_date', '>=', self.from_date),
    #             ('bill_date', '<=', self.to_date),
    #             ('mode_pay', '=', code),
    #         ])
    #
    #         lab_domain = [
    #             ('date', '>=', self.from_date),
    #             ('date', '<=', self.to_date),
    #             ('mode_of_payment', '=', code),
    #         ]
    #
    #         if code == 'credit':
    #             lab_domain.append('|')
    #             lab_domain.append(('status', '=', 'unpaid'))
    #             lab_domain.append('&')
    #             lab_domain.append(('status', '=', 'paid'))
    #             lab_domain.append(('vssc_check', '=', True))
    #         else:
    #             lab_domain.append(('status', '=', 'paid'))
    #
    #         lab = self.env['doctor.lab.report'].search(lab_domain)
    #
    #         pharmacy_records = self.env['pharmacy.description'].search([
    #             ('date', '>=', self.from_date),
    #             ('date', '<=', self.to_date),
    #             ('payment_mathod', '=', code),
    #         ])
    #
    #         patients = self.env['patient.reg'].search([
    #             ('time', '>=', self.from_date),
    #             ('time', '<=', self.to_date),
    #             ('register_mode_payment', '=', code),
    #             ('register_bool', '=', True),
    #         ])
    #         revisit = self.env['patient.appointment'].search([
    #             ('appointment_date', '>=', self.from_date),
    #             ('appointment_date', '<=', self.to_date),
    #             ('register_mode_payment', '=', code),
    #             ('status', '=', 'confirmed'),
    #         ])
    #
    #         patient_records = self.env['discharged.patient.record'].search([
    #             ('discharge_date', '>=', self.from_date),
    #             ('discharge_date', '<=', self.to_date),
    #             ('pay_mode', '=', code),
    #         ])
    #
    #         patient_recept = self.env['advance.patient.record'].search([
    #             ('admitted_date', '>=', self.from_date),
    #             ('admitted_date', '<=', self.to_date),
    #             ('pay_mode', '=', code),
    #         ])
    #
    #         # Process payment-method specific records
    #         for rec in patients:
    #             dept = 'OP'
    #             department_totals.setdefault(dept, {m[0]: 0.0 for m in payment_methods})
    #             department_totals[dept][code] += rec.register_total_amount or 0.0
    #         for rec in revisit:
    #             dept = 'Revisit'
    #             department_totals.setdefault(dept, {m[0]: 0.0 for m in payment_methods})
    #             department_totals[dept][code] += rec.register_total_amount or 0.0
    #
    #         for rec in patient_records:
    #             dept = 'IP'
    #             department_totals.setdefault(dept, {m[0]: 0.0 for m in payment_methods})
    #             department_totals[dept][code] += rec.total_amount or 0.0
    #
    #         for rec in patient_recept:
    #             dept = 'IP Recept'
    #             department_totals.setdefault(dept, {m[0]: 0.0 for m in payment_methods})
    #             department_totals[dept][code] += rec.amount_in_advance or 0.0
    #
    #         for rec in billing:
    #             dept = 'General Billing'
    #             department_totals.setdefault(dept, {m[0]: 0.0 for m in payment_methods})
    #             department_totals[dept][code] += rec.total_amount or 0.0
    #
    #         for rec in lab:
    #             dept = 'Lab Billing'
    #             department_totals.setdefault(dept, {m[0]: 0.0 for m in payment_methods})
    #             department_totals[dept][code] += rec.total_bill_amount or 0.0
    #
    #         for rec in pharmacy_records:
    #             dept = 'Pharmacy Sales'
    #             department_totals.setdefault(dept, {m[0]: 0.0 for m in payment_methods})
    #             department_totals[dept][code] += rec.total_amount or 0.0
    #
    #     # Process pharmacy returns OUTSIDE the payment methods loop (only once!)
    #     pharmacy_return = self.env['pharmacy.return'].search([
    #         ('return_date', '>=', self.from_date),
    #         ('return_date', '<=', self.to_date),
    #     ], order='return_date asc')
    #
    #     for rec in pharmacy_return:
    #         dept = 'Pharmacy Return'
    #         department_totals.setdefault(dept, {m[0]: 0.0 for m in payment_methods})
    #
    #         # Get original payment method from the original sale
    #         if rec.original_sale_id and rec.original_sale_id.payment_mathod:
    #             original_payment_method = rec.original_sale_id.payment_mathod
    #             # Subtract return amount (use negative value)
    #             department_totals[dept][original_payment_method] -= rec.total_return_amount or 0.0
    #         else:
    #             # Fallback to cash if original payment method is not found
    #             # Subtract return amount (use negative value)
    #             department_totals[dept]['cash'] -= rec.total_return_amount or 0.0
    #
    #     data = {
    #         'from_date': self.from_date.strftime('%d-%m-%Y'),
    #         'to_date': self.to_date.strftime('%d-%m-%Y'),
    #         'departments': department_totals,
    #         'payment_labels': [label for code, label in payment_methods],
    #         'payment_codes': [code for code, label in payment_methods],
    #     }
    #
    #     return self.env.ref('homeo_doctor.combined_report_action').report_action(self, data={'data': data})

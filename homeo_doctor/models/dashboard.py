from odoo import api, fields, models
from datetime import datetime, timedelta
import pytz


class DashboardModel(models.Model):
    _name = 'dashboard.model'

    name = fields.Char(string='dashboard')
    consultation_count = fields.Integer(compute='_compute_counts', store=False)
    sale_count = fields.Integer(compute='_compute_counts', store=False)
    discharge_count = fields.Integer(compute='_compute_counts', store=False)
    admit_count = fields.Integer(compute='_compute_counts', store=False)
    expired_count = fields.Integer(compute='_compute_counts', store=False)
    # collection_count = fields.Integer(compute='_compute_counts', store=False)
    purchase_count = fields.Integer(compute='_compute_counts', store=False)
    credit_bill=fields.Many2one('credit.billing.report')

    consultation_amount = fields.Float()


    sale_amount = fields.Float()


    discharge_amount = fields.Float()


    admit_amount = fields.Float()


    purchase_amount = fields.Float()
    lab_amount = fields.Float()
    revisit_amount = fields.Float()
    general_amount = fields.Float()
    ip_part_amount = fields.Float()
    credit_amount = fields.Float(
        string="Credit Total",
        compute='_compute_credit_amount',
        store=False,  # <-- never stored, recomputed per read
    )
    op_count = fields.Integer(string="OP Count")
    ip_bills = fields.Integer(string="IP Count")
    other_bills = fields.Integer(string="Others Count")

    @api.depends()
    def _compute_credit_amount(self):
        for rec in self:
            if rec.name == 'Today Credit Billing':
                reports = self.env['credit.billing.report'].search([])
                rec.credit_amount = sum(reports.mapped('amount'))
            else:
                rec.credit_amount = 0.0

    @api.depends('name','credit_bill.amount')
    def _compute_counts(self):
        user_tz = self.env.user.tz or 'UTC'
        now = fields.Datetime.now()
        today = now.astimezone(pytz.timezone(user_tz)).date()

        start_dt = datetime.combine(today, datetime.min.time())
        end_dt = datetime.combine(today, datetime.max.time())

        # Convert back to UTC for the domain
        start_dt = pytz.timezone(user_tz).localize(start_dt).astimezone(pytz.UTC)
        end_dt = pytz.timezone(user_tz).localize(end_dt).astimezone(pytz.UTC)

        for rec in self:
            # Reset counts and amounts
            rec.consultation_count = rec.sale_count = rec.discharge_count = 0
            rec.admit_count = rec.expired_count = rec.purchase_count = 0
            rec.consultation_amount = rec.sale_amount = rec.discharge_amount = 0.0
            rec.admit_amount = rec.purchase_amount = 0.0
            rec.lab_amount = rec.lab_amount = 0.0
            rec.revisit_amount = rec.revisit_amount = 0.0
            rec.general_amount = rec.general_amount = 0.0
            rec.ip_part_amount = rec.ip_part_amount = 0.0
            rec.credit_amount = rec.credit_amount = 0.0
            rec.op_count = rec.op_count = 0.0
            rec.ip_bills = rec.ip_bills = 0.0
            rec.other_bills = rec.other_bills = 0.0

            if rec.name == 'Today OP Details':
                consultations = self.env['patient.reg'].search([('time', '>=', start_dt),('time', '<=', end_dt),('status','!=','unpaid',),('register_mode_payment','!=','credit')])
                rec.consultation_count = len(consultations)
                rec.consultation_amount = sum(
                    consultations.mapped('register_total_amount'))

            elif rec.name == 'Today Pharmacy Billing Details':
                sales = self.env['pharmacy.prescription.line'].search([
                    ('pharmacy_id.date', '>=', start_dt),
                    ('pharmacy_id.date', '<', end_dt),
                    ('pharmacy_id.status', '=', 'paid'),
                ])
                rec.sale_count = len(sales)
                rec.sale_amount = sum(sales.mapped('rate'))

            elif rec.name == 'Discharged Patient Details':
                discharges = self.env['discharged.patient.record'].search([
                    ('discharge_date', '>=', start_dt),
                    ('discharge_date', '<', end_dt)
                ])
                rec.discharge_count = len(discharges)
                rec.discharge_amount = sum(
                    discharges.mapped('total_amount'))

            elif rec.name == 'Admitted Patient Details':
                admits = self.env['hospital.admitted.patient'].search([
                    ('admission_date', '>=', start_dt),
                    ('admission_date', '<', end_dt),
                    ('status', '=', 'admitted'),
                ])
                rec.admit_count = len(admits)
                # rec.admit_amount = sum(admits.mapped('amount_in_advance'))

            elif rec.name == 'Expired Medicines':
                rec.expired_count = self.env['stock.entry'].search_count([
                    ('exp_date', '<', today),
                    ('quantity', '>', 0),
                ])

            elif rec.name == 'Today Purchase Details':
                purchases = self.env['account.move'].search([
                    ('supplier_bill_date', '=', today),
                    ('state', '=', 'posted')
                ])
                rec.purchase_count = len(purchases)
                rec.purchase_amount = sum(purchases.mapped('amount_total'))
            elif rec.name == 'Today Lab Billing':
                lab = self.env['doctor.lab.report'].search([
                    ('date','>=', start_dt),
                    ('date', '<', end_dt),
                    ('status', '=', 'paid'),
                    ('mode_of_payment', '!=', 'credit'),
                ])

                rec.lab_amount = sum(lab.mapped('total_bill_amount'))
            elif rec.name == 'Today Revisit Details':
                revist = self.env['patient.appointment'].search([
                    ('appointment_date','>=', start_dt),
                    ('appointment_date','<', end_dt),
                    ('status', '=', 'confirmed'),
                    ('register_mode_payment', '!=', 'credit')
                ])

                rec.revisit_amount = sum(revist.mapped('register_total_amount'))
            elif rec.name == 'Today General Billing':
                general = self.env['general.billing'].search([
                    ('bill_date', '>=', start_dt),
                    ('bill_date', '<', end_dt),
                    ('status', '=', 'paid')
                ])

                rec.general_amount = sum(general.mapped('total_amount'))
                op_bills = general.filtered(lambda r: r.bill_type.bill_type == 'OP')
                ip_bills = general.filtered(lambda r: r.bill_type.bill_type == 'IP')
                other_bills = general.filtered(lambda r: r.bill_type.bill_type == 'Others')
                # print("OP Bills:", op_bills)
                rec.op_count = len(op_bills)
                rec.ip_bills = len(ip_bills)
                rec.other_bills = len(other_bills)
            elif rec.name == 'Today IP Part Billing':
                ip_part = self.env['ip.part.billing'].search([
                    ('bill_date', '>=', start_dt),
                    ('bill_date', '<', end_dt),
                    ('status', '=', 'paid')
                ])

                rec.ip_part_amount = sum(ip_part.mapped('total_amount'))
            elif rec.name == 'Today Credit Billing':
                reports = self.env['credit.billing.report'].search([])
                grand_total = sum(reports.mapped('amount'))

                rec.credit_amount = grand_total
    # @api.depends('name')
    # def _compute_counts(self):
    #     today = fields.Date.today()
    #     start_dt = datetime.combine(today, datetime.min.time())
    #     end_dt = start_dt + timedelta(days=1)
    #
    #     for rec in self:
    #         # Ensure all counts are set, even if 0
    #         rec.consultation_count = 0
    #         rec.sale_count = 0
    #         rec.discharge_count = 0
    #         rec.admit_count = 0
    #         rec.expired_count = 0
    #         rec.purchase_count = 0
    #
    #         # Assign specific counts based on name
    #         if rec.name == 'Today Consultation Details':
    #             rec.consultation_count = self.env['patient.reg'].search_count([('date', '=', today)])
    #         elif rec.name == 'Today Sale Report':
    #             rec.sale_count = self.env['pharmacy.prescription.line'].search_count([
    #                 ('pharmacy_id.date', '>=', start_dt),
    #                 ('pharmacy_id.date', '<', end_dt),
    #                 '|',
    #                 ('pharmacy_id.status', '=', 'paid'),
    #                 ('pharmacy_id.payment_mathod', '=', 'credit'),
    #             ])
    #         elif rec.name == 'Discharged Patient Details':
    #             rec.discharge_count = self.env['discharged.patient.record'].search_count([
    #                 ('discharge_date', '>=', start_dt),
    #                 ('discharge_date', '<', end_dt)
    #             ])
    #         elif rec.name == 'Admitted Details':
    #             rec.admit_count = self.env['hospital.admitted.patient'].search_count([
    #                 ('admission_date', '>=', start_dt),
    #                 ('admission_date', '<', end_dt)
    #             ])
    #         elif rec.name == 'Expired Medicines':
    #             rec.expired_count = self.env['stock.entry'].search_count([
    #                 ('exp_date', '<', today)
    #             ])
    #         elif rec.name == 'Today Purchase Details':
    #             rec.purchase_count = self.env['account.move'].search_count([
    #                 ('supplier_bill_date', '=', today)
    #             ])

    def open_card_action(self):
        self.ensure_one()
        user_tz = self.env.user.tz or 'UTC'
        now = fields.Datetime.now()
        today = now.astimezone(pytz.timezone(user_tz)).date()

        start_dt = datetime.combine(today, datetime.min.time())
        end_dt = datetime.combine(today, datetime.max.time())

        # Convert back to UTC for the domain
        start_dt = pytz.timezone(user_tz).localize(start_dt).astimezone(pytz.UTC)
        end_dt = pytz.timezone(user_tz).localize(end_dt).astimezone(pytz.UTC)

        if self.name == 'Today OP Details':
            return {
                'type': 'ir.actions.act_window',
                'name': 'Consultation Details',
                'res_model': 'patient.reg',
                'view_mode': 'tree,form',
                'target': 'current',
                'domain': [('time',  '>=', start_dt),('time',  '<', end_dt),('status','!=','unpaid'),('register_mode_payment','!=','credit')],
            }
        elif self.name == 'Today Pharmacy Billing Details':
            return {
                'type': 'ir.actions.act_window',
                'name': 'Today Sold Medicines',
                'res_model': 'pharmacy.prescription.line',
                'view_mode': 'tree',
                'target': 'current',
                'domain': [
                    ('pharmacy_id.date', '>=', start_dt),
                    ('pharmacy_id.date', '<', end_dt),
                    ('pharmacy_id.status', '=', 'paid'),
                ],
                'view_id': self.env.ref('homeo_doctor.view_today_sale_medicine_tree').id,
            }

        elif self.name == 'Discharged Patient Details':

                return {
                    'type': 'ir.actions.act_window',
                    'name': 'Discharged Patients',
                    'res_model': 'discharged.patient.record',
                    'view_mode': 'tree,form',
                    'target': 'current',
                    'domain': [('discharge_date', '>=', start_dt), ('discharge_date', '<', end_dt)],
                }

        elif self.name == 'Admitted Patient Details':
            return {
                'type': 'ir.actions.act_window',
                'name': 'Discharged Patients',
                'res_model': 'hospital.admitted.patient',
                'view_mode': 'tree,form',
                'target': 'current',
                'domain': [('admission_date', '>=', start_dt), ('admission_date', '<', end_dt),('status', '=', 'admitted'),],
            }
        elif self.name == 'Expired Medicines':
            return {
                'type': 'ir.actions.act_window',
                'name': 'Discharged Patients',
                'res_model': 'stock.entry',
                'view_mode': 'tree,form',
                'target': 'current',
                'domain': [('exp_date', '<', today_str),('quantity', '>', 0), ]
            }
        elif self.name == 'Today Revisit Details':
            return {
                'type': 'ir.actions.act_window',
                'name': 'Revisit',
                'res_model': 'patient.appointment',
                'view_mode': 'tree,form',
                'target': 'current',
                'domain': [('appointment_date','>=', start_dt),('appointment_date','<', end_dt),('status','=','confirmed'),('register_mode_payment','!=','credit') ]
            }
        elif self.name == 'Today General Billing':
            return {
                'type': 'ir.actions.act_window',
                'name': 'General Billing',
                'res_model': 'general.billing',
                'view_mode': 'tree,form',
                'target': 'current',
                'domain': [('bill_date', '>=', start_dt), ('bill_date', '<', end_dt),('status','=' ,'paid')]
            }

        elif self.name == 'Today Purchase Details':
            return {
                'type': 'ir.actions.act_window',
                'name': 'Purchase Details',
                'res_model': 'account.move',
                'view_mode': 'tree,form',
                'target': 'current',
                'domain': [('supplier_bill_date', '=', today_str),('state', '=', 'posted') ]
            }
        elif self.name == 'Today Lab Billing':
            return {
                'type': 'ir.actions.act_window',
                'name': 'Purchase Details',
                'res_model': 'doctor.lab.report',
                'view_mode': 'tree,form',
                'target': 'current',
                'domain': [('date','>=', start_dt),('date', '<', end_dt),('status', '=', 'paid'), ('mode_of_payment', '!=', 'credit'), ]
            }
        elif self.name == 'Today IP Part Billing':
            return {
                'type': 'ir.actions.act_window',
                'name': 'IP Part Billing',
                'res_model': 'ip.part.billing',
                'view_mode': 'tree,form',
                'target': 'current',
                'domain': [('bill_date', '>=', start_dt), ('bill_date', '<', end_dt),('status','=' ,'paid')]
            }
        elif self.name == 'Today Credit Billing':
            # Clean old data
            self.env['credit.billing.report'].search([]).unlink()


            # OP Credit
            op_records = self.env['patient.reg'].search([
                ('date', '=', today_str),
                ('register_mode_payment', '=', 'credit')
            ])

            op_total = sum(op_records.mapped('register_total_amount'))

            if op_total:
                self.env['credit.billing.report'].create({
                    'bill_type': 'op',
                    'amount': op_total,
                })
            op_revisit_records = self.env['patient.appointment'].search([
                ('appointment_date', '=', today_str),
                ('register_mode_payment', '=', 'credit')
            ])

            op_revisit_total = sum(op_revisit_records.mapped('register_total_amount'))

            if op_revisit_total:
                self.env['credit.billing.report'].create({
                    'bill_type': 'op_revisit',
                    'amount': op_revisit_total,
                })

            pharmacy_records = self.env['pharmacy.description'].search([
                ('date', '>=', start_dt),
                ('date', '<', end_dt),
                ('payment_mathod', '=', 'credit')
            ])

            pharmacy_total = sum(pharmacy_records.mapped('total_amount'))


            if pharmacy_total:
                self.env['credit.billing.report'].create({
                    'bill_type': 'pharmacy',
                    'amount': pharmacy_total,
                })

            lab_records = self.env['doctor.lab.report'].search([
                ('date', '=', today_str),
                ('mode_of_payment', '=', 'credit')
            ])

            lab_total = sum(lab_records.mapped('total_bill_amount'))

            if lab_total:
                self.env['credit.billing.report'].create({
                    'bill_type': 'lab',
                    'amount': lab_total,
                })

            general_records = self.env['general.billing'].search([
                ('bill_date', '>=', start_dt),
                ('bill_date', '<', end_dt),
                ('mode_pay', '=', 'credit'),
            ])

            general_total = sum(general_records.mapped('total_amount'))

            if general_total:
                self.env['credit.billing.report'].create({
                    'bill_type': 'general',
                    'amount': general_total,
                })

            return {
                'type': 'ir.actions.act_window',
                'name': 'Combined Credit Billing',
                'res_model': 'credit.billing.report',
                'view_mode': 'tree',
                'target': 'current',
            }

        else:
            return {'type': 'ir.actions.act_window_close'}





class CollectionReportLine(models.TransientModel):
    _name = 'collection.report.line'
    _description = 'Collection Report Line'

    date = fields.Date()
    department = fields.Char()
    payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('credit', 'Credit'),
        ('card', 'Card'),
        ('cheque', 'Cheque'),
        ('upi', 'UPI')
    ])
    amount = fields.Float()


class CreditBillingReport(models.Model):
    _name = 'credit.billing.report'
    _description = 'Combined Credit Billing Report'
    _rec_name = 'patient_name'
    _order = 'bill_date desc'

    bill_date = fields.Date(string="Bill Date")
    patient_name = fields.Char(string="Patient Name")
    bill_type = fields.Selection([
        ('op', 'OP'),
        ('op_revisit', 'OP Revisit'),
        ('pharmacy', 'Pharmacy'),
        ('lab', 'Lab'),
        ('general', 'General Bill'),
        ('ip_part', 'IP Part')

    ], string="Bill Type")
    amount = fields.Float(string="Amount")
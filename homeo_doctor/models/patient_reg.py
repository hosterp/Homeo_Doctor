import dateutil.utils
from odoo import api, fields, models, tools,_
import odoo.addons
# from datetime import datetime, date
# default=date.today()
class PatientRegistration(models.Model):
    _name = 'patient.registration'
    _description = 'Patient Registration'
    _rec_name = 'reference_no'
    _order = 'reference_no desc'

    reference_no = fields.Char(string="Reference")
    date = fields.Date(default=dateutil.utils.today(), readonly=True)
    formatted_date = fields.Char(string='Formatted Date', compute='_compute_formatted_date')
    user_id = fields.Many2one('patient.reg', string='Name',required=True)
    patient_id = fields.Char(string='Name',required=True,related='user_id.patient_id')
    address = fields.Text(string='Address',required=True,related='user_id.address')
    age = fields.Integer( string='Age',required=True,related='user_id.age')
    phone_number = fields.Char( string='Phone No',size=12,related='user_id.phone_number')
    symptoms = fields.Text(string="Sick")
    remark = fields.Text(string="Remark")
    checkup_reports=fields.Text(string='Checkup Details')
    med_ids = fields.One2many("prescription.entry.lines", 'prescription_line_id', string="Prescription Entry Lines")
    lab_report_count = fields.Integer(string="Lab Reports", compute='_compute_lab_report_count')


    def _compute_lab_report_count(self):
        for record in self:
            # Count the lab reports for this patient
            record.lab_report_count = self.env['doctor.lab.report'].search_count([('patient_id', '=', self.reference_no)])

    def action_view_lab_reports(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Lab Reports',
            'res_model': 'doctor.lab.report',
            'view_mode': 'tree,form',
            'domain': [('patient_id', '=', self.reference_no)],
            'context': dict(self.env.context, default_patient_id=self.reference_no),
        }
    @api.model
    def create(self, vals):
        if vals.get('reference_no', _('New')) == _('New'):
            vals['reference_no'] = self.env['ir.sequence'].next_by_code(
                'patient.registrartion.group') or _('New')
        res = super(PatientRegistration, self).create(vals)
        return res

    def _compute_formatted_date(self):
        for record in self:
            if record.date:
                formatted_date = record.date.strftime('%d/%m/%Y')
                record.formatted_date = formatted_date
            else:
                record.formatted_date = ''

    def action_move_to_pharmacy(self):
        pharmacy_vals = {
            'name': self.patient_id,
            'patient_id': self.reference_no,
            'phone_number': self.phone_number,
            'prescription_line_ids': [(0, 0, {
                'product_id': line.product_id.id,
                'total_med': line.total_med,
                'per_ped': line.per_ped,
                'morn': line.morn,
                'noon': line.noon,
                'night': line.night,
            }) for line in self.med_ids],
        }


        pharmacy_record = self.env['pharmacy.description'].create(pharmacy_vals)

        #
        # return {
        #     'type': 'ir.actions.act_window',
        #     'name': 'Pharmacy Description',
        #     'res_model': 'pharmacy.description',
        #     'view_mode': 'form',
        #     'res_id': pharmacy_record.id,
        #     'target': 'current',
        # }


class PrescriptionEntryLine(models.Model):
    _name = 'prescription.entry.lines'
    _description = 'Prescription Entry Line'

    prescription_line_id = fields.Many2one("patient.registration", string="Prescription Entry")
    product_id = fields.Many2one('product.product', string="Medicine")
    total_med = fields.Integer("Tot Med")
    per_ped = fields.Integer("Per Med")
    morn = fields.Boolean("Morn")
    noon = fields.Boolean("Noon")
    night = fields.Boolean("Night")


    # @api.onchange('product_id')
    # def product_stock_total(self):
    #     if self.product_id:
    #         stock_records = self.env['stock.entry.lines'].search([('product_id', '=', self.product_id.id)])
    #         print(stock_records.stock,'stock................')
    #         self.total_med=stock_records.stock
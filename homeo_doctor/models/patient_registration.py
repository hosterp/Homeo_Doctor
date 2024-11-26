import dateutil.utils
from odoo import api, fields, models, tools,_
import odoo.addons
# from datetime import datetime, date
# default=date.today()
class PatientRegistration(models.Model):
    _name = 'patient.reg'
    _description = 'Patient Registration'
    _rec_name = 'reference_no'
    _order = 'reference_no desc'

    reference_no = fields.Char(string="Reference")
    date = fields.Date(default=dateutil.utils.today(), readonly=True)
    formatted_date = fields.Char(string='Formatted Date', compute='_compute_formatted_date')
    patient_id = fields.Char(required=True, string="Name")
    address = fields.Text(required=True, string="Address")
    age = fields.Integer(required=True, string="Age")
    phone_number = fields.Char(string="Phone No",size=12)
    email = fields.Char(string="Email ID",size=12)
    doc_name=fields.Many2one('doctor.profile',string='Doctor')
    registration_fee = fields.Float(string="Registration Fee", required=True, default=50.0)
    remark = fields.Text(string="Remark")
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], string="Gender", required=True)
    lab_report_count = fields.Integer(string="Lab Reports", compute='_compute_lab_report_count')

    def _compute_lab_report_count(self):
        for record in self:
            # Count the lab reports for this patient
            record.lab_report_count = self.env['doctor.lab.report'].search_count([('patient_id', '=', record.id)])

    def action_view_lab_reports(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Lab Reports',
            'res_model': 'doctor.lab.report',
            'view_mode': 'tree,form',
            'domain': [('patient_id', '=', self.id)],
            'context': dict(self.env.context, default_patient_id=self.id),
        }

    @api.model
    def create(self, vals):
        if vals.get('reference_no', _('New')) == _('New'):
            vals['reference_no'] = self.env['ir.sequence'].next_by_code(
                'patient.reg.group') or _('New')
        record = super(PatientRegistration, self).create(vals)



        self.env['patient.registration'].create({
            'user_id': record.id,
            'patient_id': record.patient_id,
            'address': record.address,
            'age': record.age,
            'phone_number': record.phone_number,
        })

        return record

    def _compute_formatted_date(self):
        for record in self:
            if record.date:
                formatted_date = record.date.strftime('%d/%m/%Y')
                record.formatted_date = formatted_date
            else:
                record.formatted_date = ''


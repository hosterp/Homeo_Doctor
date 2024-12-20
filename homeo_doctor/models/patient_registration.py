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
    email = fields.Char(string="Email ID")
    department_id=fields.Many2one('doctor.department',string='Department',required=True)
    doc_name=fields.Many2one('doctor.profile',string='Doctor',required=True)
    registration_fee = fields.Float(string="Registration Fee", required=True, default=50.0)
    remark = fields.Text(string="Remark")
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], string="Gender", required=True)
    lab_report_count = fields.Integer(string="Lab Reports", compute='_compute_lab_report_count')
    time=fields.Datetime(string="Time")
    mri_report_ids = fields.One2many('scanning.mri', 'patient_id', string="MRI Reports")
    ct_report_ids = fields.One2many('scanning.ct', 'patient_id', string="CT Reports")
    xray_report_ids = fields.One2many('scanning.x.ray', 'patient_id', string="X-Ray Reports")

    @api.onchange('department_id')
    def _onchange_department_id(self):
        if self.department_id:
            return {
                'domain': {
                    'doc_name': [('department_id', '=', self.department_id.id)],
                }
            }
        return {
            'domain': {
                'doc_name': []
            }
        }

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
            'doctor_id': record.doc_name,
        })

        return record

    def _compute_formatted_date(self):
        for record in self:
            if record.date:
                formatted_date = record.date.strftime('%d/%m/%Y')
                record.formatted_date = formatted_date
            else:
                record.formatted_date = ''

    @api.model
    def search_patient_by_phone(self, phone_number):
        return self.search([('phone_number', 'ilike', phone_number)])

    def action_create_appointment(self):
        appointment_vals = {
            'patient_id': self.id,
            'appointment_date': fields.Datetime.now(),
            'doctor_id': self.doc_name.id,
            'department': self.department_id.id,
            'status': 'draft',
        }
        appointment = self.env['patient.appointment'].create(appointment_vals)
        registration_vals = {
            'user_id': self.id,
            'patient_id': self.patient_id,
            'address': self.address,
            'age': self.age,
            'phone_number': self.phone_number,
            'doctor_id': self.doc_name,
        }

        patient_registration = self.env['patient.registration'].create(registration_vals)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Patient Appointment',
            'res_model': 'patient.appointment',
            'view_mode': 'form',
            'res_id': appointment.id,
            'target': 'current',
        }



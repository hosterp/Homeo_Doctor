from odoo import api, fields, models, _
import datetime


class PatientAppointment(models.Model):
    _name = 'patient.appointment'
    _description = 'Patient Appointment'
    _rec_name = 'appointment_reference'
    _order = 'appointment_date desc'

    appointment_reference = fields.Char(string="Appointment Reference")
    patient_id = fields.Many2one('patient.reg', string='Patient', required=True)
    appointment_date = fields.Datetime(string="Appointment Date", required=True)
    doctor_id = fields.Many2one('doctor.profile', string='Doctor', required=True)
    reason = fields.Text(string="Reason for Appointment")
    status = fields.Selection(
        [('draft', 'Draft'), ('confirmed', 'Confirmed'), ('completed', 'Completed'), ('cancelled', 'Cancelled')],
        default='draft', string="Status")
    notes = fields.Text(string="Appointment Notes")
    created_date = fields.Datetime(default=fields.Datetime.now, readonly=True)

    @api.model
    def create(self, vals):
        if vals.get('appointment_reference', _('New')) == _('New'):
            vals['appointment_reference'] = self.env['ir.sequence'].next_by_code('patient.appointment.sequence') or _(
                'New')
        return super(PatientAppointment, self).create(vals)

    @api.model
    def search_appointments_by_patient(self, patient_id):
        return self.search([('patient_id', '=', patient_id)])


from odoo import api, fields, models, _

class DoctorLabReport(models.Model):
    _name = 'doctor.lab.report'
    _description = 'Doctor Lab Report'
    _rec_name = 'report_reference'
    _order = 'date desc'

    report_reference = fields.Char(string="Report Reference", readonly=True, default=lambda self: _('New'))
    date = fields.Date(string="Report Date", default=fields.Date.context_today, required=True)
    doctor_id = fields.Many2one('doctor.profile', string="Doctor", required=True)
    patient_id = fields.Many2one('patient.reg', string="Patient", required=True)
    report_details = fields.Text(string="Report Details")
    attachment = fields.Binary(string="Result")
    attachment_name = fields.Char(string="Result")
    bill_amount=fields.Integer('Bill Amount')

    @api.model
    def create(self, vals):
        if vals.get('report_reference', _('New')) == _('New'):
            vals['report_reference'] = self.env['ir.sequence'].next_by_code('doctor.lab.report') or _('New')
        return super(DoctorLabReport, self).create(vals)

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(DoctorLabReport, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                           submenu=submenu)
        if self.env.user.has_group('base.group_user'):
            doc_id = self.env['doctor.profile'].search([('user_id', '=', self.doctor_id.user_id.id)], limit=1)
            if doc_id:
                domain = [('doctor_id', '=', doc_id.id)]
                res['arch'] = res['arch'].replace('<tree', f'<tree domain="{domain}"')
        return res
from email.policy import default

from odoo import api, fields, models

class DoctorProfile(models.Model):
    _name = 'doctor.profile'
    _description = 'Doctor Profile'
    _rec_name = 'name'


    name = fields.Char(string='Doctor Name', required=True)
    specialization = fields.Char(string='Specialization')
    phone = fields.Char(string='Phone Number', required=True)
    email = fields.Char(string='Email')
    qualification = fields.Char(string='Qualification')
    joining_date = fields.Date(string='Joining Date', default=fields.Date.context_today)
    department_id = fields.Many2one('doctor.department', string='Department', required=True)
    doctor_id = fields.Char(string="Doctor ID", readonly=True, copy=False, default="New")
    user_id = fields.Many2one('res.users', string="Assigned User", ondelete='set null')  # Changed ondelete to set null
    experience_years = fields.Integer(string='Years of Experience')
    available_days = fields.Many2many('doctor.available.day', string='Available Days')
    available_hours = fields.Char(string='Available Hours')
    bio = fields.Text(string='Doctor Bio')
    consultation_fee_doctor = fields.Integer(string='Consultation Fee')
    consultation_fee_limit = fields.Integer(string='Consultation Fee Day Limit',default=7)
    is_doctor=fields.Boolean(default=False)

    @api.model
    def create(self, vals):
        if vals.get('doctor_id', 'New') == 'New':
            user_id = vals.get('user_id')
            if user_id:
                vals['doctor_id'] = f"DOCTOR-{user_id}"
            else:
                vals['doctor_id'] = self.env['ir.sequence'].next_by_code('doctor.profile') or 'New'
        return super(DoctorProfile, self).create(vals)


class DoctorAvailableDay(models.Model):
    _name = 'doctor.available.day'
    _rec_name = 'day'


    day = fields.Selection([
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday')
    ], string='Day', required=True)



class DoctorDepartment(models.Model):
    _name = 'doctor.department'
    _description = 'Doctor Department'
    _rec_name = 'department'
    department = fields.Char(string='Department Name', required=True)
    doctor_ids = fields.One2many('doctor.profile', 'department_id', string="Doctors")


    def action_show_doctors(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Doctors',
            'res_model': 'doctor.profile',
            'view_mode': 'tree,form',
            'domain': [('department_id', '=', self.id)],
            'target': 'current',
        }
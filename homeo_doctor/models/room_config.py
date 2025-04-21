from odoo import models, fields, api

class HospitalRoom(models.Model):
    _name = 'hospital.room'
    _description = 'Hospital Room'
    _rec_name = 'room_type'

    room_number = fields.Char(string="Room Number")
    room_type = fields.Selection([
        ('ac', 'AC'),
        ('non_ac', 'Non AC'),
        ('ward', 'Ward')
    ], string="Room Type")
    advance_amount = fields.Float(string="Advance Amount")
    bed_count = fields.Integer(string="Total Beds")
    occupied_beds = fields.Integer(string="Occupied Beds", compute="_compute_occupied_beds", store=True)
    is_available = fields.Boolean(string="Is Available", compute="_compute_is_available", store=True)
    bed_ids = fields.One2many('hospital.bed', 'room_id', string="Beds")

    @api.depends('bed_ids')
    def _compute_occupied_beds(self):
        for room in self:
            room.occupied_beds = sum(1 for bed in room.bed_ids if bed.is_occupied)

    @api.depends('bed_ids')
    def _compute_is_available(self):
        for room in self:
            room.is_available = any(not bed.is_occupied for bed in room.bed_ids)

    # Optional if you want to show available rooms
    @api.depends('bed_ids')
    def _compute_available_rooms(self):
        for room in self:
            room.available_rooms = room.bed_count - room.occupied_beds

    available_rooms = fields.Integer(string="Available Rooms", compute="_compute_available_rooms", store=True)



class HospitalBed(models.Model):
    _name = 'hospital.bed'
    _description = 'Hospital Bed'
    _rec_number='room_id'

    bed_number = fields.Char()
    room_id = fields.Many2one('hospital.room', string="Room")
    is_occupied = fields.Boolean(compute='_compute_is_occupied', store=True)
    admission_ids = fields.One2many('patient.reg', 'bed_id', string="Admissions")

    @api.depends('admission_ids.status')
    def _compute_is_occupied(self):
        for bed in self:
            bed.is_occupied = any(adm.status == 'admitted' for adm in bed.admission_ids)



class HospitakBlock(models.Model):
    _name='hospital.block'
    _rec_name='block_name'

    block_name=fields.Char(string='Block Name')


class HospitakRoomType(models.Model):
    _name='hospital.room.type'
    _rec_name='room_type'

    room_type=fields.Char(string='Room Type')
from odoo import fields, models, api


class Ordenamientos(models.Model):
    _name = 'api_tramites_servicios_17.ordenamientos'

    id_ordenamiento = fields.Char(string='Id')
    nombre = fields.Char(string='Ordenamiento Name')
    articulo = fields.Char(string='Articulo')
    fraccion = fields.Char(string='Fraccion')
    insiso = fields.Char(string='Insiso')
    parrafo = fields.Char(string='Parrafo')
    numero = fields.Char(string='Numero')
    letra = fields.Char(string='Letra')
    otro = fields.Char(string='Otro')

    service_id = fields.Many2one('servicios', string='Service')
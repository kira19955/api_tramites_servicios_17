from odoo import fields, models, api
import requests
import json
import logging

_logger = logging.getLogger(__name__)

class Servicios(models.Model):
    _name = 'servicios'

    id_servicios = fields.Char(string='Id')
    name = fields.Char(string='Nombre')
    homoclave = fields.Char(string='Homoclave')
    categoria = fields.Char(string='Categoria')
    modalidad = fields.Char(string='Modalidad')
    sujeto_obligado = fields.Char(string='Sujeto Obligado')
    descripcion_ciudadana = fields.Text(string='Descripcion ciudadana')
    tra_fecha_modificacion = fields.Datetime(string='traFechaModificacion')

    ordenamientos_ids = fields.One2many(
        'ordenamientos',
        'service_id',
        string='Ordenamientos'
    )

    ficha_id = fields.Many2one('tramite', string='Ficha')
    ficha = fields.Boolean(string="Tiene Ficha", default= False)

    @api.model
    def execute_cron(self):
        """Método que será llamado por el cron. Obtiene el token y realiza la solicitud de la página correspondiente."""
        token = self.obtain_token()
        if token:
            self.call_single_page(token)
        else:
            _logger.info("Error: No se obtuvo el token.")

    def obtain_token(self):
        """Realiza la solicitud para obtener el token."""
        url_token = "https://www.catalogonacional.gob.mx/sujetosobligados/api/Login"
        payload_token = json.dumps({
            "Usuario": "api.veracruz.xalapa",
            "Password": "D1*yR7jM4vQ2nX9sA+kT6pWf8",
            "Tipo": "Correo",
            "Ip": "0.0.0.0"
        })
        headers_token = {
            'Content-Type': 'application/json'
        }

        try:
            response_token = requests.post(url_token, headers=headers_token, data=payload_token)
            if response_token.status_code == 200:
                token_data = response_token.json()
                token = token_data.get("token")
                return token
            else:
                _logger.info(f"Error al obtener el token: {response_token.status_code}")
                return None
        except Exception as e:
            _logger.info(f"Exception occurred: {str(e)}")
            return None

    def call_single_page(self, token):
        """Realiza la consulta solo de la página especificada en el modelo `pagina`."""
        headers_consulta = {
            'Authorization': f'Bearer {token}'
        }

        # Obtener el valor de la página desde el modelo `pagina`
        pagina_obj = self.env['pagina'].search([], limit=1)
        if not pagina_obj:
            # Si no existe un registro en `pagina`, lo creamos con valor 1
            pagina_obj = self.env['pagina'].create({'numero_pagina': 1})

        page = pagina_obj.numero_pagina
        if page <=39:
            url_consulta = f"https://www.catalogonacional.gob.mx/sujetosobligados/api/ConsultaTramites/Id_nom_cat_dep_hom/all/{page}"

            try:
                response_consulta = requests.get(url_consulta, headers=headers_consulta)
                _logger.info(f"Response status: {response_consulta.status_code}")
                
                if response_consulta.status_code == 200:
                    data = response_consulta.json().get('data', [])
                    _logger.info(f"Procesando {len(data)} servicios de la página {page}")
                    
                    servicios_procesados = 0
                    servicios_con_error = 0
                    
                    for index, item in enumerate(data):
                        try:
                            _logger.info(f"Procesando servicio {index + 1}/{len(data)}: {item.get('nombre', 'Sin nombre')}")
                            
                            # Crear o actualizar el servicio
                            servicio = self.create_or_update_service(item)
                            _logger.info(f"Servicio creado/actualizado: ID {servicio.id}, Nombre: {servicio.name}")
                            
                            # Procesar ordenamientos
                            ordenamientos_data = item.get('ordenamientos', [])
                            ordenamientos_creados = 0
                            
                            for ordenamiento in ordenamientos_data:
                                try:
                                    self.env['ordenamientos'].create({
                                        'id_ordenamiento': ordenamiento.get('id'),
                                        'nombre': ordenamiento.get('nombre'),
                                        'articulo': ordenamiento.get('articulo'),
                                        'fraccion': ordenamiento.get('fraccion'),
                                        'insiso': ordenamiento.get('insiso'),
                                        'parrafo': ordenamiento.get('parrafo'),
                                        'numero': ordenamiento.get('numero'),
                                        'letra': ordenamiento.get('letra'),
                                        'otro': ordenamiento.get('otro'),
                                        'service_id': servicio.id
                                    })
                                    ordenamientos_creados += 1
                                except Exception as ordenamiento_error:
                                    _logger.error(f"Error creando ordenamiento para servicio {servicio.id}: {str(ordenamiento_error)}")
                            
                            _logger.info(f"Ordenamientos creados para servicio {servicio.id}: {ordenamientos_creados}")
                            servicios_procesados += 1
                            
                        except Exception as servicio_error:
                            _logger.error(f"Error procesando servicio {index + 1}: {str(servicio_error)}")
                            servicios_con_error += 1
                            # Continuar con el siguiente servicio
                            continue
                    
                    _logger.info(f"Página {page} procesada: {servicios_procesados} exitosos, {servicios_con_error} con errores")
                    
                    # Solo incrementar página si se procesaron servicios exitosamente
                    if servicios_procesados > 0:
                        pagina_obj.numero_pagina += 1
                        _logger.info(f"Página incrementada a: {pagina_obj.numero_pagina}")
                    else:
                        _logger.warning(f"No se procesaron servicios en la página {page}, no se incrementa el contador")
                        
                else:
                    _logger.error(f"Error al realizar la consulta de la página {page}: {response_consulta.status_code}")
                    _logger.error(f"Response content: {response_consulta.text}")
                    
            except Exception as e:
                _logger.error(f"Exception occurred while fetching page {page}: {str(e)}")
                import traceback
                _logger.error(f"Traceback: {traceback.format_exc()}")
        else:
            # Si `page` es 40, desactivamos el cron y reiniciamos la página a 1
            pagina_obj.numero_pagina = 1
            cron_id = self.env.ref('tramites_servicios_ayto.ir_cron_execute_api_calls')  # Cambia 'your_module_name' por el nombre de tu módulo
            if cron_id:
                cron_id.sudo().write({'active': False})
            _logger.info("El cron ha sido desactivado automáticamente después de alcanzar la página 39.")

    def create_or_update_service(self, data):
        """Crea o actualiza un registro del modelo servicios basado en la data de la API."""
        try:
            # Validar datos requeridos
            if not data.get('id'):
                raise ValueError("ID del servicio es requerido")
            
            servicio = self.search([('id_servicios', '=', data.get('id'))], limit=1)
            
            # Procesar fecha de modificación
            fecha_modificacion = None
            if data.get('traFechaModificacion'):
                try:
                    # Convertir fecha ISO a formato Odoo
                    from datetime import datetime
                    fecha_str = data.get('traFechaModificacion')
                    # Parsear fecha ISO: 2025-03-07T00:00:00
                    fecha_modificacion = datetime.fromisoformat(fecha_str.replace('Z', '+00:00'))
                    _logger.info(f"Fecha parseada correctamente: {fecha_modificacion}")
                except Exception as fecha_error:
                    _logger.warning(f"Error parseando fecha {data.get('traFechaModificacion')}: {str(fecha_error)}")
                    fecha_modificacion = None
            
            servicio_data = {
                'id_servicios': data.get('id'),
                'name': data.get('nombre', 'Sin nombre'),
                'homoclave': data.get('homoclave', ''),
                'categoria': data.get('categoria', ''),
                'modalidad': data.get('modalidad', ''),
                'sujeto_obligado': data.get('sujetoObligado', ''),
                'descripcion_ciudadana': data.get('descripcionCiudadana', ''),
                'tra_fecha_modificacion': fecha_modificacion
            }
            
            if not servicio:
                _logger.info(f"Creando nuevo servicio: {servicio_data['name']} (ID: {servicio_data['id_servicios']})")
                servicio = self.create(servicio_data)
                _logger.info(f"Servicio creado exitosamente: {servicio.id}")
            else:
                _logger.info(f"Actualizando servicio existente: {servicio.name} (ID: {servicio.id})")
                servicio.write(servicio_data)
                _logger.info(f"Servicio actualizado exitosamente: {servicio.id}")
            
            return servicio
            
        except Exception as e:
            _logger.error(f"Error en create_or_update_service: {str(e)}")
            _logger.error(f"Datos del servicio: {data}")
            raise

    @api.model
    def activate_cron(self):
        """Activa el cron para ejecutar las llamadas a la API si está desactivado."""
        cron_id = self.env.ref('tramites_servicios_ayto.ir_cron_execute_api_calls', raise_if_not_found=False)
        if cron_id and not cron_id.active:
            cron_id.sudo().write({'active': True})
            _logger.info("El cron 'ir_cron_execute_api_calls' ha sido activado.")
        else:
            _logger.info("El cron 'ir_cron_execute_api_calls' ya está activo o no se encontró.")
    
    @api.model
    def activate_cron_fichas(self):
        """Activa el cron de fichas y ejecuta reset antes de activar."""
        _logger.info("🔄 Activando cron de fichas con reset previo...")
        
        try:
            # Ejecutar reset de fichas (sin eliminar registros)
            reset_result = self.env['servicios'].reset_fichas_processing(delete_records=False)
            
            if reset_result:
                _logger.info("✅ Reset de fichas ejecutado exitosamente")
                
                # Verificar que el cron de fichas esté activo
                cron_ficha = self.env.ref('tramites_servicios_ayto.ir_cron_execute_api_calls_ficha', raise_if_not_found=False)
                if cron_ficha:
                    if not cron_ficha.active:
                        cron_ficha.sudo().write({'active': True})
                        _logger.info("✅ Cron de fichas activado")
                    else:
                        _logger.info("ℹ️ Cron de fichas ya estaba activo")
                    
                    _logger.info(f"📊 Próxima ejecución del cron: {cron_ficha.nextcall}")
                    return True
                else:
                    _logger.error("❌ No se encontró el cron de fichas")
                    return False
            else:
                _logger.error("❌ Error en el reset de fichas")
                return False
                
        except Exception as e:
            _logger.error(f"❌ Error en activate_cron_fichas: {str(e)}")
            import traceback
            _logger.error(f"Traceback: {traceback.format_exc()}")
            return False

    @api.model
    def test_single_page_processing(self, page_number=1):
        """Método de prueba para procesar una página específica manualmente."""
        _logger.info(f"Iniciando procesamiento de prueba para página {page_number}")
        
        try:
            # Obtener token
            token = self.obtain_token()
            if not token:
                _logger.error("No se pudo obtener el token")
                return False
            
            # Procesar página específica
            headers_consulta = {
                'Authorization': f'Bearer {token}'
            }
            
            url_consulta = f"https://www.catalogonacional.gob.mx/sujetosobligados/api/ConsultaTramites/Id_nom_cat_dep_hom/all/{page_number}"
            _logger.info(f"Consultando URL: {url_consulta}")
            
            response_consulta = requests.get(url_consulta, headers=headers_consulta)
            _logger.info(f"Response status: {response_consulta.status_code}")
            
            if response_consulta.status_code == 200:
                data = response_consulta.json().get('data', [])
                _logger.info(f"Procesando {len(data)} servicios de la página {page_number}")
                
                servicios_procesados = 0
                servicios_con_error = 0
                
                for index, item in enumerate(data):
                    try:
                        _logger.info(f"Procesando servicio {index + 1}/{len(data)}: {item.get('nombre', 'Sin nombre')}")
                        
                        # Crear o actualizar el servicio
                        servicio = self.create_or_update_service(item)
                        _logger.info(f"Servicio creado/actualizado: ID {servicio.id}, Nombre: {servicio.name}")
                        
                        # Procesar ordenamientos
                        ordenamientos_data = item.get('ordenamientos', [])
                        ordenamientos_creados = 0
                        
                        for ordenamiento in ordenamientos_data:
                            try:
                                self.env['ordenamientos'].create({
                                    'id_ordenamiento': ordenamiento.get('id'),
                                    'nombre': ordenamiento.get('nombre'),
                                    'articulo': ordenamiento.get('articulo'),
                                    'fraccion': ordenamiento.get('fraccion'),
                                    'insiso': ordenamiento.get('insiso'),
                                    'parrafo': ordenamiento.get('parrafo'),
                                    'numero': ordenamiento.get('numero'),
                                    'letra': ordenamiento.get('letra'),
                                    'otro': ordenamiento.get('otro'),
                                    'service_id': servicio.id
                                })
                                ordenamientos_creados += 1
                            except Exception as ordenamiento_error:
                                _logger.error(f"Error creando ordenamiento para servicio {servicio.id}: {str(ordenamiento_error)}")
                        
                        _logger.info(f"Ordenamientos creados para servicio {servicio.id}: {ordenamientos_creados}")
                        servicios_procesados += 1
                        
                    except Exception as servicio_error:
                        _logger.error(f"Error procesando servicio {index + 1}: {str(servicio_error)}")
                        servicios_con_error += 1
                        continue
                
                _logger.info(f"Página {page_number} procesada: {servicios_procesados} exitosos, {servicios_con_error} con errores")
                return True
                
            else:
                _logger.error(f"Error al realizar la consulta de la página {page_number}: {response_consulta.status_code}")
                return False
                
        except Exception as e:
            _logger.error(f"Exception occurred while testing page {page_number}: {str(e)}")
            import traceback
            _logger.error(f"Traceback: {traceback.format_exc()}")
            return False





class Pagina(models.Model):
    _name = 'pagina'
    _description = 'Almacena el número de página para las consultas'

    numero_pagina = fields.Integer(string='Número de Página', default=1)

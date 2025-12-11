from odoo import fields, models, api
import requests
import json
import logging

_logger = logging.getLogger(__name__)

class Servicios(models.Model):
    _name = 'api_tramites_servicios_17.servicios'

    id_servicios = fields.Char(string='Id')
    nombre = fields.Char(string='Nombre')
    homoclave = fields.Char(string='Homoclave')
    categoria = fields.Char(string='Categoria')
    modalidad = fields.Char(string='Modalidad')
    sujetoObligado = fields.Char(string='Sujeto Obligado')
    descripcionCiudadana = fields.Text(string='Descripcion ciudadana')
    traFechaModificacion = fields.Datetime(string='traFechaModificacion')

    ordenamientos_ids = fields.One2many(
        'api_tramites_servicios_17.ordenamientos',
        'service_id',
        string='Ordenamientos'
    )

    #ficha_id = fields.Many2one('tramite', string='Ficha')
    ficha = fields.Boolean(string="Tiene Ficha", default= False)

    @api.model
    def execute_cron(self):
        """Método que será llamado por el cron. Obtiene el token y realiza la solicitud de la página correspondiente."""
        
        token = self.obtain_token()
        
        if token:
            self.call_single_page(token)
            _logger.info("Token obtenido correctamente: %s", token)
            
        else:
            _logger.info("Error: No se obtuvo el token.")

    def obtain_token(self):
        """Realiza la solicitud para obtener el token desde los datos almacenados en el modelo."""
       
        settings = self.env['api_tramites_servicios_17.settings'].search([], limit=1)
        
        if not settings:
            _logger.info("No se encontraron configuraciones para obtener el token.")
            return None

        payload_token = json.dumps({
            "Usuario": settings.usuario,
            "Password": settings.password,
            "Tipo": settings.tipo,
            "Ip": settings.ip
        })

        headers_token = {
            'Content-Type': 'application/json'
        }

        url_token = "https://www.catalogonacional.gob.mx/sujetosobligados/api/Login"

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
        """Consulta una página de la API externa usando el token, y procesa los servicios recibidos."""

        headers_consulta = {
            'Authorization': f'Bearer {token}'
        }

        settings = self.env['api_tramites_servicios_17.settings'].search([], limit=1)

        # Si no hay registro de configuración, lo creamos con página 1
        if not settings:
            settings = self.env['api_tramites_servicios_17.settings'].create({
                'page': 1,
            })

        page_number = settings.page or 1  # Asegura que siempre sea al menos 1

        if page_number <= 39:
            url_consulta = f"https://www.catalogonacional.gob.mx/sujetosobligados/api/ConsultaTramites/Id_nom_cat_dep_hom/all/{page_number}"

            try:
                response = requests.get(url_consulta, headers=headers_consulta)
                _logger.info(f"Response status: {response.status_code}")

                if response.status_code == 200:
                    data = response.json().get('data', [])
                    _logger.info(f"Procesando {len(data)} servicios de la página {page_number}")

                    servicios_procesados = 0
                    servicios_con_error = 0

                    for index, item in enumerate(data):
                        try:
                            _logger.info(
                                f"Procesando servicio {index + 1}/{len(data)}: {item.get('nombre', 'Sin nombre')}")
                            servicio = self.create_or_update_service(item)
                            _logger.info(f"Servicio creado/actualizado: ID {servicio.id}, Nombre: {servicio.nombre}")

                            # Crear ordenamientos
                            ordenamientos_data = item.get('ordenamientos', [])
                            for ordenamiento in ordenamientos_data:
                                try:
                                    self.env['api_tramites_servicios_17.ordenamientos'].create({
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
                                except Exception as e:
                                    _logger.error(f"Error creando ordenamiento para servicio {servicio.id}: {e}")

                            servicios_procesados += 1

                        except Exception as e:
                            _logger.error(f"Error procesando servicio {index + 1}: {e}")
                            servicios_con_error += 1
                            continue

                    _logger.info(
                        f"Página {page_number} procesada: {servicios_procesados} exitosos, {servicios_con_error} con errores")

                    if servicios_procesados > 0:
                        settings.page += 1
                        _logger.info(f"Página incrementada a: {settings.page}")
                    else:
                        _logger.warning("No se procesaron servicios exitosamente, la página no se incrementa.")

                else:
                    _logger.error(f"Error HTTP al consultar página {page_number}: {response.status_code}")
                    _logger.error(f"Contenido de respuesta: {response.text}")

            except Exception as e:
                _logger.error(f"Error de red o parseo al procesar página {page_number}: {e}")
                import traceback
                _logger.error(f"Traceback: {traceback.format_exc()}")

        else:
            # Si se alcanza la página 40, reiniciamos y desactivamos el cron
            settings.page = 1
            _logger.info("Página reiniciada a 1")

            try:
                cron_id = self.env.ref(
                    'tramites_servicios_ayto.ir_cron_execute_api_calls')  # Asegúrate que este XML ID exista
                if cron_id:
                    cron_id.sudo().write({'active': False})
                    _logger.info("El cron fue desactivado automáticamente al llegar a la página 40.")
            except Exception as e:
                _logger.error(f"No se pudo desactivar el cron automáticamente: {str(e)}")

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
                'nombre': data.get('nombre', 'Sin nombre'),
                'homoclave': data.get('homoclave', ''),
                'categoria': data.get('categoria', ''),
                'modalidad': data.get('modalidad', ''),
                'sujetoObligado': data.get('sujetoObligado', ''),
                'descripcionCiudadana': data.get('descripcionCiudadana', ''),
                'traFechaModificacion': fecha_modificacion
            }
            
            if not servicio:
                _logger.info(f"Creando nuevo servicio: {servicio_data['nombre']} (ID: {servicio_data['id_servicios']})")
                servicio = self.create(servicio_data)
                _logger.info(f"Servicio creado exitosamente: {servicio.id}")
            else:
                _logger.info(f"Actualizando servicio existente: {servicio.nombre} (ID: {servicio.id})")
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
            reset_result = self.env['api_tramites_servicios_17.servicios'].reset_fichas_processing(delete_records=False)
            
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
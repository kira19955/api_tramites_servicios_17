from odoo import http
from odoo.http import request
import json

class ServiciosController(http.Controller):

    @http.route('/servicios/data', auth='public', methods=['GET'],cors='*')
    def get_servicios(self):
        """Devuelve la información del modelo servicios en formato JSON"""

        # Buscar todos los registros de servicios
        servicios = request.env['api_tramites_servicios_17.servicios'].sudo().search([])

        # Crear una lista con la información de cada servicio
        servicios_data = []
        for servicio in servicios:
            servicios_data.append({
                'id': servicio.id_servicios,
                'nombre': servicio.nombre,
                'homoclave': servicio.homoclave,
                'categoria': servicio.categoria,
                'modalidad': servicio.modalidad,
                'sujeto_obligado': servicio.sujeto_obligado,
                'descripcion_ciudadana': servicio.descripcion_ciudadana,
                #'tra_fecha_modificacion': servicio.tra_fecha_modificacion,
                'tra_fecha_modificacion': servicio.tra_fecha_modificacion.isoformat() if servicio.tra_fecha_modificacion else None,
                'ordenamientos': [
                    {
                        'id_ordenamiento': ordenamiento.id_ordenamiento,
                        'nombre': ordenamiento.nombre,
                        'articulo': ordenamiento.articulo,
                        'fraccion': ordenamiento.fraccion,
                        'insiso': ordenamiento.insiso,
                        'parrafo': ordenamiento.parrafo,
                        'numero': ordenamiento.numero,
                        'letra': ordenamiento.letra,
                        'otro': ordenamiento.otro,
                    }
                    for ordenamiento in servicio.ordenamientos_ids
                ]
            })

        # Devolver los datos en formato JSON como respuesta HTTP
        return http.Response(
            json.dumps(servicios_data),
            content_type='application/json',
            status=200
        )




class TramiteController(http.Controller):

    @http.route('/api/tramites/<string:homoclave>', auth='public', type='http', methods=['GET'], csrf=False, cors='*')
    def get_tramite_by_homoclave(self, homoclave):
        tramite = request.env['api_tramites_servicios_17.tramite'].sudo().search([('homoclave', '=', homoclave)], limit=1)

        if not tramite:
            return http.Response(
                json.dumps({'status': 404, 'message': 'Trámite no encontrado'}),
                status=404,
                mimetype='application/json'
            )

        data = {
            'id': tramite.id,
            'dependencia': tramite.dependencia,
            'unidadAdministrativa': tramite.unidadAdministrativa,
            'acronimoDependencia': tramite.acronimoDependencia,
            'tipo': tramite.tipo,
            'homoclave': tramite.homoclave,
            'nombre': tramite.nombre,
            'descripcionCiudadana': tramite.descripcionCiudadana,
            'descripcion': tramite.descripcion,
            'modalidad': tramite.modalidad,
            'traResolucionesFavorables': tramite.traResolucionesFavorables,
            'tramiteServicio': tramite.tramiteServicio,
            'traquienSolicita_Otro': tramite.traquienSolicita_Otro,
            'traConsultasChatLinea': tramite.traConsultasChatLinea,
            'numeroRequFormato': tramite.numeroRequFormato,
            'numeroRequNoFormato': tramite.numeroRequNoFormato,
            'requiereConservarInfo': tramite.requiereConservarInfo,
            'acreditacion': tramite.acreditacion,
            'acreditacionEspecifique': tramite.acreditacionEspecifique,
            'verificacion': tramite.verificacion,
            'verificacionEspecifique': tramite.verificacionEspecifique,
            'inspeccion': tramite.inspeccion,
            'inspeccionEspecifique': tramite.inspeccionEspecifique,
            'conservarOtros': tramite.conservarOtros,
            'conservarOtrosEspecifique': tramite.conservarOtrosEspecifique,
            'suficienteCumplirRequisitos': tramite.suficienteCumplirRequisitos,
            'metodologiaResolucion': tramite.metodologiaResolucion,
            'metodologiaAdjuntarArchivo': tramite.metodologiaAdjuntarArchivo,
            'tramiteRequiereInspeccion': tramite.tramiteRequiereInspeccion,
            'objetivoInspeccion': tramite.objetivoInspeccion,
            'traResolucionesFav': tramite.traResolucionesFav,
            'traVolumenAnual': tramite.traVolumenAnual,
            'traComentariosRespecto': tramite.traComentariosRespecto,
            'traConsultasChatLineaLigas': tramite.traConsultasChatLineaLigas,
            'fechaActualizacion': tramite.fechaActualizacion,
            'criteriosresolucion': [{'id': cr.id, 'tramite_id': cr.tramite_id.id} for cr in
                                    tramite.criteriosresolucion],
            'costos': [{'id': c.id, 'monto': c.monto, 'moneda': c.moneda , 'formula' : c.formula,
                        'tipoCosto': c.tipoCosto,
                        'momentoRealizarPago': c.momentoRealizarPago,
                        'dondeRealizarPago': c.dondeRealizarPago} for c in tramite.costos],
            'opcionesRealizarTramite': [
                {   'id': op.id, 
                    'opcionRealizarTramite': op.opcionRealizarTramite,
                    'accionesPresenciallst': [
                            {
                                'accion': ap.accion,
                                'orden': ap.orden,
                            }
            for ap in op.accionesPresenciallst
        ]
                }   for op in tramite.opcionesRealizarTramite
                ]
                                        ,
            'oficinasAtencion': [{'id': ofi.id, 'nombre': ofi.nombre, 'direccion': ofi.direccion} for ofi in
                                 tramite.oficinasAtencion],
            'contactos': [{
                        'id': con.id, 'nombre': con.nombre, 'apellidoP':con.apellidoP, 'apellidoM':con.apellidoM ,
                           'extension': con.extension, 'correo': con.correo,'telefono': con.telefono,
                           'tipoContacto': con.tipoContacto, 'cargo' : con.cargo , 'rolFuncionario' : con.rolFuncionario,
                            
                           } for con in tramite.contactos],
            'requisitos': [
                            {'id': req.id, 'nombre': req.nombre, 'descripcion': req.descripcion,
                             'original' :req.original, 'parteFormato' : req.requisitoParteFormato,
                             'naturaleza' : req.naturalezaDelRequisito,
                            
                            
                            } for req in
                           tramite.requisitos],
            'formatos': [{'id': frm.id, 'nombre': frm.nombre, 'url': frm.url} for frm in tramite.formatos],
            'fundamento': [
                    {
                        'id': fun.id if fun.id else "",
                        'nombreOrdenamiento': fun.nombreOrdenamiento if fun.nombreOrdenamiento else "",
                        'articulos': fun.articulo if fun.articulo else "",
                        'tipoOrdenamiento': fun.tipoOrdenamiento if fun.tipoOrdenamiento else "",
                        'inciso': fun.inciso if fun.inciso else "",
                        'numero': fun.numero if fun.numero else "",
                        'fraccion': fun.fraccion if fun.fraccion else "",
                        'parrafo': fun.parrafo if fun.parrafo else "",
                        'letra': fun.letra if fun.letra else "",
                        'ordenGobierno': fun.ordenGobierno if fun.ordenGobierno else "",
                    }
                    for fun in tramite.fundamento
                ],

            'plazos' : [{
                                    'id': pl.id,
                                    'nombrePlazo': pl.nombrePlazo if  pl.nombrePlazo else '',
                                    'paraPrevenir': pl.paraPrevenir if  pl.paraPrevenir else '',
                                    'responderlaPrevencion':pl.responderlaPrevencion if pl.responderlaPrevencion  else '',
                                    'respuestaResolver': pl.respuestaResolver if pl.respuestaResolver else '',
                                    }
                                    for pl in tramite.plazos
                                ],             
            'vigencia': [{'id': vig.id, 'vigenciaTramite': vig.vigenciaTramite} for vig in tramite.vigencia],
            'solicita': [{'id': sol.id, 'quienSolicita': sol.quienSolicita} for sol in tramite.solicita],
            'conservarInformacion': [{'id': ci.id, 'requiereConservar': ci.requiereConservar,
                                      'finesParaConservar': ci.finesParaConservar} for ci in
                                     tramite.conservarInformacion],
            'solicitudes': [{'id': sol.id} for sol in tramite.solicitudes],
        }

        return http.Response(
            json.dumps({'status': 200, 'data': data}),
            status=200,
            mimetype='application/json'
        )
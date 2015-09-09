# -*- coding: utf-8 -*-
from openerp import http

# class DhlDelivery(http.Controller):
#     @http.route('/dhl_delivery/dhl_delivery/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/dhl_delivery/dhl_delivery/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('dhl_delivery.listing', {
#             'root': '/dhl_delivery/dhl_delivery',
#             'objects': http.request.env['dhl_delivery.dhl_delivery'].search([]),
#         })

#     @http.route('/dhl_delivery/dhl_delivery/objects/<model("dhl_delivery.dhl_delivery"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('dhl_delivery.object', {
#             'object': obj
#         })
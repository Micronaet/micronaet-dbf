# -*- coding: utf-8 -*-
###############################################################################
#
#    Copyright (C) 2001-2014 Micronaet SRL (<http://www.micronaet.it>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
import os
import sys
import logging
import openerp
import openerp.netsvc as netsvc
import openerp.addons.decimal_precision as dp
from openerp.osv import fields, osv, expression, orm
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from openerp import SUPERUSER_ID, api
from openerp import tools
from openerp.tools.translate import _
from openerp.tools.float_utils import float_round as round
from dbfread import DBF
from openerp.tools import (DEFAULT_SERVER_DATE_FORMAT, 
    DEFAULT_SERVER_DATETIME_FORMAT, 
    DATETIME_FORMATS_MAP, 
    float_compare)


_logger = logging.getLogger(__name__)

class DbfProductProduct(orm.Model):
    """ Model name: Product product
    """
    
    _name = 'dbf.product.product'
    _description = 'DBF Product'
    _rec_name = 'name'
    _order = 'default_code'
            
    _columns = {
        'name': fields.char('Name', size=80, required=True),
        'metel_producer_code': fields.char('METEL Producer', size=3),
        'default_code': fields.char('Code', size=20),
        'ean13': fields.char('EAN 13', size=13),
        'standard_price': fields.float('Standard price', digits=(16, 3)),
        'product_id': fields.many2one('product.product', 'Product'),
        'description': fields.text('Description',),
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

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


class HrAnalyticTimesheet(orm.Model):
    ''' Model name: Analytic Account
    '''
    
    _inherit = 'hr.analytic.timesheet'
    
    def schedule_dbf_edison_intervent_import(self, cr, uid, 
            verbose_log_count=100, context=None):
        ''' Import analytic from external DBF
        '''
        _logger.info('Start import account')    

        # Pool used:
        company_pool = self.pool.get('res.company')
        partner_pool = self.pool.get('res.partner')
        
        db = company_pool.get_dbf_table(
            cr, uid, 'RAPPOR.DBF', context=context)

        i = 0
        for record in db:
            i += 1
            if verbose_log_count and i % verbose_log_count == 0:
                _logger.warning('Import intervent #: %s' % i)
            
            # -----------------------------------------------------------------
            # Mapping fields (readability):
            # -----------------------------------------------------------------
            # Analytic account ref:
            #code = '%s%s' % (
            #    '', # record['CANNCANT'] or '', # TODO remove year
            #    record['CNUMCANT'] or '',
            #    )                                
            #name = record['CDESCANT'] or ''
            
            # Partner ref.:
            #partner_code = record['CCODCLIE'] or ''

            # -----------------------------------------------------------------
            # Linked partner:
            # -----------------------------------------------------------------
            #partner_ids = partner_pool.search(cr, uid, [
            #    ('dbf_customer_code', '=', partner_code)
            #    ], context=context)

            #partner_id = False
            #if len(partner_ids) > 1:
            #    _logger.error('More then one partner code: %s' % partner_code)
            #if partner_ids:
            #    partner_id = partner_ids[0]

            data = {
                'dbf_import': True,
                #'code': code,
                #'name': name,
                #'partner_id': partner_id,
                #'address_id': address_id,
                #'type': 'normal', 
                #'use_timesheets': True,
                }
                
            # Search partner code:
            intervent_ids = self.search(cr, uid, [
                #('code', '=', code),
                ], context=context)

            #if len(intervent_ids) > 1:
            #    _logger.error('More account with code: %s' % code)

            #if intervent_ids:
            #    self.write(cr, uid, analytic_ids, data, context=context)
            #else:
            #    self.create(cr, uid, data, context=context)
        _logger.info('End import intervent')    
        return True        
            
    _columns = {
        'dbf_import': fields.boolean('DBF import'),
        }

class ResUsers(orm.Model):
    """ Model name: ResUsers
    """    
    _inherit = 'res.users'
    
    _columns = {
        'dbf_code': fields.boolean('DBF Code', 
            help='Used for link user to intervent',
            ),
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

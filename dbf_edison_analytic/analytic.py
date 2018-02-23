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


class AccountAnalyticAccount(orm.Model):
    """ Model name: Analytic Account
    """
    
    _inherit = 'account.analytic.account'
    
    def schedule_dbf_edison_analytic_import(self, cr, uid, 
            verbose_log_count=100, context=None):
        ''' Import analytic from external DBF
        '''
        # ---------------------------------------------------------------------
        #                      COMMON PART: Get parameter
        # ---------------------------------------------------------------------
        # Browse company: 
        company_pool = self.pool.get('res.company')
        company_ids = company_pool.search(cr, uid, [], context=context)
        company_proxy = company_pool.browse(
            cr, uid, company_ids, context=context)[0]
        
        # Read parameter:    
        dbf_root_path = os.path.expanduser(company_proxy.dbf_root_path)
        dbf_ignorecase = company_proxy.dbf_ignorecase
        dbf_memofile = company_proxy.dbf_memofile
        dbf_encoding = company_proxy.dbf_encoding

        # ---------------------------------------------------------------------
        #                             CUSTOMER
        # ---------------------------------------------------------------------
        filename = os.path.join(dbf_root_path, 'CANTIE.DBF')
        db = DBF(
            filename, 
            ignorecase=dbf_ignorecase,
            ignore_missing_memofile=dbf_memofile,
            encoding=dbf_encoding,
            )
            
        i = 0
        for record in db:
            i += 1
            if verbose_log_count and i % verbose_log_count == 0:
                _logger.warning('Import analytic #: %s' % i)
            
            # Mapping fields:
            # TODO change:
            code = record['']
            name = record['CDESCLIE'] or '',

            data = {
                'dbf_import': True,
                'code': code,
                'name': name,
                }
                
            # Search partner code:
            analytic_ids = self.search(cr, uid, [
                ('code', '=', code),
                ], context=context)

            # len(analytic_ids) > 1 TODO WARNING
            if analytic_ids:
                self.write(cr, uid, analytic_ids, data, context=context)
            else:
                self.create(cr, uid, data, context=context)
        return True        
            
    _columns = {
        'dbf_import': fields.boolean('DBF import'),
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

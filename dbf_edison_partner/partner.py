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


class ResPartner(orm.Model):
    """ Model name: ResPartner
    """
    
    _inherit = 'res.partner'
    
    def schedule_dbf_edison_partner_import(self, cr, uid, verbose_log_count=100, 
            context=None):
        ''' Import partner from external DBF
        '''
        # Get parameter:
        company_pool = self.pool.get('res.company')
        company_ids = company_pool.search(cr, uid, [], context=context)
        company_proxy = company_pool.browse(
            cr, uid, company_ids, context=context)[0]
        
        # Read parameter:    
        dbf_root_path = company_proxy.dbf_root_path
        dbf_ignorecase = company_proxy.dbf_ignorecase
        dbf_memofile = company_proxy.dbf_memofile
        dbf_encoding = company_proxy.dbf_encoding
        
        filename = os.path.join(dbf_root_path, 'TBCLIE.DBF')

        db = DBF(
            filename, 
            ignorecase=dbf_ignorecase,
            ignore_missing_memofile=dbf_memofile,
            encoding=dbf_encoding,
            )
            
        i = 0
        #db.field_names
        for record in db:
            i += 1
            if verbose_log_count and i % verbose_log_count == 0:
                _logger.warning('Import partner #: %s' % i)
            
            # Mapping fields:
            ref = record['CCODCLIE']
            name = '%s%s' % (
                record['CDESCLIE'] or '',
                record['CDE2CLIE'] or '',
                )
            data = {
                'dbf_import': True,
                'dbf_customer_code': ref, 
                'ref': ref,
                'name': name,
                'street': record['CINDIR'],
                #'': record['CDPROV']
                'city': record['CCOMUNE'],
                'zip': record['CCAP'],
                
                # TODO add all field
                #'CCODFISC', 
                #'CPARTIVA', 'CFASCIA', 'CCODCOPA', 'CCODBANC', 'CCODCIVA', 
                # Destination (empty):
                #'CDESDESCR', 'CDESINDIR', 'CDESCITTA', 
                #'CTEACLIE', 'CTEUCLIE', 
                #'CTECCLIE', 'CTELRIF', 'CMESIMAN', 'NCOSTMAN', 'DDATAMAN', 
                #'CTIPCLIE', 'CCODZONA', 'CTLIARSE', 'CTLIARCO', 'CNAZIONE', 
                #'LFLAGCEE', 'CCODAGEN', 'NSCONTEX', 'CCODVETT', 'CCODVALU', 
                #'CCODLIST', 'CCONTORI', 'CSTATO', 'CCONTCORR', 'CEMAIL', 
                #'CSITOWEB', 'NSPESEIN', 'NSPEBOLL', 'NSPETRAS', 'CNUMDIC', 
                #'DDATDIC', 'CNUMREG', 'DDATREG', 'LEFFRATE', 'CFILLER', 
                #'NQUALIFI', 'DDATINSE', 'CRIFERIM', 'CCORTATT', 'LSPESEIN', 
                #'LSPEBOLL', 'LNOEXPCO', 'NSPEFISS', 'CCODCINN', 'CCODCINE', 
                #'NSCOFATT', 'NSCOARFA', 'NSTSINCR', 'DDATOPER', 'CORAOPER', 
                #'CCODOPER', 'CCODUTEN', 'NRICMANO', 'NRICSPEX', 'LPERSONA', 
                #'CFILLER1', 'CTEC2CLI', 'CTELRIF2', 'CCODAMMI', 'CCODPORT', 
                #'CTIPSOGG', 'NQUALIF2', 'NQUALIF3', 'LCALCRIT', 'LFRZPRZV', 
                #'LFRZNPRZ', 'CEMAIL2', 'CPEC', 'MZONA', 'MNOTE'
                }
                
            # Search partner code:
            
            # Write or create:


        
        return True
    
    _columns = {
        'dbf_import': fields.boolean('DBF import'),
        'dbf_customer_code': fields.char('DBF customer code', size=10),
        'dbf_supplier_code': fields.char('DBF supplier code', size=10),
        'dbf_destination_code': fields.char('DBF destination code', size=10),
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

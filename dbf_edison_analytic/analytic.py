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
        _logger.info('Start import account')    

        # Pool used:
        partner_pool = self.pool.get('res.partner')
        company_pool = self.pool.get('res.company')

        # Browse company: 
        company_ids = company_pool.search(cr, uid, [], context=context)
        company_proxy = company_pool.browse(
            cr, uid, company_ids, context=context)[0]
        
        # Read parameter:    
        dbf_root_path = os.path.expanduser(company_proxy.dbf_root_path)
        dbf_ignorecase = company_proxy.dbf_ignorecase
        dbf_memofile = company_proxy.dbf_memofile
        dbf_encoding = company_proxy.dbf_encoding

        # ---------------------------------------------------------------------
        #                         ANALYTIC ACCOUNT:
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
            
            # -----------------------------------------------------------------
            # Mapping fields (readability):
            # -----------------------------------------------------------------
            # Analytic account ref:
            code = '%s%s' % (
                '', # record['CANNCANT'] or '', # TODO remove year
                record['CNUMCANT'] or '',
                )                                
            name = record['CDESCANT'] or ''
            
            # Partner ref.:
            partner_code = record['CCODCLIE'] or ''
                
            # Address ref.:    
            address_street = record['CINDCANT']
            address_city = record['CCOMCANT']
            address_code = '#%s' % code

            # -----------------------------------------------------------------
            # Linked partner:
            # -----------------------------------------------------------------
            partner_ids = partner_pool.search(cr, uid, [
                ('dbf_customer_code', '=', partner_code)
                ], context=context)

            partner_id = False
            if len(partner_ids) > 1:
                _logger.error('More then one partner code: %s' % partner_code)
            if partner_ids:
                partner_id = partner_ids[0]

            # -----------------------------------------------------------------
            # Address partner (create):
            # -----------------------------------------------------------------
            address_id = False
            if address_street or address_city:
                address_ids = partner_pool.search(cr, uid, [
                    ('dbf_destination_code', '=', address_code)
                    ], context=context)
                    
                if len(address_ids) > 1:
                    _logger.error(
                        'More then one address code: %s' % address_code)
                address_data = {
                    'name': name,
                    'parent_id': partner_id,
                    'street': address_street,
                    'city': address_city,                    
                    }        

                if address_ids:
                    address_id = address_ids[0]
                    partner_pool.write(cr, uid, address_id, address_data, 
                        context=context)
                else:       
                    address_id = partner_pool.create(
                        cr, uid, address_data, context=context)

            #= record['CDESCANT'], = record['CCODCLIE'],
            #= record['CDESDECL'], = record['DDATINLA'],
            #= record['DDATFILA'], = record['LBLOCCA'],
            #= record['CRIF1CAN'], = record['CRIF2CAN'],
            #= record['CRESESTE'], = record['LECONOMIA'],
            #= record['LCONTRATTO'], = record['NOREVIAGGI'],
            #= record['NMINVIAGGI'], = record['CFILLER'],
            #= record['LSELRIGA'],  record['NRIFIMAT'],
            #= record['NRIFIMAN'],
            #= record['NRIFISPE'],
            #= record['NRIFIMATV'],
            #= record['NRIFIMANV'],
            #= record['NRIFISPEV'],
            #= record['CTIPCOMM'],
            #= record['CTLIARTI'],
            #= record['CFASCIA'],
            #= record['CTLICOST'],
            #= record['CTLIPREZ'],
            #= record['NRICPREZ'],
            #= record['LRICNOTE'],
            #= record['LVALCOPR'],
            #= record['NRMACOST'],
            #= record['NRMAPREZ'],
            #= record['LMANCOPR'],
            #= record['NRSECOST'],
            #= record['NRSEPREZ'],
            #= record['LSEXCOPR'],
            #= record['NKMPVIAGGI'],
            #= record['NCOSVIAGGI'],
            #= record['NPRZVIAGGI'],
            #= record['LATTESA'],
            #= record['LRICNOST'],
            #= record['NRICMANO'],
            #= record['NRICSPEX'],
            #= record['DDATAANA'],
            #= record['CCODPERS'],
            #= record['CLISCECO'],
            #= record['CSTATO'],
            #= record['NRMTCOST'],
            #= record['NSTSINCR'],
            #= record['DATOPER'],
            #= record['CORAOPER'],
            #= record['CCODOPER'],
            #= record['CCODUTEN'],
            #= record['CCODRECO'],
            #= record['LVALPRZV'],
            #= record['NRICPRZV'],
            #= record['CCODPRAT'],
            #= record['CCONTORI'],
            #= record['DDATCONS'],
            #= record['CCODLUPR'],
            #= record['NIMPCONT'],
            #= record['NPERESEG'],
            #= record['LVALCOMP'],
            #= record['LVALTUOR'],
            #= record['CFILLER2'],
            #= record['NPERCOST'],
            #= record['NPERPROV'],	
            #= record['CCODAGEN'],
            #= record['NPERRITG'],
            #= record['NPERMUTA'],
            #= record['CCODARTI'],
            #= record['NQTAARTI'],
            #= record['NPERPRO2'],
            #= record['CCODAMMI'],
            #= record['MMEMO1'],
            #= record['MMEMOANA'],
            #= record['MMEMOANA2'],
            #= record['MMEMOANA3'],

            data = {
                'dbf_import': True,
                'code': code,
                'name': name,
                'partner_id': partner_id,
                'address_id': address_id,
                'type': 'normal', 
                'use_timesheets': True,
                }
                
            # Search partner code:
            analytic_ids = self.search(cr, uid, [
                ('code', '=', code),
                ], context=context)

            if len(analytic_ids) > 1:
                _logger.error('More account with code: %s' % code)

            if analytic_ids:
                self.write(cr, uid, analytic_ids, data, context=context)
            else:
                self.create(cr, uid, data, context=context)
        _logger.info('End import account')    
        return True        
            
    _columns = {
        'dbf_import': fields.boolean('DBF import'),
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

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
        account_pool = self.pool.get('account.analytic.account')
        user_pool = self.pool.get('res.users')        

        # ---------------------------------------------------------------------
        # Load foreign keys database:
        # ---------------------------------------------------------------------
        # User:
        admin_id = 1
        user_db = {}
        user_ids = user_pool.search(cr, uid, [
            ('dbf_code', '!=', False)], context=context)
        for user in user_pool.browse(
                cr, uid, user_ids, context=context):
            account_db[user.dbf_code] = user.id

        # Analytic account:
        account_db = {}
        account_ids = account_pool.search(cr, uid, [(
            'dbf_import', '=', True)], context=context)
        for account in account_pool.browse(
                cr, uid, account_ids, context=context):
            account_db[account.code] = account

        # ---------------------------------------------------------------------
        # Load intervent:
        # ---------------------------------------------------------------------
        # Load previous for delete extra intervent
        previous_ids = self.search(cr, uid, [
            ('dbf_import', '=', True),
            ], context=context)
        previous_ids = set(previous_ids)    
        
        current_ids = []    
        db = company_pool.get_dbf_table(cr, uid, 'RAPPOR.DBF', context=context)
        i = 0
        for record in db:
            i += 1
            if verbose_log_count and i % verbose_log_count == 0:
                _logger.warning('Import intervent #: %s' % i)

            # -----------------------------------------------------------------
            # Read data from DBF:
            # -----------------------------------------------------------------
            # DBF:
            account_code = record['CCODCANT']
            date = record['DDATRAPP']
            hour = record['NORE']
            user_code = record['CCODUTEN']
            unit_price = record['NPREZZOH']            
            
            # Calculated:
            dbf_key = '%s-%s-%s' % date, hour, user_code
            name = ''            
            date_start = '%s 08:00:00' % date.strftime( # TODO change hour
                DEFAULT_SERVER_DATE_FORMAT)
            amount = unit_price * hour # TODO
            
            #CCODPERS ?
            #DDATOPER CORAOPER
            #CCODCAUS CCODCECO CDESCAUS CFASCIA LORESTRA CCODPRLO
            #CCODARTI COREINIZ COREFINE CMININIZ CMINFINE CRIFPART LFATT 
            #CRIFFATT LNOFATT CCODSOCO NKMPERCO NTURNI NTRASFER NVIAGGIO 
            #CCODORDLA CCODREP CCODRAPP COREINI2 COREFIN2 CMININI2 CMINFIN2
            #CCODSOFA NSTSINCR CCODOPER CCODRAP2 CCODORDL CFILEPDF CCODBARR
            #MSEGNALA MMEMO
            
            # -----------------------------------------------------------------
            # Related fiels:            
            # -----------------------------------------------------------------
            # Analytic account:
            if account_code not in account_db:
                error = 'Analytic account not found: %s' % account_code
                continue
            account_id = account_db[account_code].id    
            partner_id = account_db[account_code].partner_id.id

            # User
            if user_code in user_db: 
                user_id = user_db[user_code] or admin_id
            else:    
                warning = 'User code not found: %s' % user_code
            
            data = {
                'dbf_import': True,                
                'dbf_key': dbf_key,
                'intervent_partner_id': partner_id,
                'account_id': account_id,
                'user_id': user_id,
                'date_start': date_start
                'intervent_duration': hour,
                'intervent_total': hour,
                'name': name,
                'intervention_request': name,
                'intervention': name,
                'mode': 'customer', # 'phone', 
                'ref': '#IMPORT'
                'amount': amount,
                #'product_uom_id': 
                #'to_invoice': 
                # TODO
                }
            
            intervent_ids = self.search(cr, uid, [
                ('dbf_key', '=', dbf_key),
                ], context=context)

            if len(intervent_ids) > 1: 
                warning = 'More than one DBF key: %s' % dbf_key
            
            if intervent_ids: # Update
                self.write(cr, uid, intervent_ids[0], data, context=context)
                current_ids.append(intervent_ids[0]
            else: # Create
                self.create(cr, uid, data, context=context)
        
        current_ids = set(current_ids)    
        remove_ids = previous_ids - current_ids
        if remove_ids:
            warning = 'Delete %s intervent!' % len(remove_ids)
            self.unlink(cr, uid, remove_ids, context=context)

        _logger.info('End import intervent')    
        return True        
            
    _columns = {
        'dbf_import': fields.boolean('DBF import'),
        'dbf_key': fields.char('DBF Code', size=40), # generated key
        }

class ResUsers(orm.Model):
    """ Model name: ResUsers
    """    
    _inherit = 'res.users'
    
    _columns = {
        'dbf_code': fields.char('DBF Code', size=8),
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

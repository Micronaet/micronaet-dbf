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
from dbfread import DBF
from openerp.tools.translate import _
from openerp.tools.float_utils import float_round as round
from openerp.tools import (DEFAULT_SERVER_DATE_FORMAT, 
    DEFAULT_SERVER_DATETIME_FORMAT, 
    DATETIME_FORMATS_MAP, 
    float_compare)


_logger = logging.getLogger(__name__)

class res_company(orm.Model):
    ''' Extra fields for res.company object
    '''
    _inherit = 'res.company'

    # -------------------------------------------------------------------------
    #                                   UTLITY:
    # -------------------------------------------------------------------------
    # Log funciton:
    def get_dbf_logevent(self, log_file, event, mode='INFO', verbose=True):
        ''' Log event        
        '''
        data = '%s [%-8s]: %s\n' % (
            datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            mode,
            event,
            )

        if not log_file:
            return False

        log_file.write(data)
        if verbose: 
            _logger.info(data.strip()) # TODO manage color mode
            
    def get_dbf_logfile(self, cr, uid, log_name, context=None):
        ''' Read parameter and get table
        '''
        # Browse company: 
        company_ids = self.search(cr, uid, [], context=context)
        company_proxy = self.browse(
            cr, uid, company_ids, context=context)[0]
        
        # Read parameter:    
        dbf_log_path = os.path.expanduser(company_proxy.dbf_log_path or '')
        if not dbf_log_path:
            _logger.error('No log file (path not setup)')
            return
            
        log_file = os.path.join(dbf_log_path, log_name)
        _logger.info('Import log file: %s' % log_file)
        return open(log_file, 'a')        

    # DB function:
    def get_dbf_table(self, cr, uid, table, context=None):
        ''' Read parameter and get table
        '''
        # Browse company: 
        company_ids = self.search(cr, uid, [], context=context)
        company_proxy = self.browse(
            cr, uid, company_ids, context=context)[0]
        
        # Read parameter:    
        dbf_root_path = os.path.expanduser(company_proxy.dbf_root_path)
        dbf_ignorecase = company_proxy.dbf_ignorecase
        dbf_memofile = company_proxy.dbf_memofile
        dbf_encoding = company_proxy.dbf_encoding

        # ---------------------------------------------------------------------
        #                         ANALYTIC ACCOUNT:
        # ---------------------------------------------------------------------
        filename = os.path.join(dbf_root_path, table)
        db = DBF(
            filename, 
            ignorecase=dbf_ignorecase,
            ignore_missing_memofile=dbf_memofile,
            encoding=dbf_encoding,
            )
        return db    
        
    _columns = {
        'dbf_root_path': fields.char(
            'DBF Root path', size=180),
        'dbf_log_path': fields.char(
            'DBF Log path', size=180),
        'dbf_ignorecase': fields.boolean(
            'DBF ignore case table name', 
            help='Capital name for files'),
        'dbf_memofile': fields.boolean(
            'DBF ignore memofile',
            help='Extra memo file for DBF is not present'),            
        'dbf_encoding': fields.selection([
            ('LATIN', 'Latin'),
            ('ASCII', 'ASCII'),
            ('UTF8', 'UTF8'),
            ], 'dbf_encoding'),
        }
        
    _defaults = {
        'dbf_encoding': lambda *x: 'LATIN',
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

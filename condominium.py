##############################################################################
#
#    GNU Condo: The Free Management Condominium System
#    Copyright (C) 2016- M. Alonso <port02.server@gmail.com>
#
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from trytond.model import ModelView, fields
from trytond.pool import PoolMeta, Pool
from trytond.pyson import Eval, Not, Bool
from trytond.transaction import Transaction
from trytond.wizard import Wizard, StateTransition, StateView, Button


__all__ = ['CondoParty',
    'CheckAddressingList', 'CheckUnitMailAddress']

class CondoParty(metaclass=PoolMeta):
    __name__ = 'condo.party'
    mail = fields.Boolean('Mail', help="Check if this party should receive mail",
        )
    address = fields.Many2One('party.address', 'Address', help="Mail address for this party",
        depends=['mail', 'party'], domain=[('party', '=', Eval('party'))],
        ondelete='SET NULL', states={
            'invisible': Not(Bool(Eval('mail')))
            })

    @staticmethod
    def default_mail():
        return True

    @classmethod
    def validate(cls, condoparties):
        super(CondoParty, cls).validate(condoparties)
        for condoparty in condoparties:
            condoparty.address_when_mail()

    def address_when_mail(self):
        #Constraint to set address if mail is true
        if self.mail:
            if not self.address:
                self.raise_user_error(
                    "Set address or uncheck mail")
            elif not self.address.active:
                self.raise_user_error(
                    "Set an active address or uncheck mail")


class CheckAddressingList(ModelView):
    'Check Addressing List'
    __name__ = 'condo.check_units_addressing.result'
    units_orphan = fields.Many2Many('condo.unit', None, None,
        'Units without mail', readonly=True)
    units_unsure = fields.Many2Many('condo.unit', None, None,
        'Units to check', readonly=True)


class CheckUnitMailAddress(Wizard):
    'Check Addressing List'
    __name__ = 'condo.check_units_addressing'
    start_state = 'check'

    check = StateTransition()
    result = StateView('condo.check_units_addressing.result',
        'condominium_mail.check_units_addressing_result', [
            Button('OK', 'end', 'tryton-ok', True),
            ])

    def transition_check(self):

        pool = Pool()
        CondoParty = pool.get('condo.party')
        CondoUnit = pool.get('condo.unit')

        units_succeed = []
        units_failed = []

        #All UNITS that BELONGS TO SELETED CONDOMINIUM and/or his childrens
        units = CondoUnit.search_read([
                    'OR', [
                            ('company', 'in', Transaction().context.get('active_ids')),
                        ],[
                            ('company.parent', 'child_of', Transaction().context.get('active_ids')),
                        ],
                ], fields_names=['id'])

        #All ACTIVE CONDOPARTIES of the unit refered above that HAVE MAIL DEFINED
        condoparties = CondoParty.search([
                ('unit', 'in', [ x['id'] for x in units ]),
                ('mail', '=', True),
                ], order=[('unit.company', 'ASC'), ('unit.name', 'ASC')])

        #All UNITS WITH PARTIES THAT HAVE MAIL defined (in the unit itself or other selected units)
        units_party_with_mail = CondoUnit.search_read([
                    ('id', 'in', [ x['id'] for x in units ]),
                    ('parties.party', 'in', [ x.party for x in condoparties ]),
                ], fields_names=['id'])

        units_condoparty_with_mail = CondoUnit.search_read([
                    ('id', 'in', [ x['id'] for x in units ]),
                    ('parties', 'in', [ x.id for x in condoparties ]),
                ], fields_names=['id'])

        units_orphan = []
        units_unsure = []

        units_orphaned_count = len(units) - len(units_party_with_mail)
        if units_orphaned_count>0:
            units_orphan = [obj['id'] for obj in units if obj not in units_party_with_mail]

        units_unsure_count = len(units_party_with_mail) - len(units_condoparty_with_mail)
        if units_unsure_count>0:
            units_unsure = [obj['id'] for obj in units_party_with_mail if obj not in units_condoparty_with_mail]

        self.result.units_orphan = units_orphan
        self.result.units_unsure = units_unsure
        return 'result'

    def default_result(self, fields):
        return {
            'units_orphan': [p.id for p in self.result.units_orphan],
            'units_unsure': [p.id for p in self.result.units_unsure],
            }

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


from sql import Null
from trytond.pool import Pool, PoolMeta
from trytond.tools import reduce_ids, grouped_slice
from trytond.transaction import Transaction


__all__ = ['Address']


class Address(metaclass=PoolMeta):
    __name__ = 'party.address'

    def get_rec_name(self, name):
        if self.street:
            street = self.street.splitlines()[0]
        else:
            street = None
        if self.country:
            country = self.country.code
        else:
            country = None
        return ', '.join([_f for _f in [self.name, street, self.zip, self.city, country] if _f])

    @classmethod
    def search_rec_name(cls, name, clause):
        if clause[1].startswith('!') or clause[1].startswith('not '):
            bool_op = 'AND'
        else:
            bool_op = 'OR'
        return [
            bool_op,
            ('name',) + tuple(clause[1:]),
            ('street',) + tuple(clause[1:]),
            ('zip',) + tuple(clause[1:]),
            ('city',) + tuple(clause[1:]),
            ('country',) + tuple(clause[1:]),
        ]

    @classmethod
    def validate(cls, addresses):
        super(Address, cls).validate(addresses)
        for address in addresses:
            address.validate_active()

    def validate_active(self):
        # Deactivate address as mail address of unit's party
        if (self.id > 0) and not self.active:
            condoparties = Pool().get('condo.party').__table__()
            cursor = Transaction().connection.cursor()

            cursor.execute(*condoparties.select(condoparties.id, where=(condoparties.address == self.id)))

            ids = [ids for (ids,) in cursor.fetchall()]
            if len(ids):
                self.raise_user_warning(
                    'warn_deactive_party_address.%d' % self.id,
                    'This address will be deactivate as mailing address in %d unit(s)/apartment(s)!',
                    len(ids),
                )

                for sub_ids in grouped_slice(ids):
                    red_sql = reduce_ids(condoparties.id, sub_ids)
                    # Use SQL to prevent double validate loop
                    cursor.execute(*condoparties.update(columns=[condoparties.address], values=[Null], where=red_sql))

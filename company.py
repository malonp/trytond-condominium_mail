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


from trytond.model import fields
from trytond.pool import PoolMeta

__all__ = ['Company']


class Company(metaclass=PoolMeta):
    __name__ = 'company.company'
    mailto = fields.Function(fields.Char('Mailto'), getter='get_mailto')

    @classmethod
    def get_mailto(cls, companies, name):
        res = {}
        for company_ in companies:
            res[company_.id] = ''
            childs = cls.search([('is_condo', '=', True), ('parent', 'child_of', [company_.id])])
            emails = []
            for child in childs:
                emails.extend(
                    [
                        e.value
                        for u in child.units
                        for p in u.condoparties
                        if p.party.email
                        for e in p.party.contact_mechanisms
                        if e.type == 'email'
                    ]
                )
            if emails:
                res[company_.id] = '?bcc=' + ';'.join(set(emails))

        return res

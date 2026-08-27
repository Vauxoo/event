# Copyright 2019 David Vidal
# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0.html

from odoo.tools import SQL


def post_init_hook(env):
    """Preload proper attendee partner for existing registrations using
    the same rules the module does"""
    # A single statement instead of one search per distinct e-mail: the loop
    # issued ~3 queries per e-mail, which on a database with 2.6M partners and
    # 50k registrations meant 108k queries and over an hour of install time.
    # `registry.unaccent` returns the expression untouched when the extension
    # is not installed, matching what `=ilike` does in that case. MIN(id)
    # reproduces the `limit=1, order="id"` tie-break of the previous search.
    unaccent = env.registry.unaccent
    env.cr.execute(
        SQL(
            """
            UPDATE event_registration er
               SET attendee_partner_id = partner.id
              FROM (
                    SELECT LOWER(%s) AS email, MIN(id) AS id
                      FROM res_partner
                     WHERE active IS TRUE
                       AND COALESCE(email, '') != ''
                     GROUP BY 1
                   ) partner
             WHERE COALESCE(er.email, '') != ''
               AND LOWER(%s) = partner.email
            """,
            unaccent(SQL("email")),
            unaccent(SQL("er.email")),
        )
    )
    env.invalidate_all()

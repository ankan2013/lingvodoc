import os
import sys
import transaction

from sqlalchemy import engine_from_config

from pyramid.paster import (
    get_appsettings,
    setup_logging,
    )

from pyramid.scripts.common import parse_vars

from ..models import (
    DBSession,
    Base,
    User,
    Passhash,
    Locale,
    BaseGroup,
    Group
    )


def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri> [var=value]\n'
          '(example: "%s development.ini")' % (cmd, cmd))
    sys.exit(1)


def main(argv=sys.argv):
    if len(argv) < 2:
        usage(argv)
    config_uri = argv[1]
    options = parse_vars(argv[2:])
    setup_logging(config_uri)
    settings = get_appsettings(config_uri, options=options)
    accounts = get_appsettings(config_uri, 'accounts')
    engine = engine_from_config(settings, 'sqlalchemy.')

    DBSession.configure(bind=engine)
    Base.metadata.create_all(engine)
    with transaction.manager:

        # creating administrator account
        admin_account = DBSession.query(User).filter_by(login=accounts['administrator_login']).first()
        if not admin_account:
            print("Admin record not found, initializing")
            admin_account = User()
            admin_account.login=accounts['administrator_login']
            pwd = Passhash(password=accounts['administrator_password'])
            pwd.id = DBSession.query(Passhash).count()+1
            admin_account.password = pwd
            DBSession.add(admin_account)
            DBSession.flush()
            print(admin_account.name)

        # creating base locales
        ru_locale = Locale(id=1, shortcut="ru", intl_name="Русский")
        en_locale = Locale(id=2, shortcut="en", intl_name="English")
        de_locale = Locale(id=3, shortcut="de", intl_name="Deutsch")
        fr_locale = Locale(id=4, shortcut="fr", intl_name="Le français")

        DBSession.add(ru_locale)
        DBSession.flush()
        DBSession.add(en_locale)
        DBSession.flush()
        DBSession.add(de_locale)
        DBSession.flush()
        DBSession.add(fr_locale)
        DBSession.flush()

        # creating base groups
        name_vector = [('can_create_dictionaries', 'Can create dictionaries'),
                       ('can_create_languages', 'Can create dictionaries'),
                       ('can_edit_languages', 'Can create dictionaries'),
                       ('can_delete_languages', 'Can create dictionaries'),
                       ('can_create_groups', 'Can create dictionaries'),
                       ('can_create_organizations', 'Can create dictionaries'),
                       ('can_edit_organizations', 'Can create dictionaries'),
                       ('can_edit_users', 'Can create dictionaries'),
                       ('can_change_dictionary_info', 'Can create dictionaries'),
                       ('can_invite_collaborators', 'Can create dictionaries'),
                       ('can_add_words', 'Can create dictionaries'),
                       ('can_delete_words', 'Can create dictionaries'),
                       ('can_set_defaults', 'Can create dictionaries'),
                       ('can_publish', 'Can create dictionaries'),

                       ]
        can_create_dictionaries = BaseGroup(name="can_create_dictionaries", readable_name="Can create dictionaries")
        can_create_dictionaries.name = "can_create_dictionaries"
        can_create_dictionaries.readable_name = 
        DBSession.add(can_create_dictionaries)
        DBSession.flush()
        can_create_languages = BaseGroup(name="can_create_languages", readable_name="Can create languages")
        DBSession.add(can_create_languages)
        DBSession.flush()
        can_edit_languages = BaseGroup(name="can_edit_languages", readable_name="Can edit languages")
        DBSession.add(can_edit_languages)
        DBSession.flush()
        can_delete_languages = BaseGroup(name="can_delete_languages", readable_name="Can delete languages")
        DBSession.add(can_delete_languages)
        DBSession.flush()
        can_create_groups = BaseGroup(name="can_create_groups", readable_name="Can create groups")
        DBSession.add(can_create_groups)
        DBSession.flush()
        can_create_organizations = BaseGroup(name="can_create_organizations", readable_name="Can create organizations")
        DBSession.add(can_create_organizations)
        DBSession.flush()
        can_edit_organizations = BaseGroup(name="can_edit_organizations", readable_name="Can edit organizations")
        DBSession.add(can_edit_organizations)
        DBSession.flush()
        can_edit_users = BaseGroup(name="can_edit_users", readable_name="Can edit users")
        DBSession.add(can_edit_users)
        DBSession.flush()
        can_change_dictionary_info = BaseGroup(name="can_change_dictionary_info", readable_name="Can change dictionary info")
        DBSession.add(can_change_dictionary_info)
        DBSession.flush()
        can_invite_collaborators = BaseGroup(name="can_invite_collaborators", readable_name="Can invite collaborators")
        DBSession.add(can_invite_collaborators)
        DBSession.flush()
        can_add_words = BaseGroup(name="can_add_words", readable_name="Can add words")
        DBSession.add(can_add_words)
        DBSession.flush()
        can_delete_words = BaseGroup(name="can_delete_words", readable_name="Can delete words")
        DBSession.add(can_delete_words)
        DBSession.flush()
        can_set_defaults = BaseGroup(name="can_set_defaults", readable_name="Can set default entries for publication")
        DBSession.add(can_set_defaults)
        DBSession.flush()
        can_publish = BaseGroup(name="can_publish", readable_name="Can publish dictionaries")
        DBSession.add(can_publish)
        DBSession.flush()

        # creating admin groups

        adm_can_create_dictionaries = Group(base_group_id=can_create_dictionaries.id, subject="ANY")
        DBSession.add(adm_can_create_dictionaries)
        DBSession.flush()
        adm_can_create_languages = Group(base_group_id=can_create_languages.id, subject="ANY")
        DBSession.add(adm_can_create_languages)
        DBSession.flush()
        adm_can_edit_languages = Group(base_group_id=can_edit_languages.id, subject="ANY")
        DBSession.add(adm_can_edit_languages)
        DBSession.flush()
        adm_can_delete_languages = Group(base_group_id=can_delete_languages.id, subject="ANY")
        DBSession.add(adm_can_delete_languages)
        DBSession.flush()
        adm_can_create_groups = Group(base_group_id=can_create_groups.id, subject="ANY")
        DBSession.add(adm_can_create_groups)
        DBSession.flush()
        adm_can_create_organizations = Group(base_group_id=can_create_organizations.id, subject="ANY")
        DBSession.add(adm_can_create_organizations)
        DBSession.flush()
        adm_can_edit_organizations = Group(base_group_id=can_edit_organizations.id, subject="ANY")
        DBSession.add(adm_can_edit_organizations)
        DBSession.flush()
        adm_can_edit_users = Group(base_group_id=can_edit_users.id, subject="ANY")
        DBSession.add(adm_can_edit_users)
        DBSession.flush()
        adm_can_change_dictionary_info = Group(base_group_id=can_change_dictionary_info.id, subject="ANY")
        DBSession.add(adm_can_change_dictionary_info)
        DBSession.flush()
        adm_can_invite_collaborators = Group(base_group_id=can_invite_collaborators.id, subject="ANY")
        DBSession.add(adm_can_invite_collaborators)
        DBSession.flush()
        adm_can_add_words = Group(base_group_id=can_add_words.id, subject="ANY")
        DBSession.add(adm_can_add_words)
        DBSession.flush()
        adm_can_delete_words = Group(base_group_id=can_delete_words.id, subject="ANY")
        DBSession.add(adm_can_delete_words)
        DBSession.flush()
        adm_can_set_defaults = Group(base_group_id=can_set_defaults.id, subject="ANY")
        DBSession.add(adm_can_set_defaults)
        DBSession.flush()
        adm_can_publish = Group(base_group_id=can_publish.id, subject="ANY")
        DBSession.add(adm_can_publish)
        DBSession.flush()

        admin_account.groups = [adm_can_create_dictionaries,
                                adm_can_create_languages,
                                adm_can_edit_languages,
                                adm_can_delete_languages,
                                adm_can_create_groups,
                                adm_can_create_organizations,
                                adm_can_edit_organizations,
                                adm_can_edit_users,
                                adm_can_change_dictionary_info,
                                adm_can_invite_collaborators,
                                adm_can_add_words,
                                adm_can_delete_words,
                                adm_can_set_defaults,
                                adm_can_publish]
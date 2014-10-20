from pyramid.config import Configurator
from sqlalchemy import engine_from_config
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy

from .models import (
    DBSession,
    Base,
    )

from .acl import (
    groupfinder
)


def configure_routes(config):
    config.add_route('home', '/')
    config.add_route('register', 'register')
    config.add_route('register/validate', 'register/validate/{param}')
    config.add_route('login', 'login')
    config.add_route('logout', 'logout')
    config.add_route('dashboard', 'dashboard')
    config.add_route('create_dictionary_page', 'create_dictionary_page')
    config.add_route('create_dictionary', 'create_dictionary')
    config.add_route('create_language_page', 'create_language_page')
    config.add_route('create_language', 'create_language')


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    from pyramid.config import Configurator
    authentication_policy = AuthTktAuthenticationPolicy('secret_string_that_you_should_change',
                                                        hashalg='sha512', callback=groupfinder)
    authorization_policy = ACLAuthorizationPolicy()
    config = Configurator(settings=settings)
    config.set_authentication_policy(authentication_policy)
    config.set_authorization_policy(authorization_policy)
    config.include('pyramid_chameleon')
    config.add_static_view('static', path='lingvodoc:static', cache_max_age=3600)
    configure_routes(config)
#    config.add_route('home', '/')
#    config.add_route('login', 'login')
#    config.add_route('logout', 'logout')
#    config.add_route('register', 'register')
#    config.add_route('acquire_client_key', 'acquire_client_key')
#    config.add_route('dictionaries.list', 'dictionaries', factory='lingvodoc.models.DictionariesACL')
#    config.add_route('dictionary', 'dictionary')

#    config.add_route('metaword', 'dictionary/{dictionary_id}/etymology/metaword')
    config.scan('.views')
    return config.make_wsgi_app()

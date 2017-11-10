import graphene
from collections import  defaultdict
from sqlalchemy import and_
from lingvodoc.models import (
    DictionaryPerspective as dbPerspective,
    Dictionary as dbDictionary,
    TranslationAtom as dbTranslationAtom,
    Language as dbLanguage,
    LexicalEntry as dbLexicalEntry,
    Client as dbClient,
    User as dbUser,
    TranslationGist as dbTranslationGist,
    BaseGroup as dbBaseGroup,
    Group as dbGroup,
    Entity as dbEntity,
    Organization as dbOrganization,
    ObjectTOC,
    DBSession,
    DictionaryPerspectiveToField as dbColumn,
    PublishingEntity as dbPublishingEntity,

)

from lingvodoc.schema.gql_holders import (
    LingvodocObjectType,
    LingvodocID,
    CommonFieldsComposite,
    TranslationHolder,
    StateHolder,
    fetch_object,
    client_id_check,
    del_object,
    ResponseError,
    acl_check_by_id,
    ObjectVal
)

from lingvodoc.schema.gql_dictionary import Dictionary
from lingvodoc.schema.gql_column import Column
from lingvodoc.schema.gql_lexicalentry import LexicalEntry
from lingvodoc.schema.gql_language import Language
from lingvodoc.schema.gql_entity import Entity
from  lingvodoc.schema.gql_user import User

from sqlalchemy.sql.expression import case, true, false

from lingvodoc.views.v2.translations import translationgist_contents
from lingvodoc.utils import statistics
from pyramid.request import Request
from lingvodoc.utils.creation import (
    create_perspective,
    create_gists_with_atoms,
    add_user_to_group, translationgist_contents)

from sqlalchemy import (
    func,
    or_,
    and_,
    tuple_
)

from lingvodoc.schema.gql_holders import UserAndOrganizationsRoles

class DictionaryPerspective(LingvodocObjectType):
    """
     #created_at                       | timestamp without time zone | NOT NULL
     #object_id                        | bigint                      | NOT NULL
     #client_id                        | bigint                      | NOT NULL
     #parent_object_id                 | bigint                      |
     #parent_client_id                 | bigint                      |
     #translation_gist_client_id       | bigint                      | NOT NULL
     #translation_gist_object_id       | bigint                      | NOT NULL
     #state_translation_gist_client_id | bigint                      | NOT NULL
     #state_translation_gist_object_id | bigint                      | NOT NULL
     #marked_for_deletion              | boolean                     | NOT NULL
     #is_template                      | boolean                     | NOT NULL
     #import_source                    | text                        |
     #import_hash                      | text                        |
     #additional_metadata              | jsonb                       |
     + .translation
     + status
     + tree

    query myQuery {
      perspective(id: [78, 4]) {
        id
        statistic(starting_time: 0, ending_time: 1506812557)
        entities(mode: "all") {
          id
          parent_id
          published
          accepted
        }
        lexical_entries(ids: [[78, 6], [78, 8]]) {
          id
        }
            columns{
                id
                field_id
            }
      }
    }

    """
    data_type = graphene.String()

    status = graphene.String()
    import_source = graphene.String()
    import_hash = graphene.String()

    tree = graphene.List(CommonFieldsComposite, )  # TODO: check it
    columns = graphene.List(Column)
    entities = graphene.List(Entity, mode=graphene.String())
    entities_old = graphene.List(Entity, mode=graphene.String())
    lexical_entries = graphene.List(LexicalEntry, ids = graphene.List(LingvodocID))
    authors = graphene.List('lingvodoc.schema.gql_user.User')
    # stats = graphene.String() # ?
    roles = graphene.Field(UserAndOrganizationsRoles)
    statistic = graphene.Field(ObjectVal, starting_time=graphene.Int(), ending_time=graphene.Int())
    is_template = graphene.Boolean()

    dbType = dbPerspective

    class Meta:
        interfaces = (CommonFieldsComposite, StateHolder)

    # @fetch_object()
    # def resolve_additional_metadata(self, args, context, info):
    #     return self.dbObject.additional_metadata

    # @fetch_object('translation')
    # def resolve_translation(self, args, context, info):
    #     return self.dbObject.get_translation(context.get('locale_id'))

    @fetch_object('is_template')
    def resolve_is_template(self, info):
        return self.dbObject.is_template

    @fetch_object('status') # tested
    def resolve_status(self, info):
        atom = DBSession.query(dbTranslationAtom).filter_by(
            parent_client_id=self.dbObject.state_translation_gist_client_id,
            parent_object_id=self.dbObject.state_translation_gist_object_id,
            locale_id=int(info.context.get('locale_id'))
        ).first()
        if atom:
            return atom.content
        else:
            return None

    @fetch_object() # tested
    def resolve_tree(self, info):
        result = list()
        iteritem = self.dbObject
        while iteritem:
            id = [iteritem.client_id, iteritem.object_id]
            if type(iteritem) == dbPerspective:
                gql_persp = DictionaryPerspective(id=id)
                gql_persp.dbObject = iteritem
                result.append(gql_persp)
            if type(iteritem) == dbDictionary:
                result.append(Dictionary(id=id))
            if type(iteritem) == dbLanguage:
                result.append(Language(id=id))
            iteritem = iteritem.parent

        return result

    @fetch_object() # tested
    def resolve_columns(self, info):
        columns = DBSession.query(dbColumn).filter_by(parent=self.dbObject, marked_for_deletion=False).all()
        result = list()
        for dbfield in columns:
            gr_field_obj = Column(id=[dbfield.client_id, dbfield.object_id])
            gr_field_obj.dbObject = dbfield
            result.append(gr_field_obj)
        return result

    #@acl_check_by_id('view', 'approve_entities')
    @fetch_object()
    def resolve_lexical_entries(self, info, ids=None):
        lex_list = list()
        query = DBSession.query(dbLexicalEntry)
        if ids is None:
            query = query.filter(dbLexicalEntry.parent == self.dbObject, dbLexicalEntry.marked_for_deletion == False)
        else:
            query = query.filter(tuple_(dbLexicalEntry.client_id, dbLexicalEntry.object_id).in_(ids), dbLexicalEntry.parent == self.dbObject, dbLexicalEntry.marked_for_deletion == False)
        for lex in query.all():
            lex_object = LexicalEntry(id=[lex.client_id, lex.object_id])
            lex_object.dbObject = lex
            lex_list.append(lex_object)
        return lex_list



    #@acl_check_by_id('view', 'approve_entities')
    @fetch_object()
    def resolve_entities_old(self, info, mode=None):
        result = list()
        request = info.context.get('request')
        if mode == 'all':
            publish=None
            accept=True
        elif mode == 'published':
            publish=True
            accept=True
        elif mode == 'not_accepted':
            publish=None
            accept=False
        else:
            raise ResponseError(message="mode: <all|published|not_accepted>")
        # dbPersp = DBSession.query(dbPerspective).filter_by(client_id=self.id[0], object_id=self.id[1]).one()
        lexes = DBSession.query(dbLexicalEntry).filter_by(parent=self.dbObject)

        lexes_composite_list = [(lex.created_at,
                                 lex.client_id, lex.object_id, lex.parent_client_id, lex.parent_object_id,
                                 lex.marked_for_deletion, lex.additional_metadata,
                                 lex.additional_metadata.get('came_from')
                                 if lex.additional_metadata and 'came_from' in lex.additional_metadata else None)
                                for lex in lexes.all()]
        # for lex in lexes:
        #     dbentities = DBSession.query(dbEntity).filter_by(parent=lex).all()
        #     entities = [Entity(id=[ent.client_id, ent.object_id]) for ent in dbentities]
        #     result.append(LexicalEntry(id=[lex.client_id, lex.object_id], entities = entities))
        sub_result = dbLexicalEntry.track_multiple(lexes_composite_list,
                                                   int(request.cookies.get('locale_id') or 2),
                                                   publish=publish, accept=accept)

        entities = []
        for entry in sub_result:
            for ent in entry['contains']:

                # del attributes that Entity class doesn`t have
                # the code below has to be refactored

                del ent["contains"]
                del ent["level"]
                # del ent["accepted"]
                del ent["entity_type"]
                # del ent["published"]
                if "link_client_id" in ent and "link_object_id" in ent:
                    ent["link_id"] = (ent["link_client_id"], ent["link_object_id"])
                    del ent["link_client_id"]
                    del ent["link_object_id"]
                else:
                    ent["link_id"] = None

                ent["field_id"] = (ent["field_client_id"], ent["field_object_id"])
                if "self_client_id" in ent and "self_object_id" in ent:
                    ent["self_id"] = (ent["self_client_id"], ent["self_object_id"])
                    del ent["self_client_id"]
                    del ent["self_object_id"]

                else:
                    ent["self_id"] = None
                    # context["request"].body = str(context["request"].body).replace("self_id", "").encode("utf-8")
                if "content" not in ent:
                    ent["content"] = None
                if "additional_metadata" in ent:

                    # used in AdditionalMetadata interface (gql_holders.py) and sets metadata dictionary

                    ent["additional_metadata_string"] = ent["additional_metadata"]
                    del ent["additional_metadata"]
                tmp_id = [ent['client_id'], ent['object_id']]
                del ent["client_id"]
                del ent["object_id"]
                del ent["field_client_id"]
                del ent["field_object_id"]
                parent_client_id, parent_object = ent["parent_client_id"], ent["parent_object_id"]
                del ent["parent_client_id"]
                del ent["parent_object_id"]
                gr_entity_object = Entity(id=tmp_id,
                                       # link_id = (ent["link_client_id"], ent["link_object_id"]),
                                       parent_id = [parent_client_id, parent_object],
                                       **ent  # all other args from sub_result
                                          )
                #print(ent)
                entities.append(gr_entity_object)
        return entities

    @fetch_object()
    def resolve_entities(self, info, mode=None, authors=None, clients=None, start_date=None, end_date=None,
                             position=1):
        result = list()
        request = info.context.get('request')
        if mode == 'all':
            publish = None
            accept = True
            delete = False
        elif mode == 'published':
            publish = True
            accept = True
            delete = False
        elif mode == 'not_accepted':
            publish = None
            accept = False
            delete = False
        elif mode == 'deleted':
            publish = None
            accept = None
            delete = True
        elif mode == 'all_with_deleted':
            publish = None
            accept = None
            delete = None
        else:
            raise ResponseError(message="mode: <all|published|not_accepted|deleted|all_with_deleted>")

        dbcolumn = DBSession.query(dbColumn).filter_by(parent=self.dbObject, position=position, self_client_id=None,
                                                       self_object_id=None).first()

        lexes = DBSession.query(dbLexicalEntry).join(dbLexicalEntry.entity).join(dbEntity.publishingentity) \
            .filter(dbLexicalEntry.parent == self.dbObject)
        if publish is not None:
            lexes = lexes.filter(dbPublishingEntity.published == publish)
        if accept is not None:
            lexes = lexes.filter(dbPublishingEntity.accepted == accept)
        if delete is not None:
            lexes = lexes.filter(or_(dbLexicalEntry.marked_for_deletion == delete, dbEntity.marked_for_deletion == delete))

        if authors:
            lexes = lexes.join(dbClient, dbEntity.client_id == dbClient.id).join(dbClient.user).filter(dbUser.id.in_(authors))
        if start_date:
            lexes = lexes.filter(dbEntity.created_at >= start_date)
        if end_date:
            lexes = lexes.filter(dbEntity.created_at <= end_date)
        lexes = lexes \
            .order_by(func.min(case(
            [(or_(dbEntity.field_client_id != dbcolumn.field_client_id,
                  dbEntity.field_object_id != dbcolumn.field_object_id),
              'яяяяяя')],
            else_=dbEntity.content))) \
            .group_by(dbLexicalEntry)

        lexes_composite_list = [(lex.client_id, lex.object_id, lex.parent_client_id, lex.parent_object_id)
                                for lex in lexes.yield_per(100)]
        entities = dbLexicalEntry.graphene_track_multiple(lexes_composite_list,
                                                   int(request.cookies.get('locale_id') or 2),
                                                   publish=publish, accept=accept, delete=delete)

        def graphene_entity(entity, publishing):
            ent = Entity(id = (entity.client_id, entity.object_id))
            ent.dbObject = entity
            ent.publishingentity = publishing
            return ent

        entities = [graphene_entity(entity[0], entity[1]) for entity in entities]

        return entities

    @fetch_object()
    def resolve_authors(self, info):
        client_id, object_id = self.dbObject.client_id, self.dbObject.object_id

        parent = DBSession.query(dbPerspective).filter_by(client_id=client_id, object_id=object_id).first()
        if parent and not parent.marked_for_deletion:
            authors = DBSession.query(dbUser).join(dbUser.clients).join(dbEntity, dbEntity.client_id == dbClient.id) \
                .join(dbEntity.parent).join(dbEntity.publishingentity) \
                .filter(dbLexicalEntry.parent_client_id == parent.client_id,# TODO: filter by accepted==True
                        dbLexicalEntry.parent_object_id == parent.object_id,
                        dbLexicalEntry.marked_for_deletion == False,
                        dbEntity.marked_for_deletion == False)

            authors_list = [User(id=author.id,
                                 name=author.name,
                                 intl_name=author.intl_name,
                                 login=author.login) for author in authors]
            return authors_list
        raise ResponseError(message="Error: no such perspective in the system.")

    @fetch_object(ACLSubject='perspective_role', ACLKey='id')
    def resolve_roles(self, info):
        client_id, object_id = self.dbObject.client_id, self.dbObject.object_id
        perspective = DBSession.query(dbPerspective).filter_by(client_id=client_id, object_id=object_id).first()
        if not perspective or perspective.marked_for_deletion:
            raise ResponseError(message="Perspective with such ID doesn`t exists in the system")


        bases = DBSession.query(dbBaseGroup).filter_by(perspective_default=True)
        roles_users = defaultdict(list)
        roles_organizations = defaultdict(list)
        for base in bases:
            group = DBSession.query(dbGroup).filter_by(base_group_id=base.id,
                                                     subject_object_id=object_id,
                                                     subject_client_id=client_id).first()
            if not group:
                continue
            for user in group.users:
                roles_users[user.id].append(base.id)
            for org in group.organizations:
                roles_organizations[org.id].append(base.id)
        roles_users = [{"user_id": x, "roles_ids": roles_users[x]} for x in roles_users]
        roles_organizations = [{"user_id": x, "roles_ids": roles_organizations[x]} for x in roles_organizations]
        return UserAndOrganizationsRoles(roles_users=roles_users, roles_organizations=roles_organizations)

    @fetch_object()
    def resolve_statistic(self, info, starting_time=None, ending_time=None):
        if starting_time is None or ending_time is None:
            raise ResponseError(message="Bad time period")
        locale_id = info.context.get('locale_id')
        return statistics.stat_perspective((self.dbObject.client_id, self.dbObject.object_id),
                                   starting_time,
                                   ending_time,
                                   locale_id=locale_id
                                   )


class CreateDictionaryPerspective(graphene.Mutation):
    """
    example:
    mutation  {
            create_perspective( parent_id:[66,4], translation_gist_id: [714, 3],is_template: true
             additional_metadata: {hash:"1234567"}, import_source: "source", import_hash: "hash") {
                triumph

                perspective{
					is_template
                    id
                }
            }
    }
    (this example works)
    returns:
    {
        "data": {
            "create_perspective": {
                "triumph": true,
                "perspective": {
                    "id": [
                        1197,
                        320
                    ]
                }
            }
        }
    }
    with atoms:
    mutation {
      create_perspective(parent_id: [1198, 16], translation_atoms: [{locale_id: 2, content: "123"}], additional_metadata: {hash: "1234567"}, import_source: "source", import_hash: "hash") {
        triumph
        perspective {
          id
          translation
        }
      }
    }

    """

    class Arguments:
        id = LingvodocID()
        parent_id = LingvodocID(required=True)
        translation_gist_id = LingvodocID()
        translation_atoms = graphene.List(ObjectVal)
        additional_metadata = ObjectVal()
        import_source = graphene.String()
        import_hash = graphene.String()
        is_template = graphene.Boolean()

    perspective = graphene.Field(DictionaryPerspective)
    triumph = graphene.Boolean()


    @staticmethod
    @client_id_check()
    @acl_check_by_id('create', 'perspective', id_key = "parent_id")
    def mutate(root, info, **args):
        id = args.get("id")
        client_id = id[0] if id else info.context["client_id"]
        object_id = id[1] if id else None
        id = [client_id, object_id]
        parent_id = args.get('parent_id')
        translation_gist_id = args.get('translation_gist_id')
        translation_atoms = args.get("translation_atoms")

        translation_gist_id = create_gists_with_atoms(translation_atoms, translation_gist_id, [client_id,object_id])
        import_source = args.get('import_source')
        import_hash = args.get('import_hash')
        additional_metadata = args.get('additional_metadata')
        is_template = args.get("is_template")
        dbperspective = create_perspective(id=id,
                                parent_id=parent_id,
                                translation_gist_id=translation_gist_id,
                                additional_metadata=additional_metadata,
                                import_source=import_source,
                                import_hash=import_hash,
                                is_template=is_template
                                )
        perspective = DictionaryPerspective(id=[dbperspective.client_id, dbperspective.object_id])
        perspective.dbObject = dbperspective
        return CreateDictionaryPerspective(perspective=perspective, triumph=True)


class UpdateDictionaryPerspective(graphene.Mutation):
    """
    example:
      mutation  {
            update_perspective(id:[949,2491], parent_id:[449,2491], translation_gist_id: [714, 3]) {
                triumph
                perspective{
                    id
                }
            }
    }

    (this example works)
    returns:

    {
      "update_perspective": {
        "triumph": true,
        "perspective": {
          "id": [
            949,
            2491
          ],
        }
      }
    }
    """
    class Arguments:
        id = LingvodocID(required=True)  #List(graphene.Int) # lingvidicID
        translation_gist_id = LingvodocID()
        parent_id = LingvodocID()

    perspective = graphene.Field(DictionaryPerspective)
    triumph = graphene.Boolean()

    @staticmethod
    @acl_check_by_id('edit', 'perspective')
    def mutate(root, info, **args):
        id = args.get("id")
        client_id = id[0]
        object_id = id[1]
        parent_id = args.get('parent_id')
        dbperspective = DBSession.query(dbPerspective).filter_by(client_id=client_id, object_id=object_id).first()
        if not dbperspective or dbperspective.marked_for_deletion:
            raise ResponseError(message="Error: No such perspective in the system")

        # dictionaryperspective_parent_object_id_fkey  (parent_object_id, parent_client_id)=(2491, 449)  in dictionary
        translation_gist_id = args.get("translation_gist_id")
        translation_gist_client_id = translation_gist_id[0] if translation_gist_id else None
        translation_gist_object_id = translation_gist_id[1] if translation_gist_id else None
        if translation_gist_client_id:
            dbperspective.translation_gist_client_id = translation_gist_client_id
        if translation_gist_object_id:
            dbperspective.translation_gist_object_id = translation_gist_object_id  # TODO: refactor like dictionaries
        if parent_id:
            parent_client_id, parent_object_id = parent_id
            dbparent_dictionary = DBSession.query(dbDictionary).filter_by(client_id=parent_client_id,
                                                                          object_id=parent_object_id).first()
            if not dbparent_dictionary:
                raise ResponseError(message="Error: No such dictionary in the system")
            dbperspective.parent_client_id = parent_client_id
            dbperspective.parent_object_id = parent_object_id


        perspective = DictionaryPerspective(id=[dbperspective.client_id, dbperspective.object_id])
        perspective.dbObject = dbperspective
        return UpdateDictionaryPerspective(perspective=perspective, triumph=True)

class UpdatePerspectiveStatus(graphene.Mutation):
    """
    mutation  {
    update_perspective_status(id:[66, 5], state_translation_gist_id: [1, 192]) {
        triumph
        perspective{
            id
        }
    }
    }

    """
    class Arguments:
        id = LingvodocID(required=True)
        state_translation_gist_id = LingvodocID(required=True)

    perspective = graphene.Field(DictionaryPerspective)
    triumph = graphene.Boolean()

    @staticmethod
    @acl_check_by_id("edit", "perspective_status")
    def mutate(root, info, **args):
        client_id, object_id = args.get('id')
        state_translation_gist_client_id, state_translation_gist_object_id = args.get('state_translation_gist_id')
        dbperspective = DBSession.query(dbPerspective).filter_by(client_id=client_id, object_id=object_id).first()
        if dbperspective and not dbperspective.marked_for_deletion:
            dbperspective.state_translation_gist_client_id = state_translation_gist_client_id
            dbperspective.state_translation_gist_object_id = state_translation_gist_object_id
            atom = DBSession.query(dbTranslationAtom).filter_by(parent_client_id=state_translation_gist_client_id,
                                                              parent_object_id=state_translation_gist_object_id,
                                                              locale_id=info.context.get('locale_id')).first()
            perspective = DictionaryPerspective(id=[dbperspective.client_id, dbperspective.object_id],
                                                status=atom.content)
            perspective.dbObject = dbperspective
            return UpdatePerspectiveStatus(perspective=perspective, triumph=True)

class UpdatePerspectiveRoles(graphene.Mutation):
    class Arguments:
        id = LingvodocID(required=True)
        parent_id = LingvodocID()
        roles_users = graphene.List(ObjectVal)
        roles_organizations = graphene.List(ObjectVal)

    perspective = graphene.Field(DictionaryPerspective)
    triumph = graphene.Boolean()

    @staticmethod
    def mutate(root, info, **args):
        DBSession.execute("LOCK TABLE user_to_group_association IN EXCLUSIVE MODE;")
        DBSession.execute("LOCK TABLE organization_to_group_association IN EXCLUSIVE MODE;")

        client_id, object_id = args.get('id')
        parent_client_id, parent_object_id = args.get('parent_id')

        request = info.context.get('request')
        cookies = info.context.get('cookies')
        url = request.route_url('perspective_roles',
                                client_id=parent_client_id,
                                object_id=parent_object_id,
                                perspective_client_id=client_id,
                                perspective_object_id=object_id)
        subreq = Request.blank(url)
        subreq.method = 'GET'
        headers = {'Cookie': cookies}
        subreq.headers = headers
        previous = request.invoke_subrequest(subreq).json_body

        roles_users = args.get('roles_users')
        roles_organizations = args.get('roles_organizations')

        for role_name in roles_users:
            remove_list = list()
            for user in roles_users[role_name]:
                if user in previous['roles_users'][role_name]:
                    previous['roles_users'][role_name].remove(user)
                    remove_list.append(user)
            for user in remove_list:
                roles_users[role_name].remove(user)

        for role_name in roles_organizations:
            remove_list = list()
            for user in roles_organizations[role_name]:
                if user in previous['roles_organizations'][role_name]:
                    previous['roles_organizations'][role_name].remove(user)
                    roles_organizations[role_name].remove(user)
            for user in remove_list:
                roles_users[role_name].remove(user)

        delete_flag = False

        for role_name in previous['roles_users']:
            if previous['roles_users'][role_name]:
                delete_flag = True
                break

        for role_name in previous['roles_organizations']:
            if previous['roles_organizations'][role_name]:
                delete_flag = True
                break

        if delete_flag:
            subreq = Request.blank(url)
            subreq.json = previous
            subreq.method = 'PATCH'
            headers = {'Cookie': cookies}
            subreq.headers = headers
            request.invoke_subrequest(subreq)

        parent = DBSession.query(dbDictionary).filter_by(client_id=parent_client_id, object_id=parent_object_id).first()
        if not parent:
            raise ResponseError(message="No such dictionary in the system")

        dbperspective = DBSession.query(dbPerspective).filter_by(client_id=client_id, object_id=object_id).first()
        if dbperspective and not dbperspective.marked_for_deletion:
            if roles_users:
                for role_name in roles_users:
                    base = DBSession.query(dbBaseGroup).filter_by(name=role_name, perspective_default=True).first()
                    if not base:
                        raise ResponseError(message="No such role in the system")

                    group = DBSession.query(dbGroup).filter_by(base_group_id=base.id,
                                                             subject_object_id=object_id,
                                                             subject_client_id=client_id).first()
                    client = DBSession.query(dbClient).filter_by(id=request.authenticated_userid).first()
                    userlogged = DBSession.query(dbUser).filter_by(id=client.user_id).first()

                    permitted = False
                    if userlogged in group.users:
                        permitted = True
                    if not permitted:
                        for org in userlogged.organizations:
                            if org in group.organizations:
                                permitted = True
                                break
                    if not permitted:
                        override_group = DBSession.query(dbGroup).filter_by(base_group_id=base.id,
                                                                            subject_override=True).first()
                        if userlogged in override_group.users:
                            permitted = True

                    if permitted:
                        users = roles_users[role_name]
                        for userid in users:
                            user = DBSession.query(dbUser).filter_by(id=userid).first()
                            if user:
                                if user not in group.users:
                                    group.users.append(user)
                    else:
                        if roles_users[role_name]:
                            raise ResponseError(message="Not enough permission")

            if roles_organizations:
                for role_name in roles_organizations:
                    base = DBSession.query(dbBaseGroup).filter_by(name=role_name, perspective_default=True).first()
                    if not base:
                        raise ResponseError(message="No such role in the system")

                    group = DBSession.query(dbGroup).filter_by(base_group_id=base.id,
                                                               subject_object_id=object_id,
                                                               subject_client_id=client_id).first()
                    client = DBSession.query(dbClient).filter_by(id=request.authenticated_userid).first()
                    userlogged = DBSession.query(dbUser).filter_by(id=client.user_id).first()

                    permitted = False
                    if userlogged in group.users:
                        permitted = True
                    if not permitted:
                        for org in userlogged.organizations:
                            if org in group.organizations:
                                permitted = True
                                break
                    if not permitted:
                        override_group = DBSession.query(dbGroup).filter_by(base_group_id=base.id,
                                                                            subject_override=True).first()
                        if userlogged in override_group.users:
                            permitted = True

                    if permitted:
                        orgs = roles_organizations[role_name]
                        for orgid in orgs:
                            org = DBSession.query(dbOrganization).filter_by(id=orgid).first()
                            if org:
                                if org not in group.organizations:
                                    group.organizations.append(org)

                    else:
                        raise ResponseError(message="Not enough permission")

            perspective = DictionaryPerspective(id=[dbperspective.client_id, dbperspective.object_id])
            perspective.dbObject = dbperspective
            return UpdatePerspectiveRoles(perspective=perspective, triumph=True)
        raise ResponseError(message="No such perspective in the system")

class DeleteDictionaryPerspective(graphene.Mutation):
    """
    example:
      mutation  {
            delete_perspective(id:[949,2491], parent_id:[449,2491]) {
                triumph
                perspective{
                    id
                }
            }
    }

    (this example works)
    returns:

    {
      "delete_perspective": {
        "triumph": true,
        "perspective": {
          "id": [
            949,
            2491
          ],
        }
      }
    }
    """
    class Arguments:
        id = LingvodocID(required=True)

    perspective = graphene.Field(DictionaryPerspective)
    triumph = graphene.Boolean()

    @staticmethod
    @acl_check_by_id('delete', 'perspective')
    def mutate(root, info, **args):
        id = args.get("id")
        client_id, object_id = id
        dbperspective = DBSession.query(dbPerspective).filter_by(client_id=client_id, object_id=object_id).first()
        if not dbPerspective or not dbperspective.marked_for_deletion:
            raise ResponseError(message="No such perspective in the system")

        del_object(dbperspective)

        perspective = DictionaryPerspective(id=[dbperspective.client_id, dbperspective.object_id])
        perspective.dbObject = dbperspective
        return DeleteDictionaryPerspective(perspective=perspective, triumph=True)

